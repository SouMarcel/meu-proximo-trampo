/**
 * Portais com login (spec 041), no painel Filtros da busca: separados dos portais de busca pública. Ligar pede
 * confirmação com o aviso de risco e só muda o formulário (vale ao salvar os filtros, na mesma lista `fontes`).
 * Conectar abre a página de login na janela da ferramenta; quem entra é a pessoa. A página nunca pede nem mostra senha.
 */
import { useCallback, useEffect, useState } from "react"
import { AlertTriangle, KeyRound, Loader2 } from "lucide-react"
import * as portaisApi from "../../services/api/portaisLogin"
import type { FonteLogin, PortaisLogin as EstadoPortais, PortalLogin } from "../../types/api"
import { ehErroApi, mensagemDeErro } from "../../services/api"
import { useFerramenta, AvisoSoLeitura } from "../../contexto/Ferramenta"
import { horaDe } from "../../utils/formatters"
import { BTN_MINI } from "../curriculo/Curriculos"

interface Props {
  /** opcoes.fontes_login de GET /api/config. */
  fontes: FonteLogin[]
  /** A lista `fontes` do formulário (ainda não salva). */
  ligados: string[]
  onLigar: (nome: string, ligar: boolean) => void
}

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"

/** Situação mostrada: o liga/desliga vem do formulário; conexão e espera, do servidor. */
function situacaoDe(ligado: boolean, p?: PortalLogin): { texto: string; cor: string } | null {
  if (!ligado) return { texto: "Desligado", cor: "text-slate-500 dark:text-slate-400" }
  if (!p) return null
  if (p.espera)
    return {
      texto: `Em espera até ${horaDe(p.espera.ate)} (${p.espera.motivo})`,
      cor: "text-rose-700 dark:text-rose-300",
    }
  if (p.conectado) return { texto: "Conectado", cor: "text-emerald-700 dark:text-emerald-400" }
  return { texto: "Desconectado", cor: "text-amber-700 dark:text-amber-300" }
}

export default function PortaisLogin({ fontes, ligados, onLigar }: Props) {
  const { podeGravar, tratarErro } = useFerramenta()
  const [estado, setEstado] = useState<EstadoPortais | null>(null)
  const [erroLeitura, setErroLeitura] = useState("")
  const [confirmando, setConfirmando] = useState<string | null>(null)
  const [conectando, setConectando] = useState<string | null>(null)
  const [aviso, setAviso] = useState<{ nome: string; texto: string } | null>(null)
  const [ocupado, setOcupado] = useState("")

  const carregar = useCallback(async () => {
    try {
      setEstado(await portaisApi.portaisLogin())
      setErroLeitura("")
    } catch (e) {
      tratarErro(e)
      setErroLeitura(
        ehErroApi(e) && e.status === 403
          ? "Conectar portais só funciona no computador onde a ferramenta roda."
          : "Não deu para ler a situação dos portais: " + mensagemDeErro(e),
      )
    }
  }, [tratarErro])

  useEffect(() => {
    carregar()
  }, [carregar])

  // cada ação recarrega a situação no fim, dando certo ou não
  const acao = async (nome: string, chave: string, fn: () => Promise<void>) => {
    setOcupado(chave)
    setAviso(null)
    try {
      await fn()
    } catch (e) {
      tratarErro(e)
      setAviso({ nome, texto: mensagemDeErro(e) })
    } finally {
      await carregar()
      setOcupado("")
    }
  }

  if (!fontes.length) return null
  const navegador = estado?.navegador !== false

  return (
    <section className="space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0">
      <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-1.5">
        <KeyRound className="w-4 h-4 text-indigo-500" /> Portais com login
      </h4>
      <p className={DICA}>
        Portais que só mostram a busca depois do login. Rodam só quando você clica em Buscar na página, com o login feito
        por você na janela da ferramenta.
      </p>
      {erroLeitura && <p className="text-[11px] text-rose-600 dark:text-rose-400">{erroLeitura}</p>}
      {estado && !estado.navegador && (
        <p className="text-[11px] text-rose-600 dark:text-rose-400">Precisa do Edge ou do Chrome neste computador.</p>
      )}

      <div className="space-y-2">
        {fontes.map((f) => {
          const p = estado?.portais.find((x) => x.nome === f.nome)
          const ligado = ligados.includes(f.nome)
          const sit = situacaoDe(ligado, p)
          const travado = !podeGravar || !estado || !navegador || Boolean(ocupado)
          return (
            <div key={f.nome} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-start gap-2 flex-wrap">
                <label className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300 cursor-pointer flex-1 min-w-[200px]">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={ligado}
                    onChange={() => {
                      if (ligado) {
                        onLigar(f.nome, false) // desligar não pede confirmação
                        setConectando(null)
                      } else {
                        setConfirmando(f.nome)
                      }
                    }}
                  />
                  <span>
                    <b>{f.rotulo}</b>
                    {f.termos && <span className={`block ${DICA}`}>{f.termos}</span>}
                    {f.aviso_login && <span className={`block ${DICA}`}>{f.aviso_login}</span>}
                  </span>
                </label>
                {sit ? (
                  <span className={`text-xs font-semibold ${sit.cor}`}>{sit.texto}</span>
                ) : (
                  !erroLeitura && <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-400" aria-label="Carregando" />
                )}
              </div>

              {confirmando === f.nome && (
                <div
                  role="alertdialog"
                  aria-label={`Ligar ${f.rotulo}`}
                  className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs space-y-2"
                >
                  <p className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{f.aviso_risco}</span>
                  </p>
                  <div className="flex items-center justify-end gap-2">
                    <button type="button" onClick={() => setConfirmando(null)} className={BTN_MINI}>
                      Cancelar
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        onLigar(f.nome, true)
                        setConfirmando(null)
                      }}
                      className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-amber-600 hover:bg-amber-500"
                    >
                      Ligar mesmo assim
                    </button>
                  </div>
                </div>
              )}

              {ligado && p && p.ligado !== ligado && <p className={DICA}>Vale para a busca depois de Salvar filtros.</p>}

              {ligado && (
                <div className="flex items-center gap-2 flex-wrap">
                  {p?.conectado ? (
                    <button
                      type="button"
                      disabled={travado}
                      onClick={() =>
                        acao(f.nome, `${f.nome}:desc`, async () => {
                          await portaisApi.desconectarPortal(f.nome)
                          setConectando(null)
                        })
                      }
                      className={BTN_MINI}
                    >
                      {ocupado === `${f.nome}:desc` && <Loader2 className="w-3 h-3 animate-spin" />} Desconectar
                    </button>
                  ) : (
                    <>
                      <button
                        type="button"
                        disabled={travado}
                        onClick={() =>
                          acao(f.nome, `${f.nome}:con`, async () => {
                            await portaisApi.conectarPortal(f.nome)
                            setConectando(f.nome)
                          })
                        }
                        className={BTN_MINI}
                      >
                        {ocupado === `${f.nome}:con` && <Loader2 className="w-3 h-3 animate-spin" />} Conectar
                      </button>
                      <button
                        type="button"
                        disabled={travado}
                        onClick={() =>
                          acao(f.nome, `${f.nome}:pronto`, async () => {
                            const j = await portaisApi.prontoPortal(f.nome)
                            if (j.conectado) {
                              setConectando(null)
                            } else {
                              setAviso({
                                nome: f.nome,
                                texto: "Login não encontrado: entre na janela da ferramenta e clique em Pronto de novo.",
                              })
                            }
                          })
                        }
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
                      >
                        {ocupado === `${f.nome}:pronto` && <Loader2 className="w-3 h-3 animate-spin" />} Pronto
                      </button>
                      {conectando === f.nome && <span className={DICA}>Entre na janela da ferramenta e clique em Pronto.</span>}
                    </>
                  )}
                  {!podeGravar && <AvisoSoLeitura />}
                </div>
              )}

              {aviso?.nome === f.nome && (
                <p role="alert" className="text-[11px] text-rose-600 dark:text-rose-400">
                  {aviso.texto}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
