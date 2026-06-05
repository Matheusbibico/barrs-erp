# importar_site + Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Management command que importa produtos/clientes/pedidos do banco secundário do site Django, e dashboard em `/dashboard/` com KPI cards + gráfico Chart.js integrado ao Jazzmin.

**Architecture:** Django multi-DB (`DATABASES['site']` via `SITE_DATABASE_URL`) com modelos espelho `unmanaged` para leitura. Campo `site_id` como chave de deduplicação. Dashboard via view Django que herda template do Jazzmin.

**Tech Stack:** Django 5.2, dj-database-url, psycopg2-binary, Chart.js 4.4 (CDN)

---

## File Map

**Criar:**
- `core/site_models.py` — modelos unmanaged espelhando banco do site
- `core/management/commands/importar_site.py` — command de importação
- `core/views.py` — DashboardView
- `templates/admin/dashboard.html` — template do dashboard

**Modificar:**
- `barrs_erp/settings/base.py` — `DATABASES['site']` + link Jazzmin
- `barrs_erp/urls.py` — rota `/dashboard/`
- `produtos/models.py` — campo `site_id`
- `clientes/models.py` — campo `site_id`
- `pedidos/models.py` — campo `site_id`

---

### Task 1: Multi-DB config

**Files:**
- Modify: `barrs_erp/settings/base.py`

- [ ] **Step 1: Adicionar banco `site` ao DATABASES**

Em `barrs_erp/settings/base.py`, logo após o bloco `DATABASES = {...}`, adicionar:

```python
_site_db_url = config('SITE_DATABASE_URL', default='')
if _site_db_url:
    DATABASES['site'] = dj_database_url.parse(_site_db_url, conn_max_age=60)
```

- [ ] **Step 2: Verificar check**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add barrs_erp/settings/base.py
git commit -m "feat: adicionar DATABASES['site'] via SITE_DATABASE_URL"
```

---

### Task 2: Modelos espelho do site

**Files:**
- Create: `core/site_models.py`

- [ ] **Step 1: Criar core/site_models.py**

```python
from django.db import models


class SiteCategoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        managed = False
        db_table = 'loja_categoria'
        app_label = 'core'


class SiteProduto(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.IntegerField(default=0)
    categoria = models.ForeignKey(
        SiteCategoria, on_delete=models.SET_NULL, null=True, blank=True,
    )
    codigo_interno = models.CharField(max_length=50, blank=True)
    visivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'loja_produto'
        app_label = 'core'


class SiteUser(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()

    class Meta:
        managed = False
        db_table = 'auth_user'
        app_label = 'core'


class SitePerfilCliente(models.Model):
    user = models.OneToOneField(
        SiteUser, on_delete=models.CASCADE, related_name='perfil',
    )
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)

    class Meta:
        managed = False
        db_table = 'loja_perfilcliente'
        app_label = 'core'


class SitePedido(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    forma_pagamento = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'loja_pedido'
        app_label = 'core'


class SiteItemPedido(models.Model):
    pedido = models.ForeignKey(
        SitePedido, on_delete=models.CASCADE, related_name='itens',
    )
    produto = models.ForeignKey(
        SiteProduto, on_delete=models.SET_NULL, null=True, blank=True,
    )
    nome_produto = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'loja_itempedido'
        app_label = 'core'
```

- [ ] **Step 2: Confirmar que nenhuma migration é gerada**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py makemigrations --check
```
Expected: `No changes detected`

- [ ] **Step 3: Commit**

```bash
git add core/site_models.py
git commit -m "feat: modelos espelho unmanaged para leitura do banco do site"
```

---

### Task 3: Campo site_id + migrations

**Files:**
- Modify: `produtos/models.py`, `clientes/models.py`, `pedidos/models.py`

- [ ] **Step 1: Adicionar site_id ao Produto**

Em `produtos/models.py`, na classe `Produto`, após o campo `status`:

```python
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
```

- [ ] **Step 2: Adicionar site_id ao Cliente**

Em `clientes/models.py`, na classe `Cliente`, após o campo `observacoes`:

```python
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
```

- [ ] **Step 3: Adicionar site_id ao Pedido**

Em `pedidos/models.py`, na classe `Pedido`, após o campo `observacoes`:

```python
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
```

- [ ] **Step 4: Gerar migrations**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py makemigrations produtos clientes pedidos
```
Expected: 3 arquivos criados (0002_produto_site_id, 0002_cliente_site_id, 0002_pedido_site_id)

- [ ] **Step 5: Aplicar localmente**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py migrate
```
Expected: `OK` para as 3 migrations

- [ ] **Step 6: Commit**

```bash
git add produtos/models.py produtos/migrations/ \
        clientes/models.py clientes/migrations/ \
        pedidos/models.py pedidos/migrations/
git commit -m "feat: campo site_id em Produto, Cliente e Pedido para deduplicação de import"
```

---

### Task 4: Management command importar_site

**Files:**
- Create: `core/management/commands/importar_site.py`

- [ ] **Step 1: Criar o command completo**

```python
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

import pedidos.signals as pedido_signals
from core.site_models import (
    SiteCategoria, SiteItemPedido, SitePedido,
    SitePerfilCliente, SiteProduto, SiteUser,
)
from clientes.models import Cliente
from pedidos.models import ItemPedido, Pagamento, Pedido
from produtos.models import Categoria, Produto

STATUS_MAP = {
    'pendente': Pedido.STATUS_AGUARDANDO,
    'confirmado': Pedido.STATUS_PAGO,
    'enviado': Pedido.STATUS_ENVIADO,
    'entregue': Pedido.STATUS_ENTREGUE,
    'cancelado': Pedido.STATUS_CANCELADO,
}


class Command(BaseCommand):
    help = 'Importa produtos, clientes e pedidos do banco secundário do site Django'

    def handle(self, *args, **options):
        post_save.disconnect(pedido_signals.calcular_lucro_pedido, sender=Pedido)
        post_save.disconnect(pedido_signals.atualizar_historico_cliente, sender=Pedido)
        try:
            stats = {
                'categorias': self._importar_categorias(),
                'produtos':   self._importar_produtos(),
                'clientes':   self._importar_clientes(),
                'pedidos':    self._importar_pedidos(),
            }
        finally:
            post_save.connect(pedido_signals.calcular_lucro_pedido, sender=Pedido)
            post_save.connect(pedido_signals.atualizar_historico_cliente, sender=Pedido)
        self._relatorio(stats)

    # ------------------------------------------------------------------ #

    def _importar_categorias(self):
        self.stdout.write('Importando categorias...')
        criadas = atualizadas = erros = 0
        for sc in SiteCategoria.objects.using('site').all():
            try:
                cat, created = Categoria.objects.get_or_create(
                    slug=sc.slug,
                    defaults={'nome': sc.nome},
                )
                if created:
                    criadas += 1
                else:
                    cat.nome = sc.nome
                    cat.save(update_fields=['nome'])
                    atualizadas += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Categoria {sc.slug}: {exc}'))
                erros += 1
        return {'criadas': criadas, 'atualizadas': atualizadas, 'erros': erros}

    def _importar_produtos(self):
        self.stdout.write('Importando produtos...')
        criados = atualizados = erros = 0
        cat_map = {c.slug: c for c in Categoria.objects.all()}

        # Produto placeholder para itens de pedido cujo produto não existe no ERP
        placeholder, _ = Produto.objects.get_or_create(
            sku='SITE-DESCONHECIDO',
            defaults={
                'nome': 'Produto não identificado (importado)',
                'preco_venda': Decimal('0'),
                'custo': Decimal('0'),
                'status': Produto.STATUS_INATIVO,
            },
        )

        for sp in SiteProduto.objects.using('site').select_related('categoria'):
            try:
                sku = (sp.codigo_interno or '').strip() or f'SITE-{sp.id}'
                status = Produto.STATUS_ATIVO if sp.visivel else Produto.STATUS_INATIVO
                cat = cat_map.get(sp.categoria.slug) if sp.categoria else None

                prod, created = Produto.objects.get_or_create(
                    site_id=sp.id,
                    defaults={
                        'sku': sku,
                        'nome': sp.nome,
                        'preco_venda': sp.preco,
                        'custo': Decimal('0'),
                        'estoque_total': sp.estoque,
                        'categoria': cat,
                        'status': status,
                    },
                )
                if created:
                    criados += 1
                else:
                    prod.nome = sp.nome
                    prod.preco_venda = sp.preco
                    prod.estoque_total = sp.estoque
                    prod.status = status
                    prod.categoria = cat
                    prod.save(update_fields=[
                        'nome', 'preco_venda', 'estoque_total', 'status', 'categoria',
                    ])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Produto site_id={sp.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _importar_clientes(self):
        self.stdout.write('Importando clientes...')
        criados = atualizados = erros = 0

        for su in SiteUser.objects.using('site').all():
            try:
                try:
                    perfil = SitePerfilCliente.objects.using('site').get(user_id=su.id)
                    whatsapp, cidade, estado = perfil.telefone, perfil.cidade, perfil.estado
                except SitePerfilCliente.DoesNotExist:
                    whatsapp = cidade = estado = ''

                nome = f'{su.first_name} {su.last_name}'.strip() or su.email

                cli, created = Cliente.objects.get_or_create(
                    site_id=su.id,
                    defaults={
                        'nome': nome,
                        'email': su.email,
                        'whatsapp': whatsapp,
                        'cidade': cidade,
                        'estado': estado,
                    },
                )
                if created:
                    criados += 1
                else:
                    cli.nome = nome
                    cli.email = su.email
                    cli.whatsapp = whatsapp
                    cli.save(update_fields=['nome', 'email', 'whatsapp'])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  User site_id={su.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _importar_pedidos(self):
        self.stdout.write('Importando pedidos...')
        criados = atualizados = erros = 0

        prod_map = {p.site_id: p for p in Produto.objects.filter(site_id__isnull=False)}
        placeholder = Produto.objects.get(sku='SITE-DESCONHECIDO')
        cli_email_map = {c.email: c for c in Cliente.objects.exclude(email='')}

        for sp in SitePedido.objects.using('site').prefetch_related('itens__produto'):
            try:
                status_erp = STATUS_MAP.get(sp.status, Pedido.STATUS_ORCAMENTO)

                cliente = cli_email_map.get(sp.email)
                if not cliente:
                    nome = sp.nome or sp.email
                    cliente, _ = Cliente.objects.get_or_create(
                        email=sp.email,
                        defaults={
                            'nome': nome,
                            'whatsapp': sp.telefone,
                            'cidade': sp.cidade,
                            'estado': sp.estado,
                        },
                    )
                    if sp.email:
                        cli_email_map[sp.email] = cliente

                ped, created = Pedido.objects.get_or_create(
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
                if created:
                    criados += 1
                    for si in sp.itens.all():
                        produto = prod_map.get(si.produto_id) if si.produto_id else placeholder
                        ItemPedido.objects.create(
                            pedido=ped,
                            produto=produto or placeholder,
                            quantidade=si.quantidade,
                            preco_unitario=si.preco_unitario,
                            custo_unitario=Decimal('0'),
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
                else:
                    ped.status = status_erp
                    ped.total_liquido = sp.total
                    ped.save(update_fields=['status', 'total_liquido'])
                    atualizados += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Pedido site_id={sp.id}: {exc}'))
                erros += 1
        return {'criadas': criados, 'atualizadas': atualizados, 'erros': erros}

    def _relatorio(self, stats):
        labels = {
            'categorias': 'Categorias',
            'produtos':   'Produtos  ',
            'clientes':   'Clientes  ',
            'pedidos':    'Pedidos   ',
        }
        self.stdout.write('\n' + self.style.SUCCESS('Relatório final:'))
        for key, label in labels.items():
            s = stats.get(key, {})
            c = s.get('criadas', 0)
            a = s.get('atualizadas', 0)
            e = s.get('erros', 0)
            cor = self.style.SUCCESS if e == 0 else self.style.WARNING
            self.stdout.write(cor(f'  {label}: {c} criadas | {a} atualizadas | {e} erros'))
```

- [ ] **Step 2: Verificar que o command está visível**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py help importar_site
```
Expected: exibe `usage: manage.py importar_site` sem ImportError

- [ ] **Step 3: Commit**

```bash
git add core/management/commands/importar_site.py
git commit -m "feat: management command importar_site com dedup via site_id"
```

---

### Task 5: Dashboard view

**Files:**
- Create: `core/views.py`

- [ ] **Step 1: Criar core/views.py**

```python
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from pedidos.models import LucroPedido, Pedido
from produtos.models import Produto


@staff_member_required
def dashboard(request):
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    trinta_dias_atras = hoje - timedelta(days=30)

    faturamento_hoje = Pedido.objects.filter(
        status='pago', criado_em__date=hoje,
    ).aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')

    faturamento_mes = Pedido.objects.filter(
        status='pago', criado_em__date__gte=inicio_mes,
    ).aggregate(v=Sum('total_liquido'))['v'] or Decimal('0')

    lucro_mes = LucroPedido.objects.filter(
        pedido__criado_em__date__gte=inicio_mes,
    ).aggregate(v=Sum('lucro_liquido'))['v'] or Decimal('0')

    pedidos_pendentes = Pedido.objects.filter(
        status__in=['orcamento', 'reservado', 'aguardando_pagamento'],
    ).count()

    estoque_baixo = (
        Produto.objects
        .filter(status='ativo', estoque_total__lte=5)
        .select_related('categoria')
        .order_by('estoque_total')[:10]
    )

    vendas_qs = (
        Pedido.objects
        .filter(status='pago', criado_em__date__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('criado_em'))
        .values('dia')
        .annotate(total=Sum('total_liquido'))
        .order_by('dia')
    )
    vendas_dict = {v['dia']: float(v['total']) for v in vendas_qs}

    labels, dados = [], []
    dia = trinta_dias_atras
    while dia <= hoje:
        labels.append(dia.strftime('%d/%m'))
        dados.append(vendas_dict.get(dia, 0))
        dia += timedelta(days=1)

    return render(request, 'admin/dashboard.html', {
        'title': 'Dashboard',
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'lucro_mes': lucro_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'estoque_baixo': estoque_baixo,
        'grafico_labels': json.dumps(labels),
        'grafico_dados': json.dumps(dados),
    })
```

- [ ] **Step 2: Commit**

```bash
git add core/views.py
git commit -m "feat: DashboardView com KPIs, estoque baixo e dados do gráfico"
```

---

### Task 6: Dashboard template + URLs + Jazzmin

**Files:**
- Create: `templates/admin/dashboard.html`
- Modify: `barrs_erp/urls.py`, `barrs_erp/settings/base.py`

- [ ] **Step 1: Criar templates/admin/dashboard.html**

```html
{% extends "admin/base_site.html" %}
{% load i18n %}

{% block extrahead %}
{{ block.super }}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}
.kpi-card{background:var(--secondary,#fff);border:1px solid var(--border-color,#dee2e6);border-radius:6px;padding:1.25rem;text-align:center}
.kpi-value{font-size:1.8rem;font-weight:700;color:var(--primary,#007bff)}
.kpi-label{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--body-quiet-color,#888);margin-top:.25rem}
.kpi-card.alerta .kpi-value{color:#e74c3c}
.dash-section{background:var(--secondary,#fff);border:1px solid var(--border-color,#dee2e6);border-radius:6px;padding:1.25rem;margin-bottom:1.5rem}
.dash-section h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.07em;color:var(--body-quiet-color,#888);margin:0 0 1rem;padding-bottom:.5rem;border-bottom:1px solid var(--border-color,#dee2e6)}
#grafico-wrap{position:relative;height:280px}
.est-table{width:100%;border-collapse:collapse;font-size:.9rem}
.est-table th,.est-table td{text-align:left;padding:.45rem .75rem;border-bottom:1px solid var(--border-color,#dee2e6)}
.est-table th{font-weight:600}
.badge{padding:2px 8px;border-radius:4px;font-size:.75rem;color:#fff}
.badge-danger{background:#e74c3c}.badge-warning{background:#f39c12}
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
</div>

<div class="dash-section">
  <h2>Vendas — Últimos 30 Dias</h2>
  <div id="grafico-wrap">
    <canvas id="graficoVendas"></canvas>
  </div>
</div>

<div class="dash-section">
  <h2>Estoque Baixo (≤ 5 unidades)</h2>
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
          {% if p.estoque_total == 0 %}
            <span class="badge badge-danger">Zerado</span>
          {% else %}
            <span class="badge badge-warning">{{ p.estoque_total }}</span>
          {% endif %}
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
  var labels = {{ grafico_labels|safe }};
  var dados  = {{ grafico_dados|safe }};
  var ctx = document.getElementById('graficoVendas').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Faturamento (R$)',
        data: dados,
        borderColor: '#4e73df',
        backgroundColor: 'rgba(78,115,223,0.08)',
        borderWidth: 2,
        fill: true,
        tension: 0.35,
        pointRadius: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: function(v){ return 'R$ ' + v.toLocaleString('pt-BR'); } }
        }
      }
    }
  });
})();
</script>
{% endblock %}
```

- [ ] **Step 2: Adicionar rota /dashboard/ em urls.py**

Substituir o conteúdo de `barrs_erp/urls.py` por:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard, name='dashboard'),
    path('api/', include([
        path('produtos/', include('produtos.urls')),
        path('clientes/', include('clientes.urls')),
        path('pedidos/', include('pedidos.urls')),
        path('estoque/', include('estoque.urls')),
        path('financeiro/', include('financeiro.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 3: Adicionar link Dashboard no Jazzmin**

Em `barrs_erp/settings/base.py`, dentro de `JAZZMIN_SETTINGS`, substituir `topmenu_links`:

```python
"topmenu_links": [
    {"name": "Dashboard", "url": "/dashboard/"},
    {"name": "API", "url": "/api/", "new_window": True},
    {"name": "Home", "url": "admin:index"},
],
```

- [ ] **Step 4: Verificar check final**

```bash
DJANGO_SETTINGS_MODULE=barrs_erp.settings.development python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add templates/admin/dashboard.html barrs_erp/urls.py barrs_erp/settings/base.py
git commit -m "feat: dashboard /dashboard/ com KPIs, estoque baixo e gráfico Chart.js"
```

---

### Task 7: Push e verificação

- [ ] **Step 1: Push**

```bash
git push
```

- [ ] **Step 2: Após deploy Railway, verificar**

1. Acesse `/admin/` → deve aparecer "Dashboard" no menu superior
2. Acesse `/dashboard/` → 4 KPI cards + gráfico vazio (banco novo) + tabela de estoque
3. Se `SITE_DATABASE_URL` estiver configurado, rodar via Railway Run Command:
   ```bash
   python manage.py importar_site
   ```
   Expected: relatório final sem erros críticos, `/dashboard/` exibe dados reais
