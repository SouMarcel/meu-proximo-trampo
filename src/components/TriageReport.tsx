import React, { useState, useMemo } from "react"
import {
  Check,
  X,
  ExternalLink,
  Filter,
  SlidersHorizontal,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  MapPin,
  DollarSign,
  Calendar,
  RotateCcw,
  ShieldAlert,
  Search,
  ArrowUpDown,
  ChevronRight,
  Eye,
} from "lucide-react"
import { Vaga, Triagem, Senioridade, ModeloTrabalho, Etapa } from "../types/job"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  formatarDataRelativa,
  formatarModelo,
  formatarSenioridade,
} from "../utils/formatters"

interface TriageReportProps {
  vagas: Vaga[]
  onSelectVaga: (vaga: Vaga) => void
  onSeguirVaga: (id: string) => void
  onNaoSeguirVaga: (id: string) => void
  onResgatarVaga: (id: string) => void
  onForcarVerificar?: (id: string) => Promise<void> | void
}

type SubTab = "pendente" | "seguir" | "visitada" | "fora"
type OrdemFiltro = "aderencia" | "publicacao" | "plataforma" | "modo"

export default function TriageReport({
  vagas,
  onSelectVaga,
  onSeguirVaga,
  onNaoSeguirVaga,
  onResgatarVaga,
  onForcarVerificar,
}: TriageReportProps) {
  const [subTab, setSubTab] = useState<SubTab>("pendente")
  const [verificandoMap, setVerificandoMap] = useState<Record<string, boolean>>({})

  const handleForcar = async (id: string) => {
    if (!onForcarVerificar) return
    setVerificandoMap((prev) => ({ ...prev, [id]: true }))
    try {
      await onForcarVerificar(id)
    } finally {
      setVerificandoMap((prev) => ({ ...prev, [id]: false }))
    }
  }
  const [searchQuery, setSearchQuery] = useState("")
  const [ordem, setOrdem] = useState<OrdemFiltro>("aderencia")
  const [filtroSenioridade, setFiltroSenioridade] = useState<Senioridade | "">(
    "",
  )
  const [filtroModo, setFiltroModo] = useState<string>("")
  const [aderenciaMinima, setAderenciaMinima] = useState<number>(0)
  const [maxDias, setMaxDias] = useState<number>(30)

  // Contagens por aba de triagem
  const counts = useMemo(() => {
    const res = { pendente: 0, seguir: 0, visitada: 0, fora: 0 }
    vagas.forEach((v) => {
      if (v.triagem in res) {
        res[(v.triagem as SubTab)]++
      }
    })
    return res
  }, [vagas])

  // Filtragem e ordenação das vagas da aba ativa
  const filteredVagas = useMemo(() => {
    return vagas
      .filter((v) => {
        // Aba atual
        if (v.triagem !== subTab) return false

        // Busca textual
        if (searchQuery) {
          const q = searchQuery.toLowerCase()
          const matchTitulo = v.titulo.toLowerCase().includes(q)
          const matchEmpresa = v.empresa.toLowerCase().includes(q)
          const matchDesc = v.descricao?.toLowerCase().includes(q)
          const matchTermos = v.termos?.some((t) => t.toLowerCase().includes(q))
          if (!matchTitulo && !matchEmpresa && !matchDesc && !matchTermos)
            return false
        }

        // Senioridade
        if (
          filtroSenioridade &&
          v.senioridade &&
          !v.senioridade.includes(filtroSenioridade)
        ) {
          return false
        }

        // Modo
        if (filtroModo) {
          if (filtroModo === "remoto" && !v.remoto) return false
          if (filtroModo === "hibrido" && v.modelo_trabalho !== "hibrido")
            return false
          if (filtroModo === "presencial" && v.modelo_trabalho !== "presencial")
            return false
        }

        // Aderência mínima
        if (aderenciaMinima > 0) {
          if ((v.aderencia || 0) < aderenciaMinima) return false
        }

        return true
      })
      .sort((a, b) => {
        if (ordem === "aderencia") {
          return (b.aderencia || 0) - (a.aderencia || 0)
        }
        if (ordem === "publicacao") {
          return (
            new Date(b.publicada_em).getTime() -
            new Date(a.publicada_em).getTime()
          )
        }
        if (ordem === "plataforma") {
          return a.plataforma.localeCompare(b.plataforma)
        }
        if (ordem === "modo") {
          return (a.modelo_trabalho || "").localeCompare(
            b.modelo_trabalho || "",
          )
        }
        return 0
      })
  }, [
    vagas,
    subTab,
    searchQuery,
    filtroSenioridade,
    filtroModo,
    aderenciaMinima,
    ordem,
  ])

  return (
    <div className="space-y-4">
      {/* Sub-tabs header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-2 shadow-2xs">
        <div className="flex flex-wrap items-center gap-1 sm:gap-2">
          <button
            onClick={() => setSubTab("pendente")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
              subTab === "pendente"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <span>Para Decidir</span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                subTab === "pendente"
                  ? "bg-indigo-700 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              {counts.pendente}
            </span>
          </button>


          <button
            onClick={() => setSubTab("visitada")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
              subTab === "visitada"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <span>Não Seguidas (Arquivadas)</span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                subTab === "visitada"
                  ? "bg-indigo-700 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              {counts.visitada}
            </span>
          </button>

          <button
            onClick={() => setSubTab("fora")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
              subTab === "fora"
                ? "bg-rose-600 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Fora dos Critérios</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                subTab === "fora"
                  ? "bg-rose-700 text-white"
                  : "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
              }`}
            >
              {counts.fora}
            </span>
          </button>
        </div>
      </div>

      {/* Filter and Sorting Options Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-2xs space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search bar */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filtrar nesta lista por termo, empresa ou habilidades..."
              className="w-full pl-9 pr-4 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>

          {/* Sort selection */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 shrink-0">
              <ArrowUpDown className="w-3.5 h-3.5" />
              Ordenar:
            </span>
            <select
              value={ordem}
              onChange={(e) => setOrdem(e.target.value as OrdemFiltro)}
              className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value="aderencia">Maior Aderência</option>
              <option value="publicacao">Mais Recentes</option>
              <option value="plataforma">Por Plataforma</option>
              <option value="modo">Modo de Trabalho</option>
            </select>
          </div>
        </div>

        {/* Secondary filters row */}
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Seniority buttons */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-slate-500">Senioridade:</span>
            {(["", "junior", "pleno", "senior", "especialista"] as const).map(
              (sen) => (
                <button
                  key={sen}
                  onClick={() => setFiltroSenioridade(sen)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition ${
                    filtroSenioridade === sen
                      ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                      : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200"
                  }`}
                >
                  {sen === ""
                    ? "Todas"
                    : sen === "junior"
                      ? "Jr"
                      : sen === "pleno"
                        ? "Pl"
                        : sen === "senior"
                          ? "Sr"
                          : "Lead"}
                </button>
              ),
            )}
          </div>

          {/* Modality buttons */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-slate-500">Modo:</span>
            {(["", "remoto", "hibrido", "presencial"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setFiltroModo(m)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  filtroModo === m
                    ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                    : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200"
                }`}
              >
                {m === ""
                  ? "Todos"
                  : m === "remoto"
                    ? "Remoto"
                    : m === "hibrido"
                      ? "Híbrido"
                      : "Presencial"}
              </button>
            ))}
          </div>

          {/* Minimum adherence slider */}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-500">Nota Mínima:</span>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={aderenciaMinima}
              onChange={(e) => setAderenciaMinima(Number(e.target.value))}
              className="w-24 accent-indigo-600"
            />
            <span className="font-bold text-indigo-600 dark:text-indigo-400 w-7">
              {aderenciaMinima}%
            </span>
          </div>
        </div>
      </div>

      {/* Job Cards List */}
      <div className="space-y-3">
        {filteredVagas.map((vaga) => {
          const platStyle = getPlataformaStyle(vaga.plataforma)
          const aderBadge = getAderenciaBadge(vaga.aderencia)
          const isVerificando =
            Boolean(verificandoMap[vaga.id] || vaga.analise_status === "verificando")

          return (
            <div
              key={vaga.id}
              className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 sm:p-5 shadow-xs hover:border-indigo-200 dark:hover:border-indigo-800 transition"
            >
              <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                {/* Left Side: Aderência + Dados da Vaga */}
                <div className="flex items-start gap-3.5 sm:gap-4 flex-1 min-w-0">
                  {/* Coluna propria de aderencia e nivel na extrema esquerda do card */}
                  <div className="shrink-0 pt-0.5">
                    {vaga.aderencia !== undefined ? (
                      <div
                        className={`w-[74px] h-[74px] sm:w-[82px] sm:h-[82px] rounded-2xl bg-slate-900 dark:bg-slate-950 border ${aderBadge.boxBorder} ${aderBadge.boxGlow} shadow-xs flex flex-col items-center justify-center p-2 text-center select-none transition-transform hover:scale-105`}
                        title={`Aderência de ${vaga.aderencia}% (${aderBadge.label})`}
                      >
                        <span
                          className={`text-2xl sm:text-3xl font-extrabold leading-none tracking-tight ${aderBadge.scoreColor}`}
                        >
                          {vaga.aderencia}
                        </span>
                        <span className="text-[10px] sm:text-[11px] font-bold tracking-wider text-slate-400 uppercase mt-1 leading-none">
                          {aderBadge.label}
                        </span>
                      </div>
                    ) : (
                      <div
                        className={`w-[74px] h-[74px] sm:w-[82px] sm:h-[82px] rounded-2xl bg-slate-900 dark:bg-slate-950 border ${
                          isVerificando
                            ? "border-indigo-500/60 shadow-xs shadow-indigo-500/10"
                            : "border-slate-800"
                        } flex flex-col items-center justify-center p-2 text-center select-none shrink-0`}
                        title={
                          isVerificando
                            ? "IA calculando a aderência desta vaga..."
                            : "Vaga sem nota de aderência calculada"
                        }
                      >
                        {isVerificando ? (
                          <>
                            <Sparkles className="w-5 h-5 text-indigo-400 animate-spin" />
                            <span className="text-[9px] sm:text-[10px] font-bold tracking-wider text-indigo-300 uppercase mt-1 leading-none">
                              Análise
                            </span>
                          </>
                        ) : (
                          <>
                            <span className="text-xl sm:text-2xl font-bold leading-none text-slate-500">
                              —
                            </span>
                            <span className="text-[9px] sm:text-[10px] font-bold tracking-wider text-slate-500 uppercase mt-1 leading-none">
                              Sem nota
                            </span>
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Main Job Info & Match Analysis */}
                  <div className="space-y-3 flex-1 min-w-0">
                  {/* Top tags: Platform, Seniority, Modality, Search term */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}
                    >
                      {vaga.plataforma}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      {formatarModelo(vaga.modelo_trabalho, vaga.remoto)}
                    </span>
                    <span className="text-slate-300 dark:text-slate-700">
                      ·
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      {formatarSenioridade(vaga.senioridade)}
                    </span>
                    <span className="text-slate-300 dark:text-slate-700">
                      ·
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatarDataRelativa(vaga.publicada_em)}
                    </span>
                    {vaga.termos && vaga.termos.length > 0 && (
                      <span className="px-2 py-0.5 rounded-md text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono">
                        termo: {vaga.termos[0]}
                      </span>
                    )}
                    {vaga.descricao_pendente && (
                      <span className="px-2 py-0.5 rounded-md text-[11px] bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 font-medium">
                        Descrição pendente
                      </span>
                    )}
                  </div>

                  {/* Title & Company */}
                  <div>
                    <h3
                      onClick={() => onSelectVaga(vaga)}
                      className="text-base sm:text-lg font-bold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer transition"
                    >
                      {vaga.titulo}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {vaga.empresa}
                      </span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {vaga.local}
                      </span>
                      {vaga.salario && (
                        <>
                          <span>·</span>
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                            {vaga.salario}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Disqualification Reason if in "Fora dos Critérios" */}
                  {subTab === "fora" &&
                    vaga.motivo_fora &&
                    vaga.motivo_fora.length > 0 && (
                      <div className="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 rounded-xl p-3 text-xs text-rose-800 dark:text-rose-300 space-y-1">
                        <div className="font-semibold flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4 text-rose-600" />
                          <span>
                            Motivos da desqualificação automática pelos filtros:
                          </span>
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 pl-1 text-rose-700 dark:text-rose-300">
                          {vaga.motivo_fora.map((motivo, idx) => (
                            <li key={idx}>{motivo}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {/* AI Match Overview */}
                  {vaga.resumo && (
                    <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-100 dark:border-slate-800 space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-700 dark:text-indigo-400">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Análise de Compatibilidade do Claude</span>
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {vaga.resumo}
                      </p>

                      {/* Encaixe & Lacunas Tags */}
                      <div className="flex flex-wrap gap-2 pt-1">
                        {vaga.encaixe &&
                          vaga.encaixe.slice(0, 2).map((item, idx) => (
                            <span
                              key={idx}
                              className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                            >
                              <Check className="w-3 h-3 text-emerald-600 shrink-0" />
                              <span>{item}</span>
                            </span>
                          ))}

                        {vaga.lacunas &&
                          vaga.lacunas.slice(0, 1).map((item, idx) => (
                            <span
                              key={idx}
                              className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                            >
                              <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                              <span>Atenção: {item}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
                </div>

                {/* Right Action Column: Triage Buttons */}
                <div className="flex flex-col items-stretch sm:items-end gap-2 shrink-0 w-full lg:w-auto pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100 dark:border-slate-800">
                  {/* Action Buttons */}
                  <div className="flex flex-col items-stretch sm:items-end gap-2 w-full sm:w-auto">
                    {subTab === "pendente" && (
                      <>
                        {/* 1. Não Seguir */}
                        <button
                          onClick={() => onNaoSeguirVaga(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition w-full sm:w-auto"
                          title="Descartar vaga (não aparecerá nas próximas buscas)"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Não Seguir</span>
                        </button>

                        {/* 2. Seguir com a Vaga */}
                        <button
                          onClick={() => onSeguirVaga(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-xs shadow-indigo-600/30 transition w-full sm:w-auto"
                          title="Mover para a coluna Salva no seu Quadro"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Seguir com a Vaga</span>
                        </button>
                      </>
                    )}

                    {/* 3. Forçar verificar (Spec 021) */}
                    {vaga.aderencia === undefined && onForcarVerificar && (
                      <div className="flex flex-col items-stretch sm:items-end gap-1 w-full sm:w-auto">
                        <button
                          onClick={() => handleForcar(vaga.id)}
                          disabled={isVerificando}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900 border border-indigo-200 dark:border-indigo-800 disabled:opacity-60 transition shadow-2xs w-full sm:w-auto"
                          title="Pede a nota desta vaga à IA agora"
                        >
                          <Sparkles
                            className={`w-3.5 h-3.5 ${
                              isVerificando
                                ? "animate-spin text-indigo-500"
                                : "text-indigo-600 dark:text-indigo-400"
                            }`}
                          />
                          <span>
                            {isVerificando
                              ? "Verificando…"
                              : "Forçar verificar"}
                          </span>
                        </button>
                        {(isVerificando) && (
                          <span className="text-[10px] text-slate-500 dark:text-slate-400 text-center sm:text-right">
                            A nota chega em alguns instantes.
                          </span>
                        )}
                        {vaga.descricao_pendente && !isVerificando && (
                          <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium text-center sm:text-right">
                            Lê descrição antes da IA
                          </span>
                        )}
                        {vaga.motivo_falha && !isVerificando && (
                          <span className="text-[10px] text-rose-600 dark:text-rose-400 text-center sm:text-right">
                            Falha: {vaga.motivo_falha}
                          </span>
                        )}
                      </div>
                    )}

                    {subTab === "fora" && (
                      <button
                        onClick={() => onResgatarVaga(vaga.id)}
                        className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-emerald-800 dark:text-emerald-200 bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-950/80 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-800 transition w-full sm:w-auto"
                        title="Resgatar vaga e mover diretamente para o Quadro"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Resgatar Vaga</span>
                      </button>
                    )}

                    {/* 4. Ver detalhes completos / Acessar a vaga na plataforma original */}
                    <div className="flex items-center justify-end gap-1.5 pt-0.5 w-full">
                      <a
                        href={vaga.url_candidatura || vaga.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 transition border border-transparent hover:border-indigo-200 dark:border-indigo-800"
                        title="Abrir vaga no portal original"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span className="text-[11px] font-medium">Acessar vaga</span>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {filteredVagas.length === 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-800 dark:text-slate-200">
              Nenhuma vaga nesta seção
            </h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {subTab === "pendente"
                ? "Tudo em dia! Você já tomou decisão sobre todas as vagas encontradas pela busca."
                : "Não há registros com estes filtros no momento."}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
