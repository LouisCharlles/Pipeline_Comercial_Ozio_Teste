import { useEffect, useId, useRef } from "react";

import { Button } from "./Button";

interface ModalProps {
  title: string;
  description: string;
  confirmLabel: string;
  confirmVariant?: "primary" | "danger";
  onCancel: () => void;
  onConfirm: () => void;
  children?: React.ReactNode;
}

export function Modal({
  title,
  description,
  confirmLabel,
  confirmVariant = "primary",
  onCancel,
  onConfirm,
  children,
}: ModalProps) {
  const idTitulo = useId();
  const idDescricao = useId();
  const cancelarRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelarRef.current?.focus();
    function aoTeclar(e: KeyboardEvent) {
      if (e.key === "Escape") onCancel();
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/40" onClick={onCancel} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        aria-describedby={idDescricao}
        className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
      >
        <h2 id={idTitulo} className="text-base font-semibold text-slate-900">
          {title}
        </h2>
        <p id={idDescricao} className="mt-2 text-sm leading-relaxed text-slate-600">
          {description}
        </p>
        {children && <div className="mt-4">{children}</div>}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button ref={cancelarRef} variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant={confirmVariant} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
