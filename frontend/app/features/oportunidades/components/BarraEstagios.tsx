import { useState } from "react";
import { useFetcher, useFetchers } from "react-router";

import { Alert } from "../../../components/ui/Alert";
import { StageBadge } from "../../../components/ui/StageBadge";
import { mensagemDeErro } from "../erros";
import { ROTULO_ESTAGIO } from "../formato";
import { ESTAGIOS, ESTAGIOS_ABERTOS, type Estagio, type Oportunidade, type ResultadoAcao } from "../types";
import { ModalEstagio, type ModoModal } from "./ModalEstagio";

const CHAVE_MUDAR_ESTAGIO = "mudar-estagio";

const ATIVO: Record<Estagio, string> = {
  LEAD: "border-blue-600 bg-blue-600 text-white",
  CONTATO: "border-blue-600 bg-blue-600 text-white",
  PROPOSTA: "border-blue-600 bg-blue-600 text-white",
  GANHO: "border-green-600 bg-green-600 text-white",
  PERDIDO: "border-red-600 bg-red-600 text-white",
};

/** Barra com os cinco estágios (FR-009 a FR-012). As regras valem também no backend. */
export function BarraEstagios({ oportunidade }: { oportunidade: Oportunidade }) {
  const fetcher = useFetcher<ResultadoAcao>({ key: CHAVE_MUDAR_ESTAGIO });
  // Qualquer ação em andamento (inclusive "Gerar pedido") trava a barra.
  const ocupado = useFetchers().some((f) => f.state !== "idle");
  const [modal, setModal] = useState<{ modo: ModoModal; destino: Estagio } | null>(null);

  const atual = oportunidade.estagio;
  const bloqueado = oportunidade.pedido?.status === "GERADO";
  const erro = fetcher.state === "idle" && fetcher.data?.ok === false ? fetcher.data : null;

  function enviar(destino: Estagio, motivoPerda?: string) {
    setModal(null);
    fetcher.submit(
      { intent: "mudar-estagio", estagio: destino, ...(motivoPerda !== undefined && { motivo_perda: motivoPerda }) },
      { method: "post" },
    );
  }

  function aoClicar(destino: Estagio) {
    if (destino === "GANHO") return setModal({ modo: "ganho", destino });
    if (destino === "PERDIDO") return setModal({ modo: "perdido", destino });
    if (atual === "PERDIDO") return setModal({ modo: "reabrir", destino });
    enviar(destino);
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5" aria-busy={fetcher.state !== "idle"}>
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Estágio</h2>

      {erro && (
        <div className="mb-3">
          <Alert variant="error">{mensagemDeErro(erro)}</Alert>
        </div>
      )}

      {bloqueado ? (
        <div className="flex items-center gap-2">
          <StageBadge stage="GANHO" />
          <span className="text-xs text-slate-500">Pedido gerado — estágio bloqueado</span>
        </div>
      ) : (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Mudar estágio">
          {ESTAGIOS.map((estagio) => {
            const ehAtual = estagio === atual;
            const ganhoAPartirDePerdido = atual === "PERDIDO" && estagio === "GANHO";
            const dica = ganhoAPartirDePerdido ? "Reabra a oportunidade antes de marcá-la como Ganho" : undefined;
            return (
              <button
                key={estagio}
                type="button"
                onClick={() => aoClicar(estagio)}
                disabled={ocupado || ehAtual || ganhoAPartirDePerdido}
                aria-pressed={ehAtual}
                title={dica}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  ehAtual
                    ? `${ATIVO[estagio]} cursor-default`
                    : ganhoAPartirDePerdido
                      ? "cursor-not-allowed border-dashed border-slate-200 text-slate-300"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                }`}
              >
                {ROTULO_ESTAGIO[estagio]}
              </button>
            );
          })}
        </div>
      )}

      {atual === "PERDIDO" && !bloqueado && (
        <p className="mt-3 text-xs text-slate-400">
          Para reabrir, escolha {ESTAGIOS_ABERTOS.map((e) => ROTULO_ESTAGIO[e]).join(", ")}.
        </p>
      )}

      {modal && (
        <ModalEstagio modo={modal.modo} destino={modal.destino} onCancel={() => setModal(null)} onConfirm={(motivo) => enviar(modal.destino, motivo)} />
      )}
    </section>
  );
}
