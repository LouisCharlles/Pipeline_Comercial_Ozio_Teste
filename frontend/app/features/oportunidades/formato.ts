import type { Estagio } from "./types";

// Fuso fixo: servidor (SSR) e navegador precisam gerar o mesmo texto para não haver erro de
// hidratação nem data trocada perto da meia-noite.
const FUSO = "America/Sao_Paulo";

// Valores inteiros sem centavos (como no protótipo); com centavos, sempre duas casas.
const moedaInteira = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});
const moedaCentavos = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const data = new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, day: "2-digit", month: "2-digit", year: "numeric" });
const dataHora = new Intl.DateTimeFormat("pt-BR", {
  timeZone: FUSO,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatarMoeda(valor: string | null): string {
  if (valor === null || valor === "") return "—";
  const numero = Number(valor);
  return (Number.isInteger(numero) ? moedaInteira : moedaCentavos).format(numero);
}

export function formatarData(iso: string | null): string {
  return iso ? data.format(new Date(iso)) : "—";
}

export function formatarDataHora(iso: string | null): string {
  return iso ? dataHora.format(new Date(iso)) : "—";
}

export const ROTULO_ESTAGIO: Record<Estagio, string> = {
  LEAD: "Lead",
  CONTATO: "Contato",
  PROPOSTA: "Proposta",
  GANHO: "Ganho",
  PERDIDO: "Perdido",
};

/**
 * Texto digitado no campo valor → decimal aceito pela API. Aceita o formato brasileiro
 * ("1.500,50" → "1500.50"); o que não for número segue como está para a API recusar.
 */
export function normalizarValorDigitado(texto: string): string {
  const limpo = texto.replace(/R\$|\s/g, "");
  if (limpo.includes(",")) return limpo.replace(/\./g, "").replace(",", ".");
  return limpo;
}

/** Valor decimal da API ("85000.00") → texto editável no formulário ("85000"). */
export function valorParaCampo(valor: string | null): string {
  if (valor === null) return "";
  return valor.replace(/\.00$/, "");
}
