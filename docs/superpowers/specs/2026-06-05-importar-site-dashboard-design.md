# Design: importar_site + Dashboard

**Data:** 2026-06-05  
**Status:** Aprovado

---

## Escopo

Duas entregas independentes:
1. Management command `importar_site` — importa dados do banco secundário (site Django) para o ERP
2. Dashboard em `/dashboard/` — KPIs, estoque baixo e gráfico de vendas 30 dias

---

## 1. Management Command `importar_site`

### Configuração de banco

`settings/base.py` passa a ter dois bancos:
- `default` — banco do ERP (já existente, via `DATABASE_URL`)  
- `site` — banco do site, via `SITE_DATABASE_URL`

### Modelos espelho (`core/site_models.py`)

Modelos `unmanaged=True` que mapeiam as tabelas do banco `site`. Sem migrations. Acesso exclusivo via `.using('site')`.

| Modelo espelho | Tabela no site |
|---|---|
| `SiteCategoria` | `loja_categoria` |
| `SiteProduto` | `loja_produto` |
| `SiteUser` | `auth_user` |
| `SitePerfilCliente` | `loja_perfilcliente` |
| `SitePedido` | `loja_pedido` |
| `SiteItemPedido` | `loja_itempedido` |

### Campo `site_id`

Adicionado em `Produto`, `Cliente` e `Pedido` do ERP:
- Tipo: `IntegerField(null=True, blank=True, db_index=True)`
- Uso: chave de deduplicação em reimportações (`get_or_create(site_id=x)`)
- Migration gerada para os três models

### Fluxo de importação (ordem por dependência)

1. **Categorias** — `get_or_create(slug=site_cat.slug)`, atualiza `nome`
2. **Produtos** — `get_or_create(site_id=site_prod.id)`, mapeia campos:
   - `codigo_interno → sku` (fallback: `f"SITE-{id}"`)
   - `preco → preco_venda`; `custo = Decimal('0')`
   - `estoque → estoque_total`
   - `visivel=True → status='ativo'`; `False → 'inativo'`
   - `categoria` resolvida pelo slug já importado
3. **Clientes** — `get_or_create(site_id=user.id)`, constrói de `auth_user` + `loja_perfilcliente` (LEFT JOIN implícito)
4. **Pedidos** — `get_or_create(site_id=site_ped.id)`, mapeia:
   - `status`: `pendente→aguardando_pagamento`, `confirmado→pago`, `enviado→enviado`, `entregue→entregue`, `cancelado→cancelado`
   - `canal = 'site'`
   - Cria `ItemPedido` para cada `loja_itempedido`
   - Cria `Pagamento(metodo='pix', status='aprovado')` se `status_erp == 'pago'`
   - **Não** dispara signal `calcular_lucro_pedido` durante import (`signal.disconnect` temporário)

### Saída do command

```
Importando categorias...  OK (12 criadas, 0 atualizadas)
Importando produtos...    OK (84 criados, 3 atualizados, 1 erro)
Importando clientes...    OK (231 criados, 0 atualizados)
Importando pedidos...     OK (412 criados, 5 atualizados)

Relatório final:
  Categorias : 12 criadas | 0 atualizadas | 0 erros
  Produtos   : 84 criadas | 3 atualizadas | 1 erro
  Clientes   : 231 criadas | 0 atualizadas | 0 erros
  Pedidos    : 412 criadas | 5 atualizadas | 0 erros
```

Erros são capturados por `try/except`, logados com `self.style.ERROR`, e não interrompem o import.

---

## 2. Dashboard

### Arquivos

| Arquivo | Descrição |
|---|---|
| `core/views.py` | `DashboardView` com contexto dos KPIs |
| `templates/admin/dashboard.html` | Template que herda `admin/base_site.html` |
| `barrs_erp/urls.py` | Rota `/dashboard/` |
| `barrs_erp/settings/base.py` | Link "Dashboard" em `JAZZMIN_SETTINGS['topmenu_links']` |

### KPI Cards

| Card | Query |
|---|---|
| Faturamento hoje | `Pedido(status='pago', criado_em__date=hoje).Sum('total_liquido')` |
| Faturamento mês | Mesmo filtro `criado_em__year/month` |
| Lucro mês | `LucroPedido(pedido__criado_em__year/month).Sum('lucro_liquido')` |
| Pedidos pendentes | `Pedido(status__in=[orcamento,reservado,aguardando_pagamento]).count()` |

### Tabela estoque baixo

`Produto.objects.filter(status='ativo', estoque_total__lte=5).order_by('estoque_total')[:10]`

### Gráfico vendas 30 dias

Query: `TruncDate('criado_em')` + `Sum('total_liquido')` nos pedidos `status='pago'` dos últimos 30 dias.  
Passado ao template como `json.dumps(lista)`. Chart.js (CDN) renderiza linha com fill.

### Proteção de acesso

`@login_required(login_url='/admin/login/')` — usa o login do admin.

---

## Arquivos a criar/modificar

**Criar:**
- `core/site_models.py`
- `core/management/commands/importar_site.py`
- `core/views.py`
- `templates/admin/dashboard.html`

**Modificar:**
- `barrs_erp/settings/base.py` — banco `site` + link dashboard no Jazzmin
- `barrs_erp/urls.py` — rota `/dashboard/`
- `produtos/models.py` — campo `site_id`
- `clientes/models.py` — campo `site_id`
- `pedidos/models.py` — campo `site_id`
- `produtos/migrations/` — migration do site_id
- `clientes/migrations/` — migration do site_id
- `pedidos/migrations/` — migration do site_id
