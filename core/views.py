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
from produtos.models import Produto, VariacaoProduto

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
    from django.db.models import Avg, F, Sum
    from clientes.models import Cliente

    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    trinta_dias_atras = hoje - timedelta(days=30)

    faturamento_hoje = (
        Pedido.objects.filter(status='pago', criado_em__date=hoje)
        .aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')
    )
    faturamento_mes = (
        Pedido.objects.filter(status='pago', criado_em__date__gte=inicio_mes)
        .aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')
    )
    lucro_mes = (
        LucroPedido.objects.filter(pedido__criado_em__date__gte=inicio_mes)
        .aggregate(v=Sum('lucro_liquido'))['v'] or Decimal('0')
    )
    pedidos_pendentes = Pedido.objects.filter(
        status__in=['orcamento', 'reservado', 'aguardando_pagamento'],
    ).count()

    ticket_medio_mes = (
        Pedido.objects.filter(status='pago', criado_em__date__gte=inicio_mes)
        .aggregate(v=Avg('total_liquido'))['v'] or Decimal('0')
    )
    clientes_ativos = Cliente.objects.filter(ativo=True).count()

    estoque_baixo = (
        Produto.objects
        .filter(status='ativo', estoque_total__lte=5)
        .select_related('categoria')
        .order_by('estoque_total')[:10]
    )
    estoque_total_ativos = Produto.objects.filter(status='ativo').count()
    estoque_baixo_count = Produto.objects.filter(
        status='ativo', estoque_total__gt=0, estoque_total__lte=5
    ).count()
    estoque_zerado_count = Produto.objects.filter(
        status='ativo', estoque_total__lte=0
    ).count()

    top5_produtos = (
        ItemPedido.objects
        .filter(pedido__status='pago', pedido__criado_em__date__gte=trinta_dias_atras)
        .values('produto__nome')
        .annotate(qty=Sum('quantidade'), receita=Sum(F('preco_unitario') * F('quantidade')))
        .order_by('-receita')[:5]
    )

    vendas_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('criado_em'))
        .values('dia')
        .annotate(total=Sum('total_liquido'))
        .order_by('dia')
    )
    lucro_qs = (
        LucroPedido.objects
        .filter(pedido__criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('pedido__criado_em'))
        .values('dia')
        .annotate(total=Sum('lucro_liquido'))
        .order_by('dia')
    )
    vendas_dict = {v['dia']: float(v['total']) for v in vendas_qs}
    lucro_dict = {v['dia']: float(v['total']) for v in lucro_qs}

    labels, dados, dados_lucro = [], [], []
    dia = trinta_dias_atras
    while dia <= hoje:
        labels.append(dia.strftime('%d/%m'))
        dados.append(vendas_dict.get(dia, 0))
        dados_lucro.append(lucro_dict.get(dia, 0))
        dia += timedelta(days=1)

    _CANAL_LABELS = {
        'site': 'Site', 'whatsapp': 'WhatsApp', 'instagram': 'Instagram',
        'presencial': 'Presencial', 'link': 'Link',
    }
    canal_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=inicio_mes)
        .values('canal')
        .annotate(total=Sum('total_liquido'))
        .order_by('-total')
    )
    canal_labels = [_CANAL_LABELS.get(v['canal'], v['canal']) for v in canal_qs]
    canal_dados = [float(v['total']) for v in canal_qs]

    return render(request, 'admin/dashboard.html', {
        'title': 'Dashboard',
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'lucro_mes': lucro_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'ticket_medio_mes': ticket_medio_mes,
        'clientes_ativos': clientes_ativos,
        'estoque_baixo': estoque_baixo,
        'estoque_total_ativos': estoque_total_ativos,
        'estoque_baixo_count': estoque_baixo_count,
        'estoque_zerado_count': estoque_zerado_count,
        'top5_produtos': top5_produtos,
        'grafico_labels': json.dumps(labels),
        'grafico_dados': json.dumps(dados),
        'grafico_lucro': json.dumps(dados_lucro),
        'vendas_canal_labels': json.dumps(canal_labels),
        'vendas_canal_dados': json.dumps(canal_dados),
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
    from django.db.models import F as _F

    sp = SitePedido.objects.using('site').prefetch_related('itens__produto').get(pk=site_id)

    status_erp = _STATUS_MAP.get(sp.status, Pedido.STATUS_ORCAMENTO)

    if sp.email:
        cliente, _ = Cliente.objects.get_or_create(
            email=sp.email,
            defaults={
                'nome': sp.nome or sp.email,
                'whatsapp': getattr(sp, 'telefone', ''),
                'cidade': getattr(sp, 'cidade', ''),
                'estado': getattr(sp, 'estado', ''),
            },
        )
    else:
        cliente, _ = Cliente.objects.get_or_create(
            site_id=site_id,
            defaults={'nome': sp.nome or f'site_{site_id}'},
        )

    ped, criado = Pedido.objects.get_or_create(
        site_id=sp.id,
        defaults={
            'cliente': cliente,
            'canal': Pedido.CANAL_SITE,
            'status': status_erp,
            'total_bruto': sp.subtotal,
            'desconto': sp.desconto,
            'frete': sp.frete,
            'total_liquido': sp.total,
        },
    )

    if not criado:
        ped.status = status_erp
        ped.total_liquido = sp.total
        ped.save(update_fields=['status', 'total_liquido'])
        return ped, False

    placeholder, _ = Produto.objects.get_or_create(
        sku='SITE-DESCONHECIDO',
        defaults={
            'nome': 'Produto não identificado (importado)',
            'preco_venda': Decimal('0'),
            'custo': Decimal('0'),
            'status': Produto.STATUS_INATIVO,
        },
    )
    prod_map = {p.site_id: p for p in Produto.objects.filter(site_id__isnull=False)}
    var_map = {v.site_id: v for v in VariacaoProduto.objects.filter(site_id__isnull=False).select_related('produto')}

    for si in sp.itens.all():
        variacao = None
        produto = None

        # Tenta encontrar por variacao_id do site (se disponível no modelo do site)
        variacao_site_id = getattr(si, 'variacao_id', None)
        if variacao_site_id:
            variacao = var_map.get(variacao_site_id)

        # Resolve produto a partir da variação ou do mapeamento direto
        if variacao:
            produto = variacao.produto
        elif si.produto_id:
            produto = prod_map.get(si.produto_id)

        produto = produto or placeholder

        ItemPedido.objects.create(
            pedido=ped,
            produto=produto,
            variacao=variacao,
            quantidade=si.quantidade,
            preco_unitario=si.preco_unitario,
            custo_unitario=variacao.custo if variacao else Decimal('0'),
        )

        # Decremento de estoque: por variação se disponível, senão por produto
        if variacao:
            VariacaoProduto.objects.filter(pk=variacao.pk).update(
                estoque=_F('estoque') - si.quantidade
            )
        elif produto.sku != 'SITE-DESCONHECIDO':
            Produto.objects.filter(pk=produto.pk).update(
                estoque_total=_F('estoque_total') - si.quantidade
            )

    if status_erp == Pedido.STATUS_PAGO:
        Pagamento.objects.get_or_create(
            pedido=ped,
            defaults={
                'metodo': Pagamento.METODO_PIX,
                'valor': sp.total,
                'status': Pagamento.STATUS_APROVADO,
            },
        )

    return ped, True
