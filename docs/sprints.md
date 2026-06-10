# Barrs ERP — Sprints de Desenvolvimento

> **Revisão crítica:** 2026-06-10
> Contexto: loja de semijoias em fase inicial, 1–3 operadores.
> Princípio: só entra no sprint o que gera valor real no dia a dia da loja.

---

## Histórico de Sprints Concluídas

| Sprint | Entregue | Status |
|--------|----------|--------|
| S1 | Variações de produto (cor/tamanho), estoque por variação, webhook do site | ✅ |
| S2 | Endereços estruturados de cliente, rastreio no pedido, lookup de CEP | ✅ |
| S3 | Devolução e troca com reversão automática de estoque | ✅ |
| S4 | Fluxo de caixa, DRE, lançamentos automáticos, categorias financeiras | ✅ |
| S5 | Parcelamento de pagamentos, módulo de compras com recebimento | ✅ |
| S6 | Limpeza do sistema — remoção de modelos e campos desnecessários | ✅ |
| S7 | `estoque_minimo` em Produto/Variação, exportação CSV de vendas e estoque | ✅ |
| S8 | Meta mensal com barra de progresso, atalhos rápidos no dashboard | ✅ |
| S9 | Webhook Mercado Pago — confirma pagamento automaticamente no ERP | ✅ |

---

## Manuais de Uso

---

### Sprint 1 — Variações de Produto e Webhook do Site

#### O que mudou
- Produtos agora têm **variações** (cor + tamanho), cada uma com estoque e custo próprios
- Pedidos do site entram automaticamente no ERP via webhook
- Estoque é decrementado por variação quando um pedido é importado

#### Como usar

**Cadastrar produto com variações**
1. Admin → Produtos → adicionar produto
2. Rolar até a seção "Variações" e adicionar uma linha por variação (ex: Dourado / P, Dourado / M, Rosê / Único)
3. Cada variação tem seu próprio SKU, custo, preço de venda e estoque

**Webhook de importação do site**
- O site envia um `POST /webhook/nova-venda/` com o `pedido_id` quando uma venda ocorre
- O ERP busca o pedido no banco de dados do site e cria o `Pedido` + `ItemPedido` automaticamente
- Variável de ambiente necessária: `WEBHOOK_TOKEN` (deve ser igual no site e no ERP)

---

### Sprint 2 — Endereços e Rastreio

#### O que mudou
- Clientes têm endereços estruturados (CEP, rua, número, cidade, UF) em vez de texto livre
- Pedidos têm campo de código de rastreio, transportadora e URL de rastreio
- Lookup de CEP automático via ViaCEP ao cadastrar endereço

#### Como usar

**Cadastrar endereço de cliente**
1. Admin → Clientes → abrir cliente → seção "Endereços"
2. Informar o CEP — os campos de rua, cidade e UF preenchem automaticamente
3. O endereço é vinculado ao pedido no momento da criação

**Registrar rastreio de um pedido**
1. Admin → Pedidos → abrir pedido
2. Preencher "Código de Rastreio", "Transportadora" e "URL de Rastreio"
3. Mudar status para **Enviado**

---

### Sprint 3 — Devoluções e Trocas

#### O que mudou
- Novo modelo `Devolucao` para registrar solicitações de troca/devolução
- Ao aprovar uma devolução, o estoque do produto é revertido automaticamente
- Pedido muda para status "Troca Pendente" ou "Devolvido"

#### Como usar

**Registrar uma devolução**
1. Admin → Devoluções → adicionar
2. Vincular ao pedido original, informar o motivo e os itens devolvidos com quantidade
3. Ao mudar o status para **Aprovada**, o estoque é restaurado automaticamente
4. Ao mudar para **Concluída**, o pedido original muda para "Devolvido"

---

### Sprint 4 — Financeiro (Fluxo de Caixa e DRE)

#### O que mudou
- Lançamentos de caixa criados **automaticamente** quando um pagamento é aprovado ou uma conta é paga
- DRE e Fluxo de Caixa disponíveis via API
- Categorias financeiras para classificar receitas e despesas
- Contas a Pagar e Contas a Receber integradas ao caixa

#### Como usar

**Configurar categorias (fazer uma vez)**

Admin → Categorias Financeiras → criar:

| Nome | Tipo |
|------|------|
| Vendas | Receita |
| Despesas Operacionais | Despesa |
| Aluguel | Despesa |
| Embalagem | Despesa |
| Frete Saída | Despesa |
| Marketing | Despesa |
| Compras | Despesa |

**Lançamentos automáticos**
- Pagamento de pedido aprovado → entrada na categoria "Vendas" criada automaticamente
- ContaPagar marcada como "pago" → saída criada automaticamente

**Lançamento manual**
Admin → Lançamentos de Caixa → adicionar → informar data, tipo (entrada/saída), valor, categoria e descrição.

**Consultar Fluxo de Caixa**
```
GET /api/financeiro/fluxo-caixa/?inicio=2026-06-01&fim=2026-06-30
```
Retorna saldo acumulado dia a dia.

**Consultar DRE**
```
GET /api/financeiro/dre/?ano=2026&mes=6
```
Retorna: receita bruta → CMV → lucro bruto → despesas → lucro líquido.

**Rotina mensal**
```
1º dia do mês  → cadastrar despesas fixas como ContaPagar (aluguel, etc.)
Dia a dia      → vendas entram automaticamente pelo webhook
Ao pagar conta → marcar ContaPagar como "pago"
Fim do mês     → consultar DRE
```

---

### Sprint 5 — Compras de Fornecedor

#### O que mudou
- Módulo de compras para registrar entrada de mercadoria com custo
- Ao confirmar recebimento: estoque aumenta, custo do produto atualiza, ContaPagar criada automaticamente

#### Como usar

**Registrar compra de fornecedor**
1. Admin → Pedidos de Compra → criar com itens e custo unitário
2. Mudar status para **Enviado ao Fornecedor**
3. Mercadoria chegou → criar Recebimento → informar quantidades recebidas → marcar **Confirmado**
4. Resultado automático: estoque atualizado + custo unitário revisado + ContaPagar criada para o fornecedor

**Pagar o fornecedor**
Admin → Contas a Pagar → localizar a conta do recebimento → marcar como **Pago** → lançamento de saída criado automaticamente.

---

### Sprint 6 — Limpeza do Sistema

#### O que mudou
O sistema foi simplificado para eliminar complexidade que não agrega valor a uma loja pequena:

| O que foi removido/simplificado | Por quê |
|---------------------------------|---------|
| `EventoRastreio` da sidebar | Ninguém cadastra eventos manualmente |
| `ParcelaPagamento` como processo | Parcelamento no cartão fica com a maquininha |
| `LucroPedido` como model separado | Lucro é calculável: `receita − custo dos itens` |
| `FotoProduto` como model | ERP não é vitrine; campo `imagem_url` resolve |
| Campo `pai` em `CategoriaFinanceira` | Hierarquia de categorias era overhead desnecessário |
| Status `reservado` e `separacao` no Pedido | Nunca eram usados na prática |
| Campo `estoque_reservado` em Produto | Nunca era incrementado automaticamente |
| Campo `slug` em Categoria | Slug é para URL pública, sem uso interno |
| App `compras` com 4 models e fluxo em 4 etapas | Substituído por Entrada de Estoque simples |

**Novo:** campo `imagem_url` (URL da foto) direto no produto.

**Novo:** `Pedido.lucro_calculado` — propriedade que calcula o lucro do pedido on-demand, sem model separado.

**Sidebar** agora tem no máximo 10 itens visíveis.

#### Como usar
Nenhuma ação necessária. As simplificações são transparentes — o sistema continua funcionando normalmente, só com menos campos e menos passos.

---

### Sprint 7 — Estoque Mínimo e Exportação CSV

#### O que mudou
- Campo `estoque_minimo` em `Produto` e `VariacaoProduto`
- Dashboard alerta para produtos com estoque **abaixo do mínimo definido** (não mais fixo em ≤ 5)
- Dashboard separa **zerados** de **abaixo do mínimo** em seções distintas
- Endpoints para exportar vendas e estoque em CSV compatível com Excel/Google Sheets

#### Como usar

**Configurar estoque mínimo de um produto**
1. Admin → Produtos → abrir o produto
2. Seção "Estoque" → preencher o campo **Estoque Mínimo** (ex: `3`)
3. Quando `estoque_total ≤ estoque_minimo`, o produto aparece no alerta do dashboard

Para variações individuais, o campo também está disponível na tabela de variações dentro do produto.

**Dashboard — alertas de estoque**
- **Zerados** (em vermelho): produtos com estoque = 0 ou negativo
- **Abaixo do mínimo** (em laranja): produtos com estoque > 0 mas ≤ ao mínimo configurado
- Produtos sem `estoque_minimo` definido (= 0) não aparecem no alerta de "abaixo do mínimo"

**Exportar CSV de vendas**
```
/relatorios/vendas.csv
/relatorios/vendas.csv?inicio=2026-06-01&fim=2026-06-30
```
Colunas: Data, Pedido, Cliente, Canal, Status, Total (R$), Itens.
O link "Exportar CSV → Vendas" no dashboard já abre sem filtro de período.

**Exportar CSV de estoque**
```
/relatorios/estoque.csv
```
Colunas: SKU, Produto, Variação, Estoque Atual, Estoque Mínimo, Custo (R$), Preço Venda (R$).
Uma linha por variação. Produtos sem variação aparecem como uma linha com a variação em branco.

> Ambos os arquivos têm BOM UTF-8 — abrem corretamente no Excel sem precisar de configuração de encoding.

---

### Sprint 8 — Meta Mensal e Atalhos no Dashboard

#### O que mudou
- Model `MetaMensal` para registrar a meta de faturamento de cada mês
- Dashboard exibe barra de progresso da meta do mês atual (só aparece se a meta estiver cadastrada)
- Três botões de atalho rápido no topo do dashboard, cada um com contagem em tempo real

#### Como usar

**Cadastrar a meta do mês**
1. Admin → Financeiro → Metas Mensais → adicionar
2. Informar Ano, Mês (1–12) e Valor da Meta em R$
3. O dashboard passa a exibir a barra de progresso automaticamente

**Barra de progresso da meta**
- 🟢 Verde: ≥ 100% da meta atingida
- 🟡 Amarelo: entre 70% e 99%
- 🔴 Vermelho: abaixo de 70%
- Exibe: percentual + "R$ realizado / R$ meta"

**Botões de atalho**
| Botão | O que mostra | Link |
|-------|-------------|------|
| Aguardando Pagamento | Pedidos com status "Aguardando Pagamento" | Lista de pedidos filtrada |
| A Enviar | Pedidos pagos sem código de rastreio | Lista de pedidos filtrada |
| Atrasados | Pedidos pagos há +3 dias sem rastreio | Lista de pedidos filtrada com filtro "Atrasados" |

Clicar em qualquer botão abre direto a lista de pedidos já filtrada — sem precisar navegar e filtrar manualmente.

**Filtro "Atrasados" no admin de Pedidos**
Disponível na barra lateral do admin de Pedidos → filtro "Envio em atraso" → "Pagos há +3 dias sem rastreio".

---

### Sprint 9 — Integração Mercado Pago

#### O que mudou
- Endpoint `POST /webhook/mercadopago/` recebe notificações de pagamento do Mercado Pago
- Quando um pagamento é aprovado: o pedido muda para "Pago", um `Pagamento` é criado e o `LancamentoCaixa` de entrada é gerado automaticamente
- A assinatura do webhook é validada via HMAC-SHA256 — requisições não autorizadas são rejeitadas

#### Como funciona (fluxo)
```
Cliente paga no site via MP
       ↓
MP envia POST /webhook/mercadopago/ com o payment_id
       ↓
ERP valida a assinatura (x-signature)
       ↓
ERP busca detalhes do pagamento na API do MP
       ↓
Localiza o Pedido pelo external_reference (= site_id)
       ↓
Pedido → status "Pago"
Pagamento criado com método e valor
LancamentoCaixa de entrada criado automaticamente
```

#### Como configurar

**Passo 1 — Variáveis de ambiente no Railway**

Railway → seu serviço → Variables → adicionar:

```
MP_ACCESS_TOKEN=APP_USR-xxxxxxxxxxxxxxxxxxxx
MP_WEBHOOK_SECRET=chave-secreta-gerada-no-dashboard-mp
```

**Passo 2 — Obter o Access Token**
- MP Dashboard → "Suas integrações" → selecionar app → "Credenciais de produção" → copiar **Access Token**

**Passo 3 — Registrar o webhook no Mercado Pago**
- MP Dashboard → "Suas integrações" → "Webhooks" → "Adicionar"
- URL: `https://seu-app.railway.app/webhook/mercadopago/`
- Eventos: marcar **Pagamentos** (`payment`)
- Copiar a **Chave secreta** gerada e colocar em `MP_WEBHOOK_SECRET`

**Passo 4 — Confirmar o `external_reference` no site**
O checkout do site precisa enviar `external_reference` igual ao ID do pedido no site. Esse valor é o que o ERP usa para localizar o pedido correspondente (campo `site_id` no model `Pedido`).

> **Sem `external_reference`**, o ERP recebe o webhook mas não consegue vincular ao pedido — o pagamento não é confirmado automaticamente.

---

## Próximas Sprints

### Sprint 10 — Integração Melhor Envio
**Objetivo:** gerar etiqueta de envio diretamente do pedido, sem copiar dados manualmente.
**Prioridade:** 🟡 Média | **Complexidade:** Média

- [ ] Integração com API Melhor Envio (token fixo)
- [ ] Botão "Gerar Etiqueta" no PedidoAdmin
- [ ] Ao confirmar: `codigo_rastreio` e `url_rastreio` salvos automaticamente no pedido
- [ ] Status muda para `enviado` automaticamente

**Critério de aceite:** operador gera etiqueta em 2 cliques sem sair do ERP.

---

### Sprint 11 — PDV (Ponto de Venda)
**Objetivo:** tela dedicada para criar pedidos por WhatsApp/presencial.
**Prioridade:** 🟢 Baixa (o admin já funciona) | **Complexidade:** Alta

---

### Sprint 12 — Integração Mercado Livre
**Objetivo:** pedidos do ML entram automaticamente no ERP.
**Prioridade:** 🟢 Baixa (só quando a loja vender no ML) | **Complexidade:** Alta

---

### Sprint 13 — NF-e
**Objetivo:** emitir nota fiscal diretamente do pedido.
**Prioridade:** 🟢 Baixa (requer certificado A1) | **Complexidade:** Muito Alta

---

### Sprint 14 — Permissões e CRM Básico
**Objetivo:** múltiplos usuários com acesso controlado.
**Prioridade:** 🟢 Baixa (irrelevante com 1–3 operadores) | **Complexidade:** Média

---

### Sprint 15 — Relatórios Avançados
**Objetivo:** Curva ABC de produtos e segmentação RFM de clientes.
**Prioridade:** 🟢 Baixa (sem volume, os dados não são representativos) | **Complexidade:** Média

---

## Resumo Geral

| Sprint | Foco | Fase | Status |
|--------|------|------|--------|
| 1 | Variações de produto + webhook do site | — | ✅ |
| 2 | Endereços estruturados + rastreio | — | ✅ |
| 3 | Devoluções e trocas | — | ✅ |
| 4 | Financeiro (caixa, DRE, lançamentos) | — | ✅ |
| 5 | Compras de fornecedor | — | ✅ |
| 6 | Limpeza e simplificação | 1 | ✅ |
| 7 | Estoque mínimo + exportação CSV | 1 | ✅ |
| 8 | Meta mensal + atalhos no dashboard | 2 | ✅ |
| 9 | Integração Mercado Pago | 2 | ✅ |
| 10 | Integração Melhor Envio | 2 | 🔲 |
| 11 | PDV | 3 | 🔲 |
| 12 | Integração Mercado Livre | 3 | 🔲 |
| 13 | NF-e | 3 | 🔲 |
| 14 | Permissões + CRM básico | 3 | 🔲 |
| 15 | Relatórios avançados (ABC, RFM) | 3 | 🔲 |
