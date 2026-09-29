"""Modelos do pipeline comercial.

As regras de integridade que não podem depender da aplicação (um pedido por oportunidade, pedido
gerado sempre com número do ERP, data de fechamento coerente com o estágio) ficam no banco como
constraints. Ver specs/001-pipeline-comercial-erp/data-model.md.
"""

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class Empresa(models.Model):
    nome = models.CharField(max_length=200)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(Lower("nome"), name="empresa_nome_unico_ci"),
        ]

    def __str__(self) -> str:
        return self.nome


class Estagio(models.TextChoices):
    LEAD = "LEAD", "Lead"
    CONTATO = "CONTATO", "Contato"
    PROPOSTA = "PROPOSTA", "Proposta"
    GANHO = "GANHO", "Ganho"
    PERDIDO = "PERDIDO", "Perdido"


ESTAGIOS_ABERTOS = frozenset({Estagio.LEAD, Estagio.CONTATO, Estagio.PROPOSTA})
ESTAGIOS_FINAIS = frozenset({Estagio.GANHO, Estagio.PERDIDO})


class Oportunidade(models.Model):
    titulo = models.CharField(max_length=200)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="oportunidades")
    valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    estagio = models.CharField(max_length=10, choices=Estagio.choices, default=Estagio.LEAD, db_index=True)
    motivo_perda = models.TextField(blank=True, default="")
    fechado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizado_em", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(valor__isnull=True) | Q(valor__gte=0),
                name="oportunidade_valor_nao_negativo",
            ),
            models.CheckConstraint(
                condition=Q(estagio__in=Estagio.values),
                name="oportunidade_estagio_valido",
            ),
            # Estágio final ⇔ data de fechamento preenchida.
            models.CheckConstraint(
                condition=(
                    Q(estagio__in=[Estagio.GANHO, Estagio.PERDIDO], fechado_em__isnull=False)
                    | (~Q(estagio__in=[Estagio.GANHO, Estagio.PERDIDO]) & Q(fechado_em__isnull=True))
                ),
                name="oportunidade_fechado_em_coerente",
            ),
        ]

    def __str__(self) -> str:
        return self.titulo


class StatusPedido(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    GERADO = "GERADO", "Gerado"
    FALHOU = "FALHOU", "Falhou"


class TipoErroErp(models.TextChoices):
    NENHUM = "", "Nenhum"
    TEMPO_ESGOTADO = "TEMPO_ESGOTADO", "Tempo esgotado"
    ERRO_SERVICO = "ERRO_SERVICO", "Erro do serviço"
    RESPOSTA_INVALIDA = "RESPOSTA_INVALIDA", "Resposta inválida"


class Pedido(models.Model):
    # OneToOne = UNIQUE no banco: a garantia central de "no máximo um pedido por oportunidade".
    oportunidade = models.OneToOneField(Oportunidade, on_delete=models.PROTECT, related_name="pedido")
    referencia_externa = models.CharField(max_length=40, unique=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=10, choices=StatusPedido.choices, default=StatusPedido.PENDENTE)
    numero_erp = models.CharField(max_length=40, null=True, blank=True, unique=True)
    tentativas = models.PositiveIntegerField(default=0)
    ultimo_erro_tipo = models.CharField(max_length=20, choices=TipoErroErp.choices, blank=True, default="")
    ultimo_erro = models.TextField(blank=True, default="")
    gerado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(valor__gt=0), name="pedido_valor_positivo"),
            models.CheckConstraint(
                condition=Q(status__in=StatusPedido.values),
                name="pedido_status_valido",
            ),
            # Gerado ⇔ tem número do ERP e data de geração.
            models.CheckConstraint(
                condition=(
                    Q(status=StatusPedido.GERADO, numero_erp__isnull=False, gerado_em__isnull=False)
                    | (~Q(status=StatusPedido.GERADO) & Q(numero_erp__isnull=True, gerado_em__isnull=True))
                ),
                name="pedido_gerado_coerente",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.referencia_externa} ({self.status})"

    @staticmethod
    def referencia_para(oportunidade_id: int) -> str:
        return f"OPP-{oportunidade_id}"
