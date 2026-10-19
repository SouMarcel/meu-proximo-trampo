import React, { useState, useEffect } from "react"
import {
  X,
  Search,
  Play,
  Square,
  CheckCircle2,
  Loader2,
  Clock,
  Sparkles,
  Globe,
  Layers,
  AlertCircle,
} from "lucide-react"
import { FiltrosBusca } from "../../types/job"

interface SearchJobsModalProps {
  isOpen: boolean
  onClose: () => void
  filtros: FiltrosBusca
  onFinishSearch: (novasVagasCount: number) => void
}

interface SearchStep {
  id: string
  name: string
  status: "idle" | "running" | "completed" | "error"
  foundCount?: number
}

export default function SearchJobsModal({
  isOpen,
  onClose,
  filtros,
  onFinishSearch,
}: SearchJobsModalProps) {
  if (!isOpen) return null

  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStepIndex, setCurrentStepIndex] = useState(-1)
  const [searchFinished, setSearchFinished] = useState(false)
  const [totalFound, setTotalFound] = useState(0)

  const [steps, setSteps] = useState<SearchStep[]>([
    { id: "s1", name: "Gupy (APIs públicas & ATS)", status: "idle" },
    { id: "s2", name: "Indeed (vagas recentes de tecnologia)", status: "idle" },
    {
      id: "s3",
      name: "LinkedIn (consultas públicas e empresas)",
      status: "idle",
    },
    { id: "s4", name: "Nerdin & Startup.jobs", status: "idle" },
    {
      id: "s5",
      name: "Fontes Globais (RemoteOK, Remotive, Himalayas)",
      status: "idle",
    },
    {
      id: "s6",
      name: "Deduplicação & Análise de Aderência com IA",
      status: "idle",
    },
  ])

  const handleStartSearch = () => {
    setIsRunning(true)
    setProgress(5)
    setCurrentStepIndex(0)
    setSearchFinished(false)
    setTotalFound(0)

    // Reseta status
    setSteps((prev) =>
      prev.map((s) => ({ ...s, status: "idle", foundCount: 0 })),
    )

    // Simula execução dos passos em sequência
    let step = 0
    let accumulatedFound = 0

    const interval = setInterval(() => {
      if (step < 6) {
        const stepCounts = [14, 18, 22, 6, 12, 0]
        const foundInStep = stepCounts[step]
        accumulatedFound += foundInStep

        setSteps((prev) =>
          prev.map((s, idx) => {
            if (idx === step) {
              return { ...s, status: "completed", foundCount: foundInStep }
            }
            if (idx === step + 1) {
              return { ...s, status: "running" }
            }
            return s
          }),
        )

        step++
        setCurrentStepIndex(step)
        setProgress(Math.min(100, Math.round((step / 6) * 100)))
      } else {
        clearInterval(interval)
        setIsRunning(false)
        setSearchFinished(true)
        setTotalFound(accumulatedFound)
        onFinishSearch(4) // 4 novas vagas elegíveis geradas
      }
    }, 900)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Buscar Vagas nos Portais
              </h3>
              <p className="text-xs text-slate-500">
                Varredura automatizada em todos os portais cadastrados com seus
                filtros
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5">
          {/* Active Search Terms Preview */}
          <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
              <span>
                Termos configurados para a busca ({filtros.termos.length}):
              </span>
              <span className="text-indigo-600 dark:text-indigo-400 font-bold">
                {filtros.localidade.cidade} / Remoto
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {filtros.termos.map((t, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md text-xs font-mono bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Progress Bar if running */}
          {isRunning && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                <span className="flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Varredura em andamento...</span>
                </span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Steps List */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Etapas da Varredura
            </h4>
            <div className="space-y-1.5">
              {steps.map((st, idx) => (
                <div
                  key={st.id}
                  className="flex items-center justify-between p-2.5 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-white dark:bg-slate-900 text-xs"
                >
                  <div className="flex items-center gap-2">
                    {st.status === "completed" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    ) : st.status === "running" ? (
                      <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-slate-300 dark:border-slate-700" />
                    )}
                    <span
                      className={
                        st.status === "completed"
                          ? "text-slate-900 dark:text-white font-medium"
                          : st.status === "running"
                            ? "text-indigo-600 dark:text-indigo-400 font-bold"
                            : "text-slate-400"
                      }
                    >
                      {st.name}
                    </span>
                  </div>

                  {st.foundCount ? (
                    <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                      +{st.foundCount} encontradas
                    </span>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          {/* Completion summary */}
          {searchFinished && (
            <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 space-y-1">
              <div className="font-bold flex items-center gap-1.5 text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Busca finalizada com sucesso!</span>
              </div>
              <p>
                Foram analisados {totalFound} anúncios nos portais e novas
                oportunidades com alta aderência foram adicionadas ao seu
                Relatório de Vagas.
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Última busca: Hoje às 14:32</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
            >
              Fechar
            </button>

            <button
              onClick={handleStartSearch}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Buscando...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Iniciar Varredura</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
