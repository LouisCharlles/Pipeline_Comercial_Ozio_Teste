import { useEffect, useId, useRef, useState } from "react";
import { useFetcher } from "react-router";

import { Input } from "../../../components/ui/FormField";
import type { Empresa } from "../types";

interface EmpresaInputProps {
  id: string;
  defaultValue: string;
  error: boolean;
  disabled?: boolean;
  "aria-describedby"?: string;
}

/**
 * Texto livre com sugestões das empresas já cadastradas (FR-003). Escolher uma sugestão é
 * opcional: o nome digitado sempre vale.
 */
export function EmpresaInput({ id, defaultValue, error, disabled, ...aria }: EmpresaInputProps) {
  const fetcher = useFetcher<Empresa[]>();
  const [valor, setValor] = useState(defaultValue);
  const [aberta, setAberta] = useState(false);
  const [ativa, setAtiva] = useState(-1);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const idLista = useId();

  const sugestoes = (fetcher.data ?? []).filter((e) => e.nome.toLowerCase() !== valor.trim().toLowerCase());
  const mostrar = aberta && sugestoes.length > 0;

  useEffect(() => () => clearTimeout(timer.current), []);

  function aoDigitar(texto: string) {
    setValor(texto);
    setAberta(true);
    setAtiva(-1);
    clearTimeout(timer.current);
    if (!texto.trim()) return;
    timer.current = setTimeout(() => fetcher.load(`/empresas/sugestoes?q=${encodeURIComponent(texto.trim())}`), 250);
  }

  function escolher(nome: string) {
    setValor(nome);
    setAberta(false);
    setAtiva(-1);
  }

  function aoTeclar(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!mostrar) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setAtiva((i) => (i + 1) % sugestoes.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setAtiva((i) => (i <= 0 ? sugestoes.length - 1 : i - 1));
    } else if (e.key === "Enter" && ativa >= 0) {
      e.preventDefault();
      escolher(sugestoes[ativa].nome);
    } else if (e.key === "Escape") {
      setAberta(false);
    }
  }

  return (
    <div className="relative">
      <Input
        id={id}
        name="empresa"
        value={valor}
        onChange={(e) => aoDigitar(e.target.value)}
        onKeyDown={aoTeclar}
        onBlur={() => setAberta(false)}
        onFocus={() => valor.trim() && setAberta(true)}
        placeholder="Ex.: Acme Logística"
        autoComplete="off"
        role="combobox"
        aria-expanded={mostrar}
        aria-controls={idLista}
        aria-autocomplete="list"
        aria-activedescendant={ativa >= 0 ? `${idLista}-${ativa}` : undefined}
        aria-invalid={error}
        error={error}
        disabled={disabled}
        {...aria}
      />
      {mostrar && (
        <ul
          id={idLista}
          role="listbox"
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 text-sm shadow-lg"
        >
          {sugestoes.map((empresa, i) => (
            <li
              key={empresa.id}
              id={`${idLista}-${i}`}
              role="option"
              aria-selected={i === ativa}
              // mousedown (e não click) para escolher antes do blur fechar a lista.
              onMouseDown={(e) => {
                e.preventDefault();
                escolher(empresa.nome);
              }}
              className={`cursor-pointer px-3 py-2 ${i === ativa ? "bg-blue-50 text-blue-700" : "text-slate-700 hover:bg-slate-50"}`}
            >
              {empresa.nome}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
