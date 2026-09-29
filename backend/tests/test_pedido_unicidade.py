"""Garantia central do desafio: no máximo um pedido por oportunidade (Princípio III)."""

import threading
from decimal import Decimal

import pytest
from django.db import IntegrityError, connection

from comercial.models import Pedido
from comercial.services import pedidos as servico_pedidos


@pytest.fixture(autouse=True)
def erp_limpo(settings):
    settings.ERP_MODO = "sucesso"


def url(op_id: int) -> str:
    return f"/api/oportunidades/{op_id}/pedido"


@pytest.mark.django_db
def test_gera_pedido(api, criar_oportunidade, espiao_erp):
    op = criar_oportunidade(estagio="GANHO", valor=Decimal("120000"))
    r = api.post(url(op.id))
    assert r.status_code == 201
    pedido = r.json()
    assert pedido["status"] == "GERADO"
    assert pedido["numero_erp"].startswith("ERP-")
    assert pedido["referencia_externa"] == f"OPP-{op.id}"
    assert pedido["valor"] == "120000.00"
    assert pedido["tentativas"] == 1
    assert pedido["gerado_em"] is not None
    assert len(espiao_erp.chamadas) == 1


@pytest.mark.django_db
def test_repeticao_devolve_o_mesmo_pedido_sem_chamar_o_erp(api, criar_oportunidade, espiao_erp):
    op = criar_oportunidade(estagio="GANHO")
    primeiro = api.post(url(op.id))
    segundo = api.post(url(op.id))
    terceiro = api.post(url(op.id))
    assert primeiro.status_code == 201
    assert segundo.status_code == 200
    assert terceiro.status_code == 200
    assert segundo.json()["id"] == primeiro.json()["id"] == terceiro.json()["id"]
    assert segundo.json()["numero_erp"] == primeiro.json()["numero_erp"]
    assert len(espiao_erp.chamadas) == 1
    assert Pedido.objects.filter(oportunidade=op).count() == 1


@pytest.mark.django_db
def test_detalhe_mostra_o_pedido(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO")
    api.post(url(op.id))
    pedido = api.get(f"/api/oportunidades/{op.id}").json()["pedido"]
    assert pedido["status"] == "GERADO"


@pytest.mark.django_db(transaction=True)
def test_10_requisicoes_simultaneas_geram_um_unico_pedido(criar_oportunidade, espiao_erp, settings):
    # Latência no ERP para que as threads realmente disputem o lock durante a chamada.
    settings.ERP_LATENCIA_MS = 50
    op = criar_oportunidade(estagio="GANHO")
    barreira = threading.Barrier(10)
    resultados: list = []
    erros: list = []

    def gerar():
        try:
            barreira.wait()
            resultados.append(servico_pedidos.gerar_pedido(op.id))
        except Exception as exc:  # noqa: BLE001 - o teste precisa ver qualquer falha
            erros.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=gerar) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert erros == []
    assert Pedido.objects.filter(oportunidade=op).count() == 1
    assert sum(1 for _, criado in resultados if criado) == 1
    assert len({pedido.id for pedido, _ in resultados}) == 1
    assert len(espiao_erp.chamadas) == 1


@pytest.mark.django_db(transaction=True)
def test_10_retries_simultaneos_chamam_o_erp_uma_vez(criar_oportunidade, espiao_erp, settings):
    # Aqui já existe o pedido FALHOU: não há INSERT para a constraint barrar, então quem
    # serializa as tentativas é o lock na oportunidade.
    op = criar_oportunidade(estagio="GANHO")
    settings.ERP_MODO = "erro"
    with pytest.raises(Exception):
        servico_pedidos.gerar_pedido(op.id)
    espiao_erp.chamadas.clear()

    settings.ERP_MODO = "sucesso"
    settings.ERP_LATENCIA_MS = 50
    barreira = threading.Barrier(10)
    resultados: list = []
    erros: list = []

    def repetir():
        try:
            barreira.wait()
            resultados.append(servico_pedidos.gerar_pedido(op.id))
        except Exception as exc:  # noqa: BLE001
            erros.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=repetir) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert erros == []
    assert len(espiao_erp.chamadas) == 1
    assert sum(1 for _, criado in resultados if criado) == 1
    pedido = Pedido.objects.get(oportunidade=op)
    assert pedido.status == "GERADO"
    assert pedido.tentativas == 2


@pytest.mark.django_db
def test_integrity_error_devolve_o_pedido_existente(api, criar_oportunidade, monkeypatch):
    op = criar_oportunidade(estagio="GANHO")
    existente = Pedido.objects.create(
        oportunidade=op,
        referencia_externa=Pedido.referencia_para(op.id),
        valor=Decimal("1000.00"),
        status="GERADO",
        numero_erp="ERP-1",
        tentativas=1,
        gerado_em=op.criado_em,
    )

    # Simula a corrida: a leitura não vê o pedido e a criação esbarra na constraint.
    monkeypatch.setattr(servico_pedidos, "_pedido_da_oportunidade", lambda oportunidade: None)

    def criar_duplicado(oportunidade):
        raise IntegrityError("duplicate key value violates unique constraint")

    monkeypatch.setattr(servico_pedidos, "_criar_pedido", criar_duplicado)

    r = api.post(url(op.id))
    assert r.status_code == 200
    assert r.json()["id"] == existente.id
    assert Pedido.objects.count() == 1
