from django.db.models import Sum
from django.utils import timezone


def dashboard_callback(request, context):
    """
    Injeta estatísticas no contexto da página inicial do Django Admin (Unfold).
    Chamado via UNFOLD["DASHBOARD_CALLBACK"] em settings.py.
    """
    # Importações aqui para evitar ciclos de importação na inicialização
    from pedidos.models import Pedido
    from produtos.models import Produto
    from clientes.models import Cliente
    from financeiro.models import ContaReceber, ContaPagar

    hoje = timezone.localdate()
    mes_inicio = hoje.replace(day=1)

    STATUS_FATURADOS = ['pago', 'enviado', 'entregue']

    pedidos_hoje = Pedido.objects.filter(criado_em__date=hoje).count()
    pedidos_mes = Pedido.objects.filter(criado_em__date__gte=mes_inicio).count()
    clientes_total = Cliente.objects.filter(ativo=True).count()
    produtos_ativos = Produto.objects.filter(status='ativo').count()

    faturamento_mes = (
        Pedido.objects.filter(
            criado_em__date__gte=mes_inicio,
            status__in=STATUS_FATURADOS,
        ).aggregate(total=Sum('total_liquido'))['total']
        or 0
    )
    ticket_medio_mes = faturamento_mes / pedidos_mes if pedidos_mes else 0

    pedidos_aguardando = Pedido.objects.filter(
        status='aguardando_pagamento'
    ).count()

    # Produtos ativos com estoque total < 5 (inclui zerados)
    estoque_baixo_count = Produto.objects.filter(
        status='ativo',
        estoque_total__lt=5,
    ).count()

    contas_vencidas = ContaReceber.objects.filter(
        status='pendente',
        vencimento__lt=hoje,
    ).count()

    contas_pagar_vencidas = ContaPagar.objects.filter(
        status='pendente',
        vencimento__lt=hoje,
    ).count()

    ultimos_pedidos = (
        Pedido.objects.select_related('cliente', 'usuario')
        .order_by('-criado_em')[:8]
    )

    context.update({
        "barrs_stats": {
            "pedidos_hoje": pedidos_hoje,
            "pedidos_mes": pedidos_mes,
            "faturamento_mes": faturamento_mes,
            "ticket_medio_mes": ticket_medio_mes,
            "clientes_total": clientes_total,
            "produtos_ativos": produtos_ativos,
            "pedidos_aguardando": pedidos_aguardando,
            "estoque_baixo": estoque_baixo_count,
            "contas_vencidas": contas_vencidas,
            "contas_pagar_vencidas": contas_pagar_vencidas,
        },
        "barrs_ultimos_pedidos": ultimos_pedidos,
    })
    return context
