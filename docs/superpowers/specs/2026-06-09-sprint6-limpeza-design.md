# Sprint 6 — Limpeza do Sistema: Design Spec

**Data:** 2026-06-09  
**Objetivo:** remover complexidade que não gera valor para uma loja pequena (1–3 operadores).  
**Abordagem:** commits por camada — models/migrations → admin cleanup → sidebar.

---

## Escopo

10 tarefas de remoção/simplificação. Nenhuma feature nova. Zero risco de perda de dados (só inativação de admin e remoção de campos não utilizados).

---

## Camada 1 — Model Changes + Migrations

### 1a. `Pedido`: remover status `reservado` e `separacao`

- Remover `STATUS_RESERVADO`, `STATUS_SEPARACAO` e suas entradas em `STATUS_CHOICES`
- Remover entradas em `_STATUS_PEDIDO_COR` no admin
- Migration: `AlterField` em `status` (sem dropar dados — registros existentes ficam com valor orphan, mas CharField não impede isso)
- **Arquivo:** `pedidos/models.py`, `pedidos/admin.py`

### 1b. `Produto`: remover `estoque_reservado`

- Remover campo `estoque_reservado = models.IntegerField`
- Remover propriedade `estoque_disponivel` (depende de `estoque_reservado`)
- Remover `estoque_reservado` de `list_display` e `fieldsets` no admin
- Migration: `RemoveField`
- **Arquivo:** `produtos/models.py`, `produtos/admin.py`

### 1c. `Categoria`: remover `slug`

- Remover `slug = models.SlugField` e método `save()` que gera o slug
- Remover `prepopulated_fields` e `slug` do admin
- Migration: `RemoveField`
- **Arquivo:** `produtos/models.py`, `produtos/admin.py`

### 1d. `CategoriaFinanceira`: remover campo `pai`

- Remover `pai = models.ForeignKey('self', ...)` e ajustar `__str__` para não referenciar `self.pai`
- Migration: `RemoveField`
- **Arquivo:** `financeiro/models.py`

### 1e. `Produto`: adicionar `imagem_url`

- Adicionar `imagem_url = models.URLField('URL da Imagem', blank=True, default='')`
- Migration: `AddField`
- **Arquivo:** `produtos/models.py`

### 1f. `Pedido`: adicionar propriedade `lucro_calculado`

- Adicionar `@property lucro_calculado` → `total_liquido - sum(item.custo_unitario * item.quantidade for item in itens)`
- Não requer migration (propriedade Python pura)
- **Arquivo:** `pedidos/models.py`

---

## Camada 2 — Admin Cleanup

### 2a. Remover `LucroPedido` do admin

- Remover `@admin.register(LucroPedido)` e classe `LucroPedidoAdmin`
- Remover `LucroPedido` dos imports no admin
- Remover o signal `calcular_lucro_pedido` em `pedidos/signals.py`
- Atualizar `core/views.py` e `financeiro/views.py` para usar `Pedido.lucro_calculado` em vez de `LucroPedido`
- **Arquivo:** `pedidos/admin.py`, `pedidos/signals.py`, `core/views.py`, `financeiro/views.py`

### 2b. Remover `EventoRastreio` do admin

- Remover `EventoRastreioInline` do `PedidoAdmin`
- Remover `@admin.register(EventoRastreio)` se existir (não existe — só inline)
- Manter model e tabela intactos no banco
- **Arquivo:** `pedidos/admin.py`

### 2c. Remover `ParcelaPagamento` do admin

- Remover `ParcelaPagamentoInline` do `PagamentoAdmin`
- Remover o signal `criar_parcelas_pagamento` em `pedidos/signals.py`
- Manter model e tabela intactos no banco
- **Arquivo:** `pedidos/admin.py`, `pedidos/signals.py`

### 2d. Remover `FotoProduto` do admin

- Remover `FotoProdutoInline` do `ProdutoAdmin`
- Adicionar `imagem_url` nos fieldsets de `ProdutoAdmin`
- Remover `FotoProduto` do `list_display` de `ProdutoAdmin`
- **Arquivo:** `produtos/admin.py`

### 2e. Atualizar serializers e views da API

- Remover `LucroPedidoViewSet` e `EventoRastreioViewSet` de `pedidos/views.py`
- Remover rotas correspondentes de `pedidos/urls.py`
- Atualizar `PedidoSerializer` para expor `lucro_calculado` como campo read-only
- **Arquivo:** `pedidos/views.py`, `pedidos/urls.py`, `pedidos/serializers.py`

---

## Camada 3 — Sidebar Simplificada

### 3a. Remover da sidebar

Itens removidos:
- Categorias (produtos — raramente acessada, disponível via Produto admin)
- Pedidos de Compra
- Recebimentos de Mercadoria

### 3b. Adicionar/renomear na sidebar

- "Entrada de Estoque" → link para `admin:estoque_movimentoestoque_changelist`
  (substituindo os 2 itens de compras)

### 3c. Resultado final da sidebar (10 itens visíveis)

| Grupo | Item |
|-------|------|
| Loja | Pedidos |
| Loja | Devoluções |
| Loja | Produtos |
| Loja | Clientes |
| Operações | Entrada de Estoque |
| Operações | Contas a Receber |
| Operações | Contas a Pagar |
| Operações | Lançamentos de Caixa |
| Operações | Categorias Financeiras |
| Operações | Fornecedores |
| Sistema (colapsível) | Usuários, Grupos, Logs |

---

## Critérios de Aceite

- Admin mais limpo: sidebar com exatamente 10 itens visíveis (+ Sistema colapsível)
- Criar pedido completo em menos de 5 cliques
- Zero campos obrigatórios desnecessários nos formulários principais
- Django `check` sem erros após as mudanças

## Decisões

- App `compras` permanece com models e dados intactos — apenas removido da sidebar
- `LucroPedido` e `EventoRastreio` mantêm tabelas no banco (sem migration DROP) — apenas removidos do admin/fluxo
- `ParcelaPagamento` mantém tabela no banco — apenas removido do fluxo de criação
- Campos `pai`, `slug`, `estoque_reservado` são dropados via migration (nunca foram populados em produção)
