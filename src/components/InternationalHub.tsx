import React, { useState, useMemo } from "react"
import {
  Globe2,
  DollarSign,
  Clock,
  ShieldCheck,
  Sparkles,
  ExternalLink,
  Search,
  Plane,
  Building,
  CheckCircle2,
  ArrowUpRight,
} from "lucide-react"
import type { Vaga, Etapa } from "../types/api"
import { CONTRATACAO } from "../utils/rotulos"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  formatarDataRelativa,
  formatarModelo,
  areaDe,
  paisDe,
  linkSeguro,
} from "../utils/formatters"
interface InternationalHubProps {
  vagas: Vaga[]
  onSelectVaga: (vaga: Vaga) => void
  onSeguirVaga: (id: string) => void
  onOpenFiltersModal: () => void
  /** Prontidão internacional (Meu perfil → Análises). */
  onAbrirProntidao: () => void
}

export default function InternationalHub({
  vagas,
  onSelectVaga,
  onSeguirVaga,
  onOpenFiltersModal,
  onAbrirProntidao,
}: InternationalHubProps) {
  const [filtroMoeda, setFiltroMoeda] = useState<string>("todas")
  const [somenteVisto, setSomenteVisto] = useState<boolean>(false)
  const [busca, setBusca] = useState<string>("")

  // Apenas vagas internacionais
  const vagasInternacionais = useMemo(() => {
    return vagas.filter((v) => {
      if (areaDe(v) !== "internacional") return false
      if (busca) {
        const q = busca.toLowerCase()
        const matchTitulo = v.titulo.toLowerCase().includes(q)
        const matchEmpresa = v.empresa.toLowerCase().includes(q)
        const matchLocal = (v.local || "").toLowerCase().includes(q)
        if (!matchTitulo && !matchEmpresa && !matchLocal) return false
      }
      if (
        filtroMoeda === "usd" &&
        !v.salario?.toLowerCase().includes("usd") &&
        !v.salario?.includes("$")
      ) {
        return false
      }
      if (
        filtroMoeda === "eur" &&
        !v.salario?.toLowerCase().includes("eur") &&
        !v.salario?.includes("€")
      ) {
        return false
      }
      if (somenteVisto) {
        const temSinalVisto = v.sinais?.some(
          (s) =>
            s.toLowerCase().includes("visto") ||
            s.toLowerCase().includes("relocation"),
        )
        if (!temSinalVisto) return false
      }
      return true
    })
  }, [vagas, busca, filtroMoeda, somenteVisto])

  // Estatísticas do Hub Internacional
  const stats = useMemo(() => {
    const total = vagasInternacionais.length
    const remotas = vagasInternacionais.filter((v) => v.remoto).length
    const comVisto = vagasInternacionais.filter((v) =>
      v.sinais?.some(
        (s) =>
          s.toLowerCase().includes("visto") ||
          s.toLowerCase().includes("relocation"),
      ),
    ).length
    return { total, remotas, comVisto }
  }, [vagasInternacionais])

  return (
    <div className="space-y-5">
      {/* Hero Banner for International Careers */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-teal-900 via-slate-900 to-indigo-950 p-6 sm:p-8 text-white border border-teal-800/40 shadow-lg">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-400/30">
            <Globe2 className="w-3.5 h-3.5" />
            <span>Carreiras Globais & Remotas em Moeda Forte</span>
          </div>
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight">
            Conquiste oportunidades remotas internacionais (USD / EUR)
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Vagas coletadas diretamente de quadros de empregos remotos globais
            (RemoteOK, Himalayas, Remotive, We Work Remotely) e portais ATS
            corporativos (Greenhouse, Lever, Ashby), sem necessidade de visto
            para posições Contractor/EOR.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-4 text-xs text-teal-200">
            <div className="flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
              <span>{stats.total} vagas ativas no radar</span>
            </div>
            <div className="flex items-center gap-1.5 font-medium">
              <Building className="w-3.5 h-3.5 text-teal-400" />
              <span>{stats.remotas} posições 100% remotas</span>
            </div>
            <div className="flex items-center gap-1.5 font-medium">
              <Plane className="w-3.5 h-3.5 text-teal-400" />
              <span>{stats.comVisto} com auxílio realocação / visto</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-2xs">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar vagas globais por cargo, empresa, país..."
              className="w-full pl-9 pr-4 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            />
          </div>

          {/* Currency and Visa Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Currency selector */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700 text-xs">
              <button
                onClick={() => setFiltroMoeda("todas")}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  filtroMoeda === "todas"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Todas Moedas
              </button>
              <button
                onClick={() => setFiltroMoeda("usd")}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  filtroMoeda === "usd"
                    ? "bg-white dark:bg-slate-700 text-teal-600 dark:text-teal-400 shadow-2xs font-bold"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Dólar ($ USD)
              </button>
              <button
                onClick={() => setFiltroMoeda("eur")}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  filtroMoeda === "eur"
                    ? "bg-white dark:bg-slate-700 text-teal-600 dark:text-teal-400 shadow-2xs font-bold"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Euro (€ EUR)
              </button>
            </div>

            {/* Visa / Relocation check */}
            <button
              onClick={() => setSomenteVisto(!somenteVisto)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                somenteVisto
                  ? "bg-teal-50 text-teal-700 border-teal-300 dark:bg-teal-950/60 dark:text-teal-300 dark:border-teal-800"
                  : "bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700 hover:bg-slate-100"
              }`}
            >
              <Plane className="w-3.5 h-3.5" />
              <span>Patrocínio de Visto / Relocation</span>
            </button>

            <button
              onClick={onOpenFiltersModal}
              className="px-3 py-1.5 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 transition"
            >
              Filtros da busca internacional
            </button>
            <button
              onClick={onAbrirProntidao}
              className="px-3 py-1.5 rounded-xl text-xs font-medium text-teal-700 dark:text-teal-300 bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 transition"
              title="O que já está pronto e o que falta para se candidatar a vagas de fora"
            >
              Prontidão internacional
            </button>
          </div>
        </div>
      </div>

      {/* International Job Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vagasInternacionais.map((vaga) => {
          const plat = getPlataformaStyle(vaga.plataforma)
          const ader = getAderenciaBadge(vaga.aderencia)

          return (
            <div
              key={vaga.id}
              className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-teal-300 dark:hover:border-teal-700 p-5 shadow-xs flex flex-col justify-between transition"
            >
              <div>
                {/* Badges: Platform + Country + Score */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`px-2 py-0.5 rounded-lg text-xs font-semibold border ${plat.bg} ${plat.text} ${plat.border}`}
                    >
                      {vaga.plataforma}
                    </span>
                    <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[11px] font-medium bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                      <Globe2 className="w-3 h-3" />
                      <span>{paisDe(vaga) || "Global"}</span>
                    </span>
                  </div>

                  {vaga.aderencia !== undefined && (
                    <span
                      className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${ader.bg} ${ader.text} ${ader.ring}`}
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>{vaga.aderencia}%</span>
                    </span>
                  )}
                </div>

                {/* Title & Company */}
                <h3
                  onClick={() => onSelectVaga(vaga)}
                  className="font-bold text-base text-slate-900 dark:text-white hover:text-teal-600 dark:hover:text-teal-400 cursor-pointer transition line-clamp-2"
                >
                  {vaga.titulo}
                </h3>
                <p className="text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-400 mt-0.5 mb-2">
                  {vaga.empresa}
                </p>

                {/* Salary Tag in Strong Currency */}
                {vaga.salario && (
                  <div className="flex items-center gap-1 text-xs font-bold text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/50 px-2.5 py-1 rounded-lg border border-teal-200 dark:border-teal-800 mb-3 w-fit">
                    <DollarSign className="w-3.5 h-3.5" />
                    <span>{vaga.salario}</span>
                  </div>
                )}

                {/* Modality & Timezone */}
                <div className="text-xs text-slate-500 space-y-1 mb-3">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{vaga.local}</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Contratação: {vaga.contratacao?.length ? vaga.contratacao.map((c) => CONTRATACAO[c.valor] || c.valor).join(", ") : "não informada"}
                  </div>
                </div>

                {/* Positive Signals (Visto, Relocation) */}
                {vaga.sinais && vaga.sinais.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {vaga.sinais.map((s, idx) => (
                      <span
                        key={idx}
                        className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                      >
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        <span>{s}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2 mt-2">
                <span className="text-[11px] text-slate-400">
                  {formatarDataRelativa(vaga.publicada_em)}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSeguirVaga(vaga.id)}
                    className="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 shadow-xs transition"
                    title="Mover vaga para o Quadro Kanban"
                  >
                    Seguir Vaga
                  </button>

                  <a
                    href={linkSeguro(vaga.url_candidatura || vaga.url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 transition"
                    title="Candidatar no portal da vaga"
                  >
                    <span>Aplicar</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {vagasInternacionais.length === 0 && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-3">
          <Globe2 className="w-8 h-8 text-slate-400 mx-auto" />
          <h4 className="font-semibold text-slate-800 dark:text-slate-200">
            Nenhuma vaga internacional encontrada com estes filtros
          </h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Ative mais fontes internacionais nas configurações de busca ou limpe
            os filtros de visto/moeda.
          </p>
        </div>
      )}
    </div>
  )
}
