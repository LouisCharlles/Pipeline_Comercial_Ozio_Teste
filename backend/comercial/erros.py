"""Erros de domínio e conversão de exceções para o corpo de erro da API.

Todo erro controlado sai no formato {codigo, mensagem, campos?, pedido?} descrito em
specs/001-pipeline-comercial-erp/contracts/api.md.
"""

import logging

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ErroDominio(Exception):
    codigo = "erro"
    mensagem = "Erro inesperado. Tente novamente."
    status_http = status.HTTP_400_BAD_REQUEST

    def __init__(self, mensagem: str | None = None, pedido=None):
        super().__init__(mensagem or self.mensagem)
        if mensagem:
            self.mensagem = mensagem
        self.pedido = pedido


class NaoEncontrado(ErroDominio):
    codigo = "nao_encontrado"
    mensagem = "Oportunidade não encontrada."
    status_http = status.HTTP_404_NOT_FOUND


class TransicaoInvalida(ErroDominio):
    codigo = "transicao_invalida"
    mensagem = "Mudança de estágio não permitida."
    status_http = status.HTTP_409_CONFLICT


class EstagioBloqueado(ErroDominio):
    codigo = "estagio_bloqueado"
    mensagem = "Oportunidade com pedido gerado não pode mudar de estágio."
    status_http = status.HTTP_409_CONFLICT


class EstagioInvalido(ErroDominio):
    codigo = "estagio_invalido"
    mensagem = "Disponível quando a oportunidade estiver em Ganho."
    status_http = status.HTTP_409_CONFLICT


class ValorObrigatorio(ErroDominio):
    codigo = "valor_obrigatorio"
    mensagem = "Informe um valor maior que zero antes de gerar o pedido."
    status_http = status.HTTP_409_CONFLICT


class ErpTempoEsgotadoErro(ErroDominio):
    codigo = "erp_tempo_esgotado"
    mensagem = "O ERP não respondeu a tempo. Tente novamente."
    status_http = status.HTTP_504_GATEWAY_TIMEOUT


class ErpErroServicoErro(ErroDominio):
    codigo = "erp_erro_servico"
    mensagem = "O ERP retornou um erro. Tente novamente."
    status_http = status.HTTP_502_BAD_GATEWAY


class ErpRespostaInvalidaErro(ErroDominio):
    codigo = "erp_resposta_invalida"
    mensagem = "O ERP enviou uma resposta inesperada. Tente novamente."
    status_http = status.HTTP_502_BAD_GATEWAY


def _corpo(codigo: str, mensagem: str, **extras) -> dict:
    return {"codigo": codigo, "mensagem": mensagem, **extras}


def _normalizar_campos(detalhe) -> dict[str, list[str]]:
    if isinstance(detalhe, dict):
        campos = {}
        for campo, erros in detalhe.items():
            lista = erros if isinstance(erros, list) else [erros]
            campos[campo] = [str(e) for e in lista]
        return campos
    lista = detalhe if isinstance(detalhe, list) else [detalhe]
    return {"non_field_errors": [str(e) for e in lista]}


def tratar_excecao(exc, context):
    if isinstance(exc, ErroDominio):
        extras = {}
        if exc.pedido is not None:
            from .serializers import PedidoSerializer

            extras["pedido"] = PedidoSerializer(exc.pedido).data
        return Response(_corpo(exc.codigo, exc.mensagem, **extras), status=exc.status_http)

    if isinstance(exc, ValidationError):
        return Response(
            _corpo("validacao", "Corrija os campos destacados.", campos=_normalizar_campos(exc.detail)),
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ParseError):
        return Response(_corpo("validacao", "Requisição inválida."), status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (Http404, NotFound)):
        return Response(_corpo(NaoEncontrado.codigo, NaoEncontrado.mensagem), status=status.HTTP_404_NOT_FOUND)

    logger.exception("Erro não tratado na API", exc_info=exc)
    return Response(
        _corpo("erro_interno", "Erro inesperado. Tente novamente."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
