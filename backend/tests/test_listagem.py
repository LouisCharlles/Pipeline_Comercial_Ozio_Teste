"""Filtro por estágio, busca e contagens da listagem (FR-014 a FR-018, SC-005)."""

import time
from decimal import Decimal

import pytest

from comercial.models import Empresa, Oportunidade

pytestmark = pytest.mark.django_db

URL = "/api/oportunidades"


@pytest.fixture
def dados(criar_oportunidade, criar_empresa):
    horizonte = criar_empresa("Horizonte Tech")
    acme = criar_empresa("Acme Logística")
    return {
        "logistica": criar_oportunidade(titulo="Contrato de Logística 2026", empresa=acme, estagio="CONTATO"),
        "frotas": criar_oportunidade(titulo="Gestão de Frotas", empresa=acme, estagio="GANHO"),
        "erp": criar_oportunidade(titulo="Implementação de ERP", empresa=horizonte, estagio="GANHO"),
        "datacenter": criar_oportunidade(titulo="Expansão de Data Center", empresa=horizonte, estagio="PROPOSTA"),
    }


def titulos(resposta) -> set[str]:
    return {o["titulo"] for o in resposta.json()["resultados"]}


def test_filtra_por_estagio(api, dados):
    assert titulos(api.get(URL, {"estagio": "GANHO"})) == {"Gestão de Frotas", "Implementação de ERP"}


def test_estagio_invalido_e_ignorado(api, dados):
    assert len(api.get(URL, {"estagio": "QUALQUER"}).json()["resultados"]) == 4


def test_busca_pelo_nome_da_empresa(api, dados):
    assert titulos(api.get(URL, {"q": "horizonte"})) == {"Implementação de ERP", "Expansão de Data Center"}


def test_busca_pelo_titulo_sem_diferenciar_maiusculas(api, dados):
    assert titulos(api.get(URL, {"q": "LOGÍST"})) == {"Contrato de Logística 2026", "Gestão de Frotas"}


def test_busca_ignora_espacos_nas_pontas(api, dados):
    assert titulos(api.get(URL, {"q": "  frotas  "})) == {"Gestão de Frotas"}


@pytest.mark.parametrize("q", ["", "   "])
def test_busca_vazia_nao_filtra(api, dados, q):
    assert len(api.get(URL, {"q": q}).json()["resultados"]) == 4


def test_estagio_e_busca_combinados(api, dados):
    assert titulos(api.get(URL, {"estagio": "GANHO", "q": "acme"})) == {"Gestão de Frotas"}


def test_contagens_aplicam_a_busca_e_ignoram_o_estagio(api, dados):
    corpo = api.get(URL, {"estagio": "GANHO", "q": "horizonte"}).json()
    assert corpo["contagens"] == {"TODOS": 2, "LEAD": 0, "CONTATO": 0, "PROPOSTA": 1, "GANHO": 1, "PERDIDO": 0}
    assert len(corpo["resultados"]) == 1


def test_total_cadastradas_ignora_filtros(api, dados):
    corpo = api.get(URL, {"q": "nada-disso"}).json()
    assert corpo["resultados"] == []
    assert corpo["contagens"]["TODOS"] == 0
    assert corpo["total_cadastradas"] == 4


def test_ordenada_pela_atualizacao_mais_recente(api, dados):
    dados["logistica"].titulo = "Contrato de Logística 2027"
    dados["logistica"].save()
    assert api.get(URL).json()["resultados"][0]["titulo"] == "Contrato de Logística 2027"


def test_1000_oportunidades_poucas_queries_e_rapida(api, django_assert_max_num_queries):
    empresas = Empresa.objects.bulk_create([Empresa(nome=f"Empresa {i}") for i in range(50)])
    Oportunidade.objects.bulk_create(
        [
            Oportunidade(titulo=f"Oportunidade {i}", empresa=empresas[i % 50], valor=Decimal(i), estagio="LEAD")
            for i in range(1000)
        ]
    )
    with django_assert_max_num_queries(3):
        inicio = time.perf_counter()
        r = api.get(URL, {"q": "oportunidade 1"})
        duracao = time.perf_counter() - inicio
    assert r.status_code == 200
    assert duracao < 1.0
