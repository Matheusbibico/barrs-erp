import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from pedidos.models import LucroPedido, Pedido
from produtos.models import Produto


@staff_member_required
def dashboard(request):
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    trinta_dias_atras = hoje - timedelta(days=30)

    faturamento_hoje = Pedido.objects.filter(
        status='pago', criado_em__date=hoje,
    ).aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')

    faturamento_mes = Pedido.objects.filter(
        status='pago', criado_em__date__gte=inicio_mes,
    ).aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')

    lucro_mes = LucroPedido.objects.filter(
        pedido__criado_em__date__gte=inicio_mes,
    ).aggregate(v=Sum('lucro_liquido'))['v'] or Decimal('0')

    pedidos_pendentes = Pedido.objects.filter(
        status__in=['orcamento', 'reservado', 'aguardando_pagamento'],
    ).count()

    estoque_baixo = (
        Produto.objects
        .filter(status='ativo', estoque_total__lte=5)
        .select_related('categoria')
        .order_by('estoque_total')[:10]
    )

    vendas_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('criado_em'))
        .values('dia')
        .annotate(total=Sum('total_liquido'))
        .order_by('dia')
    )
    vendas_dict = {v['dia']: float(v['total']) for v in vendas_qs}

    labels, dados = [], []
    dia = trinta_dias_atras
    while dia <= hoje:
        labels.append(dia.strftime('%d/%m'))
        dados.append(vendas_dict.get(dia, 0))
        dia += timedelta(days=1)

    return render(request, 'admin/dashboard.html', {
        'title': 'Dashboard',
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'lucro_mes': lucro_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'estoque_baixo': estoque_baixo,
        'grafico_labels': json.dumps(labels),
        'grafico_dados': json.dumps(dados),
    })
