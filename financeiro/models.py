from django.db import models
from core.models import TimeStampedModel


class ContaReceber(TimeStampedModel):
    STATUS_PENDENTE = 'pendente'
    STATUS_RECEBIDO = 'recebido'
    STATUS_VENCIDO = 'vencido'
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_RECEBIDO, 'Recebido'),
        (STATUS_VENCIDO, 'Vencido'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='contas_receber',
        verbose_name='Cliente',
    )
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_receber',
        verbose_name='Pedido',
    )
    descricao = models.CharField('Descrição', max_length=200)
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    vencimento = models.DateField('Vencimento')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    recebido_em = models.DateField('Recebido em', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['vencimento']

    def __str__(self):
        return f'{self.cliente.nome} — R$ {self.valor} ({self.vencimento})'


class ContaPagar(TimeStampedModel):
    STATUS_PENDENTE = 'pendente'
    STATUS_PAGO = 'pago'
    STATUS_VENCIDO = 'vencido'
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PAGO, 'Pago'),
        (STATUS_VENCIDO, 'Vencido'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    categoria = models.CharField('Categoria', max_length=100)
    descricao = models.CharField('Descrição', max_length=200)
    fornecedor = models.ForeignKey(
        'produtos.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_pagar',
        verbose_name='Fornecedor',
    )
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    vencimento = models.DateField('Vencimento')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    pago_em = models.DateField('Pago em', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['vencimento']

    def __str__(self):
        return f'{self.categoria} — {self.descricao} — R$ {self.valor}'
