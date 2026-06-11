from django.db import models
from core.models import TimeStampedModel


class CategoriaFinanceira(TimeStampedModel):
    TIPO_RECEITA = 'receita'
    TIPO_DESPESA = 'despesa'
    TIPO_CHOICES = [
        (TIPO_RECEITA, 'Receita'),
        (TIPO_DESPESA, 'Despesa'),
    ]

    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = 'Categoria Financeira'
        verbose_name_plural = 'Categorias Financeiras'
        ordering = ['tipo', 'nome']

    def __str__(self):
        return self.nome


class LancamentoCaixa(TimeStampedModel):
    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saída'),
    ]

    data = models.DateField('Data')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    categoria = models.ForeignKey(
        CategoriaFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Categoria',
    )
    descricao = models.CharField('Descrição', max_length=200)
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_caixa',
        verbose_name='Pedido',
    )
    conta_receber = models.ForeignKey(
        'ContaReceber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Conta a Receber',
    )
    conta_pagar = models.ForeignKey(
        'ContaPagar',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Conta a Pagar',
    )
    conciliado = models.BooleanField('Conciliado', default=False)

    class Meta:
        verbose_name = 'Lançamento de Caixa'
        verbose_name_plural = 'Lançamentos de Caixa'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        sinal = '+' if self.tipo == self.TIPO_ENTRADA else '-'
        return f'{self.data} {sinal}R$ {self.valor} — {self.descricao}'


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
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    pago_em = models.DateField('Pago em', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_PAGO and not self.pago_em:
            from django.utils import timezone
            self.pago_em = timezone.localdate()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['vencimento']

    def __str__(self):
        return f'{self.categoria} — {self.descricao} — R$ {self.valor}'


class MetaMensal(models.Model):
    ano = models.PositiveSmallIntegerField('Ano')
    mes = models.PositiveSmallIntegerField('Mês')
    valor_meta = models.DecimalField('Meta de Faturamento (R$)', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Meta Mensal'
        verbose_name_plural = 'Metas Mensais'
        unique_together = [('ano', 'mes')]
        ordering = ['-ano', '-mes']

    def __str__(self):
        import calendar
        return f'{calendar.month_name[self.mes].capitalize()}/{self.ano} — R$ {self.valor_meta}'
