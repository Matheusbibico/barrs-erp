# Barrs ERP — Roadmap Revisado

> **Princípio:** o sistema deve ajudar a vender mais, gastar menos tempo e ter controle real. Tudo que não serve a esses três objetivos é removido.
>
> Versão: revisão crítica de 2026-06-10 | Contexto: loja de semijoias em fase inicial, 1–3 pessoas na operação.

---

## O que foi auditado

| Módulo/Funcionalidade | Decisão | Motivo |
|---|---|---|
| Produto + VariacaoProduto | ✅ Manter | Essencial para semijoias com cor/tamanho |
| FotoProduto (model) | ❌ Remover | ERP não é vitrine. Campo `imagem_url` simples resolve |
| Categoria.slug | ⚠️ Simplificar | Slug é para URL pública — desnecessário no ERP interno |
| estoque_reservado no Produto | ⚠️ Avaliar | Nunca é incrementado/decrementado automaticamente — campo morto |
| MovimentoEstoque | ✅ Manter | Rastreamento de entrada/saída — fundamental |
| Cliente + histórico automático | ✅ Manter | Bom, atualiza total_gasto/qtd_pedidos via signal |
| EnderecoCliente | ⚠️ Manter com cautela | Útil para importação do site, overhead para pedidos manuais |
| Pedido + ItemPedido + Pagamento | ✅ Manter | Núcleo do sistema |
| STATUS `reservado` e `separacao` no Pedido | ❌ Remover | Status intermediários raramente usados na prática |
| LucroPedido (model separado) | ⚠️ Simplificar | Redundante — lucro é `receita - custo`, calculável on-demand |
| EventoRastreio (model) | ❌ Remover | Overhead alto, ninguém vai cadastrar eventos manualmente |
| ParcelaPagamento | ❌ Remover | Parcelamento no cartão fica com a maquininha/gateway. ERP não precisa disso |
| Devolucao + ItemDevolucao | ✅ Manter | Semijoias têm trocas e devoluções frequentes |
| Webhook importação do site | ✅ Manter | Já funciona, muito valioso |
| ContaReceber | ⚠️ Simplificar | Redundante com LancamentoCaixa. Manter apenas para parcelas pendentes do site |
| ContaPagar | ✅ Manter | Necessário para despesas fixas mensais |
| CategoriaFinanceira hierárquica (pai/filho) | ❌ Remover hierarquia | Categorias simples são suficientes. Remover campo `pai` |
| LancamentoCaixa | ✅ Manter | Core do controle financeiro |
| DRE + Fluxo de Caixa (endpoints API) | ✅ Manter | Simples e úteis |
| App `compras` (4 models, fluxo em 4 etapas) | ❌ Substituir | Excesso para loja pequena. Substituir por "Entrada de Estoque" simples |
| Sprint 6 — Cupons | ❌ Remover do roadmap | Cupons existem no site. ERP não duplica isso |
| Sprint 6 — Curva ABC + RFM | ⏳ Fase 3 | Análise para quando a loja tiver volume. Prematuro agora |
| Sprint 7 — NF-e | ⏳ Fase 3 | Complexidade enorme, requer certificado digital A1. Usar serviço dedicado |
| Sprint 7 — Notificações por e-mail | ⚠️ Fase 2 simplificada | Alertas no dashboard são suficientes. E-mail pode esperar |
| Sprint 8 — CRM (Atendimentos, TagCliente) | ⏳ Fase 3 | O campo `observacoes` já resolve para 1–3 operadores |
| Sprint 8 — django-simple-history | ⏳ Fase 3 | Auditoria completa é prematura agora |
| Sprint 9 — Integração Mercado Livre | ⏳ Fase 3 | Só quando a loja vender no ML |
| Sprint 10 — PDV completo | ⚠️ Fase 2 | Necessário mas o admin já resolve por enquanto |

---

## Fase 1 — Operação Essencial (agora)

> **Meta:** loja consegue operar o dia a dia sem gambiarras e sem abrir planilha.

### O que já existe e está pronto ✅

- Cadastro de produtos com variações (cor/tamanho) e controle de estoque por variação
- Cadastro de clientes com histórico automático (total gasto, qtd pedidos)
- Pedidos com itens, pagamentos, status e observações
- Controle de devoluções com reversão de estoque
- Webhook que importa pedidos do site automaticamente
- Movimentos de estoque rastreados
- Conttas a Pagar e Contas a Receber
- Fluxo de caixa + DRE por mês
- Dashboard com KPIs principais

### O que precisa ser feito na Fase 1

**F1-1 — Limpeza e simplificação** (1–2 dias)
- Remover `ParcelaPagamento` do fluxo operacional (manter model mas não exibir como processo obrigatório)
- Remover `EventoRastreio` da sidebar (model existe, mas não tem valor prático)
- Remover `LucroPedido` como model separado → transformar em propriedade calculada do Pedido
- Remover `FotoProduto` do admin principal → substituir por campo `imagem_url` opcional
- Remover campo `pai` de `CategoriaFinanceira`
- Simplificar sidebar: retirar links que ninguém usa
- Simplificar status do Pedido: remover `reservado` e `separacao`

**F1-2 — Entrada rápida de estoque** (1 dia)
- Substituir o app `compras` por uma tela simples:
  - Seleciona produto/variação
  - Informa quantidade + custo unitário + fornecedor
  - Cria `MovimentoEstoque` de entrada e atualiza custo
- Remover `PedidoCompra`, `ItemPedidoCompra`, `RecebimentoMercadoria`, `ItemRecebimento`

**F1-3 — Campo `estoque_minimo` no Produto** (meio dia)
- Adicionar `estoque_minimo` (int, default=0) em Produto e VariacaoProduto
- Dashboard já mostra alerta de estoque baixo — só precisa do campo de referência

**F1-4 — Exportação de vendas em CSV** (meio dia)
- Endpoint simples: `/api/relatorios/vendas.csv?inicio=&fim=`
- Colunas: data, pedido, cliente, canal, total, status
- Sem dependência de biblioteca extra — usa `csv` nativo do Python

---

## Fase 2 — Produtividade (próximos 2 meses)

> **Meta:** menos tempo operando o sistema, mais visibilidade do negócio.

**F2-1 — Meta mensal no Dashboard**
- Campo `meta_mensal` configurável (simples, via admin ou settings)
- Card no dashboard: R$ atingido / R$ meta / % da meta

**F2-2 — Filtros rápidos de pedidos no Dashboard**
- Botões diretos: "Ver pedidos a enviar hoje", "Ver aguardando pagamento", "Ver pendentes"
- Evita ter que abrir o admin de Pedidos e filtrar manualmente

**F2-3 — Integração Mercado Pago (webhook)**
- Receber notificação de pagamento aprovado → mudar status do pedido automaticamente
- Sem complexidade de OAuth: só receber webhook e processar

**F2-4 — Integração Melhor Envio**
- Gerar etiqueta de envio a partir de um Pedido
- Copiar código de rastreio automaticamente de volta ao pedido
- Enorme economia de tempo no dia a dia

**F2-5 — Alerta de estoque baixo por e-mail**
- Simples: um endpoint ou job semanal que envia lista de produtos abaixo do mínimo
- Não precisa de Celery — pode ser um `management command` chamado por cron

---

## Fase 3 — Escala (quando a loja crescer)

> Apenas quando o volume justificar a complexidade.

- **Exportações avançadas**: Curva ABC, análise RFM de clientes
- **NF-e**: integração com Focus NFe / NFe.io (requer certificado digital A1)
- **Integração Mercado Livre**: pedidos e sincronização de estoque
- **PDV**: tela dedicada para venda presencial/WhatsApp sem abrir o admin
- **Permissões por perfil**: grupos Vendedor/Estoque/Financeiro
- **CRM básico**: tags de cliente, histórico de atendimentos
- **Auditoria**: django-simple-history nos models críticos
- **Múltiplos canais de venda**: Shopee, Amazon

---

## Arquitetura simplificada dos módulos

```
Dashboard
├── KPIs (faturamento, lucro, saldo, pedidos pendentes, meta)
├── Alertas (estoque baixo, contas a vencer)
└── Gráfico de vendas 30 dias

Pedidos
├── Lista com filtros (status, canal, data)
├── Detalhe (itens, pagamento, endereço, rastreio)
└── Devoluções

Produtos
├── Catálogo com variações
├── Estoque por variação
└── Fornecedores

Estoque
├── Movimentos (entrada/saída/ajuste)
└── Entrada Rápida (nova compra de fornecedor)

Clientes
├── Cadastro + histórico automático
└── Endereços

Financeiro
├── Lançamentos de Caixa (entradas e saídas)
├── Contas a Pagar
├── Fluxo de Caixa
└── DRE mensal
```

**Removidos da arquitetura:**
- App `compras` (4 models → 1 tela simples)
- `LucroPedido` como model (→ propriedade calculada)
- `EventoRastreio` como model ativo
- `ParcelaPagamento` como processo (parcelamento no ERP é overhead)
- `FotoProduto` como model (→ campo URL simples)

---

## Princípios para o desenvolvimento futuro

1. **Antes de criar um model novo, pergunte:** uma coluna extra no model existente resolve?
2. **Antes de criar um fluxo de N etapas, pergunte:** uma tela com um formulário resolve?
3. **Antes de automatizar, pergunte:** o operador faria isso manualmente em menos de 30 segundos?
4. **Nenhuma funcionalidade é implementada porque "parece profissional"**
5. **O admin Django é o frontend — não construir telas custom até ter tráfego real**
