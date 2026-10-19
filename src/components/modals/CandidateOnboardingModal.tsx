import React, { useState, useMemo } from "react"
import {
  X,
  Upload,
  FileText,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  ShieldCheck,
  UserCheck,
  HelpCircle,
  SlidersHorizontal,
  Check,
  Download,
  Edit3,
  Globe,
  Layers,
  Eye,
} from "lucide-react"
import {
  PerguntaAnamnese,
  ItemDiagnostico,
  ConflitoMaterial,
  FiltrosBusca,
  PerfilUsuario,
} from "../../types/job"
import {
  ONBOARDING_PERGUNTAS,
  MOCK_CONFLITOS,
  diagnosticarPerfil,
  gerarMarkdownPerfil,
} from "../../services/onboardingData"

interface CandidateOnboardingModalProps {
  isOpen: boolean
  onClose: () => void
  onCompleteOnboarding: (
    perfilAtualizado: PerfilUsuario,
    filtrosAtualizados: FiltrosBusca,
  ) => void
  filtrosAtuais: FiltrosBusca
  perfilAtual: PerfilUsuario
}

type OnboardingStep = "materiais" | "rascunho" | "conflitos" | "anamnese" | "diagnostico" | "revisao" | "filtros"

export default function CandidateOnboardingModal({
  isOpen,
  onClose,
  onCompleteOnboarding,
  filtrosAtuais,
  perfilAtual,
}: CandidateOnboardingModalProps) {
  if (!isOpen) return null

  const [currentStep, setCurrentStep] = useState<OnboardingStep>("materiais")

  // Step 1: Materiais
  const [uploadedFiles, setUploadedFiles] = useState<{
    nome: string
    tamanho: string
    tipo: string
    contatos?: any
  }[]>([
    {
      nome: "Curriculo_Lucas_Ferreira_2025.pdf",
      tamanho: "184 KB",
      tipo: "PDF Document",
      contatos: {
        emails: ["lucas.ferreira@email.com"],
        telefones: ["(11) 98765-4321"],
        linkedin: "linkedin.com/in/lucasferreira-dev",
      },
    },
  ])
  const [rawTextCurriculo, setRawTextCurriculo] = useState("")
  const [isProcessingFile, setIsProcessingFile] = useState(false)

  // Step 3: Conflitos
  const [conflitos, setConflitos] = useState<ConflitoMaterial[]>(MOCK_CONFLITOS)

  // Step 4: Anamnese (Respostas)
  const [respostas, setRespostas] = useState<Record<string, any>>({
    cargos_alvo: [
      "Senior Frontend Engineer",
      "Fullstack TypeScript Developer",
      "Tech Lead React",
    ],
    cargos_alvo_en: ["Senior Frontend Engineer", "Staff Software Engineer"],
    senioridade: ["senior", "especialista"],
    modelos: ["remoto", "hibrido"],
    cidade: "São Paulo",
    estado: "SP",
    pretensao: "R$ 16.000 a R$ 19.000 CLT",
    nao_aceita:
      "Trabalho 100% presencial diário, PJ sem nenhum benefício ou férias",
    "conquista:0":
      "Reformulei a arquitetura do checkout de uma fintech reduzindo o tempo de carregamento em 45% com Server Components.",
    "medida:0":
      "Lighthouse score subiu de 62 para 94 e a taxa de conversão aumentou 14%.",
    ferramentas: [
      "React — avançado",
      "TypeScript — avançado",
      "Next.js — avançado",
      "GraphQL — intermediário",
      "Design Systems & Acessibilidade — avançado",
      "Jest / Testing Library — avançado",
    ],
    idiomas: ["Português — nativo", "Inglês — avançado"],
    ingles: "avancado",
    interesse_exterior: true,
    exterior_remoto: true,
    exterior_paises: ["Estados Unidos", "Canadá", "Portugal", "Alemanha"],
    morar_fora: "Sim, aceitaria realocação para Europa ou Canadá.",
    passaporte: true,
    autorizacao: "",
    sponsor: false,
    fuso: "Até 3 horas de sobreposição com fuso de Nova York (EST)",
    contratacao: ["contractor", "eor"],
  })

  // Pergunta ativa na anamnese
  const [questionIndex, setQuestionIndex] = useState(0)

  // Step 5: Contatos confirmados
  const [contatoConfirmado, setContatoConfirmado] = useState({
    email: "lucas.ferreira@email.com",
    telefone: "(11) 98765-4321",
    linkedin: "linkedin.com/in/lucasferreira-dev",
  })

  // Filtrar perguntas ativas (respeitando perguntas condicionais)
  const activeQuestions = useMemo(() => {
    return ONBOARDING_PERGUNTAS.filter((p) => {
      if (!p.condicao) return true
      return respostas[p.condicao] === true
    })
  }, [respostas])

  const currentQuestion = activeQuestions[questionIndex] || activeQuestions[0]

  // Diagnóstico em tempo real
  const diagnosticoItens = useMemo(() => {
    return diagnosticarPerfil(respostas)
  }, [respostas])

  // Markdown gerado
  const markdownPerfil = useMemo(() => {
    return gerarMarkdownPerfil(perfilAtual.nome, respostas, contatoConfirmado)
  }, [perfilAtual.nome, respostas, contatoConfirmado])

  // Filtros propostos a partir da anamnese
  const filtrosPropostos = useMemo<FiltrosBusca>(() => {
    const termosLimpos = (respostas["cargos_alvo"] || []).map(
      (c: string) => `"${c.trim()}"`,
    )
    return {
      ...filtrosAtuais,
      termos: termosLimpos.length > 0 ? termosLimpos : filtrosAtuais.termos,
      localidade: {
        ...filtrosAtuais.localidade,
        cidade: respostas["cidade"] || filtrosAtuais.localidade.cidade,
        estado: respostas["estado"] || filtrosAtuais.localidade.estado,
      },
      modelos: {
        remoto: (respostas["modelos"] || []).includes("remoto"),
        hibrido: (respostas["modelos"] || []).includes("hibrido"),
        presencial: (respostas["modelos"] || []).includes("presencial"),
      },
      senioridades: respostas["senioridade"] || ["senior"],
      internacional: {
        ...filtrosAtuais.internacional,
        ativo: !!respostas["interesse_exterior"],
        paises: respostas["exterior_paises"] || [],
        termos: respostas["cargos_alvo_en"] || [],
      },
    }
  }, [filtrosAtuais, respostas])

  // Handlers para responder a anamnese
  const handleUpdateResposta = (id: string, valor: any) => {
    setRespostas((prev) => ({ ...prev, [id]: valor }))
  }

  const handleNextQuestion = () => {
    if (questionIndex + 1 < activeQuestions.length) {
      setQuestionIndex(questionIndex + 1)
    } else {
      setCurrentStep("diagnostico")
    }
  }

  const handlePrevQuestion = () => {
    if (questionIndex > 0) {
      setQuestionIndex(questionIndex - 1)
    } else {
      setCurrentStep("conflitos")
    }
  }

  const handleJumpToQuestion = (perguntaId?: string) => {
    if (!perguntaId) return
    const idx = activeQuestions.findIndex((q) => q.id === perguntaId)
    if (idx !== -1) {
      setQuestionIndex(idx)
      setCurrentStep("anamnese")
    }
  }

  // Simula upload de arquivo
  const handleSimulateUpload = () => {
    setIsProcessingFile(true)
    setTimeout(() => {
      setIsProcessingFile(false)
      setUploadedFiles((prev) => [
        ...prev,
        {
          nome: "Perfil_Export_LinkedIn.zip",
          tamanho: "320 KB",
          tipo: "LinkedIn Archive",
          contatos: {
            emails: ["lucas.ferreira@email.com"],
            linkedin: "linkedin.com/in/lucasferreira-dev",
          },
        },
      ])
    }, 800)
  }

  // Finalizar e salvar tudo
  const handleFinalize = () => {
    const perfilAtualizado: PerfilUsuario = {
      ...perfilAtual,
      cargo_atual: respostas["cargos_alvo"]?.[0] || perfilAtual.cargo_atual,
      cargos_alvo: respostas["cargos_alvo"] || perfilAtual.cargos_alvo,
      nivel_ingles: respostas["ingles"] || perfilAtual.nivel_ingles,
      pretensao_salarial_brl:
        respostas["pretensao"] || perfilAtual.pretensao_salarial_brl,
      competencias_chave: (respostas["ferramentas"] || []).map((f: string) =>
        f.split("—")[0].trim(),
      ),
    }

    onCompleteOnboarding(perfilAtualizado, filtrosPropostos)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/60 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                  Primeiros Passos: Onboarding & Anamnese do Candidato
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Calibração de Perfil
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Estruturação do perfil a partir do currículo e LinkedIn para
                calibrar com precisão a IA de vagas
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100"
          >
            <X className="w-5 h-5 hover:text-slate-900 [button:hover_&]:text-slate-900 dark:hover:text-slate-900 dark:[button:hover_&]:text-slate-900 transition-colors" />
          </button>
        </div>

        {/* Stepper Navigation */}
        <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 py-3 overflow-x-auto">
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-max">
            {[
              { id: "materiais", label: "1. Materiais & Envio" },
              { id: "rascunho", label: "2. Rascunho" },
              { id: "conflitos", label: "3. Conflitos" },
              { id: "anamnese", label: "4. Anamnese (Perguntas)" },
              { id: "diagnostico", label: "5. Diagnóstico" },
              { id: "revisao", label: "6. Revisão do Perfil" },
              { id: "filtros", label: "7. Filtros Propostos" },
            ].map((step) => {
              const isActive = currentStep === step.id
              return (
                <button
                  key={step.id}
                  onClick={() => setCurrentStep(step.id as OnboardingStep)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                  }`}
                >
                  {step.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Body Content by Stage */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* ETAPA 1: MATERIAIS & ENVIO */}
          {currentStep === "materiais" && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-200/60 dark:border-indigo-900/40 text-xs text-indigo-900 dark:text-indigo-200 flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block text-sm">
                    Privacidade e Proteção de Dados Sensíveis
                  </span>
                  <p className="mt-0.5 text-slate-600 dark:text-slate-300">
                    Documentos como CPF, RG e data de nascimento são mascarados
                    automaticamente pela ferramenta antes de qualquer
                    processamento. Nada é enviado para a IA sem sua confirmação
                    explícita.
                  </p>
                </div>
              </div>

              {/* Upload Drop Zone */}
              <div
                onClick={handleSimulateUpload}
                className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 rounded-3xl p-8 text-center cursor-pointer bg-slate-50/50 dark:bg-slate-800/30 hover:bg-indigo-50/30 transition space-y-3"
              >
                <div className="w-12 h-12 rounded-2xl bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                    Envie seu Currículo em PDF, Word (.docx) ou Arquivo do
                    LinkedIn
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    Clique para selecionar arquivos do seu computador
                    (armazenados localmente)
                  </p>
                </div>
                {isProcessingFile && (
                  <div className="text-xs text-indigo-600 font-semibold animate-pulse">
                    Extraindo dados e mascarando documentos...
                  </div>
                )}
              </div>

              {/* Uploaded Materials List */}
              <div className="space-y-2">
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500">
                  Materiais Carregados ({uploadedFiles.length})
                </h4>
                <div className="space-y-2">
                  {uploadedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="font-bold text-slate-900 dark:text-white block">
                            {file.nome}
                          </span>
                          <span className="text-slate-400">
                            {file.tamanho} · {file.tipo}
                          </span>
                        </div>
                      </div>
                      <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Processado</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Or paste text */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
                  Ou cole o texto do seu currículo/perfil:
                </label>
                <textarea
                  rows={3}
                  value={rawTextCurriculo}
                  onChange={(e) => setRawTextCurriculo(e.target.value)}
                  placeholder="Cole aqui se preferir não fazer upload de arquivos..."
                  className="w-full p-3 rounded-2xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400"
                />
              </div>
            </div>
          )}

          {/* ETAPA 2: RASCUNHO INICIAL */}
          {currentStep === "rascunho" && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200 flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>
                    Rascunho inicial gerado a partir dos materiais fornecidos.
                  </span>
                </div>
                <span className="text-[11px] bg-emerald-100 dark:bg-emerald-900/80 px-2.5 py-0.5 rounded-full font-bold">
                  100% dos dados mascarados
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                  <h4 className="font-bold text-xs uppercase text-slate-500">
                    Objetivo & Cargo
                  </h4>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">
                    Engenheiro de Software Sênior / Frontend
                  </p>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    5 anos de experiência com TypeScript, React, Next.js e
                    Design Systems.
                  </p>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                  <h4 className="font-bold text-xs uppercase text-slate-500">
                    Últimas Experiências
                  </h4>
                  <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-1">
                    <li>
                      • <b>Tech Lead Frontend</b> na Fintech Alpha (2022 -
                      Atual)
                    </li>
                    <li>
                      • <b>Engenheiro de Software Pleno</b> na ScaleUp Beta
                      (2020 - 2022)
                    </li>
                  </ul>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                  <h4 className="font-bold text-xs uppercase text-slate-500">
                    Formação & Idiomas
                  </h4>
                  <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-1">
                    <li>• Bacharelado em Ciência da Computação (USP)</li>
                    <li>• Inglês Avançado para Negócios</li>
                  </ul>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                  <h4 className="font-bold text-xs uppercase text-slate-500">
                    Habilidades Identificadas
                  </h4>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {[
                      "React",
                      "TypeScript",
                      "Next.js",
                      "Design System",
                      "Jest",
                      "Tailwind",
                    ].map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ETAPA 3: CONFLITOS */}
          {currentStep === "conflitos" && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>Resolução de Divergências entre Fontes</span>
                </div>
                <p>
                  Quando o currículo em PDF e a exportação do LinkedIn trazem
                  informações conflitantes, você escolhe qual é o registro
                  correto para o seu perfil.
                </p>
              </div>

              <div className="space-y-3">
                {conflitos.map((conf, idx) => (
                  <div
                    key={conf.id}
                    className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3"
                  >
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                      {idx + 1}. {conf.campo}
                    </h4>
                    <div className="space-y-2">
                      {conf.opcoes.map((opcao, oIdx) => (
                        <label
                          key={oIdx}
                          className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition ${
                            conf.escolha === oIdx
                              ? "bg-indigo-50/70 border-indigo-400 text-indigo-900 dark:bg-indigo-950/50 dark:border-indigo-700 dark:text-indigo-200"
                              : "bg-slate-50 border-slate-200 dark:bg-slate-800/60 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <input
                              type="radio"
                              name={`conf-${conf.id}`}
                              checked={conf.escolha === oIdx}
                              onChange={() => {
                                setConflitos((prev) =>
                                  prev.map((c) =>
                                    c.id === conf.id
                                      ? { ...c, escolha: oIdx }
                                      : c,
                                  ),
                                )
                              }}
                              className="accent-indigo-600"
                            />
                            <span className="font-semibold text-xs sm:text-sm">
                              {opcao.valor}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-400">
                            Fonte: {opcao.fonte}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ETAPA 4: ANAMNESE GUIADA (PERGUNTAS DO PERFIL) */}
          {currentStep === "anamnese" && currentQuestion && (
            <div className="space-y-5">
              {/* Progress pill */}
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-indigo-600 dark:text-indigo-400">
                  Pergunta {questionIndex + 1} de {activeQuestions.length}
                </span>
                <span className="text-slate-400">
                  {Math.round(
                    ((questionIndex + 1) / activeQuestions.length) * 100,
                  )}
                  % concluído
                </span>
              </div>

              <div className="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                  style={{
                    width: `${((questionIndex + 1) / activeQuestions.length) * 100}%`,
                  }}
                />
              </div>

              {/* Question Card */}
              <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white leading-snug">
                    {currentQuestion.texto}
                  </h3>
                  {currentQuestion.dica && (
                    <p className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">
                      {currentQuestion.dica}
                    </p>
                  )}
                </div>

                {/* Question Input by Type */}
                <div className="pt-2">
                  {/* 1. Texto */}
                  {currentQuestion.tipo === "texto" && (
                    <textarea
                      rows={4}
                      value={respostas[currentQuestion.id] || ""}
                      onChange={(e) =>
                        handleUpdateResposta(currentQuestion.id, e.target.value)
                      }
                      placeholder="Sua resposta..."
                      className="w-full p-4 rounded-2xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                    />
                  )}

                  {/* 2. Lista (um por linha) */}
                  {currentQuestion.tipo === "lista" && (
                    <textarea
                      rows={5}
                      value={
                        Array.isArray(respostas[currentQuestion.id])
                          ? respostas[currentQuestion.id].join("\n")
                          : respostas[currentQuestion.id] || ""
                      }
                      onChange={(e) =>
                        handleUpdateResposta(
                          currentQuestion.id,
                          e.target.value
                            .split("\n")
                            .filter((x) => x.trim().length > 0),
                        )
                      }
                      placeholder="Um item por linha..."
                      className="w-full p-4 rounded-2xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-sans"
                    />
                  )}

                  {/* 3. Opções únicas (radio) */}
                  {currentQuestion.tipo === "opcoes" &&
                    currentQuestion.opcoes && (
                      <div className="space-y-2">
                        {currentQuestion.opcoes.map((op) => (
                          <label
                            key={op.valor}
                            className={`flex items-center gap-3 p-3.5 rounded-2xl border cursor-pointer transition ${
                              respostas[currentQuestion.id] === op.valor
                                ? "bg-indigo-50/70 border-indigo-400 text-indigo-900 dark:bg-indigo-950/50 dark:border-indigo-700 dark:text-indigo-200"
                                : "bg-slate-50 border-slate-200 dark:bg-slate-800/60 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                            }`}
                          >
                            <input
                              type="radio"
                              name={currentQuestion.id}
                              checked={
                                respostas[currentQuestion.id] === op.valor
                              }
                              onChange={() =>
                                handleUpdateResposta(
                                  currentQuestion.id,
                                  op.valor,
                                )
                              }
                              className="accent-indigo-600"
                            />
                            <span className="font-semibold text-xs sm:text-sm">
                              {op.rotulo}
                            </span>
                          </label>
                        ))}
                      </div>
                    )}

                  {/* 4. Multi-seleção (checkbox) */}
                  {currentQuestion.tipo === "multi" &&
                    currentQuestion.opcoes && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {currentQuestion.opcoes.map((op) => {
                          const currentArray =
                            respostas[currentQuestion.id] || []
                          const isChecked = currentArray.includes(op.valor)
                          return (
                            <label
                              key={op.valor}
                              className={`flex items-center gap-3 p-3.5 rounded-2xl border cursor-pointer transition ${
                                isChecked
                                  ? "bg-indigo-50/70 border-indigo-400 text-indigo-900 dark:bg-indigo-950/50 dark:border-indigo-700 dark:text-indigo-200"
                                  : "bg-slate-50 border-slate-200 dark:bg-slate-800/60 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => {
                                  const updated = isChecked
                                    ? currentArray.filter(
                                        (x: string) => x !== op.valor,
                                      )
                                    : [...currentArray, op.valor]
                                  handleUpdateResposta(
                                    currentQuestion.id,
                                    updated,
                                  )
                                }}
                                className="rounded accent-indigo-600"
                              />
                              <span className="font-semibold text-xs sm:text-sm">
                                {op.rotulo}
                              </span>
                            </label>
                          )
                        })}
                      </div>
                    )}

                  {/* 5. Sim / Não */}
                  {currentQuestion.tipo === "sim_nao" && (
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() =>
                          handleUpdateResposta(currentQuestion.id, true)
                        }
                        className={`flex-1 py-3.5 rounded-2xl border font-bold text-xs sm:text-sm transition ${
                          respostas[currentQuestion.id] === true
                            ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                            : "bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100"
                        }`}
                      >
                        Sim
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          handleUpdateResposta(currentQuestion.id, false)
                        }
                        className={`flex-1 py-3.5 rounded-2xl border font-bold text-xs sm:text-sm transition ${
                          respostas[currentQuestion.id] === false
                            ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                            : "bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100"
                        }`}
                      >
                        Não
                      </button>
                    </div>
                  )}
                </div>

                {/* Question Foot Controls */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={handlePrevQuestion}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Voltar</span>
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleNextQuestion}
                      className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                    >
                      Pular Pergunta
                    </button>

                    <button
                      type="button"
                      onClick={handleNextQuestion}
                      className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
                    >
                      <span>
                        {questionIndex + 1 >= activeQuestions.length
                          ? "Concluir"
                          : "Próxima"}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ETAPA 5: DIAGNÓSTICO DO PERFIL */}
          {currentStep === "diagnostico" && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-1">
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                  Diagnóstico Automático de Força do Perfil
                </h4>
                <p className="text-xs text-slate-500">
                  A ferramenta analisa o que está forte e o que ainda falta para
                  calibrar perfeitamente as notas de aderência da IA.
                </p>
              </div>

              {/* Diagnostics List */}
              <div className="space-y-3">
                {diagnosticoItens.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-2xl border flex items-start justify-between gap-3 text-xs ${
                      item.tipo === "falta"
                        ? "bg-rose-50/60 border-rose-200 text-rose-900 dark:bg-rose-950/30 dark:border-rose-900/60 dark:text-rose-200"
                        : item.tipo === "fraco"
                          ? "bg-amber-50/60 border-amber-200 text-amber-900 dark:bg-amber-950/30 dark:border-amber-900/60 dark:text-amber-200"
                          : "bg-blue-50/60 border-blue-200 text-blue-900 dark:bg-blue-950/30 dark:border-blue-900/60 dark:text-blue-200"
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 font-bold">
                        <span
                          className={`uppercase px-1.5 py-0.5 rounded text-[10px] font-extrabold ${
                            item.tipo === "falta"
                              ? "bg-rose-600 text-white"
                              : item.tipo === "fraco"
                                ? "bg-amber-600 text-white"
                                : "bg-blue-600 text-white"
                          }`}
                        >
                          {item.tipo}
                        </span>
                        <span>{item.mensagem}</span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300">
                        {item.pergunta}
                      </p>
                    </div>

                    {item.pergunta_id && (
                      <button
                        onClick={() => handleJumpToQuestion(item.pergunta_id)}
                        className="px-3 py-1.5 rounded-xl font-bold bg-white dark:bg-slate-900 border border-current shadow-2xs hover:scale-105 transition shrink-0"
                      >
                        Responder
                      </button>
                    )}
                  </div>
                ))}

                {diagnosticoItens.length === 0 && (
                  <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center text-xs text-emerald-800 dark:text-emerald-300 font-semibold">
                    Excelente! Seu perfil possui todas as respostas e métricas
                    essenciais para uma análise de alto nível.
                  </div>
                )}
              </div>

              {/* Contact Confirmation */}
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500">
                  Dados de Contato Confirmados para o Perfil
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                      E-mail
                    </label>
                    <input
                      type="email"
                      value={contatoConfirmado.email}
                      onChange={(e) =>
                        setContatoConfirmado({
                          ...contatoConfirmado,
                          email: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-medium"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                      Telefone
                    </label>
                    <input
                      type="text"
                      value={contatoConfirmado.telefone}
                      onChange={(e) =>
                        setContatoConfirmado({
                          ...contatoConfirmado,
                          telefone: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-medium"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                      LinkedIn
                    </label>
                    <input
                      type="text"
                      value={contatoConfirmado.linkedin}
                      onChange={(e) =>
                        setContatoConfirmado({
                          ...contatoConfirmado,
                          linkedin: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-medium"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ETAPA 6: REVISÃO DO PERFIL (PERFIL.MD) */}
          {currentStep === "revisao" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                    Revisão do perfil.md
                  </h4>
                  <p className="text-xs text-slate-500">
                    Este é o documento completo que alimenta o classificador de
                    vagas da IA.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    const blob = new Blob([markdownPerfil], {
                      type: "text/markdown",
                    })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement("a")
                    a.href = url
                    a.download = "perfil.md"
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Baixar perfil.md</span>
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto max-h-[380px] whitespace-pre-wrap leading-relaxed border border-slate-800">
                {markdownPerfil}
              </div>
            </div>
          )}

          {/* ETAPA 7: FILTROS PROPOSTOS AUTOMATICAMENTE */}
          {currentStep === "filtros" && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900 text-xs text-indigo-900 dark:text-indigo-200 space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-sm">
                  <SlidersHorizontal className="w-4 h-4 text-indigo-600" />
                  <span>Filtros Propostos com Base na Anamnese</span>
                </div>
                <p>
                  A ferramenta calculou automaticamente os parâmetros ideais
                  para suas próximas buscas nos portais de emprego.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <span className="font-bold text-slate-500 uppercase text-[10px] block">
                    Termos de Busca Propostos
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {filtrosPropostos.termos.map((t, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950 font-mono text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-200 dark:border-indigo-800"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <span className="font-bold text-slate-500 uppercase text-[10px] block">
                    Modelos de Trabalho & Localidade
                  </span>
                  <p className="font-semibold text-slate-800 dark:text-slate-200">
                    {filtrosPropostos.localidade.cidade},{" "}
                    {filtrosPropostos.localidade.estado}
                  </p>
                  <div className="flex gap-2">
                    {filtrosPropostos.modelos.remoto && (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 font-semibold">
                        Remoto
                      </span>
                    )}
                    {filtrosPropostos.modelos.hibrido && (
                      <span className="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 font-semibold">
                        Híbrido
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <span className="font-bold text-slate-500 uppercase text-[10px] block">
                    Busca Internacional (Exterior)
                  </span>
                  <p className="font-semibold text-slate-800 dark:text-slate-200">
                    {filtrosPropostos.internacional.ativo
                      ? "Ativada (EUA, Canadá, Europa)"
                      : "Desativada"}
                  </p>
                  <p className="text-slate-400">
                    Cargos em inglês:{" "}
                    {(filtrosPropostos.internacional.termos || []).join(", ")}
                  </p>
                </div>

                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <span className="font-bold text-slate-500 uppercase text-[10px] block">
                    Critérios de Corte (Inerentes)
                  </span>
                  <p className="text-slate-700 dark:text-slate-300 font-medium">
                    {respostas["nao_aceita"] || "Nenhum corte cadastrado"}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Action Footer */}
        <div className="p-5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/60 dark:bg-slate-800/40">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
          >
            Fechar
          </button>

          <div className="flex items-center gap-2">
            {currentStep !== "filtros" ? (
              <button
                type="button"
                onClick={() => {
                  const steps: OnboardingStep[] = [
                    "materiais",
                    "rascunho",
                    "conflitos",
                    "anamnese",
                    "diagnostico",
                    "revisao",
                    "filtros",
                  ]
                  const currIdx = steps.indexOf(currentStep)
                  if (currIdx + 1 < steps.length) {
                    setCurrentStep(steps[currIdx + 1])
                  }
                }}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
              >
                <span>Avançar Etapa</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinalize}
                className="flex items-center gap-1.5 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-600/20 transition"
              >
                <Check className="w-4 h-4" />
                <span>Gravar Perfil e Aplicar Filtros de Busca</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
