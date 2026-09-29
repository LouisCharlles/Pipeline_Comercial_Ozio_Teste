# Contrato da API REST (Django + DRF)

**Base**: `/api` · **Formato**: JSON UTF-8 · **Autenticação**: nenhuma (fora de escopo)

Consumida **apenas** pelo servidor do React Router (research R8). Os tipos TypeScript em
`frontend/app/features/oportunidades/types.ts` espelham este documento, e os dois MUST ser
atualizados juntos (restrição técnica da constituição).

## Convenções

- Valores monetários são strings decimais com 2 casas (`"85000.00"`) ou `null`.
- Datas seguem ISO 8601 com fuso (`"2026-09-29T14:03:00-03:00"`).
- Estágios: `"LEAD" | "CONTATO" | "PROPOSTA" | "GANHO" | "PERDIDO"`.
- **Corpo de erro** (todos os status 4xx e 5xx controlados):

```json
{
  "codigo": "validacao",
  "mensagem": "Corrija os campos destacados.",
  "campos": { "titulo": ["Informe o título da oportunidade."] },
  "pedido": null
}
```

`campos` só aparece em erros de validação (400). `pedido` só aparece nas falhas do ERP (502 e
504).

| `codigo` | HTTP | Quando |
|---|---|---|
| `validacao` | 400 | payload inválido (erros em `campos`) |
| `nao_encontrado` | 404 | oportunidade inexistente |
| `transicao_invalida` | 409 | mudança de estágio não permitida |
| `estagio_bloqueado` | 409 | oportunidade com pedido GERADO |
| `estagio_invalido` | 409 | gerar pedido fora de Ganho |
| `valor_obrigatorio` | 409 | gerar pedido sem valor ou com valor zero |
| `erp_tempo_esgotado` | 504 | ERP não respondeu a tempo |
| `erp_erro_servico` | 502 | ERP respondeu com erro |
| `erp_resposta_invalida` | 502 | ERP respondeu fora do contrato |
| `erro_interno` | 500 | inesperado (não deve ocorrer nos fluxos cobertos) |

## Representações

**OportunidadeResumo** (item da listagem)

```json
{
  "id": 6,
  "titulo": "Gestão de Frotas Integrada",
  "empresa": { "id": 1, "nome": "Acme Logística" },
  "valor": "95000.00",
  "estagio": "GANHO",
  "pedido_status": "FALHOU",
  "pedido_numero_erp": null,
  "atualizado_em": "2026-09-25T10:00:00-03:00"
}
```

`pedido_status` e `pedido_numero_erp` ficam `null` quando não há pedido.

**Pedido**

```json
{
  "id": 3,
  "referencia_externa": "OPP-6",
  "status": "FALHOU",
  "numero_erp": null,
  "valor": "95000.00",
  "tentativas": 2,
  "ultimo_erro_tipo": "TEMPO_ESGOTADO",
  "ultimo_erro": "ERP não respondeu em 5s",
  "gerado_em": null,
  "criado_em": "2026-09-25T09:58:00-03:00",
  "atualizado_em": "2026-09-25T10:00:00-03:00"
}
```

**Oportunidade** (detalhe)

```json
{
  "id": 6,
  "titulo": "Gestão de Frotas Integrada",
  "empresa": { "id": 1, "nome": "Acme Logística" },
  "valor": "95000.00",
  "estagio": "GANHO",
  "motivo_perda": "",
  "fechado_em": "2026-09-24T17:20:00-03:00",
  "criado_em": "2026-07-03T09:00:00-03:00",
  "atualizado_em": "2026-09-25T10:00:00-03:00",
  "pedido": { "...": "Pedido ou null" }
}
```

---

## Endpoints

### `GET /api/oportunidades`

Listagem com filtro e busca (FR-014, FR-015).

| Query | Tipo | Regra |
|---|---|---|
| `estagio` | estágio, opcional | ausente ou inválido → todos |
| `q` | string, opcional | espaços nas pontas são removidos; vazio → sem busca; `icontains` em título OU nome da empresa |

**200**

```json
{
  "resultados": [ "OportunidadeResumo..." ],
  "contagens": { "TODOS": 12, "LEAD": 3, "CONTATO": 3, "PROPOSTA": 1, "GANHO": 4, "PERDIDO": 1 },
  "total_cadastradas": 12
}
```

- `contagens` aplica `q` e **ignora** `estagio` (research R7).
- `total_cadastradas` conta as oportunidades sem nenhum filtro. É o que diferencia "Nenhuma
  oportunidade ainda" (`0`) de "Nada encontrado" (FR-018).
- Sem paginação. O volume esperado é ≤ 1.000 (SC-005).

### `POST /api/oportunidades`

Cria uma oportunidade (FR-001 a FR-003).

```json
{ "titulo": "Contrato de Serviços TI", "empresa": "acme logística ", "valor": "75000", "estagio": "LEAD" }
```

| Campo | Regra | Mensagem de erro |
|---|---|---|
| `titulo` | obrigatório, ≤ 200, com trim | "Informe o título da oportunidade." |
| `empresa` | nome obrigatório, ≤ 200, com trim; reaproveitado por `iexact` ou criado | "Informe a empresa." |
| `valor` | opcional (`null` ou `""` → nulo); decimal ≥ 0 | "Informe um valor numérico." / "O valor não pode ser negativo." |
| `estagio` | opcional, padrão `LEAD`; só `LEAD`, `CONTATO` ou `PROPOSTA` | "Escolha Lead, Contato ou Proposta." |

**201** → `Oportunidade` · **400** `validacao`

### `GET /api/oportunidades/{id}`

**200** → `Oportunidade` (com `pedido` embutido) · **404** `nao_encontrado`

### `PATCH /api/oportunidades/{id}`

Edita `titulo`, `empresa` e `valor` (FR-005), com as mesmas regras do POST. Os campos são
opcionais, e só os enviados são alterados. Os campos `estagio`, `motivo_perda` e `fechado_em` são
**ignorados/recusados** (400 `validacao` se `estagio` vier no corpo).

**200** → `Oportunidade` · **400** · **404**

### `POST /api/oportunidades/{id}/estagio`

Muda o estágio (FR-007 a FR-013; tabela de transições em [data-model.md](../data-model.md)).

```json
{ "estagio": "PERDIDO", "motivo_perda": "Orçamento aprovado para concorrente" }
```

`motivo_perda` é opcional, com até 500 caracteres, e só é considerado quando `estagio =
PERDIDO`.

**200** → `Oportunidade` · **400** `validacao` (estágio desconhecido) · **404** · **409**
`transicao_invalida` | `estagio_bloqueado`

### `POST /api/oportunidades/{id}/pedido`

Gera o pedido no ERP ou faz uma nova tentativa (FR-019 a FR-026). Não recebe corpo. É
**idempotente** por oportunidade.

| Resultado | HTTP | Corpo |
|---|---|---|
| Pedido criado agora | **201** | `Pedido` (GERADO) |
| Já havia pedido GERADO | **200** | `Pedido` existente; o ERP não é chamado |
| Fora de Ganho / sem valor | **409** | erro `estagio_invalido` / `valor_obrigatorio`; o ERP não é chamado |
| Tempo esgotado | **504** | erro `erp_tempo_esgotado` + `pedido` (FALHOU) |
| Erro do ERP / resposta inválida | **502** | erro `erp_erro_servico` / `erp_resposta_invalida` + `pedido` (FALHOU) |
| Oportunidade inexistente | **404** | erro `nao_encontrado` |

Garantia: N chamadas sequenciais ou simultâneas deixam **no máximo 1** linha em `Pedido` para a
oportunidade e no máximo 1 pedido criado no ERP simulado por `referencia_externa`.

### `GET /api/empresas?q=`

Sugestões para o campo empresa (FR-003).

- Com `q` (depois do trim) vazio → `[]`. Caso contrário, até 10 empresas cujo nome contém `q`,
  ordenadas por nome.

**200**

```json
[ { "id": 1, "nome": "Acme Logística" } ]
```

---

## Interface interna do ERP (não exposta via HTTP)

```text
ClienteErp.criar_pedido(referencia: str, valor: Decimal) -> RespostaErp(numero: str)
  lança ErpTempoEsgotado | ErpErroServico | ErpRespostaInvalida
```

- Implementação `ErpSimulado`, com o modo definido por `ERP_MODO` (research R4).
- Contrato da resposta bruta do simulador: `{"numero_pedido": "ERP-1042", "referencia": "OPP-6"}`.
  O cliente valida esse formato: `numero_pedido` precisa ser uma string não vazia e `referencia`
  precisa ser igual à referência enviada. Qualquer desvio → `ErpRespostaInvalida`.
