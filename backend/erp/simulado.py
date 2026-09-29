"""ERP simulado, determinístico, controlado por settings.ERP_MODO.

Modos: sucesso | timeout | erro | resposta_invalida. O modo é lido a cada chamada.
Como um ERP real idempotente, devolve o mesmo número para a mesma referência.
"""

import threading
import time
from decimal import Decimal

from django.conf import settings

from erp.cliente import RespostaErp, validar_resposta
from erp.erros import ErpErroServico, ErpTempoEsgotado


class ErpSimulado:
    # Estado do "ERP" compartilhado por todas as instâncias do processo.
    _pedidos: dict[str, str] = {}
    _proximo = 2000
    _lock = threading.Lock()

    def __init__(self, timeout_segundos: int):
        self.timeout_segundos = timeout_segundos

    @classmethod
    def limpar(cls) -> None:
        with cls._lock:
            cls._pedidos.clear()
            cls._proximo = 2000

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

        with self._lock:
            numero = self._pedidos.get(referencia)
            if numero is None:
                numero = f"ERP-{ErpSimulado._proximo}"
                ErpSimulado._proximo += 1
                self._pedidos[referencia] = numero
        return validar_resposta({"numero_pedido": numero, "referencia": referencia}, referencia)
