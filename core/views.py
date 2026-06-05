import hmac
import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from clientes.models import Cliente
from core.site_models import SitePedido
from pedidos.models import ItemPedido, LucroPedido, Pagamento, Pedido
from produtos.models import Produto

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    'pendente': Pedido.STATUS_AGUARDANDO,
    'confirmado': Pedido.STATUS_PAGO,
    'enviado': Pedido.STATUS_ENVIADO,
    'entregue': Pedido.STATUS_ENTREGUE,
    'cancelado': Pedido.STATUS_CANCELADO,
}


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


@csrf_exempt
@require_POST
def webhook_nova_venda(request):
    token = request.META.get('HTTP_X_WEBHOOK_TOKEN', '')
    expected = getattr(settings, 'WEBHOOK_TOKEN', '')
    if not expected or not hmac.compare_digest(token, expected):
        return JsonResponse({'status': 'error', 'detail': 'Unauthorized'}, status=401)

    try:
        body = json.loads(request.body)
        pedido_id = int(body['pedido_id'])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'status': 'error', 'detail': 'pedido_id required'}, status=400)

    if 'site' not in settings.DATABASES:
        return JsonResponse({'status': 'error', 'detail': 'Site database not configured'}, status=503)

    try:
        pedido, criado = _importar_pedido_unico(pedido_id)
    except SitePedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'detail': 'Pedido not found in site db'}, status=404)
    except Exception as exc:
        logger.exception('Webhook import error for site pedido %s', pedido_id)
        return JsonResponse({'status': 'error', 'detail': 'Internal server error'}, status=500)

    return JsonResponse({'status': 'ok', 'criado': criado, 'pedido_id': str(pedido.id)})


def _importar_pedido_unico(site_id):
    raise NotImplementedError
