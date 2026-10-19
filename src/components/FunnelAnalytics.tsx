import React, { useMemo } from "react"
import {
  TrendingUp,
  Target,
  Award,
  CheckCircle2,
  BarChart3,
  PieChart,
  ArrowRight,
  Briefcase,
  Calendar,
  Clock,
  Sparkles,
} from "lucide-react"
import { Vaga, Etapa } from "../types/job"

interface FunnelAnalyticsProps {
  vagas: Vaga[]
  onNavigateToTab?: (tab: string) => void
}

export default function FunnelAnalytics({ vagas }: FunnelAnalyticsProps) {
  const metrics = useMemo(() => {
    const total = vagas.length
    const salvas = vagas.filter((v) => v.etapa === "salva").length
    const aplicadas = vagas.filter((v) => v.etapa === "aplicada").length
    const entrevistas = vagas.filter((v) => v.etapa === "entrevista").length
    const propostas = vagas.filter((v) => v.etapa === "proposta").length
    const contratados = vagas.filter((v) => v.resultado === "contratado").length

    // Médias e taxas
    const totalAplicadasOuMais =
      aplicadas + entrevistas + propostas + contratados
    const taxaEntrevista =
      totalAplicadasOuMais > 0
        ? Math.round(
            ((entrevistas + propostas + contratados) / totalAplicadasOuMais) *
              100,
          )
        : 0

    const taxaProposta =
      entrevistas + propostas + contratados > 0
        ? Math.round(
            ((propostas + contratados) /
              (entrevistas + propostas + contratados)) *
              100,
          )
        : 0

    const notas = vagas
      .map((v) => v.aderencia)
      .filter((n): n is number => n !== undefined)
    const mediaAderencia =
      notas.length > 0
        ? Math.round(notas.reduce((acc, curr) => acc + curr, 0) / notas.length)
        : 0

    // Contagem por plataforma
    const plataformasMap: Record<string, number> = {}
    vagas.forEach((v) => {
      plataformasMap[v.plataforma] = (plataformasMap[v.plataforma] || 0) + 1
    })
    const topPlataformas = Object.entries(plataformasMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)

    // Skills mais frequentes
    const skillsMap: Record<string, number> = {}
    vagas.forEach((v) => {
      v.encaixe?.forEach((s) => {
        const limpo = s.split(" ")[0].replace(/[^a-zA-Z0-9#+.]/g, "")
        if (limpo.length > 2) {
          skillsMap[limpo] = (skillsMap[limpo] || 0) + 1
        }
      })
    })
    const topSkills = Object.entries(skillsMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)

    return {
      total,
      salvas,
      aplicadas,
      entrevistas,
      propostas,
      contratados,
      totalAplicadasOuMais,
      taxaEntrevista,
      taxaProposta,
      mediaAderencia,
      topPlataformas,
      topSkills,
    }
  }, [vagas])

  return (
    <div className="space-y-6">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold">Total Rastreadas</span>
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            {metrics.total}
          </div>
          <p className="text-xs text-slate-400">
            Em todas as plataformas configuradas
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold">
              Conversão para Entrevista
            </span>
            <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-purple-600 dark:text-purple-400">
            {metrics.taxaEntrevista}%
          </div>
          <p className="text-xs text-slate-400">
            {metrics.entrevistas} processos em fase de entrevistas
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold">
              Média de Aderência (IA)
            </span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {metrics.mediaAderencia}%
          </div>
          <p className="text-xs text-slate-400">
            Compatibilidade com seu perfil e competências
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold">Ofertas & Propostas</span>
            <div className="p-2 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-teal-600 dark:text-teal-400">
            {metrics.propostas + metrics.contratados}
          </div>
          <p className="text-xs text-slate-400">
            {metrics.contratados > 0
              ? `${metrics.contratados} contratado!`
              : "Na fase final de decisão"}
          </p>
        </div>
      </div>

      {/* Funnel Visual Pipeline */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-base text-slate-900 dark:text-white">
              Funil de Conversão de Candidaturas
            </h3>
            <p className="text-xs text-slate-500">
              Acompanhe a passagem de vagas desde a descoberta até a contratação
              final
            </p>
          </div>
        </div>

        {/* Pipeline Bar Step Chart */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          {[
            {
              label: "1. Descobertas",
              val: metrics.total,
              bg: "bg-slate-100 dark:bg-slate-800",
              text: "text-slate-700 dark:text-slate-300",
            },
            {
              label: "2. Salvas no Quadro",
              val: metrics.salvas,
              bg: "bg-slate-200 dark:bg-slate-700",
              text: "text-slate-800 dark:text-slate-200",
            },
            {
              label: "3. Aplicações",
              val: metrics.aplicadas,
              bg: "bg-blue-100 dark:bg-blue-950",
              text: "text-blue-700 dark:text-blue-300",
            },
            {
              label: "4. Entrevistas",
              val: metrics.entrevistas,
              bg: "bg-purple-100 dark:bg-purple-950",
              text: "text-purple-700 dark:text-purple-300",
            },
            {
              label: "5. Propostas",
              val: metrics.propostas,
              bg: "bg-emerald-100 dark:bg-emerald-950",
              text: "text-emerald-700 dark:text-emerald-300",
            },
            {
              label: "6. Contratado",
              val: metrics.contratados,
              bg: "bg-teal-100 dark:bg-teal-950",
              text: "text-teal-700 dark:text-teal-300",
            },
          ].map((step, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border border-slate-200 dark:border-slate-700/60 flex flex-col justify-between ${step.bg}`}
            >
              <span className="text-xs font-semibold text-slate-500">
                {step.label}
              </span>
              <div className={`text-2xl font-black mt-2 ${step.text}`}>
                {step.val}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two columns: Platforms distribution & In-demand skills */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Platforms */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-3">
          <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <PieChart className="w-4 h-4 text-indigo-500" />
            <span>Distribuição por Plataforma</span>
          </h4>
          <div className="space-y-2 pt-1">
            {metrics.topPlataformas.map(([plat, count]) => {
              const pct =
                metrics.total > 0
                  ? Math.round((count / metrics.total) * 100)
                  : 0
              return (
                <div key={plat} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                    <span>{plat}</span>
                    <span>
                      {count} vagas ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Skills in Demand */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-3">
          <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-500" />
            <span>Habilidades Mais Valorizadas nas Vagas</span>
          </h4>
          <p className="text-xs text-slate-400">
            Requisitos mais recorrentes detectados pela análise de inteligência
            artificial
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            {metrics.topSkills.map(([skill, count]) => (
              <span
                key={skill}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
              >
                <span>{skill}</span>
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 font-bold">
                  {count}x
                </span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
