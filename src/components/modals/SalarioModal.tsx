/** Faixa salarial a partir do card do quadro (spec 028), numa janela própria, fora do card arrastável. */
import React from "react"
import { createPortal } from "react-dom"
import { X, Banknote } from "lucide-react"
import type { Vaga } from "../../types/api"
import FaixaSalarial from "../kit/FaixaSalarial"

export default function SalarioModal({ vaga, onClose }: { vaga: Vaga; onClose: () => void }) {
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
        aria-labelledby="titulo-salario"
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <Banknote className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-salario" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Faixa salarial
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
        <div className="p-5 overflow-y-auto flex-1 text-slate-700 dark:text-slate-300">
          <FaixaSalarial vagaId={vaga.id} semTitulo />
        </div>
      </div>
    </div>,
    document.body,
  )
}
