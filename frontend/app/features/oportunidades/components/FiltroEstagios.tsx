import { Link } from "react-router";

import { ROTULO_ESTAGIO } from "../formato";
import { ESTAGIOS, type Estagio, type ListagemOportunidades } from "../types";

interface FiltroEstagiosProps {
  contagens: ListagemOportunidades["contagens"];
  estagio: Estagio | null;
  q: string;
}

/** Chips de estágio com contagem. São links: o filtro fica na URL e preserva a busca. */
export function FiltroEstagios({ contagens, estagio, q }: FiltroEstagiosProps) {
  const opcoes: Array<{ valor: Estagio | null; rotulo: string; total: number }> = [
    { valor: null, rotulo: "Todos", total: contagens.TODOS },
    ...ESTAGIOS.map((e) => ({ valor: e, rotulo: ROTULO_ESTAGIO[e], total: contagens[e] })),
  ];

  return (
    <nav aria-label="Filtrar por estágio" className="flex flex-wrap items-center gap-1">
      {opcoes.map(({ valor, rotulo, total }) => {
        const ativo = valor === estagio;
        const params = new URLSearchParams();
        if (valor) params.set("estagio", valor);
        if (q) params.set("q", q);
        const qs = params.toString();
        return (
          <Link
            key={rotulo}
            to={`/oportunidades${qs ? `?${qs}` : ""}`}
            aria-current={ativo ? "page" : undefined}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              ativo ? "bg-blue-600 text-white shadow-sm" : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {rotulo}
            <span className={`rounded-full px-1.5 py-0.5 text-xs ${ativo ? "bg-blue-500 text-white" : "bg-slate-100 text-slate-500"}`}>
              {total}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
