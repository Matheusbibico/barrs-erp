from django.contrib import admin
from .models import Cliente, EnderecoCliente


class EnderecoClienteInline(admin.TabularInline):
    model = EnderecoCliente
    extra = 0
    fields = ('apelido', 'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'principal')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'whatsapp', 'email', 'cidade', 'estado',
        'total_gasto', 'qtd_pedidos', 'ultima_compra', 'ativo',
    )
    list_filter = ('ativo', 'estado')
    search_fields = ('nome', 'whatsapp', 'email')
    list_editable = ('ativo',)
    readonly_fields = ('total_gasto', 'qtd_pedidos', 'primeira_compra', 'ultima_compra', 'criado_em', 'atualizado_em')
    inlines = [EnderecoClienteInline]
    fieldsets = (
        ('Dados Pessoais', {'fields': ('nome', 'whatsapp', 'email', 'ativo')}),
        ('Endereço', {'fields': ('cidade', 'estado')}),
        ('Histórico', {'fields': ('primeira_compra', 'ultima_compra', 'total_gasto', 'qtd_pedidos')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Sistema', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )
