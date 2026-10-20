import React, { useState } from "react"
import {
  X,
  ExternalLink,
  Calendar,
  MapPin,
  DollarSign,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  FileText,
  CheckSquare,
  Edit3,
  Trash2,
  Clock,
  Save,
} from "lucide-react"
import { Vaga, Etapa, Resultado, ChecklistItem } from "../../types/job"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  getEtapaInfo,
  formatarDataRelativa,
  formatarModelo,
  formatarSenioridade,
} from "../../utils/formatters"

interface JobDetailModalProps {
  vaga: Vaga | null
  isOpen: boolean
  onClose: () => void
  onUpdateVaga: (id: string, updates: Partial<Vaga>) => void
  onDeleteVaga: (id: string) => void
  onForcarVerificar?: (id: string) => Promise<void> | void
  onCompletarDescricao?: (id: string) => Promise<void> | void
}

type DetailTab = "descricao" | "analise" | "kit" | "anotacoes"

export default function JobDetailModal({
  vaga,
  isOpen,
  onClose,
  onUpdateVaga,
  onDeleteVaga,
  onForcarVerificar,
  onCompletarDescricao,
}: JobDetailModalProps) {
  if (!isOpen || !vaga) return null

  const [activeTab, setActiveTab] = useState<DetailTab>("descricao")
  const [anotacao, setAnotacao] = useState(vaga.anotacao || "")
  const [entrevistaEm, setEntrevistaEm] = useState(vaga.entrevista_em || "")
  const [etapa, setEtapa] = useState<Etapa | "">(vaga.etapa || "")
  const [resultado, setResultado] = useState<Resultado | "">(
    vaga.resultado || "",
  )
  const [savedSuccess, setSavedSuccess] = useState(false)

  const platStyle = getPlataformaStyle(vaga.plataforma)
  const aderBadge = getAderenciaBadge(vaga.aderencia)
  const etapaInfo = getEtapaInfo(vaga.etapa)

  // Alternar estado de um item do checklist
  const handleToggleChecklist = (itemId: string) => {
    const currentChecklist = vaga.checklist || []
    const updated = currentChecklist.map((item) => {
      if (item.id === itemId) {
        const nextState =
          item.estado === "a_fazer"
            ? "pronto"
            : item.estado === "pronto"
              ? "nao_se_aplica"
              : "a_fazer"
        return {
          ...item,
          estado: nextState as "a_fazer" | "pronto" | "nao_se_aplica",
        }
      }
      return item
    })
    onUpdateVaga(vaga.id, { checklist: updated })
  }

  const handleSaveNotesAndStatus = () => {
    onUpdateVaga(vaga.id, {
      anotacao,
      entrevista_em: entrevistaEm || null,
      etapa: etapa as Etapa || null,
      resultado: etapa === "encerrada" ? resultado as Resultado || null : null,
    })
    setSavedSuccess(true)
    setTimeout(() => setSavedSuccess(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-4xl max-h-[92vh] bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}
              >
                {vaga.plataforma}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${etapaInfo.badgeBg} ${etapaInfo.badgeText}`}
              >
                {etapaInfo.label}
              </span>
              {vaga.aderencia !== undefined && (
                <span
                  className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${aderBadge.bg} ${aderBadge.text} ${aderBadge.ring}`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{vaga.aderencia}% Aderência</span>
                </span>
              )}
            </div>

            <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white leading-snug">
              {vaga.titulo}
            </h2>

            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 flex-wrap">
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

          {/* Close & External Links */}
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={vaga.url_candidatura || vaga.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
            >
              <span>Abrir Vaga</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100"
            >
              <X className="w-5 h-5 hover:text-slate-900 [button:hover_&]:text-slate-900 dark:hover:text-slate-900 dark:[button:hover_&]:text-slate-900 transition-colors" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-slate-200 dark:border-slate-800 px-6 gap-2 bg-white dark:bg-slate-900">
          <button
            onClick={() => setActiveTab("descricao")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition ${
              activeTab === "descricao"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            Descrição & Requisitos
          </button>

          <button
            onClick={() => setActiveTab("analise")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "analise"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Análise da IA</span>
          </button>

          <button
            onClick={() => setActiveTab("kit")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "kit"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <CheckSquare className="w-3.5 h-3.5" />
            <span>Kit de Candidatura</span>
          </button>

          <button
            onClick={() => setActiveTab("anotacoes")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "anotacoes"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Funil & Anotações</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {/* 1. Descrição */}
          {activeTab === "descricao" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block font-medium">
                    Modelo
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">
                    {formatarModelo(vaga.modelo_trabalho, vaga.remoto)}
                  </span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block font-medium">
                    Senioridade
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">
                    {formatarSenioridade(vaga.senioridade)}
                  </span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block font-medium">
                    Contrato
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">
                    {vaga.tipo || "Tempo Integral"}
                  </span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block font-medium">
                    Publicada em
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">
                    {formatarDataRelativa(vaga.publicada_em)}
                  </span>
                </div>
              </div>

                            {/* Aviso de descrição pendente (Spec 019) */}
              {vaga.descricao_pendente && (
                <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-600 shrink-0" />
                    <p className="text-xs text-amber-800 dark:text-amber-200">
                      Esta vaga possui apenas o resumo preliminar. A descrição completa pode ser lida agora.
                    </p>
                  </div>
                  {onCompletarDescricao && (
                    <button
                      onClick={() => onCompletarDescricao(vaga.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white shrink-0 transition"
                    >
                      Completar Descrição
                    </button>
                  )}
                </div>
              )}

              <div className="space-y-2">
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                  Texto Original do Anúncio
                </h4>
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
                  {vaga.descricao}
                </div>
              </div>
            </div>
          )}

          {/* 2. Análise da IA */}
          {activeTab === "analise" && (
            <div className="space-y-4">
              {vaga.aderencia === undefined ? (
                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 text-center space-y-3">
                  <Sparkles className="w-8 h-8 text-indigo-500 mx-auto" />
                  <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                    Nota de aderência ainda não calculada
                  </h4>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Esta vaga ainda não passou pela verificação de IA com base nas competências e requisitos do seu perfil.
                  </p>
                  {onForcarVerificar && (
                    <button
                      onClick={() => onForcarVerificar(vaga.id)}
                      className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 transition shadow-xs"
                    >
                      Forçar verificar com IA agora
                    </button>
                  )}
                </div>
              ) : (
                <>
              <div className="bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/60 rounded-2xl p-4 sm:p-5 space-y-2">
                <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-bold text-sm">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>Resumo do Ajuste ao seu Perfil</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  {vaga.resumo ||
                    "Análise detalhada realizada pelo modelo de inteligência artificial configurado."}
                </p>
              </div>

              {/* Pontos de Encaixe */}
              {vaga.encaixe && vaga.encaixe.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Pontos Fortes & Competências Alinhadas</span>
                  </h4>
                  <div className="space-y-1.5">
                    {vaga.encaixe.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 text-xs text-emerald-900 dark:text-emerald-200"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Lacunas / Pontos de atenção */}
              {vaga.lacunas && vaga.lacunas.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Requisitos Não Encontrados no seu Currículo</span>
                  </h4>
                  <div className="space-y-1.5">
                    {vaga.lacunas.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-3 rounded-xl bg-amber-50/50 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-800/40 text-xs text-amber-900 dark:text-amber-200"
                      >
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sinais positivos */}
              {vaga.sinais && vaga.sinais.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-teal-700 dark:text-teal-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Sinais Positivos e Benefícios Diferenciados</span>
                  </h4>
                  <div className="space-y-1.5">
                    {vaga.sinais.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-3 rounded-xl bg-teal-50/50 dark:bg-teal-950/30 border border-teal-200/60 dark:border-teal-800/40 text-xs text-teal-900 dark:text-teal-200"
                      >
                        <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
                </>
              )}
            </div>
          )}

          {/* 3. Kit de Candidatura */}
          {activeTab === "kit" && (
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                Checklist prático dos materiais e preparações necessários para
                maximizar sua taxa de conversão nesta candidatura.
              </p>

              <div className="space-y-2">
                {(vaga.checklist && vaga.checklist.length > 0
                  ? vaga.checklist
                  : [
                      {
                        id: "k1",
                        texto:
                          "Currículo ajustado destacando palavras-chave desta vaga",
                        estado: "a_fazer",
                      },
                      {
                        id: "k2",
                        texto:
                          "Carta de motivação personalizada no método STAR",
                        estado: "a_fazer",
                      },
                      {
                        id: "k3",
                        texto:
                          "Revisar repositórios de código no GitHub relacionados à stack",
                        estado: "pronto",
                      },
                      {
                        id: "k4",
                        texto:
                          "Conexão com recrutadores da empresa no LinkedIn",
                        estado: "a_fazer",
                      },
                    ]
                ).map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleToggleChecklist(item.id)}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-5 h-5 rounded-md flex items-center justify-center transition ${
                          item.estado === "pronto"
                            ? "bg-emerald-500 text-white"
                            : item.estado === "nao_se_aplica"
                              ? "bg-slate-200 dark:bg-slate-700 text-slate-400"
                              : "border-2 border-slate-300 dark:border-slate-600"
                        }`}
                      >
                        {item.estado === "pronto" && (
                          <CheckCircle2 className="w-4 h-4" />
                        )}
                        {item.estado === "nao_se_aplica" && (
                          <span className="text-xs font-bold">-</span>
                        )}
                      </div>
                      <span
                        className={`text-xs sm:text-sm ${
                          item.estado === "pronto"
                            ? "line-through text-slate-400"
                            : "text-slate-800 dark:text-slate-200"
                        }`}
                      >
                        {item.texto}
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold text-slate-400">
                      {item.estado === "pronto"
                        ? "Concluído"
                        : item.estado === "nao_se_aplica"
                          ? "Não se aplica"
                          : "Pendente"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4. Funil & Anotações */}
          {activeTab === "anotacoes" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1">
                    Etapa Atual no Quadro
                  </label>
                  <select
                    value={etapa}
                    onChange={(e) => setEtapa(e.target.value as Etapa)}
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  >
                    <option value="salva">Salva</option>
                    <option value="aplicada">Aplicação Enviada</option>
                    <option value="entrevista">Entrevista Agendada</option>
                    <option value="proposta">Proposta Recebida</option>
                    <option value="encerrada">Encerrada</option>
                  </select>
                </div>

                {etapa === "encerrada" && (
                  <div>
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1">
                      Resultado Final
                    </label>
                    <select
                      value={resultado}
                      onChange={(e) =>
                        setResultado(e.target.value as Resultado)
                      }
                      className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                    >
                      <option value="">Selecione o desfecho...</option>
                      <option value="contratado">Contratado!</option>
                      <option value="nao_aprovado">Não Aprovado</option>
                      <option value="desisti">Desisti</option>
                      <option value="cancelada">Vaga Cancelada</option>
                    </select>
                  </div>
                )}

                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1">
                    Data de Entrevista
                  </label>
                  <input
                    type="text"
                    value={entrevistaEm}
                    onChange={(e) => setEntrevistaEm(e.target.value)}
                    placeholder="Ex.: 2025-02-26 14:00"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1">
                  Anotações Pessoais
                </label>
                <textarea
                  rows={6}
                  value={anotacao}
                  onChange={(e) => setAnotacao(e.target.value)}
                  placeholder="Feedback de entrevistadores, perguntas feitas, pretensão combinada, impressões da cultura..."
                  className="w-full p-3.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => {
                    if (
                      confirm("Remover esta vaga do quadro?")
                    ) {
                      onDeleteVaga(vaga.id)
                      onClose()
                    }
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remover do quadro</span>
                </button>

                <button
                  onClick={handleSaveNotesAndStatus}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>
                    {savedSuccess ? "Alterações Salvas!" : "Salvar Alterações"}
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
