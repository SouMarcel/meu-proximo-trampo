/**
 * Seus relatos (spec 035): o que a pessoa contou com as próprias palavras na candidatura assistida e na análise de
 * reprovação. Cada relato vale como fato e entra no que a ferramenta sabe dela (respostas, currículo, carta, histórias
 * STAR, nota e análises). Aqui ela corrige, apaga ou leva relatos ao perfil pela revisão do perfil (spec 050): a IA
 * propõe onde cada fato entra, ela aceita item a item e grava (a versão anterior do perfil fica guardada).
 */
import React, { useCallback, useEffect, useState } from "react"
import { BookOpen, Loader2 } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { Relato } from "../../services/api/perfil"
import { BTN_MINI } from "../curriculo/Curriculos"
import { useGeracao } from "../../contexto/Geracao"
import { diaMes } from "../../utils/formatters"
import { SecaoRevisaoPerfil } from "./RevisaoPerfil"

const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"

export default function Relatos({
  so,
  onAviso,
  onErro,
  onPerfilMudou,
}: {
  so: boolean
  onAviso: (m: string) => void
  onErro: (e: unknown) => void
  onPerfilMudou?: () => void
}) {
  const { ativa, comecou } = useGeracao()
  const [lista, setLista] = useState<Relato[] | null>(null)
  const [editando, setEditando] = useState<{ id: string; texto: string } | null>(null)
  const [marcados, setMarcados] = useState<string[]>([])
  const [ocupado, setOcupado] = useState("")

  const recarregar = useCallback(
    () =>
      perfilApi
        .relatos()
        .then((j) => setLista(j.relatos))
        .catch(() => setLista([])),
    [],
  )

  useEffect(() => {
    recarregar()
  }, [recarregar])

  const acao = async (chave: string, fn: () => Promise<{ relatos: Relato[] }>, aviso: string) => {
    setOcupado(chave)
    try {
      const j = await fn()
      setLista(j.relatos)
      onAviso(aviso)
    } catch (e) {
      onErro(e)
    } finally {
      setOcupado("")
    }
  }

  /** Revisar e levar ao perfil (spec 050): a IA propõe; sem IA, o relato vai como antes, com o aviso. */
  const revisar = async (ids: string[]) => {
    if (!ids.length) return
    setOcupado("revisar")
    try {
      const j = await perfilApi.revisarPerfil("relatos", ids)
      if ("sem_ia" in j) {
        onAviso(j.aviso)
        await recarregar()
        if (onPerfilMudou) onPerfilMudou()
      } else {
        comecou(j)
      }
      setMarcados([])
    } catch (e) {
      onErro(e)
    } finally {
      setOcupado("")
    }
  }

  const marcar = (id: string, sim: boolean) => setMarcados((m) => (sim ? [...new Set([...m, id])] : m.filter((x) => x !== id)))

  if (!lista || lista.length === 0) return null
  const travado = so || Boolean(ocupado)

  return (
    <section className="space-y-2">
      <h4 className={`${H} flex items-center gap-2`}>
        <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Seus relatos ({lista.length})
      </h4>
      <p className={DICA}>
        O que você contou na candidatura assistida e na análise de reprovação. Cada relato vale como fato e já entra nas
        respostas, no currículo, na carta, nas histórias STAR e na nota das vagas. Para levar ao perfil, marque os relatos
        e clique em Revisar: a IA propõe onde cada fato entra, e você confere item a item antes de gravar.
      </p>
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
          disabled={travado || ativa || marcados.length === 0}
          onClick={() => revisar(marcados)}
        >
          {ocupado === "revisar" && <Loader2 className="w-4 h-4 animate-spin" />}
          Revisar e levar ao perfil{marcados.length ? ` (${marcados.length})` : ""}
        </button>
        {marcados.length === 0 && <span className={DICA}>Marque um ou mais relatos.</span>}
      </div>
      <ul className="space-y-2">
        {lista.map((r) => (
          <li key={r.id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={marcados.includes(r.id)}
                disabled={travado}
                onChange={(e) => marcar(r.id, e.target.checked)}
              />
              <span className="font-semibold text-slate-800 dark:text-slate-200">{r.pergunta || "(sem pergunta)"}</span>
            </label>
            {editando?.id === r.id ? (
              <textarea
                rows={4}
                className={CAMPO}
                value={editando.texto}
                maxLength={4000}
                onChange={(e) => setEditando({ id: r.id, texto: e.target.value })}
              />
            ) : (
              <p className="text-slate-700 dark:text-slate-300 whitespace-pre-line">{r.relato}</p>
            )}
            <p className={DICA}>
              {diaMes(r.em)}
              {r.vaga?.empresa ? ` · ${r.vaga.titulo} — ${r.vaga.empresa}` : ""}
              {r.no_perfil ? " · já está no perfil" : " · fora do perfil: revise para levar"}
            </p>
            <div className="flex flex-wrap gap-2">
              {editando?.id === r.id ? (
                <>
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={travado || !editando.texto.trim()}
                    onClick={() =>
                      acao("editar", () => perfilApi.editarRelato(r.id, editando.texto), "Relato corrigido.").then(() =>
                        setEditando(null),
                      )
                    }
                  >
                    Salvar
                  </button>
                  <button type="button" className={BTN_MINI} onClick={() => setEditando(null)}>
                    Cancelar
                  </button>
                </>
              ) : (
                <>
                  {!r.no_perfil && (
                    <button
                      type="button"
                      className={BTN_MINI}
                      disabled={travado || ativa}
                      title="A IA propõe onde este relato entra no perfil; você confere antes de gravar"
                      onClick={() => revisar([r.id])}
                    >
                      Levar ao perfil
                    </button>
                  )}
                  <button type="button" className={BTN_MINI} disabled={travado} onClick={() => setEditando({ id: r.id, texto: r.relato })}>
                    Corrigir
                  </button>
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={travado}
                    onClick={() => acao("apagar", () => perfilApi.apagarRelato(r.id), "Relato apagado.")}
                  >
                    Apagar
                  </button>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
      <SecaoRevisaoPerfil
        origem="relatos"
        onGravado={() => {
          recarregar()
          if (onPerfilMudou) onPerfilMudou()
        }}
      />
    </section>
  )
}
