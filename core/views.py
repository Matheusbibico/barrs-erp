import csv
import hmac
import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from clientes.models import Cliente
from core.site_models import SitePedido
from financeiro.models import LancamentoCaixa, MetaMensal
from pedidos.models import ItemPedido, Pagamento, Pedido
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
    from django.db.models import DecimalField, ExpressionWrapper, F as _F
    custo_mes = (
        ItemPedido.objects
        .filter(pedido__status='pago', pedido__criado_em__date__gte=inicio_mes)
        .aggregate(
            v=Sum(ExpressionWrapper(_F('custo_unitario') * _F('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2)))
        )['v'] or Decimal('0')
    )
    lucro_mes = faturamento_mes - custo_mes
    pedidos_pendentes = Pedido.objects.filter(
        status__in=['orcamento', 'aguardando_pagamento'],
    ).count()

    ticket_medio_mes = (
        Pedido.objects.filter(status='pago', criado_em__date__gte=inicio_mes)
        .aggregate(v=Avg('total_liquido'))['v'] or Decimal('0')
    )
    clientes_ativos = Cliente.objects.filter(ativo=True).count()

    from django.db.models import F as _Fstock
    estoque_total_ativos = Produto.objects.filter(status='ativo').count()
    estoque_zerado = (
        Produto.objects
        .filter(status='ativo', estoque_total__lte=0)
        .select_related('categoria')
        .order_by('nome')[:10]
    )
    estoque_baixo = (
        Produto.objects
        .filter(status='ativo', estoque_total__gt=0, estoque_minimo__gt=0,
                estoque_total__lte=_Fstock('estoque_minimo'))
        .select_related('categoria')
        .order_by('estoque_total')[:10]
    )
    estoque_baixo_count = Produto.objects.filter(
        status='ativo', estoque_total__gt=0, estoque_minimo__gt=0,
        estoque_total__lte=_Fstock('estoque_minimo')
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
    from django.db.models import DecimalField, ExpressionWrapper, F as _F2
    custo_qs = (
        ItemPedido.objects
        .filter(pedido__status='pago', pedido__criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('pedido__criado_em'))
        .values('dia')
        .annotate(custo=Sum(ExpressionWrapper(_F2('custo_unitario') * _F2('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2))))
        .order_by('dia')
    )
    vendas_dict = {v['dia']: float(v['total']) for v in vendas_qs}
    custo_dict = {v['dia']: float(v['custo']) for v in custo_qs}

    labels, dados, dados_lucro = [], [], []
    dia = trinta_dias_atras
    while dia <= hoje:
        labels.append(dia.strftime('%d/%m'))
        vendas_dia = vendas_dict.get(dia, 0)
        dados.append(vendas_dia)
        dados_lucro.append(vendas_dia - custo_dict.get(dia, 0))
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

    from django.db.models import Q as _Q
    saldo_caixa_agg = LancamentoCaixa.objects.aggregate(
        entradas=Sum('valor', filter=_Q(tipo='entrada')),
        saidas=Sum('valor', filter=_Q(tipo='saida')),
    )
    saldo_caixa = (saldo_caixa_agg['entradas'] or Decimal('0')) - (saldo_caixa_agg['saidas'] or Decimal('0'))

    from financeiro.models import ContaReceber
    trinta_dias_frente = hoje + timedelta(days=30)
    a_receber_30d = (
        ContaReceber.objects
        .filter(status='pendente', vencimento__lte=trinta_dias_frente)
        .aggregate(v=Sum('valor'))['v'] or Decimal('0')
    )

    # Meta mensal
    meta_obj = MetaMensal.objects.filter(ano=hoje.year, mes=hoje.month).first()
    meta_valor = meta_obj.valor_meta if meta_obj else None
    meta_percent = (
        min(int(faturamento_mes / meta_valor * 100), 100)
        if meta_valor and meta_valor > 0
        else None
    )

    # Contadores para atalhos rápidos
    aguardando_pagamento_count = Pedido.objects.filter(
        status=Pedido.STATUS_AGUARDANDO
    ).count()
    a_enviar_count = Pedido.objects.filter(
        status=Pedido.STATUS_PAGO, codigo_rastreio=''
    ).count()
    tres_dias_atras = timezone.now() - timedelta(days=3)
    atrasados_count = Pedido.objects.filter(
        status=Pedido.STATUS_PAGO,
        codigo_rastreio='',
        criado_em__lte=tres_dias_atras,
    ).count()

    return render(request, 'admin/dashboard.html', {
        'title': 'Dashboard',
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'lucro_mes': lucro_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'ticket_medio_mes': ticket_medio_mes,
        'clientes_ativos': clientes_ativos,
        'estoque_baixo': estoque_baixo,
        'estoque_zerado': estoque_zerado,
        'estoque_total_ativos': estoque_total_ativos,
        'estoque_baixo_count': estoque_baixo_count,
        'estoque_zerado_count': estoque_zerado_count,
        'top5_produtos': top5_produtos,
        'grafico_labels': json.dumps(labels),
        'grafico_dados': json.dumps(dados),
        'grafico_lucro': json.dumps(dados_lucro),
        'vendas_canal_labels': json.dumps(canal_labels),
        'vendas_canal_dados': json.dumps(canal_dados),
        'saldo_caixa': saldo_caixa,
        'a_receber_30d': a_receber_30d,
        'meta_valor': meta_valor,
        'meta_percent': meta_percent,
        'aguardando_pagamento_count': aguardando_pagamento_count,
        'a_enviar_count': a_enviar_count,
        'atrasados_count': atrasados_count,
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


_MP_METODO_MAP = {
    'pix': Pagamento.METODO_PIX,
    'credit_card': Pagamento.METODO_CREDITO,
    'debit_card': Pagamento.METODO_DEBITO,
    'bolbradesco': Pagamento.METODO_BOLETO,
    'pec': Pagamento.METODO_BOLETO,
    'account_money': Pagamento.METODO_TRANSFERENCIA,
}


@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    from core.mercadopago import buscar_pagamento, validar_assinatura
    from django.db import transaction

    if not validar_assinatura(request):
        logger.warning('MP webhook: assinatura inválida')
        return JsonResponse({'status': 'error', 'detail': 'Invalid signature'}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'detail': 'Invalid JSON'}, status=400)

    if body.get('type') != 'payment':
        return JsonResponse({'status': 'ok', 'detail': 'ignored'})

    payment_id = body.get('data', {}).get('id')
    if not payment_id:
        return JsonResponse({'status': 'error', 'detail': 'Missing payment id'}, status=400)

    try:
        pag_mp = buscar_pagamento(payment_id)
    except Exception:
        logger.exception('MP webhook: falha ao buscar pagamento %s', payment_id)
        return JsonResponse({'status': 'error', 'detail': 'Failed to fetch payment'}, status=500)

    if pag_mp.get('status') != 'approved':
        return JsonResponse({'status': 'ok', 'detail': 'payment not approved'})

    external_ref = pag_mp.get('external_reference')
    if not external_ref:
        logger.warning('MP webhook: payment %s sem external_reference', payment_id)
        return JsonResponse({'status': 'ok', 'detail': 'no external_reference'})

    try:
        site_id = int(external_ref)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'ok', 'detail': 'external_reference inválido'})

    try:
        pedido = Pedido.objects.get(site_id=site_id)
    except Pedido.DoesNotExist:
        logger.warning('MP webhook: pedido site_id=%s não encontrado', site_id)
        return JsonResponse({'status': 'ok', 'detail': 'pedido not found'})

    if pedido.status == Pedido.STATUS_PAGO:
        return JsonResponse({'status': 'ok', 'detail': 'already paid', 'pedido_id': str(pedido.id)})

    metodo = _MP_METODO_MAP.get(pag_mp.get('payment_method_id', ''), Pagamento.METODO_TRANSFERENCIA)
    valor = Decimal(str(pag_mp.get('transaction_amount') or pedido.total_liquido))

    with transaction.atomic():
        pedido.status = Pedido.STATUS_PAGO
        pedido.save(update_fields=['status'])

        Pagamento.objects.get_or_create(
            pedido=pedido,
            defaults={
                'metodo': metodo,
                'valor': valor,
                'status': Pagamento.STATUS_APROVADO,
                'pago_em': timezone.now(),
            },
        )

    logger.info('MP webhook: pedido %s marcado como pago (payment %s)', pedido.id, payment_id)
    return JsonResponse({'status': 'ok', 'pedido_id': str(pedido.id)})


@staff_member_required
def relatorio_vendas_csv(request):
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')

    qs = Pedido.objects.select_related('cliente').prefetch_related('itens__produto')
    if inicio:
        qs = qs.filter(criado_em__date__gte=inicio)
    if fim:
        qs = qs.filter(criado_em__date__lte=fim)
    qs = qs.order_by('criado_em')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="vendas.csv"'
    response.write('﻿')  # BOM para Excel

    writer = csv.writer(response)
    writer.writerow(['Data', 'Pedido', 'Cliente', 'Canal', 'Status', 'Total (R$)', 'Itens'])

    status_labels = dict(Pedido.STATUS_CHOICES)
    canal_labels = dict(Pedido.CANAL_CHOICES)

    for pedido in qs:
        itens_resumo = '; '.join(
            f'{item.produto.nome} x{item.quantidade}'
            for item in pedido.itens.all()
        )
        writer.writerow([
            pedido.criado_em.strftime('%d/%m/%Y'),
            str(pedido.id)[:8].upper(),
            pedido.cliente.nome,
            canal_labels.get(pedido.canal, pedido.canal),
            status_labels.get(pedido.status, pedido.status),
            f'{pedido.total_liquido:.2f}'.replace('.', ','),
            itens_resumo,
        ])

    return response


@staff_member_required
def relatorio_estoque_csv(request):
    from produtos.models import VariacaoProduto

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="estoque.csv"'
    response.write('﻿')  # BOM para Excel

    writer = csv.writer(response)
    writer.writerow(['SKU', 'Produto', 'Variação', 'Estoque Atual', 'Estoque Mínimo', 'Custo (R$)', 'Preço Venda (R$)'])

    produtos = (
        Produto.objects
        .filter(status='ativo')
        .prefetch_related('variacoes')
        .order_by('nome')
    )

    for produto in produtos:
        variacoes = list(produto.variacoes.filter(ativo=True))
        if variacoes:
            for var in variacoes:
                writer.writerow([
                    var.sku_variacao,
                    produto.nome,
                    f'{var.cor} / {var.tamanho}'.strip(' /'),
                    var.estoque,
                    var.estoque_minimo,
                    f'{var.custo:.2f}'.replace('.', ','),
                    f'{var.preco_venda:.2f}'.replace('.', ','),
                ])
        else:
            writer.writerow([
                produto.sku,
                produto.nome,
                '',
                produto.estoque_total,
                produto.estoque_minimo,
                f'{produto.custo:.2f}'.replace('.', ','),
                f'{produto.preco_venda:.2f}'.replace('.', ','),
            ])

    return response


def _importar_pedido_unico(site_id):
    from django.db import transaction
    from django.db.models import F as _F

    sp = SitePedido.objects.using('site').prefetch_related('itens__produto').get(pk=site_id)

    with transaction.atomic():
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
