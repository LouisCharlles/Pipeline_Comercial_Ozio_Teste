# Notas de estudo de código: Odoo (CRM/Vendas) e Twenty (frontend)

> Objetivo: tirar ideias de modelagem, regras e organização para o desafio "Mini Pipeline Comercial com Integração ERP".
> Nenhum código foi copiado. As referências abaixo apontam arquivos/módulos que foram **lidos**, não reutilizados.

## Fontes consultadas

| Repositório | Commit estudado | Onde está clonado | Escopo lido |
|---|---|---|---|
| odoo/odoo (branch `20.0`) | `142bdfe` (2026-09-28) | `~/referencias/odoo` | `addons/crm`, `addons/sale`, `addons/sale_crm` |
| twentyhq/twenty (branch `main`) | `c36c806f` (2026-09-28) | `~/referencias/twenty` | `packages/twenty-front/src` |

Os dois foram clonados com `git clone --depth 1`, com `--filter=blob:none --sparse` a mais, para baixar só as pastas acima. Licenças: Odoo tem licença própria (LGPL e módulos proprietários) e o Twenty é AGPL-3.0. Por isso as notas descrevem ideias, não trechos de código.

---

## ESTUDO 1: Odoo (`crm`, `sale`, `sale_crm`)

### 1.1 Como modelam Oportunidade, Parceiro e Pedido

**Oportunidade = `crm.lead`** (`addons/crm/models/crm_lead.py`)
- Um único modelo serve para *lead* e *oportunidade*. O campo `type` diz qual das duas é (seleção `lead`/`opportunity`). Um lead "vira" oportunidade quando esse campo muda, sem trocar de tabela.
- Campos que importam para o desafio:
  - `name`: título, obrigatório.
  - `partner_id`: Many2one para `res.partner`, o cliente/contato. É **opcional**: o lead pode existir só com texto livre (`partner_name` para o nome da empresa e `contact_name` para o contato), e o parceiro "de verdade" é criado ou ligado depois.
  - `stage_id`: Many2one para `crm.stage`, com `ondelete='restrict'` (não dá para apagar um estágio que tem leads).
  - `expected_revenue`: valor esperado (Monetary).
  - `probability`: 0–100, com um CHECK no banco (`_check_probability` no mesmo arquivo).
  - `won_status`: `won`/`lost`/`pending`. É **calculado** (compute armazenado) a partir de estágio, probabilidade e `active`. Não é gravado diretamente.
  - `active`: um lead perdido é arquivado (`active=False`).
  - `lost_reason_id`: motivo da perda.
  - `date_closed` e `date_last_stage_update`: datas que o `write` preenche automaticamente.
  - Tem ainda muitos outros campos (equipe, vendedor, tags, receita recorrente, endereço, UTM, pontuação preditiva). Nenhum deles importa para o nosso escopo.
- Ordem padrão: prioridade desc, id desc (`_order` em `crm_lead.py`), com índices dedicados para isso.

**Estágio = `crm.stage`** (`addons/crm/models/crm_stage.py`)
- É uma **tabela configurável**, não um enum. Campos: `name`, `sequence` (ordem no kanban), `is_won` (flag que marca o estágio "ganho"), `fold`, `team_ids`.
- **Não existe estágio "Perdido"**. Perder é um *estado ortogonal*: arquivar o lead e zerar a probabilidade. O lead continua no estágio em que estava.
- Os estágios padrão (`addons/crm/data/crm_stage_data.xml`) são New, Qualified, Proposition e Won (esse último com `is_won`).

**Empresa/Parceiro = `res.partner`**
- O modelo base fica no módulo `base`, que eu **não clonei**. Só vi as extensões: `addons/crm/models/res_partner.py` acrescenta `opportunity_ids`/`opportunity_count` e `addons/sale/models/res_partner.py` acrescenta `sale_order_ids`/`sale_order_count`.
- Pelo que sei do Odoo (não conferido neste clone), `res.partner` guarda empresas e pessoas na mesma tabela, com `is_company` e `parent_id`. A extensão do CRM usa `is_company` e `parent_id` (`_prepare_values_from_partner` em `crm_lead.py`), o que é compatível com essa ideia.

**Pedido = `sale.order`** (`addons/sale/models/sale_order.py`)
- Campos principais: `name` (referência gerada por `ir.sequence` no `create`, com "New" como placeholder), `partner_id` (obrigatório), `state`, `date_order`, `origin` (documento de origem), `client_order_ref`, `order_line` (One2many de itens), `amount_total`, `locked` e `company_id`.
- Há um CHECK no banco: um pedido confirmado precisa ter data (`_date_order_conditional_required`).

**Ligação Oportunidade ↔ Pedido** (`addons/sale_crm/models/sale_order.py` e `addons/sale_crm/models/crm_lead.py`)
- `sale.order.opportunity_id` é um Many2one para `crm.lead`, **indexado mas sem unicidade**.
- `crm.lead.order_ids` é o One2many inverso. A partir dele o lead calcula `quotation_count`, `sale_order_count` e `sale_amount_total`.

### 1.2 Mudança de estágio e ação de "ganho"

- **Mudança de estágio** é um `write` comum em `stage_id`. O `write` sobrescrito em `crm_lead.py` faz o seguinte:
  - atualiza `date_last_stage_update` quando o estágio muda de fato;
  - se o novo estágio tem `is_won`, força `active=True` e `probability=100`;
  - recalcula `date_closed` (preenche ao ganhar/perder e limpa ao reabrir);
  - chama `_handle_won_lost`, que compara o status antigo com o novo e **lança `ValidationError` se o lead ficar ganho e perdido ao mesmo tempo**. Também atualiza as estatísticas de pontuação preditiva.
- **Não há máquina de estados com transições proibidas.** Dá para arrastar de qualquer estágio para qualquer outro no kanban. O único invariante validado é "não pode ser ganho e perdido ao mesmo tempo".
- **`action_set_won`** reativa o lead e procura o estágio `is_won` "mais próximo" (o primeiro com sequência maior que a atual, ou o anterior). Depois grava `stage_id` e `probability=100`. Isso só existe porque o Odoo permite vários estágios de ganho por equipe. `action_set_won_rainbowman` é a mesma coisa com uma animação na UI.
- **`action_set_lost`** arquiva o lead e grava probabilidade 0 e o motivo. O fluxo passa por um wizard de motivo de perda (`addons/crm/wizard/crm_lead_lost.py`).
- `action_restore`/`action_unarchive` reabrem um lead perdido.

### 1.3 Como a oportunidade ganha se liga ao pedido e o que impede duplicidade

- O botão "Nova cotação" chama `action_sale_quotations_new` (`sale_crm/models/crm_lead.py`):
  - se o lead não tem parceiro, abre um wizard (`sale_crm/wizard/crm_opportunity_to_quotation.py`) para criar ou escolher o cliente;
  - depois, `action_new_quotation` abre o **formulário de pedido** com defaults vindos do lead (`_prepare_opportunity_quotation_context`: parceiro, origem = nome do lead, equipe, vendedor, tags, UTM etc.).
- **O Odoo não cria o pedido automaticamente** no clique: ele pré-preenche um formulário e o usuário salva.
- **Não há nada que impeça vários pedidos por oportunidade. Isso é intencional**: a relação é 1:N (várias cotações e pedidos por oportunidade). O lead soma os pedidos confirmados e separa cotações (`draft`/`sent`) de pedidos (`sale`) com os domínios `_get_lead_quotation_domain` e `_get_lead_sale_order_domain`.
- Também **não exige** que o lead esteja em estágio ganho para gerar cotação. Quando um pedido é confirmado, `action_confirm` (sobrescrito em `sale_crm/models/sale_order.py`) só atualiza a `expected_revenue` do lead se o valor do pedido for maior. Não marca o lead como ganho.
- Conclusão para o desafio: o Odoo **não é referência** para a regra "um pedido por oportunidade". Essa regra é nossa e precisa de uma garantia própria (ver Síntese §3).

### 1.4 Estados do pedido e tratamento de erros

- Estados (`SALE_ORDER_STATE` em `sale/models/sale_order.py`): `draft` (Cotação), `sent` (Cotação enviada), `sale` (Pedido de venda) e `cancel` (Cancelado). O campo `locked` é um booleano à parte, e não um estado.
- Transições e guardas no mesmo arquivo:
  - `action_confirm`: para cada pedido, `_confirmation_error_message` devolve erro se o estado não for `draft`/`sent`. Nesse caso lança `UserError`. Depois grava `state='sale'` e `date_order=now` e pode travar (`locked`) o pedido, conforme configuração.
  - `action_cancel`: recusa pedido `locked` com `UserError`.
  - `action_draft`: volta de `cancel`/`sent` para `draft`, usando filtro silencioso em vez de erro.
  - `action_quotation_sent`: só aceita pedidos em `draft`.
  - Exclusão: `_unlink_except_draft_or_cancel` impede apagar pedido enviado ou confirmado.
  - `write`: impede trocar a lista de preços de um pedido confirmado.
- **Padrão de erro**: validações de regra de negócio lançam `UserError`/`ValidationError`. O framework faz rollback da transação da requisição inteira e o cliente web mostra a mensagem. Não vi try/except de "compensação" nesses fluxos: a transação atômica por requisição é a rede de segurança.
- Efeitos externos, como e-mail de confirmação, podem ser **adiados para um cron** (`_send_order_notification_mail` + `_cron_send_pending_emails`) quando a opção assíncrona está ativa. É um padrão útil: o efeito externo fica fora do caminho crítico e pode ser retentado.
- Não encontrei `SELECT ... FOR UPDATE` nem constraint de unicidade nos três módulos (grep em `crm/models`, `sale/models` e `sale_crm`).

---

## ESTUDO 2: Twenty (`packages/twenty-front`)

### 2.1 Organização de telas de lista, detalhe e formulário

- **Achado principal: não existem telas específicas de "Opportunity".** O Twenty é *orientado a metadados*. Oportunidade, empresa, pessoa etc. são "objetos" descritos por metadados vindos do servidor, e **as mesmas telas genéricas** renderizam qualquer objeto. Referências a `CoreObjectNameSingular.Opportunity` aparecem só em pontos isolados (ex.: `modules/page-layout/hooks/useOpportunityDefaultChartConfig.ts`, que procura os campos `stage` e `amount` para montar um gráfico padrão).
- **Rotas/páginas** (`src/pages/object-record/`):
  - `RecordIndexPage.tsx`: lista. Lê `objectNamePlural` da URL, encontra o metadado do objeto e renderiza um container. Enquanto os metadados não chegam, mostra `RecordIndexSkeletonLoader`.
  - `RecordShowPage.tsx`: detalhe. Lê `objectNameSingular` e `objectRecordId`, usa o hook `useRecordShowPageResource`, que devolve `{ record, loading, error }`, e passa isso para `RecordShowPageShell`.
  - As rotas são montadas com `lazy()` em `modules/app/routing/utils/createWorkspaceRouteObjects.tsx`.
  - As páginas são **finas**: resolvem parâmetros e estados de carregamento e delegam o resto para `modules/`.
- **Módulos por domínio** (`src/modules/<dominio>/`), cada um com subpastas padronizadas: `components/`, `hooks/`, `states/`, `utils/`, `types/`, `constants/`, `contexts/`, `graphql/`, além de `__tests__`/`__stories__`. Exemplos: `modules/object-record/record-index`, `record-show`, `record-board` (kanban), `record-table`, `record-filter`, `record-form`.
- **Lista**: `modules/object-record/record-index/components/RecordIndexContainer.tsx` escolhe entre tabela, **kanban** (`record-board`), calendário e lista conforme o tipo de "view". O kanban agrupa por um campo select (para oportunidades, o `stage`) e tem colunas (`record-board/record-board-column/components/RecordBoardColumn*.tsx`) com skeleton próprio por coluna.
- **Formulário de criação**: `modules/object-record/record-form/` (`RecordCreationFormProvider`, `RecordFormFieldInputs`, `useRecordCreationForm`). Os campos são gerados a partir dos metadados. Pelo feature flag `IS_RECORD_CREATION_FORM_ENABLED` em `useRecordCreationForm.ts`, parece que esse formulário ainda é experimental. No fluxo padrão, pelo que entendi, o registro é criado como rascunho e editado inline nas células (`record-inline-cell`, `record-field`). Isso é uma **dúvida**: não segui o fluxo completo.
- Convenções visíveis: **um componente por arquivo**, com nome igual ao do export; efeitos colaterais isolados em componentes `*Effect.tsx` que não renderizam UI (ex.: `RecordShowPageResourceEffect`, `RecordIndexFiltersToContextStoreEffect`); estado global com Jotai "por instância de componente" (`useAtomComponentState...`).

### 2.2 Loading, erro e validação

- **Loading**: skeletons dedicados por tela e por pedaço de tela (`RecordIndexSkeletonLoader`, `RecordBoardColumnLoadingSkeletonCards`, `RecordBoardColumnCardContainerSkeletonLoader`). Os hooks de dados devolvem sempre o trio `loading`/`error`/`data` (ex.: `useRecordShowPageResource`).
- **Erros**:
  - *Error boundaries* em camadas (`modules/error-handler/components/`): `AppRootErrorFallback`, `AppFullScreenErrorFallback` e `AppPageErrorFallback`, com `AppErrorBoundary` baseado em `react-error-boundary` e envio ao Sentry.
  - Erros de mutação (salvar/criar) viram **toast**. Um helper central, `modules/error-handler/utils/getToastOptionsFromError.tsx`, converte qualquer erro em opções de toast. Ele ignora `AbortError`, extrai a mensagem do erro do servidor e, **se o erro for de conflito/duplicidade, oferece um botão "ver registro existente"**. É uma boa ideia para o nosso "pedido já existe".
  - Estados vazios têm componentes próprios (`RecordIndexEmptyState*.tsx`).
  - Registro inexistente ou sem acesso mostra `WorkspaceRouteUnavailable`.
- **Validação**: nos formulários "feitos à mão" (sobretudo em `settings`), o padrão é **react-hook-form + zod** (`zodResolver`, 10 arquivos). O exemplo mais claro:
  - `modules/settings/developers/validation-schemas/webhookFormSchema.ts`: esquema zod com mensagens por campo e o tipo derivado do esquema;
  - `modules/settings/developers/hooks/useWebhookForm.ts`: um hook que concentra o formulário. Ele usa modo `onSubmit` na criação e `onTouched` na edição, calcula "pode salvar" a partir de `isValid`/`isDirty`/`isSubmitting`, carrega os dados para edição com `reset`, faz create/update com try/catch e mostra toast de sucesso ou de erro com o helper acima.
  - Resultado: a página/componente fica só com a apresentação e o hook fica com toda a lógica do formulário.

### 2.3 Busca e filtro em listas

- Há dois mecanismos que se combinam (`modules/object-record/record-index/hooks/useFindManyRecordIndexTableParams.ts`):
  1. **Filtros estruturados** (campo + operador + valor, com grupos AND/OR): estado em `record-filter` e `record-filter-group`, convertido para o filtro da query GraphQL.
  2. **Busca "em qualquer campo"** (*any field filter*): um texto único (`anyFieldFilterValueComponentState`) digitado em `object-filter-dropdown/components/ObjectFilterDropdownAnyFieldSearchInput.tsx` e convertido num OR de "contém" sobre os campos legíveis (função `turnAnyFieldFilterIntoRecordGqlFilter`, de `twenty-shared`).
  - Os filtros, a busca e o agrupamento do kanban são **combinados num único filtro** (AND) e mandados ao servidor. **A filtragem é no servidor**, não no cliente.
- Filtros e busca podem ser **salvos numa "view"** (`modules/views/`, ex.: `useSaveAnyFieldFilterToView.ts`). O estado fica em átomos Jotai, **não na URL**. Isso difere do que queremos com SSR (ver Síntese §5).
- Não conferi se há debounce no campo de busca da lista. Achei constantes de debounce só em outros contextos (`side-panel/pages/search/constants/SearchRecordPreviewDebounceMs.ts`). Fica como **dúvida**.

### 2.4 Padrões que valem adaptar (versão pequena)

1. Páginas finas e lógica em módulos por domínio, com subpastas `components`/`hooks`/`schemas`/`types`/`utils`.
2. Hook de formulário + esquema zod separado, com o tipo do formulário derivado do esquema.
3. Helper único "erro → mensagem amigável", incluindo o caso de conflito com link para o recurso existente.
4. Estados explícitos de loading (skeleton), erro (boundary por rota) e vazio (componente próprio).
5. Filtro e busca resolvidos no servidor, com todos os critérios combinados num único objeto de query.

---

## SÍNTESE para o meu projeto

### 1. Modelagem sugerida

**Empresa**
- `id`
- `nome` (obrigatório)
- `documento`/CNPJ (opcional, único quando presente)
- `criado_em`

Relação: 1 Empresa → N Oportunidades.

**Oportunidade**
- `id`
- `titulo` (obrigatório)
- `empresa` (FK → Empresa, obrigatória, `on_delete=PROTECT`)
- `valor` (Decimal ≥ 0)
- `estagio` (enum/TextChoices, default `LEAD`, indexado)
- `motivo_perda` (opcional, só com sentido em `PERDIDO`)
- `fechado_em` (preenchido ao ir para Ganho ou Perdido)
- `criado_em` e `atualizado_em`

Índices: `estagio`; busca por `titulo` e `empresa__nome` (`icontains` é suficiente. Com volume, `pg_trgm` como no Odoo, que usa `index='trigram'`).

**Pedido**
- `id`
- `oportunidade`: **OneToOne** → Oportunidade (unicidade no banco)
- `valor`: cópia do valor da oportunidade no momento da geração, como o Odoo copia dados do lead para a cotação
- `status`: `PENDENTE`, `ENVIADO` (confirmado no ERP) ou `FALHA`
- `numero_erp` (preenchido quando o ERP confirma, único e nulo até lá)
- `tentativas`, `ultimo_erro` (texto) e `criado_em`/`atualizado_em`

Diferenças deliberadas em relação ao Odoo:
- empresa obrigatória e numa tabela própria, em vez do `res.partner` genérico com texto livre;
- estágio como enum, e não tabela, porque os 5 estágios são fixos pelo enunciado;
- Pedido 1:1 com a oportunidade, e não 1:N;
- sem itens de pedido: o valor total basta para o escopo.

### 2. Estágios e regras de transição

- Estágios abertos: `LEAD → CONTATO → PROPOSTA`. Estágios finais: `GANHO` e `PERDIDO`.
- Regras sugeridas, validadas no **backend** (serviço/serializer), e não só na UI:
  - Entre estágios abertos, permitir avançar e voltar livremente, como no kanban do Odoo.
  - De qualquer estágio aberto, pode ir para `GANHO` ou `PERDIDO`.
  - `PERDIDO → estágio aberto` é permitido (reabrir, como `action_restore` do Odoo), limpando `motivo_perda` e `fechado_em`.
  - `GANHO → outro estágio` só é permitido **se ainda não houver pedido**. Com pedido existente, a oportunidade fica travada em Ganho, como o `locked` do Odoo, mas aplicado à oportunidade.
  - Gerar pedido exige `estagio == GANHO`.
  - Invariante inspirado em `_handle_won_lost`: nunca ganho e perdido ao mesmo tempo. Com enum, isso já vem de graça.
- Transição inválida → HTTP 400/409 com mensagem clara (padrão `UserError` do Odoo).
- Atualizar `fechado_em` automaticamente na mudança para um estágio final (inspirado no `write` de `crm_lead.py`).

### 3. Impedir pedido duplicado: comparação

| Estratégia | Como funciona | Prós | Contras |
|---|---|---|---|
| **Unicidade no banco** (OneToOne ou `UniqueConstraint` em `pedido.oportunidade_id`) | O segundo INSERT falha com `IntegrityError` | Garantia definitiva, mesmo com bug no código ou processos concorrentes. Custo zero de implementação | Sozinha não resolve a chamada ao ERP: duas requisições podem chamar o ERP antes de uma delas falhar no INSERT. Exige capturar `IntegrityError` e devolver o pedido existente |
| **Transação + lock de linha** (`select_for_update()` na oportunidade dentro de `transaction.atomic`) | A segunda requisição espera a primeira terminar, depois vê que o pedido já existe | Serializa o fluxo inteiro, **incluindo a chamada ao ERP**. Lógica simples de ler | Segura o lock durante a chamada externa (exige timeout curto). Só funciona se todo caminho que cria pedido usar o lock. Em testes com SQLite o `FOR UPDATE` é ignorado |
| **Chave de idempotência** (header `Idempotency-Key` gravado com a resposta) | O servidor guarda chave → resultado e repete o mesmo resultado para a mesma chave | Padrão de APIs de pagamento. Cobre retries de rede do cliente e devolve exatamente a mesma resposta | Mais uma tabela, expiração, comparação do corpo e o cliente precisa gerar e reenviar a chave. Sozinha não impede duas chaves diferentes para a mesma oportunidade |

**Recomendação para um projeto pequeno: unicidade no banco + transação com lock**, e o próprio id da oportunidade funcionando como chave de idempotência natural:

1. Abrir `transaction.atomic()` e fazer `select_for_update()` na oportunidade.
2. Validar `estagio == GANHO`.
3. Se já existe pedido `ENVIADO`, devolver o pedido existente com 200 (idempotente, sem erro). Se existe pedido `FALHA`, reutilizar a mesma linha para uma nova tentativa. Senão, criar o pedido `PENDENTE`, e a constraint OneToOne cobre qualquer furo.
4. Chamar o ERP com timeout curto, **enviando o id da oportunidade/pedido como referência externa**, para que o ERP também possa deduplicar do lado dele.
5. Gravar `ENVIADO` + `numero_erp`, ou `FALHA` + `ultimo_erro`.

Uma chave de idempotência via header fica como melhoria opcional. Não é necessária porque "uma oportunidade = um pedido" já é uma chave natural. Os testes de concorrência devem rodar no PostgreSQL, não no SQLite.

### 4. Simulação do ERP e tratamento de falhas

- Criar um **cliente de ERP com interface pequena** (algo como "criar pedido → número externo") e uma implementação **fake** no próprio backend. O modo de falha é configurável por variável de ambiente ou setting: `sucesso`, `timeout`, `erro` (5xx), `resposta_invalida` e, opcionalmente, `aleatorio` com uma taxa.
- Alternativa: um endpoint fake no próprio Django (`/erp-fake/pedidos`) chamado via HTTP com `requests` e `timeout`. É mais realista para demonstrar o timeout, mas dá mais trabalho. Sugestão: começar com o fake em processo e deixar essa opção como extra.
- Mapear as falhas para exceções de domínio próprias:
  - **Timeout**: a requisição ao ERP excede o limite (ex.: 3–5 s). Pedido fica `FALHA` com "ERP não respondeu a tempo" e a API responde **504**. Observação: no timeout o ERP *pode* ter criado o pedido. Por isso é importante enviar a referência externa (item 4 da §3), para que um retry não duplique do lado do ERP.
  - **Erro do serviço** (5xx ou indisponível): `FALHA` e **502** com mensagem amigável.
  - **Resposta inválida** (JSON quebrado, sem número de pedido, tipo errado): validar a resposta com um serializer ou esquema. Resultado: `FALHA` e **502** com "resposta inesperada do ERP".
  - **Erro de regra** (oportunidade não está Ganho): **409/400**, sem chamar o ERP.
- Registrar `tentativas` e `ultimo_erro` no pedido e expor os dois na tela de detalhes. O botão "Tentar novamente" reenvia o mesmo pedido. A ideia de tirar o efeito externo do caminho crítico (cron de e-mails do Odoo, `_cron_send_pending_emails`) fica como evolução futura. Para o desafio, chamada síncrona com timeout basta.
- Testes: um teste por modo de falha, um teste de "duas chamadas seguidas → um pedido só" e, se der tempo, um teste com duas threads ou conexões no PostgreSQL.

### 5. Padrões de frontend a adaptar (React + TS + React Router com SSR)

- **Estrutura** (inspirada em `pages/` + `modules/<dominio>/` do Twenty, bem reduzida):
  - `app/routes/`: rotas finas, cada uma com loader/action;
  - `app/features/oportunidades/`: `components/`, `api/` (funções `fetch` tipadas), `schemas/` (zod), `types/`, `utils/`;
  - `app/components/ui/`: botões, badge de estágio, skeleton, mensagem de erro.
- **Rotas**:
  - Listagem/pipeline com **loader no servidor (SSR)** que lê `?estagio=` e `?q=` da URL e chama a API Django.
  - Detalhe com loader e actions (mudar estágio, gerar pedido).
  - Nova oportunidade com action e validação.
- **Filtro e busca na URL (search params)**, diferente do Twenty (que guarda em estado/"views"). Assim o SSR já renderiza a lista filtrada, o link é compartilhável e o botão voltar funciona. Busca com debounce leve, ou um formulário GET.
- **Validação em duas camadas**: um esquema zod no front para feedback imediato, com mensagens por campo como em `webhookFormSchema.ts`, e a **validação autoritativa no DRF**. Os erros de campo do DRF são devolvidos pela action e mostrados nos mesmos campos.
- **Loading**: estado de navegação/fetcher do React Router para desabilitar botões ("Gerando pedido…") e skeleton simples na troca de filtro. **Erro**: `ErrorBoundary` por rota para falhas de carregamento e mensagens inline ou toast para falhas de ação. **Vazio**: componente próprio ("Nenhuma oportunidade neste estágio").
- **Um helper "erro da API → mensagem"** (inspirado em `getToastOptionsFromError.tsx`): trata 400 (campos), 409 (conflito ou pedido já existe, com link para o pedido), 502/504 (ERP falhou, com "tentar novamente") e erro de rede.
- Pipeline visual: colunas por estágio (lembra o `record-board` do Twenty), mas **sem drag-and-drop**. A mudança de estágio acontece na tela de detalhes, como pede o enunciado.

### 6. O que NÃO vale copiar

- **Twenty**:
  - toda a arquitetura orientada a metadados (objetos, campos e views dinâmicos);
  - Jotai com estado "por instância de componente" e o padrão `*Effect.tsx` em larga escala;
  - Apollo/GraphQL, cache otimista e sincronização por SSE;
  - views salvas, grupos de filtros AND/OR, kanban com drag-and-drop e virtualização, lingui/i18n e Sentry.
- **Odoo**:
  - `crm.stage` como tabela configurável por equipe e múltiplos estágios de ganho (`action_set_won` só existe por causa disso);
  - "perdido" como arquivamento + probabilidade, e a probabilidade automática/pontuação preditiva (PLS);
  - equipes, multiempresa, conversão de moeda, receita recorrente, UTM, rastreamento de mudanças por e-mail (`tracking`);
  - wizards de parceiro e de merge;
  - cotação com estados `draft`/`sent` e `locked`, itens de pedido, faturamento.
- Chave de idempotência completa com tabela, TTL e comparação de payload (desnecessária aqui, ver §3).
- Fila assíncrona (Celery ou similar) para o ERP. Chamada síncrona com timeout e retry manual resolve o escopo.

### 7. Dúvidas em aberto

1. **Regras de transição:** o enunciado só diz "com alteração de estágio". Posso travar Ganho quando já existe pedido e permitir reabrir Perdido? Ou devo aceitar qualquer transição, como o Odoo?
2. **Gerar pedido:** deve ser uma ação explícita na tela de detalhes (minha leitura de "pode gerar") ou automática ao mover para Ganho? A leitura atual é a ação explícita.
3. **Pedido com falha:** fica `FALHA` com retry manual? E, depois de uma falha, a oportunidade pode sair de Ganho? Hoje a proposta só trava Ganho quando o pedido está `ENVIADO`.
4. **Empresa:** precisa de CRUD próprio, ou basta um select/autocomplete, ou até "criar empresa pelo nome" no formulário de oportunidade?
5. **"React Router 8":** confirmar a versão exata e se o modo framework (loaders/actions com SSR) se aplica como descrevi. Não verifiquei documentação nesta etapa.
6. **Timeout no ERP fake:** simular com espera real (sleep maior que o timeout do cliente) ou só lançar a exceção de timeout? A espera real exige o endpoint HTTP fake.
7. **Twenty:** não confirmei o fluxo real de criação de oportunidade (formulário vs. rascunho com edição inline, ver §2.1) nem se há debounce na busca da lista (§2.3).
8. **Odoo:** não li o `res.partner` base (módulo `base` não foi clonado). A descrição de `is_company`/`parent_id` vem de conhecimento prévio e de uso indireto em `crm_lead.py`.
