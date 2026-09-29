// Espelho de specs/001-pipeline-comercial-erp/contracts/api.md. Atualizar os dois juntos.

export type Estagio = "LEAD" | "CONTATO" | "PROPOSTA" | "GANHO" | "PERDIDO";
export type StatusPedido = "PENDENTE" | "GERADO" | "FALHOU";
export type TipoErroErp = "" | "TEMPO_ESGOTADO" | "ERRO_SERVICO" | "RESPOSTA_INVALIDA";

export const ESTAGIOS: Estagio[] = ["LEAD", "CONTATO", "PROPOSTA", "GANHO", "PERDIDO"];
export const ESTAGIOS_ABERTOS: Estagio[] = ["LEAD", "CONTATO", "PROPOSTA"];

export interface Empresa {
  id: number;
  nome: string;
}

export interface Pedido {
  id: number;
  referencia_externa: string;
  status: StatusPedido;
  numero_erp: string | null;
  valor: string;
  tentativas: number;
  ultimo_erro_tipo: TipoErroErp;
  ultimo_erro: string;
  gerado_em: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface OportunidadeResumo {
  id: number;
  titulo: string;
  empresa: Empresa;
  valor: string | null;
  estagio: Estagio;
  pedido_status: StatusPedido | null;
  pedido_numero_erp: string | null;
  atualizado_em: string;
}

export interface Oportunidade {
  id: number;
  titulo: string;
  empresa: Empresa;
  valor: string | null;
  estagio: Estagio;
  motivo_perda: string;
  fechado_em: string | null;
  criado_em: string;
  atualizado_em: string;
  pedido: Pedido | null;
}

export interface ListagemOportunidades {
  resultados: OportunidadeResumo[];
  contagens: Record<"TODOS" | Estagio, number>;
  total_cadastradas: number;
}

export interface ErroApi {
  codigo: string;
  mensagem: string;
  campos?: Record<string, string[]>;
  pedido?: Pedido | null;
}

/** Dados que o formulário envia (sempre texto, como vem do FormData). */
export interface DadosOportunidade {
  titulo: string;
  empresa: string;
  valor: string;
  estagio?: string;
}

export type ResultadoAcao =
  | { ok: true }
  | ({ ok: false } & ErroApi & { valores?: Record<string, string> });
