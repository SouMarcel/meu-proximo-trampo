/** Andamento da busca no topo do Relatório (dash/API.md §3.3), como o painel do dashboard antigo. */
import React, { useState } from "react"
import { Loader2, X, AlertTriangle, CheckCircle2, Search } from "lucide-react"
import type { EstadoBusca } from "../types/api"
import { useFerramenta } from "../contexto/Ferramenta"
import { horaDe } from "../utils/formatters"

interface Props {
  estado: EstadoBusca
  iaErro: { motivo: string; em: string } | null
  onCancelar: () => Promise<void>
  onTentarNota: () => Promise<void>
  onFechar: () => void
  onAbrirIA: () => void
}

const CAIXA = "rounded-2xl border p-4 text-xs sm:text-sm space-y-2 shadow-2xs"

function botao(classe = "") {
  return `px-3 py-1.5 rounded-xl text-xs font-semibold transition disabled:opacity-50 ${classe}`
}

export default function AndamentoBusca({ estado: e, iaErro, onCancelar, onTentarNota, onFechar, onAbrirIA }: Props) {
  const { podeGravar } = useFerramenta()
  const [ocupado, setOcupado] = useState(false)
  const rodar = async (fn: () => Promise<void>) => {
    setOcupado(true)
    try {
      await fn()
    } finally {
      setOcupado(false)
    }
  }
  const s = e.situacao
  const podeMexer = podeGravar && e.pode_alterar !== false

  const erros =
    e.erros && e.erros.length > 0 ? (
      <details className="text-xs text-slate-600 dark:text-slate-400">
        <summary className="cursor-pointer font-semibold">Avisos dos portais ({e.erros.length})</summary>
        <ul className="list-disc pl-5 mt-1 space-y-0.5">
          {e.erros.map((x, i) => (
            <li key={i}>{x}</li>
          ))}
        </ul>
        <p className="mt-1">Se um portal falhou, espere antes de tentar de novo: insistir costuma prolongar o bloqueio.</p>
      </details>
    ) : null

  const fechar = (
    <button onClick={onFechar} className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" title="Fechar">
      <X className="w-4 h-4" />
    </button>
  )

  if (s === "externa") {
    return (
      <div role="status" className={`${CAIXA} bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-900 text-indigo-900 dark:text-indigo-200`}>
        <p className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
          <span>
            <b>Busca em andamento {e.origem === "pagina" ? "pela página" : "no terminal ou no chat"}</b>
            {e.inicio ? ` desde ${horaDe(e.inicio)}` : ""}. O relatório se atualiza quando ela terminar.
          </span>
        </p>
      </div>
    )
  }

  if (s === "consultando" || s === "descricoes" || s === "gravando" || s === "cancelando") {
    const total = e.total || 0
    const n = Math.min((e.feitas || 0) + (s === "consultando" ? 1 : 0), total)
    const pct = total ? Math.round((100 * (e.feitas || 0)) / total) : 0
    const c = e.consulta
    const linha =
      s === "cancelando"
        ? "Cancelando: termina a consulta atual e não grava nada."
        : s === "gravando"
          ? "Gravando no relatório…"
          : s === "descricoes" && e.descricoes
            ? `Lendo as descrições das vagas: ${e.descricoes.lidas} de ${e.descricoes.total}.`
            : c?.portal
              ? `Consultando ${c.portal}: ${c.cargo}${c.grupo && c.grupo !== "remoto" ? ` (${c.grupo})` : ""}…`
              : "Começando…"
    return (
      <div role="status" className={`${CAIXA} bg-white dark:bg-slate-900 border-indigo-200 dark:border-indigo-900`}>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <Search className="w-4 h-4 text-indigo-500" />
            <span>Buscando vagas</span>
            <span className="font-normal text-slate-500">
              consulta {n} de {total} · {e.encontradas || 0} vaga(s) encontrada(s)
            </span>
          </p>
          {(s === "consultando" || s === "descricoes") && e.origem === "pagina" && (
            <button
              onClick={() => rodar(onCancelar)}
              disabled={!podeMexer || ocupado}
              className={botao("text-rose-700 dark:text-rose-300 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900")}
              title="Termina a consulta atual e não grava nada"
            >
              Cancelar
            </button>
          )}
        </div>
        <div className="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
          <div className="h-full bg-indigo-500 transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-slate-600 dark:text-slate-400">{linha}</p>
      </div>
    )
  }

  if (s === "concluida" && e.resumo) {
    const r = e.resumo
    const a = e.analise
    let nota: React.ReactNode
    if (!r.com_nota) {
      nota = (
        <>
          Gravadas sem nota. Para ter a nota de aderência, escolha uma IA{" "}
          <button onClick={onAbrirIA} className="underline font-semibold">
            no botão IA
          </button>{" "}
          (com o perfil montado em Meu perfil).
        </>
      )
    } else if (a?.rodando) {
      nota = (
        <span className="flex items-center gap-1.5 font-semibold text-indigo-700 dark:text-indigo-300">
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> IA analisando: faltam {a.faltam} vaga(s)…
        </span>
      )
    } else if (a?.erro && a.faltam) {
      nota = (
        <span className="flex items-center gap-2 flex-wrap">
          <span>A nota não saiu: {a.erro.motivo}</span>
          <button
            onClick={() => rodar(onTentarNota)}
            disabled={!podeMexer || ocupado}
            className={botao("text-indigo-700 dark:text-indigo-300 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800")}
          >
            Tentar a nota de novo
          </button>
        </span>
      )
    } else if (a?.faltam) {
      nota = `${a.faltam} vaga(s) ainda sem nota.`
    } else {
      nota = "Notas prontas."
    }
    return (
      <div role="status" className={`${CAIXA} bg-white dark:bg-slate-900 border-emerald-200 dark:border-emerald-900`}>
        <div className="flex items-center justify-between gap-3">
          <p className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            Busca concluída às {horaDe(e.fim)}
          </p>
          {fechar}
        </div>
        <p className="text-slate-700 dark:text-slate-300">
          {r.brutas} vaga(s) encontrada(s) · <b>{r.novas} nova(s) para decidir</b> · {r.fora_criterios} fora dos
          critérios · {r.ja_vistas} já vista(s) · {r.excluidas_titulo} cortada(s) pelo título · {r.fora_da_janela} fora
          da janela
        </p>
        {Boolean(r.pendentes) && (
          <p className="text-slate-600 dark:text-slate-400">
            {r.pendentes} vaga(s) com descrição pendente: o portal limita os pedidos, e o texto delas é lido na próxima
            busca ou em Completar descrições, antes da nota.
          </p>
        )}
        {Boolean(r.completadas) && (
          <p className="text-slate-600 dark:text-slate-400">
            {r.completadas} descrição(ões) pendente(s) de buscas anteriores lida(s) agora.
          </p>
        )}
        <div className="text-slate-700 dark:text-slate-300">{nota}</div>
        {erros}
      </div>
    )
  }

  if (s === "ociosa") {
    // sem busca: só o aviso de que a análise automática falhou, se houver
    if (!iaErro) return null
    return (
      <div role="status" className={`${CAIXA} bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200`}>
        <p className="flex items-center gap-2 flex-wrap">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>A última análise automática não deu nota: {iaErro.motivo}</span>
          <button
            onClick={() => rodar(onTentarNota)}
            disabled={!podeMexer || ocupado}
            className={botao("bg-white/70 dark:bg-slate-900 border border-amber-300 dark:border-amber-800")}
          >
            Tentar a nota de novo
          </button>
        </p>
      </div>
    )
  }

  const titulo = s === "cancelada" ? "Busca cancelada" : s === "interrompida" ? "Busca interrompida" : "A busca não terminou"
  return (
    <div
      role="status"
      className={`${CAIXA} ${
        s === "falha"
          ? "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900"
          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="font-semibold text-slate-900 dark:text-white">{titulo}</p>
        {fechar}
      </div>
      {e.mensagem && <p className="text-slate-700 dark:text-slate-300">{e.mensagem}</p>}
      {erros}
    </div>
  )
}
