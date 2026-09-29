from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from comercial.models import ESTAGIOS_FINAIS, Empresa, Oportunidade


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def criar_empresa(db):
    def _criar(nome: str = "Acme") -> Empresa:
        return Empresa.objects.create(nome=nome)

    return _criar


@pytest.fixture
def criar_oportunidade(db, criar_empresa):
    def _criar(
        titulo: str = "Op",
        empresa: Empresa | None = None,
        valor: Decimal | None = Decimal("1000.00"),
        estagio: str = "LEAD",
        motivo_perda: str = "",
    ) -> Oportunidade:
        if empresa is None:
            empresa = Empresa.objects.filter(nome__iexact="Acme").first() or criar_empresa("Acme")
        return Oportunidade.objects.create(
            titulo=titulo,
            empresa=empresa,
            valor=valor,
            estagio=estagio,
            motivo_perda=motivo_perda,
            fechado_em=timezone.now() if estagio in ESTAGIOS_FINAIS else None,
        )

    return _criar


class EspiaoErp:
    """Envolve o cliente real do ERP contando chamadas; pode forçar uma exceção."""

    def __init__(self, real):
        self.real = real
        self.chamadas: list[tuple[str, Decimal]] = []
        self.levantar: BaseException | None = None

    def criar_pedido(self, referencia, valor):
        self.chamadas.append((referencia, valor))
        if self.levantar is not None:
            raise self.levantar
        return self.real.criar_pedido(referencia, valor)


@pytest.fixture
def espiao_erp(monkeypatch):
    # Importado aqui: o pacote erp só é usado pelos testes da US2.
    from erp.cliente import obter_cliente_erp

    espiao = EspiaoErp(obter_cliente_erp())
    # O alvo é o nome no módulo que o usa, não erp.cliente.
    monkeypatch.setattr("comercial.services.pedidos.obter_cliente_erp", lambda: espiao)
    return espiao
