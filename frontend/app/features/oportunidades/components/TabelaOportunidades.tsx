import { Link, useNavigate } from "react-router";

import { StageBadge } from "../../../components/ui/StageBadge";
import { formatarMoeda } from "../formato";
import type { OportunidadeResumo } from "../types";

const TH = "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500";

export function SeloPedido({ status, numero }: { status: OportunidadeResumo["pedido_status"]; numero: string | null }) {
  if (status === "GERADO") {
    return (
      <span className="inline-flex items-center whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-200 bg-green-50">
        Pedido #{numero}
      </span>
    );
  }
  if (status === "FALHOU") {
    return (
      <span className="inline-flex items-center whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-200 bg-red-50">
        Falha no pedido
      </span>
    );
  }
  return null;
}

export function TabelaOportunidades({ oportunidades }: { oportunidades: OportunidadeResumo[] }) {
  const navigate = useNavigate();
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50">
            <th className={TH}>Título</th>
            <th className={TH}>Empresa</th>
            <th className={TH}>Valor</th>
            <th className={TH}>Estágio</th>
            <th className={TH}>Pedido</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {oportunidades.map((op) => (
            <tr
              key={op.id}
              // A linha inteira é clicável; o link do título mantém o acesso por teclado.
              onClick={() => navigate(`/oportunidades/${op.id}`)}
              className="group cursor-pointer transition-colors hover:bg-slate-50"
            >
              <td className="px-4 py-3">
                <Link
                  to={`/oportunidades/${op.id}`}
                  onClick={(e) => e.stopPropagation()}
                  className="font-medium text-slate-900 group-hover:text-blue-600 focus:outline-none focus-visible:underline"
                >
                  {op.titulo}
                </Link>
              </td>
              <td className="px-4 py-3 text-slate-600">{op.empresa.nome}</td>
              <td className="px-4 py-3 font-medium tabular-nums text-slate-700">{formatarMoeda(op.valor)}</td>
              <td className="px-4 py-3">
                <StageBadge stage={op.estagio} />
              </td>
              <td className="px-4 py-3">
                <SeloPedido status={op.pedido_status} numero={op.pedido_numero_erp} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
