from rest_framework import serializers
from .models import MovimentoEstoque


class MovimentoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku = serializers.CharField(source='produto.sku', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = MovimentoEstoque
        fields = '__all__'
        read_only_fields = ('saldo_anterior', 'saldo_posterior')
