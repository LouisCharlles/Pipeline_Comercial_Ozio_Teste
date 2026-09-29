# Feature Specification: Mini Pipeline Comercial com Integração ERP

**Feature Branch**: `001-pipeline-comercial-erp`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "Mini Pipeline Comercial com Integração ERP: vendedores cadastram, listam,
visualizam e editam oportunidades ligadas a empresas; movem-nas entre os estágios Lead, Contato,
Proposta, Ganho e Perdido; filtram por estágio e buscam por empresa ou título; em Ganho, geram um
pedido no ERP (simulado), nunca mais de um por oportunidade, com falhas tratadas e nova tentativa
segura. Fora de escopo: autenticação, dashboards, arrastar e soltar, CI/CD."

## Clarifications

### Session 2026-09-29

Fonte: comparação do protótipo Figma Make "Mini-CRM-B2B-Prototype" com `pesquisa/`.

- Q: Como o vendedor informa a empresa no formulário (protótipo usa select de empresas
  existentes; spec previa texto livre)? → A: Campo de texto com sugestões das empresas existentes;
  nome existente é reaproveitado, nome novo cria a empresa. O select do protótipo não é adotado.
- Q: Quais estágios podem ser escolhidos ao criar uma oportunidade (protótipo oferece os cinco)?
  → A: Apenas estágios abertos (Lead, Contato, Proposta), padrão Lead; Ganho e Perdido só pelo
  detalhe, com confirmação.
- Q: Como o vendedor muda o estágio no detalhe? → A: Barra segmentada com os cinco estágios;
  clicar num estágio aberto aplica imediatamente; Ganho e Perdido abrem modal de confirmação.
- Q: Como uma oportunidade em Perdido é reaberta (protótipo desabilita estágios e cita "Reabra",
  sem botão)? → A: Clicando num estágio aberto da barra, com confirmação; limpa data de fechamento
  e motivo; Ganho indisponível a partir de Perdido. O modal de Perdido inclui o campo opcional de
  motivo.
- Q: Como o vendedor edita título, empresa e valor (protótipo não tem edição)? → A: Botão
  "Editar" no cabeçalho do detalhe leva ao mesmo formulário do cadastro, em página própria,
  pré-preenchido e sem o campo estágio; salvar volta ao detalhe, cancelar descarta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar e consultar oportunidades (Priority: P1)

O vendedor registra uma nova oportunidade informando título, empresa e valor. Depois encontra essa
oportunidade na listagem, abre o detalhe e corrige dados quando necessário.

**Why this priority**: sem oportunidades cadastradas não existe pipeline nem pedido; é a base de
todas as outras histórias.

**Independent Test**: criar uma oportunidade pelo formulário, vê-la na listagem, abrir o detalhe e
editar o título; os dados alterados aparecem na listagem e no detalhe.

**Acceptance Scenarios**:

1. **Given** o formulário de nova oportunidade, **When** o vendedor preenche título e empresa e
   salva, **Then** a oportunidade é criada no estágio escolhido (Lead, se não alterado) e o
   vendedor é levado ao detalhe dela.
2. **Given** o formulário, **When** o vendedor tenta salvar sem título ou sem empresa, **Then** a
   oportunidade não é criada, cada campo inválido exibe sua mensagem e os valores digitados são
   mantidos.
3. **Given** uma oportunidade existente, **When** o vendedor aciona "Editar" no detalhe, altera
   título, empresa ou valor no formulário pré-preenchido e salva, **Then** volta ao detalhe e os
   novos dados passam a ser exibidos no detalhe e na listagem.
4. **Given** um endereço de oportunidade inexistente, **When** o vendedor o acessa, **Then** vê a
   mensagem "Oportunidade não encontrada" e um caminho de volta à listagem.

---

### User Story 2 - Gerar pedido no ERP sem duplicidade (Priority: P1)

Com a oportunidade em Ganho, o vendedor aciona "Gerar pedido" no detalhe. O sistema envia o pedido
ao ERP; em caso de sucesso, o pedido (com o número devolvido pelo ERP) fica registrado e associado
à oportunidade. Se a integração falhar, o vendedor vê uma mensagem clara e pode tentar de novo sem
risco de gerar um segundo pedido.

**Why this priority**: é o objetivo do desafio e concentra as regras mais críticas (unicidade do
pedido e consistência diante de falhas).

**Independent Test**: com uma oportunidade em Ganho, acionar "Gerar pedido" várias vezes (inclusive
de forma simultânea) e com o ERP simulado em cada modo de falha; ao final, existe no máximo um
pedido para a oportunidade e o estado exibido corresponde ao resultado real.

**Acceptance Scenarios**:

1. **Given** uma oportunidade em Ganho sem pedido e o ERP respondendo com sucesso, **When** o
   vendedor aciona "Gerar pedido", **Then** o pedido é registrado com o número do ERP, associado à
   oportunidade, e o detalhe passa a exibir número, data e valor do pedido no lugar do botão.
2. **Given** uma oportunidade que já tem pedido gerado, **When** a solicitação de gerar pedido é
   repetida (novo clique, outra aba ou reenvio), **Then** nenhum novo pedido é criado, o ERP não é
   acionado de novo e o vendedor vê o pedido já existente.
3. **Given** uma oportunidade em Ganho sem pedido, **When** duas solicitações de gerar pedido
   chegam ao mesmo tempo, **Then** existe exatamente um pedido para a oportunidade ao final.
4. **Given** o ERP não responde a tempo, **When** o vendedor aciona "Gerar pedido", **Then** vê a
   mensagem "O ERP não respondeu a tempo. Tente novamente.", a opção "Tentar novamente" e o número
   de tentativas já feitas.
5. **Given** o ERP responde com erro ou com resposta inválida, **When** o vendedor aciona "Gerar
   pedido", **Then** vê uma mensagem específica para o tipo de falha e a opção "Tentar novamente".
6. **Given** uma tentativa anterior falhou, **When** o vendedor aciona "Tentar novamente" e o ERP
   responde com sucesso, **Then** o pedido é concluído sobre o mesmo registro (sem criar outro) e
   passa a exibir o número do ERP.
7. **Given** uma oportunidade que não está em Ganho, **When** o vendedor abre o detalhe, **Then** a
   ação "Gerar pedido" aparece indisponível com a explicação "Disponível quando a oportunidade
   estiver em Ganho"; se a solicitação for enviada mesmo assim, é recusada com mensagem clara e o
   ERP não é acionado.
8. **Given** a solicitação de pedido está em andamento, **When** o vendedor tenta acionar de novo,
   **Then** a ação permanece indisponível com a indicação "Gerando pedido…" até a resposta.

---

### User Story 3 - Mover a oportunidade entre estágios (Priority: P2)

No detalhe, o vendedor muda o estágio da oportunidade (Lead, Contato, Proposta, Ganho, Perdido)
conforme a negociação evolui, clicando no estágio desejado numa barra com os cinco estágios.

**Why this priority**: é o que caracteriza o pipeline e o que habilita a geração de pedido; depende
da história 1.

**Independent Test**: levar uma oportunidade de Lead até Ganho passando por Contato e Proposta, e
outra até Perdido; verificar estágio exibido no detalhe e na listagem após cada mudança.

**Acceptance Scenarios**:

1. **Given** uma oportunidade em estágio aberto (Lead, Contato ou Proposta), **When** o vendedor
   clica em outro estágio aberto, **Then** o estágio é atualizado imediatamente, sem pedido de
   confirmação.
2. **Given** uma oportunidade em estágio aberto, **When** o vendedor clica em Ganho ou Perdido,
   **Then** o sistema abre uma confirmação e, confirmada, registra o estágio e a data de
   fechamento; cancelada, nada muda.
3. **Given** uma oportunidade em Perdido, **When** o vendedor clica num estágio aberto e confirma
   a reabertura, **Then** ela é reaberta nesse estágio e a data de fechamento e o motivo de perda
   são limpos; Ganho permanece indisponível enquanto ela estiver em Perdido.
4. **Given** uma oportunidade em Ganho com pedido gerado com sucesso, **When** o vendedor vê a
   barra de estágios, **Then** a mudança está bloqueada com a explicação "Oportunidade com pedido
   gerado não pode mudar de estágio"; se a solicitação for enviada mesmo assim, é recusada.
5. **Given** uma mudança de estágio inválida é enviada, **When** o sistema a recusa, **Then** o
   vendedor vê a mensagem do motivo e o estágio anterior permanece.

---

### User Story 4 - Filtrar e buscar na listagem (Priority: P3)

Na listagem, o vendedor filtra as oportunidades por estágio e busca por nome da empresa ou título,
para encontrar rapidamente o que precisa trabalhar.

**Why this priority**: melhora a produtividade, mas o fluxo principal funciona sem ela.

**Independent Test**: com oportunidades em estágios e empresas variados, aplicar filtro de estágio,
busca por trecho de nome de empresa e busca por trecho de título, conferindo os resultados.

**Acceptance Scenarios**:

1. **Given** oportunidades em vários estágios, **When** o vendedor seleciona um estágio, **Then**
   apenas as oportunidades daquele estágio são exibidas, e cada estágio mostra sua contagem.
2. **Given** a listagem, **When** o vendedor busca por um trecho do nome da empresa ou do título,
   sem diferenciar maiúsculas/minúsculas, **Then** aparecem as oportunidades cujo título ou empresa
   contém o trecho.
3. **Given** filtro e busca aplicados, **When** o vendedor compartilha ou recarrega o endereço da
   página, **Then** a listagem é exibida com os mesmos filtros.
4. **Given** nenhum resultado para os filtros, **When** a listagem é exibida, **Then** aparece a
   mensagem "Nada encontrado" com a opção "Limpar filtros"; se não houver nenhuma oportunidade
   cadastrada, aparece "Nenhuma oportunidade ainda" com a opção "Nova oportunidade".

---

### Edge Cases

- Dois vendedores (ou duas abas) acionam "Gerar pedido" ao mesmo tempo para a mesma oportunidade:
  as solicitações são atendidas uma de cada vez e apenas um pedido existe ao final. A que chega
  depois recebe o pedido já gerado ou, se a anterior falhou, o resultado de uma nova tentativa
  sobre o mesmo registro; nunca um erro genérico nem um segundo pedido.
- O ERP excede o tempo limite, mas pode ter criado o pedido do lado dele: a nova tentativa usa a
  mesma referência da oportunidade, permitindo ao ERP reconhecer a repetição.
- O processamento é interrompido no meio da chamada ao ERP: a tentativa é desfeita por inteiro
  (a oportunidade volta à situação anterior: sem pedido ou com a falha anterior registrada), o
  vendedor vê uma mensagem de erro inesperado e pode repetir com segurança.
- Oportunidade em Ganho com tentativa de pedido que falhou é movida para outro estágio: permitido;
  o registro da tentativa falha é mantido e só pode ser retomado quando a oportunidade voltar a
  Ganho.
- Oportunidade em Ganho sem valor ou com valor zero: a geração do pedido é recusada com a mensagem
  "Informe um valor maior que zero antes de gerar o pedido".
- Edição do valor de uma oportunidade com pedido já gerado: o pedido mantém o valor do momento em
  que foi gerado.
- Valor negativo ou não numérico no formulário: recusado com mensagem no campo.
- Busca com espaços extras ou vazia: espaços nas pontas são ignorados; busca vazia não filtra.
- Falha de comunicação com o sistema ao carregar uma tela: mensagem "Não foi possível carregar" com
  opção de tentar de novo, sem tela em branco.
- Empresa com oportunidades não pode ser removida de forma a deixar oportunidades órfãs.

## Requirements *(mandatory)*

### Functional Requirements

**Oportunidades e empresas**

- **FR-001**: O sistema MUST permitir cadastrar oportunidade com título (obrigatório), empresa
  (obrigatória), valor (opcional, maior ou igual a zero) e estágio inicial, restrito aos estágios
  abertos (Lead, Contato ou Proposta; padrão Lead). Criar diretamente em Ganho ou Perdido MUST ser
  recusado pelo sistema.
- **FR-002**: Cada oportunidade MUST estar ligada a exatamente uma empresa; uma empresa pode ter
  várias oportunidades.
- **FR-003**: No formulário, a empresa MUST ser informada pelo nome: o sistema reaproveita a
  empresa já cadastrada com o mesmo nome (sem diferenciar maiúsculas/minúsculas e ignorando
  espaços nas pontas) ou cria uma nova. Enquanto o vendedor digita, o campo MUST sugerir empresas
  já cadastradas cujo nome contém o trecho digitado; escolher uma sugestão é opcional. Não há tela
  própria de cadastro de empresas.
- **FR-004**: O sistema MUST permitir visualizar o detalhe de uma oportunidade com título, empresa,
  valor, estágio, datas de criação/atualização/fechamento e a situação do pedido.
- **FR-005**: O sistema MUST permitir editar título, empresa e valor de uma oportunidade existente,
  com as mesmas validações do cadastro. A edição é acessada pelo botão "Editar" no cabeçalho do
  detalhe e usa o mesmo formulário do cadastro, em página própria, pré-preenchido e sem o campo
  estágio (estágio só muda pela barra do detalhe); salvar leva de volta ao detalhe.
- **FR-006**: Erros de validação MUST ser exibidos junto a cada campo, mantendo os valores digitados.

**Estágios**

- **FR-007**: Os estágios MUST ser fixos: Lead, Contato e Proposta (abertos); Ganho e Perdido
  (finais).
- **FR-008**: Entre estágios abertos, o movimento MUST ser livre nos dois sentidos; de qualquer
  estágio aberto MUST ser possível ir para Ganho ou Perdido.
- **FR-009**: No detalhe, o estágio MUST ser alterado por uma barra com os cinco estágios: clicar
  num estágio aberto aplica a mudança imediatamente; mudar para Ganho ou Perdido MUST exigir
  confirmação do vendedor em modal e registrar a data de fechamento. Enquanto a mudança está sendo
  enviada, a barra fica indisponível.
- **FR-010**: Ao ir para Perdido, o modal de confirmação MUST oferecer um campo de motivo de perda
  em texto livre (opcional); o motivo informado é exibido no detalhe.
- **FR-011**: Uma oportunidade em Perdido MUST poder ser reaberta clicando num estágio aberto na
  barra de estágios, após confirmação ("Reabrir oportunidade?"); a reabertura limpa a data de
  fechamento e o motivo de perda. Não há botão "Reabrir" separado. De Perdido não é possível ir
  direto para Ganho (a opção aparece indisponível).
- **FR-012**: Uma oportunidade com pedido gerado com sucesso MUST NOT mudar de estágio.
- **FR-013**: As regras de transição MUST ser aplicadas pelo sistema, não apenas pela tela; uma
  transição inválida é recusada com mensagem e o estágio anterior é mantido.

**Listagem**

- **FR-014**: A listagem MUST exibir as oportunidades em uma tabela única, com seletor de estágio
  (Todos, Lead, Contato, Proposta, Ganho, Perdido) mostrando a contagem de cada um, e colunas
  título, empresa, valor, estágio e indicação de pedido gerado. Cada linha leva ao detalhe.
- **FR-015**: A listagem MUST permitir filtrar por um estágio (ou todos) e buscar por trecho do
  nome da empresa ou do título, sem diferenciar maiúsculas de minúsculas.
- **FR-016**: Filtro e busca MUST ficar refletidos no endereço da página, permitindo recarregar ou
  compartilhar a mesma visão.
- **FR-017**: A primeira exibição da listagem MUST chegar ao vendedor já com os dados, sem etapa
  intermediária de carregamento.
- **FR-018**: A listagem MUST diferenciar "nenhuma oportunidade cadastrada" de "nenhum resultado
  para os filtros".

**Pedido e integração com o ERP**

- **FR-019**: A geração de pedido MUST ser uma ação explícita do vendedor no detalhe, disponível
  apenas quando a oportunidade está em Ganho e tem valor maior que zero.
- **FR-020**: Uma oportunidade MUST ter no máximo um pedido, em qualquer circunstância (cliques
  repetidos, reenvios, várias abas, solicitações simultâneas). Essa garantia MUST valer mesmo que
  as verificações da tela sejam contornadas.
- **FR-021**: Solicitar pedido para oportunidade que já tem pedido gerado MUST devolver o pedido
  existente, sem acionar o ERP novamente.
- **FR-022**: Em caso de sucesso, o pedido MUST registrar o número devolvido pelo ERP, o valor da
  oportunidade no momento da geração, a data e a associação com a oportunidade.
- **FR-023**: O sistema MUST distinguir e tratar três falhas da integração: tempo esgotado, erro do
  serviço e resposta inválida, cada uma com mensagem clara ao vendedor.
- **FR-024**: Em caso de falha, o pedido MUST ficar registrado como não concluído, com o número de
  tentativas e a última mensagem de erro, sem número do ERP e sem nenhum dado parcial inconsistente.
- **FR-025**: O vendedor MUST poder tentar novamente após uma falha; a nova tentativa MUST
  reaproveitar o mesmo registro de pedido e a mesma referência enviada ao ERP.
- **FR-026**: Enquanto uma solicitação de pedido está em andamento, a tela MUST impedir novo envio
  e indicar "Gerando pedido…".
- **FR-027**: A integração com o ERP MUST ser simulada e permitir escolher o comportamento (sucesso,
  tempo esgotado, erro, resposta inválida) para demonstração e testes.

**Estados de interface**

- **FR-028**: Todas as telas (listagem, detalhe, formulário) MUST tratar de forma consistente os
  estados de carregamento, erro e validação, com o mesmo padrão visual e de mensagens.
- **FR-029**: Falhas ao carregar uma tela MUST exibir mensagem compreensível com opção de tentar de
  novo; oportunidade inexistente MUST exibir "Oportunidade não encontrada".

### Key Entities *(include if feature involves data)*

- **Empresa**: organização cliente. Atributos: nome (obrigatório e único, sem diferenciar
  maiúsculas/minúsculas), data de criação. Tem várias oportunidades. É criada implicitamente pelo
  formulário de oportunidade.
- **Oportunidade**: negociação comercial com uma empresa. Atributos: título, empresa, valor,
  estágio, motivo de perda (opcional), data de fechamento, datas de criação e atualização. Tem no
  máximo um pedido.
- **Pedido**: registro do pedido enviado ao ERP para uma oportunidade ganha. Atributos: oportunidade
  (única), valor copiado na geração, situação (pendente, gerado, falhou), número do ERP (quando
  gerado), número de tentativas, última mensagem de erro, datas de criação e atualização.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um vendedor completa o fluxo "criar oportunidade → mover até Ganho → gerar pedido" em
  menos de 2 minutos, sem instruções externas.
- **SC-002**: Em 100% dos testes de repetição e simultaneidade (incluindo pelo menos 10 solicitações
  simultâneas para a mesma oportunidade), existe no máximo um pedido por oportunidade.
- **SC-003**: Em 100% dos cenários de falha simulados (tempo esgotado, erro, resposta inválida), o
  vendedor vê uma mensagem específica e os dados permanecem consistentes: nenhum pedido marcado
  como gerado sem número do ERP e nenhum pedido duplicado após a nova tentativa.
- **SC-004**: Após uma falha, uma nova tentativa com o ERP disponível conclui o pedido na primeira
  tentativa em 100% dos casos.
- **SC-005**: A listagem inicial é exibida com dados, sem indicador de carregamento, e filtros/busca
  apresentam o resultado em até 1 segundo para até 1.000 oportunidades.
- **SC-006**: 100% das telas exibem os estados de carregamento, erro e validação segundo o mesmo
  padrão.

## Assumptions

- Não há autenticação: qualquer pessoa com acesso ao sistema atua como vendedor; não há dono da
  oportunidade nem permissões.
- Há um único pipeline com os cinco estágios fixos; estágios não são configuráveis.
- Moeda única (Real); o valor não tem itens nem produtos: o pedido carrega apenas o valor total.
- O pedido é gerado por ação explícita, não automaticamente ao mover para Ganho.
- A nova tentativa após falha é manual; não há reprocessamento automático em segundo plano.
- O ERP é simulado dentro do próprio sistema; não há ERP real nem credenciais externas.
- Excluir oportunidades e empresas está fora do escopo (não foi pedido).
- A listagem é uma tabela com filtro por estágio; uma visão em colunas por estágio (somente
  leitura) só entra como diferencial, depois da entrega principal.
- Fora de escopo: autenticação, dashboards, arrastar e soltar, CI/CD, histórico de atividades,
  notas, e-mails e múltiplos pedidos por oportunidade.
- Uso em navegador de computador é o foco; a interface deve continuar utilizável em telas
  estreitas, sem otimização específica para celular.
