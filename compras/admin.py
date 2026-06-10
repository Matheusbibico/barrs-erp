from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import ItemPedidoCompra, ItemRecebimento, PedidoCompra, RecebimentoMercadoria

_STATUS_COR = {
    'rascunho':          '#9E9488',
    'enviado':           '#6B95B8',
    'recebido_parcial':  '#C8A040',
    'recebido':          '#8A947C',
    'cancelado':         '#C07070',
}


class ItemPedidoCompraInline(TabularInline):
    model = ItemPedidoCompra
    extra = 1
    fields = ('produto', 'variacao', 'quantidade', 'custo_unitario')
    autocomplete_fields = ('produto',)


class ItemRecebimentoInline(TabularInline):
    model = ItemRecebimento
    extra = 0
    fields = ('item_pedido_compra', 'quantidade_recebida', 'condicao')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'item_pedido_compra' and request.resolver_match.kwargs.get('object_id'):
            parent_id = request.resolver_match.kwargs['object_id']
            try:
                rec = RecebimentoMercadoria.objects.get(pk=parent_id)
                kwargs['queryset'] = ItemPedidoCompra.objects.filter(
                    pedido_compra=rec.pedido_compra
                ).select_related('produto', 'variacao')
            except RecebimentoMercadoria.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PedidoCompra)
class PedidoCompraAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = ('__str__', 'fornecedor', 'status_badge', 'total', 'previsao_entrega', 'criado_em')
    list_filter = ('status', 'fornecedor')
    search_fields = ('fornecedor__nome', 'numero', 'observacoes')
    list_select_related = ('fornecedor',)
    readonly_fields = ('total', 'criado_em', 'atualizado_em')
    inlines = [ItemPedidoCompraInline]
    fieldsets = (
        ('Pedido', {
            'fields': ('fornecedor', 'numero', 'status', 'previsao_entrega'),
        }),
        ('Valores', {
            'fields': ('total',),
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
        cor = _STATUS_COR.get(obj.status, '#9E9488')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
            cor,
            obj.get_status_display(),
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalcular_total()


@admin.register(RecebimentoMercadoria)
class RecebimentoMercadoriaAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = ('pedido_compra', 'data', 'usuario', 'confirmado')
    list_filter = ('confirmado', 'data')
    search_fields = ('pedido_compra__fornecedor__nome',)
    list_select_related = ('pedido_compra__fornecedor', 'usuario')
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines = [ItemRecebimentoInline]
    fieldsets = (
        ('Recebimento', {
            'fields': ('pedido_compra', 'data', 'usuario', 'confirmado'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )
