from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Pedido, ItemPedido, Pagamento, LucroPedido, EventoRastreio, Devolucao, ItemDevolucao
from .serializers import (
    PedidoSerializer, PedidoListSerializer, PedidoCreateSerializer,
    ItemPedidoSerializer, PagamentoSerializer, LucroPedidoSerializer,
    EventoRastreioSerializer, DevolucaoSerializer, ItemDevolucaoSerializer,
)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.select_related('cliente', 'usuario').prefetch_related(
        'itens', 'itens__variacao', 'pagamentos', 'eventos_rastreio'
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nome', 'cliente__whatsapp']
    ordering_fields = ['criado_em', 'total_liquido']

    def get_serializer_class(self):
        if self.action == 'list':
            return PedidoListSerializer
        if self.action == 'create':
            return PedidoCreateSerializer
        return PedidoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        canal = self.request.query_params.get('canal')
        cliente = self.request.query_params.get('cliente')
        if status_param:
            qs = qs.filter(status=status_param)
        if canal:
            qs = qs.filter(canal=canal)
        if cliente:
            qs = qs.filter(cliente_id=cliente)
        return qs

    @action(detail=True, methods=['patch'])
    def atualizar_status(self, request, pk=None):
        pedido = self.get_object()
        novo_status = request.data.get('status')
        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return Response({'erro': 'Status inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        pedido.status = novo_status
        pedido.save(update_fields=['status', 'atualizado_em'])
        return Response(PedidoSerializer(pedido).data)

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        from django.db.models import Sum, Count
        resumo = {}
        for s, label in Pedido.STATUS_CHOICES:
            agg = Pedido.objects.filter(status=s).aggregate(
                qtd=Count('id'), total=Sum('total_liquido')
            )
            resumo[s] = {'label': label, 'qtd': agg['qtd'], 'total': agg['total'] or 0}
        return Response(resumo)


class ItemPedidoViewSet(viewsets.ModelViewSet):
    queryset = ItemPedido.objects.select_related('pedido', 'produto', 'variacao')
    serializer_class = ItemPedidoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pedido = self.request.query_params.get('pedido')
        if pedido:
            qs = qs.filter(pedido_id=pedido)
        return qs


class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.select_related('pedido')
    serializer_class = PagamentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pedido = self.request.query_params.get('pedido')
        if pedido:
            qs = qs.filter(pedido_id=pedido)
        return qs


class LucroPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LucroPedido.objects.select_related('pedido', 'pedido__cliente')
    serializer_class = LucroPedidoSerializer


class EventoRastreioViewSet(viewsets.ModelViewSet):
    queryset = EventoRastreio.objects.select_related('pedido')
    serializer_class = EventoRastreioSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pedido = self.request.query_params.get('pedido')
        if pedido:
            qs = qs.filter(pedido_id=pedido)
        return qs


class DevolucaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Devolucao.objects.select_related(
        'pedido', 'pedido__cliente', 'responsavel'
    ).prefetch_related('itens', 'itens__item_pedido__produto')
    serializer_class = DevolucaoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['pedido__cliente__nome', 'motivo']
    ordering_fields = ['criado_em', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        pedido = self.request.query_params.get('pedido')
        if status_param:
            qs = qs.filter(status=status_param)
        if pedido:
            qs = qs.filter(pedido_id=pedido)
        return qs

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        devolucao = self.get_object()
        if devolucao.status != Devolucao.STATUS_SOLICITADA:
            return Response(
                {'erro': 'Apenas devoluções solicitadas podem ser aprovadas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        devolucao.status = Devolucao.STATUS_APROVADA
        devolucao.responsavel = request.user
        devolucao.save()
        return Response(DevolucaoSerializer(devolucao).data)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        devolucao = self.get_object()
        if devolucao.status != Devolucao.STATUS_SOLICITADA:
            return Response(
                {'erro': 'Apenas devoluções solicitadas podem ser recusadas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        devolucao.status = Devolucao.STATUS_RECUSADA
        devolucao.save()
        return Response(DevolucaoSerializer(devolucao).data)
