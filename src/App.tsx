import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import type {
  CamposEditaveis,
  Etapa,
  EstadoBusca,
  PlanoBusca,
  UltimaBusca,
  Vaga,
  Versao,
} from "./types/api"
import {
  FiltrosBusca,
  ConfigIA,
  PerfilUsuario,
  PortalConectado,
  ItemSincronizacao,
  HistoricoCandidatura,
} from "./types/job"
import { mensagemDeErro, ehErroApi } from "./services/api"
import * as vagasApi from "./services/api/vagas"
import * as buscaApi from "./services/api/busca"
import { ScreenPreferencesService } from "./services/storage"
import { areaDe, noRelatorio, noQuadro, hoje, horaDe } from "./utils/formatters"
import { naFila } from "./utils/filaVaga"
import { useConsulta } from "./hooks/useConsulta"
import { FerramentaProvider, useFerramenta, motivoSemGravar } from "./contexto/Ferramenta"
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
import AndamentoBusca from "./components/AndamentoBusca"
import UltimaBuscaLinha from "./components/UltimaBusca"
import CompletarDescricoes from "./components/CompletarDescricoes"

// Modals
import JobDetailModal from "./components/modals/JobDetailModal"
import AddJobModal from "./components/modals/AddJobModal"
import SearchJobsModal from "./components/modals/SearchJobsModal"
import SearchFiltersModal from "./components/modals/SearchFiltersModal"
import AISettingsModal from "./components/modals/AISettingsModal"
import ProfileModal from "./components/modals/ProfileModal"
import CandidateOnboardingModal from "./components/modals/CandidateOnboardingModal"
import ConnectedAccountsModal from "./components/modals/ConnectedAccountsModal"
import { Sparkles, AlertTriangle, RefreshCw, WifiOff } from "lucide-react"

export default function App() {
  const [isAIModalOpen, setIsAIModalOpen] = useState(false)
  const abrirPainelIA = useCallback(() => setIsAIModalOpen(true), [])
  return (
    <FerramentaProvider onAbrirPainelIA={abrirPainelIA}>
      <Pagina isAIModalOpen={isAIModalOpen} setIsAIModalOpen={setIsAIModalOpen} />
    </FerramentaProvider>
  )
}

/** A busca está rodando (ou acabou de terminar com nota): consulta o andamento a cada 2 s (dash/API.md §1). */
function buscaAtiva(e: EstadoBusca | null, ate: number): boolean {
  if (!e) return false
  if (buscaApi.SITUACOES_ATIVAS.includes(e.situacao) || e.analise?.rodando || Date.now() < ate) return true
  const fim = Date.parse(e.fim || "")
  return e.situacao === "concluida" && Boolean(e.resumo?.com_nota) && !isNaN(fim) && Date.now() - fim < 20000
}

function Pagina({
  isAIModalOpen,
  setIsAIModalOpen,
}: {
  isAIModalOpen: boolean
  setIsAIModalOpen: (v: boolean) => void
}) {
  const ferramenta = useFerramenta()
  const { servidor, setServidor, podeGravar, podeAlterar, registrarPodeAlterar, tratarErro, recarregarIA } =
    ferramenta

  // Dados do servidor
  const [vagas, setVagas] = useState<Vaga[]>([])
  const [versaoInfo, setVersaoInfo] = useState<Versao | null>(null)
  const versaoRef = useRef<number>(-1)
  const [ultimaBusca, setUltimaBusca] = useState<UltimaBusca | null>(null)
  const [estadoBusca, setEstadoBuscaState] = useState<EstadoBusca | null>(null)
  const estadoBuscaRef = useRef<EstadoBusca | null>(null)
  const setEstadoBusca = useCallback((e: EstadoBusca | null | ((x: EstadoBusca | null) => EstadoBusca | null)) => {
    setEstadoBuscaState((antes) => {
      const novo = typeof e === "function" ? e(antes) : e
      estadoBuscaRef.current = novo
      return novo
    })
  }, [])
  const [planoBusca, setPlanoBusca] = useState<PlanoBusca | null>(null)
  const buscaAteRef = useRef(0) // segue consultando por 20 s depois de uma ação
  const [painelBuscaFechado, setPainelBuscaFechado] = useState("")
  const [semIA, setSemIA] = useState<Record<string, boolean>>({})
  const [pendentesVersao, setPendentesVersao] = useState(0) // pede ao "Completar descrições" para reler

  // Telas ainda simuladas (passam a usar o servidor nas próximas histórias da spec 025)
  const [filtros, setFiltros] = useState<FiltrosBusca>(MOCK_FILTROS_BUSCA)
  const [configIA, setConfigIA] = useState<ConfigIA>(MOCK_CONFIG_IA)
  const [perfil, setPerfil] = useState<PerfilUsuario>(MOCK_PERFIL)
  const [portais, setPortais] = useState<PortalConectado[]>(MOCK_PORTAIS_CONECTADOS)
  const [itensSync] = useState<ItemSincronizacao[]>(MOCK_ITENS_SINCRONIZACAO)
  const [historicoSync] = useState<HistoricoCandidatura[]>(MOCK_HISTORICO_CANDIDATURAS)

  // Navegação e aba ativa (preferência de tela)
  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    return (ScreenPreferencesService.getActiveTab("relatorio") as ActiveTab) || "relatorio"
  })
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab)
    ScreenPreferencesService.setActiveTab(tab)
  }

  // Modais
  const [detalheId, setDetalheId] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const [isOnboardingModalOpen, setIsOnboardingModalOpen] = useState(false)
  const [isAccountsModalOpen, setIsAccountsModalOpen] = useState(false)

  // Avisos
  const [toast, setToast] = useState<{ message: string; type?: "info" | "erro" } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const showToast = useCallback((message: string, type: "info" | "erro" = "info") => {
    setToast({ message, type })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), type === "erro" ? 7000 : 4000)
  }, [])
  const avisarErro = useCallback(
    (e: unknown, padrao: string) => {
      tratarErro(e)
      showToast(mensagemDeErro(e, padrao), "erro")
    },
    [tratarErro, showToast],
  )

  // ---------- leitura do servidor ----------

  const carregarVagas = useCallback(async () => {
    const [lista, ultima] = await Promise.all([vagasApi.listar(), vagasApi.ultimaBusca()])
    setVagas(lista.vagas || [])
    versaoRef.current = lista.versao
    setUltimaBusca(ultima.busca)
  }, [])

  const consultarBusca = useCallback(async () => {
    try {
      const e = await buscaApi.estado()
      const antes = estadoBuscaRef.current
      estadoBuscaRef.current = e
      setEstadoBusca(e)
      // terminou: o relatório, as descrições pendentes e o intervalo mínimo mudam
      if (antes && buscaAtiva(antes, 0) && !buscaAtiva(e, buscaAteRef.current)) {
        carregarVagas().catch(() => undefined)
        buscaApi.plano().then(setPlanoBusca).catch(() => undefined)
        setPendentesVersao((n) => n + 1)
      }
      registrarPodeAlterar(e.pode_alterar)
    } catch {
      // sem resposta: o aviso de servidor fora vem da consulta da versão
    }
  }, [carregarVagas, registrarPodeAlterar])

  const carregarTudo = useCallback(async () => {
    await carregarVagas()
    recarregarIA()
    consultarBusca()
    buscaApi.plano().then(setPlanoBusca).catch(() => undefined)
  }, [carregarVagas, recarregarIA, consultarBusca])

  // Abertura: sem resposta do servidor, modo demonstração (dados de exemplo e nada é gravado).
  useEffect(() => {
    let ativo = true
    vagasApi
      .versao()
      .then(async (v) => {
        if (!ativo) return
        setVersaoInfo(v)
        await carregarTudo()
        if (ativo) setServidor("no_ar")
      })
      .catch(() => {
        if (!ativo) return
        setServidor("demo")
        setVagas(MOCK_VAGAS)
      })
    return () => {
      ativo = false
    }
  }, [carregarTudo, setServidor])

  // A cada 4 s: mudanças no banco, IA analisando, Forçar verificar, busca de outra origem, servidor no ar.
  const conferirServidor = useCallback(async () => {
    try {
      const v = await vagasApi.versao()
      setVersaoInfo(v)
      if (servidor !== "no_ar") {
        if (servidor === "demo") setVagas([])
        await carregarTudo()
        setServidor("no_ar")
        return
      }
      if (v.versao !== versaoRef.current) await carregarVagas()
      const sit = v.busca?.situacao
      if (sit && buscaApi.SITUACOES_ATIVAS.includes(sit) && !buscaAtiva(estadoBusca, buscaAteRef.current)) {
        consultarBusca()
      }
    } catch {
      if (servidor === "no_ar") setServidor("fora")
    }
  }, [servidor, carregarTudo, carregarVagas, setServidor, estadoBusca, consultarBusca])

  useConsulta(conferirServidor, 4000, servidor !== "conectando")
  useConsulta(consultarBusca, 2000, servidor === "no_ar" && buscaAtiva(estadoBusca, buscaAteRef.current))

  // ---------- telas ----------

  const vagasRelatorio = useMemo(
    () => vagas.filter((v) => noRelatorio(v) && areaDe(v) === "nacional"),
    [vagas],
  )
  const vagasInternacional = useMemo(
    () => vagas.filter((v) => noRelatorio(v) && areaDe(v) === "internacional"),
    [vagas],
  )
  const counts = useMemo(() => {
    return {
      quadro: vagas.filter(noQuadro).length,
      pendentes: vagasRelatorio.filter((v) => v.triagem === "pendente").length,
      internacional: vagasInternacional.filter((v) => v.triagem === "pendente").length,
      entrevistas: vagas.filter((v) => noQuadro(v) && (v.etapa === "entrevista" || v.entrevista_em)).length,
    }
  }, [vagas, vagasRelatorio, vagasInternacional])

  const vagaDetalhe = useMemo(() => vagas.find((v) => v.id === detalheId) || null, [vagas, detalheId])

  // Botão Buscar vagas: desligado durante uma busca, antes de proxima_em e sem poder gravar.
  const buscaRodando = Boolean(estadoBusca && buscaApi.SITUACOES_ATIVAS.includes(estadoBusca.situacao))
  const proximaBusca =
    planoBusca?.proxima_em && Date.parse(planoBusca.proxima_em) > Date.now() ? horaDe(planoBusca.proxima_em) : ""
  const motivoBuscaDesligada = !podeGravar
    ? motivoSemGravar(servidor, podeAlterar)
    : buscaRodando
      ? "Já há uma busca em andamento."
      : proximaBusca
        ? `Para os portais não bloquearem a busca, dá para buscar de novo a partir das ${proximaBusca}.`
        : ""

  // ---------- escritas (uma por vez por vaga; a vaga local vira a que o servidor devolve) ----------

  const trocarVaga = useCallback((nova: Vaga) => {
    setVagas((prev) => {
      const existe = prev.some((v) => v.id === nova.id)
      return existe ? prev.map((v) => (v.id === nova.id ? nova : v)) : [nova, ...prev]
    })
  }, [])

  const gravar = useCallback(
    async (id: string, campos: CamposEditaveis, sucesso?: string): Promise<boolean> => {
      if (!podeGravar) {
        showToast(motivoSemGravar(servidor, podeAlterar), "erro")
        return false
      }
      try {
        const res = await naFila(id, () => vagasApi.atualizar(id, campos))
        trocarVaga(res.vaga)
        if (sucesso) showToast(sucesso)
        return true
      } catch (e) {
        avisarErro(e, "Não deu para gravar a mudança na vaga.")
        return false
      }
    },
    [podeGravar, servidor, podeAlterar, showToast, trocarVaga, avisarErro],
  )

  const handleSeguirVaga = (id: string) =>
    gravar(
      id,
      { triagem: "seguir", etapa: "salva", etapa_em: hoje(), triada_em: hoje() },
      'Vaga no quadro, na coluna "Salva".',
    )

  const handleNaoSeguirVaga = (id: string) =>
    gravar(id, { triagem: "visitada", etapa: null, triada_em: hoje() }, "Vaga marcada como não seguida.")

  const handleVoltarTriagem = (id: string) =>
    gravar(
      id,
      { triagem: "pendente", etapa: null, resultado: null, triada_em: null },
      "Vaga de volta para Para decidir.",
    )

  const handleMarcarTodasNaoSeguidas = async (ids: string[]) => {
    let feitas = 0
    for (const id of ids) {
      if (await gravar(id, { triagem: "visitada", etapa: null, triada_em: hoje() })) feitas++
      else break
    }
    if (feitas) showToast(`${feitas} vaga(s) marcada(s) como não seguidas.`)
  }

  const handleForcarVerificar = async (id: string) => {
    if (!podeGravar) {
      showToast(motivoSemGravar(servidor, podeAlterar), "erro")
      return
    }
    setSemIA((prev) => {
      const novo = { ...prev }
      delete novo[id]
      return novo
    })
    try {
      const res = await vagasApi.analisar(id)
      setVersaoInfo((v) => (v ? { ...v, verificando: res.verificando || [id] } : v))
      showToast("Verificando a vaga: a nota chega em alguns minutos.")
    } catch (e) {
      if (ehErroApi(e) && e.dados?.sem_ia) {
        setSemIA((prev) => ({ ...prev, [id]: true }))
        showToast("Para dar nota, ligue uma IA (botão IA, no topo).", "erro")
        return
      }
      avisarErro(e, "Não deu para pedir a nota.")
      if (ehErroApi(e) && e.status === 409) carregarVagas().catch(() => undefined) // a vaga já ganhou nota
    }
  }

  // Remover do quadro (a confirmação, com segundo clique, fica no botão): a manual some; as outras saem do quadro.
  const handleDeleteVaga = async (id: string) => {
    if (!podeGravar) {
      showToast(motivoSemGravar(servidor, podeAlterar), "erro")
      return
    }
    try {
      await naFila(id, () => vagasApi.remover(id))
      setVagas((prev) =>
        prev.flatMap((v) =>
          v.id !== id
            ? [v]
            : v.origem === "manual"
              ? []
              : [{ ...v, triagem: "visitada" as const, etapa: null, resultado: null }],
        ),
      )
      if (detalheId === id) setDetalheId(null)
      showToast("Vaga removida do quadro.")
    } catch (e) {
      avisarErro(e, "Não deu para remover a vaga.")
    }
  }

  const handleUpdateVaga = (id: string, campos: CamposEditaveis, sucesso?: string) => gravar(id, campos, sucesso)

  const handleMoveStage = (id: string, etapa: Etapa) => {
    const campos: CamposEditaveis = { etapa, etapa_em: hoje() }
    if (etapa !== "encerrada") campos.resultado = null
    return gravar(id, campos)
  }

  const handleVagaAdicionada = (vaga: Vaga) => {
    trocarVaga(vaga)
    setPendentesVersao((n) => n + 1)
  }

  // ---------- busca ----------

  const handleBuscaIniciada = (e: EstadoBusca) => {
    setEstadoBusca(e)
    setPainelBuscaFechado("")
    buscaAteRef.current = Date.now() + 20000
    handleTabChange("relatorio")
  }

  const handleCancelarBusca = async () => {
    try {
      const e = await buscaApi.cancelar()
      setEstadoBusca(e)
      buscaAteRef.current = Date.now() + 20000
    } catch (e) {
      avisarErro(e, "Não deu para cancelar a busca.")
    }
  }

  const handleTentarNota = async () => {
    try {
      const r = await buscaApi.tentarNota()
      setEstadoBusca((e) => (e ? { ...e, analise: r.analise } : e))
      buscaAteRef.current = Date.now() + 20000
      showToast(r.analise.faltam ? "Pedindo a nota de novo." : "Nada esperando nota.")
    } catch (e) {
      avisarErro(e, "Não deu para pedir a nota de novo.")
    }
  }

  // ---------- telas ainda simuladas (próximas histórias da spec 025) ----------

  const handleSaveFilters = (newFiltros: FiltrosBusca) => {
    setFiltros(newFiltros)
    showToast("Filtros de busca atualizados.")
  }
  const handleSaveConfigIA = (newConfig: ConfigIA) => {
    setConfigIA(newConfig)
    showToast("Configuração de IA salva.")
  }
  const handleCompleteOnboarding = (perfilAtualizado: PerfilUsuario, filtrosAtualizados: FiltrosBusca) => {
    setPerfil(perfilAtualizado)
    setFiltros(filtrosAtualizados)
    showToast("Onboarding concluído! Perfil e filtros calibrados com sucesso.")
  }
  const handleSavePerfil = (newPerfil: PerfilUsuario) => {
    setPerfil(newPerfil)
    showToast("Perfil profissional atualizado.")
  }
  const handleConectarPortal = (portalId: string) => {
    setPortais((prev) => prev.map((p) => (p.id === portalId ? { ...p, conectado: true } : p)))
    showToast(`Conta conectada com sucesso.`)
  }
  const handleDesconectarPortal = (portalId: string) => {
    const confirmou = window.confirm("Deseja realmente desconectar esta conta?")
    if (!confirmou) return
    setPortais((prev) => prev.map((p) => (p.id === portalId ? { ...p, conectado: false } : p)))
    showToast(`Conta desconectada.`)
  }
  const handleSincronizarPortais = async () => {
    showToast("Portais consultados: candidaturas em dia com o quadro.")
  }
  const handleAplicarAlteracoes = (itensSelecionados: ItemSincronizacao[]) => {
    showToast(`${itensSelecionados.length} alterações aplicadas ao quadro.`)
  }

  const painelBusca =
    estadoBusca &&
    (estadoBusca.situacao !== "ociosa" || versaoInfo?.ia_erro) &&
    painelBuscaFechado !== (estadoBusca.inicio || "") + estadoBusca.situacao ? (
      <AndamentoBusca
        estado={estadoBusca}
        iaErro={versaoInfo?.ia_erro || null}
        onCancelar={handleCancelarBusca}
        onTentarNota={handleTentarNota}
        onFechar={() => setPainelBuscaFechado((estadoBusca.inicio || "") + estadoBusca.situacao)}
        onAbrirIA={() => setIsAIModalOpen(true)}
      />
    ) : null

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans antialiased selection:bg-indigo-500 selection:text-white transition-colors">
      {/* Modo demonstração: só quando o servidor não respondeu na abertura */}
      {servidor === "demo" && (
        <div className="sticky top-0 z-50 bg-amber-500 text-slate-950 font-semibold px-4 py-2.5 text-center text-xs sm:text-sm shadow-md flex items-center justify-center gap-2 flex-wrap">
          <AlertTriangle className="w-4 h-4 shrink-0 text-slate-950" />
          <span>Modo demonstração: dados de exemplo, servidor não encontrado. Nada é gravado.</span>
          <button
            onClick={conferirServidor}
            className="ml-2 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-slate-950 text-white text-xs hover:bg-slate-800 transition font-medium"
            title="Tentar conectar ao servidor local"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Tentar de novo</span>
          </button>
        </div>
      )}

      {/* Servidor caiu depois de conectado: as vagas continuam na tela e a página reconecta sozinha */}
      {servidor === "fora" && (
        <div className="sticky top-0 z-50 bg-rose-600 text-white font-semibold px-4 py-2.5 text-center text-xs sm:text-sm shadow-md flex items-center justify-center gap-2 flex-wrap">
          <WifiOff className="w-4 h-4 shrink-0" />
          <span>
            O servidor da ferramenta não está respondendo. A página tenta reconectar sozinha; enquanto isso, nada é
            gravado.
          </span>
        </div>
      )}

      <Header
        motivoBuscaDesligada={motivoBuscaDesligada}
        proximaBusca={buscaRodando ? "" : proximaBusca}
        onOpenAddModal={() => setIsAddModalOpen(true)}
        onOpenSearchModal={() => setIsSearchModalOpen(true)}
        onOpenFiltersModal={() => setIsFiltersModalOpen(true)}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
        onOpenAIModal={() => setIsAIModalOpen(true)}
        onOpenAccountsModal={() => setIsAccountsModalOpen(true)}
      />

      <NavigationTabs
        activeTab={activeTab}
        onChangeTab={handleTabChange}
        countQuadro={counts.quadro}
        countPendentes={counts.pendentes}
        countInternacional={counts.internacional}
        countEntrevistas={counts.entrevistas}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Primeiros passos (simulado até a História 3 da spec 025) */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-indigo-900/90 via-slate-900 to-purple-950 text-white border border-indigo-700/40 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-300" />
                <span>Onboarding do Candidato</span>
              </span>
              <span className="text-xs text-indigo-200/80 font-medium">Primeiros Passos & Anamnese</span>
            </div>
            <h3 className="text-sm sm:text-base font-bold">
              Calibre o perfil com as perguntas essenciais para a análise de vagas
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              Responda às perguntas sobre cargos-alvo, conquistas com métricas, critérios inegociáveis e modelos de
              trabalho para que a IA dê as notas de aderência com precisão.
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
            vagas={vagas}
            onSelectVaga={(v) => setDetalheId(v.id)}
            onMoveStage={handleMoveStage}
            onDeleteVaga={handleDeleteVaga}
            onOpenAddModal={() => setIsAddModalOpen(true)}
          />
        )}

        {activeTab === "relatorio" && (
          <div className="space-y-4">
            {painelBusca}
            <UltimaBuscaLinha busca={ultimaBusca} analisando={Boolean(versaoInfo?.analisando)} />
            {servidor === "no_ar" && (
              <CompletarDescricoes
                gatilho={pendentesVersao}
                onTerminou={() => carregarVagas().catch(() => undefined)}
                onErro={(e) => avisarErro(e, "Não deu para completar as descrições.")}
              />
            )}
            <TriageReport
              vagas={vagasRelatorio}
              versao={versaoInfo}
              semIA={semIA}
              onSelectVaga={(v) => setDetalheId(v.id)}
              onSeguirVaga={handleSeguirVaga}
              onNaoSeguirVaga={handleNaoSeguirVaga}
              onVoltarTriagem={handleVoltarTriagem}
              onMarcarTodasNaoSeguidas={handleMarcarTodasNaoSeguidas}
              onForcarVerificar={handleForcarVerificar}
              onAbrirIA={() => setIsAIModalOpen(true)}
            />
          </div>
        )}

        {activeTab === "internacional" && (
          <div className="space-y-4">
            {painelBusca}
            <InternationalHub
              vagas={vagasInternacional}
              onSelectVaga={(v) => setDetalheId(v.id)}
              onSeguirVaga={handleSeguirVaga}
              onOpenFiltersModal={() => setIsFiltersModalOpen(true)}
            />
          </div>
        )}

        {activeTab === "metricas" && (
          <FunnelAnalytics vagas={vagas} onNavigateToTab={(tab) => handleTabChange(tab as ActiveTab)} />
        )}

        {activeTab === "entrevistas" && (
          <InterviewCoach
            vagas={vagas.filter(noQuadro)}
            onUpdateVaga={(id, campos) => handleUpdateVaga(id, campos as CamposEditaveis)}
            onSelectVagaModal={(v) => setDetalheId(v.id)}
          />
        )}
      </main>

      {/* Modais */}
      {vagaDetalhe && (
        <JobDetailModal
          key={vagaDetalhe.id}
          vaga={vagaDetalhe}
          versao={versaoInfo}
          onClose={() => setDetalheId(null)}
          onUpdateVaga={handleUpdateVaga}
          onDeleteVaga={handleDeleteVaga}
          onForcarVerificar={handleForcarVerificar}
        />
      )}

      {isAddModalOpen && (
        <AddJobModal
          onClose={() => setIsAddModalOpen(false)}
          onVagaAdicionada={handleVagaAdicionada}
          onAviso={showToast}
        />
      )}

      {isSearchModalOpen && (
        <SearchJobsModal
          onClose={() => setIsSearchModalOpen(false)}
          onIniciada={handleBuscaIniciada}
          onPlano={setPlanoBusca}
          onAbrirFiltros={() => {
            setIsSearchModalOpen(false)
            setIsFiltersModalOpen(true)
          }}
          onAbrirPerfil={() => {
            setIsSearchModalOpen(false)
            setIsProfileModalOpen(true)
          }}
        />
      )}

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
        onReloadAllData={conferirServidor}
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
        onProntoPortal={handleConectarPortal}
        onSincronizar={handleSincronizarPortais}
        onAplicarAlteracoes={handleAplicarAlteracoes}
      />

      {/* Aviso flutuante */}
      {toast && (
        <div className="fixed bottom-6 right-6 left-6 sm:left-auto z-50 animate-in slide-in-from-bottom-5 fade-in duration-200">
          <div
            role="status"
            className={`px-4 py-3 rounded-2xl shadow-xl text-xs sm:text-sm font-semibold flex items-center gap-2 border max-w-md ${
              toast.type === "erro"
                ? "bg-rose-950 text-rose-100 border-rose-800"
                : "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 border-slate-700 dark:border-slate-300"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full inline-block shrink-0 ${
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
