from rest_framework import serializers
from .models import Pedido, ItemPedido, Pagamento, LucroPedido, EventoRastreio


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku = serializers.CharField(source='produto.sku', read_only=True)
    variacao_descricao = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = '__all__'

    def get_variacao_descricao(self, obj):
        if obj.variacao:
            partes = [p for p in [obj.variacao.cor, obj.variacao.tamanho] if p]
            return ' / '.join(partes) if partes else None
        return None


class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = '__all__'


class LucroPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LucroPedido
        fields = '__all__'
        read_only_fields = ('pedido', 'receita_bruta', 'custo_produtos', 'lucro_liquido')


class EventoRastreioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoRastreio
        fields = '__all__'


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    lucro = LucroPedidoSerializer(read_only=True)
    eventos_rastreio = EventoRastreioSerializer(many=True, read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'


class PedidoListSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    canal_display = serializers.CharField(source='get_canal_display', read_only=True)

    class Meta:
        model = Pedido
        fields = (
            'id', 'cliente_nome', 'canal', 'canal_display',
            'status', 'status_display', 'total_liquido', 'criado_em',
        )


class PedidoCreateSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = ('cliente', 'usuario', 'canal', 'status', 'desconto', 'frete', 'endereco_entrega', 'observacoes', 'itens')

    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        pedido = Pedido.objects.create(**validated_data)
        for item_data in itens_data:
            item = ItemPedido(pedido=pedido, **item_data)
            item.full_clean()
            item.save()
        pedido.calcular_totais()
        pedido.save()
        return pedido
