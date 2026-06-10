from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import CategoriaFinanceira, ContaPagar, ContaReceber, LancamentoCaixa

_STATUS_COR = {
    'pendente':  '#C8A040',
    'recebido':  '#8A947C',
    'pago':      '#8A947C',
    'vencido':   '#C07070',
    'cancelado': '#9E9488',
}


def _badge(obj):
    cor = _STATUS_COR.get(obj.status, '#9E9488')
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 10px;'
        'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
        cor,
        obj.get_status_display(),
    )


@admin.register(ContaReceber)
class ContaReceberAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = ('cliente', 'descricao', 'valor', 'status_badge', 'vencimento', 'recebido_em')
    list_filter = ('status', 'vencimento')
    search_fields = ('cliente__nome', 'descricao')
    list_select_related = ('cliente', 'pedido')
    date_hierarchy = 'vencimento'
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Conta', {
            'fields': ('cliente', 'pedido', 'descricao', 'valor'),
        }),
        ('Status', {
            'fields': ('status', 'vencimento', 'recebido_em'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return _badge(obj)


@admin.register(ContaPagar)
class ContaPagarAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = (
        'categoria', 'descricao', 'fornecedor',
        'valor', 'status_badge', 'vencimento', 'pago_em',
    )
    list_filter = ('status', 'categoria', 'vencimento')
    search_fields = ('descricao', 'categoria', 'fornecedor__nome')
    list_select_related = ('fornecedor',)
    date_hierarchy = 'vencimento'
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Conta', {
            'fields': ('categoria', 'descricao', 'fornecedor', 'valor'),
        }),
        ('Status', {
            'fields': ('status', 'vencimento', 'pago_em'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return _badge(obj)


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ('nome', 'tipo', 'pai')
    list_filter = ('tipo',)
    search_fields = ('nome',)
    list_select_related = ('pai',)


_TIPO_COR = {
    'entrada': '#8A947C',
    'saida': '#C07070',
}


@admin.register(LancamentoCaixa)
class LancamentoCaixaAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = (
        'data', 'tipo_badge', 'descricao', 'categoria',
        'valor', 'conciliado', 'pedido',
    )
    list_filter = ('tipo', 'conciliado', 'categoria', 'data')
    search_fields = ('descricao', 'categoria__nome')
    list_select_related = ('categoria', 'pedido', 'conta_receber', 'conta_pagar')
    date_hierarchy = 'data'
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Lançamento', {
            'fields': ('data', 'tipo', 'valor', 'categoria', 'descricao', 'conciliado'),
        }),
        ('Vínculos', {
            'fields': ('pedido', 'conta_receber', 'conta_pagar'),
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
