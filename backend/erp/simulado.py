"""ERP simulado, determinístico, controlado por settings.ERP_MODO.

Modos: sucesso | timeout | erro | resposta_invalida. O modo é lido a cada chamada.

Como um ERP real idempotente, devolve sempre o mesmo número para a mesma referência. O número é
derivado da referência (e não de um contador em memória), então continua único e estável mesmo
depois de o processo reiniciar.
"""

import hashlib
import time
from decimal import Decimal

from django.conf import settings

from erp.cliente import RespostaErp, validar_resposta
from erp.erros import ErpErroServico, ErpTempoEsgotado


def numero_para(referencia: str) -> str:
    return "ERP-" + hashlib.sha1(referencia.encode()).hexdigest()[:8].upper()


class ErpSimulado:
    def __init__(self, timeout_segundos: int):
        self.timeout_segundos = timeout_segundos

    def criar_pedido(self, referencia: str, valor: Decimal) -> RespostaErp:
        if settings.ERP_LATENCIA_MS:
            time.sleep(settings.ERP_LATENCIA_MS / 1000)

        modo = settings.ERP_MODO
        if modo == "timeout":
            raise ErpTempoEsgotado(f"ERP não respondeu em {self.timeout_segundos}s")
        if modo == "erro":
            raise ErpErroServico("ERP respondeu 503 Service Unavailable")
        if modo == "resposta_invalida":
            # Resposta fora do contrato (sem número); quem detecta é a validação do cliente.
            return validar_resposta({"referencia": referencia}, referencia)
        if modo != "sucesso":
            raise ErpErroServico(f"Modo do ERP simulado desconhecido: {modo!r}")

        return validar_resposta({"numero_pedido": numero_para(referencia), "referencia": referencia}, referencia)
