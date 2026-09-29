import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("oportunidades", "routes/oportunidades._index.tsx"),
  route("oportunidades/nova", "routes/oportunidades.nova.tsx"),
  route("oportunidades/:id", "routes/oportunidades.$id.tsx"),
  route("oportunidades/:id/editar", "routes/oportunidades.$id.editar.tsx"),
  route("empresas/sugestoes", "routes/empresas.sugestoes.ts"),
] satisfies RouteConfig;
