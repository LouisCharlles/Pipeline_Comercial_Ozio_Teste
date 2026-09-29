from django.db.models import Count, Q, QuerySet

from comercial.models import Estagio, Oportunidade


def filtrar_oportunidades(estagio: str | None, q: str | None) -> tuple[QuerySet, dict[str, int], int]:
    """Listagem com filtro e busca. Devolve (resultados, contagens, total_cadastradas).

    As contagens aplicam a busca mas ignoram o filtro de estágio: cada chip mostra quantos
    resultados da busca existem naquele estágio (research R7).
    """
    base = Oportunidade.objects.all()
    total_cadastradas = base.count()

    q = (q or "").strip()
    if q:
        base = base.filter(Q(titulo__icontains=q) | Q(empresa__nome__icontains=q))

    por_estagio = dict(base.order_by().values_list("estagio").annotate(total=Count("id")))
    contagens = {"TODOS": sum(por_estagio.values()), **{e.value: por_estagio.get(e.value, 0) for e in Estagio}}

    resultados = base.select_related("empresa", "pedido")
    if estagio in Estagio.values:
        resultados = resultados.filter(estagio=estagio)

    return resultados, contagens, total_cadastradas
