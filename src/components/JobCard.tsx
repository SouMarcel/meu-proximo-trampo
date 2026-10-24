import React, { useState } from "react"
import {
  ExternalLink,
  Calendar,
  MapPin,
  DollarSign,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  FileText,
  Globe,
  CheckCircle2,
  MoreVertical,
  Trash2,
  Wand2,
  Banknote,
} from "lucide-react"
import type { CamposEditaveis, Vaga, Etapa } from "../types/api"
import { Lembrete } from "./kit/Kit"
import { useFerramenta } from "../contexto/Ferramenta"
import CandidaturaModal from "./modals/CandidaturaModal"
import SalarioModal from "./modals/SalarioModal"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  formatarDataRelativa,
  formatarModelo,
  areaDe,
  paisDe,
  linkSeguro,
  temNota,
} from "../utils/formatters"

interface JobCardProps {
  vaga: Vaga
  onSelect: (vaga: Vaga) => void
  onMoveStage?: (id: string, nextStage: Etapa) => void
  onDelete?: (id: string) => void
  onUpdateVaga?: (id: string, campos: CamposEditaveis, sucesso?: string) => Promise<boolean>
  onPreparar?: (id: string) => void
  /** Avisos da candidatura assistida (spec 027). */
  onAviso?: (m: string, t?: "info" | "erro") => void
}

const PROXIMA_ETAPA: Record<Etapa, Etapa | null> = {
  salva: "aplicada",
  aplicada: "entrevista",
  entrevista: "proposta",
  proposta: "encerrada",
  encerrada: null,
}

const ROTULO_AVANCO: Record<Etapa, string> = {
  salva: "Marcar Aplicada",
  aplicada: "Marcar Entrevista",
  entrevista: "Recebeu Proposta?",
  proposta: "Concluir Processo",
  encerrada: "",
}

export default function JobCard({
  vaga,
  onSelect,
  onMoveStage,
  onDelete,
  onUpdateVaga,
  onPreparar,
  onAviso,
}: JobCardProps) {
  const platStyle = getPlataformaStyle(vaga.plataforma)
  const aderenciaInfo = getAderenciaBadge(vaga.aderencia)
  const proxima = vaga.etapa ? PROXIMA_ETAPA[vaga.etapa] : null
  const { podeGravar } = useFerramenta()
  const [confirmarRemocao, setConfirmarRemocao] = useState(false)
  const [candidatar, setCandidatar] = useState(false)
  const [salario, setSalario] = useState(false)
  // no funil e antes de enviar a candidatura: o botão abre a ajuda para preencher o formulário (quem envia é a pessoa)
  const mostrarCandidatar = Boolean(onAviso && podeGravar && vaga.candidatura_assistida?.ligada && vaga.etapa === "salva")
  const link = linkSeguro(vaga.url_candidatura) || linkSeguro(vaga.url)

  return (
    <div
      onClick={() => onSelect(vaga)}
      className="group relative bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200/90 dark:border-slate-800/90 hover:border-indigo-300 dark:hover:border-indigo-700 shadow-xs hover:shadow-md transition-all duration-200 p-4 cursor-pointer flex flex-col justify-between"
    >
      {/* Header: Platform, Area & Adherence Score */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Platform Tag */}
            <span
              className={`px-2 py-0.5 rounded-lg text-xs font-semibold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}
            >
              {vaga.plataforma}
            </span>

            {/* International Flag */}
            {areaDe(vaga) === "internacional" && (
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[11px] font-medium bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                <Globe className="w-3 h-3" />
                <span>{paisDe(vaga) || "Global"}</span>
              </span>
            )}

            {/* ATS Badge if present */}
            {vaga.ats && (
              <span className="px-1.5 py-0.5 rounded-md text-[10px] font-mono uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {vaga.ats}
              </span>
            )}
          </div>

          {/* Adherence Score Pill */}
          {temNota(vaga) ? (
            <div
              className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${aderenciaInfo.bg} ${aderenciaInfo.text} ${aderenciaInfo.ring}`}
              title={`Aderência de ${vaga.aderencia}% com base nas regras do seu perfil`}
            >
              <Sparkles className="w-3 h-3" />
              <span>{vaga.aderencia}%</span>
            </div>
          ) : (
            <span className="text-[11px] text-slate-400 font-medium">
              Sem nota
            </span>
          )}
        </div>

        {/* Job Title & Company */}
        <h3 className="font-semibold text-sm sm:text-base text-slate-900 dark:text-white leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
          {vaga.titulo}
        </h3>
        <p className="text-xs sm:text-sm font-medium text-slate-600 dark:text-slate-400 mt-0.5 mb-2.5">
          {vaga.empresa}
        </p>

        {/* Location & Modality */}
        <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 mb-2">
          <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400" />
          <span className="truncate">{vaga.local}</span>
          <span className="mx-1 text-slate-300 dark:text-slate-700">·</span>
          <span className="font-medium text-slate-700 dark:text-slate-300 shrink-0">
            {formatarModelo(vaga.modelo_trabalho, vaga.remoto)}
          </span>
        </div>

        {/* Salary */}
        {vaga.salario && (
          <div className="flex items-center gap-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50/80 dark:bg-emerald-950/30 px-2 py-1 rounded-lg border border-emerald-200/60 dark:border-emerald-800/40 w-fit mb-2.5">
            <DollarSign className="w-3.5 h-3.5" />
            <span>{vaga.salario}</span>
          </div>
        )}

        {/* Interview Scheduled Alert */}
        {vaga.entrevista_em && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 mb-2.5">
            <Calendar className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400 shrink-0" />
            <span>Entrevista: {vaga.entrevista_em}</span>
          </div>
        )}

        {/* Positive Signals (Visto, Relocation, etc) */}
        {vaga.sinais && vaga.sinais.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap mb-2.5">
            {vaga.sinais.slice(0, 2).map((sinal, i) => (
              <span
                key={i}
                className="flex items-start gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 max-w-full"
              >
                <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0 mt-0.5" />
                <span className="whitespace-normal break-words leading-tight shadow-none">{sinal}</span>
              </span>
            ))}
          </div>
        )}

        {onUpdateVaga && (
          <div className="mb-2.5">
            <Lembrete vaga={vaga} onUpdateVaga={onUpdateVaga} compacto />
          </div>
        )}

        {/* Notes preview if available */}
        {vaga.anotacao && (
          <p className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2 rounded-lg italic line-clamp-2 border border-slate-100 dark:border-slate-800/80 mb-2.5">
            "{vaga.anotacao}"
          </p>
        )}
      </div>

      {/* Card Footer: Publication date & Quick Actions */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2 mt-2">
        <span className="text-[11px] text-slate-400">
          {formatarDataRelativa(vaga.publicada_em)}
        </span>

        <div
          className="flex items-center gap-1.5"
          onClick={(e) => e.stopPropagation()}
        >
          {/* External Link */}
          {link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title="Abrir anúncio original em nova aba"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          )}

          {vaga.etapa && vaga.etapa !== "encerrada" && (
            <button
              onClick={() => setSalario(true)}
              className="p-1 rounded-md text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition"
              title="Faixa salarial: o que a vaga informa, vagas parecidas e pesquisa no Glassdoor"
              aria-label="Faixa salarial"
            >
              <Banknote className="w-3.5 h-3.5" />
            </button>
          )}

          {mostrarCandidatar && (
            <button
              onClick={() => setCandidatar(true)}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 transition"
              title="Abre a vaga na janela da ferramenta e preenche os campos do formulário com respostas que você confere; quem envia é você"
            >
              <Wand2 className="w-3 h-3" />
              <span>Candidatar com ajuda</span>
            </button>
          )}

          {onPreparar && vaga.etapa === "entrevista" && (
            <button
              onClick={() => onPreparar(vaga.id)}
              className="px-2 py-1 rounded-md text-[11px] font-medium bg-violet-50 hover:bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300 border border-violet-200 dark:border-violet-800 transition"
              title="Dossiê, perguntas prováveis, histórias, simulação, salário e anotações"
            >
              Preparar entrevista
            </button>
          )}

          {/* Advance Stage Button */}
          {proxima && onMoveStage && (
            <button
              disabled={!podeGravar}
              onClick={() => onMoveStage(vaga.id, proxima)}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 dark:bg-slate-800 dark:hover:bg-indigo-950/60 dark:hover:text-indigo-400 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
              title={`Avançar vaga para: ${ROTULO_AVANCO[vaga.etapa || "salva"]}`}
            >
              <span>Avançar</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          )}

          {/* Delete / Remove */}
          {onDelete && (
            <button
              disabled={!podeGravar}
              onClick={() => setConfirmarRemocao(true)}
              className="p-1 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition disabled:opacity-50"
              title="Remover do quadro"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {salario && <SalarioModal vaga={vaga} onClose={() => setSalario(false)} />}
      {candidatar && onAviso && <CandidaturaModal vaga={vaga} onAviso={onAviso} onClose={() => setCandidatar(false)} />}

      {/* Confirmação da remoção: o card escurece e o botão fica no meio dele */}
      {onDelete && confirmarRemocao && (
        <div
          onClick={(e) => {
            e.stopPropagation()
            setConfirmarRemocao(false)
          }}
          className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 rounded-2xl bg-slate-900/75 dark:bg-slate-950/80 backdrop-blur-[2px] p-4 cursor-default"
        >
          <span className="text-xs font-medium text-white">Remover do quadro?</span>
          <button
            autoFocus
            disabled={!podeGravar}
            onClick={(e) => {
              e.stopPropagation()
              onDelete(vaga.id)
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-md transition disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Confirmar remoção</span>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setConfirmarRemocao(false)
            }}
            className="text-[11px] text-slate-300 hover:text-white hover:underline"
          >
            Cancelar
          </button>
        </div>
      )}
    </div>
  )
}
