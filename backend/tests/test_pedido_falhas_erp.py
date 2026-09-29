"""Falhas do ERP: tratadas de forma distinta, sem dado inconsistente, com retry seguro (Princípio IV)."""

from decimal import Decimal

import pytest

from comercial.models import Pedido
from erp.simulado import ErpSimulado

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def erp_limpo(settings):
    settings.ERP_MODO = "sucesso"
    ErpSimulado.limpar()
    yield
    ErpSimulado.limpar()


def url(op_id: int) -> str:
    return f"/api/oportunidades/{op_id}/pedido"


FALHAS = [
    ("timeout", 504, "erp_tempo_esgotado", "TEMPO_ESGOTADO"),
    ("erro", 502, "erp_erro_servico", "ERRO_SERVICO"),
    ("resposta_invalida", 502, "erp_resposta_invalida", "RESPOSTA_INVALIDA"),
]


@pytest.mark.parametrize(("modo", "status_http", "codigo", "tipo"), FALHAS)
def test_falha_registrada_sem_dado_parcial(api, criar_oportunidade, settings, modo, status_http, codigo, tipo):
    settings.ERP_MODO = modo
    op = criar_oportunidade(estagio="GANHO")

    r = api.post(url(op.id))

    assert r.status_code == status_http
    corpo = r.json()
    assert corpo["codigo"] == codigo
    assert corpo["mensagem"]
    assert corpo["pedido"]["status"] == "FALHOU"
    assert corpo["pedido"]["tentativas"] == 1
    assert corpo["pedido"]["numero_erp"] is None
    assert corpo["pedido"]["ultimo_erro_tipo"] == tipo
    assert corpo["pedido"]["ultimo_erro"]

    pedido = Pedido.objects.get(oportunidade=op)
    assert pedido.status == "FALHOU"
    assert pedido.numero_erp is None
    assert pedido.gerado_em is None


@pytest.mark.parametrize(("modo", "status_http", "codigo", "tipo"), FALHAS)
def test_retry_conclui_sobre_o_mesmo_registro(api, criar_oportunidade, settings, modo, status_http, codigo, tipo):
    settings.ERP_MODO = modo
    op = criar_oportunidade(estagio="GANHO", valor=Decimal("95000"))
    falha = api.post(url(op.id)).json()["pedido"]

    settings.ERP_MODO = "sucesso"
    r = api.post(url(op.id))

    assert r.status_code == 201
    pedido = r.json()
    assert pedido["id"] == falha["id"]
    assert pedido["referencia_externa"] == falha["referencia_externa"]
    assert pedido["status"] == "GERADO"
    assert pedido["tentativas"] == 2
    assert pedido["ultimo_erro"] == ""
    assert pedido["ultimo_erro_tipo"] == ""
    assert Pedido.objects.count() == 1


def test_varias_falhas_somam_tentativas(api, criar_oportunidade, settings):
    settings.ERP_MODO = "erro"
    op = criar_oportunidade(estagio="GANHO")
    api.post(url(op.id))
    settings.ERP_MODO = "timeout"
    r = api.post(url(op.id))
    assert r.json()["pedido"]["tentativas"] == 2
    assert r.json()["pedido"]["ultimo_erro_tipo"] == "TEMPO_ESGOTADO"
    assert Pedido.objects.count() == 1


def test_retry_mantem_o_valor_copiado_na_primeira_tentativa(api, criar_oportunidade, settings):
    settings.ERP_MODO = "timeout"
    op = criar_oportunidade(estagio="GANHO", valor=Decimal("1000"))
    api.post(url(op.id))

    api.patch(f"/api/oportunidades/{op.id}", {"valor": "5000"}, format="json")
    settings.ERP_MODO = "sucesso"
    r = api.post(url(op.id))

    assert r.status_code == 201
    assert r.json()["valor"] == "1000.00"


def test_pedido_gerado_mantem_valor_apos_edicao(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO", valor=Decimal("1000"))
    api.post(url(op.id))
    api.patch(f"/api/oportunidades/{op.id}", {"valor": "5000"}, format="json")
    detalhe = api.get(f"/api/oportunidades/{op.id}").json()
    assert detalhe["valor"] == "5000.00"
    assert detalhe["pedido"]["valor"] == "1000.00"


@pytest.mark.parametrize("estagio", ["LEAD", "CONTATO", "PROPOSTA", "PERDIDO"])
def test_fora_de_ganho_nao_chama_o_erp(api, criar_oportunidade, espiao_erp, estagio):
    op = criar_oportunidade(estagio=estagio)
    r = api.post(url(op.id))
    assert r.status_code == 409
    assert r.json()["codigo"] == "estagio_invalido"
    assert espiao_erp.chamadas == []
    assert Pedido.objects.count() == 0


@pytest.mark.parametrize("valor", [None, Decimal("0")])
def test_sem_valor_nao_chama_o_erp(api, criar_oportunidade, espiao_erp, valor):
    op = criar_oportunidade(estagio="GANHO", valor=valor)
    r = api.post(url(op.id))
    assert r.status_code == 409
    assert r.json()["codigo"] == "valor_obrigatorio"
    assert r.json()["mensagem"] == "Informe um valor maior que zero antes de gerar o pedido."
    assert espiao_erp.chamadas == []
    assert Pedido.objects.count() == 0


def test_oportunidade_inexistente(api):
    r = api.post(url(99999))
    assert r.status_code == 404
    assert r.json()["codigo"] == "nao_encontrado"


def test_falha_permanece_se_oportunidade_sai_e_volta_para_ganho(api, criar_oportunidade, settings):
    settings.ERP_MODO = "erro"
    op = criar_oportunidade(estagio="GANHO")
    falha = api.post(url(op.id)).json()["pedido"]

    op.estagio = "PROPOSTA"
    op.fechado_em = None
    op.save()
    assert api.post(url(op.id)).status_code == 409

    op.estagio = "GANHO"
    op.fechado_em = op.atualizado_em
    op.save()
    settings.ERP_MODO = "sucesso"
    r = api.post(url(op.id))
    assert r.status_code == 201
    assert r.json()["id"] == falha["id"]


def test_interrupcao_desfaz_a_tentativa(api, criar_oportunidade, espiao_erp):
    op = criar_oportunidade(estagio="GANHO")
    espiao_erp.levantar = RuntimeError("processo interrompido")

    r = api.post(url(op.id))

    assert r.status_code == 500
    assert r.json()["codigo"] == "erro_interno"
    assert Pedido.objects.count() == 0

    espiao_erp.levantar = None
    r = api.post(url(op.id))
    assert r.status_code == 201
    assert r.json()["tentativas"] == 1


def test_interrupcao_apos_falha_mantem_a_falha_anterior(api, criar_oportunidade, espiao_erp, settings):
    settings.ERP_MODO = "erro"
    op = criar_oportunidade(estagio="GANHO")
    api.post(url(op.id))

    espiao_erp.levantar = RuntimeError("processo interrompido")
    assert api.post(url(op.id)).status_code == 500

    pedido = Pedido.objects.get(oportunidade=op)
    assert pedido.status == "FALHOU"
    assert pedido.tentativas == 1
