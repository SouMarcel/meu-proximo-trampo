import React, { useState } from "react"
import {
  X,
  Link as LinkIcon,
  FileText,
  Edit,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  Building2,
  MapPin,
  DollarSign,
  Plus,
} from "lucide-react"
import { Vaga, Plataforma, Etapa } from "../../types/job"

interface AddJobModalProps {
  isOpen: boolean
  onClose: () => void
  onAddVaga: (vaga: Vaga) => void
}

type InputMethod = "link" | "post" | "manual"

export default function AddJobModal({
  isOpen,
  onClose,
  onAddVaga,
}: AddJobModalProps) {
  if (!isOpen) return null

  const [method, setMethod] = useState<InputMethod>("link")

  // Link State
  const [urlInput, setUrlInput] = useState("")
  const [isParsingLink, setIsParsingLink] = useState(false)
  const [linkParsedInfo, setLinkParsedInfo] = useState<Partial<Vaga> | null>(
    null,
  )
  const [linkError, setLinkError] = useState("")

  // Post text State
  const [postText, setPostText] = useState("")
  const [isExtractingText, setIsExtractingText] = useState(false)

  // Common Form Fields
  const [titulo, setTitulo] = useState("")
  const [empresa, setEmpresa] = useState("")
  const [plataforma, setPlataforma] = useState<Plataforma>("LinkedIn")
  const [local, setLocal] = useState("Remoto Brasil")
  const [salario, setSalario] = useState("")
  const [descricao, setDescricao] = useState("")
  const [etapaDestino, setEtapaDestino] = useState<string>("relatorio")
  const [area, setArea] = useState<"nacional" | "internacional">("nacional")

  // Simula parsing de URL de portais conhecidos
  const handleParseUrl = () => {
    if (!urlInput.trim()) return
    setIsParsingLink(true)
    setLinkError("")

    setTimeout(() => {
      setIsParsingLink(false)
      const u = urlInput.toLowerCase()
      let detectedPlat: Plataforma = "Outra"
      let detectedTitulo = "Engenheiro de Software"
      let detectedEmpresa = "Empresa Inovadora"
      let detectedArea: "nacional" | "internacional" = "nacional"

      if (u.includes("linkedin.com")) {
        detectedPlat = "LinkedIn"
        detectedTitulo = "Senior Fullstack Engineer (React / TypeScript)"
        detectedEmpresa = "TechCorp"
      } else if (u.includes("gupy.io")) {
        detectedPlat = "Gupy"
        detectedTitulo = "Desenvolvedor Frontend Sênior"
        detectedEmpresa = "Fintech Brasil"
      } else if (u.includes("greenhouse.io")) {
        detectedPlat = "Greenhouse"
        detectedTitulo = "Staff Software Engineer - Remote Global"
        detectedEmpresa = "ScaleUp Silicon Valley"
        detectedArea = "internacional"
      } else if (u.includes("lever.co")) {
        detectedPlat = "Lever"
        detectedTitulo = "Senior Frontend Developer"
        detectedEmpresa = "Cloud Solutions Inc"
        detectedArea = "internacional"
      } else if (u.includes("indeed.com")) {
        detectedPlat = "Indeed"
        detectedTitulo = "Especialista React / Next.js"
        detectedEmpresa = "E-Commerce Líder"
      } else if (u.includes("nerdin.com.br")) {
        detectedPlat = "Nerdin"
        detectedTitulo = "Dev React Pleno"
        detectedEmpresa = "Consultoria de TI"
      }

      setTitulo(detectedTitulo)
      setEmpresa(detectedEmpresa)
      setPlataforma(detectedPlat)
      setArea(detectedArea)
      setDescricao(
        `Vaga importada via link: ${urlInput}\n\nResponsabilidades e atribuições:\n- Desenvolvimento de aplicações modernas e responsivas\n- Conhecimento em testes unitários e boas práticas de arquitetura\n- Comunicação clara e colaborativa.`,
      )
      setLinkParsedInfo({
        titulo: detectedTitulo,
        empresa: detectedEmpresa,
        plataforma: detectedPlat,
      })
    }, 800)
  }

  // Simula extração de texto de post
  const handleExtractFromPost = () => {
    if (!postText.trim()) return
    setIsExtractingText(true)

    setTimeout(() => {
      setIsExtractingText(false)
      // Detecção heurística simples
      const linhas = postText.split("\n").filter((l) => l.trim().length > 0)
      const primeiraLinha = linhas[0] || "Oportunidade Frontend"
      setTitulo(primeiraLinha.slice(0, 60))
      setEmpresa("Divulgado em Rede Social")
      setPlataforma("LinkedIn")
      setDescricao(postText)
      setLocal("Remoto")
      setLinkParsedInfo({
        titulo: primeiraLinha.slice(0, 60),
        empresa: "Rede Social",
        plataforma: "LinkedIn",
      })
    }, 600)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!titulo || !empresa) return

    const isNoRelatorio = etapaDestino === "relatorio"

    const novaVaga: Vaga = {
      id: "vaga-" + Date.now(),
      titulo,
      empresa,
      plataforma,
      local: local || "Remoto Brasil",
      remoto: local.toLowerCase().includes("remoto"),
      area,
      pais_vaga:
        area === "internacional" ? "Estados Unidos / Global" : "Brasil",
      idioma: area === "internacional" ? "en" : "pt",
      url: urlInput || "https://linkedin.com",
      url_candidatura: urlInput || null,
      salario: salario || null,
      tipo: "Tempo Integral",
      descricao: descricao || "Descrição fornecida no cadastro.",
      publicada_em: new Date().toISOString().split("T")[0],
      encontrada_em: new Date().toISOString().split("T")[0],
      triagem: isNoRelatorio ? "pendente" : "seguir",
      etapa: isNoRelatorio ? null : etapaDestino as Etapa,
      etapa_em: isNoRelatorio ? null : new Date().toISOString().split("T")[0],
      resultado: null,
      anotacao: "",
      aderencia: 85,
      analise_status: "feita",
      resumo: `Vaga adicionada manualmente. Ótima compatibilidade preliminar com suas competências-chave em ${plataforma}.`,
      encaixe: ["React", "TypeScript", "Experiência de mercado"],
      lacunas: [],
      alertas: [],
      sinais: ["Oportunidade adicionada via captura inteligente"],
      checklist: [
        {
          id: "c1",
          texto: "Revisar currículo para palavras-chave desta vaga",
          estado: "a_fazer",
        },
        {
          id: "c2",
          texto: "Enviar candidatura e registrar retorno",
          estado: "a_fazer",
        },
      ],
    }

    onAddVaga(novaVaga)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Adicionar Nova Oportunidade
              </h3>
              <p className="text-xs text-slate-500">
                Importe por link de qualquer portal, cole o texto de um post ou
                preencha os dados
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

        {/* Method Selector Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 gap-2 bg-white dark:bg-slate-900">
          <button
            type="button"
            onClick={() => setMethod("link")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              method === "link"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <LinkIcon className="w-3.5 h-3.5" />
            <span>Por Link de Vaga</span>
          </button>

          <button
            type="button"
            onClick={() => setMethod("post")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              method === "post"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Post / Mensagem</span>
          </button>

          <button
            type="button"
            onClick={() => setMethod("manual")}
            className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              method === "manual"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Edit className="w-3.5 h-3.5" />
            <span>Manual</span>
          </button>
        </div>

        {/* Form Body */}
        <form
          onSubmit={handleSubmit}
          className="p-6 overflow-y-auto flex-1 space-y-4"
        >
          {/* 1. Link Parser Input */}
          {method === "link" && (
            <div className="space-y-3 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
                Link do anúncio (LinkedIn, Indeed, Gupy, Greenhouse, Lever,
                Ashby, Nerdin...)
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://exemplo.com/vaga/..."
                  className="flex-1 px-3.5 py-2 rounded-xl text-xs sm:text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                <button
                  type="button"
                  onClick={handleParseUrl}
                  disabled={isParsingLink}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs shrink-0"
                >
                  {isParsingLink ? "Lendo dados..." : "Buscar dados"}
                </button>
              </div>
              {linkParsedInfo && (
                <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium pt-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Dados detectados com sucesso! Confira abaixo.</span>
                </div>
              )}
            </div>
          )}

          {/* 2. Text Parser Input */}
          {method === "post" && (
            <div className="space-y-3 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
                Texto completo do post, e-mail ou mensagem
              </label>
              <textarea
                rows={4}
                value={postText}
                onChange={(e) => setPostText(e.target.value)}
                placeholder="Cole aqui o texto inteiro da vaga compartilhada no LinkedIn ou WhatsApp..."
                className="w-full p-3 rounded-xl text-xs sm:text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleExtractFromPost}
                  disabled={isExtractingText}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs"
                >
                  {isExtractingText ? "Extraindo com IA..." : "Extrair campos"}
                </button>
              </div>
            </div>
          )}

          {/* Form Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Cargo / Título da Vaga *
              </label>
              <input
                type="text"
                required
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                placeholder="Ex.: Senior Frontend Engineer"
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Empresa *
              </label>
              <input
                type="text"
                required
                value={empresa}
                onChange={(e) => setEmpresa(e.target.value)}
                placeholder="Ex.: Nubank, Stone, Vercel..."
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Plataforma de Origem
              </label>
              <select
                value={plataforma}
                onChange={(e) => setPlataforma(e.target.value as Plataforma)}
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              >
                <option value="LinkedIn">LinkedIn</option>
                <option value="Gupy">Gupy</option>
                <option value="Indeed">Indeed</option>
                <option value="Greenhouse">Greenhouse</option>
                <option value="Lever">Lever</option>
                <option value="Ashby">Ashby</option>
                <option value="RemoteOK">RemoteOK</option>
                <option value="Remotive">Remotive</option>
                <option value="Nerdin">Nerdin</option>
                <option value="Outra">Outra</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Local / Modelo
              </label>
              <input
                type="text"
                value={local}
                onChange={(e) => setLocal(e.target.value)}
                placeholder="Ex.: Remoto Brasil, Híbrido SP..."
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Salário Informado (opcional)
              </label>
              <input
                type="text"
                value={salario}
                onChange={(e) => setSalario(e.target.value)}
                placeholder="Ex.: R$ 16.000 CLT ou $6,000 USD"
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Para onde enviar esta vaga?
              </label>
              <select
                value={etapaDestino}
                onChange={(e) => setEtapaDestino(e.target.value)}
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-semibold"
              >
                <option value="relatorio">
                  Relatório de Vagas (Para Decidir)
                </option>
                <option value="salva">Quadro: Salva</option>
                <option value="aplicada">Quadro: Aplicação Enviada</option>
                <option value="entrevista">Quadro: Entrevista Agendada</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
              Descrição da Vaga
            </label>
            <textarea
              rows={5}
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              placeholder="Cole aqui os requisitos e responsabilidades para que a IA analise a aderência ao seu perfil..."
              className="w-full p-3 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
            >
              <Plus className="w-4 h-4" />
              <span>Cadastrar Vaga</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
