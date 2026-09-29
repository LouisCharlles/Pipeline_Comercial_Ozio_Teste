# Mini Pipeline Comercial com Integração ERP

Vendedores cadastram oportunidades ligadas a empresas, movem-nas pelos estágios **Lead → Contato →
Proposta → Ganho / Perdido** e, em Ganho, geram **um único pedido** num ERP simulado, com
tratamento de falhas e nova tentativa segura.

- **Backend**: Django 5.2 + Django REST framework 3.17 + PostgreSQL 16
- **Frontend**: React 19 + React Router 8 (modo framework, SSR) + TypeScript + Tailwind CSS 4
- **Monorepo**: `backend/` e `frontend/` na raiz

A especificação, o plano e as decisões detalhadas estão em
[`specs/001-pipeline-comercial-erp/`](specs/001-pipeline-comercial-erp/).

## Pré-requisitos

- Docker com Docker Compose (sobe só o PostgreSQL)
- Python 3.12
- Node.js 22.22 ou superior, com npm
- `make`

## Como rodar

Use um terminal para cada serviço:

```bash
make backend    # sobe o PostgreSQL, cria backend/.venv, aplica migrações e roda a API em :8000
make seed       # (opcional) recria os dados de demonstração do protótipo — APAGA os dados atuais
make frontend   # instala dependências e roda o app em http://localhost:5173
```

Abra <http://localhost:5173>. Nenhum `.env` é obrigatório: os padrões batem com o
`docker-compose.yml`. Para mudar algo, copie os exemplos:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## Testes

```bash
make test        # sobe o PostgreSQL e o venv se preciso; roda o pytest do backend
make typecheck   # gera os tipos das rotas e roda o tsc no frontend
```

Os testes rodam **contra o PostgreSQL**, porque a garantia de pedido único depende de
`SELECT … FOR UPDATE` e das constraints do banco, que o SQLite não reproduz. Destaques:

| Arquivo | O que garante |
|---|---|
| `test_pedido_unicidade.py` | repetição devolve o mesmo pedido sem chamar o ERP; **10 requisições simultâneas** → 1 pedido; **10 retries simultâneos** → ERP chamado 1 vez; `IntegrityError` vira resposta previsível |
| `test_pedido_falhas_erp.py` | tempo esgotado (504), erro do serviço e resposta inválida (502) ficam registrados sem dado parcial; o retry conclui sobre o mesmo registro; uma interrupção no meio da chamada desfaz a tentativa |
| `test_estagios.py` | tabela completa de transições, bloqueio com pedido gerado, reabertura de Perdido |
| `test_listagem.py` | filtro, busca, contagens e 1.000 oportunidades em ≤ 3 queries e < 1 s |
| `test_oportunidades_api.py` | contrato de cadastro, detalhe, edição e sugestões de empresa |

## Variáveis de ambiente

| Variável | Onde | Padrão | Uso |
|---|---|---|---|
| `POSTGRES_DB` / `USER` / `PASSWORD` | backend | `pipeline` | credenciais do banco |
| `POSTGRES_HOST` / `POSTGRES_PORT` | backend | `localhost` / `5432` | endereço do banco |
| `DJANGO_SECRET_KEY` | backend | valor de dev | chave do Django |
| `DJANGO_DEBUG` | backend | `true` | modo debug |
| `DJANGO_ALLOWED_HOSTS` | backend | `localhost,127.0.0.1` | hosts aceitos |
| `ERP_MODO` | backend | `sucesso` | comportamento do ERP simulado: `sucesso`, `timeout`, `erro`, `resposta_invalida` |
| `ERP_LATENCIA_MS` | backend | `0` | atraso artificial de cada chamada ao ERP |
| `ERP_TIMEOUT_SEGUNDOS` | backend | `5` | tempo limite da chamada ao ERP |
| `API_URL` | frontend | `http://localhost:8000/api` | URL da API, usada só pelo servidor do React Router |

### Simular falhas do ERP

1. Em `backend/.env`, defina `ERP_MODO=timeout` (ou `erro`, ou `resposta_invalida`) e reinicie o
   `make backend`.
2. Numa oportunidade em Ganho, clique em **Gerar pedido**: aparece a mensagem específica da falha,
   o número de tentativas e o botão **Tentar novamente**.
3. Volte para `ERP_MODO=sucesso`, reinicie e clique em **Tentar novamente**: o pedido é concluído
   sobre o mesmo registro e com a mesma referência.

## Estrutura

```text
backend/
  config/             settings (tudo por variável de ambiente) e urls
  comercial/          app único: models, serializers, views finas, erros e services/
    services/         regras: pedidos.py (geração), estagios.py (transições), empresas.py, consultas.py
  erp/                integração isolada: cliente.py (interface), simulado.py, erros.py
  tests/
frontend/app/
  routes/             rotas finas com loader/action (listagem SSR, nova, detalhe, editar)
  features/oportunidades/   cliente da API (*.server.ts), tipos, formatação e componentes
  components/ui/      botão, alerta, campos, modal e estados vazio/erro/carregando
specs/                especificação, plano, contratos e tarefas (Spec Kit)
```

## Artefatos de processo

Além de `backend/` e `frontend/`, o repositório guarda o material usado para planejar a solução.
Nada disso é necessário para rodar o projeto.

- **`specs/001-pipeline-comercial-erp/`**: documentação da funcionalidade, escrita antes do código
  e mantida junto com ele.
  - `spec.md`: requisitos (FR-xxx), histórias de usuário e casos de borda. Os comentários no código
    citam esses identificadores.
  - `plan.md` e `research.md`: arquitetura e decisões com alternativas avaliadas (R1, R2...).
  - `data-model.md`: entidades, constraints e transições de estágio.
  - `contracts/`: contrato da API REST (`api.md`) e das rotas do frontend (`ui-rotas.md`).
  - `tasks.md`: lista de tarefas ordenada por dependência, que guiou os commits.
  - `quickstart.md`: roteiro de validação manual.
  - `checklists/`: checklist de qualidade dos requisitos.
- **`pesquisa/`**: notas de estudo feitas antes da especificação, sobre modelagem e UX de CRMs
  (Odoo, Twenty, Pipedrive, HubSpot). Nenhum código foi copiado.
- **`.specify/`**: estrutura do [Spec Kit](https://github.com/github/spec-kit), com templates,
  scripts e a constituição do projeto (`memory/constitution.md`), que define os princípios
  seguidos (simplicidade, integridade do pedido, ERP isolado, testes das regras de negócio,
  commits pequenos).
- **`.claude/skills/`**: comandos do Spec Kit para o Claude Code (`/speckit-specify`,
  `/speckit-plan`, `/speckit-tasks`...), usados como assistente em cada etapa.

## Decisões técnicas

### Um pedido por oportunidade

A garantia tem três camadas, da mais forte para a mais fraca
([`comercial/services/pedidos.py`](backend/comercial/services/pedidos.py)):

1. **Banco**: `Pedido.oportunidade` é `OneToOneField` (UNIQUE). Nenhum bug de aplicação consegue
   criar um segundo pedido.
2. **Lock**: a geração roda em `transaction.atomic()` com `select_for_update()` na oportunidade,
   **incluindo a chamada ao ERP**. Requisições simultâneas são atendidas uma de cada vez: a segunda
   vê o pedido já gerado e o devolve (HTTP 200) sem chamar o ERP. Essa camada é o que protege o
   *retry*, porque nele já existe a linha do pedido e não há INSERT para a constraint barrar. O
   teste de 10 retries simultâneos falha se o lock for removido.
3. **Última defesa**: um `IntegrityError` é capturado e convertido no pedido existente, nunca em
   erro 500.

O botão desabilitado durante o envio é só conveniência; a regra vale mesmo que a tela seja
contornada. A mudança de estágio usa o mesmo lock, então estágio e pedido nunca mudam ao mesmo
tempo.

**Trade-off**: o lock fica preso durante a chamada ao ERP (até o tempo limite de 5 s). Para o
volume do desafio isso é aceitável, e é mais simples e verificável que uma tabela de
`Idempotency-Key` ou uma fila assíncrona. Com volume alto, o próximo passo seria tirar a chamada
do caminho da requisição (fila + worker) mantendo a mesma chave natural.

### Integração com o ERP

- O resto do sistema só conhece a interface `ClienteErp` e três exceções:
  `ErpTempoEsgotado`, `ErpErroServico` e `ErpRespostaInvalida`. Trocar o simulador por um ERP real
  é trocar `obter_cliente_erp()`.
- A resposta do ERP é **validada pelo cliente**. No modo `resposta_invalida`, o simulador devolve
  um payload fora do contrato e quem detecta é essa validação, o mesmo caminho que um ERP real
  percorreria.
- Cada tentativa grava o resultado na **mesma transação**: o pedido termina `GERADO` (com número
  e data) ou `FALHOU` (com tentativas, tipo e mensagem do erro), nunca pela metade. Constraints
  garantem que não existe "gerado sem número do ERP". Se o processo morrer durante a chamada, o
  rollback desfaz a tentativa.
- Toda tentativa envia a mesma **referência externa** (`OPP-{id}`). O simulador, como um ERP
  idempotente, devolve o mesmo número para a mesma referência (o número é derivado dela). Assim,
  um retry depois de um tempo esgotado em que o ERP "criou mesmo assim" não duplica o pedido lá.
- A nova tentativa é manual ("Tentar novamente"), sem reprocessamento em segundo plano.

**Trade-off**: o modo do simulador vem de `ERP_MODO` e exige reiniciar o backend para trocar. Um
endpoint para mudar o modo em tempo de execução deixaria a demonstração mais rápida, mas exporia o
simulador na API pública.

### SSR e frontend

- A listagem é renderizada no servidor pelo `loader` do React Router: o HTML chega com a tabela
  preenchida e funciona sem JavaScript. **Filtro e busca ficam na URL** (chips são links; a busca é
  um `<Form method="get">`), então recarregar ou compartilhar o endereço mostra a mesma visão.
- **O navegador nunca chama a API Django**: loaders, actions e a rota de sugestões de empresa
  chamam a API a partir do servidor Node (`*.server.ts`). Isso dispensa CORS e deixa um único
  cliente HTTP tipado.
- **A validação fica só no DRF**, que é a fonte da verdade. As actions devolvem os erros por campo
  e o formulário os exibe junto aos campos, mantendo o que foi digitado. Não há zod para não
  duplicar regras e mensagens.
- **Estados de interface com um padrão único**: barra fina de progresso nas navegações, botões
  desabilitados com texto de progresso nos envios, `ErrorBoundary` por rota ("Não foi possível
  carregar" + "Tentar novamente", ou "Oportunidade não encontrada") e estados vazios distintos para
  "nada cadastrado" e "nada encontrado".
- As datas são formatadas com fuso fixo (`America/Sao_Paulo`), para que servidor e navegador
  gerem o mesmo texto.

### Outras decisões

- **Empresa pelo nome**: o vendedor digita o nome, com sugestões das empresas existentes; nome já
  cadastrado (sem diferenciar maiúsculas ou espaços nas pontas) é reaproveitado, nome novo cria a
  empresa. Não há tela de cadastro de empresas.
- **Transições**: livres entre estágios abertos; Ganho e Perdido pedem confirmação e registram a
  data de fechamento; Perdido pode ser reaberto (limpa data e motivo), mas não vai direto a Ganho;
  com pedido gerado, o estágio fica bloqueado. Com um pedido que falhou, a oportunidade pode sair
  de Ganho, e a falha fica registrada para quando ela voltar.
- **Contagens dos chips** aplicam a busca e ignoram o estágio: mostram onde estão os resultados da
  busca.

## Fora de escopo

Autenticação, dashboards, arrastar e soltar, CI/CD, exclusão de registros, histórico de atividades
e múltiplos pedidos por oportunidade. Possíveis extras: visão em colunas por estágio (somente
leitura), ERP fake via HTTP com timeout real e testes de interface automatizados.
