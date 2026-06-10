from rest_framework import serializers

from .models import CategoriaFinanceira, ContaPagar, ContaReceber, LancamentoCaixa


class ContaReceberSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaReceber
        fields = '__all__'


class ContaPagarSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaPagar
        fields = '__all__'


class CategoriaFinanceiraSerializer(serializers.ModelSerializer):
    pai_nome = serializers.CharField(source='pai.nome', read_only=True)

    class Meta:
        model = CategoriaFinanceira
        fields = '__all__'


class LancamentoCaixaSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = LancamentoCaixa
        fields = '__all__'
