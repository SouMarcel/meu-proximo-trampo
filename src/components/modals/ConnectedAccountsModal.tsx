/**
 * Atualizar candidaturas (dash/API.md §3.11; constituição VI, "Conta conectada"): a ferramenta lê a área logada da
 * Gupy e do Indeed numa janela do navegador dela, com o login feito pela pessoa. A página nunca pede nem mostra
 * senha; a leitura só propõe, e só os itens marcados vão para o quadro. Bloqueio ou novo login param a leitura.
 */
import React, { useCallback, useEffect, useRef, useState } from "react"
import { X, Link2, Loader2, AlertTriangle } from "lucide-react"
import * as contasApi from "../../services/api/contas"
import type { Contas, EstadoCandidaturas, ItemCandidatura } from "../../services/api/contas"
import { mensagemDeErro, ehErroApi } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { useConsulta } from "../../hooks/useConsulta"
import { ETAPAS, RESULTADOS } from "../../utils/rotulos"
import { linkSeguro } from "../../utils/formatters"
import { BTN_MINI } from "../curriculo/Curriculos"
import LoginGuardado from "./LoginGuardado"

interface Props {
  onClose: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
  /** O quadro mudou (aplicadas ou importadas): relê as vagas. */
  onQuadroMudou: () => void
  /** Fecha este diálogo e abre Meu perfil → Informações básicas (spec 036). */
  onAbrirInformacoes: () => void
}

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"

function etapaTexto(x: ItemCandidatura["para"] | null): string {
  if (!x || !x.etapa) return "Relatório"
  const e = ETAPAS.find((y) => y.valor === x.etapa)
  return (e ? e.rotulo : x.etapa) + (x.resultado ? ` · ${RESULTADOS[x.resultado] || x.resultado}` : "")
}

function mudanca(i: ItemCandidatura): string {
  if (i.tipo === "mudar") return `${etapaTexto(i.de)} → ${etapaTexto(i.para)}`
  if (i.tipo === "quadro") return `Relatório → ${etapaTexto(i.para)}`
  return `Nova no quadro · ${etapaTexto(i.para)}`
}

/** O ícone do portal vem do código do servidor; como <img>, um SVG não executa script. */
function Icone({ svg }: { svg: string }) {
  if (!svg || !svg.trim().startsWith("<svg")) return null
  return <img src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`} alt="" className="w-5 h-5" aria-hidden="true" />
}

export default function ConnectedAccountsModal({ onClose, onAviso, onQuadroMudou, onAbrirInformacoes }: Props) {
  const { podeGravar, tratarErro } = useFerramenta()
  const [c, setC] = useState<Contas | null>(null)
  const [e, setE] = useState<EstadoCandidaturas | null>(null)
  const [conectando, setConectando] = useState<string | null>(null)
  const [marcadas, setMarcadas] = useState<Record<string, boolean>>({})
  const [erro, setErro] = useState("")
  const [ocupado, setOcupado] = useState("")
  const antes = useRef<string | undefined>(undefined)
  const fechar = useRef(onClose)
  fechar.current = onClose
  const aviso = useRef(onAviso)
  aviso.current = onAviso

  const carregar = useCallback(async () => {
    try {
      const [cc, ee] = await Promise.all([contasApi.contas(), contasApi.estado()])
      const anterior = antes.current
      antes.current = ee.situacao
      setC(cc)
      setE(ee)
      const r = ee.resultado
      if (r && (anterior === undefined || contasApi.ATIVAS.includes(anterior || ""))) {
        // marcas sugeridas pelo servidor, na primeira vez que a proposta aparece
        const m: Record<string, boolean> = {}
        r.itens.forEach((i) => (m[i.chave] = i.marcado))
        setMarcadas(m)
      }
      const acabou = anterior !== undefined && contasApi.ATIVAS.includes(anterior) && ee.situacao === "pronta"
      if (acabou && r && !r.itens.length && !r.historico.length && !Object.keys(r.erros || {}).length) {
        aviso.current(`Tudo certo: o quadro já está em dia com os portais (${r.sem_mudanca || 0} candidatura(s) conferida(s)).`)
        fechar.current()
      }
    } catch (err) {
      setErro(
        ehErroApi(err) && err.status === 403
          ? "Contas conectadas só funcionam no computador onde a ferramenta roda."
          : mensagemDeErro(err, "Não deu para ler as contas."),
      )
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  const lendo = Boolean(e && contasApi.ATIVAS.includes(e.situacao))
  useConsulta(carregar, 1500, lendo)

  const acao = async (chave: string, fn: () => Promise<unknown>) => {
    setOcupado(chave)
    setErro("")
    try {
      await fn()
    } catch (err) {
      tratarErro(err)
      setErro(mensagemDeErro(err))
    } finally {
      setOcupado("")
    }
  }

  const r = e?.resultado
  const algum = (c?.portais || []).some((p) => p.conectado)
  const itens = r && !lendo ? r.itens : []
  const nMarcadas = itens.filter((i) => marcadas[i.chave]).length
  const grupos: Record<string, ItemCandidatura[]> = {}
  itens.forEach((i) => (grupos[i.plataforma] = grupos[i.plataforma] || []).push(i))

  const aplicar = () =>
    acao("aplicar", async () => {
      const chaves = itens.filter((i) => marcadas[i.chave]).map((i) => i.chave)
      if (!chaves.length) return setErro("Marque pelo menos uma candidatura.")
      const feitas = itens.filter((i) => chaves.includes(i.chave))
      const j = await contasApi.aplicar({ chaves })
      const lista =
        feitas.slice(0, 3).map((i) => `${i.titulo} → ${etapaTexto(i.para)}`).join("; ") + (feitas.length > 3 ? `; e mais ${feitas.length - 3}` : "")
      onQuadroMudou()
      if (j.erros?.length) {
        setErro("Não deu para gravar: " + j.erros.join(" · "))
        onAviso(`Quadro atualizado (${j.aplicados}): ${lista}. Com erro: ${j.erros.length}.`, "erro")
        await carregar()
      } else {
        onAviso(`Quadro atualizado (${j.aplicados}): ${lista}.`)
        onClose()
      }
    })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-contas"
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Link2 className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-contas" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Atualizar candidaturas
              </h3>
              <p className="text-xs text-slate-500">
                Lê o andamento das suas candidaturas na Gupy e no Indeed, numa janela do navegador só da ferramenta, com o
                login feito por você. Só leitura: nada é clicado nem enviado nos portais, e só o que você marcar vai para o
                quadro.
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          {!c && !erro && (
            <p className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
            </p>
          )}

          {c && !c.navegador && <p className="text-rose-600 dark:text-rose-400">Precisa do Edge ou do Chrome neste computador.</p>}

          {itens.length > 0 && (
            <p role="status" className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900">
              <b>Encontrei {itens.length} mudança(s) nos portais.</b> Confira e clique em Aplicar: só o que estiver marcado é
              gravado no quadro.
            </p>
          )}

          {c && (
            <section className="space-y-2">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">Portais</h4>
              {c.portais.map((p) => (
                <div key={p.nome} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Icone svg={p.icone} />
                    <b>{p.plataforma}</b>
                    <span className="ml-auto flex items-center gap-2">
                      {p.conectado ? (
                        <>
                          <span className="text-emerald-700 dark:text-emerald-400 text-xs font-semibold">Conectado</span>
                          <button
                            type="button"
                            disabled={lendo || !podeGravar || Boolean(ocupado)}
                            onClick={() =>
                              acao("desc", async () => {
                                await contasApi.desconectar(p.nome)
                                onAviso("Desconectado: a sessão desse portal foi apagada da janela da ferramenta.")
                                await carregar()
                              })
                            }
                            className={BTN_MINI}
                          >
                            Desconectar
                          </button>
                        </>
                      ) : conectando === p.nome ? (
                        <>
                          <span className={DICA}>Faça o login na janela que abriu e clique em Pronto.</span>
                          <button
                            type="button"
                            disabled={Boolean(ocupado)}
                            onClick={() =>
                              acao("pronto", async () => {
                                const j = await contasApi.pronto(p.nome)
                                if (j.conectado) {
                                  setConectando(null)
                                  onAviso("Conectado.")
                                  await carregar()
                                } else {
                                  setErro("O login ainda não foi concluído na janela. Termine o login e clique em Pronto de novo.")
                                }
                              })
                            }
                            className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
                          >
                            Pronto
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          disabled={lendo || !c.navegador || !podeGravar || Boolean(ocupado)}
                          onClick={() =>
                            acao("con", async () => {
                              await contasApi.conectar(p.nome)
                              setConectando(p.nome)
                            })
                          }
                          className={BTN_MINI}
                        >
                          Conectar
                        </button>
                      )}
                    </span>
                  </div>
                  {p.aviso_login && <p className={DICA}>{p.aviso_login}</p>}
                </div>
              ))}
            </section>
          )}

          {c && <LoginGuardado onAviso={onAviso} />}
          {c && (
            <p className="flex items-center gap-2 flex-wrap">
              <span className={DICA}>
                Seus dados de contato, respostas guardadas e sites da candidatura assistida ficam em Meu perfil → Informações
                básicas.
              </span>
              <button type="button" onClick={onAbrirInformacoes} className={BTN_MINI}>
                Abrir
              </button>
            </p>
          )}

          {e?.situacao === "lendo" && (
            <p role="status" className="flex items-center gap-2 p-3 rounded-xl bg-slate-100 dark:bg-slate-800">
              <Loader2 className="w-4 h-4 animate-spin" /> Lendo suas candidaturas{e.portal ? ` (${e.portal})` : ""}, aguarde…
            </p>
          )}
          {e?.situacao === "aguardando_login" && (
            <p role="status" className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900">
              A {e.portal} pediu login: faça o login na janela que abriu (ela veio para a frente). A leitura segue sozinha.
            </p>
          )}

          {r && !lendo && (
            <>
              {Object.entries(r.erros || {}).map(([pl, msg]) => (
                <p key={pl} className="text-rose-600 dark:text-rose-400">
                  {pl}: {msg}
                </p>
              ))}
              {Object.entries(grupos).map(([pl, lista]) => (
                <section key={pl} className="space-y-2">
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">{pl}</h4>
                  {lista.map((i) => {
                    const extra = [i.nota, ...(i.avisos || [])].filter(Boolean).join(" · ")
                    const link = linkSeguro(i.url)
                    return (
                      <label key={i.chave} className="flex items-start gap-2 p-3 rounded-xl border border-slate-200 dark:border-slate-800 cursor-pointer">
                        <input
                          type="checkbox"
                          className="mt-0.5"
                          checked={Boolean(marcadas[i.chave])}
                          onChange={(ev) => setMarcadas((m) => ({ ...m, [i.chave]: ev.target.checked }))}
                          aria-label={`Aplicar: ${i.titulo}`}
                        />
                        <span className="space-y-0.5">
                          <span className="block">
                            <b>{i.titulo}</b> — {i.empresa}
                            {link && (
                              <>
                                {" · "}
                                <a href={link} target="_blank" rel="noopener noreferrer" className="underline" onClick={(ev) => ev.stopPropagation()}>
                                  abrir
                                </a>
                              </>
                            )}
                          </span>
                          <span className="block font-semibold text-indigo-700 dark:text-indigo-300">{mudanca(i)}</span>
                          {extra && <span className={`block ${DICA}`}>{extra}</span>}
                        </span>
                      </label>
                    )
                  })}
                </section>
              ))}
              {!r.itens.length && <p className={DICA}>Nada a mudar: o quadro já está em dia com os portais.</p>}
              {r.sem_mudanca > 0 && <p className={DICA}>{r.sem_mudanca} candidatura(s) já estavam em dia.</p>}
              {r.historico.length > 0 && (
                <p className="flex items-center gap-2 flex-wrap">
                  <span className={DICA}>{r.historico.length} candidatura(s) já encerradas nos portais não estão no dashboard.</span>
                  <button
                    type="button"
                    disabled={!podeGravar || Boolean(ocupado)}
                    onClick={() =>
                      acao("hist", async () => {
                        const j = await contasApi.aplicar({ historico: true })
                        onAviso(`${j.aplicados} candidatura(s) importada(s) como Encerrada.`)
                        onQuadroMudou()
                        await carregar()
                      })
                    }
                    className={BTN_MINI}
                  >
                    Importar como histórico
                  </button>
                </p>
              )}
            </>
          )}

          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {erro}
            </p>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2 flex-wrap">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
            Fechar
          </button>
          {itens.length > 0 ? (
            <>
              <button
                type="button"
                disabled={!podeGravar || Boolean(ocupado)}
                onClick={() => acao("ler", async () => { await contasApi.ler(); antes.current = "lendo"; await carregar() })}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"
              >
                Ler de novo
              </button>
              <button
                type="button"
                disabled={!nMarcadas || !podeGravar || Boolean(ocupado)}
                onClick={aplicar}
                className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
              >
                {ocupado === "aplicar" ? "Aplicando…" : nMarcadas ? `Aplicar ${nMarcadas} ${nMarcadas === 1 ? "mudança" : "mudanças"}` : "Nada marcado"}
              </button>
            </>
          ) : (
            <button
              type="button"
              disabled={lendo || !algum || !podeGravar || Boolean(ocupado)}
              onClick={() => acao("ler", async () => { await contasApi.ler(); antes.current = "lendo"; await carregar() })}
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
            >
              {lendo ? "Lendo…" : "Atualizar agora"}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
