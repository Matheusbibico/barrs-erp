from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import ContaReceber, ContaPagar
from .serializers import ContaReceberSerializer, ContaPagarSerializer


class ContaReceberViewSet(viewsets.ModelViewSet):
    queryset = ContaReceber.objects.select_related('cliente', 'pedido')
    serializer_class = ContaReceberSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nome', 'descricao']
    ordering_fields = ['vencimento', 'valor']

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        pendente = ContaReceber.objects.filter(status='pendente').aggregate(total=Sum('valor'))
        vencido = ContaReceber.objects.filter(status='vencido').aggregate(total=Sum('valor'))
        return Response({
            'pendente': pendente['total'] or 0,
            'vencido': vencido['total'] or 0,
        })


class ContaPagarViewSet(viewsets.ModelViewSet):
    queryset = ContaPagar.objects.select_related('fornecedor')
    serializer_class = ContaPagarSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'categoria', 'fornecedor__nome']
    ordering_fields = ['vencimento', 'valor']

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        categoria = self.request.query_params.get('categoria')
        if status:
            qs = qs.filter(status=status)
        if categoria:
            qs = qs.filter(categoria=categoria)
        return qs

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        pendente = ContaPagar.objects.filter(status='pendente').aggregate(total=Sum('valor'))
        vencido = ContaPagar.objects.filter(status='vencido').aggregate(total=Sum('valor'))
        return Response({
            'pendente': pendente['total'] or 0,
            'vencido': vencido['total'] or 0,
        })
