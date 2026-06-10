from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Devolucao, EventoRastreio, ItemDevolucao,
    ItemPedido, LucroPedido, Pagamento, Pedido,
)

# Cores Barrs para cada status de pedido
_STATUS_PEDIDO_COR = {
    'orcamento':           '#9E9488',
    'reservado':           '#6B95B8',
    'aguardando_pagamento': '#C8A040',
    'pago':                '#8A947C',
    'separacao':           '#7BA3C0',
    'enviado':             '#B8962A',
    'entregue':            '#6BA080',
    'troca_pendente':      '#A87CC0',
    'devolvido':           '#8070A0',
    'cancelado':           '#C07070',
}

_STATUS_DEVOLUCAO_COR = {
    'solicitada': '#C8A040',
    'aprovada':   '#8A947C',
    'recusada':   '#C07070',
    'concluida':  '#6BA080',
}


class ItemPedidoInline(TabularInline):
    model = ItemPedido
    extra = 1
    fields = ('produto', 'variacao', 'quantidade', 'preco_unitario', 'custo_unitario')
    autocomplete_fields = ['produto', 'variacao']


class PagamentoInline(TabularInline):
    model = Pagamento
    extra = 0
    fields = ('metodo', 'valor', 'status', 'pago_em')


class EventoRastreioInline(TabularInline):
    model = EventoRastreio
    extra = 0
    fields = ('data_evento', 'status', 'descricao', 'local')
    ordering = ['-data_evento']


@admin.register(Pedido)
class PedidoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_per_page = 25
    show_full_result_count = False
    list_display = (
        'codigo', 'cliente', 'canal', 'status_badge',
        'total_liquido', 'usuario', 'criado_em',
    )
    list_filter = ('status', 'canal', 'criado_em')
    ordering = ['-id']
    search_fields = ('=id', 'cliente__nome', 'cliente__whatsapp')
    list_select_related = ('cliente', 'usuario')
    readonly_fields = ('total_bruto', 'criado_em', 'atualizado_em')
    inlines = [ItemPedidoInline, PagamentoInline, EventoRastreioInline]
    date_hierarchy = 'criado_em'
    fieldsets = (
        ('Pedido', {
            'fields': ('cliente', 'usuario', 'canal', 'status'),
        }),
        ('Valores', {
            'fields': ('total_bruto', 'desconto', 'frete', 'total_liquido'),
        }),
        ('Entrega e Rastreio', {
            'fields': (
                'endereco_entrega', 'endereco_estruturado',
                'transportadora', 'codigo_rastreio', 'url_rastreio', 'previsao_entrega',
            ),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Código', ordering='id')
    def codigo(self, obj):
        return f'#{str(obj.id)[:8].upper()}'

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        cor = _STATUS_PEDIDO_COR.get(obj.status, '#9E9488')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
            cor,
            obj.get_status_display(),
        )


@admin.register(Pagamento)
class PagamentoAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth = True
    list_display = ('pedido', 'metodo', 'valor', 'status', 'pago_em')
    list_filter = ('status', 'metodo')
    search_fields = ('pedido__cliente__nome',)
    list_select_related = ('pedido', 'pedido__cliente')
    fieldsets = (
        ('Pagamento', {
            'fields': ('pedido', 'metodo', 'valor'),
        }),
        ('Status', {
            'fields': ('status', 'pago_em', 'observacoes'),
        }),
    )


@admin.register(LucroPedido)
class LucroPedidoAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth = True
    list_display = (
        'pedido', 'receita_bruta', 'custo_produtos',
        'taxa_pagamento', 'frete', 'embalagem', 'lucro_liquido',
    )
    search_fields = ('pedido__cliente__nome',)
    list_select_related = ('pedido', 'pedido__cliente')
    readonly_fields = (
        'pedido', 'receita_bruta', 'custo_produtos',
        'lucro_liquido', 'criado_em', 'atualizado_em',
    )
    fieldsets = (
        ('Pedido', {
            'fields': ('pedido',),
        }),
        ('Receitas', {
            'fields': ('receita_bruta',),
        }),
        ('Custos', {
            'fields': ('custo_produtos', 'taxa_pagamento', 'frete', 'embalagem'),
        }),
        ('Resultado', {
            'fields': ('lucro_liquido',),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ItemDevolucaoInline(TabularInline):
    model = ItemDevolucao
    extra = 1
    fields = ('item_pedido', 'quantidade', 'condicao', 'observacao')


@admin.register(Devolucao)
class DevolucaoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = ('codigo', 'pedido', 'tipo', 'status_badge', 'responsavel', 'criado_em')
    list_filter = ('status', 'tipo', 'criado_em')
    search_fields = ('pedido__cliente__nome', 'motivo')
    list_select_related = ('pedido', 'pedido__cliente', 'responsavel')
    readonly_fields = ('aprovada_em', 'criado_em', 'atualizado_em')
    inlines = [ItemDevolucaoInline]
    actions = ['aprovar_devolucoes', 'recusar_devolucoes']
    fieldsets = (
        ('Devolução', {
            'fields': ('pedido', 'tipo', 'motivo', 'status', 'responsavel'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Datas', {
            'fields': ('aprovada_em', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Código')
    def codigo(self, obj):
        return f'#{str(obj.id)[:8].upper()}'

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        cor = _STATUS_DEVOLUCAO_COR.get(obj.status, '#9E9488')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
            cor,
            obj.get_status_display(),
        )

    @admin.action(description='Aprovar devoluções selecionadas')
    def aprovar_devolucoes(self, request, queryset):
        try:
            with transaction.atomic():
                count = 0
                for devolucao in queryset.filter(status='solicitada'):
                    devolucao.status = 'aprovada'
                    devolucao.responsavel = request.user
                    devolucao.save()
                    count += 1
            self.message_user(request, f'{count} devolução(ões) aprovada(s).')
        except Exception as exc:
            self.message_user(request, f'Erro ao aprovar devoluções: {exc}', level='error')

    @admin.action(description='Recusar devoluções selecionadas')
    def recusar_devolucoes(self, request, queryset):
        count = queryset.filter(status='solicitada').update(status='recusada')
        self.message_user(request, f'{count} devolução(ões) recusada(s).')
