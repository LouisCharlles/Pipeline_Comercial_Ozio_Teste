"""Geração do pedido no ERP, com no máximo um pedido por oportunidade.

Camadas de proteção (research R3):
1. `Pedido.oportunidade` é OneToOne: o banco recusa um segundo pedido.
2. A oportunidade fica travada (`select_for_update`) durante todo o fluxo, inclusive a chamada
   ao ERP: requisições simultâneas são atendidas uma de cada vez.
3. Se ainda assim o INSERT esbarrar na constraint, devolvemos o pedido que já existe.

O resultado de cada tentativa (GERADO ou FALHOU) é gravado na mesma transação. Se o processo
morrer no meio, o rollback desfaz a tentativa e nada fica pela metade.
"""

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from comercial.erros import (
    ErpErroServicoErro,
    ErpRespostaInvalidaErro,
    ErpTempoEsgotadoErro,
    EstagioInvalido,
    NaoEncontrado,
    ValorObrigatorio,
)
from comercial.models import Estagio, Oportunidade, Pedido, StatusPedido, TipoErroErp
from erp.cliente import obter_cliente_erp
from erp.erros import ErpErroServico, ErpRespostaInvalida, ErpTempoEsgotado, ErroErp

logger = logging.getLogger(__name__)

# Falha do ERP → (tipo gravado no pedido, erro devolvido pela API)
_FALHAS = {
    ErpTempoEsgotado: (TipoErroErp.TEMPO_ESGOTADO, ErpTempoEsgotadoErro),
    ErpErroServico: (TipoErroErp.ERRO_SERVICO, ErpErroServicoErro),
    ErpRespostaInvalida: (TipoErroErp.RESPOSTA_INVALIDA, ErpRespostaInvalidaErro),
}


def _pedido_da_oportunidade(oportunidade: Oportunidade) -> Pedido | None:
    return Pedido.objects.filter(oportunidade=oportunidade).first()


def _criar_pedido(oportunidade: Oportunidade) -> Pedido:
    return Pedido.objects.create(
        oportunidade=oportunidade,
        referencia_externa=Pedido.referencia_para(oportunidade.id),
        valor=oportunidade.valor,
        status=StatusPedido.PENDENTE,
    )


def _classificar(exc: ErroErp):
    for tipo_excecao, resultado in _FALHAS.items():
        if isinstance(exc, tipo_excecao):
            return resultado
    return TipoErroErp.ERRO_SERVICO, ErpErroServicoErro


def gerar_pedido(oportunidade_id: int) -> tuple[Pedido, bool]:
    """Gera o pedido (ou repete a tentativa). Devolve (pedido, criado_agora).

    Levanta NaoEncontrado, EstagioInvalido, ValorObrigatorio ou, depois de gravar a falha,
    ErpTempoEsgotadoErro / ErpErroServicoErro / ErpRespostaInvalidaErro com o pedido.
    """
    falha: ErroErp | None = None
    try:
        with transaction.atomic():
            try:
                oportunidade = Oportunidade.objects.select_for_update().get(pk=oportunidade_id)
            except Oportunidade.DoesNotExist:
                raise NaoEncontrado()

            pedido = _pedido_da_oportunidade(oportunidade)
            if pedido is not None and pedido.status == StatusPedido.GERADO:
                return pedido, False

            if oportunidade.estagio != Estagio.GANHO:
                raise EstagioInvalido()

            if pedido is None:
                # Na nova tentativa vale o valor copiado na primeira; aqui é a primeira.
                if oportunidade.valor is None or oportunidade.valor <= 0:
                    raise ValorObrigatorio()
                pedido = _criar_pedido(oportunidade)

            pedido.status = StatusPedido.PENDENTE
            pedido.tentativas += 1
            pedido.save()

            try:
                resposta = obter_cliente_erp().criar_pedido(pedido.referencia_externa, pedido.valor)
            except ErroErp as exc:
                tipo, _ = _classificar(exc)
                pedido.status = StatusPedido.FALHOU
                pedido.ultimo_erro_tipo = tipo
                pedido.ultimo_erro = str(exc)
                pedido.save()
                falha = exc
                logger.warning(
                    "Pedido %s: tentativa %s falhou (%s): %s",
                    pedido.referencia_externa,
                    pedido.tentativas,
                    tipo,
                    exc,
                )
            else:
                pedido.status = StatusPedido.GERADO
                pedido.numero_erp = resposta.numero
                pedido.gerado_em = timezone.now()
                pedido.ultimo_erro_tipo = TipoErroErp.NENHUM
                pedido.ultimo_erro = ""
                pedido.save()
                logger.info(
                    "Pedido %s gerado no ERP como %s (tentativa %s)",
                    pedido.referencia_externa,
                    pedido.numero_erp,
                    pedido.tentativas,
                )
                return pedido, True
    except IntegrityError:
        # Última defesa: outro processo criou o pedido; devolvemos o que existe.
        existente = Pedido.objects.filter(oportunidade_id=oportunidade_id).first()
        if existente is None:
            raise
        logger.info("Pedido %s já existia (IntegrityError tratado)", existente.referencia_externa)
        return existente, False

    # A falha já foi gravada (commit acima); agora avisamos a API.
    _, erro_api = _classificar(falha)
    raise erro_api(pedido=pedido)
