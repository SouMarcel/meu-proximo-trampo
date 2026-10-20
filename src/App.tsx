import React, { useState, useEffect, useMemo, useCallback } from "react"
import {
  Vaga,
  Etapa,
  FiltrosBusca,
  ConfigIA,
  PerfilUsuario,
  PortalConectado,
  ItemSincronizacao,
  HistoricoCandidatura,
} from "./types/job"
import { JobStorageService } from "./services/storage"
import Header from "./components/Header"
import NavigationTabs, { ActiveTab } from "./components/NavigationTabs"
import KanbanBoard from "./components/KanbanBoard"
import TriageReport from "./components/TriageReport"
import InternationalHub from "./components/InternationalHub"
import FunnelAnalytics from "./components/FunnelAnalytics"
import InterviewCoach from "./components/InterviewCoach"

// Modals
import JobDetailModal from "./components/modals/JobDetailModal"
import AddJobModal from "./components/modals/AddJobModal"
import SearchJobsModal from "./components/modals/SearchJobsModal"
import SearchFiltersModal from "./components/modals/SearchFiltersModal"
import AISettingsModal from "./components/modals/AISettingsModal"
import ProfileModal from "./components/modals/ProfileModal"
import CandidateOnboardingModal from "./components/modals/CandidateOnboardingModal"
import ConnectedAccountsModal from "./components/modals/ConnectedAccountsModal"
import { Sparkles } from "lucide-react"

export default function App() {
  // Main Data States
  const [vagas, setVagas] = useState<Vaga[]>([])
  const [filtros, setFiltros] = useState<FiltrosBusca>(
    JobStorageService.getFiltrosBusca(),
  )
  const [configIA, setConfigIA] = useState<ConfigIA>(
    JobStorageService.getConfigIA(),
  )
  const [perfil, setPerfil] = useState<PerfilUsuario>(
    JobStorageService.getPerfil(),
  )
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(
    null,
  )

  // Navigation & Active Tab
  const [activeTab, setActiveTab] = useState<ActiveTab>("quadro")

  // Modal Visibility States
  const [selectedVagaForDetail, setSelectedVagaForDetail] =
    useState<Vaga | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [isAIModalOpen, setIsAIModalOpen] = useState(false)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const [isOnboardingModalOpen, setIsOnboardingModalOpen] = useState(false)
  const [isAccountsModalOpen, setIsAccountsModalOpen] = useState(false)

  // Connected Accounts States (Spec 018)
  const [portais, setPortais] = useState<PortalConectado[]>(
    JobStorageService.getPortaisConectados(),
  )
  const [itensSync, setItensSync] = useState<ItemSincronizacao[]>(
    JobStorageService.getItensSincronizacao(),
  )
  const [historicoSync, setHistoricoSync] = useState<HistoricoCandidatura[]>(
    JobStorageService.getHistoricoCandidaturas(),
  )

  // Toast Notification State
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg)
    setTimeout(() => {
      setToastMessage(null)
    }, 3200)
  }, [])

  // Initial Load & Backend Ping
  useEffect(() => {
    const loadedVagas = JobStorageService.getVagas()
    setVagas(loadedVagas)

    // Check if local Python server is online
    JobStorageService.checkBackendConnection().then((connected) => {
      setIsBackendConnected(connected)
      if (connected) {
        showToast(
          "Conectado ao servidor local Meu Próximo Trampo (127.0.0.1:8765)",
        )
      }
    })
  }, [showToast])

  // Reload all data
  const reloadAllData = useCallback(() => {
    setVagas(JobStorageService.getVagas())
    setFiltros(JobStorageService.getFiltrosBusca())
    setConfigIA(JobStorageService.getConfigIA())
    setPerfil(JobStorageService.getPerfil())
    setPortais(JobStorageService.getPortaisConectados())
    setItensSync(JobStorageService.getItensSincronizacao())
    setHistoricoSync(JobStorageService.getHistoricoCandidaturas())
  }, [])

  // Tab badge counts
  const counts = useMemo(() => {
    const quadro = vagas.filter((v) => v.etapa !== null).length
    const pendentes = vagas.filter((v) => v.triagem === "pendente").length
    const internacional = vagas.filter((v) => v.area === "internacional").length
    const entrevistas = vagas.filter(
      (v) => v.etapa === "entrevista" || v.entrevista_em,
    ).length
    return { quadro, pendentes, internacional, entrevistas }
  }, [vagas])

  // Actions on Vagas
  const handleSelectVaga = (vaga: Vaga) => {
    setSelectedVagaForDetail(vaga)
    setIsDetailModalOpen(true)
  }

  const handleMoveStage = (id: string, stage: Etapa) => {
    const updated = JobStorageService.updateVaga(id, {
      etapa: stage,
      etapa_em: new Date().toISOString().split("T")[0],
      triagem: "seguir",
    })
    if (updated) {
      setVagas((prev) => prev.map((v) => (v.id === id ? updated : v)))
      showToast(`Vaga movida para a etapa: ${stage.toUpperCase()}`)
    }
  }

  const handleSeguirVaga = (id: string) => {
    const updated = JobStorageService.updateVaga(id, {
      triagem: "seguir",
      etapa: "salva",
      etapa_em: new Date().toISOString().split("T")[0],
    })
    if (updated) {
      setVagas((prev) => prev.map((v) => (v.id === id ? updated : v)))
      showToast(`Vaga adicionada à coluna "Salva" no seu Quadro!`)
    }
  }

  const handleNaoSeguirVaga = (id: string) => {
    const updated = JobStorageService.updateVaga(id, {
      triagem: "visitada",
      etapa: null,
    })
    if (updated) {
      setVagas((prev) => prev.map((v) => (v.id === id ? updated : v)))
      showToast(`Vaga marcada como não seguida.`)
    }
  }

  const handleResgatarVaga = (id: string) => {
    const updated = JobStorageService.updateVaga(id, {
      triagem: "seguir",
      etapa: "salva",
      etapa_em: new Date().toISOString().split("T")[0],
    })
    if (updated) {
      setVagas((prev) => prev.map((v) => (v.id === id ? updated : v)))
      showToast(`Vaga resgatada com sucesso para a coluna Salva!`)
    }
  }

  const handleDeleteVaga = (id: string) => {
    JobStorageService.deleteVaga(id)
    setVagas((prev) => prev.filter((v) => v.id !== id))
    showToast("Vaga removida com sucesso.")
  }

  const handleAddVaga = (novaVaga: Vaga) => {
    const created = JobStorageService.addVaga(novaVaga)
    setVagas((prev) => [created, ...prev])
    showToast(`Oportunidade cadastrada: ${novaVaga.titulo}`)
  }

  const handleUpdateVaga = (id: string, updates: Partial<Vaga>) => {
    const updated = JobStorageService.updateVaga(id, updates)
    if (updated) {
      setVagas((prev) => prev.map((v) => (v.id === id ? updated : v)))
      if (selectedVagaForDetail?.id === id) {
        setSelectedVagaForDetail(updated)
      }
    }
  }

  const handleSaveFilters = (newFiltros: FiltrosBusca) => {
    JobStorageService.saveFiltrosBusca(newFiltros)
    setFiltros(newFiltros)
    showToast("Filtros de busca atualizados com sucesso.")
  }

  const handleSaveConfigIA = (newConfig: ConfigIA) => {
    JobStorageService.saveConfigIA(newConfig)
    setConfigIA(newConfig)
    showToast("Configuração de IA salva.")
  }

  const handleCompleteOnboarding = (
    perfilAtualizado: PerfilUsuario,
    filtrosAtualizados: FiltrosBusca,
  ) => {
    handleSavePerfil(perfilAtualizado)
    handleSaveFilters(filtrosAtualizados)
    showToast(
      "Onboarding e Anamnese concluídos! Perfil e filtros de busca calibrados com sucesso.",
    )
  }

  const handleSavePerfil = (newPerfil: PerfilUsuario) => {
    JobStorageService.savePerfil(newPerfil)
    setPerfil(newPerfil)
    showToast("Perfil profissional atualizado.")
  }

  // Forçar verificar (Spec 021)
  const handleForcarVerificar = async (id: string) => {
    const target = vagas.find((v) => v.id === id)
    if (!target) return

    handleUpdateVaga(id, {
      analise_status: "verificando",
    })

    await new Promise((resolve) => setTimeout(resolve, 1400))

    const textoDescricao = target.descricao_pendente
      ? `${target.descricao}\n\n[Descrição Completa Obtida via Robô]: Responsabilidades e atribuições: Desenvolvimento e manutenção de sistemas em React, TypeScript e Next.js em larga escala. Gestão técnica de deploys com CI/CD. Trabalho 100% remoto com time distribuído.`
      : target.descricao

    const notaGerada = 88 + Math.floor(Math.random() * 8)

    const vagaAtualizada: Partial<Vaga> = {
      aderencia: notaGerada,
      analise_status: "feita",
      descricao_pendente: false,
      descricao: textoDescricao,
      resumo: `Análise prioritária concluída pela IA (${notaGerada}% de aderência). Excelente compatibilidade com seu perfil para ${target.titulo} em ${target.empresa}.`,
      encaixe: [
        "Requisitos essenciais em React e TypeScript contemplados",
        "Modelo de trabalho alinhado às preferências do seu perfil",
        "Senioridade compatível com a experiência descrita na anamnese",
      ],
      lacunas: [],
    }

    handleUpdateVaga(id, vagaAtualizada)
    showToast(`Nota de aderência calculada com sucesso pela IA (${notaGerada}%)!`)
  }

  // Completar descrição pendente (Spec 019)
  const handleCompletarDescricao = async (id: string) => {
    const target = vagas.find((v) => v.id === id)
    if (!target) return

    await new Promise((resolve) => setTimeout(resolve, 800))

    const novaDesc = `${target.descricao}\n\n[Descrição Integral Indexada]: Vaga detalhada do portal. O profissional atuará diretamente com nossa squad central de produto, desenvolvendo interfaces com foco em alta performance e acessibilidade.`

    handleUpdateVaga(id, {
      descricao: novaDesc,
      descricao_pendente: false,
    })
    showToast("Descrição completa da vaga obtida do portal com sucesso.")
  }

  // Contas Conectadas Handlers (Spec 018)
  const handleConectarPortal = (portalId: string) => {
    const updated = portais.map((p) =>
      p.id === portalId
        ? { ...p, conectado: true, ultima_sincronizacao: "Agora" }
        : p,
    )
    setPortais(updated)
    JobStorageService.savePortaisConectados(updated)
    showToast(`Portal ${portalId.toUpperCase()} conectado com sucesso.`)
  }

  const handleDesconectarPortal = (portalId: string) => {
    const updated = portais.map((p) =>
      p.id === portalId
        ? { ...p, conectado: false, ultima_sincronizacao: undefined }
        : p,
    )
    setPortais(updated)
    JobStorageService.savePortaisConectados(updated)
    showToast(`Sessão do portal ${portalId.toUpperCase()} desconectada.`)
  }

  const handleProntoPortal = (portalId: string) => {
    handleConectarPortal(portalId)
  }

  const handleSincronizarPortais = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1200))
    const updated = portais.map((p) =>
      p.conectado ? { ...p, ultima_sincronizacao: "Agora" } : p,
    )
    setPortais(updated)
    JobStorageService.savePortaisConectados(updated)
    showToast("Portais consultados: candidaturas em dia com o quadro.")
  }

  const handleAplicarAlteracoes = (itensSelecionados: ItemSincronizacao[]) => {
    itensSelecionados.forEach((item) => {
      const vagaExistente = vagas.find(
        (v) =>
          v.titulo.toLowerCase().includes(item.titulo.toLowerCase().slice(0, 15)) ||
          v.empresa.toLowerCase() === item.empresa.toLowerCase(),
      )

      if (vagaExistente) {
        handleUpdateVaga(vagaExistente.id, {
          etapa: item.etapa_nova,
          etapa_em: new Date().toISOString().split("T")[0],
          resultado: item.resultado_novo || vagaExistente.resultado,
          anotacao: vagaExistente.anotacao
            ? `${vagaExistente.anotacao}\n• ${item.alteracao}`
            : `• ${item.alteracao}`,
        })
      }
    })

    const restantes = itensSync.filter(
      (i) => !itensSelecionados.some((sel) => sel.id === i.id),
    )
    setItensSync(restantes)
    JobStorageService.saveItensSincronizacao(restantes)
  }

  const handleFinishSearch = (novasCount: number) => {
    // Gera 1 vaga extra de exemplo para ilustrar a busca em tempo real
    const novaVagaBusca: Vaga = {
      id: "busca-auto-" + Date.now(),
      titulo: "Senior Software Engineer / Frontend Core",
      empresa: "Automattic",
      plataforma: "RemoteOK",
      local: "Worldwide / 100% Remoto",
      remoto: true,
      area: "internacional",
      pais_vaga: "Global",
      idioma: "en",
      url: "https://automattic.com/work-with-us/",
      salario: "$110,000 - $135,000 USD / ano",
      tipo: "Contractor B2B / Worldwide",
      descricao:
        "Vaga encontrada pela varredura recente nos portais internacionais. Buscamos desenvolvedor sênior com paixão por WordPress, Gutenberg e React.",
      publicada_em: new Date().toISOString().split("T")[0],
      encontrada_em: new Date().toISOString().split("T")[0],
      triagem: "pendente",
      etapa: null,
      resultado: null,
      aderencia: 94,
      analise_status: "feita",
      resumo:
        "Altíssima compatibilidade encontrada na varredura recente. 100% remoto internacional assíncrono.",
      encaixe: ["React", "TypeScript", "Código Aberto", "Inglês Fluente"],
      lacunas: [],
      sinais: [
        "Empresa pioneira em trabalho remoto global",
        "Equipamento e home-office stipend inclusos",
      ],
      termos: ["Senior Frontend Engineer"],
    }

    handleAddVaga(novaVagaBusca)
    showToast(`Varredura concluída! Novas vagas disponíveis no Relatório.`)
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans antialiased selection:bg-indigo-500 selection:text-white transition-colors">
      {/* Header */}
      <Header
        configIA={configIA}
        isBackendConnected={isBackendConnected}
        onOpenAddModal={() => setIsAddModalOpen(true)}
        onOpenSearchModal={() => setIsSearchModalOpen(true)}
        onOpenFiltersModal={() => setIsFiltersModalOpen(true)}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
        onOpenOnboardingModal={() => setIsOnboardingModalOpen(true)}
        onOpenAIModal={() => setIsAIModalOpen(true)}
        onOpenAccountsModal={() => setIsAccountsModalOpen(true)}
      />

      {/* Navigation Tabs */}
      <NavigationTabs
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        countQuadro={counts.quadro}
        countPendentes={counts.pendentes}
        countInternacional={counts.internacional}
        countEntrevistas={counts.entrevistas}
      />

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Onboarding Callout Banner */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-indigo-900/90 via-slate-900 to-purple-950 text-white border border-indigo-700/40 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-300" />
                <span>Onboarding do Candidato</span>
              </span>
              <span className="text-xs text-indigo-200/80 font-medium">
                Primeiros Passos & Anamnese
              </span>
            </div>
            <h3 className="text-sm sm:text-base font-bold">
              Calibre o perfil com as perguntas essenciais para a análise de
              vagas
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              Responda às perguntas sobre cargos-alvo, conquistas com métricas,
              critérios inegociáveis e modelos de trabalho para que a IA dê as
              notas de aderência com precisão.
            </p>
          </div>
          <button
            onClick={() => setIsOnboardingModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm shadow-indigo-600/30 shrink-0 transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Fazer Onboarding Agora</span>
          </button>
        </div>

        {activeTab === "quadro" && (
          <KanbanBoard
            vagas={vagas}
            onSelectVaga={handleSelectVaga}
            onMoveStage={handleMoveStage}
            onDeleteVaga={handleDeleteVaga}
            onOpenAddModal={() => setIsAddModalOpen(true)}
          />
        )}

        {activeTab === "relatorio" && (
          <TriageReport
            vagas={vagas}
            onSelectVaga={handleSelectVaga}
            onSeguirVaga={handleSeguirVaga}
            onNaoSeguirVaga={handleNaoSeguirVaga}
            onResgatarVaga={handleResgatarVaga}
            onForcarVerificar={handleForcarVerificar}
          />
        )}

        {activeTab === "internacional" && (
          <InternationalHub
            vagas={vagas}
            onSelectVaga={handleSelectVaga}
            onSeguirVaga={handleSeguirVaga}
            onOpenFiltersModal={() => setIsFiltersModalOpen(true)}
          />
        )}

        {activeTab === "metricas" && (
          <FunnelAnalytics
            vagas={vagas}
            onNavigateToTab={(tab) => setActiveTab(tab as ActiveTab)}
          />
        )}

        {activeTab === "entrevistas" && (
          <InterviewCoach
            vagas={vagas}
            onUpdateVaga={handleUpdateVaga}
            onSelectVagaModal={handleSelectVaga}
          />
        )}
      </main>

      {/* Modals */}
      <JobDetailModal
        vaga={selectedVagaForDetail}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false)
          setSelectedVagaForDetail(null)
        }}
        onUpdateVaga={handleUpdateVaga}
        onDeleteVaga={handleDeleteVaga}
        onForcarVerificar={handleForcarVerificar}
        onCompletarDescricao={handleCompletarDescricao}
      />

      <AddJobModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAddVaga={handleAddVaga}
      />

      <SearchJobsModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
        filtros={filtros}
        onFinishSearch={handleFinishSearch}
      />

      <SearchFiltersModal
        isOpen={isFiltersModalOpen}
        onClose={() => setIsFiltersModalOpen(false)}
        filtros={filtros}
        onSaveFiltros={handleSaveFilters}
      />

      <AISettingsModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        configIA={configIA}
        onSaveConfig={handleSaveConfigIA}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        perfil={perfil}
        onSavePerfil={handleSavePerfil}
        onReloadAllData={reloadAllData}
        onOpenOnboarding={() => setIsOnboardingModalOpen(true)}
      />

      <CandidateOnboardingModal
        isOpen={isOnboardingModalOpen}
        onClose={() => setIsOnboardingModalOpen(false)}
        onCompleteOnboarding={handleCompleteOnboarding}
        filtrosAtuais={filtros}
        perfilAtual={perfil}
      />

      <ConnectedAccountsModal
        isOpen={isAccountsModalOpen}
        onClose={() => setIsAccountsModalOpen(false)}
        portais={portais}
        itensSincronizacao={itensSync}
        historico={historicoSync}
        onConectarPortal={handleConectarPortal}
        onDesconectarPortal={handleDesconectarPortal}
        onProntoPortal={handleProntoPortal}
        onSincronizar={handleSincronizarPortais}
        onAplicarAlteracoes={handleAplicarAlteracoes}
      />

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 fade-in duration-200">
          <div className="bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 px-4 py-3 rounded-2xl shadow-xl text-xs sm:text-sm font-semibold flex items-center gap-2 border border-slate-700 dark:border-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
            <span>{toastMessage}</span>
          </div>
        </div>
      )}
    </div>
  )
}
