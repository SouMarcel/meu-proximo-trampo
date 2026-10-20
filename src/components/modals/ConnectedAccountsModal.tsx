import React, { useState } from "react"
import {
  X,
  Link2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Check,
  Clock,
  ArrowRight,
  ShieldCheck,
  Globe,
} from "lucide-react"
import {
  PortalConectado,
  ItemSincronizacao,
  HistoricoCandidatura,
  Etapa,
} from "../../types/job"
import { getPlataformaStyle, getEtapaInfo } from "../../utils/formatters"

interface ConnectedAccountsModalProps {
  isOpen: boolean
  onClose: () => void
  portais: PortalConectado[]
  itensSincronizacao: ItemSincronizacao[]
  historico: HistoricoCandidatura[]
  onConectarPortal: (portalId: string) => void
  onDesconectarPortal: (portalId: string) => void
  onProntoPortal: (portalId: string) => void
  onSincronizar: () => Promise<void> | void
  onAplicarAlteracoes: (itensSelecionados: ItemSincronizacao[]) => void
}

export default function ConnectedAccountsModal({
  isOpen,
  onClose,
  portais,
  itensSincronizacao,
  historico,
  onConectarPortal,
  onDesconectarPortal,
  onProntoPortal,
  onSincronizar,
  onAplicarAlteracoes,
}: ConnectedAccountsModalProps) {
  if (!isOpen) return null

  const [itens, setItens] = useState<ItemSincronizacao[]>(itensSincronizacao)
  const [isSyncing, setIsSyncing] = useState(false)
  const [portalEmConexao, setPortalEmConexao] = useState<string | null>(null)
  const [sucessoMsg, setSucessoMsg] = useState<string | null>(null)

  const handleToggleItem = (id: string) => {
    setItens((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, selecionado: !item.selecionado } : item,
      ),
    )
  }

  const handleSelectAll = (selecionar: boolean) => {
    setItens((prev) => prev.map((item) => ({ ...item, selecionado: selecionar })))
  }

  const handleSyncClick = async () => {
    setIsSyncing(true)
    setSucessoMsg(null)
    try {
      await onSincronizar()
      setSucessoMsg("Portais sincronizados com sucesso!")
    } finally {
      setIsSyncing(false)
    }
  }

  const handleAplicar = () => {
    const selecionados = itens.filter((i) => i.selecionado)
    if (selecionados.length === 0) return
    onAplicarAlteracoes(selecionados)
    setItens((prev) => prev.filter((i) => !i.selecionado))
    setSucessoMsg(
      `${selecionados.length} alteração(ões) aplicada(s) ao Quadro Kanban!`,
    )
  }

  const itensSelecionadosCount = itens.filter((i) => i.selecionado).length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-3xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Link2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Contas Conectadas & Sincronização
              </h3>
              <p className="text-xs text-slate-500">
                Atualize o quadro Kanban com o andamento das suas candidaturas nos
                portais (Gupy, Indeed, LinkedIn)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5 hover:text-slate-900 [button:hover_&]:text-slate-900 dark:hover:text-slate-900 dark:[button:hover_&]:text-slate-900 transition-colors" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {sucessoMsg && (
            <div className="p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{sucessoMsg}</span>
            </div>
          )}

          {/* 1. Portais Conectados */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <span>Portais e Sessões</span>
                <span className="text-xs font-normal text-slate-500">
                  (Princípio VI da Constituição)
                </span>
              </h4>
              <button
                onClick={handleSyncClick}
                disabled={isSyncing}
                className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`}
                />
                <span>{isSyncing ? "Lendo portais…" : "Ler portais agora"}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {portais.map((portal) => {
                const isConnecting = portalEmConexao === portal.id
                const platStyle = getPlataformaStyle(portal.plataforma)

                return (
                  <div
                    key={portal.id}
                    className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex flex-col justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span
                          className={`px-2 py-0.5 rounded-md text-xs font-bold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}
                        >
                          {portal.nome}
                        </span>
                        <span
                          className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                            portal.conectado
                              ? "bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300"
                              : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                          }`}
                        >
                          {portal.conectado ? "Conectado" : "Desconectado"}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-relaxed mt-2">
                        {portal.aviso_login}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between gap-2">
                      {portal.conectado ? (
                        <>
                          <span className="text-[10px] text-slate-400">
                            {portal.candidaturas_encontradas || 0} candidaturas
                          </span>
                          <button
                            type="button"
                            onClick={() => onDesconectarPortal(portal.id)}
                            className="text-xs text-rose-600 hover:text-rose-500 font-medium"
                          >
                            Desconectar
                          </button>
                        </>
                      ) : isConnecting ? (
                        <div className="w-full flex items-center justify-between gap-2">
                          <span className="text-[10px] text-amber-600 animate-pulse">
                            Faça login na janela
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              setPortalEmConexao(null)
                              onProntoPortal(portal.id)
                            }}
                            className="px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500"
                          >
                            Pronto
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            setPortalEmConexao(portal.id)
                            onConectarPortal(portal.id)
                          }}
                          className="w-full py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 transition shadow-2xs"
                        >
                          Conectar
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 2. Alterações Detectadas Prontas para Atualizar o Quadro */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                  Mudanças Reais no Quadro Kanban
                </h4>
                <p className="text-xs text-slate-500">
                  Selecione as alterações detectadas nos portais que deseja aplicar às
                  suas vagas
                </p>
              </div>
              {itens.length > 0 && (
                <div className="flex items-center gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => handleSelectAll(true)}
                    className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
                  >
                    Todas
                  </button>
                  <span className="text-slate-300 dark:text-slate-700">·</span>
                  <button
                    type="button"
                    onClick={() => handleSelectAll(false)}
                    className="text-slate-500 hover:underline font-medium"
                  >
                    Nenhuma
                  </button>
                </div>
              )}
            </div>

            {itens.length > 0 ? (
              <div className="space-y-2">
                {itens.map((item) => {
                  const platStyle = getPlataformaStyle(item.plataforma)
                  const etapaNovaInfo = getEtapaInfo(item.etapa_nova)

                  return (
                    <div
                      key={item.id}
                      onClick={() => handleToggleItem(item.id)}
                      className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-center justify-between gap-3 ${
                        item.selecionado
                          ? "border-indigo-300 dark:border-indigo-700 bg-indigo-50/40 dark:bg-indigo-950/20"
                          : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 opacity-70 hover:opacity-100"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={item.selecionado}
                          onChange={() => handleToggleItem(item.id)}
                          className="w-4 h-4 rounded-md accent-indigo-600 cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}
                            >
                              {item.plataforma}
                            </span>
                            <h5 className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white">
                              {item.titulo}
                            </h5>
                            <span className="text-xs text-slate-500">
                              · {item.empresa}
                            </span>
                          </div>
                          <p className="text-xs text-indigo-700 dark:text-indigo-300 font-medium mt-1 flex items-center gap-1.5">
                            <ArrowRight className="w-3 h-3 text-indigo-500" />
                            <span>{item.alteracao}</span>
                          </p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <span
                          className={`px-2.5 py-1 rounded-xl text-xs font-semibold ${etapaNovaInfo.badgeBg} ${etapaNovaInfo.badgeText}`}
                        >
                          → {etapaNovaInfo.label}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-6 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-center space-y-1">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Quadro em dia com os portais
                </p>
                <p className="text-[11px] text-slate-500">
                  Nenhuma mudança de etapa pendente encontrada nas contas conectadas.
                </p>
              </div>
            )}
          </div>

          {/* 3. Histórico de Candidaturas nos Portais */}
          {historico.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Histórico nos Portais
              </h4>
              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 space-y-2">
                {historico.map((h) => (
                  <div
                    key={h.id}
                    className="flex items-center justify-between text-xs py-1 border-b border-slate-200/50 dark:border-slate-700/50 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {h.titulo}
                      </span>
                      <span>· {h.empresa}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        ({h.plataforma})
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                      <span>{h.data}</span>
                      <span className="capitalize">({h.etapa})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-5 sm:p-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 transition"
          >
            Fechar
          </button>

          <div className="flex items-center gap-2">
            {itens.length > 0 && (
              <button
                type="button"
                onClick={handleAplicar}
                disabled={itensSelecionadosCount === 0}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs"
              >
                Aplicar no Quadro ({itensSelecionadosCount})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
