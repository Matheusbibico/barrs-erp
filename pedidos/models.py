from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from core.models import TimeStampedModel


class Pedido(TimeStampedModel):
    CANAL_SITE = 'site'
    CANAL_WHATSAPP = 'whatsapp'
    CANAL_INSTAGRAM = 'instagram'
    CANAL_PRESENCIAL = 'presencial'
    CANAL_LINK = 'link'
    CANAL_CHOICES = [
        (CANAL_SITE, 'Site'),
        (CANAL_WHATSAPP, 'WhatsApp'),
        (CANAL_INSTAGRAM, 'Instagram'),
        (CANAL_PRESENCIAL, 'Presencial'),
        (CANAL_LINK, 'Link de Pagamento'),
    ]

    STATUS_ORCAMENTO = 'orcamento'
    STATUS_RESERVADO = 'reservado'
    STATUS_AGUARDANDO = 'aguardando_pagamento'
    STATUS_PAGO = 'pago'
    STATUS_SEPARACAO = 'separacao'
    STATUS_ENVIADO = 'enviado'
    STATUS_ENTREGUE = 'entregue'
    STATUS_CANCELADO = 'cancelado'
    STATUS_TROCA_PENDENTE = 'troca_pendente'
    STATUS_DEVOLVIDO = 'devolvido'
    STATUS_CHOICES = [
        (STATUS_ORCAMENTO, 'Orçamento'),
        (STATUS_RESERVADO, 'Reservado'),
        (STATUS_AGUARDANDO, 'Aguardando Pagamento'),
        (STATUS_PAGO, 'Pago'),
        (STATUS_SEPARACAO, 'Em Separação'),
        (STATUS_ENVIADO, 'Enviado'),
        (STATUS_ENTREGUE, 'Entregue'),
        (STATUS_TROCA_PENDENTE, 'Troca Pendente'),
        (STATUS_DEVOLVIDO, 'Devolvido'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Cliente',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Vendedor',
    )
    canal = models.CharField('Canal', max_length=20, choices=CANAL_CHOICES)
    status = models.CharField('Status', max_length=30, choices=STATUS_CHOICES, default=STATUS_ORCAMENTO)
    total_bruto = models.DecimalField('Total Bruto (R$)', max_digits=12, decimal_places=2, default=0)
    desconto = models.DecimalField('Desconto (R$)', max_digits=12, decimal_places=2, default=0)
    frete = models.DecimalField('Frete (R$)', max_digits=10, decimal_places=2, default=0)
    total_liquido = models.DecimalField('Total Líquido (R$)', max_digits=12, decimal_places=2, default=0)
    endereco_entrega = models.TextField('Endereço de Entrega', blank=True)
    observacoes = models.TextField('Observações', blank=True)
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
    endereco_estruturado = models.ForeignKey(
        'clientes.EnderecoCliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Endereço de Entrega',
    )
    transportadora = models.CharField('Transportadora', max_length=100, blank=True)
    codigo_rastreio = models.CharField('Código de Rastreio', max_length=50, blank=True, db_index=True)
    url_rastreio = models.URLField('URL de Rastreio', blank=True)
    previsao_entrega = models.DateField('Previsão de Entrega', null=True, blank=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'Pedido #{str(self.id)[:8].upper()} — {self.cliente.nome}'

    def calcular_totais(self):
        total = sum(item.subtotal for item in self.itens.all())
        self.total_bruto = total
        self.total_liquido = total - self.desconto + self.frete

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('update_fields'):
            self.total_liquido = self.total_bruto - self.desconto + self.frete
        super().save(*args, **kwargs)


class ItemPedido(TimeStampedModel):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido',
    )
    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        related_name='itens_pedido',
        verbose_name='Produto',
    )
    variacao = models.ForeignKey(
        'produtos.VariacaoProduto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_pedido',
        verbose_name='Variação',
    )
    quantidade = models.PositiveIntegerField('Quantidade')
    preco_unitario = models.DecimalField('Preço Unitário (R$)', max_digits=10, decimal_places=2)
    custo_unitario = models.DecimalField('Custo Unitário (R$)', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'

    def clean(self):
        if self.variacao_id and self.produto_id:
            if str(self.variacao.produto_id) != str(self.produto_id):
                raise ValidationError({'variacao': 'A variação deve pertencer ao produto selecionado.'})

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade

    @property
    def custo_total(self):
        return self.custo_unitario * self.quantidade


class Pagamento(TimeStampedModel):
    METODO_PIX = 'pix'
    METODO_CREDITO = 'cartao_credito'
    METODO_DEBITO = 'cartao_debito'
    METODO_BOLETO = 'boleto'
    METODO_DINHEIRO = 'dinheiro'
    METODO_TRANSFERENCIA = 'transferencia'
    METODO_CHOICES = [
        (METODO_PIX, 'PIX'),
        (METODO_CREDITO, 'Cartão de Crédito'),
        (METODO_DEBITO, 'Cartão de Débito'),
        (METODO_BOLETO, 'Boleto'),
        (METODO_DINHEIRO, 'Dinheiro'),
        (METODO_TRANSFERENCIA, 'Transferência'),
    ]

    STATUS_PENDENTE = 'pendente'
    STATUS_APROVADO = 'aprovado'
    STATUS_RECUSADO = 'recusado'
    STATUS_ESTORNADO = 'estornado'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_RECUSADO, 'Recusado'),
        (STATUS_ESTORNADO, 'Estornado'),
    ]

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name='Pedido',
    )
    metodo = models.CharField('Método', max_length=20, choices=METODO_CHOICES)
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    parcelas = models.PositiveSmallIntegerField('Nº de Parcelas', default=1)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    pago_em = models.DateTimeField('Pago em', null=True, blank=True)
    observacoes = models.CharField('Observações', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_metodo_display()} — R$ {self.valor}'


class LucroPedido(TimeStampedModel):
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='lucro',
        verbose_name='Pedido',
    )
    receita_bruta = models.DecimalField('Receita Bruta (R$)', max_digits=12, decimal_places=2, default=0)
    custo_produtos = models.DecimalField('Custo dos Produtos (R$)', max_digits=12, decimal_places=2, default=0)
    taxa_pagamento = models.DecimalField('Taxa de Pagamento (R$)', max_digits=10, decimal_places=2, default=0)
    frete = models.DecimalField('Frete (R$)', max_digits=10, decimal_places=2, default=0)
    embalagem = models.DecimalField('Embalagem (R$)', max_digits=10, decimal_places=2, default=0)
    lucro_liquido = models.DecimalField('Lucro Líquido (R$)', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Lucro do Pedido'
        verbose_name_plural = 'Lucros dos Pedidos'

    def __str__(self):
        return f'Lucro — {self.pedido}'

    def recalcular(self):
        self.lucro_liquido = (
            self.receita_bruta
            - self.custo_produtos
            - self.taxa_pagamento
            - self.frete
            - self.embalagem
        )


class EventoRastreio(TimeStampedModel):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='eventos_rastreio',
        verbose_name='Pedido',
    )
    data_evento = models.DateTimeField('Data do Evento')
    status = models.CharField('Status', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    local = models.CharField('Local', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Evento de Rastreio'
        verbose_name_plural = 'Eventos de Rastreio'
        ordering = ['-data_evento']

    def __str__(self):
        return f'{self.pedido} — {self.status} ({self.data_evento:%d/%m/%Y})'


class Devolucao(TimeStampedModel):
    TIPO_REEMBOLSO = 'reembolso'
    TIPO_TROCA = 'troca'
    TIPO_CREDITO = 'credito'
    TIPO_CHOICES = [
        (TIPO_REEMBOLSO, 'Reembolso'),
        (TIPO_TROCA, 'Troca'),
        (TIPO_CREDITO, 'Crédito em Conta'),
    ]

    STATUS_SOLICITADA = 'solicitada'
    STATUS_APROVADA = 'aprovada'
    STATUS_RECUSADA = 'recusada'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CHOICES = [
        (STATUS_SOLICITADA, 'Solicitada'),
        (STATUS_APROVADA, 'Aprovada'),
        (STATUS_RECUSADA, 'Recusada'),
        (STATUS_CONCLUIDA, 'Concluída'),
    ]

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name='devolucoes',
        verbose_name='Pedido',
    )
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    motivo = models.TextField('Motivo')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_SOLICITADA)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Responsável',
    )
    observacoes = models.TextField('Observações', blank=True)
    aprovada_em = models.DateTimeField('Aprovada em', null=True, blank=True)

    class Meta:
        verbose_name = 'Devolução'
        verbose_name_plural = 'Devoluções'
        ordering = ['-criado_em']

    def __str__(self):
        return f'Devolução #{str(self.id)[:8].upper()} — {self.pedido}'


class ItemDevolucao(TimeStampedModel):
    CONDICAO_OK = 'ok'
    CONDICAO_DEFEITO = 'defeito'
    CONDICAO_AVARIA = 'avaria'
    CONDICAO_CHOICES = [
        (CONDICAO_OK, 'Em bom estado'),
        (CONDICAO_DEFEITO, 'Com defeito'),
        (CONDICAO_AVARIA, 'Avariado'),
    ]

    devolucao = models.ForeignKey(
        Devolucao,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Devolução',
    )
    item_pedido = models.ForeignKey(
        ItemPedido,
        on_delete=models.PROTECT,
        related_name='itens_devolucao',
        verbose_name='Item do Pedido',
    )
    quantidade = models.PositiveIntegerField('Quantidade')
    condicao = models.CharField('Condição', max_length=20, choices=CONDICAO_CHOICES, default=CONDICAO_OK)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Item de Devolução'
        verbose_name_plural = 'Itens de Devolução'

    def __str__(self):
        return f'{self.quantidade}x {self.item_pedido.produto.nome} ({self.get_condicao_display()})'


class ParcelaPagamento(TimeStampedModel):
    STATUS_PENDENTE = 'pendente'
    STATUS_PAGO = 'pago'
    STATUS_VENCIDO = 'vencido'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PAGO, 'Pago'),
        (STATUS_VENCIDO, 'Vencido'),
    ]

    pagamento = models.ForeignKey(
        Pagamento,
        on_delete=models.CASCADE,
        related_name='itens_parcela',
        verbose_name='Pagamento',
    )
    numero = models.PositiveSmallIntegerField('Nº da Parcela')
    vencimento = models.DateField('Vencimento')
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    pago_em = models.DateField('Pago em', null=True, blank=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['pagamento', 'numero']

    def __str__(self):
        return f'Parcela {self.numero}/{self.pagamento.parcelas} — R$ {self.valor}'
