<!--
Sync Impact Report
- Version change: (template, sem versão) → 1.0.0
- Princípios definidos (primeira ratificação):
  I. Stack Obrigatória e Monorepo
  II. Simplicidade e Escopo Controlado
  III. Integridade do Pedido (NÃO NEGOCIÁVEL)
  IV. Integração ERP Isolada e Resiliente
  V. Testes Focados em Regras de Negócio
  VI. Commits Pequenos e Semânticos
  VII. Código Autoral
  VIII. Estados de Interface Consistentes
  IX. Documentação de Execução e Decisões
- Seções adicionadas: Restrições Técnicas e de Escopo; Fluxo de Desenvolvimento e Gates de Qualidade
- Seções removidas: nenhuma
- Templates:
  ✅ .specify/templates/plan-template.md — "Constitution Check" é derivado deste arquivo; sem alteração
  ✅ .specify/templates/spec-template.md — sem seções obrigatórias novas; sem alteração
  ✅ .specify/templates/tasks-template.md — nota adicionada: testes de regras de negócio
     (Princípios III e V) são obrigatórios, não opcionais
  ✅ .claude/skills/speckit-*/SKILL.md — sem referências desatualizadas
  ⚠ README.md — ainda não existe; deve ser criado conforme Princípio IX
- TODOs adiados: nenhum
-->

# Mini Pipeline Comercial com Integração ERP Constitution

## Core Principles

### I. Stack Obrigatória e Monorepo

- Backend MUST usar Django com PostgreSQL e expor uma API RESTful (recursos, verbos HTTP e
  códigos de status semânticos; payloads JSON).
- Frontend MUST usar React + React Router 8 + TypeScript. A primeira renderização da
  listagem de oportunidades MUST ocorrer via SSR (dados carregados no servidor, HTML
  entregue já preenchido).
- O repositório MUST ser um monorepo com as pastas `backend/` e `frontend/` na raiz.
- Trocar qualquer tecnologia desta lista é proibido; bibliotecas auxiliares são permitidas
  quando justificadas no plano.

**Justificativa**: a stack é requisito do desafio; desviar dela invalida a entrega.

### II. Simplicidade e Escopo Controlado

- A solução MUST ser a mais simples que atenda ao requisito de forma funcional e bem
  estruturada (YAGNI).
- MUST NOT ser implementado nada fora do escopo pedido: autenticação, dashboards,
  drag-and-drop, CI/CD, entre outros.
- Extras são permitidos apenas como diferencial, somente após a entrega principal estar
  completa e testada, e sem aumentar o risco ou a complexidade dela.
- Toda abstração adicional (camadas, padrões, bibliotecas) MUST resolver um problema
  concreto registrado no plano; caso contrário, é removida.

**Justificativa**: o avaliador mede qualidade e decisões, não volume de funcionalidades.

### III. Integridade do Pedido (NÃO NEGOCIÁVEL)

- Uma oportunidade MUST gerar no máximo um pedido, inclusive sob requisições repetidas
  ou concorrentes.
- A garantia MUST existir no banco de dados por restrição de unicidade (ex.: `unique` na
  referência à oportunidade); validações na aplicação são complementares, nunca a única
  proteção.
- A violação da restrição MUST ser tratada e convertida em resposta previsível da API
  (ex.: devolver o pedido existente ou `409 Conflict`), nunca em erro 500.
- MUST existir teste automatizado cobrindo a tentativa de pedido duplicado, incluindo o
  cenário de requisições repetidas.

**Justificativa**: pedido duplicado gera prejuízo real e é a regra central do desafio.

### IV. Integração ERP Isolada e Resiliente

- A integração com o ERP MUST ser simulada e ficar atrás de uma interface própria
  (cliente/serviço), de modo que o restante do código não conheça detalhes do simulador.
- As falhas MUST ser tratadas explicitamente e de forma distinta: timeout, erro do
  serviço e resposta inválida.
- Uma falha MUST NOT deixar dados inconsistentes: operações locais dependentes do ERP
  MUST ser transacionais ou ter estado explícito (ex.: status de sincronização) que
  permita identificar e repetir a operação.
- O simulador MUST permitir provocar cada tipo de falha de forma determinística, para
  uso em testes e demonstração.

**Justificativa**: integrações externas falham; o valor está em como o sistema reage.

### V. Testes Focados em Regras de Negócio

- Cobertura total NÃO é objetivo; as regras de negócio importantes MUST ser testadas.
- São obrigatórios: teste de pedido duplicado (Princípio III) e testes dos cenários de
  falha do ERP (Princípio IV).
- Testes MUST rodar contra PostgreSQL quando dependerem de restrições do banco.
- Os testes MUST poder ser executados com um único comando documentado no README.

**Justificativa**: testes onde o risco está, sem custo desproporcional.

### VI. Commits Pequenos e Semânticos

- Cada commit MUST representar uma única unidade lógica de trabalho e deixar o projeto
  em estado funcional.
- Mensagens MUST seguir Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`,
  `refactor:`, `chore:`), com escopo quando útil (ex.: `feat(backend): ...`).
- Commits MUST ser frequentes; commits gigantes ou genéricos ("ajustes", "wip") são
  proibidos no histórico final.

**Justificativa**: o histórico de commits é critério explícito de avaliação.

### VII. Código Autoral

- Todo código MUST ser autoral. É proibido copiar trechos de repositórios de terceiros.
- Projetos de referência (ex.: Odoo, Twenty) servem apenas para estudo de conceitos e
  fluxos; nenhuma estrutura ou trecho deles é transcrito.
- Documentação oficial das bibliotecas usadas pode ser seguida como guia de uso da API.

**Justificativa**: a avaliação mede a capacidade do candidato, não de terceiros.

### VIII. Estados de Interface Consistentes

- Toda tela MUST tratar os estados de carregamento, erro e validação de forma
  consistente, usando os mesmos componentes/padrões em todo o frontend.
- Erros de validação da API MUST ser exibidos junto aos campos correspondentes; erros
  gerais (incluindo falhas do ERP) MUST ter mensagem compreensível ao usuário.
- Ações que disparam requisições MUST impedir envio duplicado enquanto pendentes
  (ex.: botão desabilitado), sem substituir a garantia do Princípio III.

**Justificativa**: a experiência consistente demonstra maturidade de frontend.

### IX. Documentação de Execução e Decisões

- O README na raiz MUST conter: pré-requisitos, instruções para subir backend, frontend e
  banco, como rodar os testes e variáveis de ambiente necessárias.
- O README MUST explicar brevemente as principais decisões técnicas (ex.: garantia de
  unicidade do pedido, desenho da integração ERP, estratégia de SSR) e seus trade-offs.

**Justificativa**: o avaliador precisa executar o projeto e entender as decisões sem
ajuda do autor.

## Restrições Técnicas e de Escopo

- Configurações sensíveis (credenciais do banco, URLs) MUST vir de variáveis de ambiente,
  com um arquivo de exemplo (`.env.example`) versionado.
- O ambiente local SHOULD ser reproduzível com o mínimo de passos (ex.: PostgreSQL via
  Docker Compose), desde que isso não conflite com o Princípio II.
- Contratos da API (endpoints, payloads, códigos de erro) MUST ser definidos no plano antes
  da implementação e mantidos coerentes entre backend e frontend (tipos TypeScript).

## Fluxo de Desenvolvimento e Gates de Qualidade

- Fluxo Spec Kit: especificação → plano → tarefas → implementação. Cada plano MUST passar
  pelo "Constitution Check" contra os princípios acima antes da implementação.
- Uma funcionalidade só é considerada concluída quando: os testes obrigatórios passam,
  os estados de interface (Princípio VIII) estão tratados e o commit segue o Princípio VI.
- Antes da entrega final: README revisado, histórico de commits limpo e nenhum item fora
  de escopo que comprometa a entrega principal.

## Governance

- Esta constituição prevalece sobre qualquer outra prática ou preferência do projeto.
- Emendas MUST ser registradas neste arquivo com atualização do Sync Impact Report, da
  versão e da data, e commitadas como `docs: amend constitution to vX.Y.Z (...)`.
- Versionamento semântico: MAJOR para remoção ou redefinição incompatível de princípios;
  MINOR para novo princípio/seção ou expansão material; PATCH para clarificações.
- Toda complexidade que viole um princípio MUST ser justificada na tabela "Complexity
  Tracking" do plano; sem justificativa, a violação é rejeitada.
- A conformidade é verificada em cada `/speckit-plan` (Constitution Check) e revisada
  antes da entrega final.

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29
