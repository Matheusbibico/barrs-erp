from rest_framework import serializers
from .models import Categoria, Fornecedor, Produto, FotoProduto, VariacaoProduto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = '__all__'


class FotoProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoProduto
        fields = '__all__'


class VariacaoProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariacaoProduto
        fields = '__all__'


class ProdutoSerializer(serializers.ModelSerializer):
    fotos = FotoProdutoSerializer(many=True, read_only=True)
    variacoes = VariacaoProdutoSerializer(many=True, read_only=True)
    estoque_disponivel = serializers.ReadOnlyField()
    margem = serializers.ReadOnlyField()
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)

    class Meta:
        model = Produto
        fields = '__all__'


class ProdutoListSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    estoque_disponivel = serializers.ReadOnlyField()

    class Meta:
        model = Produto
        fields = (
            'id', 'sku', 'nome', 'categoria_nome', 'preco_venda',
            'custo', 'estoque_total', 'estoque_reservado', 'estoque_disponivel', 'status',
        )
