/**
 * Seus relatos (spec 035): o que a pessoa contou com as próprias palavras na candidatura assistida. Cada relato vale
 * como fato e entra no que a ferramenta sabe dela (respostas, currículo, carta, histórias STAR, nota e análises). Aqui
 * ela corrige, apaga ou leva o relato ao perfil.md (a versão anterior do perfil fica guardada).
 */
import React, { useEffect, useState } from "react"
import { BookOpen } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { Relato } from "../../services/api/perfil"
import { BTN_MINI } from "../curriculo/Curriculos"
import { diaMes } from "../../utils/formatters"

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
  const [lista, setLista] = useState<Relato[] | null>(null)
  const [editando, setEditando] = useState<{ id: string; texto: string } | null>(null)
  const [ocupado, setOcupado] = useState("")

  useEffect(() => {
    perfilApi
      .relatos()
      .then((j) => setLista(j.relatos))
      .catch(() => setLista([]))
  }, [])

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

  if (!lista || lista.length === 0) return null

  return (
    <section className="space-y-2">
      <h4 className={`${H} flex items-center gap-2`}>
        <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Seus relatos ({lista.length})
      </h4>
      <p className={DICA}>
        O que você contou na candidatura assistida. Cada relato vale como fato e já entra nas respostas, no currículo, na
        carta, nas histórias STAR e na nota das vagas. Leve ao perfil os que descrevem a sua carreira.
      </p>
      <ul className="space-y-2">
        {lista.map((r) => (
          <li key={r.id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
            <p className="font-semibold text-slate-800 dark:text-slate-200">{r.pergunta || "(sem pergunta)"}</p>
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
              {r.no_perfil ? " · já está no perfil" : ""}
            </p>
            <div className="flex flex-wrap gap-2">
              {editando?.id === r.id ? (
                <>
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={so || Boolean(ocupado) || !editando.texto.trim()}
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
                      disabled={so || Boolean(ocupado)}
                      title="Acrescenta o relato à seção Relatos do perfil.md; a versão atual do perfil fica guardada"
                      onClick={() =>
                        acao("perfil", () => perfilApi.levarRelatoAoPerfil(r.id), "Relato levado ao perfil.").then(
                          () => onPerfilMudou && onPerfilMudou(),
                        )
                      }
                    >
                      Levar ao perfil
                    </button>
                  )}
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={so || Boolean(ocupado)}
                    onClick={() => setEditando({ id: r.id, texto: r.relato })}
                  >
                    Corrigir
                  </button>
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={so || Boolean(ocupado)}
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
    </section>
  )
}
