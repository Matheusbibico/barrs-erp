from django.contrib import admin
from django.utils.html import format_html
from .models import ContaReceber, ContaPagar

STATUS_CORES = {
    'pendente': '#ffc107',
    'recebido': '#28a745',
    'pago': '#28a745',
    'vencido': '#dc3545',
    'cancelado': '#6c757d',
}


def status_badge(obj):
    cor = STATUS_CORES.get(obj.status, '#6c757d')
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
        cor,
        obj.get_status_display(),
    )


status_badge.short_description = 'Status'


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'descricao', 'valor', status_badge, 'vencimento', 'recebido_em')
    list_filter = ('status', 'vencimento')
    search_fields = ('cliente__nome', 'descricao')
    list_select_related = ('cliente', 'pedido')
    date_hierarchy = 'vencimento'
    fieldsets = (
        ('Conta', {'fields': ('cliente', 'pedido', 'descricao', 'valor')}),
        ('Status', {'fields': ('status', 'vencimento', 'recebido_em')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('criado_em', 'atualizado_em')


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'descricao', 'fornecedor', 'valor', status_badge, 'vencimento', 'pago_em')
    list_filter = ('status', 'categoria', 'vencimento')
    search_fields = ('descricao', 'categoria', 'fornecedor__nome')
    list_select_related = ('fornecedor',)
    date_hierarchy = 'vencimento'
    fieldsets = (
        ('Conta', {'fields': ('categoria', 'descricao', 'fornecedor', 'valor')}),
        ('Status', {'fields': ('status', 'vencimento', 'pago_em')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('criado_em', 'atualizado_em')
