// Leitura do formulário de oportunidade nas actions (cadastro e edição).

import { data } from "react-router";

import { normalizarValorDigitado } from "./formato";
import type { ErroApi } from "./types";

export function lerFormulario(formData: FormData) {
  const texto = (campo: string) => String(formData.get(campo) ?? "");
  const valores = {
    titulo: texto("titulo"),
    empresa: texto("empresa"),
    valor: texto("valor"),
    estagio: texto("estagio") || undefined,
  };
  const dados = { ...valores, valor: normalizarValorDigitado(valores.valor) };
  return { valores, dados };
}

/** Erro de action de formulário: devolve o erro e os valores digitados para reexibir. */
export function erroDeFormulario(erro: ErroApi, status: number, valores: Record<string, string | undefined>) {
  return data({ ok: false as const, ...erro, valores }, { status });
}
