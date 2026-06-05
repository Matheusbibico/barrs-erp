# Design: Webhook de Sincronização + Dashboard Melhorado

**Data:** 2026-06-05  
**Projetos:** barrs-erp (ERP) + barrsstore (Site)  
**Escopo:** Duas melhorias independentes entregues juntas.

---

## 1. Webhook de Sincronização Automática

### Problema
O comando `importar_site` é manual e batch. Quando uma venda é confirmada no site, o ERP só fica sabendo na próxima execução manual. A meta é sincronização em tempo real: assim que o pedido muda para `'confirmado'` no site, o ERP importa e processa automaticamente.

### Arquitetura

```
Site (barrsstore)               ERP (barrs-erp)
─────────────────               ───────────────
Pedido.status → 'confirmado'
  └─ post_save signal
       └─ requests.post ──────► POST /webhook/nova-venda/
                                  ├─ valida X-Webhook-Token
                                  ├─ busca SitePedido no banco 'site'
                                  ├─ _importar_pedido_unico()
                                  │    ├─ get_or_create Cliente
                                  │    ├─ get_or_create Pedido (signals ON)
                                  │    ├─ cria ItemPedidos
                                  │    ├─ cria Pagamento (se status=pago)
                                  │    └─ decrementa estoque_total por item
                                  └─ retorna JSON {status, criado, pedido_id}
```

### ERP — `core/views.py`

Adicionar função `webhook_nova_venda(request)`:

- Decoradores: `@csrf_exempt`, `require_POST`
- **Autenticação:** lê `request.META.get('HTTP_X_WEBHOOK_TOKEN')`, compara com `settings.WEBHOOK_TOKEN` usando `hmac.compare_digest` (resistente a timing attack). Retorna 401 se inválido ou se `WEBHOOK_TOKEN` não estiver configurado.
- **Input:** `json.loads(request.body)` → `pedido_id` (inteiro). Retorna 400 se ausente ou malformado.
- **Pré-condição:** verifica se banco `'site'` está em `settings.DATABASES`. Retorna 503 se não.
- **Import:** chama `_importar_pedido_unico(pedido_id)` (função privada no mesmo arquivo). Retorna 404 se o pedido não existir no banco do site.
- **Idempotência:** `get_or_create` em Pedido/Cliente — re-chamadas são inofensivas.
- **Resposta:** `{"status": "ok", "criado": true/false, "pedido_id": "<uuid>"}` com HTTP 200.
- **Erros:** JSON `{"status": "error", "detail": "..."}` com status HTTP adequado.

#### Função `_importar_pedido_unico(site_id)`

Signals **não** são desconectados (diferença intencional do `importar_site` batch).  
Isso garante que `calcular_lucro_pedido` e `atualizar_historico_cliente` disparam automaticamente ao salvar um Pedido com `status='pago'`.

Passos:
1. `SitePedido.objects.using('site').prefetch_related('itens__produto').get(pk=site_id)`
2. Mapeia status via `STATUS_MAP` (mesmo dict do `importar_site`)
3. `get_or_create` Cliente por `site_id` (com fallback por `email`)
4. `get_or_create` Pedido por `site_id` — se já existe, atualiza status e total e retorna `criado=False`
5. Se criado: cria `ItemPedido` para cada item; usa `Produto.objects.get(site_id=sp_item.produto_id)` ou placeholder `SITE-DESCONHECIDO`
6. Para cada item criado: `Produto.objects.filter(pk=prod.pk).update(estoque_total=F('estoque_total') - quantidade)` — sem disparar signals de produto
7. Se `status == STATUS_PAGO`: `get_or_create Pagamento` (mesmo padrão do `importar_site`)
8. Retorna `(pedido_erpobj, criado: bool)`

### ERP — `barrs_erp/urls.py`

```python
path('webhook/nova-venda/', webhook_nova_venda, name='webhook_nova_venda'),
```

### ERP — Settings

`barrs_erp/settings/base.py`:
```python
WEBHOOK_TOKEN = config('WEBHOOK_TOKEN', default='')
```

`.env` (local) e variável de ambiente Railway:
```
WEBHOOK_TOKEN=<token gerado com secrets.token_hex(32)>
```

### Site — `loja/signals.py` (arquivo novo)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pedido

@receiver(post_save, sender=Pedido)
def notificar_erp_nova_venda(sender, instance, created, update_fields, **kwargs):
    if created:
        return
    if update_fields is not None and 'status' not in update_fields:
        return
    if instance.status != 'confirmado':
        return
    # dispara aqui
    _chamar_webhook_erp(instance.id)
```

`_chamar_webhook_erp(pedido_id)` — função privada no mesmo arquivo:
- Lê `settings.ERP_WEBHOOK_URL` e `settings.ERP_WEBHOOK_TOKEN`; se vazios, retorna imediatamente (feature desativada)
- `requests.post(url, json={"pedido_id": pedido_id}, headers={"X-Webhook-Token": token}, timeout=5)`
- Envolto em `try/except Exception`: captura qualquer falha (network, timeout, 4xx/5xx) e faz `logger.warning(...)` — nunca propaga exceção

### Site — `loja/apps.py`

```python
class LojaConfig(AppConfig):
    name = 'loja'

    def ready(self):
        import loja.signals  # noqa: F401
```

### Site — Settings

```python
ERP_WEBHOOK_URL = os.environ.get('ERP_WEBHOOK_URL', '')
ERP_WEBHOOK_TOKEN = os.environ.get('ERP_WEBHOOK_TOKEN', '')
```

`.env` do site:
```
ERP_WEBHOOK_URL=https://barrs-erp-production.up.railway.app/webhook/nova-venda/
ERP_WEBHOOK_TOKEN=<mesmo token do ERP>
```

### Variáveis de ambiente — resumo

| Projeto | Variável | Valor |
|---------|----------|-------|
| ERP | `WEBHOOK_TOKEN` | `secrets.token_hex(32)` gerado uma vez |
| Site | `ERP_WEBHOOK_URL` | `https://barrs-erp-production.up.railway.app/webhook/nova-venda/` |
| Site | `ERP_WEBHOOK_TOKEN` | mesmo valor de `WEBHOOK_TOKEN` do ERP |

---

## 2. Dashboard Melhorado

### Novos dados — `core/views.py`

Adicionar às queries existentes da view `dashboard`:

| Variável | Query |
|----------|-------|
| `ticket_medio_mes` | `Pedido.filter(status='pago', criado_em__gte=inicio_mes).aggregate(Avg('total_liquido'))` |
| `clientes_ativos` | `Cliente.objects.filter(ativo=True).count()` |
| `top5_produtos` | `ItemPedido.filter(pedido__status='pago', pedido__criado_em__gte=trinta_dias_atras).values('produto__nome').annotate(qty=Sum('quantidade'), receita=Sum(F('preco_unitario')*F('quantidade'))).order_by('-receita')[:5]` |
| `lucro_30d_dados` | `LucroPedido.filter(pedido__criado_em__date__gte=trinta_dias_atras).annotate(dia=TruncDate('pedido__criado_em')).values('dia').annotate(total=Sum('lucro_liquido')).order_by('dia')` — serializado igual ao `vendas_dict` existente |
| `vendas_canal` | `Pedido.filter(status='pago', criado_em__date__gte=inicio_mes).values('canal').annotate(total=Sum('total_liquido')).order_by('-total')` — serializado como JSON para Chart.js |
| `estoque_total_ativos` | `Produto.objects.filter(status='ativo').count()` |
| `estoque_baixo_count` | `Produto.objects.filter(status='ativo', estoque_total__gt=0, estoque_total__lte=5).count()` |
| `estoque_zerado_count` | `Produto.objects.filter(status='ativo', estoque_total__lte=0).count()` |

### Template — `templates/admin/dashboard.html`

**KPI grid (6 cards):**
- Faturamento Hoje *(existente)*
- Faturamento do Mês *(existente)*
- Lucro do Mês *(existente)*
- Pedidos Pendentes *(existente)*
- Ticket Médio do Mês *(novo)*
- Clientes Ativos *(novo)*

**Gráfico de linhas — dual (seção existente renomeada "Vendas e Lucro — Últimos 30 Dias"):**
- Dataset 1: Faturamento (azul `#4e73df`, fill)
- Dataset 2: Lucro Líquido (verde `#1cc88a`, fill false)
- Mesmo canvas, legenda habilitada

**Gráfico de rosca — Vendas por Canal (seção nova):**
- Chart.js `type: 'doughnut'`
- Labels: nomes dos canais traduzidos (Site, WhatsApp, Instagram, Presencial, Link)
- Dados: totais do mês por canal
- Posicionado em grid de 2 colunas ao lado do gráfico de linhas em telas largas

**Top 5 Produtos — 30 dias (seção nova):**
- Tabela: Produto | Qtd vendida | Receita
- Ordenada por receita decrescente

**Resumo de Estoque (seção nova):**
- 3 cards inline: Total de produtos ativos | Estoque baixo (1–5 un) | Zerados
- Zerados com cor de alerta se > 0

### Sem novas dependências

Tudo usa Chart.js 4.4 (já carregado via CDN) e queries Django ORM. Nenhum pacote novo.

---

## Arquivos alterados

### barrs-erp
| Arquivo | Operação |
|---------|----------|
| `core/views.py` | editar — adicionar `webhook_nova_venda` + `_importar_pedido_unico` + novos dados do dashboard |
| `barrs_erp/urls.py` | editar — adicionar rota `/webhook/nova-venda/` |
| `barrs_erp/settings/base.py` | editar — adicionar `WEBHOOK_TOKEN` |
| `templates/admin/dashboard.html` | editar — KPIs, dual-line chart, rosca, top5, resumo estoque |

### barrsstore
| Arquivo | Operação |
|---------|----------|
| `loja/signals.py` | criar — signal `notificar_erp_nova_venda` |
| `loja/apps.py` | editar — `ready()` importa signals |
| `barrs_store/settings.py` | editar — adicionar `ERP_WEBHOOK_URL` e `ERP_WEBHOOK_TOKEN` |

---

## Fora do escopo

- Retry automático no site em caso de falha do webhook (pode ser adicionado depois com Celery/django-tasks)
- Autenticação mútua (HMAC de payload) — token simples é suficiente para este volume
- Histórico de chamadas ao webhook
