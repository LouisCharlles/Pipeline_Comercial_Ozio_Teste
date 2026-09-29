"""Interface da integração com o ERP.

O restante do sistema só conhece `ClienteErp`, `RespostaErp`, as exceções de `erp.erros` e
`obter_cliente_erp()`. Trocar o simulador por um ERP real significa trocar só esta função.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from django.conf import settings

from erp.erros import ErpRespostaInvalida


@dataclass(frozen=True)
class RespostaErp:
    numero: str


class ClienteErp(Protocol):
    def criar_pedido(self, referencia: str, valor: Decimal) -> RespostaErp:
        """Cria o pedido no ERP. Levanta ErpTempoEsgotado, ErpErroServico ou ErpRespostaInvalida.

        `referencia` identifica a oportunidade e se repete em toda nova tentativa, para que o ERP
        reconheça um pedido que ele já criou (ex.: depois de um tempo esgotado).
        """
        ...


def validar_resposta(bruta: object, referencia: str) -> RespostaErp:
    """Confere o contrato {"numero_pedido": str não vazio, "referencia": igual à enviada}."""
    if not isinstance(bruta, dict):
        raise ErpRespostaInvalida(f"Resposta do ERP não é um objeto: {bruta!r}")
    numero = bruta.get("numero_pedido")
    if not isinstance(numero, str) or not numero.strip():
        raise ErpRespostaInvalida(f"Resposta do ERP sem número de pedido válido: {bruta!r}")
    if bruta.get("referencia") != referencia:
        raise ErpRespostaInvalida(
            f"Resposta do ERP com referência {bruta.get('referencia')!r}, esperada {referencia!r}"
        )
    return RespostaErp(numero=numero.strip())


def obter_cliente_erp() -> ClienteErp:
    from erp.simulado import ErpSimulado

    return ErpSimulado(timeout_segundos=settings.ERP_TIMEOUT_SEGUNDOS)
