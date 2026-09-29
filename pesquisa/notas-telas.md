# Notas de telas: Pipedrive e HubSpot + proposta de telas do app

> Objetivo: tirar ideias de UX para o desafio "Mini Pipeline Comercial com Integração ERP".
> Data: 2026-09-28.

## ⚠️ Limitação desta pesquisa: as telas NÃO foram observadas

- Nesta sessão eu **não tinha acesso a um navegador** conectado às suas contas logadas do Pipedrive e do HubSpot. O navegador do Antigravity não é controlável daqui. Por isso **nenhuma tela foi aberta, nenhum dado foi criado e nenhum print foi salvo** (a pasta `pesquisa/prints/` não existe).
- Como você decidiu, a Parte 1 foi feita com a **documentação oficial pública** (Pipedrive Knowledge Base e HubSpot Knowledge Base). Cada afirmação indica a fonte.
- Legenda usada abaixo:
  - **[doc]**: está escrito na documentação oficial.
  - **[não documentado]**: a documentação consultada não cobre o ponto. Fica como lacuna e **não foi preenchido com suposição**.
- Pontos como aparência de loading, textos de estado vazio e mensagens de erro exatas **só podem ser confirmados olhando a tela**. Se quiser fechar essas lacunas, os prints podem ir em `pesquisa/prints/`.

---

## PARTE 1: Produtos de referência

### 1. Pipedrive

**Layout da listagem/pipeline**
- [doc] A visão principal é o *pipeline*: colunas por estágio com cards de negócio (*deal*). Por padrão o card mostra **título, pessoa de contato e organização, valor, etiqueta (label) e responsável (owner)**. Há um ícone de atividades no card. Clicar no card abre o detalhe. ([pipeline-view], [deal-card])
- [doc] Os campos do card são configuráveis em "Customize deal cards", no seletor do pipeline. ([deal-card])
- [doc] A ordem padrão dos cards é por **próxima atividade**. O "Sort by" permite ordenar por valor, data prevista de fechamento, responsável etc. ([pipeline-view])
- [doc] Negócios ganhos ou perdidos **somem do pipeline ativo** e continuam acessíveis por filtros. Ganho/Perdido é um **status**, não uma coluna do pipeline. ([pipeline-view], [won-lost-disappear])
- [não documentado] Conteúdo do cabeçalho das colunas (soma de valor, contagem).

**Filtro e busca**
- [doc] Os filtros ficam em *Filter › Filters*: escolher um filtro salvo ou "+ Add new filter". Os filtros podem ir para favoritos. ([pipeline-view])
- [doc] Para ver ganhos, perdidos e excluídos usa-se filtro de status. ([filter-won-lost])
- [não documentado] Busca textual *dentro* da visão de pipeline. Pelo material lido, a busca é a global do app, e não confirmei se ela filtra o pipeline.

**Seletor de estágio no detalhe e confirmação**
- [doc] O detalhe tem uma **barra de progresso de estágios** com o estágio atual e os dias em cada estágio. Ela **para de ser atualizada depois que o negócio é ganho**. ([deal-detail])
- [doc] "Marcar como perdido" abre um **prompt que pede o motivo** (texto livre ou lista pré-definida, conforme configuração) e comentários. A mudança só acontece ao clicar "Mark as lost". ([lost-reasons])
- [doc] Se o estágio de destino exige **campos obrigatórios** ainda vazios, o usuário é **solicitado a preencher antes de avançar**. ([required-fields])
- [não documentado] Se a barra é clicável para trocar de estágio, a posição exata dos botões Won/Lost e se existe confirmação para mudanças entre estágios abertos.

**Formulário de novo negócio**
- [doc] O **título é obrigatório** e o negócio precisa estar ligado a **uma pessoa ou organização** (ou projeto). ([add-deal], [required-fields-search])
- [doc] Dá para adicionar produtos já no formulário. Os campos exibidos no modal são configuráveis. ([products], [add-modal-fields])
- [doc] Campo obrigatório vazio → **mensagem de erro que impede a criação**. A obrigatoriedade pode valer por pipeline e por estágio. ([required-fields])
- [doc] **Não há detecção de negócio duplicado**. A solução é o merge manual. ([duplicates])
- [não documentado] Texto exato das mensagens e se a validação é por campo ou por submit.

**Estados vazio, loading e erro**
- [não documentado] Nada disso aparece na documentação consultada. Só dá para ver na tela.

**Ação equivalente a "gerar pedido/proposta"**
- [doc] **Smart Docs** gera propostas, cotações e contratos a partir do negócio, com os dados dos produtos preenchidos por template. ([smart-docs])
- [doc/inferência] Nada impede gerar **vários documentos** para o mesmo negócio. Não há regra "um por negócio".
- [não documentado] Se o botão é desabilitado em alguma condição e como o documento gerado aparece no detalhe.

### 2. HubSpot

**Layout da listagem/pipeline**
- [doc] O índice de Deals tem **visão de tabela** (colunas são propriedades) e **visão de board** (colunas por estágio). ([view-filter], [board-view])
- [doc] Os cards do board são configuráveis: até **15 itens** (propriedades, associações, seções). As colunas podem ter até **3 métricas** de resumo, configuráveis, por exemplo no rodapé. As propriedades do card são **editáveis inline**. ([board-custom], [board-manage])
- [doc] Estágios padrão do "Sales Pipeline" têm uma probabilidade associada. Aqui **Closed Won / Closed Lost são estágios** (colunas), e não um status à parte como no Pipedrive. ([pipelines])
- [não documentado] Conteúdo padrão do card e métricas padrão da coluna.

**Filtro e busca**
- [doc] **Quick filters** ficam acima da tabela/board (dropdown por propriedade, até 10, configuráveis). Há ainda **Advanced filters** com grupos AND/OR. ([view-filter], [quick-filters])
- [doc] Filtros aplicados **não persistem no refresh** a menos que a *view* seja salva. ([view-filter])
- [não documentado] Quais campos a caixa de busca do índice pesquisa.

**Seletor de estágio no detalhe e confirmação**
- [doc] O estágio é uma propriedade (*Deal stage*) editável por **dropdown**. Com **pipeline rules**, o dropdown **mostra estágios disponíveis e indisponíveis** (ex.: proibir pular estágios ou voltar). Mover para Closed Lost pode pular estágios. ([pipeline-rules])
- [doc] Pode-se exigir propriedades ao entrar num estágio ("conditional stage logic"). ([pipeline-rules])
- [não documentado] Existência de diálogo de confirmação ao mudar estágio e o formato do prompt de propriedades obrigatórias.

**Formulário de novo negócio**
- [doc] Criação por painel lateral. No board, dá para criar direto numa coluna ("Create record" ao passar o mouse): **Pipeline e Deal stage vêm pré-preenchidos**. Campos vistos: nome, pipeline, estágio, valor (*Amount*), data de fechamento, associações com contato/empresa existentes e line items. ([create-deals], [board-manage])
- [doc] Propriedades-chave: Deal name, Deal owner, Deal stage. ([default-props])
- [não documentado] Quais campos são obrigatórios na tela e as mensagens de validação.

**Estados vazio, loading e erro**
- [não documentado] Nada disso aparece na documentação consultada.

**Ação equivalente a "gerar pedido/proposta"**
- [doc] O detalhe do deal tem um **card "Quotes" na barra lateral, com botão "+ Add"**. No board também existe "Create a quote" no hover. ([quotes-create], [quotes-search])
- [doc] **Pré-condições**: permissão de editar/criar deals; o vendedor precisa ter e-mail e nome de empresa; pelo menos um contato comprador. Deals vindos de e-commerce (ex.: Shopify) **não podem** ter quote. ([quotes-create])
- [doc] Depois de criada, a quote **aparece listada no card Quotes** do deal, com link compartilhável e **status** (Draft, Pending approval, Changes requested, Publishing, Published…). ([quotes-create], [quotes-search])
- [doc] **Várias quotes por deal são permitidas**. O valor do deal reflete a última publicada. ([quotes-create])

### 3. O que isso diz para o desafio

| Tema | Pipedrive | HubSpot | Leitura para o app |
|---|---|---|---|
| Card | título, contato/org, valor, label, owner | configurável | título, empresa, valor, estágio |
| Ganho/Perdido | status, fora do pipeline | estágios Closed Won/Lost | enunciado trata como **estágios** (mais perto do HubSpot) |
| Perder | pede motivo em prompt | propriedade exigível por regra | confirmação ao ir para Perdido; motivo opcional (dúvida) |
| Regras de estágio | campos obrigatórios por estágio | pipeline rules (pular/voltar) | regras mínimas no backend; UI desabilita opções inválidas |
| Documento comercial | Smart Docs, N por negócio | Quotes, N por deal, card na lateral | **nosso é 1:1** e só em Ganho. Nenhum dos dois serve de modelo para a regra; serve o **card lateral com status + link** |
| Filtros | filtros salvos | quick filters + advanced, views | 1 filtro de estágio + 1 busca, **na URL** |

---

## PARTE 2: Estrutura proposta para o meu app

### 2.1 Telas e rotas

| Rota | Tela | Dados | Observações |
|---|---|---|---|
| `/oportunidades?estagio=&q=` | Listagem (**SSR**) | `loader` no servidor chama `GET /api/oportunidades?estagio=&q=` | Chips de estágio com contagem (Todos, Lead, Contato, Proposta, Ganho, Perdido) + campo de busca (empresa ou título) num `<Form method="get">`. Tabela: título, empresa, valor, badge de estágio, badge "Pedido #123" se houver. Linha leva ao detalhe. |
| `/oportunidades/nova` | Formulário | `action` → `POST /api/oportunidades` | Campos: título*, empresa*, valor, estágio inicial (default Lead). Depois de salvar: redirect para o detalhe. |
| `/oportunidades/:id` | Detalhe | `loader` → `GET /api/oportunidades/:id` (inclui o pedido, se houver) | Cabeçalho (título, empresa, valor). **Seletor de estágio** logo abaixo do cabeçalho. **Card "Pedido"** na lateral/abaixo, no estilo do card Quotes do HubSpot. Duas actions via `intent`: `mudar-estagio` e `gerar-pedido`. |
| `/` | redirect para `/oportunidades` | | |

- Listagem em **tabela com filtro por chips**, e não kanban. Filtrar por estágio num kanban é redundante, e a tabela funciona melhor no celular e com SSR. Um kanban somente leitura pode ser um extra (ver conflito nº 1 em `notas-pesquisa.md`).
- **Seletor de estágio**: um `<select>`, ou uma barra segmentada (como a barra do Pipedrive), com botão "Salvar estágio". Opções inválidas aparecem **desabilitadas com dica** (ideia das pipeline rules do HubSpot). Ir para **Ganho ou Perdido pede confirmação** ("Marcar como Perdido? Isso encerra a oportunidade."), como o prompt de perda do Pipedrive. Mudanças entre estágios abertos não pedem confirmação.

### 2.2 Botão "Gerar pedido": comportamento por situação

O card "Pedido" no detalhe sempre aparece. O conteúdo muda conforme o estado:

| Situação | O que o usuário vê | Ação |
|---|---|---|
| Estágio ≠ Ganho, sem pedido | Botão **desabilitado** + texto "Disponível quando a oportunidade estiver em Ganho". | nenhuma |
| Ganho, sem pedido | Botão **"Gerar pedido"** habilitado (primário). | `POST .../gerar-pedido` |
| Pedido em andamento (requisição enviada, aguardando resposta) | Botão desabilitado com spinner, **"Gerando pedido…"**. O seletor de estágio também fica desabilitado. Duplo clique não gera 2 requisições. | nenhuma (espera) |
| Pedido gerado (`ENVIADO`) | O botão **some** e em seu lugar aparece: "Pedido **#ERP-123** gerado em 28/09 · R$ X" + badge verde. Estágio travado em Ganho (seletor desabilitado com explicação). | nenhuma |
| Erro na integração (`FALHA`) | Alerta vermelho: mensagem amigável ("O ERP não respondeu a tempo" / "O ERP retornou erro") + nº de tentativas + botão **"Tentar novamente"**. | mesma action; reaproveita o pedido |
| Pedido `PENDENTE` "preso" (ao recarregar a página) | Aviso "Pedido em processamento…" + "Tentar novamente". Ver dúvida no `notas-pesquisa.md`. | a definir |
| Servidor responde "já existe pedido" (outra aba gerou antes) | Não mostra erro: recarrega e exibe o estado "Pedido gerado" com o link. | nenhuma |

- O botão é só conveniência: **a regra é do backend**. A UI apenas reflete o estado que vem no `loader`.

### 2.3 Loading, erro e validação: um padrão só

- **Loading**
  - A listagem vem pronta via SSR, então não tem spinner inicial.
  - Troca de filtro ou busca: `useNavigation().state === "loading"` → lista com opacidade reduzida + barra fina no topo. Um único componente `<PendingBar/>`.
  - Submits: botão com `disabled` e texto "Salvando…" / "Gerando pedido…", usando `navigation.state === "submitting"` ou `fetcher.state`.
- **Erro de carregamento**: `ErrorBoundary` por rota. 404 → "Oportunidade não encontrada" + link para a lista. Outros → "Não foi possível carregar" + "Tentar de novo".
- **Erro de ação**: a action **retorna** `{ ok: false, error, fieldErrors }` em vez de lançar. A tela mostra um `<Alert>` no topo do bloco afetado (card Pedido ou seletor de estágio). Um helper único `apiErrorToMessage(status, body)` cobre 400, 404, 409, 502, 504 e erro de rede.
- **Validação**: zod no front (feedback no submit, mensagem abaixo do campo) + **DRF como fonte da verdade**. A action repassa os `fieldErrors` do DRF para os mesmos campos. Os valores digitados são mantidos depois de um erro.
- **Estado vazio**: `<EmptyState>` com duas variantes: "Nenhuma oportunidade ainda" + botão "Nova oportunidade", e "Nada encontrado para 'x' em Proposta" + "Limpar filtros".

### 2.4 O que NÃO copiar (complexo demais para o escopo)

- Kanban com drag-and-drop, cards configuráveis, métricas por coluna, edição inline nos cards.
- Vários pipelines, estágios configuráveis, probabilidade por estágio, "rotting"/SLA.
- Filtros salvos/views, filtros avançados AND/OR, quick filters configuráveis.
- Campos obrigatórios por estágio configuráveis e pipeline rules com permissões por usuário/time.
- Motivo de perda com lista gerenciável (no máximo, texto livre opcional).
- Quotes/Smart Docs: templates, line items/produtos, status de aprovação, assinatura, link público, várias cotações por oportunidade.
- Atividades, e-mails, notas, arquivos e histórico no detalhe; owner/responsável; merge de duplicados.

---

## Fontes (documentação oficial consultada em 2026-09-28)

Pipedrive:
- [pipeline-view]: https://support.pipedrive.com/en/article/pipeline-view
- [deal-card]: https://support.pipedrive.com/en/article/deal-card-customization-sorting
- [deal-detail]: https://support.pipedrive.com/en/article/deal-detail-view
- [add-deal]: https://support.pipedrive.com/en/article/deals-what-they-are-and-how-to-add-them
- [required-fields] / [required-fields-search]: https://support.pipedrive.com/en/article/required-fields
- [add-modal-fields]: https://support.pipedrive.com/en/article/how-can-i-add-data-fields-to-an-add-deal-contact-or-product-modal
- [lost-reasons]: https://support.pipedrive.com/en/article/lost-reasons
- [filter-won-lost]: https://support.pipedrive.com/en/article/filtering-for-my-won-lost-or-deleted-deals
- [won-lost-disappear]: https://support.pipedrive.com/hc/en-us/articles/115001107449-Why-does-my-deal-disappear-in-the-pipeline-when-it-gets-marked-as-Won-or-Lost-
- [products]: https://support.pipedrive.com/en/article/products
- [duplicates]: https://support.pipedrive.com/en/article/how-to-avoid-duplicates-during-an-import · https://support.pipedrive.com/en/article/merge-duplicates
- [smart-docs]: https://support.pipedrive.com/en/article/sales-documents-beta

HubSpot:
- [board-manage]: https://knowledge.hubspot.com/records/manage-records-in-board-view
- [board-custom]: https://knowledge.hubspot.com/object-settings/select-properties-to-show-on-records-in-board-view
- [pipelines]: https://knowledge.hubspot.com/object-settings/set-up-and-customize-pipelines
- [pipeline-rules]: https://knowledge.hubspot.com/object-settings/set-up-pipeline-rules
- [create-deals]: https://knowledge.hubspot.com/records/create-deals
- [default-props]: https://knowledge.hubspot.com/properties/hubspots-default-deal-properties
- [view-filter]: https://knowledge.hubspot.com/records/view-and-filter-records
- [quick-filters]: https://knowledge.hubspot.com/records/customize-quick-filters
- [quotes-create]: https://knowledge.hubspot.com/quotes/create-and-send-quotes
- [quotes-search]: https://knowledge.hubspot.com/quotes/understand-how-quotes-work-in-hubspot

Observação: algumas páginas foram lidas por um extrator automático que resume o conteúdo. Os trechos marcados [doc] refletem esse resumo e não uma leitura linha a linha. As páginas [pipelines], [default-props], [quick-filters], [products], [duplicates] e [quotes-search] foram vistas só pelo resumo da busca.
