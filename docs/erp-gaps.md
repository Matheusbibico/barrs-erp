# Barrs ERP — Análise de Gaps para ERP Completo

> Gerado em: 2026-06-08  
> Base: análise dos models, views e APIs existentes

---

## O que já existe

| Módulo | O que está implementado |
|--------|------------------------|
| **Produtos** | SKU, categorias, fornecedores, fotos, custo, preço de venda, margem, estoque total/reservado |
| **Pedidos** | Múltiplos canais (site/whatsapp/instagram/presencial/link), fluxo completo de status, pagamento, lucro por pedido |
| **Clientes** | Dados básicos, histórico (total gasto, qtd pedidos, ticket médio) |
| **Estoque** | Movimentos rastreados (entrada/saída/ajuste/perda/troca/reserva) com saldo anterior/posterior |
| **Financeiro** | Contas a receber (vinculada ao pedido), contas a pagar (vinculada ao fornecedor) |
| **Dashboard** | 6 KPIs, gráfico dual-line 30 dias, top 5 produtos, distribuição por canal |
| **Webhook** | Importação automática de pedidos do site e-commerce externo |
| **API REST** | CRUD completo em todos os módulos via Django REST Framework |
| **Deploy** | Railway com PostgreSQL, Gunicorn, WhiteNoise, migrations automáticas |

---

## Gaps por módulo

### 🔴 Crítico — sem isso a operação trava

#### 1. Variações de produto (Grade)
O maior gap para loja de moda. Atualmente `Produto` é uma entidade plana — não há suporte a cor/tamanho.

**O que falta:**
- Model `VariacaoProduto` (produto_pai, cor, tamanho, sku_variacao, custo, preco_venda)
- Estoque individual por variação (hoje é só `estoque_total` no produto)
- `ItemPedido` apontar para variação, não só para produto
- Admin com inline de grade (matriz cor × tamanho)
- Importação do webhook mapeando variações do site

---

#### 2. Endereços de entrega dos clientes
`Cliente` tem apenas `cidade` e `estado` como campos de texto livre. Insuficiente para gerar etiqueta ou NF-e.

**O que falta:**
- Model `EnderecoCliente` (cep, logradouro, numero, complemento, bairro, cidade, estado, principal)
- Múltiplos endereços por cliente
- `Pedido.endereco_entrega` hoje é `TextField` — precisa ser FK para `EnderecoCliente`
- Integração com ViaCEP para autopreenchimento

---

#### 3. Rastreamento de envio
`Pedido` não tem nenhum campo de logística após envio.

**O que falta:**
- Campos: `transportadora`, `codigo_rastreio`, `url_rastreio`, `previsao_entrega`
- Model `EventoRastreio` (pedido, data, status, descricao) para histórico
- Integração opcional com Correios / Jadlog / Shopee Envios

---

#### 4. Devolução e Troca
Nenhum fluxo existe para recusar itens, fazer estorno ou registrar reentrada de mercadoria.

**O que falta:**
- Model `Devolucao` (pedido, motivo, tipo: troca/reembolso, status)
- `ItemDevolucao` (devolucao, item_pedido, quantidade, condicao: ok/defeito)
- Signal que ao aprovar devolução: reverte estoque + gera estorno financeiro
- Status `devolvido` no `Pedido`

---

### 🟡 Importante — ERP incompleto sem eles

#### 5. Módulo de Compras
Estoque só entra manualmente hoje (movimento de ajuste). Não há fluxo de compra de fornecedor.

**O que falta:**
- App `compras` com models: `PedidoCompra`, `ItemPedidoCompra`, `RecebimentoMercadoria`
- Status: rascunho → enviado ao fornecedor → recebido parcial → recebido total
- Ao receber: gera `MovimentoEstoque` de entrada + vincula `ContaPagar`
- Histórico de compras por fornecedor

---

#### 6. Fluxo de Caixa e DRE
`ContaReceber` e `ContaPagar` existem mas são entidades isoladas. Falta visão consolidada.

**O que falta:**
- Model `LancamentoCaixa` (data, tipo: entrada/saída, valor, categoria, descricao, conciliado)
- View de fluxo de caixa: saldo atual, entradas/saídas por período, projeção
- DRE mensal: receita bruta → CMV → lucro bruto → despesas → lucro líquido
- Conciliação: vincular `LancamentoCaixa` ao `Pagamento` do pedido
- Categorias de despesa estruturadas (não é só um `CharField` livre como hoje)

---

#### 7. Cupons e Promoções
`Pedido` tem campo `desconto` mas é valor livre — não há entidade de cupom ou regra de desconto.

**O que falta:**
- Model `Cupom` (codigo, tipo: percentual/fixo, valor, uso_maximo, validade, ativo)
- Regras: desconto por categoria, por quantidade mínima, por cliente específico, frete grátis
- Rastreio de uso: `UsoCupom` (cupom, pedido, cliente, desconto_aplicado)
- Validação ao criar pedido (via API ou admin)

---

#### 8. Parcelamento
`Pagamento` é um registro único por pedido. Não suporta cartão 3x, carnê ou boleto parcelado.

**O que falta:**
- `Pagamento` ganhar campo `parcelas` e `valor_parcela`
- Model `ParcelaPagamento` (pagamento, numero, vencimento, valor, status, pago_em)
- Ao criar parcelas: gerar entradas em `ContaReceber` correspondentes
- Dashboard mostrar inadimplência

---

#### 9. Nota Fiscal (NF-e / NFC-e)
Zero suporte fiscal. Para operação formal é obrigatório.

**Opção recomendada:** integração com serviço externo (Focus NFe, NFe.io, Bling).

**O que falta:**
- Model `NotaFiscal` (pedido, numero, serie, chave_acesso, status, xml, pdf_url)
- Campos fiscais no `Produto`: NCM, CFOP, origem, CST
- Webhook/callback para receber status da SEFAZ (autorizada/rejeitada/cancelada)
- Botão no admin para emitir NF diretamente do pedido

---

### 🟢 Evolução — torna o produto mais robusto

#### 10. CRM e Pós-venda
`Cliente` hoje não tem vínculo com interações após a compra.

**O que falta:**
- Model `Atendimento` (cliente, tipo: reclamação/elogio/dúvida/troca, status, descricao)
- Avaliação de pedido (nota 1–5, comentário)
- Tags de cliente (VIP, inadimplente, atacado, influencer)
- Histórico de comunicações (WhatsApp enviados)

---

#### 11. Relatórios Gerenciais
Dashboard existe mas relatórios exportáveis e análises profundas não.

**O que falta:**
- DRE por mês/trimestre/ano (exportável em CSV/Excel)
- Vendas por período / produto / categoria / vendedor / canal
- Análise RFM de clientes (Recência, Frequência, Monetário — segmentação automática)
- CMV e giro de estoque por produto
- Relatório de margem por produto/categoria
- Curva ABC de produtos

---

#### 12. Controle de Usuários e Permissões
Hoje qualquer `is_staff=True` acessa tudo no admin.

**O que falta:**
- Grupos de perfil: `Vendedor` (pedidos), `Estoque` (movimentos), `Financeiro` (contas), `Admin` (tudo)
- Permissões por módulo no Django Admin
- Log de ações auditável (`django-simple-history` ou `LogEntry`)
- Usuário vendedor vinculado ao pedido (já existe `usuario` no Pedido, mas sem restrição)

---

#### 13. Notificações e Alertas
Nenhum sistema de alerta proativo existe.

**O que falta:**
- Alertas de estoque: produto zerado ou abaixo do mínimo configurável
- Alerta de pedido parado há X dias sem atualização
- Contas a vencer em N dias
- Canal: e-mail (django-anymail + SendGrid/Resend) ou WhatsApp (Z-API / Evolution API)
- Tarefa agendada (Celery Beat ou django-apscheduler) para verificações diárias

---

#### 14. Integrações de Marketplace
Hoje só existe webhook para o site próprio.

**O que falta:**
- Mercado Livre: sync de produtos, recebimento de pedidos, atualização de estoque
- Shopee: idem
- Amazon: idem
- Padrão recomendado: app `integracoes` com adapter por marketplace + fila de sincronização
- Rastreio de qual pedido veio de qual marketplace (campo `origem_marketplace`)

---

#### 15. Interface Operacional Própria (Frontend)
Toda operação é pelo Django Admin. Funciona, mas tem limites de UX para equipes maiores.

**O que falta:**
- Tela de PDV / criação rápida de pedido (para vendas presenciais/WhatsApp)
- Painel de separação e expedição (lista de pedidos a enviar, impressão de etiqueta)
- App mobile básico (ou PWA) para consulta de estoque e criação de pedido
- Tecnologia sugerida: HTMX + Alpine.js (sem JS framework pesado, integrado ao Django)

---

## Roadmap sugerido

```
Fase 1 — Operação básica completa
├── Variações de produto (grade cor/tamanho)
├── Endereços estruturados de clientes
├── Rastreamento de envio
└── Devolução / Troca

Fase 2 — Financeiro real
├── Fluxo de caixa e DRE
├── Parcelamento
└── Módulo de Compras

Fase 3 — Crescimento comercial
├── Cupons e promoções
├── NF-e (via serviço externo)
├── Relatórios gerenciais
└── Notificações e alertas

Fase 4 — Escala e automação
├── Marketplaces (ML, Shopee)
├── CRM / Pós-venda
├── Permissões por perfil
└── Interface operacional própria
```

---

## Resumo numérico

| Prioridade | Qtd de gaps | Impacto |
|------------|------------|---------|
| 🔴 Crítico | 4 | Operação trava sem eles |
| 🟡 Importante | 5 | ERP incompleto sem eles |
| 🟢 Evolução | 6 | Robustez e escala |
| **Total** | **15** | — |

A base do projeto é sólida — models bem estruturados, UUID como PK, signals, API REST, deploy Railway funcionando. Os gaps são de escopo, não de qualidade.
