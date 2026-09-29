import { data, Link, useNavigation } from "react-router";

import { classesBotao } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { listarOportunidades } from "../features/oportunidades/api.server";
import { BuscaOportunidades } from "../features/oportunidades/components/BuscaOportunidades";
import { FiltroEstagios } from "../features/oportunidades/components/FiltroEstagios";
import { TabelaOportunidades } from "../features/oportunidades/components/TabelaOportunidades";
import { ROTULO_ESTAGIO } from "../features/oportunidades/formato";
import { ESTAGIOS, type Estagio } from "../features/oportunidades/types";
import type { Route } from "./+types/oportunidades._index";

export function meta() {
  return [{ title: "Oportunidades · Pipeline Comercial" }];
}

// Roda no servidor: a primeira resposta já traz o HTML com a tabela preenchida (FR-017), e
// filtro e busca vêm da URL (FR-016).
export async function loader({ request }: Route.LoaderArgs) {
  const params = new URL(request.url).searchParams;
  const estagioParam = params.get("estagio");
  const estagio = ESTAGIOS.includes(estagioParam as Estagio) ? (estagioParam as Estagio) : null;
  const q = (params.get("q") ?? "").trim();

  const resposta = await listarOportunidades({ estagio, q });
  if (!resposta.ok) throw data(resposta.erro, { status: resposta.status });
  return { ...resposta.dados, estagio, q };
}

export default function Oportunidades({ loaderData }: Route.ComponentProps) {
  const { resultados, contagens, total_cadastradas, estagio, q } = loaderData;
  const navigation = useNavigation();
  const atualizando = navigation.state === "loading" && navigation.location.pathname === "/oportunidades";

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-slate-900">Oportunidades</h1>

      {total_cadastradas === 0 ? (
        <EmptyState
          title="Nenhuma oportunidade ainda"
          description="Crie sua primeira oportunidade para começar."
          action={
            <Link to="/oportunidades/nova" className={classesBotao("primary", "md")}>
              Nova oportunidade
            </Link>
          }
        />
      ) : (
        <>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <FiltroEstagios contagens={contagens} estagio={estagio} q={q} />
            <BuscaOportunidades q={q} estagio={estagio} />
          </div>

          <div aria-busy={atualizando} className={`transition-opacity ${atualizando ? "opacity-60" : ""}`}>
            {resultados.length === 0 ? (
              <EmptyState
                icon="busca"
                title="Nada encontrado"
                description={`Nenhum resultado${q ? ` para “${q}”` : ""}${estagio ? ` em ${ROTULO_ESTAGIO[estagio]}` : ""}.`}
                action={
                  <Link to="/oportunidades" className={classesBotao("secondary", "sm")}>
                    Limpar filtros
                  </Link>
                }
              />
            ) : (
              <TabelaOportunidades oportunidades={resultados} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function ErrorBoundary() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-slate-900">Oportunidades</h1>
      <ErrorState title="Não foi possível carregar as oportunidades" />
    </div>
  );
}
