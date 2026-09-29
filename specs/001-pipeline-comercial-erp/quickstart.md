# Quickstart: validação ponta a ponta

Roteiro para subir o projeto e comprovar as histórias da [spec](./spec.md). Os detalhes de
payload estão em [contracts/api.md](./contracts/api.md) e as regras em
[data-model.md](./data-model.md).

## Pré-requisitos

- Docker + Docker Compose (PostgreSQL 16)
- Python 3.12
- Node.js ≥ 22.22 e npm

## Subir o ambiente

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

make db          # docker compose up -d db
make backend     # venv + pip install + migrate + runserver :8000
make seed        # python manage.py popular_demo (dados do protótipo)
make frontend    # npm install + npm run dev (:5173)
```

Resultado esperado: <http://localhost:5173> redireciona para `/oportunidades` com 12
oportunidades.

## Testes

```bash
make test        # pytest no backend, contra o PostgreSQL do compose
make typecheck   # react-router typegen && tsc --noEmit no frontend
```

Resultado esperado: todos os testes passam, inclusive `test_pedido_concorrente_10_requisicoes` e
um teste por modo de falha do ERP.

## Cenários de validação manual

### 1. SSR da listagem (FR-017, SC-005)

```bash
curl -s "http://localhost:5173/oportunidades?estagio=GANHO" | grep -c "<tr"
```

O HTML já vem com as linhas da tabela, sem skeleton. Com JavaScript desativado no navegador, a
listagem, os chips e a busca continuam funcionando.

### 2. Cadastro, detalhe e edição (US1)

1. Clique em "Nova oportunidade", digite "acme" no campo empresa e confira a sugestão "Acme
   Logística".
2. Salve sem título: aparece a mensagem no campo e os valores continuam preenchidos.
3. Salve com título, empresa "  ACME logística " e valor 1000: você é levado ao detalhe e a
   empresa foi reaproveitada (não aparece empresa nova nas sugestões).
4. Clique em "Editar", troque o título e salve: você volta ao detalhe e o novo título aparece
   também na listagem.
5. Acesse `/oportunidades/99999`: aparece "Oportunidade não encontrada" com o link de volta.

### 3. Estágios (US3)

1. Lead → Contato → Proposta: cada clique aplica na hora.
2. Proposta → Ganho: o modal aparece; ao confirmar, o detalhe mostra a data de fechamento.
3. Em outra oportunidade, → Perdido com motivo: o detalhe exibe o motivo. Depois, → Contato: o
   modal "Reabrir oportunidade?" aparece e, ao confirmar, o motivo e a data somem.
4. Com a API: `POST /api/oportunidades/{id}/estagio` de Perdido para GANHO → 409
   `transicao_invalida`.

### 4. Pedido sem duplicidade (US2, SC-002)

Com uma oportunidade em Ganho e valor > 0 (`ERP_MODO=sucesso`):

```bash
for i in $(seq 10); do curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  http://localhost:8000/api/oportunidades/{id}/pedido & done; wait
```

Resultado esperado: um `201` e nove `200`. O detalhe mostra um único "#ERP-…", e a barra de
estágios aparece bloqueada.

### 5. Falhas do ERP e retry (US2, SC-003, SC-004)

Para cada modo `timeout`, `erro` e `resposta_invalida`:

1. Ajuste `ERP_MODO=<modo>` em `backend/.env` e reinicie `make backend`.
2. Clique em "Gerar pedido": aparece a mensagem específica do modo, com as tentativas e o botão
   "Tentar novamente". A listagem mostra "Falha no pedido".
3. Volte para `ERP_MODO=sucesso`, reinicie e clique em "Tentar novamente": o pedido é gerado com
   `tentativas` incrementado e **o mesmo** `referencia_externa`.

### 6. Regras de bloqueio

- Oportunidade em Proposta: o botão aparece desabilitado com "Disponível quando a oportunidade
  estiver em Ganho". `POST .../pedido` → 409 `estagio_invalido`.
- Oportunidade em Ganho sem valor: `POST .../pedido` → 409 `valor_obrigatorio`.
- Oportunidade com pedido gerado: `POST .../estagio` → 409 `estagio_bloqueado`.

### 7. Filtros e busca (US4)

1. Clique no chip "Ganho" e busque "horizonte": a URL passa a ser
   `?estagio=GANHO&q=horizonte`. Recarregue a página e confira que a mesma visão aparece.
2. Busque "xyz": aparece "Nada encontrado" com "Limpar filtros".
3. Com o banco vazio (`make reset-db`), a listagem mostra "Nenhuma oportunidade ainda".
