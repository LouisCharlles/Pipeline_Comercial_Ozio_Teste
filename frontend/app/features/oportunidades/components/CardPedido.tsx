import { Link, useFetcher } from "react-router";

import { Alert } from "../../../components/ui/Alert";
import { Button, Spinner } from "../../../components/ui/Button";
import { mensagemDeErro, mensagemDeFalhaErp } from "../erros";
import { formatarData, formatarMoeda } from "../formato";
import type { Oportunidade, ResultadoAcao } from "../types";

export const CHAVE_GERAR_PEDIDO = "gerar-pedido";

function Linha({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span>{rotulo}</span>
      <span className="text-right font-medium text-slate-700">{children}</span>
    </div>
  );
}

/** Card "Pedido no ERP" do detalhe, com os estados de contracts/ui-rotas.md. */
export function CardPedido({ oportunidade }: { oportunidade: Oportunidade }) {
  const fetcher = useFetcher<ResultadoAcao>({ key: CHAVE_GERAR_PEDIDO });
  const enviando = fetcher.state !== "idle";
  const { pedido, estagio } = oportunidade;
  const emGanho = estagio === "GANHO";
  const semValor = oportunidade.valor === null || Number(oportunidade.valor) <= 0;

  // Falhas do ERP já aparecem pelo pedido FALHOU gravado; aqui só os outros erros da ação.
  const erroAcao = fetcher.state === "idle" && fetcher.data?.ok === false && !fetcher.data.codigo.startsWith("erp_") ? fetcher.data : null;

  function botao(rotulo: string) {
    return (
      <fetcher.Form method="post">
        <input type="hidden" name="intent" value="gerar-pedido" />
        <Button type="submit" className="w-full" disabled={enviando}>
          {enviando ? (
            <>
              <Spinner />
              Gerando pedido…
            </>
          ) : (
            rotulo
          )}
        </Button>
      </fetcher.Form>
    );
  }

  let conteudo: React.ReactNode;

  if (pedido?.status === "GERADO") {
    conteudo = (
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-900">#{pedido.numero_erp}</span>
          <span className="inline-flex items-center rounded bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-200">
            Gerado
          </span>
        </div>
        <div className="flex flex-col gap-1 text-xs text-slate-500">
          <Linha rotulo="Gerado em">{formatarData(pedido.gerado_em)}</Linha>
          <Linha rotulo="Valor">
            <span className="tabular-nums">{formatarMoeda(pedido.valor)}</span>
          </Linha>
        </div>
      </div>
    );
  } else if (enviando) {
    conteudo = (
      <div className="flex flex-col gap-3">
        {botao("Gerar pedido")}
        <p className="text-center text-xs text-slate-400">Comunicando com o ERP. Aguarde.</p>
      </div>
    );
  } else if (pedido?.status === "FALHOU" && emGanho) {
    conteudo = (
      <div className="flex flex-col gap-3">
        <Alert variant="error">
          <p className="font-medium">{mensagemDeFalhaErp(pedido.ultimo_erro_tipo)}</p>
          <p className="mt-0.5 text-xs">Você pode tentar novamente sem risco de duplicar o pedido.</p>
        </Alert>
        <div className="flex flex-col gap-1 text-xs text-slate-500">
          <Linha rotulo="Tentativas">{pedido.tentativas}</Linha>
          {pedido.ultimo_erro && <Linha rotulo="Último erro">{pedido.ultimo_erro}</Linha>}
        </div>
        {botao("Tentar novamente")}
      </div>
    );
  } else if (pedido?.status === "FALHOU") {
    conteudo = (
      <div className="flex flex-col gap-2 text-xs text-slate-500">
        <p>Tentativa anterior não concluída. Volte a oportunidade para Ganho para tentar novamente.</p>
        <Linha rotulo="Tentativas">{pedido.tentativas}</Linha>
      </div>
    );
  } else if (!emGanho) {
    conteudo = (
      <div className="flex flex-col gap-3">
        <Button className="w-full" disabled>
          Gerar pedido
        </Button>
        <p className="text-center text-xs leading-relaxed text-slate-400">
          Disponível quando a oportunidade estiver em <strong className="text-slate-500">Ganho</strong>.
        </p>
      </div>
    );
  } else if (semValor) {
    conteudo = (
      <div className="flex flex-col gap-3">
        <Button className="w-full" disabled>
          Gerar pedido
        </Button>
        <p className="text-center text-xs leading-relaxed text-slate-400">
          Informe um valor maior que zero antes de gerar o pedido.{" "}
          <Link to={`/oportunidades/${oportunidade.id}/editar`} className="font-medium text-blue-600 hover:underline">
            Editar
          </Link>
        </p>
      </div>
    );
  } else {
    conteudo = (
      <div className="flex flex-col gap-3">
        {botao("Gerar pedido")}
        <p className="text-center text-xs text-slate-400">Nenhum pedido gerado ainda.</p>
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5" aria-busy={enviando}>
      <div className="flex items-center gap-2">
        <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5A3.375 3.375 0 006.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0015 2.25h-1.5a2.251 2.251 0 00-2.15 1.586m5.8 0c.065.21.1.433.1.664v.75h-6V4.5c0-.231.035-.454.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 00-9-9z"
          />
        </svg>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pedido no ERP</h2>
      </div>
      {erroAcao && <Alert variant="error">{mensagemDeErro(erroAcao)}</Alert>}
      {conteudo}
    </section>
  );
}
