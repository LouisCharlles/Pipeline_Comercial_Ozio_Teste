"""Endpoints REST. Views finas: validam a entrada e delegam regras aos serviços."""

from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from comercial.erros import NaoEncontrado
from comercial.models import Estagio, Oportunidade
from comercial.serializers import (
    EmpresaSerializer,
    MudarEstagioSerializer,
    OportunidadeCriacaoSerializer,
    OportunidadeEdicaoSerializer,
    OportunidadeResumoSerializer,
    OportunidadeSerializer,
    PedidoSerializer,
)
from comercial.services import empresas, estagios, pedidos


def _obter_oportunidade(pk: int) -> Oportunidade:
    try:
        return Oportunidade.objects.select_related("empresa", "pedido").get(pk=pk)
    except Oportunidade.DoesNotExist:
        raise NaoEncontrado()


class OportunidadeListaView(APIView):
    def get(self, request):
        qs = Oportunidade.objects.select_related("empresa", "pedido")
        por_estagio = dict(qs.order_by().values_list("estagio").annotate(total=Count("id")))
        contagens = {e.value: por_estagio.get(e.value, 0) for e in Estagio}
        total = sum(contagens.values())
        return Response(
            {
                "resultados": OportunidadeResumoSerializer(qs, many=True).data,
                "contagens": {"TODOS": total, **contagens},
                "total_cadastradas": total,
            }
        )

    def post(self, request):
        entrada = OportunidadeCriacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        oportunidade = entrada.save()
        return Response(OportunidadeSerializer(_obter_oportunidade(oportunidade.pk)).data, status=status.HTTP_201_CREATED)


class OportunidadeDetalheView(APIView):
    def get(self, request, pk: int):
        return Response(OportunidadeSerializer(_obter_oportunidade(pk)).data)

    def patch(self, request, pk: int):
        oportunidade = _obter_oportunidade(pk)
        entrada = OportunidadeEdicaoSerializer(oportunidade, data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        entrada.save()
        return Response(OportunidadeSerializer(_obter_oportunidade(pk)).data)


class MudarEstagioView(APIView):
    def post(self, request, pk: int):
        entrada = MudarEstagioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        estagios.mudar_estagio(pk, entrada.validated_data["estagio"], entrada.validated_data["motivo_perda"])
        return Response(OportunidadeSerializer(_obter_oportunidade(pk)).data)


class GerarPedidoView(APIView):
    def post(self, request, pk: int):
        pedido, criado = pedidos.gerar_pedido(pk)
        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)


class EmpresaSugestoesView(APIView):
    def get(self, request):
        return Response(EmpresaSerializer(empresas.sugerir(request.query_params.get("q", "")), many=True).data)
