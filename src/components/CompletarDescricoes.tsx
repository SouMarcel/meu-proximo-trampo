/**
 * Descrições pendentes (spec 019; dash/API.md §3.3): vagas que a busca trouxe sem o texto porque o portal limitou
 * os pedidos. O botão lê só essas descrições, sem buscar vagas novas; durante a espera do portal fica desligado.
 */
import React, { useCallback, useEffect, useRef, useState } from "react"
import { FileText, Loader2 } from "lucide-react"
import type { EstadoPendentes } from "../types/api"
import * as buscaApi from "../services/api/busca"
import { useConsulta } from "../hooks/useConsulta"
import { useFerramenta } from "../contexto/Ferramenta"
import { horaDe } from "../utils/formatters"

interface Props {
  /** Muda quando algo pode ter alterado as pendentes (busca terminou, vaga adicionada). */
  gatilho: number
  onTerminou: () => void
  onErro: (e: unknown) => void
}

export default function CompletarDescricoes({ gatilho, onTerminou, onErro }: Props) {
  const { podeGravar } = useFerramenta()
  const [e, setE] = useState<EstadoPendentes | null>(null)
  const [pedindo, setPedindo] = useState(false)
  const antes = useRef<string | undefined>(undefined)
  const aoTerminar = useRef(onTerminou)
  aoTerminar.current = onTerminou

  const carregar = useCallback(async () => {
    try {
      const j = await buscaApi.pendentes()
      if (antes.current === "lendo" && j.situacao !== "lendo") aoTerminar.current()
      antes.current = j.situacao
      setE(j)
    } catch {
      // sem resposta: o aviso de servidor fora vem da consulta da versão
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar, gatilho])

  useConsulta(carregar, 2000, e?.situacao === "lendo")

  const iniciar = async () => {
    setPedindo(true)
    try {
      const j = await buscaApi.completarPendentes()
      antes.current = "lendo"
      setE((x) => ({ ...(x || {}), ...j }))
    } catch (err) {
      onErro(err)
      carregar()
    } finally {
      setPedindo(false)
    }
  }

  if (!e) return null
  const caixa =
    "flex items-start gap-2 flex-wrap rounded-2xl border p-3 text-xs bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200"

  if (e.situacao === "lendo") {
    return (
      <p role="status" className={caixa}>
        <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        <span>
          Completando as descrições pendentes{e.total ? ` (${e.lidas || 0} de ${e.total})` : ""}…
        </span>
      </p>
    )
  }

  const fim = e.situacao === "pronta" && e.completadas ? `Descrições completadas: ${e.completadas}. ` : ""
  if (!e.pendentes) {
    return fim ? <p className={caixa}>{fim}As vagas seguem para a nota de aderência.</p> : null
  }
  const espera = (e.espera || [])[0]
  return (
    <div className={caixa}>
      <FileText className="w-4 h-4 shrink-0" />
      <span className="flex-1 min-w-[200px]">
        {fim}
        {e.pendentes} vaga(s) sem descrição: o portal limitou os pedidos na busca, e elas ficam sem nota até o texto
        chegar.
        {e.situacao === "erro" && e.mensagem ? ` ${e.mensagem}` : ""}
      </span>
      {espera ? (
        <span className="text-amber-700 dark:text-amber-300">
          disponível a partir das {horaDe(espera.ate)} ({espera.portal} em espera: {espera.motivo})
        </span>
      ) : (
        <button
          onClick={iniciar}
          disabled={!podeGravar || e.pode_alterar === false || pedindo}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white transition disabled:opacity-50"
        >
          Completar descrições
        </button>
      )}
    </div>
  )
}
