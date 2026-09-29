import { data, Link } from "react-router";

import { classesBotao } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { listarOportunidades } from "../features/oportunidades/api.server";
import { TabelaOportunidades } from "../features/oportunidades/components/TabelaOportunidades";
import type { Route } from "./+types/oportunidades._index";

export function meta() {
  return [{ title: "Oportunidades · Pipeline Comercial" }];
}

// Roda no servidor: a primeira resposta já traz o HTML com a tabela preenchida (FR-017).
export async function loader() {
  const resposta = await listarOportunidades({});
  if (!resposta.ok) throw data(resposta.erro, { status: resposta.status });
  return resposta.dados;
}

export default function Oportunidades({ loaderData }: Route.ComponentProps) {
  const { resultados, total_cadastradas } = loaderData;
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
        <TabelaOportunidades oportunidades={resultados} />
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
