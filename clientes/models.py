from django.db import models
from core.models import TimeStampedModel


class Cliente(TimeStampedModel):
    nome = models.CharField('Nome', max_length=200)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado (UF)', max_length=2, blank=True)
    primeira_compra = models.DateField('Primeira Compra', null=True, blank=True)
    ultima_compra = models.DateField('Última Compra', null=True, blank=True)
    total_gasto = models.DecimalField('Total Gasto (R$)', max_digits=12, decimal_places=2, default=0)
    qtd_pedidos = models.PositiveIntegerField('Qtd. Pedidos', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    observacoes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def ticket_medio(self):
        if self.qtd_pedidos:
            return round(self.total_gasto / self.qtd_pedidos, 2)
        return 0
