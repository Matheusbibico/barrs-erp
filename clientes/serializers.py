from rest_framework import serializers
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    ticket_medio = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = '__all__'


class ClienteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ('id', 'nome', 'whatsapp', 'email', 'cidade', 'estado', 'total_gasto', 'qtd_pedidos', 'ativo')
