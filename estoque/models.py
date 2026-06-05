from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class MovimentoEstoque(TimeStampedModel):
    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPO_AJUSTE = 'ajuste'
    TIPO_PERDA = 'perda'
    TIPO_TROCA = 'troca'
    TIPO_RESERVA = 'reserva'
    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saída'),
        (TIPO_AJUSTE, 'Ajuste'),
        (TIPO_PERDA, 'Perda'),
        (TIPO_TROCA, 'Troca'),
        (TIPO_RESERVA, 'Reserva'),
    ]

    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name='Produto',
    )
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_estoque',
        verbose_name='Pedido',
    )
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    quantidade = models.IntegerField('Quantidade')
    saldo_anterior = models.IntegerField('Saldo Anterior')
    saldo_posterior = models.IntegerField('Saldo Posterior')
    motivo = models.TextField('Motivo', blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário',
    )

    class Meta:
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.produto.nome} ({self.quantidade:+d})'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.saldo_anterior = self.produto.estoque_total
            self.saldo_posterior = self.saldo_anterior + self.quantidade
            self.produto.estoque_total = self.saldo_posterior
            self.produto.save(update_fields=['estoque_total'])
        super().save(*args, **kwargs)
