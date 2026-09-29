import { Link } from "react-router";

export function VoltarLink({ to, children = "Voltar" }: { to: string; children?: React.ReactNode }) {
  return (
    <Link to={to} className="inline-flex w-fit items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      {children}
    </Link>
  );
}
