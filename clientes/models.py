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
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)

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


class EnderecoCliente(TimeStampedModel):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='enderecos',
        verbose_name='Cliente',
    )
    apelido = models.CharField('Apelido', max_length=50, blank=True, help_text='Ex: Casa, Trabalho')
    cep = models.CharField('CEP', max_length=9)
    logradouro = models.CharField('Logradouro', max_length=200)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado (UF)', max_length=2)
    principal = models.BooleanField('Principal', default=False)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
        ordering = ['-principal', 'apelido']

    def __str__(self):
        return f'{self.logradouro}, {self.numero} — {self.cidade}/{self.estado}'

    def save(self, *args, **kwargs):
        if self.principal:
            from django.db import transaction
            with transaction.atomic():
                super().save(*args, **kwargs)
                EnderecoCliente.objects.filter(
                    cliente=self.cliente, principal=True
                ).exclude(pk=self.pk).update(principal=False)
        else:
            super().save(*args, **kwargs)
