import React from "react"
import {
  Plus,
  Search,
  SlidersHorizontal,
  Sparkles,
  User,
  Coffee,
  CheckCircle2,
  Briefcase,
  Link2,
} from "lucide-react"
import { ConfigIA } from "../types/job"

interface HeaderProps {
  configIA: ConfigIA
  isBackendConnected?: boolean | null
  onOpenAddModal: () => void
  onOpenSearchModal: () => void
  onOpenFiltersModal: () => void
  onOpenProfileModal: () => void
  onOpenOnboardingModal?: () => void
  onOpenAIModal: () => void
  onOpenAccountsModal?: () => void
}

export default function Header({
  configIA,
  isBackendConnected,
  onOpenAddModal,
  onOpenSearchModal,
  onOpenFiltersModal,
  onOpenProfileModal,
  onOpenOnboardingModal,
  onOpenAIModal,
  onOpenAccountsModal,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">
                  Meu Próximo Trampo
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
                  v2.0
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
                Agregador & Funil Inteligente de Vagas Multiplataforma
              </p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="hidden md:flex items-center gap-2">
            {/* IA Status Badge */}
            <button
              onClick={onOpenAIModal}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
              title="Configurações do Modelo de IA"
            >
              <Sparkles className="w-3.5 h-3.5 text-violet-500" />
              <span>
                IA: <span className="font-semibold">{configIA.modelo}</span>
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
            </button>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-2">
            {/* Support / Buy Me a Coffee */}
            <a
              href="https://buymeacoffee.com/meuproximotrampo"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/50 border border-amber-200 dark:border-amber-800 transition"
              title="Apoie o desenvolvedor com um café"
            >
              <Coffee className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Apoiar</span>
            </a>

            {/* Search Trigger */}
            <button
              onClick={onOpenSearchModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title="Executar varredura em todas as plataformas"
            >
              <Search className="w-3.5 h-3.5 text-indigo-500" />
              <span className="hidden sm:inline">Buscar Vagas</span>
            </button>

            {/* Filters Trigger */}
            <button
              onClick={onOpenFiltersModal}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title="Configurar filtros de busca e portais"
            >
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden sm:inline">Filtros</span>
              </div>
            </button>



                        {/* Connected Accounts Trigger */}
            {onOpenAccountsModal && (
              <button
                onClick={onOpenAccountsModal}
                className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
                title="Atualizar o quadro com o andamento das suas candidaturas nos portais (Gupy, Indeed, LinkedIn)"
              >
                <div className="flex items-center gap-1.5">
                  <Link2 className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="hidden sm:inline">Contas</span>
                </div>
              </button>
            )}

            {/* Profile Trigger */}
            <button
              onClick={onOpenProfileModal}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title="Meu perfil profissional e competências"
            >
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden sm:inline">Perfil</span>
              </div>
            </button>

            {/* Add Job CTA */}
            <button
              onClick={onOpenAddModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-sm shadow-indigo-600/30 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Adicionar Vaga</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
