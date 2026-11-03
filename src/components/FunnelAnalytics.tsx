import React, { useMemo } from "react"
import { TrendingUp, Award, PieChart, Briefcase, Sparkles } from "lucide-react"
import type { Vaga } from "../types/api"
import { useRequisitos, widgetsRequisitos } from "./RequisitosVagas"
import PainelWidgets from "./painel/PainelWidgets"
import type { WidgetDef } from "./painel/layout"

interface FunnelAnalyticsProps {
  vagas: Vaga[]
  onNavigateToTab?: (tab: string) => void
  /** Versão do banco: muda a cada gravação, e a seção O que as vagas pedem refaz o resumo (spec 045). */
  versao?: number
  onSelectVaga?: (v: Vaga) => void
  onAbrirIA?: () => void
  onAbrirPerfil?: () => void
}

export default function FunnelAnalytics({ vagas, versao, onSelectVaga, onAbrirIA, onAbrirPerfil }: FunnelAnalyticsProps) {
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
    }
  }, [vagas])

  const requisitos = useRequisitos({ vagas, versao })

  const numero = (
    id: string,
    titulo: string,
    Icone: typeof Briefcase,
    corIcone: string,
    corValor: string,
    valor: React.ReactNode,
    nota: string,
  ): WidgetDef => ({
    id,
    titulo,
    tipo: "numero",
    icone: <Icone className="w-4 h-4" />,
    corIcone,
    corpo: (
      <>
        {/* O tamanho do número segue a largura do widget, não a da janela (spec 046). */}
        <div className={`text-2xl @[10rem]:text-3xl font-extrabold ${corValor}`}>{valor}</div>
        <p className="text-xs text-slate-400">{nota}</p>
      </>
    ),
  })

  const widgets: WidgetDef[] = [
    numero(
      "total",
      "Total Rastreadas",
      Briefcase,
      "bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400",
      "text-slate-900 dark:text-white",
      metrics.total,
      "Em todas as plataformas configuradas",
    ),
    numero(
      "conversao",
      "Conversão para Entrevista",
      TrendingUp,
      "bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400",
      "text-purple-600 dark:text-purple-400",
      `${metrics.taxaEntrevista}%`,
      `${metrics.entrevistas} processos em fase de entrevistas`,
    ),
    numero(
      "aderencia",
      "Média de Aderência (IA)",
      Sparkles,
      "bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400",
      "text-emerald-600 dark:text-emerald-400",
      `${metrics.mediaAderencia}%`,
      "Compatibilidade com seu perfil e competências",
    ),
    numero(
      "ofertas",
      "Ofertas & Propostas",
      Award,
      "bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400",
      "text-teal-600 dark:text-teal-400",
      metrics.propostas + metrics.contratados,
      metrics.contratados > 0 ? `${metrics.contratados} contratado!` : "Na fase final de decisão",
    ),
    {
      id: "funil",
      titulo: "Funil de Conversão de Candidaturas",
      tipo: "secao",
      subtitulo: "Acompanhe a passagem de vagas desde a descoberta até a contratação final",
      corpo: (
        // As etapas se arranjam em 2, 3 ou 6 colunas pela largura do widget (spec 046).
        <div className="grid grid-cols-2 @md:grid-cols-3 @4xl:grid-cols-6 gap-3 pt-3">
          {[
            {
              label: "1. Descobertas",
              val: metrics.total,
              bg: "bg-slate-100 dark:bg-slate-800",
              text: "text-slate-700 dark:text-slate-300",
            },
            {
              label: "2. Salvas em Aplicações",
              val: metrics.salvas,
              bg: "bg-slate-200 dark:bg-slate-700",
              text: "text-slate-800 dark:text-slate-200",
            },
            {
              label: "3. Aplicações enviadas",
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
              className={`p-4 rounded-xl border border-slate-200 dark:border-slate-700/60 flex flex-col justify-between min-w-0 ${step.bg}`}
            >
              <span className="text-xs font-semibold text-slate-500 break-words">{step.label}</span>
              <div className={`text-2xl font-black mt-2 ${step.text}`}>{step.val}</div>
            </div>
          ))}
        </div>
      ),
    },
    // O que as vagas pedem (spec 045): a barra e os nove blocos, cada um um widget (spec 046)
    ...widgetsRequisitos(requisitos, { onSelectVaga, onAbrirIA, onAbrirPerfil }),
    {
      id: "plataformas",
      titulo: "Distribuição por Plataforma",
      tipo: "bloco",
      icone: <PieChart className="w-4 h-4 shrink-0 text-indigo-500" />,
      corpo: (
        <div className="space-y-2 pt-1">
          {metrics.topPlataformas.map(([plat, count]) => {
            const pct = metrics.total > 0 ? Math.round((count / metrics.total) * 100) : 0
            return (
              <div key={plat} className="space-y-1">
                <div className="flex items-center justify-between gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <span className="min-w-0 break-words">{plat}</span>
                  <span className="whitespace-nowrap">
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
      ),
    },
  ]

  return <PainelWidgets widgets={widgets} />
}
