from django.db import IntegrityError, transaction

from comercial.models import Empresa


def normalizar_nome(nome: str) -> str:
    return nome.strip()


def obter_ou_criar_por_nome(nome: str) -> Empresa:
    """Reaproveita a empresa com o mesmo nome (sem diferenciar maiúsculas) ou cria uma nova."""
    nome = normalizar_nome(nome)
    existente = Empresa.objects.filter(nome__iexact=nome).first()
    if existente:
        return existente
    try:
        with transaction.atomic():
            return Empresa.objects.create(nome=nome)
    except IntegrityError:
        # Outra requisição criou a mesma empresa entre a busca e o insert.
        return Empresa.objects.get(nome__iexact=nome)


def sugerir(q: str, limite: int = 10):
    q = (q or "").strip()
    if not q:
        return Empresa.objects.none()
    return Empresa.objects.filter(nome__icontains=q).order_by("nome")[:limite]
