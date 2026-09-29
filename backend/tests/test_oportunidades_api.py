from decimal import Decimal

import pytest

from comercial.models import Empresa, Oportunidade

pytestmark = pytest.mark.django_db

URL = "/api/oportunidades"


def criar(api, **dados):
    corpo = {"titulo": "Contrato", "empresa": "Acme Logística", **dados}
    return api.post(URL, corpo, format="json")


class TestCriar:
    def test_cria_com_estagio_padrao_lead(self, api):
        r = criar(api, valor="75000")
        assert r.status_code == 201
        corpo = r.json()
        assert corpo["estagio"] == "LEAD"
        assert corpo["titulo"] == "Contrato"
        assert corpo["empresa"]["nome"] == "Acme Logística"
        assert corpo["valor"] == "75000.00"
        assert corpo["pedido"] is None
        assert corpo["fechado_em"] is None

    def test_aceita_estagio_aberto(self, api):
        r = criar(api, estagio="PROPOSTA")
        assert r.status_code == 201
        assert r.json()["estagio"] == "PROPOSTA"

    def test_reaproveita_empresa_sem_diferenciar_maiusculas_e_espacos(self, api, criar_empresa):
        existente = criar_empresa("Acme Logística")
        r = criar(api, empresa="  acme LOGÍSTICA ")
        assert r.status_code == 201
        assert r.json()["empresa"]["id"] == existente.id
        assert Empresa.objects.count() == 1

    def test_cria_empresa_nova(self, api, criar_empresa):
        criar_empresa("Acme Logística")
        r = criar(api, empresa="  Nova Alimentos ")
        assert r.status_code == 201
        assert r.json()["empresa"]["nome"] == "Nova Alimentos"
        assert Empresa.objects.count() == 2

    @pytest.mark.parametrize("valor", [None, ""])
    def test_valor_opcional(self, api, valor):
        r = criar(api, valor=valor)
        assert r.status_code == 201
        assert r.json()["valor"] is None

    def test_titulo_apenas_com_espacos_e_aparado(self, api):
        r = criar(api, titulo="  Renovação  ")
        assert r.status_code == 201
        assert r.json()["titulo"] == "Renovação"

    @pytest.mark.parametrize(
        ("dados", "campo", "mensagem"),
        [
            ({"titulo": ""}, "titulo", "Informe o título da oportunidade."),
            ({"titulo": "   "}, "titulo", "Informe o título da oportunidade."),
            ({"empresa": ""}, "empresa", "Informe a empresa."),
            ({"valor": "-1"}, "valor", "O valor não pode ser negativo."),
            ({"valor": "abc"}, "valor", "Informe um valor numérico."),
            ({"estagio": "GANHO"}, "estagio", "Escolha Lead, Contato ou Proposta."),
            ({"estagio": "PERDIDO"}, "estagio", "Escolha Lead, Contato ou Proposta."),
        ],
    )
    def test_validacao_por_campo(self, api, dados, campo, mensagem):
        r = criar(api, **dados)
        assert r.status_code == 400
        corpo = r.json()
        assert corpo["codigo"] == "validacao"
        assert corpo["campos"][campo] == [mensagem]
        assert Oportunidade.objects.count() == 0

    def test_campos_obrigatorios_ausentes(self, api):
        r = api.post(URL, {}, format="json")
        assert r.status_code == 400
        campos = r.json()["campos"]
        assert campos["titulo"] == ["Informe o título da oportunidade."]
        assert campos["empresa"] == ["Informe a empresa."]


class TestDetalhe:
    def test_detalhe(self, api, criar_oportunidade):
        op = criar_oportunidade(titulo="Suporte", valor=Decimal("32000"))
        r = api.get(f"{URL}/{op.id}")
        assert r.status_code == 200
        corpo = r.json()
        assert corpo["id"] == op.id
        assert corpo["empresa"] == {"id": op.empresa_id, "nome": "Acme"}
        assert corpo["valor"] == "32000.00"
        assert corpo["pedido"] is None
        for campo in ("motivo_perda", "fechado_em", "criado_em", "atualizado_em"):
            assert campo in corpo

    def test_inexistente(self, api):
        r = api.get(f"{URL}/99999")
        assert r.status_code == 404
        assert r.json()["codigo"] == "nao_encontrado"


class TestEditar:
    def test_edita_titulo_empresa_e_valor_mantendo_estagio(self, api, criar_oportunidade, criar_empresa):
        op = criar_oportunidade(estagio="PROPOSTA")
        nova = criar_empresa("Horizonte Tech")
        r = api.patch(
            f"{URL}/{op.id}",
            {"titulo": "Novo título", "empresa": "horizonte tech", "valor": "500"},
            format="json",
        )
        assert r.status_code == 200
        corpo = r.json()
        assert corpo["titulo"] == "Novo título"
        assert corpo["empresa"]["id"] == nova.id
        assert corpo["valor"] == "500.00"
        assert corpo["estagio"] == "PROPOSTA"

    def test_edita_so_campos_enviados(self, api, criar_oportunidade):
        op = criar_oportunidade(titulo="Antigo", valor=Decimal("10"))
        r = api.patch(f"{URL}/{op.id}", {"titulo": "Novo"}, format="json")
        assert r.status_code == 200
        assert r.json()["valor"] == "10.00"

    def test_cria_empresa_na_edicao(self, api, criar_oportunidade):
        op = criar_oportunidade()
        r = api.patch(f"{URL}/{op.id}", {"empresa": "Grupo Aurora"}, format="json")
        assert r.status_code == 200
        assert r.json()["empresa"]["nome"] == "Grupo Aurora"

    def test_recusa_estagio_no_corpo(self, api, criar_oportunidade):
        op = criar_oportunidade()
        r = api.patch(f"{URL}/{op.id}", {"estagio": "GANHO"}, format="json")
        assert r.status_code == 400
        assert "estagio" in r.json()["campos"]
        op.refresh_from_db()
        assert op.estagio == "LEAD"

    def test_validacao_na_edicao(self, api, criar_oportunidade):
        op = criar_oportunidade()
        r = api.patch(f"{URL}/{op.id}", {"titulo": "", "valor": "-5"}, format="json")
        assert r.status_code == 400
        assert set(r.json()["campos"]) == {"titulo", "valor"}

    def test_inexistente(self, api):
        r = api.patch(f"{URL}/99999", {"titulo": "X"}, format="json")
        assert r.status_code == 404


class TestListagemBasica:
    def test_formato(self, api, criar_oportunidade):
        criar_oportunidade(titulo="A", estagio="LEAD")
        criar_oportunidade(titulo="B", estagio="GANHO")
        r = api.get(URL)
        assert r.status_code == 200
        corpo = r.json()
        assert corpo["total_cadastradas"] == 2
        assert corpo["contagens"] == {"TODOS": 2, "LEAD": 1, "CONTATO": 0, "PROPOSTA": 0, "GANHO": 1, "PERDIDO": 0}
        item = corpo["resultados"][0]
        assert set(item) == {
            "id",
            "titulo",
            "empresa",
            "valor",
            "estagio",
            "pedido_status",
            "pedido_numero_erp",
            "atualizado_em",
        }
        assert item["pedido_status"] is None

    def test_vazia(self, api):
        corpo = api.get(URL).json()
        assert corpo["resultados"] == []
        assert corpo["total_cadastradas"] == 0
        assert corpo["contagens"]["TODOS"] == 0


class TestSugestoesEmpresa:
    @pytest.mark.parametrize("q", ["", "   "])
    def test_busca_vazia(self, api, criar_empresa, q):
        criar_empresa("Acme")
        r = api.get("/api/empresas", {"q": q})
        assert r.status_code == 200
        assert r.json() == []

    def test_contem_ordenado_por_nome(self, api, criar_empresa):
        for nome in ["Zeta Alimentos", "Acme Alimentos", "Horizonte Tech"]:
            criar_empresa(nome)
        r = api.get("/api/empresas", {"q": "ALIM"})
        assert [e["nome"] for e in r.json()] == ["Acme Alimentos", "Zeta Alimentos"]

    def test_limite_de_10(self, api, criar_empresa):
        for i in range(15):
            criar_empresa(f"Empresa {i:02d}")
        assert len(api.get("/api/empresas", {"q": "empresa"}).json()) == 10
