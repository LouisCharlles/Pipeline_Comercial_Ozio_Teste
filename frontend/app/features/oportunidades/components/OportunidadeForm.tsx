import { Form, Link, useNavigation } from "react-router";

import { Alert } from "../../../components/ui/Alert";
import { Button, classesBotao, Spinner } from "../../../components/ui/Button";
import { classesCampo, FormField, Input, Select } from "../../../components/ui/FormField";
import { ROTULO_ESTAGIO } from "../formato";
import { ESTAGIOS_ABERTOS } from "../types";
import { EmpresaInput } from "./EmpresaInput";

export interface ValoresForm {
  titulo: string;
  empresa: string;
  valor: string;
  estagio?: string;
}

interface OportunidadeFormProps {
  valores: ValoresForm;
  campos?: Record<string, string[]>;
  erroGeral?: string;
  mostrarEstagio: boolean;
  rotuloEnviar: string;
  rotuloEnviando: string;
  cancelarPara: string;
}

export function OportunidadeForm({
  valores,
  campos = {},
  erroGeral,
  mostrarEstagio,
  rotuloEnviar,
  rotuloEnviando,
  cancelarPara,
}: OportunidadeFormProps) {
  const enviando = useNavigation().state === "submitting";
  const erro = (campo: string) => campos[campo]?.[0];

  return (
    <Form method="post" noValidate className="flex flex-col gap-5">
      {erroGeral && <Alert variant="error">{erroGeral}</Alert>}

      <FormField label="Título" required error={erro("titulo")}>
        {(aria) => (
          <Input
            {...aria}
            name="titulo"
            defaultValue={valores.titulo}
            placeholder="Ex.: Contrato de Logística 2026"
            error={Boolean(erro("titulo"))}
            disabled={enviando}
          />
        )}
      </FormField>

      <FormField label="Empresa" required error={erro("empresa")}>
        {(aria) => (
          <EmpresaInput
            id={aria.id}
            aria-describedby={aria["aria-describedby"]}
            defaultValue={valores.empresa}
            error={Boolean(erro("empresa"))}
            disabled={enviando}
          />
        )}
      </FormField>

      <FormField label="Valor (R$)" error={erro("valor")}>
        {(aria) => (
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">R$</span>
            <input
              {...aria}
              name="valor"
              type="text"
              inputMode="decimal"
              defaultValue={valores.valor}
              placeholder="0"
              disabled={enviando}
              className={classesCampo(Boolean(erro("valor")), "pl-9")}
            />
          </div>
        )}
      </FormField>

      {mostrarEstagio && (
        <FormField label="Estágio" error={erro("estagio")}>
          {(aria) => (
            <Select {...aria} name="estagio" defaultValue={valores.estagio ?? "LEAD"} disabled={enviando} error={Boolean(erro("estagio"))}>
              {ESTAGIOS_ABERTOS.map((e) => (
                <option key={e} value={e}>
                  {ROTULO_ESTAGIO[e]}
                </option>
              ))}
            </Select>
          )}
        </FormField>
      )}

      <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
        <Link
          to={cancelarPara}
          className={classesBotao("secondary", "md", enviando ? "pointer-events-none opacity-50" : "")}
          aria-disabled={enviando}
        >
          Cancelar
        </Link>
        <Button type="submit" disabled={enviando}>
          {enviando ? (
            <>
              <Spinner className="h-3.5 w-3.5" />
              {rotuloEnviando}
            </>
          ) : (
            rotuloEnviar
          )}
        </Button>
      </div>
    </Form>
  );
}
