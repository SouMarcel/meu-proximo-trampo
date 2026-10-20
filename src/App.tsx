import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
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
import { ApiService, PatchVagaPayload } from "./services/api"
import { ScreenPreferencesService } from "./services/storage"
import {
  MOCK_VAGAS,
  MOCK_FILTROS_BUSCA,
  MOCK_CONFIG_IA,
  MOCK_PERFIL,
  MOCK_PORTAIS_CONECTADOS,
  MOCK_ITENS_SINCRONIZACAO,
  MOCK_HISTORICO_CANDIDATURAS,
} from "./services/mockData"
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
import { Sparkles, AlertTriangle, RefreshCw } from "lucide-react"

export default function App() {
  // Main Data States
  const [vagas, setVagas] = useState<Vaga[]>([])
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false)
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(null)
  const [backendVersao, setBackendVersao] = useState<number>(0)
  const backendVersaoRef = useRef<number>(0)

  // Status de verificação e falhas vindos de /api/versao
  const [verificandoIds, setVerificandoIds] = useState<string[]>([])
  const [falhasMap, setFalhasMap] = useState<Record<string, string>>({})
  const [analisandoAuto, setAnalisandoAuto] = useState<boolean>(false)
  const [erroIA, setErroIA] = useState<string | null>(null)

  // Outros estados da ferramenta (serão integrados conforme a ordem)
  const [filtros, setFiltros] = useState<FiltrosBusca>(MOCK_FILTROS_BUSCA)
  const [configIA, setConfigIA] = useState<ConfigIA>(MOCK_CONFIG_IA)
  const [perfil, setPerfil] = useState<PerfilUsuario>(MOCK_PERFIL)
  const [portais, setPortais] = useState<PortalConectado[]>(MOCK_PORTAIS_CONECTADOS)
  const [itensSync, setItensSync] = useState<ItemSincronizacao[]>(MOCK_ITENS_SINCRONIZACAO)
  const [historicoSync, setHistoricoSync] = useState<HistoricoCandidatura[]>(MOCK_HISTORICO_CANDIDATURAS)

  // Navegação e aba ativa (preferência de tela)
  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    return (ScreenPreferencesService.getActiveTab("relatorio") as ActiveTab) || "relatorio"
  })

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab)
    ScreenPreferencesService.setActiveTab(tab)
  }

  // Modais
  const [selectedVagaForDetail, setSelectedVagaForDetail] = useState<Vaga | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [isAIModalOpen, setIsAIModalOpen] = useState(false)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const [isOnboardingModalOpen, setIsOnboardingModalOpen] = useState(false)
  const [isAccountsModalOpen, setIsAccountsModalOpen] = useState(false)

  // Toast Notification State
  const [toast, setToast] = useState<{ message: string; type?: "info" | "erro" } | null>(null)

  const showToast = useCallback((message: string, type: "info" | "erro" = "info") => {
    setToast({ message, type })
    setTimeout(() => {
      setToast(null)
    }, 4000)
  }, [])

  // Carrega vagas da API real
  const carregarVagasDoServidor = useCallback(async () => {
    try {
      const res = await ApiService.getVagas()
      setVagas(res.vagas || [])
      setBackendVersao(res.versao)
      backendVersaoRef.current = res.versao
    } catch (err: any) {
      showToast(err?.message || "Erro ao obter vagas do servidor.", "erro")
    }
  }, [showToast])

  // Conferência periódica do servidor via GET /api/versao
  const conferirServidor = useCallback(async () => {
    if (typeof document !== "undefined" && document.hidden) return
    try {
      const vRes = await ApiService.getVersao()
      const estavaOffline = isDemoMode || !isBackendConnected
      setIsBackendConnected(true)
      setIsDemoMode(false)
      setVerificandoIds(vRes.verificando || [])
      setFalhasMap(vRes.falhas || {})
      setAnalisandoAuto(!!vRes.analisando)
      setErroIA(vRes.ia_erro || null)

      // Se estava em modo demonstração ou a versão do banco aumentou, recarrega vagas
      if (estavaOffline || vRes.versao !== backendVersaoRef.current) {
        backendVersaoRef.current = vRes.versao
        setBackendVersao(vRes.versao)
        await carregarVagasDoServidor()
      }
    } catch {
      // Servidor não respondeu: entra em Modo demonstração
      setIsBackendConnected(false)
      if (!isDemoMode) {
        setIsDemoMode(true)
        // No modo demonstração com servidor fora do ar, exibe os dados de exemplo em memória
        setVagas(MOCK_VAGAS)
      }
    }
  }, [isDemoMode, isBackendConnected, carregarVagasDoServidor])

  // Inicialização e polling periódico
  useEffect(() => {
    let mounted = true

    ApiService.getVersao()
      .then(async (vRes) => {
        if (!mounted) return
        setIsBackendConnected(true)
        setIsDemoMode(false)
        backendVersaoRef.current = vRes.versao
        setBackendVersao(vRes.versao)
        setVerificandoIds(vRes.verificando || [])
        setFalhasMap(vRes.falhas || {})
        setAnalisandoAuto(!!vRes.analisando)
        setErroIA(vRes.ia_erro || null)

        const vagasRes = await ApiService.getVagas()
        if (!mounted) return
        setVagas(vagasRes.vagas || [])
        showToast("Conectado ao servidor local (dash/servidor.py)")
      })
      .catch(() => {
        if (!mounted) return
        setIsBackendConnected(false)
        setIsDemoMode(true)
        setVagas(MOCK_VAGAS)
      })

    const intervalId = setInterval(() => {
      conferirServidor()
    }, 4000)

    return () => {
      mounted = false
      clearInterval(intervalId)
    }
  }, [conferirServidor, showToast])

  // Vagas com status de verificação e falhas mesclados em tempo real
  const vagasComStatus = useMemo(() => {
    return vagas.map((v) => {
      const isVerificando = verificandoIds.includes(v.id)
      const falha = falhasMap[v.id]
      if (isVerificando) {
        return { ...v, analise_status: "verificando" as const }
      }
      if (falha) {
        return { ...v, analise_status: "falha" as const, motivo_falha: falha }
      }
      return v
    })
  }, [vagas, verificandoIds, falhasMap])

  // Contadores das abas
  const counts = useMemo(() => {
    const quadro = vagasComStatus.filter((v) => v.etapa !== null).length
    const pendentes = vagasComStatus.filter((v) => v.triagem === "pendente").length
    const internacional = vagasComStatus.filter((v) => v.area === "internacional").length
    const entrevistas = vagasComStatus.filter(
      (v) => v.etapa === "entrevista" || v.entrevista_em,
    ).length
    return { quadro, pendentes, internacional, entrevistas }
  }, [vagasComStatus])

  // Ações no Relatório de Vagas (Ligação real com a API)
  const handleSelectVaga = (vaga: Vaga) => {
    setSelectedVagaForDetail(vaga)
    setIsDetailModalOpen(true)
  }

  // 1. Seguir com a Vaga (PATCH /api/vagas/{id}) -> Manda para a coluna Salva
  const handleSeguirVaga = async (id: string) => {
    const hojeStr = new Date().toISOString().split("T")[0]
    if (isDemoMode) {
      setVagas((prev) =>
        prev.map((v) =>
          v.id === id
            ? { ...v, triagem: "seguir", etapa: "salva", etapa_em: hojeStr, triada_em: hojeStr }
            : v,
        ),
      )
      showToast('Vaga adicionada à coluna "Salva" no seu Quadro!')
      return
    }

    try {
      const res = await ApiService.patchVaga(id, {
        triagem: "seguir",
        etapa: "salva",
        etapa_em: hojeStr,
        triada_em: hojeStr,
      })
      setVagas((prev) => prev.map((v) => (v.id === id ? res.vaga : v)))
      showToast('Vaga adicionada à coluna "Salva" no seu Quadro!')
    } catch (err: any) {
      showToast(err?.message || "Não foi possível seguir com a vaga.", "erro")
    }
  }

  // 2. Não Seguir (PATCH /api/vagas/{id}) -> Marca como visitada
  const handleNaoSeguirVaga = async (id: string) => {
    if (isDemoMode) {
      setVagas((prev) =>
        prev.map((v) => (v.id === id ? { ...v, triagem: "visitada", etapa: null } : v)),
      )
      showToast("Vaga marcada como não seguida.")
      return
    }

    try {
      const res = await ApiService.patchVaga(id, {
        triagem: "visitada",
        etapa: null,
      })
      setVagas((prev) => prev.map((v) => (v.id === id ? res.vaga : v)))
      showToast("Vaga marcada como não seguida.")
    } catch (err: any) {
      showToast(err?.message || "Não foi possível marcar a vaga como visitada.", "erro")
    }
  }

  // 3. Resgatar Vaga (PATCH /api/vagas/{id}) -> Manda de Fora dos Critérios para Salva
  const handleResgatarVaga = async (id: string) => {
    const hojeStr = new Date().toISOString().split("T")[0]
    if (isDemoMode) {
      setVagas((prev) =>
        prev.map((v) =>
          v.id === id
            ? { ...v, triagem: "seguir", etapa: "salva", etapa_em: hojeStr, triada_em: hojeStr }
            : v,
        ),
      )
      showToast("Vaga resgatada com sucesso para a coluna Salva!")
      return
    }

    try {
      const res = await ApiService.patchVaga(id, {
        triagem: "seguir",
        etapa: "salva",
        etapa_em: hojeStr,
        triada_em: hojeStr,
      })
      setVagas((prev) => prev.map((v) => (v.id === id ? res.vaga : v)))
      showToast("Vaga resgatada com sucesso para a coluna Salva!")
    } catch (err: any) {
      showToast(err?.message || "Não foi possível resgatar a vaga.", "erro")
    }
  }

  // 4. Forçar verificar (POST /api/vagas/{id}/analisar)
  // Regra: "Ações que gravam, apagam ou chamam a IA pedem confirmação, como hoje."
  const handleForcarVerificar = async (id: string) => {
    const confirmou = window.confirm("Pedir a análise desta vaga para a IA agora?")
    if (!confirmou) return

    if (isDemoMode) {
      setVerificandoIds((prev) => [...prev, id])
      showToast("Verificando a vaga: a nota chega em instantes.")
      setTimeout(() => {
        setVerificandoIds((prev) => prev.filter((x) => x !== id))
        setVagas((prev) =>
          prev.map((v) =>
            v.id === id
              ? {
                  ...v,
                  aderencia: 88,
                  analise_status: "feita",
                  descricao_pendente: false,
                  resumo: "Análise concluída com sucesso pela IA.",
                }
              : v,
          ),
        )
      }, 1500)
      return
    }

    try {
      const res = await ApiService.forcarAnalisar(id)
      setVerificandoIds(res.verificando || [id])
      setFalhasMap((prev) => {
        const novo = { ...prev }
        delete novo[id]
        return novo
      })
      showToast("Verificando a vaga: a nota chega em alguns minutos.")
    } catch (err: any) {
      if (err?.dados?.sem_ia) {
        showToast("Para dar nota, ligue uma IA (botão IA, no topo).", "erro")
      } else {
        showToast(err?.message || "Não foi possível iniciar a análise da vaga.", "erro")
      }
    }
  }

  // 5. Excluir vaga (DELETE /api/vagas/{id})
  // Regra: "Ações que gravam, apagam ou chamam a IA pedem confirmação, como hoje."
  const handleDeleteVaga = async (id: string) => {
    const confirmou = window.confirm("Tem certeza que deseja excluir esta vaga do acompanhamento?")
    if (!confirmou) return

    if (isDemoMode) {
      setVagas((prev) => prev.filter((v) => v.id !== id))
      showToast("Vaga removida com sucesso.")
      return
    }

    try {
      await ApiService.deleteVaga(id)
      setVagas((prev) => prev.filter((v) => v.id !== id))
      showToast("Vaga removida com sucesso.")
    } catch (err: any) {
      showToast(err?.message || "Não foi possível excluir a vaga.", "erro")
    }
  }

  // 6. Atualizar vaga (PATCH /api/vagas/{id})
  const handleUpdateVaga = async (id: string, updates: Partial<Vaga>) => {
    if (isDemoMode) {
      setVagas((prev) =>
        prev.map((v) => {
          if (v.id === id) {
            const updated = { ...v, ...updates }
            if (selectedVagaForDetail?.id === id) {
              setSelectedVagaForDetail(updated)
            }
            return updated
          }
          return v
        }),
      )
      return
    }

    // Filtra apenas campos editáveis pelo usuário suportados pela rota PATCH /api/vagas/{id}
    const payload: PatchVagaPayload = {}
    if ("triagem" in updates) payload.triagem = updates.triagem
    if ("etapa" in updates) payload.etapa = updates.etapa
    if ("resultado" in updates) payload.resultado = updates.resultado
    if ("etapa_em" in updates) payload.etapa_em = updates.etapa_em
    if ("triada_em" in updates) payload.triada_em = updates.triada_em
    if ("anotacao" in updates) payload.anotacao = updates.anotacao
    if ("kit" in updates) payload.kit = updates.kit
    if ("lembretes" in updates) payload.lembretes = updates.lembretes
    if ("entrevista_em" in updates) payload.entrevista_em = updates.entrevista_em
    if ("email_candidatura" in updates) payload.email_candidatura = updates.email_candidatura
    if ("assunto_candidatura" in updates) payload.assunto_candidatura = updates.assunto_candidatura

    try {
      const res = await ApiService.patchVaga(id, payload)
      setVagas((prev) => prev.map((v) => (v.id === id ? res.vaga : v)))
      if (selectedVagaForDetail?.id === id) {
        setSelectedVagaForDetail(res.vaga)
      }
    } catch (err: any) {
      showToast(err?.message || "Não foi possível salvar alterações da vaga.", "erro")
    }
  }

  // Mover etapa no quadro
  const handleMoveStage = async (id: string, stage: Etapa) => {
    const hojeStr = new Date().toISOString().split("T")[0]
    await handleUpdateVaga(id, {
      etapa: stage,
      etapa_em: hojeStr,
      triagem: "seguir",
    })
    showToast(`Vaga movida para a etapa: ${stage.toUpperCase()}`)
  }

  // Ações de modais ainda em modo demonstração (serão integrados na sequência)
  const handleAddVaga = (novaVaga: Vaga) => {
    setVagas((prev) => [novaVaga, ...prev])
    showToast(`Oportunidade cadastrada: ${novaVaga.titulo}`)
  }

  const handleSaveFilters = (newFiltros: FiltrosBusca) => {
    setFiltros(newFiltros)
    showToast("Filtros de busca atualizados.")
  }

  const handleSaveConfigIA = (newConfig: ConfigIA) => {
    setConfigIA(newConfig)
    showToast("Configuração de IA salva.")
  }

  const handleCompleteOnboarding = (
    perfilAtualizado: PerfilUsuario,
    filtrosAtualizados: FiltrosBusca,
  ) => {
    setPerfil(perfilAtualizado)
    setFiltros(filtrosAtualizados)
    showToast("Onboarding concluído! Perfil e filtros calibrados com sucesso.")
  }

  const handleSavePerfil = (newPerfil: PerfilUsuario) => {
    setPerfil(newPerfil)
    showToast("Perfil profissional atualizado.")
  }

  const handleCompletarDescricao = async (id: string) => {
    showToast("Completando descrição da vaga...")
  }

  const reloadAllData = () => {
    conferirServidor()
  }

  const handleConectarPortal = (portalId: string) => {
    setPortais((prev) =>
      prev.map((p) => (p.id === portalId ? { ...p, conectado: true } : p)),
    )
    showToast(`Conta conectada com sucesso.`)
  }

  const handleDesconectarPortal = (portalId: string) => {
    const confirmou = window.confirm("Deseja realmente desconectar esta conta?")
    if (!confirmou) return
    setPortais((prev) =>
      prev.map((p) => (p.id === portalId ? { ...p, conectado: false } : p)),
    )
    showToast(`Conta desconectada.`)
  }

  const handleProntoPortal = (portalId: string) => {
    handleConectarPortal(portalId)
  }

  const handleSincronizarPortais = async () => {
    showToast("Portais consultados: candidaturas em dia com o quadro.")
  }

  const handleAplicarAlteracoes = (itensSelecionados: ItemSincronizacao[]) => {
    showToast(`${itensSelecionados.length} alterações aplicadas ao quadro.`)
  }

  const handleFinishSearch = () => {
    conferirServidor()
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans antialiased selection:bg-indigo-500 selection:text-white transition-colors">
      {/* Aviso fixo e visível de Modo demonstração quando servidor não for encontrado */}
      {isDemoMode && (
        <div className="sticky top-0 z-50 bg-amber-500 text-slate-950 font-semibold px-4 py-2.5 text-center text-xs sm:text-sm shadow-md flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-slate-950" />
          <span>Modo demonstração: dados de exemplo, servidor não encontrado</span>
          <button
            onClick={conferirServidor}
            className="ml-2 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-slate-950 text-white text-xs hover:bg-slate-800 transition font-medium"
            title="Tentar conectar ao servidor local"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Tentar novamente</span>
          </button>
        </div>
      )}

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
        onChangeTab={handleTabChange}
        countQuadro={counts.quadro}
        countPendentes={counts.pendentes}
        countInternacional={counts.internacional}
        countEntrevistas={counts.entrevistas}
      />

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Onboarding Callout Banner */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-indigo-900/90 via-slate-900 to-purple-950 text-white border border-indigo-700/40 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
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
              Calibre o perfil com as perguntas essenciais para a análise de vagas
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              Responda às perguntas sobre cargos-alvo, conquistas com métricas,
              critérios inegociáveis e modelos de trabalho para que a IA dê as
              notas de aderência com precisão.
            </p>
          </div>
          <button
            onClick={() => setIsOnboardingModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs shadow-indigo-600/30 shrink-0 transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Fazer Onboarding Agora</span>
          </button>
        </div>

        {activeTab === "quadro" && (
          <KanbanBoard
            vagas={vagasComStatus}
            onSelectVaga={handleSelectVaga}
            onMoveStage={handleMoveStage}
            onDeleteVaga={handleDeleteVaga}
            onOpenAddModal={() => setIsAddModalOpen(true)}
          />
        )}

        {activeTab === "relatorio" && (
          <TriageReport
            vagas={vagasComStatus}
            onSelectVaga={handleSelectVaga}
            onSeguirVaga={handleSeguirVaga}
            onNaoSeguirVaga={handleNaoSeguirVaga}
            onResgatarVaga={handleResgatarVaga}
            onForcarVerificar={handleForcarVerificar}
          />
        )}

        {activeTab === "internacional" && (
          <InternationalHub
            vagas={vagasComStatus}
            onSelectVaga={handleSelectVaga}
            onSeguirVaga={handleSeguirVaga}
            onOpenFiltersModal={() => setIsFiltersModalOpen(true)}
          />
        )}

        {activeTab === "metricas" && (
          <FunnelAnalytics
            vagas={vagasComStatus}
            onNavigateToTab={(tab) => handleTabChange(tab as ActiveTab)}
          />
        )}

        {activeTab === "entrevistas" && (
          <InterviewCoach
            vagas={vagasComStatus}
            onUpdateVaga={handleUpdateVaga}
            onSelectVagaModal={handleSelectVaga}
          />
        )}
      </main>

      {/* Modais */}
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
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 fade-in duration-200">
          <div
            className={`px-4 py-3 rounded-2xl shadow-xl text-xs sm:text-sm font-semibold flex items-center gap-2 border ${
              toast.type === "erro"
                ? "bg-rose-950 text-rose-100 border-rose-800"
                : "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 border-slate-700 dark:border-slate-300"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full inline-block ${
                toast.type === "erro" ? "bg-rose-400" : "bg-emerald-400 animate-pulse"
              }`}
            />
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  )
}
