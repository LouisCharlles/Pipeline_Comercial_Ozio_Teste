from rest_framework import serializers

from comercial.models import ESTAGIOS_ABERTOS, Empresa, Estagio, Oportunidade, Pedido
from comercial.services.empresas import obter_ou_criar_por_nome

# ---------------------------------------------------------------------------
# Representações (saída)
# ---------------------------------------------------------------------------


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ["id", "nome"]


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = [
            "id",
            "referencia_externa",
            "status",
            "numero_erp",
            "valor",
            "tentativas",
            "ultimo_erro_tipo",
            "ultimo_erro",
            "gerado_em",
            "criado_em",
            "atualizado_em",
        ]


def _pedido_de(oportunidade: Oportunidade) -> Pedido | None:
    try:
        return oportunidade.pedido
    except Pedido.DoesNotExist:
        return None


class OportunidadeSerializer(serializers.ModelSerializer):
    empresa = EmpresaSerializer()
    pedido = serializers.SerializerMethodField()

    class Meta:
        model = Oportunidade
        fields = [
            "id",
            "titulo",
            "empresa",
            "valor",
            "estagio",
            "motivo_perda",
            "fechado_em",
            "criado_em",
            "atualizado_em",
            "pedido",
        ]

    def get_pedido(self, obj: Oportunidade):
        pedido = _pedido_de(obj)
        return PedidoSerializer(pedido).data if pedido else None


class OportunidadeResumoSerializer(serializers.ModelSerializer):
    empresa = EmpresaSerializer()
    pedido_status = serializers.SerializerMethodField()
    pedido_numero_erp = serializers.SerializerMethodField()

    class Meta:
        model = Oportunidade
        fields = ["id", "titulo", "empresa", "valor", "estagio", "pedido_status", "pedido_numero_erp", "atualizado_em"]

    def get_pedido_status(self, obj: Oportunidade):
        pedido = _pedido_de(obj)
        return pedido.status if pedido else None

    def get_pedido_numero_erp(self, obj: Oportunidade):
        pedido = _pedido_de(obj)
        return pedido.numero_erp if pedido else None


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

MSG_TITULO = "Informe o título da oportunidade."
MSG_EMPRESA = "Informe a empresa."
MSG_TAMANHO = "Use no máximo {max_length} caracteres."


class ValorField(serializers.DecimalField):
    """Decimal opcional em que texto vazio vale como "sem valor"."""

    def run_validation(self, data=serializers.empty):
        if isinstance(data, str) and not data.strip():
            data = None
        return super().run_validation(data)


def _campo_valor():
    return ValorField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
        allow_null=True,
        required=False,
        error_messages={
            "invalid": "Informe um valor numérico.",
            "min_value": "O valor não pode ser negativo.",
            "max_digits": "Valor muito alto.",
            "max_whole_digits": "Valor muito alto.",
            "max_decimal_places": "Use no máximo 2 casas decimais.",
            "max_string_length": "Valor muito alto.",
        },
    )


def _campo_texto(mensagem_obrigatorio: str, **kwargs):
    return serializers.CharField(
        max_length=200,
        error_messages={
            "required": mensagem_obrigatorio,
            "blank": mensagem_obrigatorio,
            "null": mensagem_obrigatorio,
            "max_length": MSG_TAMANHO,
        },
        **kwargs,
    )


class OportunidadeCriacaoSerializer(serializers.Serializer):
    titulo = _campo_texto(MSG_TITULO)
    empresa = _campo_texto(MSG_EMPRESA)
    valor = _campo_valor()
    estagio = serializers.ChoiceField(
        choices=[(e.value, e.label) for e in Estagio if e in ESTAGIOS_ABERTOS],
        default=Estagio.LEAD,
        error_messages={"invalid_choice": "Escolha Lead, Contato ou Proposta."},
    )

    def create(self, validated_data):
        empresa = obter_ou_criar_por_nome(validated_data.pop("empresa"))
        return Oportunidade.objects.create(empresa=empresa, **validated_data)


class MudarEstagioSerializer(serializers.Serializer):
    estagio = serializers.ChoiceField(
        choices=Estagio.choices,
        error_messages={
            "required": "Informe o estágio.",
            "invalid_choice": "Estágio desconhecido.",
        },
    )
    motivo_perda = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="",
        error_messages={"max_length": "Use no máximo {max_length} caracteres."},
    )


class OportunidadeEdicaoSerializer(serializers.Serializer):
    titulo = _campo_texto(MSG_TITULO, required=False)
    empresa = _campo_texto(MSG_EMPRESA, required=False)
    valor = _campo_valor()

    def validate(self, attrs):
        if "estagio" in self.initial_data:
            raise serializers.ValidationError({"estagio": ["Altere o estágio pelo detalhe da oportunidade."]})
        return attrs

    def update(self, instance: Oportunidade, validated_data):
        if "empresa" in validated_data:
            instance.empresa = obter_ou_criar_por_nome(validated_data.pop("empresa"))
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()
        return instance
