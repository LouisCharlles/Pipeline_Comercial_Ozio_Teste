# Notas de pesquisa: consolidação

> Junta `notas-codigo.md` (estudo de código do Odoo e do Twenty) e `notas-telas.md` (Pipedrive e HubSpot).
> **Atenção:** as telas do Pipedrive e do HubSpot **não foram observadas**. Aquela parte vem da documentação oficial pública (ver o aviso em `notas-telas.md`).

## 1. Modelagem sugerida

| Modelo | Campos | Regras |
|---|---|---|
| **Empresa** | `id`, `nome`*, `documento` (opcional, único quando presente), `criado_em` | 1 → N oportunidades |
| **Oportunidade** | `id`, `titulo`*, `empresa`* (FK, `PROTECT`), `valor` (Decimal ≥ 0), `estagio` (TextChoices, default `LEAD`, indexado), `motivo_perda` (opcional), `fechado_em`, `criado_em`, `atualizado_em` | busca `icontains` em `titulo` e `empresa__nome` |
| **Pedido** | `id`, `oportunidade` (**OneToOne**), `valor` (cópia do valor na geração), `status` (`PENDENTE`/`ENVIADO`/`FALHA`), `numero_erp` (único, nulo até confirmar), `tentativas`, `ultimo_erro`, `criado_em`, `atualizado_em` | no máximo 1 pedido por oportunidade, garantido pelo banco |

- O estágio é um enum porque os 5 estágios são fixos. Não há itens de pedido.
- As referências (Odoo, Pipedrive, HubSpot) usam **1 oportunidade → N cotações/pedidos**. O 1:1 é regra do desafio, não padrão de mercado.

## 2. Estágios e regras de transição

- Estágios abertos: `LEAD`, `CONTATO`, `PROPOSTA`. Estágios finais: `GANHO` e `PERDIDO`.
- Entre estágios abertos, o movimento é livre nos dois sentidos. De qualquer estágio aberto, pode ir para Ganho ou Perdido.
- `PERDIDO → aberto` é permitido (reabrir), limpando `motivo_perda` e `fechado_em`.
- `GANHO → outro` é bloqueado quando existe pedido (ver conflito nº 3 sobre o caso `FALHA`).
- `fechado_em` é preenchido automaticamente ao entrar em estágio final.
- A validação fica no **backend**. Transição inválida → 400/409 com mensagem.
- A UI mostra as opções inválidas desabilitadas e pede **confirmação** só para ir a Ganho ou Perdido.

## 3. Estratégia contra pedido duplicado

**Unicidade no banco (OneToOne) + `transaction.atomic()` com `select_for_update()` na oportunidade.** O id da oportunidade funciona como chave natural de idempotência.

1. Travar a oportunidade e validar `estagio == GANHO`.
2. Se já existe pedido `ENVIADO`, devolver o pedido existente (sem chamar o ERP). Se existe pedido `FALHA`, reaproveitar a mesma linha. Senão, criar um pedido `PENDENTE`.
3. Chamar o ERP com timeout curto e **referência externa** (id do pedido/oportunidade).
4. Gravar `ENVIADO` + `numero_erp`, ou `FALHA` + `ultimo_erro` + `tentativas += 1`.
5. Capturar `IntegrityError` como última defesa.

- No front, o botão fica desabilitado durante o envio. Isso é conveniência, não garantia.
- O teste de concorrência roda no **PostgreSQL** (no SQLite o `FOR UPDATE` é ignorado).
- Header `Idempotency-Key`: fica fora do escopo.

## 4. Simulação do ERP e falhas

- Interface `ErpClient.criar_pedido(ref, valor) → numero_erp` com uma implementação **fake em processo**. O modo é escolhido por setting ou env: `sucesso` | `timeout` | `erro` | `resposta_invalida` (opcional: `aleatorio`).
- Mapeamento das falhas:

| Falha | Status do pedido | HTTP |
|---|---|---|
| Timeout | `FALHA` ("ERP não respondeu a tempo") | 504 |
| 5xx / indisponível | `FALHA` | 502 |
| Resposta inválida | `FALHA` ("resposta inesperada do ERP") | 502 |
| Oportunidade não está em Ganho | não chama o ERP | 400/409 |

- No timeout, o ERP pode ter criado o pedido. A referência externa permite que o ERP deduplique no retry.
- O retry é manual ("Tentar novamente"), com `tentativas` e `ultimo_erro` visíveis no detalhe. Não há fila assíncrona.
- Testes: um por modo de falha + "duas chamadas → um pedido".

## 5. Telas, rotas e estados do frontend

| Rota | Conteúdo |
|---|---|
| `/oportunidades?estagio=&q=` | **SSR** via `loader`. Filtro por estágio (chips com contagem) + busca por título/empresa, **na URL** (`<Form method="get">`). Tabela: título, empresa, valor, estágio, badge do pedido. |
| `/oportunidades/nova` | Formulário com título*, empresa*, valor, estágio (default Lead). Validação zod + DRF. Redirect para o detalhe. |
| `/oportunidades/:id` | Detalhe + seletor de estágio + **card Pedido**. Actions por `intent` (`mudar-estagio`, `gerar-pedido`). |

Card Pedido (detalhes em `notas-telas.md` §2.2):
- **≠ Ganho**: botão desabilitado + explicação.
- **Ganho sem pedido**: botão "Gerar pedido".
- **Enviando**: "Gerando pedido…", com o botão e o seletor desabilitados.
- **`ENVIADO`**: o botão dá lugar a "Pedido #ERP-123" + data/valor.
- **`FALHA`**: alerta + "Tentar novamente".

Estados:
- **Loading**: SSR na carga inicial; `useNavigation`/`fetcher` para troca de filtro e submits.
- **Erro**: `ErrorBoundary` por rota para falhas de carga; `{ok:false, error, fieldErrors}` retornado pela action para falhas de ação; um helper único `apiErrorToMessage`.
- **Vazio**: `<EmptyState>` "sem dados" vs "sem resultados + limpar filtros".

Estrutura de pastas: `app/routes/` (finas), `app/features/oportunidades/{components,api,schemas,types}`, `app/components/ui/`.

## 6. O que não copiar

- **Twenty**: arquitetura por metadados, Jotai por instância, GraphQL/Apollo, views salvas.
- **Odoo**: estágio configurável, vários estágios de ganho, "perdido" como arquivamento, probabilidade/PLS, cotação `draft/sent/locked`, itens de pedido.
- **Pipedrive/HubSpot**: kanban com drag-and-drop, cards e métricas configuráveis, pipelines múltiplos, pipeline rules por permissão, filtros avançados/salvos, Smart Docs/Quotes (templates, aprovação, assinatura), atividades/e-mails/notas.
- **Infra**: tabela de idempotency key, Celery/fila, Sentry, i18n.

## 7. Conflitos e dúvidas em aberto (apontados, não resolvidos)

**Conflitos entre os arquivos (e dentro de `notas-codigo.md`)**

1. **Kanban ou tabela na listagem.** `notas-codigo.md` §5 propõe "colunas por estágio (sem drag-and-drop)". `notas-telas.md` §2.1 propõe tabela + chips de estágio, porque filtro por estágio e kanban são redundantes. É preciso escolher uma, ou tabela + kanban somente leitura como extra.
2. **"Pedido já existe": 200 ou 409?** `notas-codigo.md` §3 diz que a API devolve o pedido existente com **200** (idempotente). O mesmo arquivo, no §5, lista **409** ("pedido já existe, com link") no helper de erros. `notas-telas.md` segue o 200 (a tela só mostra o pedido).
3. **Ganho trava com pedido em `FALHA`?** `notas-codigo.md` §2 diz que Ganho → outro é bloqueado "se ainda não houver pedido" (qualquer status). O §7.3 do mesmo arquivo diz que "só trava quando `ENVIADO`". `notas-telas.md` não decide.
4. **Busca: debounce ou submit?** `notas-codigo.md` §5 deixa em aberto ("debounce leve, ou um formulário GET"). `notas-telas.md` propõe o `<Form method="get">` com submit.
5. **Perdido como estágio.** O enunciado, o HubSpot (Closed Lost) e as duas notas tratam Perdido como estágio. Odoo e Pipedrive tratam como *status* à parte. Não é conflito entre os arquivos, mas vale registrar que a modelagem segue o enunciado.

**Dúvidas em aberto**

6. **Pedido `PENDENTE` preso.** Com chamada síncrona, `PENDENTE` só fica gravado se o processo morrer no meio da chamada. Ele deve ser tratado como `FALHA` (permitir retry) ou exigir outra ação? Isso afeta o card Pedido.
7. **Valor obrigatório?** O modelo aceita `valor ≥ 0`, mas o pedido copia o valor. Dá para gerar pedido com valor vazio ou zero?
8. **Motivo de perda**: obrigatório ao ir para Perdido (como no prompt do Pipedrive) ou opcional?
9. **Empresa no formulário**: select de empresas existentes, autocomplete ou "criar pelo nome"? Precisa de CRUD próprio? (`notas-codigo.md` §7.4)
10. **Gerar pedido**: ação explícita (proposta atual) ou automática ao mover para Ganho? (`notas-codigo.md` §7.2)
11. **Transições livres** entre estágios abertos, ou restritas como nas pipeline rules do HubSpot? (`notas-codigo.md` §7.1)
12. **"React Router 8"**: confirmar a versão e o modo framework (loaders/actions com SSR). Não foi verificado.
13. **Timeout do ERP fake**: espera real (exige endpoint HTTP) ou exceção simulada? (`notas-codigo.md` §7.6)
14. **Lacunas da Parte 1**: estados vazio/loading/erro e mensagens de validação do Pipedrive e do HubSpot não foram vistos. Só com acesso às telas ou prints.
