type Icone = "caixa" | "busca" | "alerta";

const CAMINHOS: Record<Icone, string> = {
  caixa:
    "M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z",
  busca: "M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z",
  alerta:
    "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
};

interface EmptyStateProps {
  icon?: Icone;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon = "caixa", title, description, action }: EmptyStateProps) {
  const erro = icon === "alerta";
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-slate-200 bg-white px-4 py-16 text-center">
      <div className={`flex h-12 w-12 items-center justify-center rounded-full ${erro ? "bg-red-50" : "bg-slate-100"}`}>
        <svg
          className={`h-6 w-6 ${erro ? "text-red-500" : "text-slate-400"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d={CAMINHOS[icon]} />
        </svg>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-700">{title}</p>
        {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}
