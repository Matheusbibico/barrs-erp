# Webhook de Sincronização + Dashboard Melhorado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar endpoint de webhook no ERP para sincronização automática de pedidos confirmados no site, e enriquecer o dashboard com novos KPIs, gráficos e tabelas.

**Architecture:** O site dispara um `post_save` signal quando `Pedido.status` muda para `'confirmado'`, fazendo POST para `/webhook/nova-venda/` no ERP. O ERP valida o token, importa o pedido único do banco do site com signals habilitados (diferente do import batch) e decrementa estoque. O dashboard recebe novas queries sem dependências externas.

**Tech Stack:** Django 5.2, Django ORM (F, Sum, Avg, TruncDate), Chart.js 4.4 (já no CDN), `requests` (já presente no barrsstore), `hmac.compare_digest` para timing-safe token comparison.

---

## Mapa de arquivos

### barrs-erp
| Arquivo | Operação |
|---------|----------|
| `barrs_erp/settings/base.py` | Editar — adicionar `WEBHOOK_TOKEN` |
| `core/tests/__init__.py` | Criar — vazio |
| `core/tests/test_webhook.py` | Criar — testes do endpoint |
| `core/tests/test_dashboard.py` | Criar — testes da view dashboard |
| `core/views.py` | Editar — webhook + `_importar_pedido_unico` + novos dados do dashboard |
| `barrs_erp/urls.py` | Editar — rota `/webhook/nova-venda/` |
| `templates/admin/dashboard.html` | Editar — 6 KPIs, dual-line, rosca, top5, estoque |

### barrsstore
| Arquivo | Operação |
|---------|----------|
| `barrs_store/settings.py` | Editar — `ERP_WEBHOOK_URL` + `ERP_WEBHOOK_TOKEN` |
| `loja/signals.py` | Criar — signal `notificar_erp_nova_venda` |
| `loja/apps.py` | Editar — `ready()` importa signals |
| `loja/tests.py` | Editar — adicionar testes do signal |

---

## Task 1: ERP — Configurar WEBHOOK_TOKEN

**Files:**
- Modify: `barrs_erp/settings/base.py`

- [ ] **Gerar token**

```bash
cd ~/Documents/projetos/barrs-erp
.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o output — será usado no próximo passo.

- [ ] **Adicionar ao settings**

Em `barrs_erp/settings/base.py`, após a linha `CORS_ALLOW_ALL_ORIGINS = ...`:

```python
WEBHOOK_TOKEN = config('WEBHOOK_TOKEN', default='')
```

- [ ] **Adicionar ao .env local**

Abra (ou crie) `barrs_erp/.env` e adicione:

```
WEBHOOK_TOKEN=<output do secrets.token_hex acima>
```

- [ ] **Verificar que o Django carrega sem erros**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py check
```

Esperado: `System check identified no issues (0 silenced).`

- [ ] **Commit**

```bash
git add barrs_erp/settings/base.py
git commit -m "feat: adicionar WEBHOOK_TOKEN ao settings"
```

---

## Task 2: ERP — Endpoint webhook (autenticação e roteamento)

**Files:**
- Create: `core/tests/__init__.py`
- Create: `core/tests/test_webhook.py`
- Modify: `core/views.py`
- Modify: `barrs_erp/urls.py`

- [ ] **Criar diretório de testes**

```bash
mkdir -p core/tests
touch core/tests/__init__.py
```

- [ ] **Escrever testes de autenticação e roteamento**

Criar `core/tests/test_webhook.py`:

```python
import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

GOOD_TOKEN = 'testtokenabcdef1234567890'


@override_settings(WEBHOOK_TOKEN=GOOD_TOKEN)
class WebhookAuthTests(TestCase):
    URL = '/webhook/nova-venda/'

    def post(self, body, token=GOOD_TOKEN, **extra):
        headers = {}
        if token is not None:
            headers['HTTP_X_WEBHOOK_TOKEN'] = token
        return self.client.post(
            self.URL,
            data=json.dumps(body),
            content_type='application/json',
            **headers,
            **extra,
        )

    def test_get_retorna_405(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 405)

    def test_sem_token_retorna_401(self):
        r = self.post({'pedido_id': 1}, token=None)
        self.assertEqual(r.status_code, 401)

    def test_token_errado_retorna_401(self):
        r = self.post({'pedido_id': 1}, token='tokenerrado')
        self.assertEqual(r.status_code, 401)

    def test_sem_pedido_id_retorna_400(self):
        r = self.post({})
        self.assertEqual(r.status_code, 400)

    def test_pedido_id_invalido_retorna_400(self):
        r = self.post({'pedido_id': 'abc'})
        self.assertEqual(r.status_code, 400)

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
    def test_sem_banco_site_retorna_503(self):
        r = self.post({'pedido_id': 1})
        self.assertEqual(r.status_code, 503)

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'site': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
    )
    @patch('core.views._importar_pedido_unico')
    def test_requisicao_valida_retorna_200(self, mock_import):
        import uuid
        mock_pedido = MagicMock()
        mock_pedido.id = uuid.uuid4()
        mock_import.return_value = (mock_pedido, True)

        r = self.post({'pedido_id': 1})

        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(data['criado'])

    @override_settings(
        WEBHOOK_TOKEN=GOOD_TOKEN,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'site': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
    )
    @patch('core.views._importar_pedido_unico')
    def test_pedido_nao_encontrado_retorna_404(self, mock_import):
        from core.site_models import SitePedido
        mock_import.side_effect = SitePedido.DoesNotExist

        r = self.post({'pedido_id': 999})

        self.assertEqual(r.status_code, 404)
```

- [ ] **Executar testes — esperar FAIL**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests.test_webhook -v 2
```

Esperado: erros de importação ou `AssertionError` porque o endpoint não existe.

- [ ] **Implementar o endpoint em `core/views.py`**

No topo do arquivo, adicionar os imports que faltam (manter os existentes):

```python
import hmac
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from clientes.models import Cliente
from core.site_models import SitePedido
from pedidos.models import ItemPedido, Pagamento, Pedido
from produtos.models import Produto

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    'pendente': Pedido.STATUS_AGUARDANDO,
    'confirmado': Pedido.STATUS_PAGO,
    'enviado': Pedido.STATUS_ENVIADO,
    'entregue': Pedido.STATUS_ENTREGUE,
    'cancelado': Pedido.STATUS_CANCELADO,
}
```

Adicionar a view após o `dashboard`:

```python
@csrf_exempt
@require_POST
def webhook_nova_venda(request):
    token = request.META.get('HTTP_X_WEBHOOK_TOKEN', '')
    expected = getattr(settings, 'WEBHOOK_TOKEN', '')
    if not expected or not hmac.compare_digest(token, expected):
        return JsonResponse({'status': 'error', 'detail': 'Unauthorized'}, status=401)

    if 'site' not in settings.DATABASES:
        return JsonResponse({'status': 'error', 'detail': 'Site database not configured'}, status=503)

    try:
        body = json.loads(request.body)
        pedido_id = int(body['pedido_id'])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'status': 'error', 'detail': 'pedido_id required'}, status=400)

    try:
        pedido, criado = _importar_pedido_unico(pedido_id)
    except SitePedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'detail': 'Pedido not found in site db'}, status=404)
    except Exception as exc:
        logger.exception('Webhook import error for site pedido %s', pedido_id)
        return JsonResponse({'status': 'error', 'detail': str(exc)}, status=500)

    return JsonResponse({'status': 'ok', 'criado': criado, 'pedido_id': str(pedido.id)})


def _importar_pedido_unico(site_id):
    raise NotImplementedError
```

- [ ] **Adicionar rota em `barrs_erp/urls.py`**

```python
from core.views import dashboard, webhook_nova_venda

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard, name='dashboard'),
    path('webhook/nova-venda/', webhook_nova_venda, name='webhook_nova_venda'),
    path('api/', include([
        ...
    ])),
]
```

- [ ] **Executar testes — esperar PASS (exceto test_requisicao_valida e test_pedido_nao_encontrado que dependem da Task 3)**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests.test_webhook -v 2
```

Os 5 primeiros testes (405, 401×2, 400×2, 503) devem passar. Os dois últimos falham com `NotImplementedError` — OK por agora.

- [ ] **Commit**

```bash
git add core/tests/__init__.py core/tests/test_webhook.py core/views.py barrs_erp/urls.py
git commit -m "feat: endpoint POST /webhook/nova-venda/ com autenticação por token"
```

---

## Task 3: ERP — `_importar_pedido_unico`

**Files:**
- Modify: `core/views.py`
- Modify: `core/tests/test_webhook.py` (adicionar testes de importação)

- [ ] **Adicionar testes de importação ao `core/tests/test_webhook.py`**

No final do arquivo, adicionar:

```python
from decimal import Decimal

from clientes.models import Cliente
from pedidos.models import Pedido
from produtos.models import Produto


class ImportarPedidoUnicoTests(TestCase):
    def setUp(self):
        self.placeholder = Produto.objects.create(
            sku='SITE-DESCONHECIDO',
            nome='Produto não identificado (importado)',
            preco_venda=Decimal('0'),
            custo=Decimal('0'),
            status='inativo',
        )
        self.produto = Produto.objects.create(
            sku='P001',
            nome='Brinco Dourado',
            preco_venda=Decimal('50'),
            custo=Decimal('10'),
            estoque_total=10,
            site_id=7,
        )

    def _make_site_item(self, produto_site_id, quantidade, preco):
        item = MagicMock()
        item.produto_id = produto_site_id
        item.quantidade = quantidade
        item.preco_unitario = Decimal(str(preco))
        return item

    def _make_site_pedido(self, site_id=1, status='confirmado', itens=None):
        from django.utils import timezone
        sp = MagicMock()
        sp.id = site_id
        sp.nome = 'Ana Silva'
        sp.email = 'ana@test.com'
        sp.telefone = '11999999999'
        sp.cidade = 'São Paulo'
        sp.estado = 'SP'
        sp.status = status
        sp.subtotal = Decimal('100.00')
        sp.desconto = Decimal('0.00')
        sp.frete = Decimal('10.00')
        sp.total = Decimal('110.00')
        sp.criado_em = timezone.now()
        sp.itens.all.return_value = itens or []
        return sp

    @patch('core.views.SitePedido')
    def test_cria_pedido_e_cliente(self, MockSP):
        sp = self._make_site_pedido(site_id=100)
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        pedido, criado = _importar_pedido_unico(100)

        self.assertTrue(criado)
        self.assertTrue(Cliente.objects.filter(email='ana@test.com').exists())
        self.assertTrue(Pedido.objects.filter(site_id=100).exists())
        self.assertEqual(pedido.status, Pedido.STATUS_PAGO)

    @patch('core.views.SitePedido')
    def test_idempotente_segunda_chamada(self, MockSP):
        sp = self._make_site_pedido(site_id=101)
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        _, criado1 = _importar_pedido_unico(101)
        _, criado2 = _importar_pedido_unico(101)

        self.assertTrue(criado1)
        self.assertFalse(criado2)
        self.assertEqual(Pedido.objects.filter(site_id=101).count(), 1)

    @patch('core.views.SitePedido')
    def test_decrementa_estoque_do_produto(self, MockSP):
        item = self._make_site_item(produto_site_id=7, quantidade=3, preco='50.00')
        sp = self._make_site_pedido(site_id=102, itens=[item])
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        _importar_pedido_unico(102)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque_total, 7)  # 10 - 3

    @patch('core.views.SitePedido')
    def test_item_sem_produto_usa_placeholder(self, MockSP):
        item = self._make_site_item(produto_site_id=999, quantidade=1, preco='30.00')
        sp = self._make_site_pedido(site_id=103, itens=[item])
        MockSP.objects.using.return_value.prefetch_related.return_value.get.return_value = sp

        from core.views import _importar_pedido_unico
        pedido, _ = _importar_pedido_unico(103)

        item_ped = pedido.itens.first()
        self.assertEqual(item_ped.produto.sku, 'SITE-DESCONHECIDO')
```

- [ ] **Rodar testes — esperar FAIL**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests.test_webhook.ImportarPedidoUnicoTests -v 2
```

Esperado: `NotImplementedError`.

- [ ] **Implementar `_importar_pedido_unico` em `core/views.py`**

Substituir o stub `raise NotImplementedError` pela implementação completa:

```python
def _importar_pedido_unico(site_id):
    from django.db.models import F as _F

    sp = SitePedido.objects.using('site').prefetch_related('itens__produto').get(pk=site_id)

    status_erp = _STATUS_MAP.get(sp.status, Pedido.STATUS_ORCAMENTO)

    if sp.email:
        cliente, _ = Cliente.objects.get_or_create(
            email=sp.email,
            defaults={
                'nome': sp.nome or sp.email,
                'whatsapp': getattr(sp, 'telefone', ''),
                'cidade': getattr(sp, 'cidade', ''),
                'estado': getattr(sp, 'estado', ''),
            },
        )
    else:
        cliente, _ = Cliente.objects.get_or_create(
            site_id=site_id,
            defaults={'nome': sp.nome or f'site_{site_id}'},
        )

    ped, criado = Pedido.objects.get_or_create(
        site_id=sp.id,
        defaults={
            'cliente': cliente,
            'canal': Pedido.CANAL_SITE,
            'status': status_erp,
            'total_bruto': sp.subtotal,
            'desconto': sp.desconto,
            'frete': sp.frete,
            'total_liquido': sp.total,
        },
    )

    if not criado:
        ped.status = status_erp
        ped.total_liquido = sp.total
        ped.save(update_fields=['status', 'total_liquido'])
        return ped, False

    placeholder, _ = Produto.objects.get_or_create(
        sku='SITE-DESCONHECIDO',
        defaults={
            'nome': 'Produto não identificado (importado)',
            'preco_venda': Decimal('0'),
            'custo': Decimal('0'),
            'status': Produto.STATUS_INATIVO,
        },
    )
    prod_map = {p.site_id: p for p in Produto.objects.filter(site_id__isnull=False)}

    for si in sp.itens.all():
        produto = prod_map.get(si.produto_id) if si.produto_id else None
        produto = produto or placeholder
        ItemPedido.objects.create(
            pedido=ped,
            produto=produto,
            quantidade=si.quantidade,
            preco_unitario=si.preco_unitario,
            custo_unitario=Decimal('0'),
        )
        if produto.sku != 'SITE-DESCONHECIDO':
            Produto.objects.filter(pk=produto.pk).update(
                estoque_total=_F('estoque_total') - si.quantidade
            )

    if status_erp == Pedido.STATUS_PAGO:
        Pagamento.objects.get_or_create(
            pedido=ped,
            defaults={
                'metodo': Pagamento.METODO_PIX,
                'valor': sp.total,
                'status': Pagamento.STATUS_APROVADO,
            },
        )

    return ped, True
```

- [ ] **Rodar todos os testes do webhook — esperar PASS**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests.test_webhook -v 2
```

Esperado: todos os testes passando.

- [ ] **Commit**

```bash
git add core/views.py core/tests/test_webhook.py
git commit -m "feat: _importar_pedido_unico com signals habilitados e decremento de estoque"
```

---

## Task 4: ERP — Dashboard: novas queries

**Files:**
- Create: `core/tests/test_dashboard.py`
- Modify: `core/views.py`

- [ ] **Escrever testes da view dashboard**

Criar `core/tests/test_dashboard.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase


class DashboardViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            'staff', 'staff@test.com', 'pass', is_staff=True
        )

    def test_redireciona_usuario_anonimo(self):
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin/login/', r['Location'])

    def test_renderiza_para_staff(self):
        self.client.force_login(self.staff)
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 200)

    def test_context_contem_chaves_obrigatorias(self):
        self.client.force_login(self.staff)
        r = self.client.get('/dashboard/')
        chaves = [
            'faturamento_hoje', 'faturamento_mes', 'lucro_mes', 'pedidos_pendentes',
            'ticket_medio_mes', 'clientes_ativos', 'top5_produtos',
            'grafico_labels', 'grafico_dados', 'grafico_lucro',
            'vendas_canal_labels', 'vendas_canal_dados',
            'estoque_total_ativos', 'estoque_baixo_count', 'estoque_zerado_count',
        ]
        for chave in chaves:
            self.assertIn(chave, r.context, f'Context faltando: {chave}')
```

- [ ] **Rodar testes — esperar FAIL**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests.test_dashboard -v 2
```

Esperado: `KeyError` ou `AssertionError` nas novas chaves.

- [ ] **Atualizar a view `dashboard` em `core/views.py`**

Substituir a função `dashboard` existente integralmente:

```python
@staff_member_required
def dashboard(request):
    from django.db.models import Avg, F, Sum
    from clientes.models import Cliente

    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    trinta_dias_atras = hoje - timedelta(days=30)

    faturamento_hoje = (
        Pedido.objects.filter(status='pago', criado_em__date=hoje)
        .aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')
    )
    faturamento_mes = (
        Pedido.objects.filter(status='pago', criado_em__date__gte=inicio_mes)
        .aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')
    )
    lucro_mes = (
        LucroPedido.objects.filter(pedido__criado_em__date__gte=inicio_mes)
        .aggregate(v=Sum('lucro_liquido'))['v'] or Decimal('0')
    )
    pedidos_pendentes = Pedido.objects.filter(
        status__in=['orcamento', 'reservado', 'aguardando_pagamento'],
    ).count()

    ticket_medio_mes = (
        Pedido.objects.filter(status='pago', criado_em__date__gte=inicio_mes)
        .aggregate(v=Avg('total_liquido'))['v'] or Decimal('0')
    )
    clientes_ativos = Cliente.objects.filter(ativo=True).count()

    estoque_baixo = (
        Produto.objects
        .filter(status='ativo', estoque_total__lte=5)
        .select_related('categoria')
        .order_by('estoque_total')[:10]
    )
    estoque_total_ativos = Produto.objects.filter(status='ativo').count()
    estoque_baixo_count = Produto.objects.filter(
        status='ativo', estoque_total__gt=0, estoque_total__lte=5
    ).count()
    estoque_zerado_count = Produto.objects.filter(
        status='ativo', estoque_total__lte=0
    ).count()

    top5_produtos = (
        ItemPedido.objects
        .filter(pedido__status='pago', pedido__criado_em__date__gte=trinta_dias_atras)
        .values('produto__nome')
        .annotate(qty=Sum('quantidade'), receita=Sum(F('preco_unitario') * F('quantidade')))
        .order_by('-receita')[:5]
    )

    # Gráfico linhas — 30 dias
    vendas_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('criado_em'))
        .values('dia')
        .annotate(total=Sum('total_liquido'))
        .order_by('dia')
    )
    lucro_qs = (
        LucroPedido.objects
        .filter(pedido__criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('pedido__criado_em'))
        .values('dia')
        .annotate(total=Sum('lucro_liquido'))
        .order_by('dia')
    )
    vendas_dict = {v['dia']: float(v['total']) for v in vendas_qs}
    lucro_dict = {v['dia']: float(v['total']) for v in lucro_qs}

    labels, dados, dados_lucro = [], [], []
    dia = trinta_dias_atras
    while dia <= hoje:
        labels.append(dia.strftime('%d/%m'))
        dados.append(vendas_dict.get(dia, 0))
        dados_lucro.append(lucro_dict.get(dia, 0))
        dia += timedelta(days=1)

    # Gráfico rosca — vendas por canal no mês
    _CANAL_LABELS = {
        'site': 'Site', 'whatsapp': 'WhatsApp', 'instagram': 'Instagram',
        'presencial': 'Presencial', 'link': 'Link',
    }
    canal_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=inicio_mes)
        .values('canal')
        .annotate(total=Sum('total_liquido'))
        .order_by('-total')
    )
    canal_labels = [_CANAL_LABELS.get(v['canal'], v['canal']) for v in canal_qs]
    canal_dados = [float(v['total']) for v in canal_qs]

    return render(request, 'admin/dashboard.html', {
        'title': 'Dashboard',
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'lucro_mes': lucro_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'ticket_medio_mes': ticket_medio_mes,
        'clientes_ativos': clientes_ativos,
        'estoque_baixo': estoque_baixo,
        'estoque_total_ativos': estoque_total_ativos,
        'estoque_baixo_count': estoque_baixo_count,
        'estoque_zerado_count': estoque_zerado_count,
        'top5_produtos': top5_produtos,
        'grafico_labels': json.dumps(labels),
        'grafico_dados': json.dumps(dados),
        'grafico_lucro': json.dumps(dados_lucro),
        'vendas_canal_labels': json.dumps(canal_labels),
        'vendas_canal_dados': json.dumps(canal_dados),
    })
```

Também adicionar `ItemPedido` ao import existente de `pedidos.models` no topo de `views.py`:

```python
from pedidos.models import ItemPedido, LucroPedido, Pedido
```

- [ ] **Rodar testes — esperar PASS**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core.tests -v 2
```

Esperado: todos os testes passando.

- [ ] **Commit**

```bash
git add core/views.py core/tests/test_dashboard.py
git commit -m "feat: dashboard com ticket médio, clientes ativos, top5, canal e estoque"
```

---

## Task 5: ERP — Dashboard template

**Files:**
- Modify: `templates/admin/dashboard.html`

- [ ] **Substituir o template inteiro**

Conteúdo completo de `templates/admin/dashboard.html`:

```html
{% extends "admin/base_site.html" %}
{% load i18n %}

{% block extrahead %}
{{ block.super }}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}
.kpi-card{background:var(--secondary,#fff);border:1px solid var(--border-color,#dee2e6);border-radius:6px;padding:1.25rem;text-align:center}
.kpi-value{font-size:1.8rem;font-weight:700;color:var(--primary,#007bff)}
.kpi-label{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--body-quiet-color,#888);margin-top:.25rem}
.kpi-card.alerta .kpi-value{color:#e74c3c}
.dash-section{background:var(--secondary,#fff);border:1px solid var(--border-color,#dee2e6);border-radius:6px;padding:1.25rem;margin-bottom:1.5rem}
.dash-section h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.07em;color:var(--body-quiet-color,#888);margin:0 0 1rem;padding-bottom:.5rem;border-bottom:1px solid var(--border-color,#dee2e6)}
.dash-two-col{display:grid;grid-template-columns:2fr 1fr;gap:1rem;margin-bottom:1.5rem}
@media(max-width:768px){.dash-two-col{grid-template-columns:1fr}}
#grafico-wrap{position:relative;height:280px}
#grafico-canal-wrap{position:relative;height:280px}
.est-table{width:100%;border-collapse:collapse;font-size:.9rem}
.est-table th,.est-table td{text-align:left;padding:.45rem .75rem;border-bottom:1px solid var(--border-color,#dee2e6)}
.est-table th{font-weight:600}
.badge{padding:2px 8px;border-radius:4px;font-size:.75rem;color:#fff}
.badge-danger{background:#e74c3c}.badge-warning{background:#f39c12}
.mini-kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem}
.mini-kpi{text-align:center;padding:.75rem;border-radius:4px;background:var(--darkened-bg,#f8f9fa)}
.mini-kpi .val{font-size:1.4rem;font-weight:700}
.mini-kpi .lbl{font-size:.75rem;color:var(--body-quiet-color,#888);margin-top:.2rem}
.mini-kpi.alerta .val{color:#e74c3c}
</style>
{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
  <a href="{% url 'admin:index' %}">{% trans 'Início' %}</a> › Dashboard
</div>
{% endblock %}

{% block content %}
<h1>Dashboard</h1>

<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-value">R$ {{ faturamento_hoje|floatformat:2 }}</div>
    <div class="kpi-label">Faturamento Hoje</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">R$ {{ faturamento_mes|floatformat:2 }}</div>
    <div class="kpi-label">Faturamento do Mês</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">R$ {{ lucro_mes|floatformat:2 }}</div>
    <div class="kpi-label">Lucro do Mês</div>
  </div>
  <div class="kpi-card {% if pedidos_pendentes > 0 %}alerta{% endif %}">
    <div class="kpi-value">{{ pedidos_pendentes }}</div>
    <div class="kpi-label">Pedidos Pendentes</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">R$ {{ ticket_medio_mes|floatformat:2 }}</div>
    <div class="kpi-label">Ticket Médio do Mês</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">{{ clientes_ativos }}</div>
    <div class="kpi-label">Clientes Ativos</div>
  </div>
</div>

<div class="dash-two-col">
  <div class="dash-section" style="margin-bottom:0">
    <h2>Vendas e Lucro — Últimos 30 Dias</h2>
    <div id="grafico-wrap"><canvas id="graficoVendas"></canvas></div>
  </div>
  <div class="dash-section" style="margin-bottom:0">
    <h2>Vendas por Canal — Mês Atual</h2>
    <div id="grafico-canal-wrap"><canvas id="graficoCanel"></canvas></div>
  </div>
</div>

<div class="dash-section">
  <h2>Top 5 Produtos — Últimos 30 Dias</h2>
  {% if top5_produtos %}
  <table class="est-table">
    <thead><tr><th>Produto</th><th style="text-align:right">Qtd</th><th style="text-align:right">Receita</th></tr></thead>
    <tbody>
    {% for p in top5_produtos %}
      <tr>
        <td>{{ p.produto__nome|default:"—" }}</td>
        <td style="text-align:right">{{ p.qty }}</td>
        <td style="text-align:right">R$ {{ p.receita|floatformat:2 }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p style="color:var(--body-quiet-color)">Nenhuma venda registrada nos últimos 30 dias.</p>
  {% endif %}
</div>

<div class="dash-section">
  <h2>Estoque Baixo (≤ 5 unidades)</h2>
  <div class="mini-kpi-grid" style="margin-bottom:1rem">
    <div class="mini-kpi">
      <div class="val">{{ estoque_total_ativos }}</div>
      <div class="lbl">Produtos Ativos</div>
    </div>
    <div class="mini-kpi {% if estoque_baixo_count > 0 %}alerta{% endif %}">
      <div class="val">{{ estoque_baixo_count }}</div>
      <div class="lbl">Estoque Baixo (1–5)</div>
    </div>
    <div class="mini-kpi {% if estoque_zerado_count > 0 %}alerta{% endif %}">
      <div class="val">{{ estoque_zerado_count }}</div>
      <div class="lbl">Zerados</div>
    </div>
  </div>
  {% if estoque_baixo %}
  <table class="est-table">
    <thead><tr><th>SKU</th><th>Produto</th><th>Categoria</th><th>Qtd</th></tr></thead>
    <tbody>
    {% for p in estoque_baixo %}
      <tr>
        <td><code>{{ p.sku }}</code></td>
        <td><a href="{% url 'admin:produtos_produto_change' p.pk %}">{{ p.nome }}</a></td>
        <td>{{ p.categoria.nome|default:"—" }}</td>
        <td>
          {% if p.estoque_total <= 0 %}<span class="badge badge-danger">Zerado</span>
          {% else %}<span class="badge badge-warning">{{ p.estoque_total }}</span>{% endif %}
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p style="color:var(--body-quiet-color)">Nenhum produto com estoque baixo.</p>
  {% endif %}
</div>

<script>
(function(){
  // Gráfico de linhas — Vendas e Lucro
  var ctx1 = document.getElementById('graficoVendas').getContext('2d');
  new Chart(ctx1, {
    type: 'line',
    data: {
      labels: {{ grafico_labels|safe }},
      datasets: [
        {
          label: 'Faturamento (R$)',
          data: {{ grafico_dados|safe }},
          borderColor: '#4e73df',
          backgroundColor: 'rgba(78,115,223,0.08)',
          borderWidth: 2, fill: true, tension: 0.35, pointRadius: 2
        },
        {
          label: 'Lucro Líquido (R$)',
          data: {{ grafico_lucro|safe }},
          borderColor: '#1cc88a',
          backgroundColor: 'rgba(28,200,138,0.05)',
          borderWidth: 2, fill: true, tension: 0.35, pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: true, position: 'top' } },
      scales: { y: { beginAtZero: true,
        ticks: { callback: function(v){ return 'R$ ' + v.toLocaleString('pt-BR'); } }
      }}
    }
  });

  // Gráfico de rosca — Canal
  var ctx2 = document.getElementById('graficoCanel').getContext('2d');
  var canalLabels = {{ vendas_canal_labels|safe }};
  var canalDados = {{ vendas_canal_dados|safe }};
  if (canalLabels.length > 0) {
    new Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: canalLabels,
        datasets: [{
          data: canalDados,
          backgroundColor: ['#4e73df','#1cc88a','#36b9cc','#f6c23e','#e74a3b'],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                return ' R$ ' + ctx.parsed.toLocaleString('pt-BR', {minimumFractionDigits:2});
              }
            }
          }
        }
      }
    });
  } else {
    document.getElementById('grafico-canal-wrap').innerHTML =
      '<p style="text-align:center;color:var(--body-quiet-color);padding-top:2rem">Sem vendas no mês.</p>';
  }
})();
</script>
{% endblock %}
```

- [ ] **Verificar check do Django**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py check
```

Esperado: `0 issues`.

- [ ] **Rodar todos os testes**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development .venv/bin/python manage.py test core -v 2
```

Esperado: todos passando.

- [ ] **Commit**

```bash
git add templates/admin/dashboard.html
git commit -m "feat: dashboard com 6 KPIs, dual-line, rosca canal, top5 produtos, resumo estoque"
```

---

## Task 6: barrsstore — Configuração de variáveis

**Files:**
- Modify: `barrs_store/settings.py`

Todos os comandos abaixo são executados em `~/Documents/projetos/barrsstore`.

- [ ] **Adicionar variáveis no settings**

Em `barrs_store/settings.py`, após as linhas de `WHATSAPP_*`:

```python
ERP_WEBHOOK_URL = os.environ.get('ERP_WEBHOOK_URL', '')
ERP_WEBHOOK_TOKEN = os.environ.get('ERP_WEBHOOK_TOKEN', '')
```

- [ ] **Adicionar ao .env do site**

No arquivo `.env` do barrsstore:

```
ERP_WEBHOOK_URL=https://barrs-erp-production.up.railway.app/webhook/nova-venda/
ERP_WEBHOOK_TOKEN=<mesmo valor de WEBHOOK_TOKEN do ERP>
```

- [ ] **Verificar check do Django**

```bash
cd ~/Documents/projetos/barrsstore
python manage.py check
```

Esperado: `0 issues`.

- [ ] **Commit**

```bash
git add barrs_store/settings.py
git commit -m "feat: adicionar ERP_WEBHOOK_URL e ERP_WEBHOOK_TOKEN ao settings"
```

---

## Task 7: barrsstore — Signal + apps.py

**Files:**
- Create: `loja/signals.py`
- Modify: `loja/apps.py`
- Modify: `loja/tests.py`

- [ ] **Adicionar testes do signal ao final de `loja/tests.py`**

```python
# ── TESTES DO SIGNAL DE WEBHOOK ───────────────────────────────────
import logging
from decimal import Decimal
from unittest.mock import call, patch

from django.test import TestCase, override_settings


def _criar_pedido_site(status='pendente'):
    return Pedido.objects.create(
        nome='Test',
        email='t@test.com',
        telefone='',
        cpf='',
        cep='01310-100',
        rua='Av Paulista',
        numero='1',
        bairro='Bela Vista',
        cidade='SP',
        estado='SP',
        forma_pagamento='pix',
        status=status,
        total=Decimal('100'),
    )


class WebhookSignalTests(TestCase):
    @patch('loja.signals._chamar_webhook_erp')
    def test_dispara_ao_confirmar(self, mock_chamar):
        ped = _criar_pedido_site('pendente')
        ped.status = 'confirmado'
        ped.save(update_fields=['status'])
        mock_chamar.assert_called_once_with(ped.id)

    @patch('loja.signals._chamar_webhook_erp')
    def test_nao_dispara_sem_status_no_update_fields(self, mock_chamar):
        ped = _criar_pedido_site('pendente')
        ped.nome = 'Outro'
        ped.save(update_fields=['nome'])
        mock_chamar.assert_not_called()

    @patch('loja.signals._chamar_webhook_erp')
    def test_nao_dispara_na_criacao(self, mock_chamar):
        _criar_pedido_site('confirmado')
        mock_chamar.assert_not_called()

    @patch('loja.signals._chamar_webhook_erp')
    def test_nao_dispara_para_outros_status(self, mock_chamar):
        ped = _criar_pedido_site('pendente')
        ped.status = 'enviado'
        ped.save(update_fields=['status'])
        mock_chamar.assert_not_called()

    @override_settings(
        ERP_WEBHOOK_URL='http://erp.test/webhook/nova-venda/',
        ERP_WEBHOOK_TOKEN='tok123',
    )
    @patch('loja.signals.requests.post')
    def test_chamar_webhook_faz_post_correto(self, mock_post):
        from loja.signals import _chamar_webhook_erp
        _chamar_webhook_erp(42)
        mock_post.assert_called_once_with(
            'http://erp.test/webhook/nova-venda/',
            json={'pedido_id': 42},
            headers={'X-Webhook-Token': 'tok123'},
            timeout=5,
        )

    @override_settings(ERP_WEBHOOK_URL='', ERP_WEBHOOK_TOKEN='')
    @patch('loja.signals.requests.post')
    def test_sem_url_nao_faz_post(self, mock_post):
        from loja.signals import _chamar_webhook_erp
        _chamar_webhook_erp(42)
        mock_post.assert_not_called()

    @override_settings(
        ERP_WEBHOOK_URL='http://erp.test/',
        ERP_WEBHOOK_TOKEN='tok',
    )
    @patch('loja.signals.requests.post', side_effect=Exception('timeout'))
    def test_falha_silenciosa(self, mock_post):
        from loja.signals import _chamar_webhook_erp
        # não deve levantar exceção
        _chamar_webhook_erp(42)
```

- [ ] **Rodar testes — esperar FAIL**

```bash
python manage.py test loja.tests.WebhookSignalTests -v 2
```

Esperado: `ImportError: cannot import name '_chamar_webhook_erp' from 'loja.signals'`.

- [ ] **Criar `loja/signals.py`**

```python
import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Pedido

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Pedido)
def notificar_erp_nova_venda(sender, instance, created, update_fields, **kwargs):
    if created:
        return
    if update_fields is not None and 'status' not in update_fields:
        return
    if instance.status != 'confirmado':
        return
    _chamar_webhook_erp(instance.id)


def _chamar_webhook_erp(pedido_id):
    url = getattr(settings, 'ERP_WEBHOOK_URL', '')
    token = getattr(settings, 'ERP_WEBHOOK_TOKEN', '')
    if not url or not token:
        return
    try:
        requests.post(
            url,
            json={'pedido_id': pedido_id},
            headers={'X-Webhook-Token': token},
            timeout=5,
        )
    except Exception as exc:
        logger.warning('ERP webhook falhou para pedido %s: %s', pedido_id, exc)
```

- [ ] **Atualizar `loja/apps.py`**

```python
from django.apps import AppConfig


class LojaConfig(AppConfig):
    name = 'loja'

    def ready(self):
        import loja.signals  # noqa: F401
```

- [ ] **Rodar testes — esperar PASS**

```bash
python manage.py test loja.tests.WebhookSignalTests -v 2
```

Esperado: 7 testes passando.

- [ ] **Rodar suite completa para verificar regressões**

```bash
python manage.py test loja -v 1
```

Esperado: todos os testes existentes continuam passando.

- [ ] **Commit**

```bash
git add loja/signals.py loja/apps.py loja/tests.py
git commit -m "feat: signal notificar_erp_nova_venda ao confirmar pedido no site"
```

---

## Checklist final — variáveis de ambiente no Railway

Antes de fazer push, confirmar que as seguintes variáveis estão configuradas no Railway de cada projeto:

**barrs-erp Railway:**
- [ ] `WEBHOOK_TOKEN` = valor gerado na Task 1

**barrsstore Railway:**
- [ ] `ERP_WEBHOOK_URL` = `https://barrs-erp-production.up.railway.app/webhook/nova-venda/`
- [ ] `ERP_WEBHOOK_TOKEN` = mesmo valor de `WEBHOOK_TOKEN`
