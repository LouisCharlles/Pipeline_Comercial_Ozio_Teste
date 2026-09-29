"""Mudança de estágio com as regras de transição (data-model.md, "Estágios e transições")."""

from django.db import transaction
from django.utils import timezone

from comercial.erros import EstagioBloqueado, NaoEncontrado, TransicaoInvalida
from comercial.models import ESTAGIOS_ABERTOS, ESTAGIOS_FINAIS, Estagio, Oportunidade, Pedido, StatusPedido

# Destinos permitidos a partir de cada estágio (o bloqueio por pedido gerado é à parte).
TRANSICOES: dict[str, frozenset[str]] = {
    **{aberto: frozenset(Estagio.values) - {aberto} for aberto in ESTAGIOS_ABERTOS},
    Estagio.GANHO: frozenset(ESTAGIOS_ABERTOS | {Estagio.PERDIDO}),
    Estagio.PERDIDO: frozenset(ESTAGIOS_ABERTOS),
}


def mudar_estagio(oportunidade_id: int, destino: str, motivo_perda: str = "") -> Oportunidade:
    with transaction.atomic():
        # O mesmo lock usado em gerar_pedido: mudança de estágio e geração nunca correm juntas.
        try:
            oportunidade = Oportunidade.objects.select_for_update().get(pk=oportunidade_id)
        except Oportunidade.DoesNotExist:
            raise NaoEncontrado()

        origem = oportunidade.estagio
        if destino == origem:
            return oportunidade

        if Pedido.objects.filter(oportunidade=oportunidade, status=StatusPedido.GERADO).exists():
            raise EstagioBloqueado()

        if destino not in TRANSICOES[origem]:
            raise TransicaoInvalida(
                f"Não é possível mudar de {Estagio(origem).label} para {Estagio(destino).label}. "
                "Reabra a oportunidade antes."
            )

        oportunidade.estagio = destino
        oportunidade.fechado_em = timezone.now() if destino in ESTAGIOS_FINAIS else None
        oportunidade.motivo_perda = motivo_perda.strip() if destino == Estagio.PERDIDO else ""
        oportunidade.save()
        return oportunidade
