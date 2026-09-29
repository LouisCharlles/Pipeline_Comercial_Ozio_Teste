import { sugerirEmpresas } from "../features/oportunidades/api.server";
import type { Route } from "./+types/empresas.sugestoes";

// Resource route: o campo empresa busca sugestões aqui, e daqui o servidor chama a API.
export async function loader({ request }: Route.LoaderArgs) {
  const q = new URL(request.url).searchParams.get("q") ?? "";
  const resposta = await sugerirEmpresas(q);
  return Response.json(resposta.ok ? resposta.dados : []);
}
