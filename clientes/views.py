from rest_framework import viewsets, filters
from .models import Cliente
from .serializers import ClienteSerializer, ClienteListSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'whatsapp', 'email']
    ordering_fields = ['nome', 'total_gasto', 'qtd_pedidos', 'ultima_compra']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        estado = self.request.query_params.get('estado')
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs
