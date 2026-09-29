import { redirect } from "react-router";

import { criarOportunidade } from "../features/oportunidades/api.server";
import { OportunidadeForm } from "../features/oportunidades/components/OportunidadeForm";
import { mensagemDeErro } from "../features/oportunidades/erros";
import { erroDeFormulario, lerFormulario } from "../features/oportunidades/formulario.server";
import type { Route } from "./+types/oportunidades.nova";

export function meta() {
  return [{ title: "Nova oportunidade · Pipeline Comercial" }];
}

export async function action({ request }: Route.ActionArgs) {
  const { valores, dados } = lerFormulario(await request.formData());
  const resposta = await criarOportunidade({ ...dados, estagio: dados.estagio ?? "LEAD" });
  if (resposta.ok) return redirect(`/oportunidades/${resposta.dados.id}`);
  return erroDeFormulario(resposta.erro, resposta.status, valores);
}

export default function NovaOportunidade({ actionData }: Route.ComponentProps) {
  const erroGeral = actionData && actionData.codigo !== "validacao" ? mensagemDeErro(actionData) : undefined;
  return (
    <div className="flex max-w-lg flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Nova oportunidade</h1>
        <p className="mt-0.5 text-sm text-slate-500">Preencha os dados para registrar a oportunidade.</p>
      </div>
      <OportunidadeForm
        // Remonta a cada resposta para reexibir exatamente o que foi digitado.
        key={JSON.stringify(actionData?.valores ?? {})}
        valores={{ titulo: "", empresa: "", valor: "", estagio: "LEAD", ...actionData?.valores }}
        campos={actionData?.campos}
        erroGeral={erroGeral}
        mostrarEstagio
        rotuloEnviar="Criar oportunidade"
        rotuloEnviando="Criando…"
        cancelarPara="/oportunidades"
      />
    </div>
  );
}
