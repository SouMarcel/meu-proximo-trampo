/**
 * Buscar vagas (dash/API.md §3.3): mostra o plano antes (portais, cargos, janela, tempo, IA e custo) e só busca
 * na confirmação. Busca recente ou portal em espera: o aviso aparece e o pedido segue com a confirmação.
 */
import React, { useEffect, useState } from "react"
import { X, Search, Loader2, AlertTriangle, Sparkles } from "lucide-react"
import type { EstadoBusca, PlanoBusca } from "../../types/api"
import * as buscaApi from "../../services/api/busca"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta, motivoSemGravar } from "../../contexto/Ferramenta"
import { horaDe } from "../../utils/formatters"

interface SearchJobsModalProps {
  onClose: () => void
  onIniciada: (estado: EstadoBusca) => void
  onPlano: (plano: PlanoBusca) => void
  onAbrirFiltros: () => void
  onAbrirPerfil: () => void
}

export default function SearchJobsModal({ onClose, onIniciada, onPlano, onAbrirFiltros, onAbrirPerfil }: SearchJobsModalProps) {
  const { podeGravar, servidor, podeAlterar, tratarErro } = useFerramenta()
  const [plano, setPlano] = useState<PlanoBusca | null>(null)
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [semNota, setSemNota] = useState(false)

  const carregarPlano = async () => {
    try {
      const p = await buscaApi.plano()
      setPlano(p)
      onPlano(p)
      // com IA e sem perfil, a nota não tem base: a busca segue sem nota
      setSemNota(Boolean(p.ia?.ligada && !p.perfil_ok))
    } catch (e) {
      setErro(mensagemDeErro(e, "Não deu para preparar a busca: o servidor não respondeu."))
    }
  }

  useEffect(() => {
    carregarPlano()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const iniciar = async () => {
    if (!plano) return
    setEnviando(true)
    setErro("")
    try {
      const e = await buscaApi.iniciar({
        sem_nota: semNota,
        confirmar_recente: Boolean(plano.recente),
        confirmar_espera: Boolean(plano.espera?.length),
      })
      onIniciada(e)
      onClose()
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "A busca não começou."))
      carregarPlano()
    } finally {
      setEnviando(false)
    }
  }

  const espera = plano?.proxima_em && Date.parse(plano.proxima_em) > Date.now() ? horaDe(plano.proxima_em) : ""
  const esperas = plano?.espera || []
  const portaisEspera = esperas.map((x) => x.portal).join(" e o ")
  const motivo = motivoSemGravar(servidor, podeAlterar)
  const rotulo = semNota
    ? "Buscar sem nota"
    : esperas.length
      ? `Buscar sem o ${portaisEspera}`
      : plano?.recente
        ? "Buscar mesmo assim"
        : "Buscar agora"
  const dias = plano ? Math.round(plano.janela_horas / 24) : 0
  const ia = plano?.ia

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-busca"
        className="relative w-full max-w-xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-busca" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Buscar vagas
              </h3>
              <p className="text-xs text-slate-500">Confira o que vai rodar antes de começar.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1 space-y-3 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          {!plano && !erro && (
            <p className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Preparando a busca…
            </p>
          )}

          {plano && !plano.filtros_ok && (
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 space-y-2">
              <p>Escolha os cargos antes de buscar.</p>
              <button onClick={onAbrirFiltros} className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-600 text-white hover:bg-amber-500">
                Abrir os filtros da busca
              </button>
            </div>
          )}

          {plano && plano.filtros_ok && (
            <>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>
                  <b>{plano.consultas} consulta(s)</b> em {plano.portais.join(", ")} ({plano.resumo})
                </li>
                <li>Cargos: {plano.cargos.join(", ")}</li>
                <li>Vagas publicadas {dias <= 1 ? "nas últimas 24 horas" : `nos últimos ${dias} dias`}</li>
                <li>
                  Leva cerca de {plano.estimativa_min} minuto(s); dá para usar a página enquanto isso e cancelar a
                  qualquer momento.
                </li>
                {ia?.ligada && plano.perfil_ok && (
                  <li>
                    As vagas novas recebem a nota de aderência pela IA:{" "}
                    <b>
                      {ia.nome}
                      {ia.modelo ? ` · ${ia.modelo}` : ""}
                    </b>
                    .
                    {ia.cobranca === "uso" &&
                      " Cobrado por uso na sua conta do provedor: cada vaga analisada consome créditos."}
                    {ia.cobranca === "gratuito" &&
                      " Modelo gratuito: sem custo, mas com limite de pedidos por dia no provedor; se o limite acabar, a nota para e dá para tentar de novo depois."}
                  </li>
                )}
                {!ia?.ligada && <li>Sem IA: as vagas ficam sem nota (dá para escolher uma IA no botão IA).</li>}
              </ul>

              {ia?.ligada && !plano.perfil_ok && (
                <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 space-y-2">
                  <p>
                    Você ainda não tem perfil: sem ele, a nota de aderência não tem base. Monte o perfil antes ou busque
                    assim mesmo, com as vagas sem nota.
                  </p>
                  <button onClick={onAbrirPerfil} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/70 dark:bg-slate-900 border border-amber-300 dark:border-amber-800">
                    <Sparkles className="w-3.5 h-3.5" /> Montar meu perfil
                  </button>
                </div>
              )}

              {espera ? (
                <p className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200">
                  Para os portais não bloquearem a busca, espere: dá para buscar de novo a partir das {espera}.
                </p>
              ) : (
                plano.recente &&
                plano.ultima && (
                  <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200">
                    A última busca terminou às {horaDe(plano.ultima.fim)}: os portais devem ter pouca vaga nova.
                  </p>
                )
              )}
              {esperas.map((x) => (
                <p
                  key={x.portal}
                  className={`p-3 rounded-xl border ${
                    plano.so_espera
                      ? "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200"
                      : "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200"
                  }`}
                >
                  O {x.portal} está em espera até {horaDe(x.ate)} ({x.motivo})
                  {plano.so_espera
                    ? " e é o único portal ligado: não há o que buscar agora."
                    : ": fica de fora desta busca, que segue com os outros portais."}
                </p>
              ))}
              {plano.aviso_cargos && (
                <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200">
                  {plano.aviso_cargos}
                </p>
              )}
              {plano.aviso_pausa && (
                <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200">
                  {plano.aviso_pausa}
                </p>
              )}
            </>
          )}

          {motivo && (
            <p className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">{motivo}</p>
          )}
          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{erro}</span>
            </p>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            Cancelar
          </button>
          <button
            onClick={iniciar}
            disabled={!plano || !plano.filtros_ok || Boolean(espera) || plano.so_espera || !podeGravar || enviando}
            className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>{rotulo}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
