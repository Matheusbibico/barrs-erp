from rest_framework import serializers
from .models import ContaReceber, ContaPagar


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
