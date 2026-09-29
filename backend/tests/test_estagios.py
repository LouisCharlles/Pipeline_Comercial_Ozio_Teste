"""Regras de transição de estágio, aplicadas pelo backend (FR-007 a FR-013)."""

from decimal import Decimal

import pytest
from django.utils import timezone

from comercial.models import Oportunidade, Pedido

pytestmark = pytest.mark.django_db

ABERTOS = ["LEAD", "CONTATO", "PROPOSTA"]


def mudar(api, op_id: int, estagio: str, **extra):
    return api.post(f"/api/oportunidades/{op_id}/estagio", {"estagio": estagio, **extra}, format="json")


def criar_pedido(op: Oportunidade, status: str) -> Pedido:
    gerado = status == "GERADO"
    return Pedido.objects.create(
        oportunidade=op,
        referencia_externa=Pedido.referencia_para(op.id),
        valor=Decimal("1000.00"),
        status=status,
        numero_erp="ERP-1" if gerado else None,
        gerado_em=timezone.now() if gerado else None,
        tentativas=1,
    )


@pytest.mark.parametrize("origem", ABERTOS)
@pytest.mark.parametrize("destino", ABERTOS)
def test_livre_entre_abertos(api, criar_oportunidade, origem, destino):
    op = criar_oportunidade(estagio=origem)
    r = mudar(api, op.id, destino)
    assert r.status_code == 200
    assert r.json()["estagio"] == destino
    assert r.json()["fechado_em"] is None


@pytest.mark.parametrize("origem", ABERTOS)
def test_aberto_para_ganho_registra_fechamento(api, criar_oportunidade, origem):
    op = criar_oportunidade(estagio=origem)
    r = mudar(api, op.id, "GANHO")
    assert r.status_code == 200
    assert r.json()["estagio"] == "GANHO"
    assert r.json()["fechado_em"] is not None


def test_aberto_para_perdido_com_motivo(api, criar_oportunidade):
    op = criar_oportunidade(estagio="PROPOSTA")
    r = mudar(api, op.id, "PERDIDO", motivo_perda="  Preço acima do concorrente  ")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["estagio"] == "PERDIDO"
    assert corpo["motivo_perda"] == "Preço acima do concorrente"
    assert corpo["fechado_em"] is not None


def test_perdido_sem_motivo(api, criar_oportunidade):
    op = criar_oportunidade(estagio="LEAD")
    r = mudar(api, op.id, "PERDIDO")
    assert r.status_code == 200
    assert r.json()["motivo_perda"] == ""


def test_reabrir_perdido_limpa_fechamento_e_motivo(api, criar_oportunidade):
    op = criar_oportunidade(estagio="PERDIDO", motivo_perda="Sem orçamento")
    r = mudar(api, op.id, "CONTATO")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["estagio"] == "CONTATO"
    assert corpo["fechado_em"] is None
    assert corpo["motivo_perda"] == ""


def test_perdido_para_ganho_e_recusado(api, criar_oportunidade):
    op = criar_oportunidade(estagio="PERDIDO", motivo_perda="Sem orçamento")
    r = mudar(api, op.id, "GANHO")
    assert r.status_code == 409
    assert r.json()["codigo"] == "transicao_invalida"
    assert "Perdido" in r.json()["mensagem"] and "Ganho" in r.json()["mensagem"]
    op.refresh_from_db()
    assert op.estagio == "PERDIDO"
    assert op.motivo_perda == "Sem orçamento"


def test_ganho_sem_pedido_reabre(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO")
    r = mudar(api, op.id, "PROPOSTA")
    assert r.status_code == 200
    assert r.json()["fechado_em"] is None


def test_ganho_sem_pedido_para_perdido(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO")
    r = mudar(api, op.id, "PERDIDO", motivo_perda="Cliente desistiu")
    assert r.status_code == 200
    assert r.json()["estagio"] == "PERDIDO"
    assert r.json()["motivo_perda"] == "Cliente desistiu"


@pytest.mark.parametrize("destino", ["LEAD", "CONTATO", "PROPOSTA", "PERDIDO"])
def test_ganho_com_pedido_gerado_fica_bloqueado(api, criar_oportunidade, destino):
    op = criar_oportunidade(estagio="GANHO")
    criar_pedido(op, "GERADO")
    r = mudar(api, op.id, destino)
    assert r.status_code == 409
    assert r.json()["codigo"] == "estagio_bloqueado"
    assert r.json()["mensagem"] == "Oportunidade com pedido gerado não pode mudar de estágio."
    op.refresh_from_db()
    assert op.estagio == "GANHO"


def test_ganho_com_pedido_falhou_pode_sair_e_mantem_a_falha(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO")
    pedido = criar_pedido(op, "FALHOU")
    r = mudar(api, op.id, "PROPOSTA")
    assert r.status_code == 200
    assert r.json()["pedido"]["id"] == pedido.id
    assert r.json()["pedido"]["status"] == "FALHOU"


def test_mesmo_estagio_nao_altera(api, criar_oportunidade):
    op = criar_oportunidade(estagio="GANHO")
    fechado_antes = op.fechado_em
    r = mudar(api, op.id, "GANHO")
    assert r.status_code == 200
    op.refresh_from_db()
    assert op.fechado_em == fechado_antes


def test_estagio_desconhecido(api, criar_oportunidade):
    op = criar_oportunidade()
    r = mudar(api, op.id, "ARQUIVADO")
    assert r.status_code == 400
    assert r.json()["codigo"] == "validacao"
    assert "estagio" in r.json()["campos"]


def test_estagio_ausente(api, criar_oportunidade):
    op = criar_oportunidade()
    r = api.post(f"/api/oportunidades/{op.id}/estagio", {}, format="json")
    assert r.status_code == 400
    assert "estagio" in r.json()["campos"]


def test_motivo_ignorado_fora_de_perdido(api, criar_oportunidade):
    op = criar_oportunidade(estagio="LEAD")
    r = mudar(api, op.id, "CONTATO", motivo_perda="não se aplica")
    assert r.status_code == 200
    assert r.json()["motivo_perda"] == ""


def test_motivo_longo_demais(api, criar_oportunidade):
    op = criar_oportunidade(estagio="LEAD")
    r = mudar(api, op.id, "PERDIDO", motivo_perda="x" * 501)
    assert r.status_code == 400
    assert "motivo_perda" in r.json()["campos"]
    op.refresh_from_db()
    assert op.estagio == "LEAD"


def test_oportunidade_inexistente(api):
    r = mudar(api, 99999, "CONTATO")
    assert r.status_code == 404
