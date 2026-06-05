from rest_framework import viewsets, filters
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from .models import MovimentoEstoque
from .serializers import MovimentoEstoqueSerializer


class MovimentoEstoqueViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = MovimentoEstoque.objects.select_related('produto', 'pedido', 'usuario')
    serializer_class = MovimentoEstoqueSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['produto__nome', 'produto__sku', 'motivo']
    ordering_fields = ['criado_em']

    def get_queryset(self):
        qs = super().get_queryset()
        produto = self.request.query_params.get('produto')
        tipo = self.request.query_params.get('tipo')
        if produto:
            qs = qs.filter(produto_id=produto)
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
