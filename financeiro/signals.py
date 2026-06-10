from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pedidos.Pagamento')
def pagamento_aprovado_gera_lancamento(sender, instance, **kwargs):
    from .models import CategoriaFinanceira, LancamentoCaixa

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

    cat, _ = CategoriaFinanceira.objects.get_or_create(
        nome='Vendas',
        tipo=CategoriaFinanceira.TIPO_RECEITA,
    )

    data = instance.pago_em.date() if instance.pago_em else instance.criado_em.date()

    LancamentoCaixa.objects.create(
        data=data,
        tipo=LancamentoCaixa.TIPO_ENTRADA,
        valor=instance.valor,
        categoria=cat,
        descricao=f'Pagamento pedido #{instance.pedido.id}',
        pedido=instance.pedido,
        conciliado=False,
    )


@receiver(post_save, sender='financeiro.ContaPagar')
def conta_pagar_paga_gera_lancamento(sender, instance, **kwargs):
    from .models import CategoriaFinanceira, LancamentoCaixa

    if instance.status != 'pago':
        return

    if LancamentoCaixa.objects.filter(conta_pagar=instance).exists():
        return

    cat, _ = CategoriaFinanceira.objects.get_or_create(
        nome=instance.categoria or 'Despesas Gerais',
        tipo=CategoriaFinanceira.TIPO_DESPESA,
    )

    data = instance.pago_em or instance.criado_em.date()

    LancamentoCaixa.objects.create(
        data=data,
        tipo=LancamentoCaixa.TIPO_SAIDA,
        valor=instance.valor,
        categoria=cat,
        descricao=instance.descricao,
        conta_pagar=instance,
        conciliado=False,
    )
