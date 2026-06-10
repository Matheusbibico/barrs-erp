from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Categoria, Fornecedor, Produto, VariacaoProduto

# Mapeamento status → cor Barrs (hex)
_STATUS_PRODUTO_COR = {
    'ativo':    '#8A947C',
    'inativo':  '#C07070',
    'rascunho': '#C8A96A',
}


@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ('nome', 'ativa', 'criado_em')
    list_filter = ('ativa',)
    search_fields = ('nome',)
    list_editable = ('ativa',)
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'ativa'),
        }),
        ('Descrição', {
            'fields': ('descricao',),
        }),
    )


@admin.register(Fornecedor)
class FornecedorAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = ('nome', 'contato', 'whatsapp', 'email', 'cidade', 'estado', 'ativo')
    list_filter = ('ativo', 'estado')
    search_fields = ('nome', 'email', 'whatsapp', 'contato')
    list_editable = ('ativo',)
    fieldsets = (
        ('Dados do Fornecedor', {
            'fields': ('nome', 'contato', 'ativo'),
        }),
        ('Contato', {
            'fields': ('whatsapp', 'email'),
        }),
        ('Localização', {
            'fields': ('cidade', 'estado'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
    )


class VariacaoProdutoInline(TabularInline):
    model = VariacaoProduto
    extra = 1
    fields = ('cor', 'tamanho', 'sku_variacao', 'custo', 'preco_venda', 'estoque', 'estoque_minimo', 'ativo')


@admin.register(Produto)
class ProdutoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = (
        'sku', 'nome', 'categoria', 'preco_venda', 'custo',
        'estoque_total', 'status_badge',
    )
    list_filter = ('status', 'categoria', 'fornecedor')
    search_fields = ('sku', 'nome', 'descricao')
    list_select_related = ('categoria', 'fornecedor')
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines = [VariacaoProdutoInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('sku', 'nome', 'categoria', 'fornecedor', 'status', 'site_id', 'imagem_url'),
        }),
        ('Descrição', {
            'fields': ('descricao',),
        }),
        ('Preços', {
            'fields': ('custo', 'preco_venda'),
        }),
        ('Estoque', {
            'fields': ('estoque_total', 'estoque_minimo'),
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        cor = _STATUS_PRODUTO_COR.get(obj.status, '#9E9488')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:6px;font-size:11px;font-weight:500;">{}</span>',
            cor,
            obj.get_status_display(),
        )


@admin.register(VariacaoProduto)
class VariacaoProdutoAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth = True
    list_display = ('produto', 'cor', 'tamanho', 'sku_variacao', 'estoque', 'ativo')
    list_filter = ('ativo', 'cor')
    search_fields = ('sku_variacao', 'produto__nome', 'cor', 'tamanho')
    list_select_related = ('produto',)
    fieldsets = (
        ('Produto', {
            'fields': ('produto',),
        }),
        ('Variação', {
            'fields': ('cor', 'tamanho', 'sku_variacao', 'ativo'),
        }),
        ('Preços e Estoque', {
            'fields': ('custo', 'preco_venda', 'estoque', 'estoque_minimo'),
        }),
    )
