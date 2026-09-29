import { Link } from "react-router";

import { classesBotao } from "./Button";
import { EmptyState } from "./EmptyState";

export function NaoEncontrado({ title = "Oportunidade não encontrada" }: { title?: string }) {
  return (
    <EmptyState
      icon="busca"
      title={title}
      description="O endereço pode estar errado ou o registro não existe mais."
      action={
        <Link to="/oportunidades" className={classesBotao("secondary", "sm")}>
          Voltar para oportunidades
        </Link>
      }
    />
  );
}
