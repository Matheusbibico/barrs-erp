from django.contrib import admin
from .models import MovimentoEstoque


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'variacao', 'tipo', 'quantidade', 'saldo_anterior', 'saldo_posterior', 'pedido', 'criado_em')
    list_filter = ('tipo', 'criado_em')
    search_fields = ('produto__nome', 'produto__sku', 'motivo')
    list_select_related = ('produto', 'pedido', 'usuario')
    readonly_fields = ('saldo_anterior', 'saldo_posterior', 'criado_em', 'atualizado_em')
    date_hierarchy = 'criado_em'
    fieldsets = (
        ('Movimento', {'fields': ('produto', 'variacao', 'tipo', 'quantidade', 'pedido', 'usuario')}),
        ('Saldos', {'fields': ('saldo_anterior', 'saldo_posterior')}),
        ('Motivo', {'fields': ('motivo',)}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def has_change_permission(self, request, obj=None):
        return False
