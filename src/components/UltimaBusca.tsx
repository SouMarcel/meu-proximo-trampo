/** Linha da última busca no topo do Relatório (dash/API.md §3.1); registros antigos podem não ter todos os campos. */
import React from "react"
import { History, Loader2 } from "lucide-react"
import type { UltimaBusca as TUltimaBusca } from "../types/api"
import { diaMes, horaDe } from "../utils/formatters"

export default function UltimaBusca({ busca, analisando }: { busca: TUltimaBusca | null; analisando: boolean }) {
  const partes: string[] = []
  if (busca) {
    if (busca.termos?.length) partes.push(busca.termos.join(", "))
    partes.push(
      `${busca.brutas || 0} vagas encontradas, ${busca.avaliadas || 0}${
        busca.com_nota === false ? " novas (sem nota)" : " novas avaliadas"
      }`,
    )
    if (busca.fora_criterios) partes.push(`${busca.fora_criterios} fora dos critérios`)
    const faixas = [
      busca.fortes ? `${busca.fortes} fortes` : "",
      busca.boas ? `${busca.boas} boas` : "",
      busca.parciais ? `${busca.parciais} parciais` : "",
      busca.baixas ? `${busca.baixas} baixas` : "",
    ].filter(Boolean)
    if (faixas.length) partes.push(faixas.join(", "))
  }
  return (
    <div className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400 px-1 flex-wrap">
      <History className="w-4 h-4 shrink-0 text-slate-400" />
      {busca ? (
        <span>
          Última busca em{" "}
          <b className="text-slate-800 dark:text-slate-200">
            {diaMes(busca.data)} às {horaDe(busca.data)}
          </b>
          {partes.length ? " · " + partes.join(" · ") : ""}
        </span>
      ) : (
        <span>Nenhuma busca registrada ainda.</span>
      )}
      {analisando && (
        <b className="flex items-center gap-1 text-indigo-700 dark:text-indigo-300">
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> IA analisando vagas adicionadas…
        </b>
      )}
    </div>
  )
}
