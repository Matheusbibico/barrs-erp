from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class PedidoCompra(TimeStampedModel):
    STATUS_RASCUNHO = 'rascunho'
    STATUS_ENVIADO = 'enviado'
    STATUS_RECEBIDO_PARCIAL = 'recebido_parcial'
    STATUS_RECEBIDO = 'recebido'
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_RASCUNHO, 'Rascunho'),
        (STATUS_ENVIADO, 'Enviado ao Fornecedor'),
        (STATUS_RECEBIDO_PARCIAL, 'Recebido Parcialmente'),
        (STATUS_RECEBIDO, 'Recebido Completo'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    fornecedor = models.ForeignKey(
        'produtos.Fornecedor',
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
        verbose_name='Fornecedor',
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    total = models.DecimalField('Total (R$)', max_digits=12, decimal_places=2, default=0)
    previsao_entrega = models.DateField('Previsão de Entrega', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    numero = models.CharField('Nº do Pedido', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Pedido de Compra'
        verbose_name_plural = 'Pedidos de Compra'
        ordering = ['-criado_em']

    def __str__(self):
        return f'PC-{str(self.id)[:8].upper()} — {self.fornecedor.nome}'

    def recalcular_total(self):
        from django.db.models import DecimalField, ExpressionWrapper, F, Sum
        total = self.itens.aggregate(
            v=Sum(ExpressionWrapper(F('quantidade') * F('custo_unitario'), output_field=DecimalField()))
        )['v'] or 0
        self.total = total
        self.save(update_fields=['total'])


class ItemPedidoCompra(TimeStampedModel):
    pedido_compra = models.ForeignKey(
        PedidoCompra,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido de Compra',
    )
    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        related_name='itens_compra',
        verbose_name='Produto',
    )
    variacao = models.ForeignKey(
        'produtos.VariacaoProduto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_compra',
        verbose_name='Variação',
    )
    quantidade = models.PositiveIntegerField('Quantidade')
    custo_unitario = models.DecimalField('Custo Unitário (R$)', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item do Pedido de Compra'
        verbose_name_plural = 'Itens do Pedido de Compra'

    def __str__(self):
        nome = str(self.variacao) if self.variacao else self.produto.nome
        return f'{self.quantidade}x {nome} — R$ {self.custo_unitario}'

    @property
    def custo_total(self):
        return self.quantidade * self.custo_unitario


class RecebimentoMercadoria(TimeStampedModel):
    pedido_compra = models.ForeignKey(
        PedidoCompra,
        on_delete=models.PROTECT,
        related_name='recebimentos',
        verbose_name='Pedido de Compra',
    )
    data = models.DateField('Data do Recebimento')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Recebido por',
    )
    observacoes = models.TextField('Observações', blank=True)
    confirmado = models.BooleanField('Confirmado', default=False)

    class Meta:
        verbose_name = 'Recebimento de Mercadoria'
        verbose_name_plural = 'Recebimentos de Mercadoria'
        ordering = ['-data']

    def __str__(self):
        return f'Recebimento {self.data} — {self.pedido_compra}'


class ItemRecebimento(TimeStampedModel):
    CONDICAO_OK = 'ok'
    CONDICAO_AVARIA = 'avaria'
    CONDICAO_CHOICES = [
        (CONDICAO_OK, 'Ok'),
        (CONDICAO_AVARIA, 'Avariado'),
    ]

    recebimento = models.ForeignKey(
        RecebimentoMercadoria,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Recebimento',
    )
    item_pedido_compra = models.ForeignKey(
        ItemPedidoCompra,
        on_delete=models.PROTECT,
        related_name='itens_recebimento',
        verbose_name='Item do Pedido',
    )
    quantidade_recebida = models.PositiveIntegerField('Qtd Recebida')
    condicao = models.CharField('Condição', max_length=10, choices=CONDICAO_CHOICES, default=CONDICAO_OK)

    class Meta:
        verbose_name = 'Item de Recebimento'
        verbose_name_plural = 'Itens de Recebimento'

    def __str__(self):
        return f'{self.quantidade_recebida}x {self.item_pedido_compra.produto.nome} ({self.get_condicao_display()})'
