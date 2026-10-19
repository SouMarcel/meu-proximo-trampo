import React from "react"
import {
  Kanban,
  FileText,
  Globe2,
  BarChart3,
  MessageSquareCode,
} from "lucide-react"

export type ActiveTab = "quadro" | "relatorio" | "internacional" | "metricas" | "entrevistas"

interface NavigationTabsProps {
  activeTab: ActiveTab
  onChangeTab: (tab: ActiveTab) => void
  countQuadro: number
  countPendentes: number
  countInternacional: number
  countEntrevistas: number
}

export default function NavigationTabs({
  activeTab,
  onChangeTab,
  countQuadro,
  countPendentes,
  countInternacional,
  countEntrevistas,
}: NavigationTabsProps) {
  const tabs: {
    id: ActiveTab
    label: string
    icon: React.ReactNode
    count?: number
    countColor?: string
  }[] = [
    {
      id: "quadro",
      label: "Quadro de Candidaturas",
      icon: <Kanban className="w-4 h-4" />,
      count: countQuadro,
      countColor:
        "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
    },
    {
      id: "relatorio",
      label: "Relatório de Vagas (Triagem)",
      icon: <FileText className="w-4 h-4" />,
      count: countPendentes,
      countColor:
        "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
    },
    {
      id: "internacional",
      label: "Internacional & Remoto",
      icon: <Globe2 className="w-4 h-4" />,
      count: countInternacional,
      countColor:
        "bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300",
    },
    {
      id: "metricas",
      label: "Métricas & Funil",
      icon: <BarChart3 className="w-4 h-4" />,
    },
    {
      id: "entrevistas",
      label: "Preparador de Entrevistas",
      icon: <MessageSquareCode className="w-4 h-4" />,
      count: countEntrevistas > 0 ? countEntrevistas : undefined,
      countColor:
        "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
    },
  ]

  return (
    <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav
          className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2 scrollbar-none"
          aria-label="Tabs"
        >
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => onChangeTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-150 ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 shadow-xs border border-indigo-200 dark:border-indigo-800"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
                }`}
              >
                <span
                  className={
                    isActive
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-slate-400"
                  }
                >
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-xs font-semibold ${
                      tab.countColor ||
                      "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
