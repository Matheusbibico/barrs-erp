from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cliente, EnderecoCliente


class EnderecoClienteInline(TabularInline):
    model = EnderecoCliente
    extra = 0
    fields = (
        'apelido', 'cep', 'logradouro', 'numero',
        'complemento', 'bairro', 'cidade', 'estado', 'principal',
    )


@admin.register(Cliente)
class ClienteAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth = True
    list_display = (
        'nome', 'whatsapp', 'email', 'cidade', 'estado',
        'total_gasto', 'qtd_pedidos', 'ultima_compra', 'ativo',
    )
    list_filter = ('ativo', 'estado')
    search_fields = ('nome', 'whatsapp', 'email')
    list_editable = ('ativo',)
    readonly_fields = (
        'total_gasto', 'qtd_pedidos',
        'primeira_compra', 'ultima_compra',
        'criado_em', 'atualizado_em',
    )
    inlines = [EnderecoClienteInline]
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome', 'whatsapp', 'email', 'ativo'),
        }),
        ('Localização', {
            'fields': ('cidade', 'estado'),
        }),
        ('Histórico de Compras', {
            'fields': ('primeira_compra', 'ultima_compra', 'total_gasto', 'qtd_pedidos'),
        }),
        ('Observações', {
            'fields': ('observacoes',),
        }),
        ('Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )
