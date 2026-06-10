# Barrs ERP — Sprints de Desenvolvimento

> **Revisão crítica:** 2026-06-10  
> Contexto: loja de semijoias em fase inicial, 1–3 operadores.  
> Princípio: só entra no sprint o que gera valor real no dia a dia da loja.

---

## Sprints já executadas (histórico)

| Sprint | Entregue | Status |
|--------|----------|--------|
| S1 | Variações de produto (cor/tamanho), estoque por variação, webhook do site | ✅ |
| S2 | Endereços estruturados de cliente, rastreio no pedido, lookup de CEP | ✅ |
| S3 | Devolução e troca com reversão automática de estoque | ✅ |
| S4 | Fluxo de caixa, DRE, lançamentos automáticos, categorias financeiras | ✅ |
| S5 | Parcelamento de pagamentos, módulo de compras com recebimento | ✅ |

---

## Fase 1 — Limpeza e Essencial Faltante

> **Meta:** sistema enxuto, sem overhead, com as funcionalidades que o dia a dia realmente usa.

---

### Sprint 6 — Limpeza do Sistema
**Objetivo:** remover complexidade que não gera valor para uma loja pequena.  
**Prioridade:** 🔴 Alta — antes de construir mais, remover o que atrapalha.  
**Complexidade:** Baixa

#### O que remover/simplificar

- [x] **[BE]** Remover `EventoRastreio` da sidebar e tornar o model inativo no admin
- [x] **[BE]** Remover `ParcelaPagamento` do fluxo principal — modelo de parcelamento é overhead desnecessário para uma loja pequena onde o parcelamento fica com a maquininha/gateway
- [x] **[BE]** Substituir `LucroPedido` (model separado) por propriedade calculada: `Pedido.lucro_calculado` = `total_liquido - soma(custo_unitario × quantidade dos itens)`
- [x] **[BE]** Remover `FotoProduto` do admin — adicionar campo `imagem_url` (URLField, opcional) diretamente em `Produto`
- [x] **[BE]** Remover campo `pai` de `CategoriaFinanceira` — categorias simples são suficientes
- [x] **[BE]** Remover status `reservado` e `separacao` de `Pedido` — na prática não são usados
- [x] **[BE]** Remover `estoque_reservado` de `Produto` — nunca é atualizado automaticamente, campo morto
- [x] **[BE]** Remover `Categoria.slug` — slug é para URL pública, não tem uso no ERP interno
- [x] **[BE]** Simplificar sidebar: retirar `EventoRastreio`, `LancamentoCaixa` de Eventos de Rastreio e itens raramente acessados
- [x] **[BE]** Substituir app `compras` por tela simples de "Entrada de Estoque" (produto + qtd + custo + fornecedor → MovimentoEstoque)

#### Critério de aceite
- Admin mais limpo: sidebar com no máximo 10 itens visíveis
- Criar pedido completo em menos de 5 cliques
- Zero campos obrigatórios desnecessários nos formulários principais

---

### Sprint 7 — Campo `estoque_minimo` e Exportação de Vendas
**Objetivo:** alerta de estoque baixo funcional + exportação rápida para planilha.  
**Prioridade:** 🔴 Alta  
**Complexidade:** Baixa

#### Tarefas

- [ ] **[BE]** Adicionar `estoque_minimo` (IntegerField, default=0) em `Produto` e `VariacaoProduto`
- [ ] **[BE]** Dashboard: ajustar card de "Estoque Baixo" para usar `estoque_total <= estoque_minimo` em vez do hardcoded `<= 5`
- [ ] **[BE]** Dashboard: exibir lista de produtos zerados separada de "abaixo do mínimo"
- [ ] **[BE]** Endpoint CSV de vendas: `GET /relatorios/vendas.csv?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Colunas: data, nº pedido, cliente, canal, status, total, itens (resumo)
  - Usar `csv` nativo do Python, sem dependência extra
- [ ] **[BE]** Endpoint CSV de estoque: `GET /relatorios/estoque.csv`
  - Colunas: sku, produto, variação, estoque atual, estoque mínimo, custo, preço venda
- [ ] **[BE]** Links "Exportar CSV" visíveis no Dashboard e nas listas de Produtos/Pedidos

#### Critério de aceite
- Produto com `estoque_minimo = 3` e `estoque_total = 2` aparece no alerta
- CSV de vendas abre corretamente no Excel/Google Sheets com acentos

---

## Fase 2 — Produtividade

> **Meta:** menos tempo operando, mais visibilidade do negócio.

---

### Sprint 8 — Meta Mensal e Filtros Rápidos no Dashboard
**Objetivo:** gestor vê em 5 segundos se o mês está bem ou mal.  
**Prioridade:** 🟡 Média  
**Complexidade:** Baixa

#### Tarefas

- [ ] **[BE]** Criar model simples `MetaMensal` (ano, mes, valor_meta) — ou configuração direta no `settings.py`
- [ ] **[BE]** Dashboard: card de meta com barra de progresso (R$ atual / R$ meta / %)
- [ ] **[FE]** Dashboard: botões de atalho rápido para pedidos filtrados:
  - "Aguardando Pagamento (N)"
  - "A Enviar hoje (N)"
  - "Atrasados (N)" — pedidos pagos há mais de 3 dias sem rastreio
- [ ] **[BE]** Calcular `dias_sem_envio` para pedidos pagos sem `codigo_rastreio`

#### Critério de aceite
- Dashboard mostra meta e progresso sem precisar abrir nenhuma outra página
- Clicando em "A Enviar hoje" vai direto para lista filtrada de pedidos

---

### Sprint 9 — Integração Mercado Pago
**Objetivo:** pagamentos do site confirmam-se automaticamente no ERP.  
**Prioridade:** 🟡 Média  
**Complexidade:** Média

#### Tarefas

- [ ] **[BE]** Criar endpoint `POST /webhooks/mercadopago/` para receber notificações de pagamento
- [ ] **[BE]** Ao receber notificação de pagamento aprovado:
  - Localizar `Pedido` pelo `external_reference` (= `site_id`)
  - Mudar status para `pago`
  - Criar `Pagamento` com método e valor
  - Criar `LancamentoCaixa` de entrada automaticamente
- [ ] **[BE]** Validar assinatura do webhook (header `x-signature` do MP)
- [ ] **[BE]** Documentar no `sprints.md` como configurar a chave no Railway

#### Critério de aceite
- Pedido pago no site muda para status "pago" no ERP sem intervenção manual
- Tentativa de falsificação do webhook é rejeitada

---

### Sprint 10 — Integração Melhor Envio
**Objetivo:** gerar etiqueta de envio diretamente do pedido, sem copiar dados manualmente.  
**Prioridade:** 🟡 Média  
**Complexidade:** Média

#### Tarefas

- [ ] **[BE]** Integração com API Melhor Envio (OAuth2 ou token fixo)
- [ ] **[BE]** No `PedidoAdmin`: botão "Gerar Etiqueta" que abre modal com:
  - Peso e dimensões do pacote (configurável por padrão)
  - Transportadora selecionada (Correios/Jadlog/etc.)
  - Custo do frete calculado
- [ ] **[BE]** Ao confirmar: criar etiqueta via API → salvar `codigo_rastreio` e `url_rastreio` no pedido automaticamente
- [ ] **[BE]** Mudar status do pedido para `enviado` automaticamente ao gerar etiqueta
- [ ] **[BE]** Salvar credenciais do Melhor Envio como variáveis de ambiente (Railway)

#### Critério de aceite
- Operador gera etiqueta em 2 cliques sem sair do ERP
- Código de rastreio salvo automaticamente no pedido

---

## Fase 3 — Escala (quando o volume justificar)

> Só implementar quando a operação crescer e a complexidade se pagar.

---

### Sprint 11 — PDV (Ponto de Venda)
**Objetivo:** tela dedicada para criar pedidos por WhatsApp/presencial sem abrir o admin.  
**Prioridade:** 🟢 Baixa (o admin já funciona)  
**Complexidade:** Alta

- Busca de cliente por nome/WhatsApp
- Busca de produto por SKU/nome com grade de variações
- Carrinho simples com desconto e forma de pagamento
- Criar pedido sem sair da tela

---

### Sprint 12 — Integração Mercado Livre
**Objetivo:** pedidos do ML entram automaticamente no ERP.  
**Prioridade:** 🟢 Baixa (só quando a loja vender no ML)  
**Complexidade:** Alta

- Webhook ML → criar Pedido no ERP
- Sincronização de estoque (ERP → ML)
- Mapeamento de produtos por `item_id`

---

### Sprint 13 — NF-e
**Objetivo:** emitir nota fiscal diretamente do pedido.  
**Prioridade:** 🟢 Baixa (requer certificado A1)  
**Complexidade:** Muito Alta

- Integração com Focus NFe ou NFe.io
- Campos fiscais em Produto (NCM, CFOP, CST)
- Emissão e cancelamento via admin

---

### Sprint 14 — Permissões e CRM Básico
**Objetivo:** múltiplos usuários com acesso controlado.  
**Prioridade:** 🟢 Baixa (irrelevante com 1–3 operadores)  
**Complexidade:** Média

- Grupos: Vendedor, Estoque, Financeiro, Admin
- Tags de cliente (VIP, atacado, etc.)
- Campo avaliação no pedido

---

### Sprint 15 — Relatórios Avançados
**Objetivo:** análise de produtos e clientes por volume.  
**Prioridade:** 🟢 Baixa (sem volume, os dados não são representativos)  
**Complexidade:** Média

- Curva ABC de produtos (A=80% da receita, B=15%, C=5%)
- Segmentação RFM de clientes
- Exportação completa com filtros avançados

---

## Resumo das Sprints

| Sprint | Foco | Fase | Prioridade | Complexidade |
|--------|------|------|-----------|--------------|
| 1–5 | Variações, endereços, devoluções, financeiro, compras | — | ✅ Feito | — |
| 6 | Limpeza e simplificação do sistema | 1 | 🔴 Alta | Baixa |
| 7 | Estoque mínimo + exportação CSV | 1 | 🔴 Alta | Baixa |
| 8 | Meta mensal + filtros rápidos no dashboard | 2 | 🟡 Média | Baixa |
| 9 | Integração Mercado Pago | 2 | 🟡 Média | Média |
| 10 | Integração Melhor Envio | 2 | 🟡 Média | Média |
| 11 | PDV (ponto de venda) | 3 | 🟢 Baixa | Alta |
| 12 | Integração Mercado Livre | 3 | 🟢 Baixa | Alta |
| 13 | NF-e | 3 | 🟢 Baixa | Muito Alta |
| 14 | Permissões + CRM básico | 3 | 🟢 Baixa | Média |
| 15 | Relatórios avançados (ABC, RFM) | 3 | 🟢 Baixa | Média |

---

## Manual de Uso — Sprint 4 (Financeiro)

### 1. Categorias Financeiras
**Onde:** Admin → Categorias Financeiras

Crie uma vez:

| Nome | Tipo |
|------|------|
| Vendas | Receita |
| Despesas Operacionais | Despesa |
| Aluguel | Despesa |
| Embalagem | Despesa |
| Frete Saída | Despesa |
| Marketing | Despesa |
| Compras | Despesa |

### 2. Lançamentos de Caixa
**Automático:** pagamento aprovado → entrada criada; ContaPagar paga → saída criada.  
**Manual:** Admin → Lançamentos → informar data, tipo, valor, categoria, descrição.

### 3. Fluxo de Caixa
`GET /api/financeiro/fluxo-caixa/?inicio=2026-06-01&fim=2026-06-30`  
Retorna saldo acumulado dia a dia.

### 4. DRE
`GET /api/financeiro/dre/?ano=2026&mes=6`  
Retorna: receita bruta → CMV → lucro bruto → despesas → lucro líquido.

### 5. Rotina mensal
```
1º dia: cadastrar despesas fixas como ContaPagar
Dia a dia: lançamentos de vendas entram automaticamente
Ao pagar conta: marcar ContaPagar como "pago"
Fim do mês: consultar DRE
```

---

## Manual de Uso — Sprint 5 (Compras e Parcelamento)

### 1. Pagamento parcelado
Criar Pagamento com `Nº de Parcelas > 1` → gera parcelas com vencimentos mensais + ContaReceber por parcela automaticamente.

### 2. Pedido de Compra
1. Admin → Pedidos de Compra → criar com itens e custo unitário
2. Mudar status para "Enviado ao Fornecedor"
3. Mercadoria chegou → criar Recebimento → informar qtd por item → marcar Confirmado
4. Ao confirmar: estoque entra, custo atualiza, ContaPagar criada automaticamente

### 3. Pagar o fornecedor
Contas a Pagar → localizar a conta do recebimento → marcar como "pago" → lançamento de saída criado.
