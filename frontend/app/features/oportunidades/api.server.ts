// Cliente HTTP da API Django. Só roda no servidor do React Router: o navegador nunca fala com a
// API diretamente (research R8).

import type {
  DadosOportunidade,
  Empresa,
  ErroApi,
  Estagio,
  ListagemOportunidades,
  Oportunidade,
  Pedido,
} from "./types";

const API_URL = (process.env.API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");

export type Resposta<T> = { ok: true; status: number; dados: T } | { ok: false; status: number; erro: ErroApi };

const ERRO_REDE: ErroApi = { codigo: "rede", mensagem: "Não foi possível falar com o servidor." };

async function requisitar<T>(metodo: string, caminho: string, corpo?: unknown): Promise<Resposta<T>> {
  let resposta: Response;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      method: metodo,
      headers: { Accept: "application/json", ...(corpo !== undefined && { "Content-Type": "application/json" }) },
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    });
  } catch {
    return { ok: false, status: 503, erro: ERRO_REDE };
  }

  let json: unknown;
  try {
    json = await resposta.json();
  } catch {
    return { ok: false, status: resposta.ok ? 502 : resposta.status, erro: ERRO_REDE };
  }

  if (resposta.ok) return { ok: true, status: resposta.status, dados: json as T };
  return { ok: false, status: resposta.status, erro: json as ErroApi };
}

export function listarOportunidades(filtros: { estagio?: string | null; q?: string | null }) {
  const params = new URLSearchParams();
  if (filtros.estagio) params.set("estagio", filtros.estagio);
  if (filtros.q) params.set("q", filtros.q);
  const qs = params.toString();
  return requisitar<ListagemOportunidades>("GET", `/oportunidades${qs ? `?${qs}` : ""}`);
}

export function obterOportunidade(id: string | number) {
  return requisitar<Oportunidade>("GET", `/oportunidades/${encodeURIComponent(String(id))}`);
}

export function criarOportunidade(dados: DadosOportunidade) {
  return requisitar<Oportunidade>("POST", "/oportunidades", dados);
}

export function editarOportunidade(id: string | number, dados: Omit<DadosOportunidade, "estagio">) {
  return requisitar<Oportunidade>("PATCH", `/oportunidades/${encodeURIComponent(String(id))}`, dados);
}

export function mudarEstagio(id: string | number, estagio: Estagio, motivoPerda?: string) {
  return requisitar<Oportunidade>("POST", `/oportunidades/${encodeURIComponent(String(id))}/estagio`, {
    estagio,
    ...(motivoPerda !== undefined && { motivo_perda: motivoPerda }),
  });
}

export function gerarPedido(id: string | number) {
  return requisitar<Pedido>("POST", `/oportunidades/${encodeURIComponent(String(id))}/pedido`);
}

export function sugerirEmpresas(q: string) {
  return requisitar<Empresa[]>("GET", `/empresas?q=${encodeURIComponent(q)}`);
}
