import { isRouteErrorResponse, redirect } from "react-router";

import { ErrorState } from "../components/ui/ErrorState";
import { NaoEncontrado } from "../components/ui/NaoEncontrado";
import { VoltarLink } from "../components/ui/VoltarLink";
import { editarOportunidade } from "../features/oportunidades/api.server";
import { carregarOportunidade } from "../features/oportunidades/carregar.server";
import { OportunidadeForm } from "../features/oportunidades/components/OportunidadeForm";
import { mensagemDeErro } from "../features/oportunidades/erros";
import { valorParaCampo } from "../features/oportunidades/formato";
import { erroDeFormulario, lerFormulario } from "../features/oportunidades/formulario.server";
import type { Route } from "./+types/oportunidades.$id.editar";

export function meta({ loaderData }: Route.MetaArgs) {
  return [{ title: `Editar ${loaderData?.titulo ?? "oportunidade"} · Pipeline Comercial` }];
}

export async function loader({ params }: Route.LoaderArgs) {
  return carregarOportunidade(params.id);
}

export async function action({ request, params }: Route.ActionArgs) {
  const { valores, dados } = lerFormulario(await request.formData());
  const resposta = await editarOportunidade(params.id, { titulo: dados.titulo, empresa: dados.empresa, valor: dados.valor });
  if (resposta.ok) return redirect(`/oportunidades/${params.id}`);
  return erroDeFormulario(resposta.erro, resposta.status, valores);
}

export default function EditarOportunidade({ loaderData: op, actionData }: Route.ComponentProps) {
  const erroGeral = actionData && actionData.codigo !== "validacao" ? mensagemDeErro(actionData) : undefined;
  const iniciais = { titulo: op.titulo, empresa: op.empresa.nome, valor: valorParaCampo(op.valor) };
  return (
    <div className="flex max-w-lg flex-col gap-6">
      <VoltarLink to={`/oportunidades/${op.id}`} />
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Editar oportunidade</h1>
        <p className="mt-0.5 text-sm text-slate-500">O estágio é alterado pelo detalhe da oportunidade.</p>
      </div>
      <OportunidadeForm
        key={JSON.stringify(actionData?.valores ?? {})}
        valores={{ ...iniciais, ...actionData?.valores }}
        campos={actionData?.campos}
        erroGeral={erroGeral}
        mostrarEstagio={false}
        rotuloEnviar="Salvar alterações"
        rotuloEnviando="Salvando…"
        cancelarPara={`/oportunidades/${op.id}`}
      />
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
