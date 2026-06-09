from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import MovimentoEstoque

_TIPO_COR = {
    'entrada': '#8A947C',
    'saida':   '#C07070',
    'ajuste':  '#6B95B8',
    'perda':   '#C07070',
    'troca':   '#C8A96A',
    'reserva': '#9E9488',
}


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth = True
    list_display = (
        'produto', 'variacao', 'tipo_badge', 'quantidade',
        'saldo_anterior', 'saldo_posterior', 'pedido', 'usuario', 'criado_em',
    )
    list_filter = ('tipo', 'criado_em')
    search_fields = ('produto__nome', 'produto__sku', 'motivo')
    list_select_related = ('produto', 'variacao', 'pedido', 'usuario')
    readonly_fields = ('saldo_anterior', 'saldo_posterior', 'criado_em', 'atualizado_em')
    date_hierarchy = 'criado_em'
    fieldsets = (
        ('Movimento', {
            'fields': ('produto', 'variacao', 'tipo', 'quantidade', 'pedido', 'usuario'),
        }),
        ('Saldos', {
            'fields': ('saldo_anterior', 'saldo_posterior'),
        }),
        ('Motivo', {
            'fields': ('motivo',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Tipo', ordering='tipo')
    def tipo_badge(self, obj):
        cor = _TIPO_COR.get(obj.tipo, '#9E9488')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
            cor,
            obj.get_tipo_display(),
        )

    # Movimentos são auditoria — não podem ser editados
    def has_change_permission(self, request, obj=None):
        return False
