# Contrato de UI: rotas do React Router 8 (modo framework, SSR)

Referência visual: protótipo Figma Make "Mini-CRM-B2B-Prototype", com os ajustes da seção
Clarifications da [spec](../spec.md). Todas as chamadas à API são feitas no servidor
(`app/features/oportunidades/api.server.ts`, com `API_URL`).

| Rota (URL) | Módulo | loader | action | Observações |
|---|---|---|---|---|
| `/` | `routes/home.tsx` | `redirect("/oportunidades")` | — | |
| `/oportunidades?estagio=&q=` | `routes/oportunidades._index.tsx` | `GET /api/oportunidades` | — | **SSR** (FR-017); chips = links que preservam `q`; busca = `<Form method="get">` com botão "Buscar" |
| `/oportunidades/nova` | `routes/oportunidades.nova.tsx` | — | `POST /api/oportunidades` → `redirect` ao detalhe | select de estágio só com Lead/Contato/Proposta |
| `/oportunidades/:id` | `routes/oportunidades.$id.tsx` | `GET /api/oportunidades/:id` (404 → `throw data(..., {status: 404})`) | `intent=mudar-estagio` → `POST .../estagio`; `intent=gerar-pedido` → `POST .../pedido` | barra de estágios + card "Pedido no ERP" |
| `/oportunidades/:id/editar` | `routes/oportunidades.$id.editar.tsx` | `GET /api/oportunidades/:id` | `PATCH` → `redirect` ao detalhe | mesmo `<OportunidadeForm>`, sem estágio |
| `/empresas/sugestoes?q=` | `routes/empresas.sugestoes.ts` (resource route) | `GET /api/empresas?q=` | — | usada via `useFetcher().load` no campo empresa |

## Retorno das actions (erro)

```ts
type ResultadoAcao =
  | { ok: false; codigo: string; mensagem: string; campos?: Record<string, string[]>; pedido?: Pedido | null }
```

Em caso de sucesso, a action faz `redirect` (formulários) ou retorna `{ ok: true }`, e o loader
revalida (detalhe).

## Estados por tela

| Tela | Carregando | Erro de carga | Erro de ação | Vazio |
|---|---|---|---|---|
| Listagem | 1ª carga via SSR (sem indicador); filtros → `<PendingBar>` + opacidade | `ErrorBoundary`: "Não foi possível carregar" + "Tentar novamente" | — | "Nenhuma oportunidade ainda" + "Nova oportunidade" / "Nada encontrado" + "Limpar filtros" |
| Formulário (nova/editar) | botão "Criando…"/"Salvando…" desabilitado, campos desabilitados | editar: 404 → "Oportunidade não encontrada" | `campos` junto aos campos + `<Alert>` geral no topo; valores mantidos | — |
| Detalhe | 1ª carga via SSR; navegação → `<PendingBar>` (tela anterior mantida até os dados chegarem); envios com botão desabilitado e texto de progresso | 404 → "Oportunidade não encontrada" + "Voltar para oportunidades"; outros → "Não foi possível carregar" | `<Alert>` no bloco afetado (barra de estágio ou card Pedido) | — |

## Card "Pedido no ERP" (detalhe)

| Estado | Condição | Conteúdo |
|---|---|---|
| Indisponível | estágio ≠ GANHO e sem pedido GERADO | botão desabilitado + "Disponível quando a oportunidade estiver em Ganho" |
| Sem valor | GANHO, sem pedido, valor nulo/0 | botão desabilitado + "Informe um valor maior que zero antes de gerar o pedido" + link "Editar" |
| Pronto | GANHO, sem pedido, valor > 0 | botão primário "Gerar pedido" + "Nenhum pedido gerado ainda." |
| Enviando | `fetcher.state !== "idle"` com `intent=gerar-pedido` | botão desabilitado com spinner "Gerando pedido…"; barra de estágios desabilitada |
| Gerado | `pedido.status = GERADO` | "#ERP-…" + selo "Gerado" + "Gerado em" + "Valor"; sem botão; barra de estágios substituída por "Pedido gerado — estágio bloqueado" |
| Falhou | `pedido.status = FALHOU` e estágio GANHO | `<Alert>` com a mensagem do tipo de falha + "Você pode tentar novamente sem risco de duplicar o pedido." + Tentativas + Último erro + botão "Tentar novamente" |
| Falhou fora de Ganho | `pedido.status = FALHOU` e estágio ≠ GANHO | aviso "Tentativa anterior não concluída. Volte a oportunidade para Ganho para tentar novamente." + tentativas |

## Barra de estágios (detalhe)

- Mostra cinco botões. O estágio atual fica destacado (azul se aberto, verde em Ganho, vermelho
  em Perdido).
- Clicar num estágio aberto a partir de outro aberto envia `intent=mudar-estagio` direto.
- Clicar em Ganho abre o modal "Marcar como Ganho?". Clicar em Perdido abre o modal "Marcar como
  Perdido?" com o campo "Motivo da perda (opcional)". Em Perdido, clicar num estágio aberto abre o
  modal "Reabrir oportunidade?". Ganho fica desabilitado, com a dica "Reabra a oportunidade antes
  de marcá-la como Ganho".
- Durante o envio, todos os botões ficam desabilitados.

## Listagem: coluna "Pedido"

- `GERADO` → selo verde "Pedido #ERP-…".
- `FALHOU` → selo vermelho "Falha no pedido" (como no protótipo).
- Sem pedido → vazio.
