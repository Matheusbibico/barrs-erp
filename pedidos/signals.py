from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pedidos.Pedido')
def calcular_lucro_pedido(sender, instance, **kwargs):
    """Cria ou atualiza LucroPedido automaticamente quando o pedido é marcado como pago."""
    if instance.status != 'pago':
        return

    from .models import LucroPedido

    custo_produtos = sum(
        item.custo_unitario * item.quantidade
        for item in instance.itens.all()
    )

    lucro, _ = LucroPedido.objects.get_or_create(pedido=instance)
    lucro.receita_bruta = instance.total_liquido
    lucro.custo_produtos = custo_produtos
    lucro.frete = instance.frete
    lucro.recalcular()
    lucro.save()


@receiver(post_save, sender='pedidos.Pedido')
def atualizar_historico_cliente(sender, instance, **kwargs):
    """Atualiza total_gasto e qtd_pedidos do cliente ao confirmar pagamento."""
    if instance.status != 'pago':
        return

    from django.db.models import Sum, Count
    from pedidos.models import Pedido

    cliente = instance.cliente
    agregado = Pedido.objects.filter(
        cliente=cliente,
        status='pago',
    ).aggregate(total=Sum('total_liquido'), qtd=Count('id'))

    from django.utils import timezone

    cliente.total_gasto = agregado['total'] or 0
    cliente.qtd_pedidos = agregado['qtd'] or 0
    cliente.ultima_compra = instance.criado_em.date()
    if not cliente.primeira_compra:
        cliente.primeira_compra = instance.criado_em.date()
    cliente.save(update_fields=['total_gasto', 'qtd_pedidos', 'ultima_compra', 'primeira_compra'])


@receiver(post_save, sender='pedidos.Devolucao')
def processar_aprovacao_devolucao(sender, instance, **kwargs):
    """Ao aprovar devolução: reverte estoque dos itens em bom estado e cria registro financeiro."""
    if instance.status != 'aprovada':
        return

    if instance.aprovada_em:
        return  # Já processado — evita duplicação de MovimentoEstoque e ContaReceber

    from django.db import transaction
    from django.utils import timezone as tz
    from estoque.models import MovimentoEstoque
    from financeiro.models import ContaReceber

    with transaction.atomic():
        # 1. Reverte estoque dos itens em bom estado
        for item_dev in instance.itens.select_related(
            'item_pedido__produto', 'item_pedido__variacao'
        ).all():
            if item_dev.condicao == 'ok':
                MovimentoEstoque.objects.create(
                    produto=item_dev.item_pedido.produto,
                    variacao=item_dev.item_pedido.variacao,
                    tipo=MovimentoEstoque.TIPO_ENTRADA,
                    quantidade=item_dev.quantidade,
                    motivo=f'Devolução aprovada #{str(instance.id)[:8].upper()}',
                    usuario=instance.responsavel,
                )

        # 2. Para reembolso: cria ContaReceber com valor negativo (estorno)
        if instance.tipo == 'reembolso':
            valor_reembolso = sum(
                item.item_pedido.preco_unitario * item.quantidade
                for item in instance.itens.all()
            )
            if valor_reembolso > 0:
                ContaReceber.objects.create(
                    cliente=instance.pedido.cliente,
                    pedido=instance.pedido,
                    descricao=f'[ESTORNO] Reembolso — Devolução #{str(instance.id)[:8].upper()}',
                    valor=-valor_reembolso,
                    vencimento=tz.localdate(),
                    status='recebido',  # Estorno já efetivado
                    observacoes='Estorno gerado automaticamente por aprovação de devolução tipo reembolso.',
                )

        # 3. Atualiza status do pedido
        if instance.tipo == 'troca':
            instance.pedido.status = 'troca_pendente'
        else:
            instance.pedido.status = 'devolvido'
        instance.pedido.save(update_fields=['status', 'atualizado_em'])

        # 4. Registra aprovada_em se ainda não preenchido
        if not instance.aprovada_em:
            sender.objects.filter(pk=instance.pk).update(aprovada_em=tz.now())
