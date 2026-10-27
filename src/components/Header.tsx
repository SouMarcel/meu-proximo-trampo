import React, { useState } from "react"
import {
  Plus,
  Search,
  SlidersHorizontal,
  Sparkles,
  User,
  Coffee,
  Briefcase,
  Link2,
  Monitor,
  Sun,
  Moon,
} from "lucide-react"
import { useFerramenta } from "../contexto/Ferramenta"
import { ScreenPreferencesService, aplicarTema, Tema } from "../services/storage"

interface HeaderProps {
  /** Motivo de o Buscar vagas estar desligado ("" = pode buscar). */
  motivoBuscaDesligada: string
  /** "HH:MM" a partir de quando dá para buscar de novo, ou "". */
  proximaBusca: string
  onOpenAddModal: () => void
  onOpenSearchModal: () => void
  onOpenFiltersModal: () => void
  onOpenProfileModal: () => void
  onOpenAIModal: () => void
  /** A IA principal falhou na última tentativa (spec 032): o botão IA mostra o alerta com o motivo. */
  iaAlerta?: { nome: string; modelo: string; motivo: string; em: string } | null
  onOpenAccountsModal?: () => void
}

const PROXIMO_TEMA: Record<Tema, Tema> = { sistema: "claro", claro: "escuro", escuro: "sistema" }
const ROTULO_TEMA: Record<Tema, string> = {
  sistema: "Tema: o do sistema",
  claro: "Tema: claro",
  escuro: "Tema: escuro",
}

export default function Header({
  motivoBuscaDesligada,
  proximaBusca,
  onOpenAddModal,
  onOpenSearchModal,
  onOpenFiltersModal,
  onOpenProfileModal,
  onOpenAIModal,
  onOpenAccountsModal,
  iaAlerta,
}: HeaderProps) {
  const { ia, servidor } = useFerramenta()
  const [tema, setTema] = useState<Tema>(() => ScreenPreferencesService.getTema())

  const trocarTema = () => {
    const novo = PROXIMO_TEMA[tema]
    setTema(novo)
    ScreenPreferencesService.setTema(novo)
    aplicarTema(novo)
  }
  const IconeTema = tema === "claro" ? Sun : tema === "escuro" ? Moon : Monitor

  const rotuloIA =
    servidor === "demo"
      ? "IA"
      : ia?.disponivel
        ? `IA: ${ia.nome}${ia.modelo ? " · " + ia.modelo : ""}`
        : "IA: escolher"

  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-16 py-2 gap-3 flex-wrap">
          {/* Marca */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">
                Meu Próximo Trampo
              </span>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
                Busca de vagas, nota de aderência e quadro de candidaturas
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* IA escolhida */}
            <button
              onClick={onOpenAIModal}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition max-w-[220px]"
              title={
                iaAlerta
                  ? `${iaAlerta.nome} falhou às ${iaAlerta.em.slice(11, 16)}: ${iaAlerta.motivo} (clique para ver as reservas)`
                  : ia?.disponivel
                    ? "IA escolhida (clique para trocar)"
                    : "Nenhuma IA pronta: clique para escolher"
              }
            >
              <Sparkles className="w-3.5 h-3.5 text-violet-500 shrink-0" />
              <span className="truncate">{rotuloIA}</span>
              <span
                className={`w-2 h-2 rounded-full inline-block shrink-0 ${
                  iaAlerta ? "bg-amber-500" : ia?.disponivel ? "bg-emerald-500" : "bg-slate-400"
                }`}
              />
            </button>

            {/* Tema */}
            <button
              onClick={trocarTema}
              className="p-1.5 rounded-lg text-slate-600 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title={`${ROTULO_TEMA[tema]} (clique para trocar)`}
              aria-label={ROTULO_TEMA[tema]}
            >
              <IconeTema className="w-4 h-4" />
            </button>

            {/* Apoie o projeto */}
            <a
              href="https://buymeacoffee.com/meuproximotrampo"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/50 border border-amber-200 dark:border-amber-800 transition"
              title="Gostou da ferramenta? Apoie o projeto com um café (Buy Me a Coffee)"
            >
              <Coffee className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Apoie ☕</span>
            </a>

            {/* Buscar vagas */}
            <div className="flex items-center gap-1">
              <button
                onClick={onOpenSearchModal}
                disabled={Boolean(motivoBuscaDesligada)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                title={motivoBuscaDesligada || "Consultar os portais com os seus filtros e gravar as vagas novas no relatório"}
              >
                <Search className="w-3.5 h-3.5 text-indigo-500" />
                <span className="hidden sm:inline">Buscar vagas</span>
              </button>
              {proximaBusca && (
                <span className="text-[11px] text-slate-500 dark:text-slate-400" title={motivoBuscaDesligada}>
                  de novo às {proximaBusca}
                </span>
              )}
            </div>

            {/* Filtros da busca */}
            <button
              onClick={onOpenFiltersModal}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title="Filtros da busca"
            >
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden sm:inline">Filtros</span>
              </div>
            </button>

            {/* Contas conectadas */}
            {onOpenAccountsModal && (
              <button
                onClick={onOpenAccountsModal}
                className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
                title="Atualizar o quadro com o andamento das suas candidaturas na Gupy e no Indeed"
              >
                <div className="flex items-center gap-1.5">
                  <Link2 className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="hidden sm:inline">Atualizar candidaturas</span>
                </div>
              </button>
            )}

            {/* Meu perfil */}
            <button
              onClick={onOpenProfileModal}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
              title="Meu perfil"
            >
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden sm:inline">Meu perfil</span>
              </div>
            </button>

            {/* Adicionar vaga */}
            <button
              onClick={onOpenAddModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-sm shadow-indigo-600/30 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Adicionar vaga</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
