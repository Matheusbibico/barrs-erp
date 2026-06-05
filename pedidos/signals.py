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
