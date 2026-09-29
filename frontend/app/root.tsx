import { isRouteErrorResponse, Link, Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";

import type { Route } from "./+types/root";
import { classesBotao } from "./components/ui/Button";
import { ErrorState } from "./components/ui/ErrorState";
import { NaoEncontrado } from "./components/ui/NaoEncontrado";
import { PendingBar } from "./components/ui/PendingBar";

import "./app.css";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <PendingBar />
        <Cabecalho />
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">{children}</main>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

function Cabecalho() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/oportunidades" className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-blue-600" aria-hidden="true">
            <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
              />
            </svg>
          </span>
          <span className="text-sm font-semibold text-slate-900">Pipeline Comercial</span>
        </Link>
        <Link to="/oportunidades/nova" className={classesBotao("primary", "sm")}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nova oportunidade
        </Link>
      </div>
    </header>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  if (isRouteErrorResponse(error) && error.status === 404) {
    return <NaoEncontrado title="Página não encontrada" />;
  }
  return <ErrorState />;
}
