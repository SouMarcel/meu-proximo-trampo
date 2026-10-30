import React, { useState, useMemo, useEffect } from "react"
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
import type { Vaga, Senioridade, Versao } from "../types/api"
import { useFerramenta, AvisoSoLeitura } from "../contexto/Ferramenta"
import { ScreenPreferencesService } from "../services/storage"
import { SeloIntegridade } from "./Integridade"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  formatarDataRelativa,
  formatarModelo,
  formatarSenioridade,
  modoDe,
  situacaoNota,
  podeForcar,
  linkSeguro,
  temNota,
  diaMes,
  semAcento,
} from "../utils/formatters"

interface TriageReportProps {
  vagas: Vaga[]
  versao: Versao | null
  /** Vagas em que o Forçar verificar voltou "ligue uma IA". */
  semIA: Record<string, boolean>
  onSelectVaga: (vaga: Vaga) => void
  onSeguirVaga: (id: string) => void
  onNaoSeguirVaga: (id: string) => void
  onVoltarTriagem: (id: string) => void
  onMarcarTodasNaoSeguidas: (ids: string[]) => Promise<void>
  onForcarVerificar?: (id: string) => Promise<void> | void
  onAbrirIA: () => void
}

type SubTab = "pendente" | "seguir" | "visitada" | "fora"

/** Níveis da vaga: os da análise; sem análise, os que o título diz (a mesma leitura do dashboard antigo). */
function niveisDa(v: Vaga): string[] {
  if (Array.isArray(v.senioridade)) return v.senioridade
  let t = " " + semAcento(v.titulo || "").replace(/[^a-z0-9]+/g, " ") + " "
  t = t.replace(/ semi ?(senior|sr) /g, " ssr ") // "Semi Senior" (espanhol) é pleno
  const r: string[] = []
  if (/ (jr|junior|entry level) /.test(t)) r.push("junior")
  if (/ (pl(?! sql )|pleno|mid|intermediate|intermediario|intermediaria|ssr|ii) /.test(t)) r.push("pleno")
  if (/ (sr|snr|senior|iii|principal) /.test(t)) r.push("senior")
  return r
}

/** Modo para o filtro: o da análise; sem ele, a marcação do portal; senão "ni" (não informado). */
function modoFiltro(v: Vaga): string {
  if (v.modelo_trabalho === "remoto" || v.modelo_trabalho === "hibrido" || v.modelo_trabalho === "presencial") return v.modelo_trabalho
  if (v.modelo_trabalho === "nao_informado") return "ni"
  return v.remoto === true ? "remoto" : "ni"
}

/** Dias desde a publicação, ou null sem data. */
function diasDesde(iso?: string | null): number | null {
  if (!iso) return null
  const t = Date.parse(String(iso).slice(0, 10) + "T12:00:00")
  return isNaN(t) ? null : Math.max(0, Math.round((Date.now() - t) / 86400000))
}

/** "Marcar todas como não seguidas", com o segundo clique para confirmar. */
function BotaoMarcarTodas({
  ids,
  rotulo,
  podeGravar,
  onMarcar,
}: {
  ids: string[]
  rotulo: string
  podeGravar: boolean
  onMarcar: (ids: string[]) => Promise<void>
}) {
  const [confirmar, setConfirmar] = useState(false)
  const [marcando, setMarcando] = useState(false)
  return (
    <span className="flex items-center gap-2">
      {confirmar && (
        <button
          type="button"
          onClick={() => setConfirmar(false)}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          Cancelar
        </button>
      )}
      <button
        type="button"
        disabled={!podeGravar || marcando || !ids.length}
        onClick={async () => {
          if (!confirmar) return setConfirmar(true)
          setMarcando(true)
          try {
            await onMarcar(ids)
          } finally {
            setMarcando(false)
            setConfirmar(false)
          }
        }}
        className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition disabled:opacity-50 ${
          confirmar
            ? "bg-rose-600 hover:bg-rose-500 text-white border-rose-600"
            : "text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800"
        }`}
        title="Marca estas vagas como não seguidas"
      >
        {marcando ? "Marcando…" : confirmar ? `Confirmar: marcar todas (${ids.length})` : rotulo}
      </button>
    </span>
  )
}
type OrdemFiltro = "aderencia" | "publicacao" | "plataforma" | "modo"

export default function TriageReport({
  vagas,
  versao,
  semIA,
  onSelectVaga,
  onSeguirVaga,
  onNaoSeguirVaga,
  onVoltarTriagem,
  onMarcarTodasNaoSeguidas,
  onForcarVerificar,
  onAbrirIA,
}: TriageReportProps) {
  const { podeGravar } = useFerramenta()
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
  const prefs = useMemo(() => ScreenPreferencesService.getTriagePreferences(), [])
  const [ordem, setOrdem] = useState<OrdemFiltro>(
    (["aderencia", "publicacao", "plataforma", "modo"] as string[]).includes(String(prefs.triageOrdem))
      ? (prefs.triageOrdem as OrdemFiltro)
      : "aderencia",
  )
  const [niveis, setNiveis] = useState<string[]>(Array.isArray(prefs.niveis) ? prefs.niveis : [])
  const [modos, setModos] = useState<string[]>(Array.isArray(prefs.modos) ? prefs.modos : [])
  const [aderMin, setAderMin] = useState<number | null>(typeof prefs.ader === "number" ? prefs.ader : null)
  const [diasMax, setDiasMax] = useState<number | null>(typeof prefs.dias === "number" ? prefs.dias : null)
  // Analisadas (spec 038): marcada, as vagas ainda sem nota somem de todas as abas (a nota provisória conta como nota)
  const [soAnalisadas, setSoAnalisadas] = useState(prefs.analisadas === true)
  const [baixasAbertas, setBaixasAbertas] = useState(false)

  useEffect(() => {
    ScreenPreferencesService.saveTriagePreferences({ triageOrdem: ordem, niveis, modos, ader: aderMin, dias: diasMax, analisadas: soAnalisadas })
  }, [ordem, niveis, modos, aderMin, diasMax, soAnalisadas])

  const filtrando = niveis.length > 0 || modos.length > 0 || aderMin != null || diasMax != null || Boolean(searchQuery) || soAnalisadas
  const limparFiltros = () => {
    setNiveis([])
    setModos([])
    setAderMin(null)
    setDiasMax(null)
    setSearchQuery("")
    setSoAnalisadas(false)
  }
  const alternar = (lista: string[], k: string) => (lista.includes(k) ? lista.filter((x) => x !== k) : [...lista, k])

  // Com Analisadas marcada, os números das abas e o Marcar todas contam só as vagas com nota (spec 038)
  const visivel = (v: Vaga) => !soAnalisadas || temNota(v)

  // Contagens por aba de triagem
  const counts = useMemo(() => {
    const res = { pendente: 0, seguir: 0, visitada: 0, fora: 0 }
    vagas.forEach((v) => {
      if (v.triagem in res && (!soAnalisadas || temNota(v))) {
        res[(v.triagem as SubTab)]++
      }
    })
    return res
  }, [vagas, soAnalisadas])

  // Filtragem e ordem da aba ativa (as regras do dashboard antigo; "ni" = não informado)
  const naAba = useMemo(() => vagas.filter((v) => v.triagem === subTab), [vagas, subTab])
  const daTriagem = useMemo(() => (soAnalisadas ? naAba.filter(temNota) : naAba), [naAba, soAnalisadas])
  const ocultas = naAba.length - daTriagem.length
  const lista = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    const nota = (v: Vaga) => (temNota(v) ? (v.aderencia as number) : -1)
    const recente = (a: Vaga, b: Vaga) => String(b.publicada_em || "").localeCompare(String(a.publicada_em || ""))
    const ordemModo = ["remoto", "hibrido", "presencial", "ni"]
    const criterio: Record<OrdemFiltro, (a: Vaga, b: Vaga) => number> = {
      aderencia: () => 0,
      publicacao: recente,
      plataforma: (a, b) => {
        const pa = a.plataforma || "Outra"
        const pb = b.plataforma || "Outra"
        return Number(pa === "Outra") - Number(pb === "Outra") || pa.localeCompare(pb, "pt-BR")
      },
      modo: (a, b) => ordemModo.indexOf(modoFiltro(a)) - ordemModo.indexOf(modoFiltro(b)),
    }
    return daTriagem
      .filter((v) => {
        if (q) {
          const achou =
            v.titulo.toLowerCase().includes(q) ||
            v.empresa.toLowerCase().includes(q) ||
            Boolean(v.descricao?.toLowerCase().includes(q)) ||
            Boolean(v.termos?.some((t) => t.toLowerCase().includes(q)))
          if (!achou) return false
        }
        // vaga ainda sem nota (aguardando a IA, descrição pendente, falha): os outros filtros dependem da análise ou
        // a escondiam sem aviso; ela aparece sempre, salvo com Analisadas marcada (spec 038)
        if (!temNota(v)) return true
        if (niveis.length) {
          const nv = niveisDa(v)
          if (!(nv.length ? nv.some((x) => niveis.includes(x)) : niveis.includes("ni"))) return false
        }
        if (modos.length && !modos.includes(modoFiltro(v))) return false
        if (aderMin != null && !(temNota(v) && (v.aderencia as number) >= aderMin)) return false
        if (diasMax != null) {
          const d = diasDesde(v.publicada_em)
          if (d == null || d > diasMax) return false
        }
        return true
      })
      .sort((a, b) => criterio[ordem](a, b) || nota(b) - nota(a) || recente(a, b))
  }, [daTriagem, searchQuery, niveis, modos, aderMin, diasMax, ordem])

  // Em Para decidir, as de nota abaixo de 50 ficam recolhidas, como no dashboard antigo
  const baixas = subTab === "pendente" ? lista.filter((v) => temNota(v) && (v.aderencia as number) < 50) : []
  const principais = subTab === "pendente" ? lista.filter((v) => !(temNota(v) && (v.aderencia as number) < 50)) : lista

  const cartao = (vaga: Vaga) => {
          const platStyle = getPlataformaStyle(vaga.plataforma)
          const aderBadge = getAderenciaBadge(vaga.aderencia)
          const nota = situacaoNota(vaga, versao)
          const isVerificando = Boolean(verificandoMap[vaga.id] || nota.tipo === "verificando")
          const linkVaga = linkSeguro(vaga.url)

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
                    {temNota(vaga) ? (
                      <div
                        className={`w-[74px] h-[74px] sm:w-[82px] sm:h-[82px] rounded-2xl bg-slate-900 dark:bg-slate-950 border ${aderBadge.boxBorder} ${aderBadge.boxGlow} shadow-xs flex flex-col items-center justify-center p-2 text-center select-none transition-transform hover:scale-105`}
                        title={
                          vaga.nota_sem_descricao
                            ? "Nota provisória, sem a descrição da vaga"
                            : `Aderência ao seu perfil: ${vaga.aderencia} de 100 (${aderBadge.label})`
                        }
                      >
                        <span
                          className={`text-2xl sm:text-3xl font-extrabold leading-none tracking-tight ${aderBadge.scoreColor}`}
                        >
                          {vaga.aderencia}
                        </span>
                        <span className="text-[10px] sm:text-[11px] font-bold tracking-wider text-slate-400 uppercase mt-1 leading-none">
                          {vaga.nota_sem_descricao ? "provisória" : aderBadge.label}
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
                            <span className="text-[9px] sm:text-[10px] font-bold tracking-wider text-slate-500 uppercase mt-1 leading-tight">
                              {nota.tipo === "descricao_pendente"
                                ? "descrição pendente"
                                : nota.tipo === "pendente"
                                  ? "aguardando"
                                  : "sem nota"}
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
                      {vaga.senioridade_origem === "sugerida" && vaga.senioridade?.length ? " (sugerida)" : ""}
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
                    {vaga.formato === "post" && (
                      <span className="px-2 py-0.5 rounded-md text-[11px] bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 font-medium">
                        Post
                      </span>
                    )}
                    {vaga.origem === "link" && !vaga.termos?.length && (
                      <span className="text-[11px] text-slate-400">adicionada pelo link</span>
                    )}
                    {vaga.descricao_pendente && (
                      <span className="px-2 py-0.5 rounded-md text-[11px] bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 font-medium">
                        Descrição pendente
                      </span>
                    )}
                  </div>

                  {/* Title & Company */}
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3
                        onClick={() => onSelectVaga(vaga)}
                        className="text-base sm:text-lg font-bold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer transition"
                        title="Ver descrição, análise e anotações"
                      >
                        {vaga.titulo}
                      </h3>
                      <SeloIntegridade vaga={vaga} />
                      {linkVaga && (
                        <a
                          href={linkVaga}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-medium text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 border border-slate-200 dark:border-slate-700 hover:border-indigo-200 dark:hover:border-indigo-800 transition shrink-0"
                          title="Abrir vaga no portal original"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Abrir a vaga</span>
                        </a>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {vaga.empresa}
                      </span>
                      <span>·</span>
                      {vaga.local && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {vaga.local}
                        </span>
                      )}
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
                            Fora dos critérios:
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
                        <span>Análise da IA</span>
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
                          vaga.lacunas.slice(0, 2).map((item, idx) => (
                            <span
                              key={idx}
                              className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                            >
                              <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                              <span>Lacuna: {item}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
                </div>

                {/* Right Action Column: Triage Buttons */}
                <div className="flex flex-col items-stretch sm:items-end justify-center gap-2 shrink-0 w-full lg:w-auto lg:self-center pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100 dark:border-slate-800">
                  {/* Action Buttons */}
                  <div className="flex flex-col items-stretch sm:items-end gap-2 w-full sm:w-auto">
                    {subTab === "pendente" && (
                      <>
                        {/* 1. Não Seguir */}
                        <button
                          disabled={!podeGravar}
                          onClick={() => onNaoSeguirVaga(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition w-full sm:w-auto"
                          title="Marca como não seguida (a busca não traz de novo)"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Não seguir</span>
                        </button>

                        {/* 2. Seguir com a Vaga */}
                        <button
                          disabled={!podeGravar}
                          onClick={() => onSeguirVaga(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-xs shadow-indigo-600/30 transition w-full sm:w-auto"
                          title="Mover para a coluna Salva no seu Quadro"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Seguir com a vaga</span>
                        </button>
                      </>
                    )}

                    {/* 3. Forçar verificar (Spec 021) */}
                    {podeForcar(vaga) && onForcarVerificar && (
                      <div className="flex flex-col items-stretch sm:items-end gap-1 w-full sm:w-auto">
                        <button
                          onClick={() => handleForcar(vaga.id)}
                          disabled={isVerificando || !podeGravar}
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
                            A nota chega em alguns minutos.
                          </span>
                        )}
                        {vaga.descricao_pendente && !isVerificando && (
                          <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium text-center sm:text-right">
                            Lê descrição antes da IA
                          </span>
                        )}
                        {semIA[vaga.id] && !isVerificando && (
                          <span className="text-[10px] text-slate-600 dark:text-slate-400 text-center sm:text-right">
                            Para dar nota, ligue uma IA.{" "}
                            <button onClick={onAbrirIA} className="underline font-semibold">
                              IA
                            </button>
                          </span>
                        )}
                        {nota.tipo === "falha" && !semIA[vaga.id] && !isVerificando && (
                          <span className="text-[10px] text-rose-600 dark:text-rose-400 text-center sm:text-right">
                            Não deu para verificar: {nota.motivo}
                          </span>
                        )}
                      </div>
                    )}

                    {subTab === "fora" && (
                      <>
                        {vaga.triada_em && (
                          <span className="text-[11px] text-slate-500 text-center sm:text-right">
                            Fora dos critérios desde {diaMes(vaga.triada_em)}
                          </span>
                        )}
                        <button
                          disabled={!podeGravar}
                          onClick={() => onSeguirVaga(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-emerald-800 dark:text-emerald-200 bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-950/80 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-800 transition w-full sm:w-auto disabled:opacity-50"
                          title="Seguir com a vaga mesmo fora dos critérios: vai para a coluna Salva do quadro"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Seguir com a vaga</span>
                        </button>
                      </>
                    )}

                    {subTab === "visitada" && (
                      <>
                        {vaga.triada_em && (
                          <span className="text-[11px] text-slate-500 text-center sm:text-right">
                            Marcada como não seguida em {diaMes(vaga.triada_em)}
                          </span>
                        )}
                        <button
                          disabled={!podeGravar}
                          onClick={() => onVoltarTriagem(vaga.id)}
                          className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition w-full sm:w-auto disabled:opacity-50"
                          title="Devolve a vaga para Para decidir"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Voltar para triagem</span>
                        </button>
                      </>
                    )}

                  </div>
                </div>
              </div>
            </div>
          )
        }

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
            <span>Para decidir</span>
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
            <span>Não seguidas</span>
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
              <span>Fora dos critérios</span>
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
          {/* Senioridade (várias) */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-slate-500">Senioridade:</span>
            {(
              [
                ["junior", "Jr", "Júnior"],
                ["pleno", "Pl", "Pleno"],
                ["senior", "Sr", "Sênior"],
                ["ni", "Não informada", "Vagas que não dizem o nível"],
              ] as const
            ).map(([k, rotulo, dica]) => (
              <button
                key={k}
                type="button"
                aria-pressed={niveis.includes(k)}
                title={dica}
                onClick={() => setNiveis((l) => alternar(l, k))}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  niveis.includes(k)
                    ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                    : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200"
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>

          {/* Modo (vários) */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-slate-500">Modo:</span>
            {(
              [
                ["remoto", "Remoto"],
                ["hibrido", "Híbrido"],
                ["presencial", "Presencial"],
                ["ni", "Não informado"],
              ] as const
            ).map(([k, rotulo]) => (
              <button
                key={k}
                type="button"
                aria-pressed={modos.includes(k)}
                onClick={() => setModos((l) => alternar(l, k))}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  modos.includes(k)
                    ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                    : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200"
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>

          {/* Nota mínima e dias desde a publicação */}
          <div className="flex items-center gap-3 flex-wrap">
            <label className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500">Nota mínima:</span>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                max={100}
                step={5}
                placeholder="0"
                value={aderMin ?? ""}
                onChange={(e) => {
                  const n = parseInt(e.target.value, 10)
                  setAderMin(isNaN(n) || n < 1 ? null : Math.min(100, n))
                }}
                className="w-16 px-2 py-1 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </label>
            <label className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500">Publicada há até:</span>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                max={365}
                placeholder="todas"
                value={diasMax ?? ""}
                onChange={(e) => {
                  const n = parseInt(e.target.value, 10)
                  setDiasMax(isNaN(n) || n < 0 ? null : Math.min(365, n))
                }}
                className="w-16 px-2 py-1 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
              <span className="text-slate-500">dias</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer" title="Oculta as vagas ainda sem análise">
              <input
                type="checkbox"
                checked={soAnalisadas}
                onChange={(e) => setSoAnalisadas(e.target.checked)}
                className="w-3.5 h-3.5 accent-indigo-600"
              />
              <span className="font-semibold text-slate-500">Analisadas</span>
            </label>
          </div>
        </div>
      </div>

      {/* Marcar todas como não seguidas (dois cliques) */}
      {subTab === "pendente" && counts.pendente > 0 && (
        <div className="flex items-center justify-end gap-2 flex-wrap">
          <AvisoSoLeitura />
          <BotaoMarcarTodas
            ids={vagas.filter((v) => v.triagem === "pendente" && visivel(v)).map((v) => v.id)}
            rotulo="Marcar todas como não seguidas"
            podeGravar={podeGravar}
            onMarcar={onMarcarTodasNaoSeguidas}
          />
        </div>
      )}

      {/* Job Cards List */}
      <div className="space-y-3">
        {filtrando && naAba.length > 0 && (
          <p className="text-xs text-slate-500 dark:text-slate-400 px-1">
            Mostrando {lista.length} de {daTriagem.length} {daTriagem.length === 1 ? "vaga" : "vagas"}
            {ocultas > 0 ? ` (${ocultas} sem análise ${ocultas === 1 ? "oculta" : "ocultas"})` : ""}.{" "}
            <button type="button" onClick={limparFiltros} className="underline font-semibold text-indigo-600 dark:text-indigo-400">
              Limpar filtros
            </button>
          </p>
        )}

        {principais.map(cartao)}

        {subTab === "pendente" && baixas.length > 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 p-3 sm:p-4 space-y-3">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <button
                type="button"
                onClick={() => setBaixasAbertas((x) => !x)}
                aria-expanded={baixasAbertas}
                className="font-bold text-sm text-slate-500 dark:text-slate-400"
              >
                {baixasAbertas ? "▾" : "▸"} Baixa aderência ({baixas.length})
              </button>
              {baixasAbertas && (
                <BotaoMarcarTodas
                  ids={baixas.map((v) => v.id)}
                  rotulo="Marcar todas como não seguidas"
                  podeGravar={podeGravar}
                  onMarcar={onMarcarTodasNaoSeguidas}
                />
              )}
            </div>
            {baixasAbertas && <div className="space-y-3">{baixas.map(cartao)}</div>}
          </div>
        )}

        {lista.length === 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-800 dark:text-slate-200">
              Nenhuma vaga nesta seção
            </h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {naAba.length && filtrando
                ? "Nenhuma vaga passa nos filtros."
                : subTab === "pendente"
                  ? "Nenhuma vaga esperando decisão. Clique em Buscar vagas, no topo, ou peça a busca no chat do seu assistente."
                  : subTab === "fora"
                    ? "Nenhuma vaga fora dos critérios. Quando uma busca trouxer vagas que furam os seus filtros, elas aparecem aqui com o motivo."
                    : "Nada por aqui ainda."}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
