# Auditoria Técnica do ERP Barrs Store

Data: 10/06/2026 — Auditor: análise automatizada (Claude)

## 1. Resumo executivo

O sistema está **bem encaminhado, mas NÃO está pronto para uso real** por causa de 3 problemas críticos: **vendas não dão baixa no estoque**, **senha padrão fraca do admin** e **risco de perda de dados no Railway** (banco/fotos). A segurança web (CSRF, HTTPS, webhooks assinados, API autenticada) está correta. Os cálculos financeiros usam `Decimal` corretamente. A arquitetura é simples e adequada ao porte da loja — não precisa de refatoração.

## 2. Problemas críticos

### C1 — Venda nunca dá baixa no estoque
- **Arquivo:** nenhum (código ausente) — esperado em `pedidos/signals.py`
- **Problema:** Não existe NENHUM ponto no sistema que crie `MovimentoEstoque` tipo `saida` quando um pedido é pago. Estoque só muda por: compras (entrada), devolução aprovada (entrada), ajuste manual e sincronização do site (sobrescreve total). Vendas manuais/fora do site **nunca** reduzem estoque.
- **Risco real:** estoque sempre inflado → vender produto que não existe, inventário irreal, lucro/CMV sem confiabilidade física.
- **Prioridade:** **Crítica**
- **Correção:** signal `post_save` em Pedido: quando status muda para `pago`, criar um `MovimentoEstoque(tipo='saida', quantidade=-item.quantidade)` por item, com guarda de idempotência (verificar se já existe movimento de saída ligado ao pedido). ~30 linhas, isolado, reversível.

### C2 — Senha padrão `admin123` no superusuário
- **Arquivo:** `core/management/commands/create_default_admin.py`
- **Problema:** se `ADMIN_PASSWORD` não estiver setada no Railway, cria superusuário `admin`/`admin123` em URL pública.
- **Risco real:** invasão trivial do admin → acesso total a clientes, finanças e pedidos.
- **Prioridade:** **Crítica**
- **Correção:** (1) o comando deve **recusar** criar usuário sem `ADMIN_PASSWORD` definida; (2) **trocar a senha do admin atual em produção AGORA** (pode ter sido criada com o default).

### C3 — Risco de perda de dados no Railway (banco e fotos)
- **Arquivo:** `barrs_erp/settings/base.py` (DATABASES fallback sqlite, MEDIA_ROOT local)
- **Problema:** (a) se `DATABASE_URL` não estiver setada no Railway, o banco é SQLite dentro do container — **apagado a cada deploy**; (b) `MEDIA_ROOT` é pasta local — fotos de produto somem a cada deploy; (c) WhiteNoise não serve `/media/` e o urls.py só serve media com `DEBUG=True` → fotos quebradas em produção mesmo antes de sumir.
- **Risco real:** perda total de dados de vendas/clientes ou de todas as fotos.
- **Prioridade:** **Crítica** (verificar) / **Alta** (media)
- **Correção:** confirmar `DATABASE_URL` (Postgres) no Railway — se já usa Postgres, (a) está OK; para fotos, usar volume persistente do Railway ou armazenamento externo (Cloudinary/S3). Sem isso, evitar depender de upload de fotos no ERP (o catálogo já vem do site).

### C4 — Segundo pagamento do mesmo pedido não entra no caixa
- **Arquivo:** `financeiro/signals.py` (`pagamento_aprovado_gera_lancamento`)
- **Problema:** a deduplicação por `descricao__startswith='Pagamento pedido'` bloqueia QUALQUER segundo pagamento aprovado do mesmo pedido (ex.: entrada + restante).
- **Risco real:** dinheiro recebido que não aparece no caixa → caixa menor que o real.
- **Prioridade:** **Alta**
- **Correção:** deduplicar por pagamento específico (ex.: FK `pagamento` no LancamentoCaixa, ou descrição com id do Pagamento), não por pedido.

### C5 — Estorno de devolução invisível no caixa
- **Arquivo:** `pedidos/signals.py` (`processar_aprovacao_devolucao`)
- **Problema:** reembolso vira `ContaReceber` com valor **negativo** e status `recebido` — nunca gera `LancamentoCaixa` de saída. O dinheiro devolvido ao cliente não aparece no fluxo de caixa nem no DRE.
- **Risco real:** caixa e lucro superestimados quando há devoluções.
- **Prioridade:** **Alta**
- **Correção:** em vez do ContaReceber negativo, criar `LancamentoCaixa(tipo='saida')` com vínculo ao pedido.

## 3. Melhorias recomendadas

| # | Melhoria | Arquivo | Prioridade |
|---|----------|---------|------------|
| M1 | Impedir venda sem estoque (validação no `ItemPedido.clean` comparando com saldo) — ou apenas alertar | `pedidos/models.py` | Média |
| M2 | Status `vencido` em ContaReceber/ContaPagar nunca é marcado automaticamente — comando diário simples ou calcular on-the-fly | `financeiro/` | Média |
| M3 | `Pedido.calcular_totais()` é manual — totals podem divergir dos itens. Recalcular no admin via `save_related` | `pedidos/admin.py` | Média |
| M4 | `ParcelaPagamento` paga não gera lançamento no caixa | `financeiro/signals.py` | Média |
| M5 | `MetaMensal.__str__` usa `calendar.month_name` (sai em inglês) — usar lista PT já existente no admin | `financeiro/models.py` | Baixa |
| M6 | Índice em `LancamentoCaixa.data` (ordering + filtros) | migration nova | Baixa |
| M7 | Backup automático do Postgres no Railway (verificar se plano inclui; senão, cron de `pg_dump`) | infra | Alta |

## 4. O que remover ou simplificar

- **`CategoriaFinanceira`**: o model ainda existe mas foi removido do admin/fluxo (lançamentos não usam mais). Manter o model por ora (dados antigos), mas remover o endpoint da API `/api/financeiro/categorias/` se não houver consumidor.
- **`EventoRastreio` / transportadora**: só vale manter se realmente alimentado pelo site; não exigir nada disso em pedidos manuais (já está opcional — OK).
- **`LucroPedido`** com taxa/embalagem por pedido: bom conceito, mas só útil se alguém preencher. Se não for usado no dia a dia, o `lucro_calculado` (receita − custo dos itens) já basta.
- **BasicAuthentication** na API: se a API só é usada pelo próprio admin logado (Session), pode remover Basic. Baixo risco mantê-la (exige HTTPS, já forçado).

## 5. Checklist de segurança

| Item | Status |
|------|--------|
| DEBUG=False em produção | ✅ OK |
| SECRET_KEY via env | ✅ OK (fallback inseguro só em dev) |
| ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS via env | ✅ OK |
| HTTPS forçado + HSTS + cookies secure | ✅ OK |
| Admin protegido (staff) — dashboard e CSVs também | ✅ OK |
| API exige autenticação (IsAuthenticated) | ✅ OK |
| Webhook nova-venda com token HMAC (compare_digest) | ✅ OK |
| Webhook Mercado Pago com assinatura validada | ✅ OK |
| .env e db.sqlite3 fora do git | ✅ OK |
| Logs sem dados sensíveis | ✅ OK |
| **Senha padrão admin123** | 🔴 **CRÍTICO — trocar já** |
| **Fotos/media em produção** | 🟡 Pendente (não servidas/persistidas) |
| SQL Injection | ✅ OK (só ORM, sem raw SQL) |
| XSS | ✅ OK (format_html usado corretamente nos badges) |

## 6. Checklist financeiro/estoque

| Item | Status |
|------|--------|
| Decimal em todos os valores monetários | ✅ OK |
| Receita (DRE) = pedidos pagos no período | ✅ OK |
| CMV = custo_unitario × quantidade dos itens | ✅ OK |
| Lucro bruto/líquido e margens no DRE | ✅ OK |
| Pagamento aprovado → entrada no caixa | 🟡 OK só para o 1º pagamento (C4) |
| Conta paga → saída no caixa (com pago_em automático) | ✅ OK |
| **Venda → baixa de estoque** | 🔴 **NÃO EXISTE (C1)** |
| Devolução → estoque volta (itens em bom estado) | ✅ OK (idempotente via aprovada_em) |
| **Devolução → dinheiro sai do caixa** | 🔴 Invisível no caixa (C5) |
| Compra recebida → entrada de estoque | ✅ OK |
| Movimento de estoque com lock (select_for_update) e histórico de saldo | ✅ OK |
| Venda sem estoque bloqueada | 🟡 Não bloqueia (M1) |
| Parcelas → caixa | 🟡 Não integra (M4) |
| Histórico do cliente (total gasto, qtd pedidos) | ✅ OK |

## 7. Plano de correção seguro

**Etapa 1 — Riscos críticos (fazer já, um por commit):**
1. `create_default_admin`: recusar criar sem `ADMIN_PASSWORD` + **trocar senha do admin em produção**
2. Confirmar `DATABASE_URL` (Postgres) no Railway
3. Baixa de estoque em pedido pago (C1) — signal idempotente

**Etapa 2 — Regras financeiras:**
4. Corrigir dedup do lançamento de pagamento (C4)
5. Estorno de devolução como saída de caixa (C5)

**Etapa 3 — Consistência:**
6. Recalcular totais do pedido ao salvar itens no admin (M3)
7. Marcar vencidos automaticamente (M2)

**Etapa 4 — Simplificação/performance:**
8. Remover endpoint de categorias se não usado; índice em data; backup.

## 8. Antes de alterar código

| Mudança | Arquivos | Risco | Como testar |
|---------|----------|-------|-------------|
| C2 admin password | `core/management/commands/create_default_admin.py` | Baixo — só afeta criação inicial | Rodar comando sem env → deve falhar com mensagem clara |
| C1 baixa de estoque | `pedidos/signals.py` | Médio — regra nova; idempotência obrigatória | Criar pedido, marcar pago → conferir MovimentoEstoque e saldo; salvar 2× → sem duplicar |
| C4 dedup pagamento | `financeiro/signals.py` | Baixo | 2 pagamentos no mesmo pedido → 2 lançamentos |
| C5 estorno caixa | `pedidos/signals.py` | Baixo | Aprovar devolução reembolso → saída no caixa |
