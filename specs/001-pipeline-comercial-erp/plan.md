# Implementation Plan: Mini Pipeline Comercial com Integração ERP

**Branch**: `001-pipeline-comercial-erp` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-pipeline-comercial-erp/spec.md`

## Summary

Um CRM mínimo para vendedores. Eles cadastram oportunidades ligadas a empresas (a empresa é criada
pelo nome digitado, com sugestões), movem as oportunidades entre cinco estágios fixos e, em Ganho,
geram **no máximo um** pedido num ERP simulado, com tratamento distinto para tempo esgotado, erro
e resposta inválida, e retry seguro.

Abordagem técnica:

- **Backend**: API REST em Django 5.2 + DRF sobre PostgreSQL. A unicidade do pedido é garantida
  por `OneToOne` no banco, e a geração do pedido roda em transação com `select_for_update()` na
  oportunidade, incluindo a chamada ao ERP (research R3).
- **Integração ERP**: fica atrás de `ClienteErp`, com um simulador determinístico configurado por
  `ERP_MODO` (R4).
- **Frontend**: React Router 8 em modo framework. A listagem é renderizada no servidor (SSR),
  filtro e busca ficam na URL, e todas as chamadas à API partem do servidor Node (R1, R8). A
  interface segue o protótipo do Figma Make, com os ajustes da seção Clarifications da spec.

## Technical Context

**Language/Version**: Python 3.12 (backend); TypeScript 5.x sobre Node.js ≥ 22.22 (frontend)

**Primary Dependencies**:
- Backend: Django 5.2 LTS, Django REST framework 3.17, psycopg 3.
- Frontend: React 19.2, React Router 8 (`react-router`, `@react-router/dev`,
  `@react-router/node`, `@react-router/serve`), Vite 7, Tailwind CSS 4.

**Storage**: PostgreSQL 16 (Docker Compose)

**Testing**: pytest + pytest-django contra PostgreSQL (inclui teste de concorrência com 10
threads); no frontend, `react-router typegen && tsc --noEmit` como gate

**Target Platform**: servidor Linux (Django em :8000 e servidor Node do React Router em :5173/:3000);
navegadores desktop modernos

**Project Type**: aplicação web (monorepo `backend/` + `frontend/`)

**Performance Goals**: listagem SSR com dados na primeira resposta; filtro e busca com resultado
em ≤ 1 s para até 1.000 oportunidades (SC-005)

**Constraints**: no máximo 1 pedido por oportunidade sob concorrência (SC-002); tempo limite do ERP
de 5 s; nenhum estado inconsistente após falha (SC-003); sem autenticação

**Scale/Scope**: ≤ 1.000 oportunidades, poucos usuários simultâneos; 5 rotas de UI (+1 resource route),
7 endpoints REST, 3 modelos

Todos os itens estão resolvidos em [research.md](./research.md). Não restou nenhum NEEDS
CLARIFICATION.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio | Como o plano atende | Status |
|---|---|---|---|
| I | Stack obrigatória e monorepo | Django + PostgreSQL + API REST (DRF); React + React Router 8 + TS; SSR na listagem (loader no servidor); pastas `backend/` e `frontend/` na raiz | ✅ |
| II | Simplicidade e escopo | 3 modelos, 1 app Django; sem auth, dashboard, DnD ou CI; sem zod, sem fila, sem Idempotency-Key; bibliotecas extras (Tailwind, pytest-django) justificadas abaixo | ✅ |
| III | Integridade do pedido | `OneToOneField` + `UNIQUE` em `referencia_externa` e `numero_erp`; `select_for_update`; `IntegrityError` → 200 com pedido existente; testes de repetição e de 10 requisições simultâneas | ✅ |
| IV | ERP isolado e resiliente | interface `ClienteErp` em `backend/erp/`; 3 exceções distintas; transação garante GERADO ou FALHOU, nunca parcial; `ERP_MODO` determinístico | ✅ |
| V | Testes de regra de negócio | duplicidade, concorrência, 3 falhas, retry, transições; PostgreSQL; `make test` | ✅ |
| VI | Commits semânticos | Conventional Commits por unidade lógica (definidos nas tarefas) | ✅ (processo) |
| VII | Código autoral | referências (Odoo, Twenty, protótipo) usadas só como conceito; componentes próprios | ✅ |
| VIII | Estados consistentes | padrão único de loading, erro, ação e vazio (research R11, contracts/ui-rotas.md); botões desabilitados durante o envio | ✅ |
| IX | Documentação | README com pré-requisitos, execução, testes, variáveis e decisões (unicidade, ERP, SSR), gerado a partir do quickstart | ✅ (tarefa) |
| — | Restrições técnicas | `.env.example` em backend e frontend; PostgreSQL via Compose; contrato da API definido antes da implementação ([contracts/api.md](./contracts/api.md)) com tipos TS espelhados | ✅ |

**Justificativa das bibliotecas auxiliares** (Princípio I/II):

- **Tailwind CSS 4**: o protótipo aprovado usa classes Tailwind, então a tradução é direta e
  evita escrever CSS próprio.
- **pytest + pytest-django**: fixtures e `transaction=True` simplificam o teste de concorrência.
- **psycopg 3**: driver oficial do PostgreSQL.

**Re-check pós-design (Phase 1)**: ✅ o design não introduziu violações. O lock mantido durante a
chamada ao ERP foi avaliado (R3) e aceito sem entrar em Complexity Tracking, porque é a opção mais
simples entre as alternativas.

## Project Structure

### Documentation (this feature)

```text
specs/001-pipeline-comercial-erp/
├── plan.md              # este arquivo
├── research.md          # Phase 0: decisões R1–R14
├── data-model.md        # Phase 1: modelos, constraints, transições, ciclo do pedido
├── quickstart.md        # Phase 1: roteiro de execução e validação
├── contracts/
│   ├── api.md           # Phase 1: contrato REST + interface interna do ERP
│   └── ui-rotas.md      # Phase 1: rotas, loaders/actions e estados de tela
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; não criado aqui)
```

### Source Code (repository root)

```text
docker-compose.yml               # só o serviço db (PostgreSQL 16)
Makefile                         # db, backend, frontend, seed, test, typecheck, reset-db
README.md

backend/
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── config/                      # settings.py (lê os.environ), urls.py, wsgi.py
├── comercial/                   # app Django único
│   ├── models.py                # Empresa, Oportunidade, Pedido (+ constraints)
│   ├── migrations/
│   ├── serializers.py           # validação (mensagens pt-BR) e representações
│   ├── views.py                 # endpoints DRF finos → serviços
│   ├── urls.py
│   ├── erros.py                 # exceções de domínio + handler → corpo {codigo, mensagem, ...}
│   ├── services/
│   │   ├── empresas.py          # obter_ou_criar_por_nome, sugerir
│   │   ├── estagios.py          # mudar_estagio + tabela de transições
│   │   └── pedidos.py           # gerar_pedido (lock + ERP + persistência)
│   └── management/commands/popular_demo.py
├── erp/                         # pacote Python puro (não é app Django)
│   ├── cliente.py               # ClienteErp (Protocol), RespostaErp, obter_cliente_erp()
│   ├── erros.py                 # ErpTempoEsgotado, ErpErroServico, ErpRespostaInvalida
│   └── simulado.py              # ErpSimulado (modos, dedup por referência)
└── tests/
    ├── conftest.py
    ├── test_oportunidades_api.py
    ├── test_estagios.py
    ├── test_pedido_unicidade.py      # repetição + 10 threads + IntegrityError
    ├── test_pedido_falhas_erp.py     # timeout, erro, resposta inválida, retry
    └── test_erp_cliente.py

frontend/
├── package.json
├── react-router.config.ts       # ssr: true
├── vite.config.ts               # reactRouter() + tailwindcss()
├── tsconfig.json
├── .env.example                 # API_URL=http://localhost:8000/api
└── app/
    ├── root.tsx                 # layout, header "Pipeline Comercial", ErrorBoundary raiz
    ├── routes.ts
    ├── app.css
    ├── routes/
    │   ├── home.tsx
    │   ├── oportunidades._index.tsx
    │   ├── oportunidades.nova.tsx
    │   ├── oportunidades.$id.tsx
    │   ├── oportunidades.$id.editar.tsx
    │   └── empresas.sugestoes.ts
    ├── features/oportunidades/
    │   ├── api.server.ts        # cliente HTTP tipado (somente servidor)
    │   ├── types.ts             # espelho de contracts/api.md
    │   ├── erros.ts             # mensagemDeErro(codigo)
    │   ├── formato.ts           # moeda BRL, datas pt-BR, rótulos de estágio
    │   └── components/          # OportunidadeForm, EmpresaInput, TabelaOportunidades,
    │                            # FiltroEstagios, BarraEstagios, CardPedido, ModalEstagio
    └── components/ui/           # Button, Alert, FormField, Modal, Skeleton, StageBadge,
                                 # EmptyState, PendingBar
```

**Structure Decision**: aplicação web em monorepo, com `backend/` (Django, um app `comercial` e o
pacote `erp` isolado) e `frontend/` (React Router 8 em modo framework, rotas finas e lógica em
`features/oportunidades`). Os testes do backend ficam em `backend/tests/`. Não há testes
automatizados de frontend na entrega principal.

## Complexity Tracking

Nenhuma violação da constituição a justificar.
