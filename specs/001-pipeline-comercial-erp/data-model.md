# Data Model: Mini Pipeline Comercial com Integração ERP

**Feature**: `001-pipeline-comercial-erp` | **Data**: 2026-09-29 | Base: [spec.md](./spec.md),
[research.md](./research.md)

Os três modelos ficam no app Django `comercial`. Nomes de campos em português, sem acento, iguais
aos do JSON da API ([contracts/api.md](./contracts/api.md)).

```text
Empresa 1 ──── N Oportunidade 1 ──── 0..1 Pedido
```

---

## Empresa

| Campo | Tipo | Regras |
|---|---|---|
| `id` | bigint PK | |
| `nome` | varchar(200) | obrigatório; espaços nas pontas removidos antes de gravar; **único sem diferenciar maiúsculas/minúsculas** (`UniqueConstraint(Lower("nome"))`) |
| `criado_em` | timestamptz | `auto_now_add` |

- Criada **implicitamente** a partir do nome digitado no formulário da oportunidade (FR-003):
  procura por `nome__iexact` e, se não encontrar, cria. Em caso de corrida, o `IntegrityError` da
  constraint é capturado e a empresa é buscada de novo.
- Não é removida pela aplicação. A FK das oportunidades usa `PROTECT` (Edge Case "empresa não pode
  ficar com oportunidades órfãs").
- Índice para as sugestões: a busca `nome__icontains` é suficiente para o volume (≤ 1.000).

## Oportunidade

| Campo | Tipo | Regras |
|---|---|---|
| `id` | bigint PK | |
| `titulo` | varchar(200) | obrigatório; espaços nas pontas removidos; não pode ficar vazio |
| `empresa` | FK → Empresa | obrigatório; `on_delete=PROTECT`; `related_name="oportunidades"` |
| `valor` | numeric(14,2), nulo | opcional; `≥ 0` (`CheckConstraint`); em reais |
| `estagio` | varchar(10), `TextChoices` | `LEAD` · `CONTATO` · `PROPOSTA` · `GANHO` · `PERDIDO`; padrão `LEAD`; indexado |
| `motivo_perda` | text | vazio por padrão; só preenchido em `PERDIDO` |
| `fechado_em` | timestamptz, nulo | preenchido ao entrar em `GANHO`/`PERDIDO`; limpo ao reabrir |
| `criado_em` | timestamptz | `auto_now_add` |
| `atualizado_em` | timestamptz | `auto_now` |

- **Ordenação padrão**: `-atualizado_em, -id` (o que foi mexido por último aparece primeiro).
- **Busca** (`q`): `titulo__icontains` OU `empresa__nome__icontains`, com `q` sem espaços nas
  pontas; se `q` ficar vazio, não filtra.
- **Criação** (FR-001): o estágio inicial é restrito a `LEAD`, `CONTATO` e `PROPOSTA`. `GANHO` e
  `PERDIDO` são recusados com erro de campo.
- **Edição** (FR-005): só aceita `titulo`, `empresa` e `valor`. O estágio **não** é alterado por
  esse caminho. Editar o valor não afeta o pedido já existente, que guarda a própria cópia.
- **Constraints de banco**:
  - `valor IS NULL OR valor >= 0`;
  - `estagio IN (...)`;
  - `(estagio IN ('GANHO','PERDIDO')) = (fechado_em IS NOT NULL)`, para que nenhuma oportunidade
    aberta tenha data de fechamento e vice-versa.

### Estágios e transições (FR-007 a FR-013)

Abertos: `LEAD`, `CONTATO`, `PROPOSTA`. Finais: `GANHO`, `PERDIDO`.

| De \ Para | LEAD / CONTATO / PROPOSTA | GANHO | PERDIDO |
|---|---|---|---|
| **Aberto** | ✅ livre, sem confirmação | ✅ com confirmação | ✅ com confirmação + motivo opcional |
| **GANHO** sem pedido GERADO | ✅ reabre (limpa `fechado_em`) | — | ✅ com confirmação + motivo opcional |
| **GANHO** com pedido GERADO | ❌ `estagio_bloqueado` | — | ❌ `estagio_bloqueado` |
| **PERDIDO** | ✅ reabre, com confirmação (limpa `fechado_em` e `motivo_perda`) | ❌ `transicao_invalida` | — |

Regras aplicadas pelo serviço `mudar_estagio(oportunidade_id, destino, motivo_perda="")`:

1. Roda em `transaction.atomic()` com `select_for_update()` na oportunidade, para não correr em
   paralelo com `gerar_pedido`.
2. Se o destino for igual ao estágio atual, não faz nada e devolve a oportunidade.
3. Se houver pedido com status `GERADO`, a mudança é recusada com `estagio_bloqueado` (FR-012).
4. A transição é checada na tabela acima; se não estiver permitida, é recusada com
   `transicao_invalida` e o estágio atual é mantido (FR-013).
5. Entrar em `GANHO` ou `PERDIDO` grava `fechado_em = now()`. Sair para um estágio aberto limpa
   `fechado_em`.
6. Entrar em `PERDIDO` grava `motivo_perda` (texto livre, opcional, até 500 caracteres). Qualquer
   outro destino limpa o motivo.
7. Um pedido `FALHOU` **não** bloqueia a mudança e continua registrado. Ele só pode ser retomado
   quando a oportunidade voltar a `GANHO` (Edge Case 4).

A confirmação ao ir para Ganho/Perdido e ao reabrir de Perdido é **responsabilidade da tela**
(modal). O backend aplica as regras, mas não exige um "token de confirmação".

## Pedido

| Campo | Tipo | Regras |
|---|---|---|
| `id` | bigint PK | |
| `oportunidade` | OneToOne → Oportunidade | **UNIQUE** (garantia do Princípio III); `on_delete=PROTECT`; `related_name="pedido"` |
| `referencia_externa` | varchar(40) | **UNIQUE**; `"OPP-{oportunidade_id}"`; enviada ao ERP em toda tentativa (FR-025) |
| `valor` | numeric(14,2) | cópia de `oportunidade.valor` na **primeira** tentativa; `> 0` (`CheckConstraint`) |
| `status` | varchar(10), `TextChoices` | `PENDENTE` · `GERADO` · `FALHOU` |
| `numero_erp` | varchar(40), nulo | **UNIQUE** quando não nulo; obrigatório se `GERADO`, nulo caso contrário |
| `tentativas` | int | ≥ 1; incrementado a cada chamada ao ERP |
| `ultimo_erro_tipo` | varchar(20) | `""` · `TEMPO_ESGOTADO` · `ERRO_SERVICO` · `RESPOSTA_INVALIDA` |
| `ultimo_erro` | text | mensagem técnica da última falha; vazio quando `GERADO` |
| `gerado_em` | timestamptz, nulo | momento do sucesso (a "data do pedido" exibida no card) |
| `criado_em` | timestamptz | `auto_now_add` |
| `atualizado_em` | timestamptz | `auto_now` |

- **Constraints de banco**:
  - `(status = 'GERADO') = (numero_erp IS NOT NULL)`, para que nunca exista "gerado sem número"
    (SC-003);
  - `(status = 'GERADO') = (gerado_em IS NOT NULL)`;
  - `valor > 0`.

### Ciclo de vida do pedido

```text
                 (gerar_pedido, 1ª vez)
 [sem pedido] ───────────────► PENDENTE ──ERP ok──────► GERADO   (final, imutável)
                                   │
                                   └──ERP falha──► FALHOU ──"Tentar novamente"──► PENDENTE ─► …
```

- `PENDENTE` só existe **dentro** da transação de `gerar_pedido`. Todo commit termina em `GERADO`
  ou `FALHOU`. Se o processo morrer no meio, o rollback volta ao estado anterior: "sem pedido" ou o
  `FALHOU` anterior (ver research R3).
- O retry reaproveita a **mesma linha**, a mesma `referencia_externa` e o mesmo `valor` copiado
  (FR-025). O `valor` **não** é atualizado no retry, mesmo que a oportunidade tenha sido editada
  depois da primeira tentativa.
- `GERADO` é final: nenhuma operação altera um pedido gerado.

### Serviço `gerar_pedido(oportunidade_id)` (FR-019 a FR-026)

1. Abre `transaction.atomic()` e trava a oportunidade com `select_for_update()` (espera o lock).
2. Se já houver pedido `GERADO`, devolve esse pedido com `criado=False` → HTTP 200, **sem
   chamar o ERP** (FR-021).
3. Se `estagio != GANHO`, recusa com `estagio_invalido` (409).
4. Se o valor for nulo ou ≤ 0, recusa com `valor_obrigatorio` (409). Essa verificação só se
   aplica quando ainda não existe pedido; num retry vale o valor copiado.
5. Obtém o pedido `FALHOU` existente ou cria um novo `PENDENTE` com `valor` e
   `referencia_externa`.
6. Grava `status=PENDENTE` e `tentativas += 1`, e chama `ClienteErp.criar_pedido(referencia,
   valor)`.
7. **Sucesso**: grava `GERADO`, `numero_erp` e `gerado_em`, e limpa os campos de erro → 201.
8. **Falha**: grava `FALHOU`, `ultimo_erro_tipo` e `ultimo_erro` → 504 ou 502, com o pedido no
   corpo da resposta.
9. Um `IntegrityError` em qualquer ponto → rollback, nova leitura e retorno do pedido existente
   (200).
