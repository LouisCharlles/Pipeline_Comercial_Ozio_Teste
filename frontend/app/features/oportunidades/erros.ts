import type { ErroApi, TipoErroErp } from "./types";

const MENSAGENS: Record<string, string> = {
  validacao: "Corrija os campos destacados.",
  nao_encontrado: "Oportunidade não encontrada.",
  transicao_invalida: "Essa mudança de estágio não é permitida.",
  estagio_bloqueado: "Oportunidade com pedido gerado não pode mudar de estágio.",
  estagio_invalido: "Disponível quando a oportunidade estiver em Ganho.",
  valor_obrigatorio: "Informe um valor maior que zero antes de gerar o pedido.",
  erp_tempo_esgotado: "O ERP não respondeu a tempo. Tente novamente.",
  erp_erro_servico: "O ERP retornou um erro. Tente novamente.",
  erp_resposta_invalida: "O ERP enviou uma resposta inesperada. Tente novamente.",
  erro_interno: "Erro inesperado. Tente novamente.",
  rede: "Não foi possível falar com o servidor. Tente novamente.",
};

export function mensagemDeErro(erro: Pick<ErroApi, "codigo" | "mensagem">): string {
  // Para transições inválidas o backend explica origem e destino; preferimos a mensagem dele.
  if (erro.codigo === "transicao_invalida" && erro.mensagem) return erro.mensagem;
  return MENSAGENS[erro.codigo] ?? erro.mensagem ?? "Erro inesperado. Tente novamente.";
}

const MENSAGENS_FALHA_ERP: Record<Exclude<TipoErroErp, "">, string> = {
  TEMPO_ESGOTADO: MENSAGENS.erp_tempo_esgotado,
  ERRO_SERVICO: MENSAGENS.erp_erro_servico,
  RESPOSTA_INVALIDA: MENSAGENS.erp_resposta_invalida,
};

export function mensagemDeFalhaErp(tipo: TipoErroErp): string {
  return tipo ? MENSAGENS_FALHA_ERP[tipo] : "A última tentativa de gerar o pedido não foi concluída.";
}
