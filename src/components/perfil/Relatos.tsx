/**
 * Seus relatos (spec 035): o que a pessoa contou com as próprias palavras na candidatura assistida e na análise de
 * reprovação. Cada relato vale como fato e entra no que a ferramenta sabe dela (respostas, currículo, carta, histórias
 * STAR, nota e análises). Aqui ela corrige, apaga ou leva relatos ao perfil pela revisão do perfil (spec 050): a IA
 * propõe onde cada fato entra, ela aceita item a item e grava (a versão anterior do perfil fica guardada).
 */
import React, { useCallback, useEffect, useState } from "react"
import { BookOpen, Loader2 } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { Incorporacao, Relato } from "../../services/api/perfil"
import { BTN_MINI } from "../curriculo/Curriculos"
import { useGeracao } from "../../contexto/Geracao"
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
  vazio = false,
  onAbrirConflitos,
}: {
  so: boolean
  onAviso: (m: string) => void
  onErro: (e: unknown) => void
  onPerfilMudou?: () => void
  /** Na aba Seus relatos: sem relatos, mostra o título e a dica em vez de sumir. */
  vazio?: boolean
  onAbrirConflitos?: () => void
}) {
  const { ativa, comecou, versao } = useGeracao()
  const [lista, setLista] = useState<Relato[] | null>(null)
  const [incorporacao, setIncorporacao] = useState<Incorporacao | null>(null)
  const [abertas, setAbertas] = useState(0)
  const [editando, setEditando] = useState<{ id: string; texto: string } | null>(null)
  const [marcados, setMarcados] = useState<string[]>([])
  const [ocupado, setOcupado] = useState("")

  const recarregar = useCallback(
    () =>
      Promise.all([
        perfilApi
          .relatos()
          .then((j) => setLista(j.relatos))
          .catch(() => setLista([])),
        perfilApi
          .obterRevisao("relatos")
          .then((j) => {
            setIncorporacao(j.incorporacao ?? null)
            setAbertas(j.revisao ? j.revisao.discordancias.filter((d) => !d.escolha && !j.revisao?.gravada_em).length : 0)
          })
          .catch(() => {
            setIncorporacao(null)
            setAbertas(0)
          }),
      ]),
    [],
  )

  useEffect(() => {
    recarregar()
  }, [recarregar, versao])

  const desfazer = async () => {
    if (!window.confirm("Desfazer a incorporação? O perfil volta à versão anterior e os relatos voltam para cá.")) return
    setOcupado("desfazer")
    try {
      await perfilApi.desfazerIncorporacao()
      await recarregar()
      if (onPerfilMudou) onPerfilMudou()
    } catch (e) {
      onErro(e)
    } finally {
      setOcupado("")
    }
  }

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

  /** Incorporar ao perfil: a IA analisa; o que diverge vai para Conflitos. Sem IA, o servidor responde erro. */
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

  const pendentes = (lista ?? []).filter((r) => !r.no_perfil && !r.em_conflito)
  const incorporados = (lista ?? []).filter((r) => r.no_perfil || r.em_conflito)

  const marcar = (id: string, sim: boolean) => setMarcados((m) => (sim ? [...new Set([...m, id])] : m.filter((x) => x !== id)))

  if (lista === null && vazio)
    return (
      <p className={`${DICA} flex items-center gap-2`}>
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando os relatos…
      </p>
    )
  if (lista && lista.length === 0 && vazio)
    return (
      <section className="space-y-2">
        <h4 className={`${H} flex items-center gap-2`}>
          <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Seus relatos (0)
        </h4>
        <p className={DICA}>
          Ainda não há relatos. Eles surgem quando você escreve um relato na candidatura assistida ou na análise de
          reprovação; cada um vale como fato e entra na nota das vagas.
        </p>
      </section>
    )
  if (!lista || lista.length === 0) return null
  const travado = so || Boolean(ocupado)
  const entrou = incorporacao?.entrou ?? []

  return (
    <section className="space-y-2">
      <h4 className={`${H} flex items-center gap-2`}>
        <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Seus relatos ({pendentes.length})
      </h4>
      <p className={DICA}>
        O que você contou na candidatura assistida e na análise de reprovação. Enquanto não entra no perfil, cada relato
        vale só na vaga em que foi escrito. Marque e clique em Incorporar: a IA põe no perfil o que encaixa e manda para
        Conflitos o que diverge.
      </p>
      {entrou.length > 0 && (
        <div className="p-3 rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/30 space-y-1.5 text-xs">
          <p className="font-semibold text-emerald-800 dark:text-emerald-300">Entrou no perfil:</p>
          <ul className="list-disc pl-4 space-y-1 text-slate-700 dark:text-slate-300">
            {entrou.map((e, i) => (
              <li key={i}>
                {e.novo}
                {(e.secao || e.cargo) && (
                  <span className={`${DICA} ml-1`}>({[e.secao, e.cargo].filter(Boolean).join(" · ")})</span>
                )}
              </li>
            ))}
          </ul>
          <button type="button" className={BTN_MINI} disabled={travado || ativa} onClick={desfazer}>
            {ocupado === "desfazer" ? "Desfazendo…" : "Desfazer"}
          </button>
        </div>
      )}
      {abertas > 0 && (
        <p className={`${DICA} flex items-center gap-2 flex-wrap`}>
          {abertas} ponto(s) para decidir em Conflitos.
          {onAbrirConflitos && (
            <button type="button" className={BTN_MINI} onClick={onAbrirConflitos}>
              Abrir Conflitos
            </button>
          )}
        </p>
      )}
      {pendentes.length === 0 && vazio && <p className={DICA}>Nenhum relato fora do perfil.</p>}
      {pendentes.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
            disabled={travado || ativa || marcados.length === 0}
            onClick={() => revisar(marcados)}
          >
            {ocupado === "revisar" && <Loader2 className="w-4 h-4 animate-spin" />}
            Incorporar ao perfil{marcados.length ? ` (${marcados.length})` : ""}
          </button>
          {marcados.length === 0 && <span className={DICA}>Marque um ou mais relatos.</span>}
        </div>
      )}
      <ul className="space-y-2">
        {pendentes.map((r) => (
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
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={travado || ativa}
                    title="A IA põe no perfil o que encaixa e manda para Conflitos o que diverge"
                    onClick={() => revisar([r.id])}
                  >
                    Incorporar
                  </button>
                  <button type="button" className={BTN_MINI} disabled={travado} onClick={() => setEditando({ id: r.id, texto: r.relato })}>
                    Corrigir
                  </button>
                  <button
                    type="button"
                    className={BTN_MINI}
                    disabled={travado}
                    onClick={() => acao("apagar", () => perfilApi.apagarRelato(r.id), "Relato apagado.")}
                  >
                    Excluir
                  </button>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
      {incorporados.length > 0 && (
        <details className="rounded-xl border border-slate-200 dark:border-slate-800 p-3 text-xs">
          <summary className="cursor-pointer font-semibold text-slate-800 dark:text-slate-200">
            Relatos incorporados ({incorporados.length})
          </summary>
          <ul className="space-y-2 mt-2">
            {incorporados.map((r) => (
              <li key={r.id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5">
                <p className="font-semibold text-slate-800 dark:text-slate-200">{r.pergunta || "(sem pergunta)"}</p>
                <p className="text-slate-700 dark:text-slate-300 whitespace-pre-line">{r.relato}</p>
                <p className={DICA}>
                  {diaMes(r.em)}
                  {r.vaga?.empresa ? ` · ${r.vaga.titulo} — ${r.vaga.empresa}` : ""}
                  {r.em_conflito ? " · esperando a sua decisão em Conflitos" : ""}
                </p>
                {r.em_conflito && onAbrirConflitos && (
                  <button type="button" className={BTN_MINI} onClick={onAbrirConflitos}>
                    Abrir Conflitos
                  </button>
                )}
                <button
                  type="button"
                  className={BTN_MINI}
                  disabled={travado}
                  onClick={() => {
                    if (window.confirm("Apagar este relato? O perfil não muda."))
                      acao("apagar", () => perfilApi.apagarRelato(r.id), "Relato apagado.")
                  }}
                >
                  Apagar
                </button>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}
