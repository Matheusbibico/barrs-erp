# Barrs ERP — Sprints de Desenvolvimento

> Baseado em: [erp-gaps.md](erp-gaps.md)  
> Cadência: sprints de 2 semanas  
> Início estimado: 2026-06-09

---

## Fase 1 — Operação Básica Completa
> Meta: loja consegue operar o dia a dia sem gambiarras

---

### Sprint 1 — Variações de Produto (Grade)
**Período:** 09/06 → 22/06  
**Objetivo:** Loja de moda consegue cadastrar produtos com cor e tamanho, controlar estoque por variação e vender uma variação específica.

#### Tarefas

- [ ] **[BE]** Criar model `VariacaoProduto` (produto, cor, tamanho, sku, custo, preco_venda, estoque, ativo)
- [ ] **[BE]** Criar migration e registrar no admin com inline de grade (matriz cor × tamanho)
- [ ] **[BE]** Adaptar `ItemPedido` para ter FK opcional `variacao` (além de `produto`)
- [ ] **[BE]** Adaptar `MovimentoEstoque` para movimentar por variação quando existir
- [ ] **[BE]** Atualizar `Produto.estoque_total` para ser soma das variações (ou manter manual para produto simples)
- [ ] **[BE]** Adaptar serializers da API: `ProdutoSerializer` expor variações; `ItemPedidoSerializer` aceitar `variacao_id`
- [ ] **[BE]** Adaptar webhook `_importar_pedido_unico` para mapear variação por `site_id` do produto
- [ ] **[TEST]** Criar produto simples e produto com grade, verificar estoque por variação
- [ ] **[TEST]** Criar pedido com variação via API, confirmar desconto de estoque correto

#### Critério de aceite
- Produto "Camiseta" com variações P/Azul, M/Azul, G/Preto cadastradas com estoques independentes
- Ao criar pedido com M/Azul, só o estoque da variação M/Azul é decrementado
- Admin mostra a grade visualmente (tabela cor × tamanho)

---

### Sprint 2 — Endereços e Rastreamento de Envio
**Período:** 23/06 → 06/07  
**Objetivo:** Cliente tem endereços salvos; pedido enviado tem código de rastreio visível.

#### Tarefas

- [ ] **[BE]** Criar model `EnderecoCliente` (cliente, cep, logradouro, numero, complemento, bairro, cidade, estado, principal, apelido)
- [ ] **[BE]** Criar migration + admin inline em `ClienteAdmin`
- [ ] **[BE]** Trocar `Pedido.endereco_entrega` (TextField) por FK `endereco_entrega → EnderecoCliente` (manter TextField como fallback para pedidos antigos)
- [ ] **[BE]** Adicionar campos em `Pedido`: `transportadora`, `codigo_rastreio`, `url_rastreio`, `previsao_entrega`
- [ ] **[BE]** Criar model `EventoRastreio` (pedido, data, status, descricao) para histórico de rastreio
- [ ] **[BE]** Endpoint API para buscar CEP via ViaCEP (`GET /api/cep/<cep>/`)
- [ ] **[BE]** Serializers e endpoints atualizados: `EnderecoClienteViewSet`, campos de rastreio em `PedidoSerializer`
- [ ] **[TEST]** Criar cliente, adicionar 2 endereços, marcar um como principal
- [ ] **[TEST]** Atualizar pedido com código de rastreio, verificar histórico de eventos

#### Critério de aceite
- Cliente tem endereços com CEP autopreenchível
- Pedido enviado exibe transportadora + código de rastreio
- Histórico de rastreio registra eventos cronológicos

---

### Sprint 3 — Devolução e Troca
**Período:** 07/07 → 20/07  
**Objetivo:** Operador consegue registrar uma devolução, aprovar e o estoque volta automaticamente.

#### Tarefas

- [ ] **[BE]** Criar model `Devolucao` (pedido, tipo: reembolso/troca/crédito, motivo, status: solicitada/aprovada/recusada/concluída, responsavel)
- [ ] **[BE]** Criar model `ItemDevolucao` (devolucao, item_pedido, quantidade, condicao: ok/defeito/avaria)
- [ ] **[BE]** Signal/método: ao aprovar devolução → criar `MovimentoEstoque` de entrada para cada item devolvido em bom estado
- [ ] **[BE]** Signal: ao aprovar reembolso → criar `ContaReceber` estornada ou lançamento de saída no caixa
- [ ] **[BE]** Adicionar status `devolvido` e `troca_pendente` em `Pedido.STATUS_CHOICES`
- [ ] **[BE]** Admin: `DevolucaoAdmin` com inline de itens, ação "Aprovar devolução"
- [ ] **[BE]** Serializers e endpoints para `Devolucao`
- [ ] **[TEST]** Criar devolução para pedido pago, aprovar, verificar estoque revertido
- [ ] **[TEST]** Devolução por troca: item devolvido + novo pedido de troca vinculado

#### Critério de aceite
- Devolução aprovada reverte estoque automaticamente
- Tipo reembolso gera registro financeiro de saída
- Tipo troca cria novo pedido vinculado à devolução original

---

## Fase 2 — Financeiro Real
> Meta: gestão financeira completa, não só registros soltos

---

### Sprint 4 — Fluxo de Caixa e DRE
**Período:** 21/07 → 03/08  
**Objetivo:** Gestor vê saldo atual, entradas/saídas do mês e DRE básico.

#### Tarefas

- [ ] **[BE]** Criar model `CategoriaFinanceira` (nome, tipo: receita/despesa, pai) para estrutura de categorias
- [ ] **[BE]** Criar model `LancamentoCaixa` (data, tipo: entrada/saída, valor, categoria, descricao, pedido_fk_opt, conta_fk_opt, conciliado)
- [ ] **[BE]** Signal: ao `Pagamento` ser aprovado → criar `LancamentoCaixa` de entrada automaticamente
- [ ] **[BE]** Signal: ao `ContaPagar` ser paga → criar `LancamentoCaixa` de saída automaticamente
- [ ] **[BE]** View `fluxo_caixa`: saldo acumulado dia a dia, filtro por período
- [ ] **[BE]** View `dre`: receita bruta, CMV, lucro bruto, despesas por categoria, lucro líquido (mensal)
- [ ] **[BE]** Admin: `LancamentoCaixaAdmin`, `CategoriasFinanceirasAdmin`
- [ ] **[BE]** Adicionar links DRE e Fluxo de Caixa no dashboard
- [ ] **[TEST]** Criar 10 lançamentos, verificar saldo acumulado correto
- [ ] **[TEST]** Validar DRE bate com soma de LucroPedido do mês

#### Critério de aceite
- Dashboard tem card de saldo atual de caixa
- Página DRE exibe receita → CMV → lucro bruto → despesas → lucro líquido por mês
- Fluxo de caixa mostra linha do tempo com saldo projetado

---

### Sprint 5 — Parcelamento e Módulo de Compras
**Período:** 04/08 → 17/08  
**Objetivo:** Registrar pagamento parcelado; registrar compra de fornecedor que entra no estoque.

#### Tarefas — Parcelamento

- [ ] **[BE]** Adicionar `parcelas` (int, default 1) em `Pagamento`
- [ ] **[BE]** Criar model `ParcelaPagamento` (pagamento, numero, vencimento, valor, status, pago_em)
- [ ] **[BE]** Ao criar `Pagamento` parcelado → gerar N `ParcelaPagamento` + N `ContaReceber`
- [ ] **[BE]** Admin: inline de parcelas no `PagamentoAdmin`
- [ ] **[BE]** Dashboard: card de "a receber próximos 30 dias"

#### Tarefas — Compras

- [ ] **[BE]** Criar app `compras`
- [ ] **[BE]** Model `PedidoCompra` (fornecedor, status: rascunho/enviado/recebido_parcial/recebido, total, previsao_entrega)
- [ ] **[BE]** Model `ItemPedidoCompra` (pedido_compra, produto, variacao_opt, quantidade, custo_unitario)
- [ ] **[BE]** Model `RecebimentoMercadoria` (pedido_compra, data, usuario, observacoes)
- [ ] **[BE]** Model `ItemRecebimento` (recebimento, item_pedido_compra, quantidade_recebida, condicao)
- [ ] **[BE]** Signal: ao confirmar recebimento → criar `MovimentoEstoque` de entrada + atualizar custo do produto
- [ ] **[BE]** Signal: ao confirmar recebimento → criar `ContaPagar` se não existir
- [ ] **[BE]** Admin completo para app compras
- [ ] **[TEST]** Criar PedidoCompra, receber parcial, verificar estoque atualizado
- [ ] **[TEST]** Receber completo, verificar ContaPagar gerada

#### Critério de aceite
- Pagamento em 3x gera 3 parcelas com vencimentos calculados automaticamente
- Recebimento de mercadoria entra no estoque com movimento rastreado
- Custo do produto atualiza ao receber compra

---

## Fase 3 — Crescimento Comercial
> Meta: ferramentas para vender mais e controle fiscal

---

### Sprint 6 — Cupons, Promoções e Relatórios
**Período:** 18/08 → 31/08  
**Objetivo:** Criar e aplicar cupons de desconto; exportar relatórios de vendas.

#### Tarefas — Cupons

- [ ] **[BE]** Criar model `Cupom` (codigo, tipo: percentual/fixo/frete_gratis, valor, uso_maximo, usos, validade, ativo, restrito_cliente_fk_opt)
- [ ] **[BE]** Model `UsoCupom` (cupom, pedido, cliente, desconto_aplicado, usado_em)
- [ ] **[BE]** Endpoint `POST /api/cupons/validar/` (recebe código + valor do pedido, retorna desconto calculado)
- [ ] **[BE]** Ao criar `Pedido` com cupom → registrar `UsoCupom` e incrementar `Cupom.usos`
- [ ] **[BE]** Admin: `CupomAdmin` com estatísticas de uso

#### Tarefas — Relatórios

- [ ] **[BE]** Endpoint exportação CSV: vendas por período (`GET /api/relatorios/vendas/?inicio=&fim=&formato=csv`)
- [ ] **[BE]** Endpoint exportação CSV: estoque atual com CMV
- [ ] **[BE]** View de Curva ABC de produtos (A: 80% receita, B: 15%, C: 5%)
- [ ] **[BE]** View análise RFM de clientes (segmentação em 5 grupos automática)
- [ ] **[BE]** Adicionar `django-import-export` para exportação no admin
- [ ] **[TEST]** Aplicar cupom percentual, verificar desconto no pedido
- [ ] **[TEST]** Exportar relatório de vendas do mês em CSV

#### Critério de aceite
- Cupom de 10% aplicado reduz `Pedido.desconto` corretamente
- Cupom com limite de uso não aceita uso acima do máximo
- Relatório de vendas exporta CSV com pedido, cliente, valor, canal, data

---

### Sprint 7 — NF-e e Notificações
**Período:** 01/09 → 14/09  
**Objetivo:** Emitir nota fiscal de pedidos; receber alertas automáticos de operação.

#### Tarefas — NF-e

- [ ] **[BE]** Adicionar campos fiscais em `Produto`: `ncm`, `cfop`, `origem`, `cst_icms`, `cst_pis`, `cst_cofins`
- [ ] **[BE]** Criar model `NotaFiscal` (pedido, numero, serie, chave_acesso, status, xml, pdf_url, emitida_em, ambiente: homologacao/producao)
- [ ] **[BE]** Integração com Focus NFe ou NFe.io (via requests): endpoint para emitir NF a partir de um `Pedido`
- [ ] **[BE]** Webhook/callback para receber status SEFAZ (autorizada/rejeitada/cancelada)
- [ ] **[BE]** Admin: botão "Emitir NF" no `PedidoAdmin`, aba NotaFiscal com download XML/PDF
- [ ] **[TEST]** Emitir NF em ambiente homologação a partir de pedido de teste

#### Tarefas — Notificações

- [ ] **[BE]** Instalar e configurar `django-apscheduler` (ou Celery Beat se já tiver Redis)
- [ ] **[BE]** Job diário: produtos com `estoque_total <= estoque_minimo` → e-mail/alerta admin
- [ ] **[BE]** Job diário: `ContaPagar` vencendo em 3 dias → e-mail responsável financeiro
- [ ] **[BE]** Job diário: pedidos em `aguardando_pagamento` há mais de 3 dias → e-mail admin
- [ ] **[BE]** Configurar transporte de e-mail (django-anymail + Resend ou SendGrid)
- [ ] **[TEST]** Forçar estoque baixo, verificar alerta disparado

#### Critério de aceite
- NF emitida em homologação retorna chave de acesso e PDF disponível
- Alerta de estoque baixo chega por e-mail com lista de produtos

---

## Fase 4 — Escala e Automação
> Meta: vender em mais canais, equipe maior com controle de acesso

---

### Sprint 8 — Permissões por Perfil e CRM
**Período:** 15/09 → 28/09  
**Objetivo:** Cada usuário acessa só o que precisa; histórico de atendimento por cliente.

#### Tarefas — Permissões

- [ ] **[BE]** Criar grupos Django: `Vendedor`, `Estoque`, `Financeiro`, `Admin`
- [ ] **[BE]** Mapear permissões por grupo (admin.py: `has_add_permission`, `has_change_permission`, etc.)
- [ ] **[BE]** `Vendedor`: acesso a Pedidos, Clientes, Produtos (leitura)
- [ ] **[BE]** `Estoque`: acesso a Movimentos, Produtos, Compras
- [ ] **[BE]** `Financeiro`: acesso a Financeiro, Relatórios, ContasReceber/Pagar
- [ ] **[BE]** Instalar `django-simple-history` em models críticos (Pedido, Produto, LancamentoCaixa)
- [ ] **[BE]** View de auditoria no admin

#### Tarefas — CRM

- [ ] **[BE]** Criar model `Atendimento` (cliente, tipo: duvida/reclamacao/elogio/troca, status, descricao, responsavel, pedido_opt)
- [ ] **[BE]** Criar model `TagCliente` (nome, cor) + M2M em `Cliente`
- [ ] **[BE]** Admin: inline de atendimentos em `ClienteAdmin`, filtro por tag
- [ ] **[BE]** Campo `avaliacao` (1–5) e `comentario_avaliacao` em `Pedido`
- [ ] **[TEST]** Usuário Vendedor tenta acessar Financeiro → bloqueado

#### Critério de aceite
- Usuário do grupo Vendedor não vê menu Financeiro no admin
- Cliente VIP (tag) visível no admin de pedidos
- Atendimento vinculado ao pedido de reclamação

---

### Sprint 9 — Integração Mercado Livre
**Período:** 29/09 → 12/10  
**Objetivo:** Pedidos do ML entram automaticamente no ERP; estoque sincroniza.

#### Tarefas

- [ ] **[BE]** Criar app `integracoes` com estrutura de adapters
- [ ] **[BE]** Model `ContaMarketplace` (plataforma: mercadolivre/shopee/amazon, seller_id, access_token, refresh_token, ativo)
- [ ] **[BE]** Model `PedidoMarketplace` (conta, pedido_externo_id, pedido_erp, status_externo, sincronizado_em)
- [ ] **[BE]** OAuth2 flow para autenticar conta ML
- [ ] **[BE]** Webhook receiver para notificações ML (`POST /integracoes/ml/webhook/`)
- [ ] **[BE]** Job de importação: buscar pedidos novos do ML → criar `Pedido` no ERP via adapter
- [ ] **[BE]** Job de sincronização de estoque: ao mover estoque no ERP → atualizar quantidade no ML via API
- [ ] **[BE]** Mapeamento de `Produto.site_id` para `item_id` do ML por variação
- [ ] **[TEST]** Simular webhook de pedido ML, verificar pedido criado no ERP
- [ ] **[TEST]** Atualizar estoque no ERP, verificar que ML recebe a atualização

#### Critério de aceite
- Novo pedido no ML aparece no ERP em menos de 5 minutos
- Estoque zerado no ERP dispara atualização para ML (produto pausado)
- Pedido ML tem `canal = marketplace_ml` distinguível no dashboard

---

### Sprint 10 — Interface Operacional (PDV e Expedição)
**Período:** 13/10 → 26/10  
**Objetivo:** Telas dedicadas para vendas presenciais/WhatsApp e expedição de pedidos.

#### Tarefas

- [ ] **[FE]** Instalar HTMX + Alpine.js no projeto Django
- [ ] **[FE]** Tela de PDV: busca de cliente por nome/WhatsApp, busca de produto por SKU/nome, grade de variações clicável, carrinho com desconto e forma de pagamento
- [ ] **[FE]** Tela de Expedição: lista de pedidos com status `separacao`/`enviado`, filtro por data, botão "Marcar como enviado" com input de código de rastreio
- [ ] **[FE]** Tela de Estoque rápido: entrada de mercadoria por SKU + quantidade (sem precisar abrir admin)
- [ ] **[BE]** Endpoints HTMX: busca de produto, validação de cupom, submit de pedido
- [ ] **[TEST]** Criar pedido pelo PDV para cliente existente com variação de produto
- [ ] **[TEST]** Marcar lote de pedidos como enviados na tela de expedição

#### Critério de aceite
- Vendedor cria pedido completo no PDV em menos de 2 minutos
- Expedição lista todos os pedidos a enviar do dia com 1 clique para confirmar envio
- Telas funcionam em tablet (touch-friendly)

---

## Resumo das Sprints

| Sprint | Período | Foco | Prioridade |
|--------|---------|------|-----------|
| 1 | 09/06 → 22/06 | Variações de produto (grade) | 🔴 Crítico |
| 2 | 23/06 → 06/07 | Endereços + Rastreamento de envio | 🔴 Crítico |
| 3 | 07/07 → 20/07 | Devolução e Troca | 🔴 Crítico |
| 4 | 21/07 → 03/08 | Fluxo de Caixa e DRE | 🟡 Importante |
| 5 | 04/08 → 17/08 | Parcelamento + Módulo de Compras | 🟡 Importante |
| 6 | 18/08 → 31/08 | Cupons + Relatórios | 🟡 Importante |
| 7 | 01/09 → 14/09 | NF-e + Notificações | 🟡 Importante |
| 8 | 15/09 → 28/09 | Permissões por perfil + CRM | 🟢 Evolução |
| 9 | 29/09 → 12/10 | Integração Mercado Livre | 🟢 Evolução |
| 10 | 13/10 → 26/10 | Interface Operacional (PDV + Expedição) | 🟢 Evolução |

**Duração total estimada: ~20 semanas (5 meses)**

---

## Notas

- Cada sprint assume ~3–4 dias úteis de trabalho assistido (Claude Code)
- Sprints 1–3 são dependentes: fazer nessa ordem pois variações impactam pedidos e devoluções
- Sprint 7 (NF-e) requer conta em Focus NFe / NFe.io e certificado digital A1 da empresa
- Sprint 9 (ML) requer conta de desenvolvedor no Mercado Livre
- Sprints podem ser paralelizadas por desenvolvedor humano (ex: Sprint 6 backend + Sprint 5 testes)
