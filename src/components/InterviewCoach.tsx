import React, { useState, useMemo } from "react"
import {
  MessageSquareCode,
  Sparkles,
  Plus,
  Calendar,
  BookOpen,
  CheckCircle2,
  HelpCircle,
  Award,
  Edit3,
  Save,
  Building2,
  UserCheck,
  Target,
} from "lucide-react"
import { Vaga, HistoriaSTAR, PerguntaEntrevista } from "../types/job"

interface InterviewCoachProps {
  vagas: Vaga[]
  onUpdateVaga: (id: string, updates: Partial<Vaga>) => void
  onSelectVagaModal: (vaga: Vaga) => void
}

export default function InterviewCoach({
  vagas,
  onUpdateVaga,
  onSelectVagaModal,
}: InterviewCoachProps) {
  // Vagas que estão em entrevista ou têm histórias/perguntas
  const vagasParaEntrevista = useMemo(() => {
    const priorizadas = vagas.filter(
      (v) =>
        v.etapa === "entrevista" || v.etapa === "aplicada" || v.entrevista_em,
    )
    return priorizadas.length > 0 ? priorizadas : vagas.slice(0, 5)
  }, [vagas])

  const [selectedVagaId, setSelectedVagaId] = useState<string>(
    vagasParaEntrevista[0]?.id || "",
  )

  const selectedVaga = useMemo(() => {
    return (
      vagas.find((v) => v.id === selectedVagaId) ||
      vagasParaEntrevista[0] ||
      null
    )
  }, [vagas, selectedVagaId, vagasParaEntrevista])

  // Aba interna: Perguntas Frequentes vs Histórias STAR vs Bloco de Notas
  const [coachTab, setCoachTab] = useState<"perguntas" | "star" | "anotacoes">(
    "perguntas",
  )

  // Estado do formulário de nova história STAR
  const [showAddStar, setShowAddStar] = useState(false)
  const [newStar, setNewStar] = useState<Partial<HistoriaSTAR>>({
    titulo: "",
    situacao: "",
    tarefa: "",
    acao: "",
    resultado: "",
    competencias: [],
  })

  // Anotações da entrevista
  const [anotacaoTexto, setAnotacaoTexto] = useState(
    selectedVaga?.anotacao || "",
  )
  const [dataEntrevistaInput, setDataEntrevistaInput] = useState(
    selectedVaga?.entrevista_em || "",
  )
  const [salvouSucesso, setSalvouSucesso] = useState(false)

  const handleSaveNotes = () => {
    if (!selectedVaga) return
    onUpdateVaga(selectedVaga.id, {
      anotacao: anotacaoTexto,
      entrevista_em: dataEntrevistaInput || null,
    })
    setSalvouSucesso(true)
    setTimeout(() => setSalvouSucesso(false), 2000)
  }

  const handleAddStarStory = () => {
    if (!selectedVaga || !newStar.titulo) return
    const historia: HistoriaSTAR = {
      id: "star-" + Date.now(),
      titulo: newStar.titulo || "História de Sucesso",
      situacao: newStar.situacao || "",
      tarefa: newStar.tarefa || "",
      acao: newStar.acao || "",
      resultado: newStar.resultado || "",
      competencias: newStar.competencias || [
        "Resolução de Problemas",
        "Comunicação",
      ],
    }

    const updated = [...(selectedVaga.historias_star || []), historia]
    onUpdateVaga(selectedVaga.id, { historias_star: updated })
    setShowAddStar(false)
    setNewStar({
      titulo: "",
      situacao: "",
      tarefa: "",
      acao: "",
      resultado: "",
      competencias: [],
    })
  }

  if (!selectedVaga) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
        <MessageSquareCode className="w-10 h-10 text-slate-400 mx-auto mb-3" />
        <h3 className="font-bold text-slate-800 dark:text-slate-200">
          Nenhuma vaga selecionada para preparação de entrevista
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Adicione uma vaga ao seu quadro para começar a treinar perguntas e
          respostas.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Top Selector Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-2xs">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400">
              <MessageSquareCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                Treinador & Preparador de Entrevistas com IA
              </h3>
              <p className="text-xs text-slate-500">
                Perguntas técnicas, comportamentais e histórias estruturadas no
                método STAR
              </p>
            </div>
          </div>

          {/* Select dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 shrink-0">
              Preparar para:
            </span>
            <select
              value={selectedVaga.id}
              onChange={(e) => {
                setSelectedVagaId(e.target.value)
                const v = vagas.find((item) => item.id === e.target.value)
                if (v) {
                  setAnotacaoTexto(v.anotacao || "")
                  setDataEntrevistaInput(v.entrevista_em || "")
                }
              }}
              className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none"
            >
              {vagasParaEntrevista.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.empresa} - {v.titulo}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Company & Role Briefing Card */}
      <div className="bg-gradient-to-r from-purple-900/90 via-slate-900 to-indigo-950 rounded-2xl p-5 text-white border border-purple-800/40 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-purple-500/30 text-purple-200 border border-purple-400/30">
                {selectedVaga.empresa}
              </span>
              <span className="text-xs text-purple-200/80">
                {selectedVaga.local} · {selectedVaga.plataforma}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold">
              {selectedVaga.titulo}
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl line-clamp-2">
              {selectedVaga.resumo || selectedVaga.descricao?.slice(0, 180)}
            </p>
          </div>

          {/* Interview Date Setting */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-3 border border-white/10 space-y-1.5 shrink-0">
            <span className="text-[11px] font-semibold text-purple-200 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              Data da Próxima Conversa
            </span>
            <input
              type="text"
              value={dataEntrevistaInput}
              onChange={(e) => setDataEntrevistaInput(e.target.value)}
              placeholder="Ex.: 26/02 às 14:00"
              className="px-2.5 py-1 rounded-lg text-xs bg-black/40 border border-white/20 text-white placeholder-slate-400 focus:outline-none w-full"
            />
          </div>
        </div>
      </div>

      {/* Navigation Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setCoachTab("perguntas")}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
            coachTab === "perguntas"
              ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          <span>Perguntas Prováveis & Dicas da IA</span>
        </button>

        <button
          onClick={() => setCoachTab("star")}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
            coachTab === "star"
              ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Banco de Histórias STAR</span>
          <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-purple-200 dark:bg-purple-900 text-purple-800 dark:text-purple-200 font-bold">
            {selectedVaga.historias_star?.length || 0}
          </span>
        </button>

        <button
          onClick={() => setCoachTab("anotacoes")}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
            coachTab === "anotacoes"
              ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
        >
          <Edit3 className="w-4 h-4" />
          <span>Bloco de Anotações & Feedback</span>
        </button>
      </div>

      {/* Tab 1: Perguntas Prováveis */}
      {coachTab === "perguntas" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(selectedVaga.perguntas_frequentes &&
            selectedVaga.perguntas_frequentes.length > 0
              ? selectedVaga.perguntas_frequentes
              : [
                  {
                    id: "p-gen-1",
                    pergunta:
                      "Fale sobre sua experiência técnica com as principais ferramentas exigidas nesta oportunidade.",
                    tipo: "tecnica",
                    dica: "Destaque projetos reais onde você aumentou performance, reduziu bugs ou mentorou colegas de equipe.",
                  },
                  {
                    id: "p-gen-2",
                    pergunta:
                      "Como você resolve divergências técnicas com outros engenheiros ou com o time de Produto?",
                    tipo: "comportamental",
                    dica: "Cite escuta ativa, criação de provas de conceito (PoC) objetivas e priorização baseada em dados e métricas de negócio.",
                  },
                  {
                    id: "p-gen-3",
                    pergunta:
                      "Por que você tem interesse específico nesta oportunidade na " +
                      selectedVaga.empresa +
                      "?",
                    tipo: "situacional",
                    dica: "Demonstre que você pesquisou sobre o produto deles, desafios recentes de escala e valores culturais da organização.",
                  },
                ]
            ).map((item, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`px-2 py-0.5 rounded-md text-[11px] font-semibold uppercase ${
                      item.tipo === "tecnica"
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                        : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                    }`}
                  >
                    {item.tipo}
                  </span>
                  <span className="text-xs text-slate-400">
                    Questão #{idx + 1}
                  </span>
                </div>

                <h4 className="font-bold text-sm text-slate-900 dark:text-white leading-snug">
                  "{item.pergunta}"
                </h4>

                <div className="bg-slate-50 dark:bg-slate-800/80 rounded-xl p-3 border border-slate-100 dark:border-slate-800 space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-700 dark:text-purple-400">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Como estruturar uma resposta de alto impacto:</span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {item.dica}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Banco de Histórias STAR */}
      {coachTab === "star" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              O método STAR (Situação, Tarefa, Ação, Resultado) é o formato
              padrão ouro para impressionar recrutadores e lideranças técnicas.
            </p>
            <button
              onClick={() => setShowAddStar(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 transition shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nova História STAR</span>
            </button>
          </div>

          {/* Form to add a new STAR story */}
          {showAddStar && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-purple-200 dark:border-purple-800 p-5 shadow-md space-y-3">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Criar Nova História no Método STAR
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                    Título da História
                  </label>
                  <input
                    type="text"
                    value={newStar.titulo || ""}
                    onChange={(e) =>
                      setNewStar({ ...newStar, titulo: e.target.value })
                    }
                    placeholder="Ex.: Resolução do gargalo de memória no microsserviço de checkout"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white mt-1"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="font-semibold text-slate-600 dark:text-slate-300">
                      S - Situação (O contexto / problema)
                    </label>
                    <textarea
                      rows={2}
                      value={newStar.situacao || ""}
                      onChange={(e) =>
                        setNewStar({ ...newStar, situacao: e.target.value })
                      }
                      placeholder="Qual era o cenário ou desafio enfrentado pela empresa?"
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white mt-1"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-600 dark:text-slate-300">
                      T - Tarefa (Sua responsabilidade)
                    </label>
                    <textarea
                      rows={2}
                      value={newStar.tarefa || ""}
                      onChange={(e) =>
                        setNewStar({ ...newStar, tarefa: e.target.value })
                      }
                      placeholder="O que exatamente cabia a você entregar ou solucionar?"
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white mt-1"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-600 dark:text-slate-300">
                      A - Ação (O que você executou)
                    </label>
                    <textarea
                      rows={2}
                      value={newStar.acao || ""}
                      onChange={(e) =>
                        setNewStar({ ...newStar, acao: e.target.value })
                      }
                      placeholder="Quais técnicas, arquiteturas e decisões você implementou?"
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white mt-1"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-600 dark:text-slate-300">
                      R - Resultado (Impacto quantificável)
                    </label>
                    <textarea
                      rows={2}
                      value={newStar.resultado || ""}
                      onChange={(e) =>
                        setNewStar({ ...newStar, resultado: e.target.value })
                      }
                      placeholder="Números, porcentagens, redução de custos ou tempo poupado"
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white mt-1"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setShowAddStar(false)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleAddStarStory}
                    className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500"
                  >
                    Salvar História
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Existing STAR stories list */}
          <div className="space-y-3">
            {selectedVaga.historias_star &&
            selectedVaga.historias_star.length > 0 ? (
              selectedVaga.historias_star.map((hist) => (
                <div
                  key={hist.id}
                  className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                      {hist.titulo}
                    </h4>
                    <div className="flex items-center gap-1.5">
                      {hist.competencias.map((comp, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                        >
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                    <div className="bg-slate-50 dark:bg-slate-800/80 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                      <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                        Situação (S)
                      </span>
                      <p className="text-slate-600 dark:text-slate-400">
                        {hist.situacao}
                      </p>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800/80 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                      <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                        Tarefa (T)
                      </span>
                      <p className="text-slate-600 dark:text-slate-400">
                        {hist.tarefa}
                      </p>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800/80 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                      <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                        Ação (A)
                      </span>
                      <p className="text-slate-600 dark:text-slate-400">
                        {hist.acao}
                      </p>
                    </div>
                    <div className="bg-emerald-50 dark:bg-emerald-950/40 p-3 rounded-xl border border-emerald-200 dark:border-emerald-800">
                      <span className="font-bold text-emerald-800 dark:text-emerald-300 block mb-1">
                        Resultado (R)
                      </span>
                      <p className="text-emerald-700 dark:text-emerald-300 font-medium">
                        {hist.resultado}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 text-center text-xs text-slate-500">
                Nenhuma história STAR cadastrada ainda para esta vaga. Clique em
                "Nova História STAR" para cadastrar seu case de sucesso!
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Bloco de Anotações */}
      {coachTab === "anotacoes" && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-sm text-slate-900 dark:text-white">
              Anotações, Feedback de Entrevistadores & Próximos Passos
            </h4>
            <button
              onClick={handleSaveNotes}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition shadow-xs"
            >
              <Save className="w-3.5 h-3.5" />
              <span>
                {salvouSucesso ? "Salvo com sucesso!" : "Salvar Anotações"}
              </span>
            </button>
          </div>
          <textarea
            rows={6}
            value={anotacaoTexto}
            onChange={(e) => setAnotacaoTexto(e.target.value)}
            placeholder="Registre aqui quem participou da entrevista, perguntas feitas, impressões sobre a cultura da empresa, pretensão salarial informada e data de retorno prometida..."
            className="w-full p-4 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
          />
        </div>
      )}
    </div>
  )
}
