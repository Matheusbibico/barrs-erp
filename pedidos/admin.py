from django.contrib import admin
from django.utils.html import format_html
from .models import Pedido, ItemPedido, Pagamento, LucroPedido, EventoRastreio

STATUS_CORES = {
    'orcamento': '#6c757d',
    'reservado': '#17a2b8',
    'aguardando_pagamento': '#ffc107',
    'pago': '#28a745',
    'separacao': '#007bff',
    'enviado': '#fd7e14',
    'entregue': '#20c997',
    'cancelado': '#dc3545',
}


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    fields = ('produto', 'variacao', 'quantidade', 'preco_unitario', 'custo_unitario')
    autocomplete_fields = ['produto', 'variacao']


class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0
    fields = ('metodo', 'valor', 'status', 'pago_em')


class EventoRastreioInline(admin.TabularInline):
    model = EventoRastreio
    extra = 0
    fields = ('data_evento', 'status', 'descricao', 'local')
    ordering = ['-data_evento']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'cliente', 'canal', 'status_badge',
        'total_liquido', 'usuario', 'criado_em',
    )
    list_filter = ('status', 'canal', 'criado_em')
    search_fields = ('cliente__nome', 'cliente__whatsapp', 'id')
    list_select_related = ('cliente', 'usuario')
    readonly_fields = ('total_bruto', 'criado_em', 'atualizado_em')
    inlines = [ItemPedidoInline, PagamentoInline, EventoRastreioInline]
    date_hierarchy = 'criado_em'
    fieldsets = (
        ('Pedido', {'fields': ('cliente', 'usuario', 'canal', 'status')}),
        ('Valores', {'fields': ('total_bruto', 'desconto', 'frete', 'total_liquido')}),
        ('Entrega', {'fields': ('endereco_entrega', 'endereco_estruturado', 'transportadora', 'codigo_rastreio', 'url_rastreio', 'previsao_entrega')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Código')
    def codigo(self, obj):
        return f'#{str(obj.id)[:8].upper()}'

    @admin.display(description='Status')
    def status_badge(self, obj):
        cor = STATUS_CORES.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            cor,
            obj.get_status_display(),
        )


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'metodo', 'valor', 'status', 'pago_em')
    list_filter = ('status', 'metodo')
    search_fields = ('pedido__cliente__nome',)
    list_select_related = ('pedido', 'pedido__cliente')


@admin.register(LucroPedido)
class LucroPedidoAdmin(admin.ModelAdmin):
    list_display = (
        'pedido', 'receita_bruta', 'custo_produtos',
        'taxa_pagamento', 'frete', 'embalagem', 'lucro_liquido',
    )
    search_fields = ('pedido__cliente__nome',)
    list_select_related = ('pedido', 'pedido__cliente')
    readonly_fields = ('pedido', 'receita_bruta', 'custo_produtos', 'lucro_liquido', 'criado_em', 'atualizado_em')
    fieldsets = (
        ('Pedido', {'fields': ('pedido',)}),
        ('Receitas', {'fields': ('receita_bruta',)}),
        ('Custos', {'fields': ('custo_produtos', 'taxa_pagamento', 'frete', 'embalagem')}),
        ('Resultado', {'fields': ('lucro_liquido',)}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
