import { useState } from "react";

import { classesCampo } from "../../../components/ui/FormField";
import { Modal } from "../../../components/ui/Modal";
import { ROTULO_ESTAGIO } from "../formato";
import type { Estagio } from "../types";

export type ModoModal = "ganho" | "perdido" | "reabrir";

interface ModalEstagioProps {
  modo: ModoModal;
  destino: Estagio;
  onCancel: () => void;
  onConfirm: (motivoPerda?: string) => void;
}

export function ModalEstagio({ modo, destino, onCancel, onConfirm }: ModalEstagioProps) {
  const [motivo, setMotivo] = useState("");

  if (modo === "ganho") {
    return (
      <Modal
        title="Marcar como Ganho?"
        description="Ao marcar como Ganho, você poderá gerar o pedido no ERP. Essa ação pode ser desfeita enquanto não houver pedido gerado."
        confirmLabel="Confirmar como Ganho"
        onCancel={onCancel}
        onConfirm={() => onConfirm()}
      />
    );
  }

  if (modo === "perdido") {
    return (
      <Modal
        title="Marcar como Perdido?"
        description="Ao marcar como Perdido, a oportunidade será encerrada. Você poderá reabri-la depois."
        confirmLabel="Confirmar como Perdido"
        confirmVariant="danger"
        onCancel={onCancel}
        onConfirm={() => onConfirm(motivo)}
      >
        <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
          Motivo da perda (opcional)
          <textarea
            name="motivo_perda"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            maxLength={500}
            rows={3}
            placeholder="Ex.: orçamento aprovado para concorrente"
            className={classesCampo(false, "resize-y font-normal")}
          />
        </label>
      </Modal>
    );
  }

  return (
    <Modal
      title="Reabrir oportunidade?"
      description={`A oportunidade volta para ${ROTULO_ESTAGIO[destino]}; a data de fechamento e o motivo da perda serão apagados.`}
      confirmLabel="Reabrir"
      onCancel={onCancel}
      onConfirm={() => onConfirm()}
    />
  );
}
