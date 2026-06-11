from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pedidos.Pagamento')
def pagamento_aprovado_gera_lancamento(sender, instance, **kwargs):
    from .models import LancamentoCaixa

    if instance.status != 'aprovado':
        return

    if LancamentoCaixa.objects.filter(
        pedido=instance.pedido,
        conta_receber=None,
        conta_pagar=None,
        descricao__startswith='Pagamento pedido',
    ).filter(
        tipo=LancamentoCaixa.TIPO_ENTRADA,
    ).exists():
        return

    data = instance.pago_em.date() if instance.pago_em else instance.criado_em.date()

    LancamentoCaixa.objects.create(
        data=data,
        tipo=LancamentoCaixa.TIPO_ENTRADA,
        valor=instance.valor,
        descricao=f'Pagamento pedido #{instance.pedido.id}',
        pedido=instance.pedido,
        conciliado=False,
    )


@receiver(post_save, sender='financeiro.ContaPagar')
def conta_pagar_paga_gera_lancamento(sender, instance, **kwargs):
    from .models import LancamentoCaixa

    if instance.status != 'pago':
        return

    if LancamentoCaixa.objects.filter(conta_pagar=instance).exists():
        return

    data = instance.pago_em or instance.criado_em.date()

    LancamentoCaixa.objects.create(
        data=data,
        tipo=LancamentoCaixa.TIPO_SAIDA,
        valor=instance.valor,
        descricao=instance.descricao,
        conta_pagar=instance,
        conciliado=False,
    )
