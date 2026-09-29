type Variante = "primary" | "secondary" | "danger";
type Tamanho = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50";

const VARIANTES: Record<Variante, string> = {
  primary: "bg-blue-600 text-white shadow-sm hover:bg-blue-700 disabled:hover:bg-blue-600",
  secondary: "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:hover:bg-white",
  danger: "bg-red-600 text-white shadow-sm hover:bg-red-700 disabled:hover:bg-red-600",
};

const TAMANHOS: Record<Tamanho, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
};

/** Classes de botão, para usar também em <Link> com aparência de botão. */
export function classesBotao(variante: Variante = "primary", tamanho: Tamanho = "md", extra = "") {
  return [BASE, VARIANTES[variante], TAMANHOS[tamanho], extra].filter(Boolean).join(" ");
}

interface ButtonProps extends React.ComponentProps<"button"> {
  variant?: Variante;
  size?: Tamanho;
}

export function Button({ variant = "primary", size = "md", className = "", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={classesBotao(variant, size, className)} {...props} />;
}

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
