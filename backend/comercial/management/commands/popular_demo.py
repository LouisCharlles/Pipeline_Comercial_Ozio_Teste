"""Popula o banco com os dados do protótipo, para demonstração.

Apaga todas as empresas, oportunidades e pedidos antes de criar os dados.
"""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction

from comercial.models import ESTAGIOS_FINAIS, Empresa, Estagio, Oportunidade, Pedido, StatusPedido, TipoErroErp

FUSO = ZoneInfo("America/Sao_Paulo")


def _data(texto: str) -> datetime:
    dia, mes, ano = (int(p) for p in texto.split("/"))
    return datetime(ano, mes, dia, 10, 0, tzinfo=FUSO)


# (título, empresa, valor, estágio, criado, atualizado, extras)
OPORTUNIDADES = [
    ("Contrato de Logística 2026", "Acme Logística", 85000, Estagio.CONTATO, "12/08/2026", "22/09/2026", {}),
    (
        "Fornecimento de Alimentos Premium",
        "Nova Alimentos",
        120000,
        Estagio.GANHO,
        "05/07/2026",
        "20/09/2026",
        {"pedido": ("ERP-1042", "20/09/2026")},
    ),
    (
        "Implementação de ERP Industrial",
        "Horizonte Tech",
        250000,
        Estagio.GANHO,
        "10/06/2026",
        "15/09/2026",
        {"pedido": ("ERP-0987", "15/09/2026")},
    ),
    ("Consultoria em Processos", "Grupo Aurora", 45000, Estagio.LEAD, "01/09/2026", "01/09/2026", {}),
    ("Expansão de Data Center", "Horizonte Tech", 380000, Estagio.PROPOSTA, "18/08/2026", "24/09/2026", {}),
    (
        "Gestão de Frotas Integrada",
        "Acme Logística",
        95000,
        Estagio.GANHO,
        "03/07/2026",
        "25/09/2026",
        {"falha": 2},
    ),
    (
        "Plataforma de Vendas Online",
        "Nova Alimentos",
        67000,
        Estagio.PERDIDO,
        "14/07/2026",
        "10/09/2026",
        {"motivo": "Orçamento aprovado para concorrente com prazo menor"},
    ),
    ("Suporte Técnico Anual", "Grupo Aurora", 32000, Estagio.LEAD, "10/09/2026", "10/09/2026", {}),
    (
        "Integração de Sistemas Legados",
        "Horizonte Tech",
        158000,
        Estagio.GANHO,
        "22/07/2026",
        "28/09/2026",
        {"pedido": ("ERP-1105", "28/09/2026")},
    ),
    ("Campanha de Marketing Digital", "Grupo Aurora", 28000, Estagio.CONTATO, "05/09/2026", "15/09/2026", {}),
    ("Renovação de Licenças de Software", "Acme Logística", 41000, Estagio.LEAD, "20/09/2026", "20/09/2026", {}),
    ("Treinamento e Capacitação de Equipe", "Nova Alimentos", 18000, Estagio.CONTATO, "25/09/2026", "25/09/2026", {}),
]


class Command(BaseCommand):
    help = "Apaga os dados e cria as empresas e oportunidades do protótipo."

    @transaction.atomic
    def handle(self, *args, **options):
        Pedido.objects.all().delete()
        Oportunidade.objects.all().delete()
        Empresa.objects.all().delete()

        empresas: dict[str, Empresa] = {}
        for titulo, nome_empresa, valor, estagio, criado, atualizado, extras in OPORTUNIDADES:
            empresa = empresas.get(nome_empresa) or Empresa.objects.create(nome=nome_empresa)
            empresas[nome_empresa] = empresa

            op = Oportunidade.objects.create(
                titulo=titulo,
                empresa=empresa,
                valor=Decimal(valor),
                estagio=estagio,
                motivo_perda=extras.get("motivo", ""),
                fechado_em=_data(atualizado) if estagio in ESTAGIOS_FINAIS else None,
            )

            if "pedido" in extras:
                numero, gerado = extras["pedido"]
                Pedido.objects.create(
                    oportunidade=op,
                    referencia_externa=Pedido.referencia_para(op.id),
                    valor=op.valor,
                    status=StatusPedido.GERADO,
                    numero_erp=numero,
                    tentativas=1,
                    gerado_em=_data(gerado),
                )
            elif "falha" in extras:
                Pedido.objects.create(
                    oportunidade=op,
                    referencia_externa=Pedido.referencia_para(op.id),
                    valor=op.valor,
                    status=StatusPedido.FALHOU,
                    tentativas=extras["falha"],
                    ultimo_erro_tipo=TipoErroErp.TEMPO_ESGOTADO,
                    ultimo_erro="ERP não respondeu em 5s",
                )

            # auto_now/auto_now_add ignoram valores passados no create; ajusta direto no banco.
            Oportunidade.objects.filter(pk=op.pk).update(criado_em=_data(criado), atualizado_em=_data(atualizado))

        self.stdout.write(
            self.style.SUCCESS(f"{len(empresas)} empresas e {len(OPORTUNIDADES)} oportunidades criadas.")
        )
