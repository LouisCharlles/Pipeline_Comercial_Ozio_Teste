import { data } from "react-router";

import { obterOportunidade } from "./api.server";

/** Loader comum do detalhe e da edição: 404 vira "Oportunidade não encontrada". */
export async function carregarOportunidade(id: string) {
  const resposta = await obterOportunidade(id);
  if (resposta.ok) return resposta.dados;
  if (resposta.status === 404) throw data(null, { status: 404 });
  throw data(resposta.erro, { status: resposta.status });
}
