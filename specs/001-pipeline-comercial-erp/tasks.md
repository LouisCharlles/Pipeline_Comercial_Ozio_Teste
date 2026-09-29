---

description: "Lista de tarefas da feature Mini Pipeline Comercial com Integração ERP"
---

# Tasks: Mini Pipeline Comercial com Integração ERP

**Input**: documentos de design em `specs/001-pipeline-comercial-erp/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md),
[contracts/ui-rotas.md](./contracts/ui-rotas.md), [quickstart.md](./quickstart.md)

**Tests**: incluídos. A constituição (Princípios III e V) torna **obrigatórios** os testes de
pedido duplicado e de falhas do ERP. O plano (research R12) também pede testes de transições e
de contrato dos endpoints. Em cada história, os testes são escritos **antes** da implementação e
precisam falhar primeiro.

**Organization**: tarefas agrupadas por história de usuário. A ordem segue a prioridade da spec:
US1 (P1), US2 (P1), US3 (P2), US4 (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história a que a tarefa pertence (US1…US4)

## Convenções para quem executa

- Os caminhos são relativos à raiz do repositório.
- Campos, códigos de erro e mensagens MUST seguir exatamente [contracts/api.md](./contracts/api.md)
  e [data-model.md](./data-model.md). As telas seguem
  [contracts/ui-rotas.md](./contracts/ui-rotas.md).
- Todo código é autoral (Princípio VII). O protótipo do Figma Make é só referência visual.
- **Commits** (Princípio VI): ao fim de cada bloco marcado com **Commit**, faça um commit com a
  mensagem sugerida (Conventional Commits). O projeto MUST estar funcionando em cada commit.
  Commits menores que os sugeridos são bem-vindos.
- Os testes do backend rodam com `make test`, que sobe o PostgreSQL do compose e cria o
  `.venv` sozinho se for preciso (Docker precisa estar rodando).

---

## Phase 1: Setup (infraestrutura compartilhada)

**Purpose**: esqueleto do monorepo, banco, backend Django e frontend React Router 8 rodando
vazios.

- [X] T001 Criar `.gitignore` na raiz ignorando `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.env` (mas não `.env.example`), `node_modules/`, `frontend/build/`, `frontend/.react-router/`
- [X] T002 [P] Criar `docker-compose.yml` na raiz com um único serviço `db`: imagem `postgres:16`, `POSTGRES_DB=pipeline`, `POSTGRES_USER=pipeline`, `POSTGRES_PASSWORD=pipeline`, porta `5432:5432`, volume nomeado `pgdata` e healthcheck `pg_isready -U pipeline`
- [X] T003 [P] Criar `backend/requirements.txt` com `Django>=5.2,<5.3`, `djangorestframework>=3.17,<3.18`, `psycopg[binary]>=3.2`, `pytest>=8`, `pytest-django>=4.9`
- [X] T004 Gerar o projeto Django em `backend/` (`django-admin startproject config backend`) e o app `comercial` (`python manage.py startapp comercial`). Remover `admin.py` e `tests.py` do app e remover a rota `admin/` de `config/urls.py`; criar `backend/comercial/services/__init__.py` e `backend/erp/__init__.py`
- [X] T005 Configurar `backend/config/settings.py` lendo tudo de `os.environ`, com padrões iguais aos do compose: `DJANGO_SECRET_KEY` (padrão inseguro de dev), `DJANGO_DEBUG` (padrão `true`), `DJANGO_ALLOWED_HOSTS` (padrão `localhost,127.0.0.1`), `DATABASES` PostgreSQL via `POSTGRES_DB/USER/PASSWORD/HOST/PORT`; `INSTALLED_APPS` exatamente com `django.contrib.contenttypes`, `django.contrib.auth` (o DRF importa os dois), `django.contrib.staticfiles`, `rest_framework` e `comercial`, removendo `admin`, `sessions` e `messages`; `MIDDLEWARE` só com `SecurityMiddleware`, `CommonMiddleware` e `XFrameOptionsMiddleware` (sem sessão, CSRF, autenticação e mensagens, já que a API não tem login e só recebe chamadas do servidor Node); `TEMPLATES` com `context_processors` vazios (sem `auth`/`messages`); `LANGUAGE_CODE="pt-br"`, `TIME_ZONE="America/Sao_Paulo"`, `USE_TZ=True`; `REST_FRAMEWORK` com somente `JSONRenderer`/`JSONParser`, `DEFAULT_AUTHENTICATION_CLASSES=[]`, `DEFAULT_PERMISSION_CLASSES=["rest_framework.permissions.AllowAny"]`, `UNAUTHENTICATED_USER=None` e `EXCEPTION_HANDLER="comercial.erros.tratar_excecao"`; settings próprios `ERP_MODO` (padrão `sucesso`), `ERP_LATENCIA_MS` (int, padrão `0`) e `ERP_TIMEOUT_SEGUNDOS` (int, padrão `5`); `LOGGING` básico no console
- [X] T006 [P] Criar `backend/.env.example` com todas as variáveis do T005 e comentários curtos (valores do compose; `ERP_MODO` = `sucesso|timeout|erro|resposta_invalida`)
- [X] T007 [P] Criar `backend/pytest.ini` com `DJANGO_SETTINGS_MODULE = config.settings`, `testpaths = tests`, `python_files = test_*.py` e `addopts = -q`
- [X] T008 [P] Criar `frontend/package.json` (`"type": "module"`, `"private": true`, `"engines": {"node": ">=22.22"}`) com dependências `react-router@^8`, `@react-router/node@^8`, `@react-router/serve@^8`, `react@^19.2.7`, `react-dom@^19.2.7`, `isbot` e devDependencies `@react-router/dev@^8`, `vite@^7`, `typescript@^5`, `@types/react`, `@types/react-dom`, `@types/node`, `tailwindcss@^4`, `@tailwindcss/vite@^4`; scripts `dev: react-router dev`, `build: react-router build`, `start: react-router-serve ./build/server/index.js`, `typecheck: react-router typegen && tsc`. Rodar `npm install` para gerar `frontend/package-lock.json`
- [X] T009 Criar `frontend/react-router.config.ts` (`ssr: true`, `appDirectory: "app"`), `frontend/vite.config.ts` (plugins `tailwindcss()` e `reactRouter()`, `server.port: 5173`) e `frontend/tsconfig.json` (`strict`, `moduleResolution: "bundler"`, `jsx: "react-jsx"`, `types: ["node", "vite/client"]`, `rootDirs: [".", "./.react-router/types"]`, `include` com `app/**/*`, `.react-router/types/**/*` e os arquivos de config, `paths: {"~/*": ["./app/*"]}`, `noEmit: true`)
- [X] T010 [P] Criar `frontend/.env.example` com `API_URL=http://localhost:8000/api` e `frontend/app/app.css` com `@import "tailwindcss";` e fundo `bg-slate-50` no `body` (via `@layer base`)
- [X] T011 Criar `Makefile` na raiz com os alvos:
  - `db`: `docker compose up -d --wait db` (espera o healthcheck ficar saudável);
  - `venv`: cria `backend/.venv` se faltar e roda `pip install -r requirements.txt`; é idempotente e usa `backend/requirements.txt` como pré-requisito para reinstalar só quando o arquivo mudar;
  - `backend`: depende de `db` e `venv`; carrega `backend/.env` se existir (com `set -a`), roda `migrate` e `runserver 0.0.0.0:8000`;
  - `seed`: depende de `db` e `venv`; roda `manage.py popular_demo`;
  - `frontend`: roda `npm install` e `npm run dev`, exportando `API_URL` de `frontend/.env` se existir;
  - `test`: **depende de `db` e `venv`** e roda `cd backend && .venv/bin/pytest`, para funcionar num clone limpo com um único comando (Princípio V);
  - `typecheck`: roda `npm install` se `frontend/node_modules` faltar e depois `cd frontend && npm run typecheck`;
  - `reset-db`: depende de `db` e `venv`; roda `manage.py flush --no-input`.

  Declarar todos os alvos (exceto o de arquivo do `venv`) como `.PHONY`.

**Commit**: `chore: scaffold monorepo with django backend, react router 8 frontend and postgres`

---

## Phase 2: Foundational (pré-requisitos bloqueantes)

**Purpose**: modelos, migração, tratamento de erro da API, cliente HTTP do frontend,
componentes de UI e layout. Tudo isso é compartilhado por todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase terminar.

### Backend

- [X] T012 Implementar `Empresa`, `Oportunidade` (com `Estagio(TextChoices)`: `LEAD`, `CONTATO`, `PROPOSTA`, `GANHO`, `PERDIDO`; constantes `ESTAGIOS_ABERTOS` e `ESTAGIOS_FINAIS`) e `Pedido` (com `StatusPedido`: `PENDENTE`, `GERADO`, `FALHOU`; e `TipoErroErp`: `""`, `TEMPO_ESGOTADO`, `ERRO_SERVICO`, `RESPOSTA_INVALIDA`) em `backend/comercial/models.py`, com **todos** os campos, `related_name`, `on_delete=PROTECT`, índice em `estagio`, `ordering = ["-atualizado_em", "-id"]` e todas as `UniqueConstraint`/`CheckConstraint` listadas em [data-model.md](./data-model.md). Destaques: `UniqueConstraint(Lower("nome"))` em Empresa; `OneToOneField` em `Pedido.oportunidade`; `referencia_externa` e `numero_erp` únicos; checks de `valor`, `fechado_em` × estágio e `numero_erp`/`gerado_em` × status
- [X] T013 Gerar a migração inicial em `backend/comercial/migrations/0001_initial.py` (`makemigrations comercial`) e conferir que `migrate` roda sem erro no PostgreSQL do compose
- [X] T014 Implementar `backend/comercial/erros.py` com:
  - a base `ErroDominio(Exception)`, com os atributos `codigo`, `mensagem`, `status_http` e `pedido=None`;
  - as subclasses `NaoEncontrado` (404), `TransicaoInvalida` (409), `EstagioBloqueado` (409), `EstagioInvalido` (409), `ValorObrigatorio` (409), `ErpTempoEsgotadoErro` (504, `erp_tempo_esgotado`), `ErpErroServicoErro` (502, `erp_erro_servico`) e `ErpRespostaInvalidaErro` (502, `erp_resposta_invalida`), com as mensagens em pt-BR de research R5;
  - a função `tratar_excecao(exc, context)`, que monta o corpo `{codigo, mensagem, campos?, pedido?}` do contrato: `ErroDominio` → corpo próprio (serializando `pedido` com `PedidoSerializer`, importado dentro da função); `ValidationError` do DRF → 400 `validacao`, com `mensagem="Corrija os campos destacados."` e `campos` normalizado para `dict[str, list[str]]`; `Http404`/`NotFound` → 404 `nao_encontrado` com "Oportunidade não encontrada."; `ParseError` → 400 `validacao`; qualquer outra exceção → registra no log com `logger.exception` e devolve 500 `erro_interno` com "Erro inesperado. Tente novamente."
- [X] T015 [P] Criar `backend/comercial/urls.py` (lista vazia por enquanto) e incluí-lo em `backend/config/urls.py` sob o prefixo `api/`
- [X] T016 [P] Criar `backend/tests/conftest.py` com as fixtures `api` (`rest_framework.test.APIClient`), `criar_empresa(nome="Acme")` e `criar_oportunidade(titulo="Op", empresa=None, valor=Decimal("1000.00"), estagio="LEAD", motivo_perda="")`. Essa última preenche `fechado_em=timezone.now()` quando o estágio é final, para respeitar a check constraint. Criar também a fixture `espiao_erp(monkeypatch)`, usada pelos testes da US2 (T039 e T040). Ela importa `erp.cliente.obter_cliente_erp` **dentro** da fixture (o módulo ainda não existe nesta fase) e cria um objeto que delega `criar_pedido` ao cliente real, contando as chamadas em `espiao.chamadas` e permitindo forçar uma exceção com `espiao.levantar = RuntimeError(...)`. Em seguida, aplica `monkeypatch.setattr("comercial.services.pedidos.obter_cliente_erp", lambda: espiao)` e devolve o espião
- [X] T017 Implementar o comando `backend/comercial/management/commands/popular_demo.py` (criar os `__init__.py` de `management/` e `commands/`), que apaga os dados existentes e cria as 4 empresas e as 12 oportunidades do protótipo (Acme Logística, Nova Alimentos, Horizonte Tech, Grupo Aurora), com os mesmos títulos, valores e estágios. Pedidos: GERADO `ERP-1042` para "Fornecimento de Alimentos Premium" (**em GANHO**, corrigindo o protótipo; research R14), GERADO `ERP-0987` e `ERP-1105` nas outras duas ganhas com pedido, e FALHOU (2 tentativas, `TEMPO_ESGOTADO`, "ERP não respondeu em 5s") em "Gestão de Frotas Integrada". Motivo de perda em "Plataforma de Vendas Online". Preencher `referencia_externa="OPP-{id}"`, `gerado_em` e `fechado_em` coerentes com as constraints

### Frontend

- [X] T018 [P] Criar `frontend/app/features/oportunidades/types.ts` espelhando [contracts/api.md](./contracts/api.md): `Estagio`, `StatusPedido`, `TipoErroErp`, `Empresa`, `Pedido`, `OportunidadeResumo`, `Oportunidade`, `ListagemOportunidades` (`resultados`, `contagens: Record<"TODOS" | Estagio, number>`, `total_cadastradas`), `ErroApi` (`codigo`, `mensagem`, `campos?`, `pedido?`) e `ResultadoAcao` (`{ ok: true } | ({ ok: false } & ErroApi & { valores?: Record<string, string> })`); constantes `ESTAGIOS` (ordem da barra) e `ESTAGIOS_ABERTOS`
- [X] T019 [P] Criar `frontend/app/features/oportunidades/api.server.ts`, com a base `process.env.API_URL ?? "http://localhost:8000/api"` e uma função interna `requisitar<T>(metodo, caminho, corpo?)` que devolve `{ ok: true; status: number; dados: T } | { ok: false; status: number; erro: ErroApi }`. Falha de rede ou corpo que não é JSON → `{ ok: false, status: 503, erro: { codigo: "rede", mensagem: "Não foi possível falar com o servidor." } }`. Funções exportadas: `listarOportunidades({ estagio?, q? })`, `obterOportunidade(id)`, `criarOportunidade(dados)`, `editarOportunidade(id, dados)`, `mudarEstagio(id, estagio, motivoPerda?)`, `gerarPedido(id)` e `sugerirEmpresas(q)`
- [X] T020 [P] Criar `frontend/app/features/oportunidades/erros.ts` com `mensagemDeErro(erro: ErroApi): string`, que mapeia cada `codigo` do contrato e `rede` para o texto de research R5 / contracts; código desconhecido → `erro.mensagem`, ou "Erro inesperado. Tente novamente."
- [X] T021 [P] Criar `frontend/app/features/oportunidades/formato.ts` com `formatarMoeda(valor: string | null)` (BRL `pt-BR`, sem casas decimais, `null` → "—"), `formatarData(iso)` (`dd/mm/aaaa`), `formatarDataHora(iso)` e `ROTULO_ESTAGIO`. Todos os `Intl.DateTimeFormat` MUST usar `timeZone: "America/Sao_Paulo"` fixo, e os formatadores MUST ser criados uma vez no módulo: servidor (SSR) e navegador precisam produzir o mesmo texto, para não haver erro de hidratação nem data trocada perto da meia-noite (`LEAD` → "Lead" etc.)
- [X] T022 [P] Criar os componentes base, um arquivo cada, inspirados no protótipo (classes Tailwind `slate`/`blue`, cantos `rounded-lg`/`rounded-xl`):
  - `frontend/app/components/ui/Button.tsx`: variantes `primary`, `secondary` e `danger`; tamanhos `sm` e `md`; suporte a `disabled`.
  - `frontend/app/components/ui/Alert.tsx`: variantes `error`, `info` e `success`, com `role="alert"` em `error`.
  - `frontend/app/components/ui/FormField.tsx`: exporta `FormField` (label, marcador de obrigatório, `error` exibido abaixo com `id` ligado por `aria-describedby`), `Input` e `Select`, com borda vermelha em erro.
  - `frontend/app/components/ui/Modal.tsx`: overlay, `role="dialog"`, `aria-modal`, título, descrição, `children` para campos extras, botões Cancelar e Confirmar com variante configurável, fecha com Esc.
- [X] T023 [P] Criar os componentes de estado:
  - `frontend/app/components/ui/StageBadge.tsx`: cores por estágio iguais às do protótipo; Ganho em verde, Perdido em vermelho.
  - `frontend/app/components/ui/EmptyState.tsx`: ícone, título, descrição e ação opcional.
  - `frontend/app/components/ui/PendingBar.tsx`: barra fina fixa no topo, animada, visível quando `useNavigation().state !== "idle"`.
  - `frontend/app/components/ui/ErrorState.tsx`: mensagem "Não foi possível carregar" com a descrição "Verifique sua conexão e tente novamente" e o botão "Tentar novamente", que chama `useRevalidator().revalidate()`.
  - `frontend/app/components/ui/NaoEncontrado.tsx`: "Oportunidade não encontrada" + link "Voltar para oportunidades" (`/oportunidades`).
- [X] T024 Criar `frontend/app/root.tsx` com:
  - `Layout`: `<html lang="pt-BR">`, `Meta`, `Links`, `ScrollRestoration`, `Scripts`, import de `app.css`;
  - o header do protótipo: logo, "Pipeline Comercial" com link para `/oportunidades`, e botão/link "Nova oportunidade" para `/oportunidades/nova`;
  - `<PendingBar />`;
  - `<main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">` com `<Outlet />`;
  - `ErrorBoundary` raiz usando `isRouteErrorResponse`: 404 → `NaoEncontrado`; outros casos → `ErrorState`.
- [X] T025 Criar `frontend/app/routes.ts` com `index("routes/home.tsx")` e as rotas de [contracts/ui-rotas.md](./contracts/ui-rotas.md) (`oportunidades`, `oportunidades/nova`, `oportunidades/:id`, `oportunidades/:id/editar`, `empresas/sugestoes`), e `frontend/app/routes/home.tsx`, cujo loader faz `redirect("/oportunidades")`. Nesta fase, as outras rotas podem ser arquivos mínimos que só exportam um componente com o título, para o typecheck passar

**Checkpoint**: `make db && make backend` sobe a API com a migração aplicada; `make seed` popula
o banco; `make frontend` abre o layout; `make typecheck` passa.

**Commit** (sugestão em três): `feat(backend): add empresa, oportunidade and pedido models with db
constraints` · `feat(backend): add domain error handling and demo seed command` ·
`feat(frontend): add api client, formatting helpers, ui components and root layout`

---

## Phase 3: User Story 1 - Cadastrar e consultar oportunidades (Priority: P1) 🎯 MVP

**Goal**: o vendedor cria uma oportunidade (com empresa por nome + sugestões), vê a oportunidade
na listagem, abre o detalhe e edita título, empresa e valor.

**Independent Test**: criar uma oportunidade pelo formulário, vê-la na listagem, abrir o detalhe
e editar o título; os dados alterados aparecem na listagem e no detalhe. Acessar
`/oportunidades/99999` mostra "Oportunidade não encontrada".

### Tests for User Story 1 ⚠️ (escrever antes e ver falhar)

- [X] T026 [P] [US1] Escrever `backend/tests/test_oportunidades_api.py` cobrindo:
  - `POST /api/oportunidades`:
    - cria com 201 e estágio padrão `LEAD`;
    - reaproveita a empresa ao receber `"  acme LOGÍSTICA "` quando "Acme Logística" existe, sem criar outra;
    - cria a empresa quando o nome é novo;
    - aceita `valor` vazio ou `null`;
    - devolve 400 `validacao` com `campos.titulo` quando falta o título, `campos.empresa` quando falta a empresa, `campos.valor` para valor negativo e para `"abc"`, e `campos.estagio` para `"GANHO"` e para `"PERDIDO"`.
  - `GET /api/oportunidades/{id}`: devolve 200 com `empresa {id, nome}` e `pedido: null`; id inexistente → 404 `{codigo: "nao_encontrado"}`.
  - `PATCH`: altera `titulo`, `empresa` (reaproveitando ou criando) e `valor`, mantendo o estágio; `estagio` no corpo → 400.
  - `GET /api/oportunidades` (sem filtros): devolve `resultados`, `contagens` e `total_cadastradas`, com os campos de `OportunidadeResumo`.
  - `GET /api/empresas?q=`: `q` vazio ou só espaços → `[]`; `icontains` ordenado por nome; no máximo 10 resultados.

### Implementation for User Story 1

- [X] T027 [P] [US1] Implementar `backend/comercial/services/empresas.py`:
  - `normalizar_nome(nome) -> str`: aplica `strip`.
  - `obter_ou_criar_por_nome(nome) -> Empresa`: faz `nome__iexact`; se não encontrar, cria dentro de `transaction.atomic()` (savepoint); se a criação levantar `IntegrityError`, busca de novo por `nome__iexact`.
  - `sugerir(q, limite=10) -> QuerySet`: `q` vazio → `none()`.
- [X] T028 [US1] Implementar `backend/comercial/serializers.py`:
  - `EmpresaSerializer` (`id`, `nome`);
  - `PedidoSerializer` (todos os campos do contrato);
  - `OportunidadeSerializer` (detalhe, com `empresa` e `pedido` aninhados; o `pedido` vem do reverse one-to-one e é `null` se não existir);
  - `OportunidadeResumoSerializer` (com `pedido_status` e `pedido_numero_erp`);
  - `OportunidadeEntradaSerializer`, com `titulo` (`CharField`, `max_length=200`, trim), `empresa` (`CharField`, `max_length=200`, trim), `valor` (`DecimalField(max_digits=14, decimal_places=2, min_value=0, allow_null=True, required=False)`, com string vazia convertida em `None` em `to_internal_value`) e `estagio` (`ChoiceField`, apenas os estágios abertos, padrão `LEAD`). Todas as mensagens `required`, `blank`, `invalid`, `min_value` e `invalid_choice` ficam exatamente como em contracts/api.md. `create()` e `update()` usam `obter_ou_criar_por_nome`. No `update`, o `validate` recusa `estagio` presente em `initial_data` com o erro de campo "Altere o estágio pelo detalhe da oportunidade.". O `DecimalField` MUST serializar como string com 2 casas.
- [X] T029 [US1] Implementar em `backend/comercial/views.py`:
  - `OportunidadeListaView` (APIView): o `GET` usa `select_related("empresa", "pedido")` e devolve `resultados` (ordenação padrão), `contagens` (uma consulta agregada `values("estagio").annotate(Count("id"))`, completando os estágios ausentes com 0 e somando `TODOS`) e `total_cadastradas`; o `POST` valida com `OportunidadeEntradaSerializer` e devolve 201 com `OportunidadeSerializer`.
  - `OportunidadeDetalheView`: `GET` e `PATCH`; id inexistente → `NaoEncontrado`.
  - `EmpresaSugestoesView`: `GET ?q=`.

  Registrar as rotas `oportunidades`, `oportunidades/<int:pk>` e `empresas` em `backend/comercial/urls.py`. Rodar `make test`: T026 deve passar.
- [X] T030 [P] [US1] Criar `frontend/app/routes/empresas.sugestoes.ts` (resource route): o loader lê `q` e devolve `Response.json(await sugerirEmpresas(q))`; em caso de erro, devolve `[]`
- [X] T031 [P] [US1] Criar `frontend/app/features/oportunidades/components/EmpresaInput.tsx`: `Input` de texto com `name="empresa"`, `autoComplete="off"`, `defaultValue` e `error`, usando `useFetcher<Empresa[]>()`. Ao digitar, faz `fetcher.load("/empresas/sugestoes?q=...")` com debounce de 250 ms. Mostra uma lista suspensa (`role="listbox"`) com as sugestões, navegável com ↑/↓, Enter e Esc; clicar ou pressionar Enter preenche o campo e fecha a lista. Sem sugestões, nada aparece. O texto livre continua válido (FR-003)
- [X] T032 [US1] Criar `frontend/app/features/oportunidades/components/OportunidadeForm.tsx`: um `<Form method="post" noValidate>` com as props `valores` (`titulo`, `empresa`, `valor`, `estagio`), `campos` (erros por campo), `erroGeral?`, `mostrarEstagio: boolean`, `rotuloEnviar` e `rotuloEnviando`. Campos:
  - Título (obrigatório);
  - Empresa (`EmpresaInput`, obrigatório);
  - Valor (R$) com prefixo "R$", `inputMode="decimal"`, `type="text"`;
  - Estágio (`Select` com Lead, Contato e Proposta, só se `mostrarEstagio`).

  O `<Alert variant="error">` com `erroGeral` fica no topo. Durante o envio (`useNavigation().state === "submitting"`), os campos e os botões ficam desabilitados e o botão principal mostra spinner + `rotuloEnviando`. Botão "Cancelar" leva para `/oportunidades` (Link). Os valores digitados persistem após um erro, via `defaultValue` + `key` que muda a cada resposta da action.
- [X] T033 [US1] Implementar `frontend/app/routes/oportunidades.nova.tsx`:
  - `action`: lê o `formData` e chama `criarOportunidade`. Sucesso → `redirect(`/oportunidades/${id}`)`. Erro → `data({ ok: false, ...erro, valores }, { status: erro.status })`.
  - Componente: título "Nova oportunidade" + subtítulo do protótipo, `OportunidadeForm` com `mostrarEstagio`, "Criar oportunidade"/"Criando…" e `campos`/`erroGeral` vindos de `useActionData` (o `erroGeral` usa `mensagemDeErro` quando `codigo !== "validacao"`).
  - `meta` com o título da página.
- [X] T034 [P] [US1] Criar `frontend/app/features/oportunidades/components/TabelaOportunidades.tsx`: tabela do protótipo com as colunas Título, Empresa, Valor, Estágio (`StageBadge`) e Pedido (selo verde "Pedido #{numero}" para `GERADO`; selo vermelho "Falha no pedido" para `FALHOU`; vazio sem pedido). A linha inteira é clicável e o título é um `<Link>` para `/oportunidades/{id}`, acessível por teclado. Em telas estreitas, o contêiner tem `overflow-x-auto`
- [X] T035 [US1] Implementar `frontend/app/routes/oportunidades._index.tsx` (versão inicial, sem filtros):
  - `loader` no servidor: chama `listarOportunidades({})`; em caso de erro, `throw data(erro, { status })`.
  - Componente: título "Oportunidades", `TabelaOportunidades` e, quando `total_cadastradas === 0`, `EmptyState` "Nenhuma oportunidade ainda" + botão "Nova oportunidade".
  - `ErrorBoundary` → `ErrorState`.
  - `meta`.
- [X] T036 [US1] Implementar `frontend/app/routes/oportunidades.$id.tsx` (versão inicial):
  - `loader`: `obterOportunidade(params.id)`; 404 → `throw data(null, { status: 404 })`; outros erros → `throw data(erro, { status })`.
  - Layout em grade `md:grid-cols-[1fr_320px]` (uma coluna no celular):
    - link "Voltar";
    - card de cabeçalho: título, `StageBadge`, empresa, valor formatado, bloco "Motivo da perda" quando `PERDIDO` com motivo, e rodapé "Criado em", "Atualizado em" e "Fechado em" (só se houver);
    - botão/link "Editar" para `/oportunidades/{id}/editar`;
    - as áreas da barra de estágios (US3) e do card Pedido (US2) ficam vazias por ora.
  - `ErrorBoundary`: 404 → `NaoEncontrado`; demais erros → `ErrorState`.
  - `meta` com o título da oportunidade.
- [X] T037 [US1] Implementar `frontend/app/routes/oportunidades.$id.editar.tsx`:
  - `loader`: igual ao do detalhe.
  - `action`: `editarOportunidade(id, { titulo, empresa, valor })`. Sucesso → `redirect` para o detalhe. Erro → `data({ ok: false, ...erro, valores }, { status })`.
  - Componente: título "Editar oportunidade", `OportunidadeForm` sem estágio, pré-preenchido com os dados do loader (valor convertido para texto sem formatação), "Salvar alterações"/"Salvando…" e "Cancelar" levando ao detalhe.
  - `ErrorBoundary` como o do detalhe.

**Checkpoint**: roteiro 2 do [quickstart.md](./quickstart.md) funciona ponta a ponta; `make test`
e `make typecheck` passam.

**Commit** (sugestão em três): `test(backend): cover oportunidade create, detail, edit and empresa
suggestions` · `feat(backend): add oportunidade and empresa endpoints` · `feat(frontend): add
oportunidade list, create, detail and edit screens`

---

## Phase 4: User Story 2 - Gerar pedido no ERP sem duplicidade (Priority: P1)

**Goal**: em Ganho, "Gerar pedido" cria no máximo um pedido no ERP simulado, com tratamento
distinto para tempo esgotado, erro e resposta inválida, e "Tentar novamente" sobre o mesmo
registro.

**Independent Test**: com uma oportunidade em Ganho (via `make seed` ou fixture), acionar "Gerar
pedido" várias vezes, inclusive 10 vezes em simultâneo e em cada `ERP_MODO`. No fim, existe no
máximo um pedido e o card mostra o estado real (quickstart, roteiros 4, 5 e 6).

### Tests for User Story 2 ⚠️ (OBRIGATÓRIOS — Princípios III e V)

- [X] T038 [P] [US2] Escrever `backend/tests/test_erp_cliente.py`:
  - `ErpSimulado` em modo `sucesso` devolve `RespostaErp(numero="ERP-…")`;
  - a mesma `referencia` devolve o mesmo número (deduplicação);
  - os modos `timeout`, `erro` e `resposta_invalida` levantam `ErpTempoEsgotado`, `ErpErroServico` e `ErpRespostaInvalida`;
  - `validar_resposta` recusa payloads sem `numero_pedido`, com número vazio ou não-string, e com `referencia` diferente.

  Usar `settings.ERP_MODO` via fixture `settings` do pytest-django e uma fixture autouse que limpa o registro em memória do simulador.
- [X] T039 [P] [US2] Escrever `backend/tests/test_pedido_unicidade.py`:
  - `POST /api/oportunidades/{id}/pedido` em GANHO com valor devolve 201 com `status="GERADO"`, `numero_erp`, `referencia_externa="OPP-{id}"` e `valor` copiado;
  - a segunda chamada devolve 200 com o mesmo `id`, e o ERP não é chamado de novo. Conferir com a fixture `espiao_erp` (criada em T016), que injeta o espião em `comercial.services.pedidos.obter_cliente_erp`, o nome **no módulo que o usa**, e não em `erp.cliente`;
  - **concorrência**: com `@pytest.mark.django_db(transaction=True)`, 10 threads chamam `gerar_pedido` ao mesmo tempo, cada uma fechando a própria conexão no fim (`connection.close()`). Resultado esperado: exatamente 1 linha em `Pedido`, um único `criado=True`, e o espião do ERP chamado 1 vez;
  - **última defesa**: com um pedido GERADO já no banco, forçar `IntegrityError` no caminho de criação (por `monkeypatch` da função interna de criação em `comercial.services.pedidos`); a resposta deve ser 200 com o pedido existente, nunca 500.
- [X] T040 [P] [US2] Escrever `backend/tests/test_pedido_falhas_erp.py`, parametrizado por modo:
  - `timeout` → 504 `erp_tempo_esgotado`; `erro` → 502 `erp_erro_servico`; `resposta_invalida` → 502 `erp_resposta_invalida`. Em todos, o corpo traz `pedido.status="FALHOU"`, `tentativas=1`, `numero_erp=null` e o `ultimo_erro_tipo` certo, e o banco fica com 1 linha FALHOU e sem `gerado_em`.
  - Retry: trocar para `sucesso` e chamar de novo → 201, **mesmo** `id` e `referencia_externa`, `tentativas=2`, `status="GERADO"`, `ultimo_erro` vazio.
  - O retry mantém o `valor` copiado mesmo se a oportunidade for editada para outro valor entre as tentativas.
  - Oportunidade fora de GANHO → 409 `estagio_invalido`, e o ERP não é chamado.
  - GANHO com `valor` nulo ou `0` → 409 `valor_obrigatorio`, e o ERP não é chamado.
  - Id inexistente → 404.
  - **Interrupção**: o cliente levanta `RuntimeError` na 1ª tentativa → 500 `erro_interno` e **nenhuma** linha em `Pedido` (rollback). Em seguida, uma tentativa com sucesso → 201.

### Implementation for User Story 2

- [X] T041 [P] [US2] Implementar `backend/erp/erros.py` (`ErroErp` base e as subclasses `ErpTempoEsgotado`, `ErpErroServico` e `ErpRespostaInvalida`, cada uma com a mensagem técnica) e `backend/erp/cliente.py`, que contém:
  - `RespostaErp` (dataclass congelada com `numero: str`);
  - `ClienteErp` (`typing.Protocol` com `criar_pedido(referencia: str, valor: Decimal) -> RespostaErp`);
  - `validar_resposta(bruta: object, referencia: str) -> RespostaErp`, que levanta `ErpRespostaInvalida` quando o formato difere de contracts/api.md;
  - `obter_cliente_erp() -> ClienteErp`, que devolve `ErpSimulado(timeout_segundos=settings.ERP_TIMEOUT_SEGUNDOS)`.

  Nenhum código fora de `backend/erp/` pode conhecer o `ErpSimulado`.
- [X] T042 [US2] Implementar `backend/erp/simulado.py` com a classe `ErpSimulado`:
  - um registro em memória no nível da classe (`dict[referencia, numero]`, protegido por `threading.Lock`), com o método de classe `limpar()` para os testes, e um contador sequencial que começa em 2000 e gera `ERP-{n}`;
  - `criar_pedido`:
    1. dorme `settings.ERP_LATENCIA_MS` ms;
    2. lê `settings.ERP_MODO` **a cada chamada**;
    3. `timeout` → levanta `ErpTempoEsgotado(f"ERP não respondeu em {timeout}s")`;
    4. `erro` → levanta `ErpErroServico("ERP respondeu 503 Service Unavailable")`;
    5. `resposta_invalida` → monta a resposta bruta `{"referencia": referencia}`, sem número, e a passa por `validar_resposta`;
    6. `sucesso` → reaproveita o número já registrado para a referência, ou gera um novo, e passa `{"numero_pedido": numero, "referencia": referencia}` por `validar_resposta`;
    7. modo desconhecido → `ErpErroServico`.
- [X] T043 [US2] Implementar `backend/comercial/services/pedidos.py` com `gerar_pedido(oportunidade_id: int) -> tuple[Pedido, bool]`, seguindo exatamente os passos 1–9 de "Serviço `gerar_pedido`" em [data-model.md](./data-model.md):
  - Dentro do `transaction.atomic()` + `select_for_update()` da oportunidade: devolve o pedido GERADO existente com `criado=False`; valida o estágio (`EstagioInvalido`) e o valor (`ValorObrigatorio`); reaproveita o pedido FALHOU ou o cria com uma função interna `_criar_pedido(oportunidade)` (ponto de `monkeypatch` do T039); marca `PENDENTE` e soma `tentativas`; chama `obter_cliente_erp().criar_pedido(pedido.referencia_externa, pedido.valor)`. Importar com `from erp.cliente import obter_cliente_erp` no topo do módulo e chamar a função **a cada execução**, sem guardar o cliente em variável global, para que o `monkeypatch` de `comercial.services.pedidos.obter_cliente_erp` usado em T039 e T040 funcione.
  - Sucesso → grava GERADO, `numero_erp` e `gerado_em`, e limpa os erros.
  - `ErroErp` → grava FALHOU, `ultimo_erro_tipo` e `ultimo_erro`, e guarda a falha numa variável local.
  - **Depois** que o bloco atômico fecha (commit), se houve falha, levanta o `ErroDominio` correspondente (`ErpTempoEsgotadoErro` etc.) com `pedido` recarregado.
  - `IntegrityError` → busca de novo e devolve `(pedido_existente, False)`.
  - Registrar no log (`logging.getLogger(__name__)`) cada tentativa, com o resultado e a referência.
- [X] T044 [US2] Adicionar `GerarPedidoView` (`POST`, sem corpo) em `backend/comercial/views.py`, que chama `gerar_pedido` e devolve `PedidoSerializer` com 201 se `criado`, senão 200. Registrar `oportunidades/<int:pk>/pedido` em `backend/comercial/urls.py`. Rodar `make test`: T038–T040 devem passar
- [X] T045 [P] [US2] Criar `frontend/app/features/oportunidades/components/CardPedido.tsx` com as props `oportunidade`, `erro?: ErroApi` (resultado da última ação) e `ocupado: boolean`. Título "Pedido no ERP" com ícone, e os 7 estados da tabela "Card Pedido no ERP" de [contracts/ui-rotas.md](./contracts/ui-rotas.md):
  - indisponível, sem valor (com link "Editar"), pronto, enviando (spinner + "Gerando pedido…" + "Comunicando com o ERP. Aguarde."), gerado, falhou e falhou fora de Ganho;
  - o botão fica num `fetcher.Form method="post"` com `<input type="hidden" name="intent" value="gerar-pedido">`, usando `useFetcher({ key: "gerar-pedido" })`;
  - no estado falhou, a mensagem do `Alert` vem de `ultimo_erro_tipo` (mapeado para o texto de R5) e vale mesmo depois de recarregar a página;
  - um `erro` de ação que não seja do ERP (por exemplo, 409 `estagio_invalido` ou `rede`) aparece num `Alert` acima do botão, com `mensagemDeErro`.
- [X] T046 [US2] Adicionar ao `frontend/app/routes/oportunidades.$id.tsx` a `action`, que lê `intent`: `gerar-pedido` → `gerarPedido(id)`. Sucesso → `{ ok: true }`. Erro → `{ ok: false, ...erro }` **com status 200**, para que o React Router revalide o loader e o card reflita o FALHOU persistido. `intent` desconhecido → 400. Renderizar `CardPedido` na coluna direita, com `ocupado = fetcher.state !== "idle"` e `erro = fetcher.data?.ok === false ? fetcher.data : undefined`

**Checkpoint**: roteiros 4, 5 e 6 do [quickstart.md](./quickstart.md) funcionam (com a
oportunidade em Ganho vinda do seed); os testes obrigatórios passam.

**Commit** (sugestão em quatro): `test(backend): cover duplicate order prevention and erp failure
modes` · `feat(backend): add isolated erp client with deterministic simulator` ·
`feat(backend): add idempotent order generation endpoint` · `feat(frontend): add erp order card
with retry`

---

## Phase 5: User Story 3 - Mover a oportunidade entre estágios (Priority: P2)

**Goal**: no detalhe, a barra de estágios aplica mudanças entre estágios abertos com um clique e
pede confirmação para Ganho, Perdido (com motivo opcional) e reabertura. As regras são
garantidas pelo backend.

**Independent Test**: levar uma oportunidade de Lead até Ganho passando por Contato e Proposta, e
outra até Perdido e de volta a Contato; conferir o estágio no detalhe e na listagem após cada
mudança (quickstart, roteiro 3).

### Tests for User Story 3 ⚠️

- [X] T047 [P] [US3] Escrever `backend/tests/test_estagios.py`, cobrindo a tabela de transições de [data-model.md](./data-model.md) via `POST /api/oportunidades/{id}/estagio`:
  - entre abertos, nos dois sentidos: 200 com `fechado_em=null`;
  - aberto → GANHO: `fechado_em` preenchido;
  - aberto → PERDIDO com `motivo_perda`: motivo salvo;
  - PERDIDO → CONTATO: `fechado_em` e `motivo_perda` limpos;
  - PERDIDO → GANHO: 409 `transicao_invalida`, e o estágio não muda;
  - GANHO sem pedido → PROPOSTA: `fechado_em` limpo;
  - GANHO sem pedido → PERDIDO: 200;
  - GANHO com pedido GERADO → qualquer destino: 409 `estagio_bloqueado`;
  - GANHO com pedido FALHOU → PROPOSTA: 200, e o pedido FALHOU continua existindo;
  - destino igual ao atual: 200 sem alteração;
  - estágio desconhecido: 400 `validacao`;
  - `motivo_perda` ignorado para destinos diferentes de PERDIDO;
  - `motivo_perda` com mais de 500 caracteres: 400;
  - id inexistente: 404.

### Implementation for User Story 3

- [X] T048 [US3] Implementar `backend/comercial/services/estagios.py` com a tabela de transições permitidas (dicionário origem → destinos, conforme data-model) e com `mudar_estagio(oportunidade_id, destino, motivo_perda="") -> Oportunidade`, seguindo as regras 1–7 de data-model: `transaction.atomic()` + `select_for_update()`; bloqueio se existe `Pedido` GERADO (`EstagioBloqueado` com "Oportunidade com pedido gerado não pode mudar de estágio."); `TransicaoInvalida` com mensagem que cita a origem e o destino; `fechado_em` e `motivo_perda` atualizados
- [X] T049 [US3] Adicionar `MudarEstagioSerializer` (`estagio`: `ChoiceField` com todos os estágios; `motivo_perda`: `CharField(max_length=500, required=False, allow_blank=True)`, mensagens em pt-BR) em `backend/comercial/serializers.py` e `MudarEstagioView` (`POST` → `mudar_estagio` → 200 com `OportunidadeSerializer`) em `backend/comercial/views.py`. Registrar `oportunidades/<int:pk>/estagio` em `backend/comercial/urls.py`. Rodar `make test`: T047 deve passar
- [X] T050 [P] [US3] Criar `frontend/app/features/oportunidades/components/ModalEstagio.tsx`, com os modos `ganho` ("Marcar como Ganho?", texto do protótipo, botão "Confirmar como Ganho"), `perdido` ("Marcar como Perdido?", texto do protótipo, `textarea` "Motivo da perda (opcional)" com `name="motivo_perda"` e `maxLength={500}`, botão `danger` "Confirmar como Perdido") e `reabrir` ("Reabrir oportunidade?", "A oportunidade volta para {estágio}; a data de fechamento e o motivo da perda serão apagados.", botão "Reabrir"). Ao confirmar, envia o `fetcher.Form` recebido por prop com `intent=mudar-estagio`, `estagio` e, no modo perdido, `motivo_perda`
- [X] T051 [US3] Criar `frontend/app/features/oportunidades/components/BarraEstagios.tsx` (card "Estágio"), usando `useFetcher({ key: "mudar-estagio" })`:
  - Mostra cinco botões na ordem de `ESTAGIOS`, com as cores do protótipo para o estágio atual.
  - Com pedido GERADO, a barra dá lugar a `StageBadge` Ganho + "Pedido gerado — estágio bloqueado".
  - Regras de clique:
    - aberto → aberto: envia direto;
    - → GANHO: modal `ganho`;
    - → PERDIDO: modal `perdido`;
    - PERDIDO → aberto: modal `reabrir`;
    - em PERDIDO, o botão Ganho fica desabilitado, com `title` e tooltip "Reabra a oportunidade antes de marcá-la como Ganho";
    - o estágio atual não é clicável.
  - Todos os botões ficam desabilitados enquanto qualquer fetcher (`useFetchers()`) estiver ocupado, inclusive o `gerar-pedido`.
  - Um erro da action aparece em `Alert` dentro do card, via `mensagemDeErro`.
- [X] T052 [US3] Adicionar ao `frontend/app/routes/oportunidades.$id.tsx` o `intent` `mudar-estagio` na `action` (chama `mudarEstagio(id, estagio, motivo_perda)`; erro → `{ ok: false, ...erro }` com status 200, como em T046) e renderizar `BarraEstagios` abaixo do card de cabeçalho. Conferir que o `CardPedido` passa de "indisponível" para "pronto" logo depois de confirmar Ganho, sem recarregar a página

**Checkpoint**: roteiro 3 do [quickstart.md](./quickstart.md) funciona; o fluxo completo "criar →
mover até Ganho → gerar pedido" roda só pela interface (SC-001).

**Commit** (sugestão em três): `test(backend): cover stage transition rules` · `feat(backend): add
stage transition endpoint with backend-enforced rules` · `feat(frontend): add stage bar with
confirmation modals`

---

## Phase 6: User Story 4 - Filtrar e buscar na listagem (Priority: P3)

**Goal**: chips de estágio com contagem e busca por título ou empresa, refletidos na URL e
renderizados no servidor.

**Independent Test**: com dados variados (`make seed`), aplicar o filtro de estágio, buscar por
trecho do nome da empresa e por trecho do título, recarregar a página com a URL e ver
"Nada encontrado" (quickstart, roteiros 1 e 7).

### Tests for User Story 4 ⚠️

- [X] T053 [P] [US4] Escrever `backend/tests/test_listagem.py`:
  - `?estagio=GANHO` devolve só as oportunidades em GANHO;
  - um `estagio` inválido é ignorado (lista todas);
  - `?q=horizonte` encontra pelo nome da empresa e `?q=LOGÍST` pelo título, sem diferenciar maiúsculas e minúsculas;
  - `?q=%20%20` não filtra;
  - `estagio` e `q` combinados funcionam;
  - `contagens` aplicam `q` e ignoram `estagio`, e `TODOS` é a soma;
  - `total_cadastradas` ignora os filtros;
  - a ordenação é `-atualizado_em`;
  - com 1.000 oportunidades, a listagem executa no máximo 3 queries (`django_assert_max_num_queries`) e responde em menos de 1 s.

### Implementation for User Story 4

- [X] T054 [US4] Criar `backend/comercial/services/consultas.py` com `filtrar_oportunidades(estagio: str | None, q: str | None) -> tuple[QuerySet, dict, int]` (resultados com `select_related`, contagens por estágio com a busca aplicada e total geral), aplicando trim em `q`, ignorando `estagio` inválido e usando `Q(titulo__icontains=q) | Q(empresa__nome__icontains=q)`. Mudar `OportunidadeListaView.get` em `backend/comercial/views.py` para ler `estagio` e `q` da query string e usar esse serviço. Rodar `make test`: T053 deve passar
- [ ] T055 [P] [US4] Criar `frontend/app/features/oportunidades/components/FiltroEstagios.tsx`: chips "Todos", "Lead", "Contato", "Proposta", "Ganho" e "Perdido", cada um com a contagem de `contagens`, como `<Link>` para `?estagio=X` que **preserva `q`** ("Todos" remove `estagio`). O chip ativo usa o estilo azul do protótipo e `aria-current="page"`
- [ ] T056 [P] [US4] Criar `frontend/app/features/oportunidades/components/BuscaOportunidades.tsx`: um `<Form method="get">` com `input` `name="q"` (placeholder "Buscar por título ou empresa", `defaultValue` e `key` iguais ao `q` atual), um `hidden` `estagio` quando houver filtro, e o botão "Buscar". No `onSubmit`, se o `q` sem espaços ficar vazio, remove o campo antes de enviar, para não gerar `q=` na URL
- [ ] T057 [US4] Atualizar `frontend/app/routes/oportunidades._index.tsx`:
  - `loader`: lê `estagio` e `q` de `request.url` e os repassa a `listarOportunidades`.
  - Filtros: renderiza `FiltroEstagios` e `BuscaOportunidades` acima da tabela, lado a lado no desktop e empilhados no celular.
  - Vazio: `total_cadastradas === 0` → "Nenhuma oportunidade ainda" + "Nova oportunidade"; caso contrário, `resultados` vazio → `EmptyState` "Nada encontrado", com a descrição "Nenhum resultado para “{q}”{em {estágio}}", e o link "Limpar filtros" para `/oportunidades`.
  - Carregamento: enquanto `useNavigation().location?.pathname === "/oportunidades"`, a tabela fica com `opacity-60` e `aria-busy`. Na primeira carga, a lista vem pronta via SSR, sem skeleton.

**Checkpoint**: roteiros 1 e 7 do [quickstart.md](./quickstart.md) funcionam, inclusive com
JavaScript desativado.

**Commit** (sugestão em três): `test(backend): cover listing filters, search and counts` ·
`feat(backend): add stage filter, search and counts to listing` · `feat(frontend): add stage chips
and search persisted in url`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: documentação exigida pela constituição, consistência de estados e validação final.

- [ ] T058 [P] Escrever `README.md` na raiz (Princípio IX), com as seções:
  - visão geral;
  - pré-requisitos (Docker, Python 3.12, Node ≥ 22.22);
  - como subir (`make db`, `make backend`, `make seed`, `make frontend`);
  - como rodar os testes (`make test`, `make typecheck`);
  - tabela de variáveis de ambiente (backend e frontend);
  - como simular falhas do ERP (`ERP_MODO` + reinício);
  - estrutura de pastas;
  - **decisões técnicas e trade-offs**: unicidade do pedido (OneToOne + `select_for_update` + `IntegrityError`, lock durante a chamada ao ERP), desenho da integração ERP (interface, simulador determinístico, referência externa para deduplicação), SSR (loaders no servidor, filtros na URL, API só chamada pelo servidor Node), validação só no DRF, contagens com a busca aplicada;
  - o que ficou fora de escopo e os possíveis extras.
- [ ] T059 [P] Revisar a consistência dos estados de interface (Princípio VIII, SC-006) em `frontend/app/routes/*.tsx` e `frontend/app/features/oportunidades/components/*.tsx`:
  - todas as telas usam os mesmos `ErrorState`, `NaoEncontrado`, `EmptyState`, `Alert`, `PendingBar` e botões com texto de progresso;
  - toda ação que dispara requisição fica desabilitada enquanto estiver pendente;
  - nenhuma tela fica em branco quando a API está fora do ar (testar derrubando o backend).

  Corrigir as divergências encontradas.
- [ ] T060 [P] Conferir o uso em tela estreita (~375 px) das rotas em `frontend/app/routes/` (detalhe em uma coluna, tabela com rolagem horizontal, chips com quebra de linha, modal cabendo na tela) e ajustar as classes Tailwind onde for preciso
- [ ] T061 Rodar `make test` e `make typecheck` do zero (`docker compose down -v`, `make db`, migrações) e depois executar todos os roteiros do [quickstart.md](./quickstart.md), registrando em `specs/001-pipeline-comercial-erp/quickstart.md` qualquer correção de comando ou resultado esperado encontrada
- [ ] T062 Revisar o histórico com `git log --oneline` antes da entrega: as mensagens devem seguir Conventional Commits, sem "wip" ou "ajustes"; se precisar, reescrever **apenas commits locais ainda não publicados** e confirmar com o autor antes

**Commit**: `docs: add readme with setup, tests and technical decisions` · `fix(frontend): align
loading, error and empty states across screens` (se houver ajustes) · `docs(quickstart): update
validation steps` (se houver ajustes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende da Setup. **Bloqueia** todas as histórias.
- **US1 (Phase 3)**: depende só da Phase 2.
- **US2 (Phase 4)**: o backend (T038–T044) depende só da Phase 2, porque os testes criam a
  oportunidade em GANHO por fixture. O frontend (T045–T046) depende do detalhe do T036 (US1).
- **US3 (Phase 5)**: o backend (T047–T049) depende só da Phase 2. O frontend (T050–T052)
  depende do T036 (US1) e usa o mesmo arquivo de rota que o T046.
- **US4 (Phase 6)**: o backend (T053–T054) depende do T029 (US1), porque evolui a mesma view. O
  frontend (T055–T057) depende do T035 (US1).
- **Polish (Phase 7)**: depende das histórias concluídas.

### User Story Dependencies

```text
Setup → Foundational ─┬─► US1 (MVP) ─┬─► US2 (frontend)
                      │              ├─► US3 (frontend)
                      │              └─► US4 (backend + frontend)
                      ├─► US2 (backend)
                      └─► US3 (backend)
                                         └──────────────► Polish
```

- O T046 e o T052 editam o mesmo arquivo (`oportunidades.$id.tsx`), então precisam rodar em
  sequência.
- O T029, o T044, o T049 e o T054 editam `views.py`/`urls.py`, então também rodam em
  sequência.

### Within Each User Story

- Testes primeiro (e falhando), depois serviços, serializers, views e urls, e por fim as rotas e
  componentes do frontend.
- Commit ao fim de cada bloco lógico (ver **Commit** em cada fase).

### Parallel Opportunities

- **Setup**: T002, T003, T006, T007, T008 e T010 em paralelo, depois de T001.
- **Foundational**: T015 e T016 (backend) em paralelo com T018–T023 (frontend). T012 → T013 →
  T017 em sequência.
- **Depois da Phase 2**: os testes T026, T038–T040 e T047 podem ser escritos todos em paralelo.
  O backend da US2 e da US3 pode avançar em paralelo ao frontend da US1.
- **Dentro das histórias**: os componentes marcados [P] (T030, T031, T034, T045, T050, T055,
  T056) não dependem uns dos outros.

---

## Parallel Example: User Story 2

```bash
# Testes obrigatórios juntos (arquivos distintos):
Task: "T038 Escrever backend/tests/test_erp_cliente.py"
Task: "T039 Escrever backend/tests/test_pedido_unicidade.py"
Task: "T040 Escrever backend/tests/test_pedido_falhas_erp.py"

# Em paralelo com o serviço, o componente de UI:
Task: "T041 Implementar backend/erp/erros.py e backend/erp/cliente.py"
Task: "T045 Criar frontend/app/features/oportunidades/components/CardPedido.tsx"
```

## Parallel Example: User Story 1

```bash
Task: "T026 Escrever backend/tests/test_oportunidades_api.py"
Task: "T027 Implementar backend/comercial/services/empresas.py"
Task: "T031 Criar frontend/app/features/oportunidades/components/EmpresaInput.tsx"
Task: "T034 Criar frontend/app/features/oportunidades/components/TabelaOportunidades.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (Setup) → Phase 2 (Foundational).
2. Phase 3 (US1): cadastrar, listar, detalhar e editar.
3. **PARAR e VALIDAR** com o roteiro 2 do quickstart.

### Incremental Delivery

1. US1: MVP navegável.
2. US2: o objetivo central do desafio, com os testes obrigatórios. As oportunidades em Ganho vêm
   do seed até a US3 existir.
3. US3: fecha o fluxo completo pela interface (SC-001).
4. US4: produtividade na listagem (filtros e busca na URL, SSR).
5. Polish: README, consistência, validação do quickstart e revisão do histórico.

Cada incremento termina com `make test` e `make typecheck` passando e com commits semânticos.
Extras (visão em colunas somente leitura, endpoint HTTP fake do ERP, testes de UI) só entram
depois da Phase 7 (Princípio II).

---

## Notes

- [P] = arquivos diferentes, sem dependência de tarefa incompleta.
- [USn] liga a tarefa à história, para rastreabilidade.
- Cada história pode ser testada de forma independente no seu checkpoint.
- Não pular a etapa "teste falhando primeiro" nos testes obrigatórios (T038–T040).
- Evitar tarefas vagas e conflitos de arquivo: as rotas e `views.py` compartilhados estão
  sequenciados acima.
