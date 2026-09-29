import { ROTULO_ESTAGIO } from "../../features/oportunidades/formato";
import type { Estagio } from "../../features/oportunidades/types";

const CORES: Record<Estagio, string> = {
  LEAD: "bg-slate-100 text-slate-700 ring-slate-200",
  CONTATO: "bg-sky-50 text-sky-700 ring-sky-200",
  PROPOSTA: "bg-amber-50 text-amber-700 ring-amber-200",
  GANHO: "bg-green-50 text-green-700 ring-green-200",
  PERDIDO: "bg-red-50 text-red-700 ring-red-200",
};

export function StageBadge({ stage }: { stage: Estagio }) {
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${CORES[stage]}`}>
      {ROTULO_ESTAGIO[stage]}
    </span>
  );
}
