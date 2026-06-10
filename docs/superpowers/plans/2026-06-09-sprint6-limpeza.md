# Sprint 6 — Limpeza do Sistema: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remover complexidade que não gera valor — campos mortos, models desnecessários no admin e sidebar inflada — deixando o sistema enxuto para uma loja pequena.

**Architecture:** 3 camadas de mudança executadas em ordem: (1) model changes + migrations, (2) admin/signals/views cleanup, (3) sidebar. Cada tarefa termina em commit atômico. Nenhum dado é apagado do banco — apenas tabelas/campos de admin são desativados.

**Tech Stack:** Django 5.2, django-unfold, DRF 3.15, PostgreSQL/SQLite, Python 3.13. Venv em `.venv/`. Rodar comandos com `.venv/bin/python manage.py` ou via `source .venv/bin/activate`.

---

## Files Overview

| Arquivo | O que muda |
|---------|-----------|
| `produtos/models.py` | Remove `estoque_reservado`, `estoque_disponivel`, `Categoria.slug`; adiciona `Produto.imagem_url` |
| `financeiro/models.py` | Remove `CategoriaFinanceira.pai` |
| `pedidos/models.py` | Remove `STATUS_RESERVADO`, `STATUS_SEPARACAO`; adiciona `Pedido.lucro_calculado` |
| `pedidos/admin.py` | Remove `LucroPedidoAdmin`, `EventoRastreioInline`, `ParcelaPagamentoInline` |
| `pedidos/signals.py` | Remove `calcular_lucro_pedido` e `gerar_parcelas_pagamento` |
| `pedidos/serializers.py` | Remove `LucroPedidoSerializer`, `EventoRastreioSerializer`; adiciona `lucro_calculado` |
| `pedidos/views.py` | Remove `LucroPedidoViewSet`, `EventoRastreioViewSet` |
| `pedidos/urls.py` | Remove rotas de lucros e eventos-rastreio |
| `produtos/admin.py` | Remove `FotoProdutoInline`, `estoque_reservado`; remove `slug` de `CategoriaAdmin`; adiciona `imagem_url` |
| `core/views.py` | Substitui queries `LucroPedido` por anotações em `ItemPedido` |
| `financeiro/views.py` | Substitui CMV de `LucroPedido` por soma de `ItemPedido` |
| `barrs_erp/settings/base.py` | Simplifica sidebar UNFOLD para 10 itens |

---

## Task 1: Model — Produto e Categoria

**Files:**
- Modify: `produtos/models.py`

- [ ] **Step 1: Remover `estoque_reservado` e `estoque_disponivel` de `Produto`; remover `slug` e `save()` de `Categoria`; adicionar `imagem_url` em `Produto`**

Em `produtos/models.py`:

Substitua a classe `Categoria` completa por:
```python
class Categoria(TimeStampedModel):
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    ativa = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome
```

Na classe `Produto`, remova o campo `estoque_reservado`:
```python
# Remover esta linha:
estoque_reservado = models.IntegerField('Estoque Reservado', default=0)
```

Adicione `imagem_url` logo após `site_id`:
```python
site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
imagem_url = models.URLField('URL da Imagem', blank=True, default='')
```

Remova a propriedade `estoque_disponivel` de `Produto` (as linhas abaixo devem ser deletadas):
```python
@property
def estoque_disponivel(self):
    return self.estoque_total - self.estoque_reservado
```

- [ ] **Step 2: Gerar migration para produtos**

```bash
cd /Users/bibico/Documents/projetos/barrs-erp
.venv/bin/python manage.py makemigrations produtos --name "sprint6_remove_slug_estoque_reservado_add_imagem_url"
```

Saída esperada: `Migrations for 'produtos': produtos/migrations/0004_sprint6_...py`

- [ ] **Step 3: Verificar migration gerada**

```bash
.venv/bin/python manage.py sqlmigrate produtos 0004
```

Saída esperada: `ALTER TABLE "produtos_produto" DROP COLUMN "estoque_reservado"`, `ALTER TABLE "produtos_produto" ADD COLUMN "imagem_url"`, `ALTER TABLE "produtos_categoria" DROP COLUMN "slug"`.

- [ ] **Step 4: Aplicar migration**

```bash
.venv/bin/python manage.py migrate produtos
```

Saída esperada: `Applying produtos.0004_sprint6... OK`

- [ ] **Step 5: Commit**

```bash
git add produtos/models.py produtos/migrations/0004_sprint6_remove_slug_estoque_reservado_add_imagem_url.py
git commit -m "feat(sprint6): remove estoque_reservado, slug; adiciona imagem_url em Produto"
```

---

## Task 2: Model — CategoriaFinanceira e Pedido

**Files:**
- Modify: `financeiro/models.py`
- Modify: `pedidos/models.py`

- [ ] **Step 1: Remover `pai` de `CategoriaFinanceira` e atualizar `__str__`**

Em `financeiro/models.py`, substitua a classe `CategoriaFinanceira` por:
```python
class CategoriaFinanceira(TimeStampedModel):
    TIPO_RECEITA = 'receita'
    TIPO_DESPESA = 'despesa'
    TIPO_CHOICES = [
        (TIPO_RECEITA, 'Receita'),
        (TIPO_DESPESA, 'Despesa'),
    ]

    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = 'Categoria Financeira'
        verbose_name_plural = 'Categorias Financeiras'
        ordering = ['tipo', 'nome']

    def __str__(self):
        return self.nome
```

- [ ] **Step 2: Gerar migration para financeiro**

```bash
.venv/bin/python manage.py makemigrations financeiro --name "sprint6_remove_categoriafinanceira_pai"
```

Saída esperada: `Migrations for 'financeiro': financeiro/migrations/0003_sprint6...py`

- [ ] **Step 3: Remover status `reservado` e `separacao` de `Pedido`; adicionar `lucro_calculado`**

Em `pedidos/models.py`, na classe `Pedido`:

Remova as constantes e entradas em `STATUS_CHOICES` referentes a `reservado` e `separacao`. O bloco de STATUS deve ficar assim:
```python
STATUS_ORCAMENTO = 'orcamento'
STATUS_AGUARDANDO = 'aguardando_pagamento'
STATUS_PAGO = 'pago'
STATUS_ENVIADO = 'enviado'
STATUS_ENTREGUE = 'entregue'
STATUS_CANCELADO = 'cancelado'
STATUS_TROCA_PENDENTE = 'troca_pendente'
STATUS_DEVOLVIDO = 'devolvido'
STATUS_CHOICES = [
    (STATUS_ORCAMENTO, 'Orçamento'),
    (STATUS_AGUARDANDO, 'Aguardando Pagamento'),
    (STATUS_PAGO, 'Pago'),
    (STATUS_ENVIADO, 'Enviado'),
    (STATUS_ENTREGUE, 'Entregue'),
    (STATUS_TROCA_PENDENTE, 'Troca Pendente'),
    (STATUS_DEVOLVIDO, 'Devolvido'),
    (STATUS_CANCELADO, 'Cancelado'),
]
```

Adicione a propriedade `lucro_calculado` no final da classe `Pedido` (antes de `ItemPedido`):
```python
@property
def lucro_calculado(self):
    custo = sum(
        item.custo_unitario * item.quantidade
        for item in self.itens.all()
    )
    return self.total_liquido - custo
```

- [ ] **Step 4: Gerar migration para pedidos**

```bash
.venv/bin/python manage.py makemigrations pedidos --name "sprint6_remove_status_reservado_separacao"
```

Saída esperada: `Migrations for 'pedidos': pedidos/migrations/0007_sprint6...py`

- [ ] **Step 5: Aplicar todas as migrations pendentes**

```bash
.venv/bin/python manage.py migrate
```

Saída esperada: `Applying financeiro.0003... OK`, `Applying pedidos.0007... OK`

- [ ] **Step 6: Verificar que o sistema não tem erros**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Commit**

```bash
git add financeiro/models.py financeiro/migrations/ pedidos/models.py pedidos/migrations/0007_sprint6_remove_status_reservado_separacao.py
git commit -m "feat(sprint6): remove pai de CategoriaFinanceira, remove status reservado/separacao, adiciona lucro_calculado"
```

---

## Task 3: Admin — Pedidos

**Files:**
- Modify: `pedidos/admin.py`

- [ ] **Step 1: Atualizar imports no topo de `pedidos/admin.py`**

Substitua o bloco de imports do arquivo por:
```python
from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Devolucao, ItemDevolucao,
    ItemPedido, Pagamento, Pedido,
)
```

- [ ] **Step 2: Remover `EventoRastreioInline` e atualizar `PedidoAdmin.inlines`**

Remova a classe `EventoRastreioInline` inteira:
```python
# DELETAR:
class EventoRastreioInline(TabularInline):
    model = EventoRastreio
    extra = 0
    fields = ('data_evento', 'status', 'descricao', 'local')
    ordering = ['-data_evento']
```

Na classe `PedidoAdmin`, altere `inlines`:
```python
inlines = [ItemPedidoInline, PagamentoInline]
```

- [ ] **Step 3: Remover `ParcelaPagamentoInline` e atualizar `PagamentoAdmin.inlines`**

Remova a classe `ParcelaPagamentoInline` inteira:
```python
# DELETAR:
class ParcelaPagamentoInline(TabularInline):
    model = ParcelaPagamento
    fk_name = 'pagamento'
    extra = 0
    readonly_fields = ('numero', 'vencimento', 'valor', 'pago_em')
    fields = ('numero', 'vencimento', 'valor', 'status', 'pago_em')
```

Na classe `PagamentoAdmin`, remova `inlines = [ParcelaPagamentoInline]` (deixe sem inlines ou remova a linha).

- [ ] **Step 4: Remover `LucroPedidoAdmin`**

Remova o bloco inteiro:
```python
# DELETAR:
@admin.register(LucroPedido)
class LucroPedidoAdmin(ModelAdmin):
    ...  # classe inteira
```

- [ ] **Step 5: Remover entradas de `reservado` e `separacao` do dicionário de cores**

Em `_STATUS_PEDIDO_COR`, remova as entradas:
```python
# REMOVER estas duas linhas:
'reservado':           '#6B95B8',
'separacao':           '#7BA3C0',
```

O dicionário final deve ser:
```python
_STATUS_PEDIDO_COR = {
    'orcamento':           '#9E9488',
    'aguardando_pagamento': '#C8A040',
    'pago':                '#8A947C',
    'enviado':             '#B8962A',
    'entregue':            '#6BA080',
    'troca_pendente':      '#A87CC0',
    'devolvido':           '#8070A0',
    'cancelado':           '#C07070',
}
```

- [ ] **Step 6: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Commit**

```bash
git add pedidos/admin.py
git commit -m "feat(sprint6): remove LucroPedidoAdmin, EventoRastreioInline, ParcelaPagamentoInline do admin"
```

---

## Task 4: Admin — Produtos

**Files:**
- Modify: `produtos/admin.py`

- [ ] **Step 1: Atualizar imports e remover `FotoProdutoInline`**

No topo de `produtos/admin.py`, substitua a linha de imports dos models:
```python
from .models import Categoria, Fornecedor, Produto, VariacaoProduto
```

Remova a classe `FotoProdutoInline` inteira:
```python
# DELETAR:
class FotoProdutoInline(TabularInline):
    model = FotoProduto
    extra = 1
    fields = ('imagem', 'principal', 'ordem')
```

- [ ] **Step 2: Atualizar `ProdutoAdmin`**

Em `ProdutoAdmin.list_display`, remova `estoque_reservado`:
```python
list_display = (
    'sku', 'nome', 'categoria', 'preco_venda', 'custo',
    'estoque_total', 'status_badge',
)
```

Em `ProdutoAdmin.inlines`, remova `FotoProdutoInline`:
```python
inlines = [VariacaoProdutoInline]
```

Em `ProdutoAdmin.fieldsets`, substitua o fieldset de Estoque por:
```python
('Imagem', {
    'fields': ('imagem_url',),
}),
('Estoque', {
    'fields': ('estoque_total',),
}),
```

- [ ] **Step 3: Atualizar `CategoriaAdmin`**

Substitua a classe `CategoriaAdmin` por:
```python
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
```

- [ ] **Step 4: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add produtos/admin.py
git commit -m "feat(sprint6): remove FotoProdutoInline, estoque_reservado e slug do admin de produtos"
```

---

## Task 5: Signals — Remover calcular_lucro_pedido e gerar_parcelas_pagamento

**Files:**
- Modify: `pedidos/signals.py`

- [ ] **Step 1: Reescrever `pedidos/signals.py` removendo os dois signals**

Substitua o conteúdo completo do arquivo por (mantendo apenas os dois signals que continuam válidos):

```python
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pedidos.Pedido')
def atualizar_historico_cliente(sender, instance, **kwargs):
    """Atualiza total_gasto e qtd_pedidos do cliente ao confirmar pagamento."""
    if instance.status != 'pago':
        return

    from django.db.models import Sum, Count
    from pedidos.models import Pedido

    cliente = instance.cliente
    agregado = Pedido.objects.filter(
        cliente=cliente,
        status='pago',
    ).aggregate(total=Sum('total_liquido'), qtd=Count('id'))

    from django.utils import timezone

    cliente.total_gasto = agregado['total'] or 0
    cliente.qtd_pedidos = agregado['qtd'] or 0
    cliente.ultima_compra = instance.criado_em.date()
    if not cliente.primeira_compra:
        cliente.primeira_compra = instance.criado_em.date()
    cliente.save(update_fields=['total_gasto', 'qtd_pedidos', 'ultima_compra', 'primeira_compra'])


@receiver(post_save, sender='pedidos.Devolucao')
def processar_aprovacao_devolucao(sender, instance, **kwargs):
    """Ao aprovar devolução: reverte estoque dos itens em bom estado e cria registro financeiro."""
    if instance.status != 'aprovada':
        return

    if instance.aprovada_em:
        return  # Já processado — evita duplicação de MovimentoEstoque e ContaReceber

    from django.db import transaction
    from django.utils import timezone as tz
    from estoque.models import MovimentoEstoque
    from financeiro.models import ContaReceber

    with transaction.atomic():
        # 1. Reverte estoque dos itens em bom estado
        for item_dev in instance.itens.select_related(
            'item_pedido__produto', 'item_pedido__variacao'
        ).all():
            if item_dev.condicao == 'ok':
                MovimentoEstoque.objects.create(
                    produto=item_dev.item_pedido.produto,
                    variacao=item_dev.item_pedido.variacao,
                    tipo=MovimentoEstoque.TIPO_ENTRADA,
                    quantidade=item_dev.quantidade,
                    motivo=f'Devolução aprovada #{str(instance.id)[:8].upper()}',
                    usuario=instance.responsavel,
                )

        # 2. Para reembolso: cria ContaReceber com valor negativo (estorno)
        if instance.tipo == 'reembolso':
            valor_reembolso = sum(
                item.item_pedido.preco_unitario * item.quantidade
                for item in instance.itens.all()
            )
            if valor_reembolso > 0:
                ContaReceber.objects.create(
                    cliente=instance.pedido.cliente,
                    pedido=instance.pedido,
                    descricao=f'[ESTORNO] Reembolso — Devolução #{str(instance.id)[:8].upper()}',
                    valor=-valor_reembolso,
                    vencimento=tz.localdate(),
                    status='recebido',
                    observacoes='Estorno gerado automaticamente por aprovação de devolução tipo reembolso.',
                )

        # 3. Atualiza status do pedido
        if instance.tipo == 'troca':
            instance.pedido.status = 'troca_pendente'
        else:
            instance.pedido.status = 'devolvido'
        instance.pedido.save(update_fields=['status', 'atualizado_em'])

        # 4. Registra aprovada_em se ainda não preenchido
        if not instance.aprovada_em:
            sender.objects.filter(pk=instance.pk).update(aprovada_em=tz.now())
```

- [ ] **Step 2: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add pedidos/signals.py
git commit -m "feat(sprint6): remove signals calcular_lucro_pedido e gerar_parcelas_pagamento"
```

---

## Task 6: Views — Substituir LucroPedido por anotações em ItemPedido

**Files:**
- Modify: `core/views.py`
- Modify: `financeiro/views.py`

- [ ] **Step 1: Atualizar imports de `core/views.py`**

Localize a linha:
```python
from pedidos.models import ItemPedido, LucroPedido, Pagamento, Pedido
```

Substitua por:
```python
from pedidos.models import ItemPedido, Pagamento, Pedido
```

- [ ] **Step 2: Substituir `lucro_mes` no dashboard**

Localize o bloco (aprox. linha 52):
```python
lucro_mes = (
    LucroPedido.objects.filter(pedido__criado_em__date__gte=inicio_mes)
    .aggregate(v=Sum('lucro_liquido'))['v'] or Decimal('0')
)
```

Substitua por:
```python
from django.db.models import DecimalField, ExpressionWrapper, F as _F
custo_mes = (
    ItemPedido.objects
    .filter(pedido__status='pago', pedido__criado_em__date__gte=inicio_mes)
    .aggregate(
        v=Sum(
            ExpressionWrapper(_F('custo_unitario') * _F('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
    )['v'] or Decimal('0')
)
lucro_mes = faturamento_mes - custo_mes
```

- [ ] **Step 3: Substituir `lucro_qs` (gráfico 30 dias)**

Localize o bloco:
```python
lucro_qs = (
    LucroPedido.objects
    .filter(pedido__criado_em__date__gte=trinta_dias_atras)
    .annotate(dia=TruncDate('pedido__criado_em'))
    .values('dia')
    .annotate(total=Sum('lucro_liquido'))
    .order_by('dia')
)
lucro_dict = {v['dia']: float(v['total']) for v in lucro_qs}
```

Substitua por:
```python
from django.db.models import DecimalField, ExpressionWrapper, F as _F2
custo_qs = (
    ItemPedido.objects
    .filter(pedido__status='pago', pedido__criado_em__date__gte=trinta_dias_atras)
    .annotate(dia=TruncDate('pedido__criado_em'))
    .values('dia')
    .annotate(
        custo=Sum(
            ExpressionWrapper(_F2('custo_unitario') * _F2('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
    )
    .order_by('dia')
)
custo_dict = {v['dia']: float(v['custo']) for v in custo_qs}
```

- [ ] **Step 4: Atualizar o loop de construção dos dados do gráfico**

Localize o loop:
```python
dia = trinta_dias_atras
while dia <= hoje:
    labels.append(dia.strftime('%d/%m'))
    dados.append(vendas_dict.get(dia, 0))
    dados_lucro.append(lucro_dict.get(dia, 0))
    dia += timedelta(days=1)
```

Substitua por (lucro por dia = vendas - custo, `lucro_dict` é removido):
```python
dia = trinta_dias_atras
while dia <= hoje:
    labels.append(dia.strftime('%d/%m'))
    vendas_dia = vendas_dict.get(dia, 0)
    dados.append(vendas_dia)
    dados_lucro.append(vendas_dia - custo_dict.get(dia, 0))
    dia += timedelta(days=1)
```

- [ ] **Step 5: Atualizar `pedidos_pendentes` — remover `reservado` do filtro**

Localize (aprox. linha 55):
```python
pedidos_pendentes = Pedido.objects.filter(
    status__in=['orcamento', 'reservado', 'aguardando_pagamento'],
).count()
```

Substitua por:
```python
pedidos_pendentes = Pedido.objects.filter(
    status__in=['orcamento', 'aguardando_pagamento'],
).count()
```

- [ ] **Step 6: Atualizar `financeiro/views.py` — substituir CMV**

Localize o bloco (aprox. linha 173):
```python
from pedidos.models import ItemPedido, LucroPedido, Pedido
```
Substitua por:
```python
from pedidos.models import ItemPedido, Pedido
```

Localize o bloco do CMV:
```python
cmv = (
    LucroPedido.objects
    .filter(pedido__status='pago', pedido__criado_em__date__gte=inicio, pedido__criado_em__date__lte=fim)
    .aggregate(v=Sum('custo_produtos'))['v'] or Decimal('0')
)
```

Substitua por:
```python
from django.db.models import DecimalField, ExpressionWrapper, F as _F
cmv = (
    ItemPedido.objects
    .filter(pedido__status='pago', pedido__criado_em__date__gte=inicio, pedido__criado_em__date__lte=fim)
    .aggregate(
        v=Sum(
            ExpressionWrapper(_F('custo_unitario') * _F('quantidade'), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
    )['v'] or Decimal('0')
)
```

- [ ] **Step 7: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 8: Commit**

```bash
git add core/views.py financeiro/views.py
git commit -m "feat(sprint6): substitui LucroPedido por ItemPedido annotations no dashboard e DRE"
```

---

## Task 7: API — Serializers, ViewSets e URLs

**Files:**
- Modify: `pedidos/serializers.py`
- Modify: `pedidos/views.py`
- Modify: `pedidos/urls.py`

- [ ] **Step 1: Atualizar `pedidos/serializers.py`**

Substitua o conteúdo completo por:
```python
from rest_framework import serializers
from .models import Pedido, ItemPedido, Pagamento, Devolucao, ItemDevolucao


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku = serializers.CharField(source='produto.sku', read_only=True)
    variacao_descricao = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = '__all__'

    def get_variacao_descricao(self, obj):
        if obj.variacao:
            partes = [p for p in [obj.variacao.cor, obj.variacao.tamanho] if p]
            return ' / '.join(partes) if partes else None
        return None


class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = '__all__'


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    lucro_calculado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'


class PedidoListSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    canal_display = serializers.CharField(source='get_canal_display', read_only=True)

    class Meta:
        model = Pedido
        fields = (
            'id', 'cliente_nome', 'canal', 'canal_display',
            'status', 'status_display', 'total_liquido', 'criado_em',
        )


class PedidoCreateSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = ('cliente', 'usuario', 'canal', 'status', 'desconto', 'frete', 'endereco_entrega', 'observacoes', 'itens')

    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        pedido = Pedido.objects.create(**validated_data)
        for item_data in itens_data:
            item = ItemPedido(pedido=pedido, **item_data)
            item.full_clean()
            item.save()
        pedido.calcular_totais()
        pedido.save()
        return pedido


class ItemDevolucaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='item_pedido.produto.nome', read_only=True)

    class Meta:
        model = ItemDevolucao
        fields = '__all__'


class DevolucaoSerializer(serializers.ModelSerializer):
    itens = ItemDevolucaoSerializer(many=True, read_only=True)
    pedido_codigo = serializers.SerializerMethodField()

    class Meta:
        model = Devolucao
        fields = '__all__'
        read_only_fields = ('aprovada_em',)

    def get_pedido_codigo(self, obj):
        return f'#{str(obj.pedido_id)[:8].upper()}'
```

- [ ] **Step 2: Atualizar `pedidos/views.py` — remover ViewSets de LucroPedido e EventoRastreio**

Localize e remova as duas classes ViewSet abaixo (aprox. linhas 87-94):
```python
# DELETAR:
class LucroPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LucroPedido.objects.select_related('pedido', 'pedido__cliente')
    serializer_class = LucroPedidoSerializer

class EventoRastreioViewSet(viewsets.ModelViewSet):
    queryset = EventoRastreio.objects.select_related('pedido')
    serializer_class = EventoRastreioSerializer
```

Atualize os imports no topo de `pedidos/views.py`:
```python
from .models import Pedido, ItemPedido, Pagamento, Devolucao, ItemDevolucao
from .serializers import (
    PedidoSerializer, PedidoListSerializer, PedidoCreateSerializer,
    ItemPedidoSerializer, PagamentoSerializer, DevolucaoSerializer, ItemDevolucaoSerializer,
)
```

- [ ] **Step 3: Atualizar `pedidos/urls.py`**

Substitua o conteúdo por:
```python
from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, ItemPedidoViewSet, PagamentoViewSet, DevolucaoViewSet

router = DefaultRouter()
router.register('pedidos', PedidoViewSet)
router.register('itens-pedido', ItemPedidoViewSet)
router.register('pagamentos', PagamentoViewSet)
router.register('devolucoes', DevolucaoViewSet)

urlpatterns = router.urls
```

- [ ] **Step 4: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add pedidos/serializers.py pedidos/views.py pedidos/urls.py
git commit -m "feat(sprint6): remove LucroPedidoSerializer/ViewSet e EventoRastreioSerializer/ViewSet da API"
```

---

## Task 8: Sidebar — Simplificar UNFOLD navigation

**Files:**
- Modify: `barrs_erp/settings/base.py`

- [ ] **Step 1: Localizar o bloco `"navigation"` em `barrs_erp/settings/base.py` (aprox. linha 188)**

Substitua o conteúdo completo da lista `"navigation"` por:

```python
"navigation": [
    {
        "title": "Loja",
        "separator": False,
        "collapsible": False,
        "items": [
            {
                "title": "Pedidos",
                "icon": "orders",
                "link": reverse_lazy("admin:pedidos_pedido_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Devoluções",
                "icon": "assignment_returned",
                "link": reverse_lazy("admin:pedidos_devolucao_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Produtos",
                "icon": "inventory",
                "link": reverse_lazy("admin:produtos_produto_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Clientes",
                "icon": "groups",
                "link": reverse_lazy("admin:clientes_cliente_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
        ],
    },
    {
        "title": "Operações",
        "separator": True,
        "collapsible": False,
        "items": [
            {
                "title": "Entrada de Estoque",
                "icon": "warehouse",
                "link": reverse_lazy("admin:estoque_movimentoestoque_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Contas a Receber",
                "icon": "account_balance_wallet",
                "link": reverse_lazy("admin:financeiro_contareceber_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Contas a Pagar",
                "icon": "request_quote",
                "link": reverse_lazy("admin:financeiro_contapagar_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Lançamentos de Caixa",
                "icon": "payments",
                "link": reverse_lazy("admin:financeiro_lancamentocaixa_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Categorias Financeiras",
                "icon": "category",
                "link": reverse_lazy("admin:financeiro_categoriafinanceira_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": "Fornecedores",
                "icon": "local_shipping",
                "link": reverse_lazy("admin:produtos_fornecedor_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
        ],
    },
    {
        "title": "Sistema",
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": "Usuários",
                "icon": "manage_accounts",
                "link": reverse_lazy("admin:auth_user_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": "Grupos",
                "icon": "group",
                "link": reverse_lazy("admin:auth_group_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": "Logs de Atividade",
                "icon": "history",
                "link": reverse_lazy("admin:admin_logentry_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
],
```

- [ ] **Step 2: Verificar**

```bash
.venv/bin/python manage.py check
```

Saída esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Subir o servidor e conferir a sidebar no browser**

```bash
.venv/bin/python manage.py runserver
```

Acesse `http://127.0.0.1:8000/admin/` e verifique:
- Sidebar mostra exatamente: Pedidos, Devoluções, Produtos, Clientes (Loja) + Entrada de Estoque, Contas a Receber, Contas a Pagar, Lançamentos de Caixa, Categorias Financeiras, Fornecedores (Operações) + Sistema colapsível
- Total de 10 itens visíveis
- "Pedidos de Compra" e "Recebimentos" não aparecem mais
- "Categorias" (produtos) não aparece mais

- [ ] **Step 4: Commit**

```bash
git add barrs_erp/settings/base.py
git commit -m "feat(sprint6): sidebar simplificada — 10 itens visíveis, remove compras e categorias"
```

---

## Verificação Final

- [ ] **Rodar check completo**

```bash
.venv/bin/python manage.py check --deploy 2>/dev/null || .venv/bin/python manage.py check
```

Saída esperada: zero erros.

- [ ] **Conferir migrations aplicadas**

```bash
.venv/bin/python manage.py showmigrations produtos financeiro pedidos
```

Todas devem mostrar `[X]`.

- [ ] **Atualizar `docs/sprints.md` — marcar tarefas da Sprint 6 como concluídas**

Abra `docs/sprints.md` e substitua todos os `- [ ]` da Sprint 6 por `- [x]`.

- [ ] **Commit final**

```bash
git add docs/sprints.md
git commit -m "docs: Sprint 6 concluída — limpeza e simplificação do sistema"
```
