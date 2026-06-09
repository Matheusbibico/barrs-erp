# Barrs ERP — direção visual premium para Unfold

## Crítica do layout anterior

- A área principal tinha muito fundo vazio e pouca densidade útil para um ERP desktop-first.
- As tabelas pareciam CRUD padrão: linhas baixas, cabeçalho sem presença, hover fraco e pouca hierarquia.
- A sidebar era pesada por contraste, mas sem refinamento de produto premium.
- Os botões primários e ações importantes não guiavam o olhar.
- O dashboard mostrava dados, mas não contava uma história operacional clara.

## Wireframe textual

```text
┌ Sidebar 264px ┬ Topbar discreta ───────────────────────────────┐
│ Barrs Store   │ Gestão interna / breadcrumb                     │
│ Busca         ├─────────────────────────────────────────────────┤
│ Loja          │ Hero: Visão geral da Barrs Store   [Clientes]   │
│ Pedidos       │                                   [Novo pedido]  │
│ Produtos      │ ┌ KPI ┐ ┌ KPI ┐ ┌ KPI ┐ ┌ KPI ┐                │
│ Clientes      │ └─────┘ └─────┘ └─────┘ └─────┘                │
│ Operações     │ ┌ KPI ┐ ┌ KPI ┐ ┌ KPI ┐ ┌ KPI ┐                │
│ Financeiro    │ └─────┘ └─────┘ └─────┘ └─────┘                │
│ Sistema       │ ┌ Card tabela: últimos pedidos ───────────────┐ │
│ Usuário       │ │ cabeçalho, status, total, data               │ │
└───────────────┴─┴──────────────────────────────────────────────┘
```

## Melhorias aplicadas

- Design system novo em `static/admin/css/barrs_premium.css`.
- Sidebar com fundo `#2C2822`, menor largura visual, hover suave e ativo destacado.
- Dashboard com hero, ações rápidas e KPIs de clientes, pedidos, faturamento e ticket médio.
- Tabelas com linhas mais altas, cabeçalho sticky, hover verde suave e melhor legibilidade.
- Botões, inputs, cards, empty states e fieldsets com raio 12px e sombra sutil.
- Tipografia premium: Playfair Display para títulos e Montserrat para interface.

## Próximos passos recomendados

- Criar cards específicos no topo das listagens principais: Pedidos, Clientes, Produtos e Financeiro.
- Separar formulários longos em fieldsets: Dados principais, Financeiro, Entrega e Observações.
- Adicionar filtros salvos nas listagens mais usadas.
- Trocar ações destrutivas para botões secundários/terciários com confirmação visual.
- Criar indicadores de status padronizados para pedidos, estoque e financeiro.
