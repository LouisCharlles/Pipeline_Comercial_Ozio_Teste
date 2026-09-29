# Research: Mini Pipeline Comercial com Integração ERP

**Feature**: `001-pipeline-comercial-erp` | **Data**: 2026-09-29

Resolve as incógnitas do Technical Context e os conflitos e dúvidas listados em
`pesquisa/notas-pesquisa.md` §7. O que já foi decidido na spec (seção Clarifications) não é
repetido aqui.

---

## R1. Versão do React Router e modo de uso

- **Decision**: React Router **8.x** em **modo framework** (`@react-router/dev` + Vite 7), com
  `ssr: true`. Rotas declaradas em `app/routes.ts`; `loader`/`action` rodando no servidor Node
  (`@react-router/node` + `@react-router/serve`). Imports de `react-router` (não existe mais
  `react-router-dom`). Requisitos: Node ≥ 22.22, React/React DOM ≥ 19.2.7, Vite ≥ 7.
- **Rationale**: a constituição exige React Router 8 e SSR na listagem. O v8 foi lançado em
  2026-06-17 e mantém a API de loaders e actions do v7. As flags `v8_*` do v7 viraram padrão:
  middleware, Vite Environment API, split route modules e pass-through requests. Nenhuma delas
  obriga a usar middleware; o projeto não precisa de middleware.
- **Alternatives considered**: modo *data*/SPA (descartado porque não entrega HTML pronto na
  primeira carga, o que viola o Princípio I e a FR-017); React Router 7 (descartado porque a
  constituição fixa a v8).
- **Fontes**: [React Router v8 (blog)](https://remix.run/blog/react-router-v8),
  [Updating from v7](https://reactrouter.com/upgrading/v7).

## R2. Versões do backend

- **Decision**: Python **3.12**, Django **5.2 LTS**, Django REST framework **3.17**, `psycopg` 3,
  PostgreSQL **16** (via Docker Compose).
- **Rationale**: o 5.2 é LTS, com suporte até abril de 2028, e o DRF 3.17 suporta oficialmente
  Django 4.2–6.0. O Python 3.12 é o que está instalado na máquina de desenvolvimento. O PostgreSQL
  16 é a mesma versão do cliente `psql` local.
- **Alternatives considered**: Django 6.0 (suporte estendido termina em abril de 2027, o que não
  traz ganho para o escopo); Django 6.1 (sem suporte declarado pelo DRF 3.17).
- **Fontes**: [endoflife.date/django](https://endoflife.date/django),
  [djangorestframework 3.17](https://pepy.tech/projects/djangorestframework).

## R3. Garantia de um pedido por oportunidade (conflitos nº 2 e nº 3; dúvida nº 6)

- **Decision**: a garantia tem três camadas:
  1. **No banco**: `Pedido.oportunidade` é `OneToOneField` (UNIQUE), e `numero_erp` e
     `referencia_externa` também são UNIQUE.
  2. **No serviço `gerar_pedido`**: tudo roda em `transaction.atomic()`. A oportunidade é
     travada com `select_for_update()` (espera o lock, não usa `nowait`), as regras são validadas,
     o pedido é obtido ou criado, o ERP é chamado com timeout e o resultado (GERADO ou FALHOU) é
     gravado **dentro da mesma transação**.
  3. **Última defesa**: se ainda assim ocorrer um `IntegrityError`, ele é capturado e o sistema
     devolve o pedido existente.
- **Pedido já existente → 200** com o pedido (idempotente); **pedido novo → 201**. O 409 fica
  reservado para as violações de regra: fora de Ganho, sem valor e estágio bloqueado. Isso
  resolve o conflito nº 2.
- **O estágio só trava com pedido GERADO** (FR-012). Com pedido FALHOU, a oportunidade pode sair
  de Ganho (conflito nº 3). A mudança de estágio também usa `select_for_update()` na
  oportunidade, então não corre em paralelo com a geração do pedido.
- **PENDENTE preso (dúvida nº 6)**: não acontece. O estado PENDENTE só existe dentro da transação.
  Se o processo morrer durante a chamada ao ERP, o rollback desfaz a criação do pedido (ou mantém
  o FALHOU anterior), e a tela mostra "não concluído" com a opção de repetir. Isso atende à Edge
  Case 3. `PENDENTE` continua no enum para deixar o estado explícito durante a transação e para
  proteger contra leituras futuras fora dela; ele nunca é gravado de forma visível.
- **Requisições simultâneas**: a segunda requisição espera o lock. Quando a primeira termina com
  GERADO, a segunda recebe **200 com o mesmo pedido**. Quando a primeira termina com FALHOU, a
  segunda faz uma nova tentativa sobre o mesmo registro, e isso é legítimo. O resultado nunca é um
  erro genérico nem um segundo pedido (SC-002).
- **Rationale**: é a solução mais simples que atende ao Princípio III: a unicidade vem do banco e
  o lock serializa inclusive a chamada externa. O custo é segurar o lock por até o tempo limite do
  ERP (5 s), o que é aceitável para o volume do desafio.
- **Alternatives considered**: `Idempotency-Key` com tabela própria (resolve retry de rede, mas
  a oportunidade já é a chave natural; ver `notas-codigo.md` §3); `nowait=True` com 409 "em
  processamento" (dá mais atrito para o usuário e complica o teste de 10 requisições
  simultâneas); fila assíncrona (proibida pelo Princípio II).

## R4. Simulação do ERP (dúvida nº 13)

- **Decision**: a interface `ClienteErp.criar_pedido(referencia: str, valor: Decimal) ->
  RespostaErp` fica em `backend/erp/`. A implementação `ErpSimulado` roda em processo. As falhas
  são exceções de domínio próprias: `ErpTempoEsgotado`, `ErpErroServico` e `ErpRespostaInvalida`.
  - **Modo de falha**: vem da variável `ERP_MODO` (`sucesso` | `timeout` | `erro` |
    `resposta_invalida`, padrão `sucesso`) e é lido **a cada chamada**, a partir de settings. Nos
    testes, o modo é trocado com `override_settings` / fixture.
  - **Timeout**: o simulador dorme `ERP_LATENCIA_MS` (padrão 0) e, no modo `timeout`, lança
    `ErpTempoEsgotado` sem esperar os 5 s reais. O tempo limite real (`ERP_TIMEOUT_SEGUNDOS=5`)
    fica documentado e é repassado ao cliente, pronto para uma implementação HTTP futura.
  - **Resposta inválida**: o simulador devolve um payload fora do contrato (sem número ou com
    tipo errado), e quem detecta o problema é a **validação do cliente**, não o simulador. Assim o
    caminho de validação é exercitado de verdade.
  - **Deduplicação no ERP**: o simulador guarda `referencia → numero` em memória e devolve o mesmo
    número para a mesma referência. É isso que torna seguro o retry depois de um timeout em que o
    ERP "criou mesmo assim" (Edge Case 2).
- **Troca de modo na demonstração**: alterar `ERP_MODO` no `.env` do backend e reiniciar o
  processo. O `quickstart.md` descreve o roteiro falha → retry com sucesso.
- **Rationale**: é determinístico (Princípio IV), não precisa de um segundo servidor e não expõe
  detalhes do simulador na API pública.
- **Alternatives considered**: endpoint HTTP fake com `requests` e timeout real (mais realista,
  porém mais lento e com mais peças; fica como extra); endpoint para trocar o modo em tempo de
  execução (expõe o simulador na API e, com vários workers, o estado em memória diverge); modo
  `aleatorio` (não é determinístico, então fica fora).

## R5. Mapeamento de falhas → HTTP → UI

| Situação | Pedido | HTTP | `codigo` | Mensagem na UI |
|---|---|---|---|---|
| Sucesso (novo) | GERADO | 201 | — | card mostra número, data e valor |
| Já existia GERADO | GERADO | 200 | — | card mostra o pedido existente |
| Tempo esgotado | FALHOU (`TEMPO_ESGOTADO`) | 504 | `erp_tempo_esgotado` | "O ERP não respondeu a tempo. Tente novamente." |
| Erro do serviço | FALHOU (`ERRO_SERVICO`) | 502 | `erp_erro_servico` | "O ERP retornou um erro. Tente novamente." |
| Resposta inválida | FALHOU (`RESPOSTA_INVALIDA`) | 502 | `erp_resposta_invalida` | "O ERP enviou uma resposta inesperada. Tente novamente." |
| Fora de Ganho | — (ERP não chamado) | 409 | `estagio_invalido` | "Disponível quando a oportunidade estiver em Ganho" |
| Valor vazio ou zero | — (ERP não chamado) | 409 | `valor_obrigatorio` | "Informe um valor maior que zero antes de gerar o pedido" |

Nas falhas, o corpo da resposta traz o `pedido` atualizado (FALHOU, `tentativas`,
`ultimo_erro`), para a tela exibir o card sem precisar de outra requisição.

## R6. Busca: submit ou debounce (conflito nº 4)

- **Decision**: `<Form method="get">` com campo `q` e botão "Buscar" (como no protótipo). Os chips
  de estágio são links (`?estagio=`) que **preservam `q`**. Busca vazia ou só com espaços remove o
  parâmetro da URL.
- **Rationale**: funciona sem JavaScript, deixa filtro e busca na URL (FR-016) e reaproveita o
  loader SSR, sem estado duplicado.
- **Alternatives considered**: debounce com `useSubmit` (mais requisições e mais código, sem ganho
  para o volume do desafio).

## R7. Contagem por estágio nos chips

- **Decision**: a API devolve `contagens` por estágio **aplicando a busca `q` e ignorando o filtro
  de estágio**, mais o total (`TODOS`). Assim os chips mostram quantos resultados da busca há em
  cada estágio.
- **Rationale**: "cada estágio mostra sua contagem" (US4, Cenário 1) continua útil com a busca
  aplicada, e o vendedor sabe para onde trocar de chip. Tudo sai numa única consulta agregada
  (`values('estagio').annotate(Count)`).
- **Alternatives considered**: contagens globais, sem a busca (o chip mostra números que não batem
  com o que aparece ao clicar).

## R8. Chamadas do frontend ao backend

- **Decision**: **todas** as chamadas à API Django são feitas no servidor do React Router
  (loaders, actions e uma *resource route* para sugestões de empresa), com a URL em `API_URL`. O
  navegador nunca chama o Django diretamente.
- **Rationale**: não precisa de CORS nem de uma URL pública da API. O SSR já exige o fetch no
  servidor, e há um único cliente HTTP tipado (`api.server.ts`).
- **Alternatives considered**: fetch direto do navegador para o Django (exige CORS e duplica o
  cliente).

## R9. Validação de formulários

- **Decision**: o **DRF é a única fonte de validação**. A action repassa `campos` (erros por campo)
  e o formulário reexibe as mensagens e os valores digitados. As mensagens ficam em pt-BR nos
  serializers. O formulário usa `noValidate` para não misturar balões nativos do navegador com o
  padrão da aplicação.
- **Rationale**: é uma regra só, uma mensagem só e nenhuma dependência extra (Princípio II). O
  Princípio VIII exige que os erros da API apareçam junto aos campos, e é isso que acontece.
- **Alternatives considered**: zod no front + DRF (duplica regras e mensagens; fica como extra).

## R10. Estilo e componentes de UI

- **Decision**: **Tailwind CSS v4** (`@tailwindcss/vite`) com componentes próprios em
  `app/components/ui/` (Button, Alert, FormField, Modal, Skeleton, StageBadge, EmptyState,
  PendingBar), reproduzindo o protótipo do Figma Make.
- **Rationale**: o protótipo já está escrito com classes Tailwind, então a tradução para a
  implementação é direta. Os componentes são poucos e autorais (Princípio VII).
- **Alternatives considered**: biblioteca de componentes (shadcn, MUI) (mais dependências e mais
  código gerado do que o escopo pede).

## R11. Estados de interface (Princípio VIII)

- **Decision**:
  - **Carregamento**: a primeira carga vem pronta pelo SSR. Na troca de filtro, busca ou
    navegação, `useNavigation()` → `<PendingBar>` fina no topo e a lista com opacidade reduzida.
    Nos envios, o botão fica desabilitado com o texto de progresso ("Criando…", "Salvando…",
    "Gerando pedido…").
  - **Erro de carga**: um `ErrorBoundary` por rota. 404 → "Oportunidade não encontrada" + link
    para a listagem. Os demais erros → "Não foi possível carregar" + "Tentar novamente"
    (revalida).
  - **Erro de ação**: a action **retorna** `{ ok: false, codigo, mensagem, campos?, pedido? }` em
    vez de lançar. O `<Alert>` aparece no bloco afetado (formulário, barra de estágio ou card
    Pedido). Um helper único, `mensagemDeErro()`, converte os códigos em texto.
  - **Vazio**: `<EmptyState>` com as variantes "Nenhuma oportunidade ainda" (+ "Nova
    oportunidade") e "Nada encontrado" (+ "Limpar filtros"), conforme a spec.
  - O skeleton do protótipo só aparece em navegação client-side do detalhe; na listagem, a
    primeira carga nunca mostra skeleton (FR-017).
- **Rationale**: é um padrão único para as quatro telas, como pede a SC-006.

## R12. Testes

- **Decision**: `pytest` + `pytest-django` contra o **PostgreSQL** do Docker Compose. Testes
  obrigatórios:
  - regras de transição de estágio;
  - pedido duplicado por repetição sequencial;
  - **concorrência com 10 threads** (`django_db(transaction=True)`), para cumprir a SC-002;
  - um teste por modo de falha do ERP;
  - retry após falha sobre o mesmo registro;
  - `IntegrityError` convertido em resposta previsível;
  - contrato dos endpoints (status e formato).

  No frontend, o gate é `react-router typegen && tsc --noEmit`. Não há testes de UI na entrega
  principal.
- **Rationale**: é o Princípio V, com testes onde o risco está. O `select_for_update` exige
  PostgreSQL de verdade.
- **Alternatives considered**: SQLite nos testes (ignora o `FOR UPDATE`, então está descartado);
  Vitest/Playwright (extra depois da entrega).

## R13. Configuração e ambiente

- **Decision**: o `docker-compose.yml` na raiz sobe **apenas o PostgreSQL**. O backend e o
  frontend rodam localmente (`venv` + `pip`, `npm`). As variáveis ficam em `backend/.env.example`
  (`POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `ERP_MODO`, `ERP_LATENCIA_MS`,
  `ERP_TIMEOUT_SEGUNDOS`) e em `frontend/.env.example` (`API_URL`), lidas com `os.environ`, sem
  biblioteca extra. Os comandos repetitivos ficam num `Makefile` na raiz (`make db`,
  `make backend`, `make frontend`, `make test`, `make seed`).
- **Rationale**: é o mínimo de passos reproduzível (restrições técnicas da constituição) e o
  README descreve um único caminho.
- **Alternatives considered**: tudo em containers (build mais lento e hot reload mais frágil);
  `uv` (mais rápido, mas é uma ferramenta a mais para o avaliador instalar).

## R14. Dados de demonstração

- **Decision**: o comando `python manage.py popular_demo` cria as 4 empresas e as oportunidades do
  protótipo, **corrigindo a inconsistência** do protótipo em que a #2 estava em Proposta com pedido
  gerado: ela passa a ser Ganho + GERADO.
- **Rationale**: o avaliador vê todos os estados da listagem logo de início.
