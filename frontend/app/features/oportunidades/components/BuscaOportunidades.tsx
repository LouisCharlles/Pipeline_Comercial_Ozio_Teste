import { Form } from "react-router";

import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/FormField";

/** Busca por título ou empresa num formulário GET: funciona sem JavaScript e fica na URL. */
export function BuscaOportunidades({ q, estagio }: { q: string; estagio: string | null }) {
  function aoEnviar(e: React.FormEvent<HTMLFormElement>) {
    // Busca vazia não vai para a URL (sem "?q=").
    const campo = e.currentTarget.elements.namedItem("q") as HTMLInputElement;
    if (!campo.value.trim()) campo.disabled = true;
  }

  return (
    <Form method="get" action="/oportunidades" role="search" onSubmit={aoEnviar} className="flex w-full items-center gap-2 sm:w-auto">
      {estagio && <input type="hidden" name="estagio" value={estagio} />}
      <Input
        key={q}
        type="search"
        name="q"
        defaultValue={q}
        placeholder="Buscar por título ou empresa"
        aria-label="Buscar por título ou empresa"
        className="sm:w-64"
      />
      <Button type="submit" variant="secondary" size="sm" className="shrink-0 py-2">
        Buscar
      </Button>
    </Form>
  );
}
