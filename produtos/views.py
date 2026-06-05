from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Categoria, Fornecedor, Produto, FotoProduto
from .serializers import (
    CategoriaSerializer, FornecedorSerializer,
    ProdutoSerializer, ProdutoListSerializer, FotoProdutoSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.filter(ativa=True)
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'criado_em']


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.filter(ativo=True)
    serializer_class = FornecedorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'email']


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.select_related('categoria', 'fornecedor').prefetch_related('fotos')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sku', 'nome', 'descricao']
    ordering_fields = ['nome', 'preco_venda', 'estoque_total', 'criado_em']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProdutoListSerializer
        return ProdutoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        categoria = self.request.query_params.get('categoria')
        if status:
            qs = qs.filter(status=status)
        if categoria:
            qs = qs.filter(categoria__slug=categoria)
        return qs

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        limite = int(request.query_params.get('limite', 5))
        produtos = self.get_queryset().filter(estoque_total__lte=limite, status='ativo')
        serializer = ProdutoListSerializer(produtos, many=True)
        return Response(serializer.data)


class FotoProdutoViewSet(viewsets.ModelViewSet):
    queryset = FotoProduto.objects.select_related('produto')
    serializer_class = FotoProdutoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        produto_id = self.request.query_params.get('produto')
        if produto_id:
            qs = qs.filter(produto_id=produto_id)
        return qs
