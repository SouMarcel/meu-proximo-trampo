import React, { useState, useMemo } from "react"
import {
  Search,
  LayoutGrid,
  List,
  Filter,
  Sparkles,
  ChevronDown,
  Plus,
  Briefcase,
  Building2,
  MapPin,
  Calendar,
  ExternalLink,
  Clock,
} from "lucide-react"
import { Vaga, Etapa, Plataforma, Area, ModeloTrabalho } from "../types/job"
import JobCard from "./JobCard"
import {
  getEtapaInfo,
  getPlataformaStyle,
  getAderenciaBadge,
  formatarDataRelativa,
  formatarModelo,
  areaDe,
} from "../utils/formatters"

interface KanbanBoardProps {
  vagas: Vaga[]
  onSelectVaga: (vaga: Vaga) => void
  onMoveStage: (id: string, stage: Etapa) => void
  onDeleteVaga: (id: string) => void
  onOpenAddModal: () => void
}

const ETAPAS: {
  key: Etapa
  title: string
  description: string
  headerColor: string
  badgeBg: string
}[] = [
  {
    key: "salva",
    title: "Salva",
    description: "Vagas marcadas para revisão ou preparo",
    headerColor: "border-slate-400 text-slate-700 dark:text-slate-300",
    badgeBg:
      "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  },
  {
    key: "aplicada",
    title: "Aplicação Enviada",
    description: "Candidaturas enviadas aguardando retorno",
    headerColor: "border-blue-500 text-blue-700 dark:text-blue-300",
    badgeBg: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  {
    key: "entrevista",
    title: "Entrevista",
    description: "Em fase de conversas e testes práticos",
    headerColor: "border-purple-500 text-purple-700 dark:text-purple-300",
    badgeBg:
      "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  },
  {
    key: "proposta",
    title: "Proposta Recebida",
    description: "Ofertas em análise ou negociação",
    headerColor: "border-emerald-500 text-emerald-700 dark:text-emerald-300",
    badgeBg:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  {
    key: "encerrada",
    title: "Encerrada",
    description: "Processos concluídos ou declinados",
    headerColor: "border-zinc-400 text-zinc-600 dark:text-zinc-400",
    badgeBg: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  },
]

export default function KanbanBoard({
  vagas,
  onSelectVaga,
  onMoveStage,
  onDeleteVaga,
  onOpenAddModal,
}: KanbanBoardProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [filterPlataforma, setFilterPlataforma] = useState<string>("")
  const [filterArea, setFilterArea] = useState<string>("")
  const [filterModo, setFilterModo] = useState<string>("")
  const [viewMode, setViewMode] = useState<"board" | "list">("board")
  const [draggedVagaId, setDraggedVagaId] = useState<string | null>(null)

  // Todas as plataformas presentes nas vagas
  const availablePlatforms = useMemo(() => {
    const set = new Set<string>()
    vagas.forEach((v) => {
      if (v.plataforma) set.add(v.plataforma)
    })
    return Array.from(set).sort()
  }, [vagas])

  // Filtrar apenas vagas que possuem etapa (isto é, estão no funil)
  const pipelineVagas = useMemo(() => {
    return vagas.filter((v) => {
      const noQuadro = Boolean(v.etapa && (v.origem === "manual" || v.triagem === "seguir"))
      if (!noQuadro) return false
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        const matchTitulo = v.titulo.toLowerCase().includes(q)
        const matchEmpresa = v.empresa.toLowerCase().includes(q)
        const matchDesc = v.descricao?.toLowerCase().includes(q)
        if (!matchTitulo && !matchEmpresa && !matchDesc) return false
      }
      if (filterPlataforma) {
        const plats = [v.plataforma, ...(v.outras_plataformas || [])]
        if (!plats.includes(filterPlataforma)) {
          return false
        }
      }
      if (filterArea && areaDe(v) !== filterArea) {
        return false
      }
      if (filterModo) {
        if (filterModo === "remoto" && !v.remoto) return false
        if (filterModo === "hibrido" && v.modelo_trabalho !== "hibrido")
          return false
        if (filterModo === "presencial" && v.modelo_trabalho !== "presencial")
          return false
      }
      return true
    })
  }, [vagas, searchQuery, filterPlataforma, filterArea, filterModo])

  // Agrupar vagas por etapa
  const vagasPorEtapa = useMemo(() => {
    const map: Record<Etapa, Vaga[]> = {
      salva: [],
      aplicada: [],
      entrevista: [],
      proposta: [],
      encerrada: [],
    }
    pipelineVagas.forEach((v) => {
      if (v.etapa && map[v.etapa]) {
        map[v.etapa].push(v)
      }
    })
    return map
  }, [pipelineVagas])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetStage: Etapa) => {
    e.preventDefault()
    if (draggedVagaId) {
      onMoveStage(draggedVagaId, targetStage)
      setDraggedVagaId(null)
    }
  }

  return (
    <div className="space-y-4">
      {/* Filter and Control Toolbar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-2xs">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filtrar por cargo, empresa, tecnologia..."
              className="w-full pl-9 pr-4 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
            />
          </div>

          {/* Dropdown Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Platform filter */}
            <select
              value={filterPlataforma}
              onChange={(e) => setFilterPlataforma(e.target.value)}
              className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="">Todas as plataformas</option>
              {availablePlatforms.map((plat) => (
                <option key={plat} value={plat}>
                  {plat}
                </option>
              ))}
            </select>

            {/* Area filter */}
            <select
              value={filterArea}
              onChange={(e) => setFilterArea(e.target.value)}
              className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="">Todas as áreas</option>
              <option value="nacional">Nacional (Brasil)</option>
              <option value="internacional">
                Internacional (Remoto Exterior)
              </option>
            </select>

            {/* Modality pills */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700 text-xs">
              <button
                onClick={() => setFilterModo("")}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  filterModo === ""
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setFilterModo("remoto")}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  filterModo === "remoto"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Remoto
              </button>
              <button
                onClick={() => setFilterModo("hibrido")}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  filterModo === "hibrido"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Híbrido
              </button>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setViewMode("board")}
                className={`p-1.5 rounded-lg transition ${
                  viewMode === "board"
                    ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-2xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
                title="Visualização em Quadro Kanban"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`p-1.5 rounded-lg transition ${
                  viewMode === "list"
                    ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-2xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
                title="Visualização em Lista / Tabela"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Board View */}
      {viewMode === "board" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-start">
          {ETAPAS.map((etapa) => {
            const cards = vagasPorEtapa[etapa.key] || []

            return (
              <div
                key={etapa.key}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, etapa.key)}
                className="flex flex-col bg-slate-100/70 dark:bg-slate-900/50 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 p-3 min-h-[580px] transition"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-xs sm:text-sm text-slate-800 dark:text-slate-200">
                      {etapa.title}
                    </h2>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-bold ${etapa.badgeBg}`}
                    >
                      {cards.length}
                    </span>
                  </div>

                  {etapa.key === "salva" && (
                    <button
                      onClick={onOpenAddModal}
                      className="p-1 rounded-md text-slate-400 hover:text-indigo-600 hover:bg-slate-200 dark:hover:bg-slate-800 transition"
                      title="Adicionar vaga nesta coluna"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Cards Container */}
                <div className="space-y-3 flex-1">
                  {cards.map((vaga) => (
                    <div
                      key={vaga.id}
                      draggable
                      onDragStart={() => setDraggedVagaId(vaga.id)}
                      onDragEnd={() => setDraggedVagaId(null)}
                    >
                      <JobCard
                        vaga={vaga}
                        onSelect={onSelectVaga}
                        onMoveStage={onMoveStage}
                        onDelete={onDeleteVaga}
                      />
                    </div>
                  ))}

                  {cards.length === 0 && (
                    <div className="h-32 flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                      <p className="text-xs text-slate-400">
                        {etapa.description}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        /* List / Table View */
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 border-b border-slate-200 dark:border-slate-800 font-semibold">
                <tr>
                  <th className="py-3.5 px-4">Vaga & Empresa</th>
                  <th className="py-3.5 px-4">Plataforma</th>
                  <th className="py-3.5 px-4">Etapa</th>
                  <th className="py-3.5 px-4">Aderência</th>
                  <th className="py-3.5 px-4">Localidade</th>
                  <th className="py-3.5 px-4">Publicada</th>
                  <th className="py-3.5 px-4 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {pipelineVagas.map((vaga) => {
                  const plat = getPlataformaStyle(vaga.plataforma)
                  const ader = getAderenciaBadge(vaga.aderencia)
                  const infoEtapa = getEtapaInfo(vaga.etapa)

                  return (
                    <tr
                      key={vaga.id}
                      onClick={() => onSelectVaga(vaga)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {vaga.titulo}
                        </div>
                        <div className="text-xs text-slate-500">
                          {vaga.empresa}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-md text-xs font-semibold border ${plat.bg} ${plat.text} ${plat.border}`}
                        >
                          {vaga.plataforma}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-semibold ${infoEtapa.badgeBg} ${infoEtapa.badgeText}`}
                        >
                          {infoEtapa.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {vaga.aderencia !== undefined ? (
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-bold border ${ader.bg} ${ader.text} ${ader.ring}`}
                          >
                            {vaga.aderencia}%
                          </span>
                        ) : (
                          <span className="text-slate-400 text-xs">
                            Pendente
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600 dark:text-slate-400">
                        {vaga.local}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 text-xs">
                        {formatarDataRelativa(vaga.publicada_em)}
                      </td>
                      <td
                        className="py-3.5 px-4 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <a
                          href={vaga.url_candidatura || vaga.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          <span>Abrir</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
