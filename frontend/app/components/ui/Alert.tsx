type Variante = "error" | "info" | "success";

const ESTILOS: Record<Variante, string> = {
  error: "border-red-200 bg-red-50 text-red-800",
  info: "border-blue-200 bg-blue-50 text-blue-800",
  success: "border-green-200 bg-green-50 text-green-800",
};

export function Alert({ variant = "info", children }: { variant?: Variante; children: React.ReactNode }) {
  return (
    <div role={variant === "error" ? "alert" : "status"} className={`rounded-lg border px-3.5 py-3 text-sm ${ESTILOS[variant]}`}>
      {children}
    </div>
  );
}
