from decimal import Decimal

import pytest

from erp.cliente import RespostaErp, obter_cliente_erp, validar_resposta
from erp.erros import ErpErroServico, ErpRespostaInvalida, ErpTempoEsgotado
from erp.simulado import ErpSimulado


@pytest.fixture(autouse=True)
def limpar_simulador():
    ErpSimulado.limpar()
    yield
    ErpSimulado.limpar()


def test_sucesso_devolve_numero(settings):
    settings.ERP_MODO = "sucesso"
    resposta = obter_cliente_erp().criar_pedido("OPP-1", Decimal("10.00"))
    assert isinstance(resposta, RespostaErp)
    assert resposta.numero.startswith("ERP-")


def test_mesma_referencia_devolve_mesmo_numero(settings):
    settings.ERP_MODO = "sucesso"
    cliente = obter_cliente_erp()
    primeiro = cliente.criar_pedido("OPP-1", Decimal("10.00"))
    segundo = obter_cliente_erp().criar_pedido("OPP-1", Decimal("10.00"))
    outro = cliente.criar_pedido("OPP-2", Decimal("10.00"))
    assert primeiro.numero == segundo.numero
    assert outro.numero != primeiro.numero


@pytest.mark.parametrize(
    ("modo", "excecao"),
    [
        ("timeout", ErpTempoEsgotado),
        ("erro", ErpErroServico),
        ("resposta_invalida", ErpRespostaInvalida),
        ("desconhecido", ErpErroServico),
    ],
)
def test_modos_de_falha(settings, modo, excecao):
    settings.ERP_MODO = modo
    with pytest.raises(excecao):
        obter_cliente_erp().criar_pedido("OPP-1", Decimal("10.00"))


def test_modo_lido_a_cada_chamada(settings):
    cliente = obter_cliente_erp()
    settings.ERP_MODO = "erro"
    with pytest.raises(ErpErroServico):
        cliente.criar_pedido("OPP-1", Decimal("10.00"))
    settings.ERP_MODO = "sucesso"
    assert cliente.criar_pedido("OPP-1", Decimal("10.00")).numero


def test_timeout_cita_o_limite(settings):
    settings.ERP_MODO = "timeout"
    settings.ERP_TIMEOUT_SEGUNDOS = 7
    with pytest.raises(ErpTempoEsgotado, match="7s"):
        obter_cliente_erp().criar_pedido("OPP-1", Decimal("10.00"))


@pytest.mark.parametrize(
    "bruta",
    [
        {"referencia": "OPP-1"},
        {"numero_pedido": "", "referencia": "OPP-1"},
        {"numero_pedido": "   ", "referencia": "OPP-1"},
        {"numero_pedido": 123, "referencia": "OPP-1"},
        {"numero_pedido": "ERP-1", "referencia": "OPP-2"},
        {"numero_pedido": "ERP-1"},
        "texto",
        None,
    ],
)
def test_validar_resposta_recusa_formato_errado(bruta):
    with pytest.raises(ErpRespostaInvalida):
        validar_resposta(bruta, "OPP-1")


def test_validar_resposta_aceita_contrato():
    assert validar_resposta({"numero_pedido": "ERP-9", "referencia": "OPP-1"}, "OPP-1") == RespostaErp(numero="ERP-9")
