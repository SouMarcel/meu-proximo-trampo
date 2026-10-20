/**
 * Telas que ainda não usam o servidor na página nova (spec 025, histórias 2 a 6): em vez de dados de exemplo,
 * um aviso com o caminho para a mesma tela no dashboard de sempre. Some quando a tela é ligada.
 */
import React from "react"
import { X, ExternalLink, Construction } from "lucide-react"
import { getApiBaseUrl } from "../services/api"

export interface TelaAntiga {
  titulo: string
  /** Onde fica na página de sempre, ex.: 'botão "Meu perfil", no topo'. */
  onde: string
}

function Conteudo({ tela }: { tela: TelaAntiga }) {
  return (
    <div className="space-y-3 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
      <p>
        <b>{tela.titulo}</b> ainda não está na página nova: por enquanto, use a página de sempre, no {tela.onde}. Nada
        se perde: as duas páginas usam os mesmos dados.
      </p>
      <a
        href={getApiBaseUrl() + "/"}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
      >
        <span>Abrir a página de sempre</span>
        <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </div>
  )
}

export function AvisoTelaAntiga({ tela, onClose }: { tela: TelaAntiga; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-tela-antiga"
        className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <h3 id="titulo-tela-antiga" className="flex items-center gap-2 font-bold text-base text-slate-900 dark:text-white">
            <Construction className="w-5 h-5 text-amber-500" />
            {tela.titulo}
          </h3>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>
        <Conteudo tela={tela} />
      </div>
    </div>
  )
}

export function CartaoTelaAntiga({ tela }: { tela: TelaAntiga }) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 space-y-3 max-w-2xl">
      <h3 className="flex items-center gap-2 font-bold text-base text-slate-900 dark:text-white">
        <Construction className="w-5 h-5 text-amber-500" />
        {tela.titulo}
      </h3>
      <Conteudo tela={tela} />
    </div>
  )
}

export const TELAS_ANTIGAS = {
  contas: { titulo: "Atualizar candidaturas", onde: 'botão "Atualizar candidaturas", no topo' },
} satisfies Record<string, TelaAntiga>
