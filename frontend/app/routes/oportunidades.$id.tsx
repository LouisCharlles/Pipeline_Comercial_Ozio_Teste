import { data, isRouteErrorResponse, Link } from "react-router";

import { classesBotao } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { NaoEncontrado } from "../components/ui/NaoEncontrado";
import { StageBadge } from "../components/ui/StageBadge";
import { VoltarLink } from "../components/ui/VoltarLink";
import { gerarPedido, mudarEstagio } from "../features/oportunidades/api.server";
import { carregarOportunidade } from "../features/oportunidades/carregar.server";
import { BarraEstagios } from "../features/oportunidades/components/BarraEstagios";
import { CardPedido } from "../features/oportunidades/components/CardPedido";
import { formatarData, formatarMoeda } from "../features/oportunidades/formato";
import type { Estagio, ResultadoAcao } from "../features/oportunidades/types";
import type { Route } from "./+types/oportunidades.$id";

export function meta({ loaderData }: Route.MetaArgs) {
  return [{ title: `${loaderData?.titulo ?? "Oportunidade"} · Pipeline Comercial` }];
}

export async function loader({ params }: Route.LoaderArgs) {
  return carregarOportunidade(params.id);
}

// Erros de ação voltam com status 200 de propósito: assim o React Router revalida o loader e a
// tela mostra o estado gravado (ex.: pedido FALHOU com tentativas), não só a mensagem.
export async function action({ request, params }: Route.ActionArgs): Promise<ResultadoAcao> {
  const form = await request.formData();
  const intent = form.get("intent");

  if (intent === "gerar-pedido") {
    const resposta = await gerarPedido(params.id);
    return resposta.ok ? { ok: true } : { ok: false, ...resposta.erro };
  }

  if (intent === "mudar-estagio") {
    const motivo = form.get("motivo_perda");
    const resposta = await mudarEstagio(
      params.id,
      String(form.get("estagio") ?? "") as Estagio,
      motivo === null ? undefined : String(motivo),
    );
    return resposta.ok ? { ok: true } : { ok: false, ...resposta.erro };
  }

  throw data({ codigo: "validacao", mensagem: "Ação desconhecida." }, { status: 400 });
}

export default function DetalheOportunidade({ loaderData: op }: Route.ComponentProps) {
  return (
    <div className="flex flex-col gap-6">
      <VoltarLink to="/oportunidades" />

      <div className="grid items-start gap-6 md:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-5">
          <section className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex flex-col gap-1.5">
              <div className="flex items-start justify-between gap-4">
                <h1 className="text-lg font-semibold leading-snug text-slate-900">{op.titulo}</h1>
                <div className="flex shrink-0 items-center gap-2">
                  <StageBadge stage={op.estagio} />
                  <Link to={`/oportunidades/${op.id}/editar`} className={classesBotao("secondary", "sm")}>
                    Editar
                  </Link>
                </div>
              </div>
              <p className="text-sm text-slate-500">{op.empresa.nome}</p>
              <p className="mt-1 text-xl font-semibold tabular-nums text-slate-900">{formatarMoeda(op.valor)}</p>
              {op.estagio === "PERDIDO" && op.motivo_perda && (
                <div className="mt-1 border-t border-slate-100 pt-3">
                  <p className="mb-1 text-xs font-medium text-slate-500">Motivo da perda</p>
                  <p className="text-sm text-slate-700">{op.motivo_perda}</p>
                </div>
              )}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-3 text-xs text-slate-400">
              <span>
                Criado em <span className="font-medium text-slate-600">{formatarData(op.criado_em)}</span>
              </span>
              <span>
                Atualizado em <span className="font-medium text-slate-600">{formatarData(op.atualizado_em)}</span>
              </span>
              {op.fechado_em && (
                <span>
                  Fechado em <span className="font-medium text-slate-600">{formatarData(op.fechado_em)}</span>
                </span>
              )}
            </div>
          </section>

          <BarraEstagios oportunidade={op} />
        </div>

        <CardPedido oportunidade={op} />
      </div>
    </div>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  return (
    <div className="flex flex-col gap-6">
      <VoltarLink to="/oportunidades" />
      {isRouteErrorResponse(error) && error.status === 404 ? (
        <NaoEncontrado />
      ) : (
        <ErrorState title="Não foi possível carregar a oportunidade" />
      )}
    </div>
  );
}
