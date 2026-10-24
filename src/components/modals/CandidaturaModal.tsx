/**
 * Candidatar com ajuda a partir do card do quadro (spec 027): a mesma ajuda do kit da vaga, numa janela própria. Abre a
 * vaga na janela da ferramenta ao abrir; a ferramenta só preenche campos, e quem envia é a pessoa.
 */
import React from "react"
import { createPortal } from "react-dom"
import { X, Wand2 } from "lucide-react"
import type { Vaga } from "../../types/api"
import CandidaturaAssistida from "../kit/CandidaturaAssistida"

export default function CandidaturaModal({
  vaga,
  onClose,
  onAviso,
}: {
  vaga: Vaga
  onClose: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
}) {
  // portal: fora do card arrastável; o clique não sobe para o card (que abriria o detalhe)
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs cursor-default"
      onClick={(e) => {
        e.stopPropagation()
        onClose()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-candidatar"
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Wand2 className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-candidatar" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Candidatar com ajuda
              </h3>
              <p className="text-xs text-slate-500">
                {vaga.titulo} — {vaga.empresa}
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-5 overflow-y-auto flex-1 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          <CandidaturaAssistida vaga={vaga} onAviso={onAviso} abrirAoMontar semMoldura />
        </div>
      </div>
    </div>,
    document.body,
  )
}
