import { useRevalidator } from "react-router";

import { Button, Spinner } from "./Button";
import { EmptyState } from "./EmptyState";

/** Falha ao carregar uma tela: mensagem + "Tentar novamente" (revalida os loaders). */
export function ErrorState({ title = "Não foi possível carregar" }: { title?: string }) {
  const revalidator = useRevalidator();
  const carregando = revalidator.state === "loading";
  return (
    <EmptyState
      icon="alerta"
      title={title}
      description="Verifique sua conexão e tente novamente."
      action={
        <Button variant="secondary" size="sm" onClick={() => revalidator.revalidate()} disabled={carregando}>
          {carregando && <Spinner className="h-3.5 w-3.5" />}
          Tentar novamente
        </Button>
      }
    />
  );
}
