from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework import filters, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import CategoriaFinanceira, ContaPagar, ContaReceber, LancamentoCaixa
from .serializers import (
    CategoriaFinanceiraSerializer,
    ContaPagarSerializer,
    ContaReceberSerializer,
    LancamentoCaixaSerializer,
)


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
    queryset = ContaPagar.objects.all()
    serializer_class = ContaPagarSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'categoria']
    ordering_fields = ['valor']

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


class CategoriaFinanceiraViewSet(viewsets.ModelViewSet):
    queryset = CategoriaFinanceira.objects.all()
    serializer_class = CategoriaFinanceiraSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome']


class LancamentoCaixaViewSet(viewsets.ModelViewSet):
    queryset = LancamentoCaixa.objects.select_related('pedido', 'conta_receber', 'conta_pagar')
    serializer_class = LancamentoCaixaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['data', 'valor']

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.query_params.get('tipo')
        inicio = self.request.query_params.get('inicio')
        fim = self.request.query_params.get('fim')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return qs


@api_view(['GET'])
def fluxo_caixa(request):
    hoje = date.today()
    inicio_str = request.query_params.get('inicio')
    fim_str = request.query_params.get('fim')

    try:
        inicio = date.fromisoformat(inicio_str) if inicio_str else hoje.replace(day=1)
        fim = date.fromisoformat(fim_str) if fim_str else hoje
    except ValueError:
        return Response({'error': 'Datas inválidas. Use formato YYYY-MM-DD.'}, status=400)

    lancamentos = (
        LancamentoCaixa.objects
        .filter(data__gte=inicio, data__lte=fim)
        .order_by('data')
        .values('data', 'tipo', 'valor')
    )

    saldo_anterior = (
        LancamentoCaixa.objects
        .filter(data__lt=inicio)
        .aggregate(
            entradas=Sum('valor', filter=Q(tipo='entrada')),
            saidas=Sum('valor', filter=Q(tipo='saida')),
        )
    )
    entradas_ant = saldo_anterior['entradas'] or Decimal('0')
    saidas_ant = saldo_anterior['saidas'] or Decimal('0')
    saldo = entradas_ant - saidas_ant

    dias = {}
    for lanc in lancamentos:
        d = str(lanc['data'])
        if d not in dias:
            dias[d] = {'entradas': Decimal('0'), 'saidas': Decimal('0')}
        if lanc['tipo'] == 'entrada':
            dias[d]['entradas'] += lanc['valor']
        else:
            dias[d]['saidas'] += lanc['valor']

    linha_tempo = []
    dia = inicio
    while dia <= fim:
        d = str(dia)
        mov = dias.get(d, {'entradas': Decimal('0'), 'saidas': Decimal('0')})
        saldo += mov['entradas'] - mov['saidas']
        linha_tempo.append({
            'data': d,
            'entradas': float(mov['entradas']),
            'saidas': float(mov['saidas']),
            'saldo_acumulado': float(saldo),
        })
        dia += timedelta(days=1)

    return Response({
        'periodo': {'inicio': str(inicio), 'fim': str(fim)},
        'saldo_inicial': float(entradas_ant - saidas_ant),
        'saldo_final': float(saldo),
        'linha_tempo': linha_tempo,
    })


@api_view(['GET'])
def dre(request):
    from django.db.models import Q
    hoje = date.today()
    ano = int(request.query_params.get('ano', hoje.year))
    mes = int(request.query_params.get('mes', hoje.month))

    inicio = date(ano, mes, 1)
    if mes == 12:
        fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        fim = date(ano, mes + 1, 1) - timedelta(days=1)

    from pedidos.models import ItemPedido, Pedido

    receita_bruta = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=inicio, criado_em__date__lte=fim)
        .aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')
    )

    from django.db.models import DecimalField, ExpressionWrapper, F as _F
    cmv = (
        ItemPedido.objects
        .filter(pedido__status='pago', pedido__criado_em__date__gte=inicio, pedido__criado_em__date__lte=fim)
        .aggregate(
            v=Sum(ExpressionWrapper(_F('custo_unitario') * _F('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2)))
        )['v'] or Decimal('0')
    )

    lucro_bruto = receita_bruta - cmv

    despesas_qs = (
        LancamentoCaixa.objects
        .filter(tipo='saida', data__gte=inicio, data__lte=fim)
        .values('descricao')
        .annotate(total=Sum('valor'))
        .order_by('-total')
    )
    total_despesas = sum(d['total'] for d in despesas_qs)

    lucro_liquido = lucro_bruto - total_despesas

    return Response({
        'periodo': {'ano': ano, 'mes': mes, 'inicio': str(inicio), 'fim': str(fim)},
        'receita_bruta': float(receita_bruta),
        'cmv': float(cmv),
        'lucro_bruto': float(lucro_bruto),
        'despesas': [
            {'categoria': d['descricao'], 'total': float(d['total'])}
            for d in despesas_qs
        ],
        'total_despesas': float(total_despesas),
        'lucro_liquido': float(lucro_liquido),
        'margem_bruta_pct': round(float(lucro_bruto / receita_bruta * 100), 2) if receita_bruta else 0,
        'margem_liquida_pct': round(float(lucro_liquido / receita_bruta * 100), 2) if receita_bruta else 0,
    })
