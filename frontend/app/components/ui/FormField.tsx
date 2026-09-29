import { useId } from "react";

const CAMPO =
  "w-full rounded-lg border bg-white px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 disabled:bg-slate-50 disabled:opacity-60";
const CAMPO_OK = "border-slate-200 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500";
const CAMPO_ERRO = "border-red-400 focus:border-red-400 focus:ring-red-400";

export function classesCampo(erro: boolean, extra = "") {
  return [CAMPO, erro ? CAMPO_ERRO : CAMPO_OK, extra].filter(Boolean).join(" ");
}

interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: (props: { id: string; "aria-invalid": boolean; "aria-describedby"?: string }) => React.ReactNode;
}

/** Rótulo + campo + mensagem de erro ligados por id/aria. */
export function FormField({ label, required, error, children }: FormFieldProps) {
  const id = useId();
  const idErro = `${id}-erro`;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
        {required && <span className="ml-0.5 text-red-500" aria-hidden="true">*</span>}
      </label>
      {children({ id, "aria-invalid": Boolean(error), "aria-describedby": error ? idErro : undefined })}
      {error && (
        <p id={idErro} className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export function Input({ error = false, className = "", ...props }: InputProps) {
  return <input className={classesCampo(error, className)} {...props} />;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export function Select({ error = false, className = "", ...props }: SelectProps) {
  return <select className={classesCampo(error, className)} {...props} />;
}
