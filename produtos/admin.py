from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Fornecedor, Produto, FotoProduto, VariacaoProduto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'ativa', 'criado_em')
    list_filter = ('ativa',)
    search_fields = ('nome',)
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ('ativa',)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'whatsapp', 'email', 'cidade', 'estado', 'ativo')
    list_filter = ('ativo', 'estado')
    search_fields = ('nome', 'email', 'whatsapp')
    list_editable = ('ativo',)


class FotoProdutoInline(admin.TabularInline):
    model = FotoProduto
    extra = 1
    fields = ('imagem', 'principal', 'ordem')


class VariacaoProdutoInline(admin.TabularInline):
    model = VariacaoProduto
    extra = 1
    fields = ('cor', 'tamanho', 'sku_variacao', 'custo', 'preco_venda', 'estoque', 'ativo')


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'nome', 'categoria', 'preco_venda', 'custo',
        'estoque_total', 'estoque_reservado', 'status_badge',
    )
    list_filter = ('status', 'categoria', 'fornecedor')
    search_fields = ('sku', 'nome', 'descricao')
    list_select_related = ('categoria', 'fornecedor')
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines = [FotoProdutoInline, VariacaoProdutoInline]
    fieldsets = (
        ('Identificação', {'fields': ('sku', 'nome', 'categoria', 'fornecedor', 'status')}),
        ('Descrição', {'fields': ('descricao',)}),
        ('Preços', {'fields': ('custo', 'preco_venda')}),
        ('Estoque', {'fields': ('estoque_total', 'estoque_reservado')}),
        ('Datas', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        cores = {'ativo': '#28a745', 'inativo': '#dc3545', 'rascunho': '#ffc107'}
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            cor,
            obj.get_status_display(),
        )


@admin.register(VariacaoProduto)
class VariacaoProdutoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'cor', 'tamanho', 'sku_variacao', 'estoque', 'ativo')
    list_filter = ('ativo', 'cor')
    search_fields = ('sku_variacao', 'produto__nome', 'cor', 'tamanho')
    list_select_related = ('produto',)
