from rest_framework import serializers
from .models import Cliente, EnderecoCliente


class EnderecoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnderecoCliente
        fields = '__all__'


class ClienteSerializer(serializers.ModelSerializer):
    ticket_medio = serializers.ReadOnlyField()
    enderecos = EnderecoClienteSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'


class ClienteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ('id', 'nome', 'whatsapp', 'email', 'cidade', 'estado', 'total_gasto', 'qtd_pedidos', 'ativo')
