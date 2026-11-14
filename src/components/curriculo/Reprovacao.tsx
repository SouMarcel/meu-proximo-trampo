/**
 * Análise de reprovação (spec 049, dash/API.md §3.8): a IA tentou reprovar a pessoa para a vaga. Mostra os motivos nos
 * cinco grupos, com o trecho do currículo e a frase da vaga; as perguntas com Não tenho (❌) / Tenho (⚠️, com o relato e
 * o destino) / Pular, gravadas sozinhas; e o botão Reescrever e gerar o currículo, com os trechos "antes → depois".
 * Só a última análise da vaga aparece.
 */
import React, { useCallback, useEffect, useRef, useState } from "react"
import { Loader2, ShieldAlert } from "lucide-react"
import * as curriculoApi from "../../services/api/curriculo"
import type { GrupoReprovacao, MotivoReprovacao, Reprovacao, RespostaReprovacao } from "../../services/api/curriculo"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { useGeracao } from "../../contexto/Geracao"
import { diaMes, horaDe } from "../../utils/formatters"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const BTN_OPCAO = "px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-colors disabled:opacity-50"
const OPCAO_LIGADA = "bg-indigo-600 text-white border-indigo-600"
const OPCAO_DESLIGADA =
  "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
const ORDEM: GrupoReprovacao[] = [
  "requisito_nao_comprovado",
  "experiencia_generica",
  "competencia_sem_evidencia",
  "resultado_pouco_claro",
  "informacao_ausente",
]
const ESTADO: Record<MotivoReprovacao["estado"], { rotulo: string; cor: string }> = {
  nao_tenho: { rotulo: "❌ não tenho esse requisito", cor: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300" },
  tenho: {
    rotulo: "⚠️ tenho, mas o currículo não deixa claro",
    cor: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  },
  sem_resposta: { rotulo: "sem resposta", cor: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300" },
  sem_pergunta: { rotulo: "", cor: "" },
}

function Opcao({ ligada, onClick, children, disabled }: { ligada: boolean; onClick: () => void; children: React.ReactNode; disabled?: boolean }) {
  return (
    <button type="button" disabled={disabled} onClick={onClick} className={`${BTN_OPCAO} ${ligada ? OPCAO_LIGADA : OPCAO_DESLIGADA}`}>
      {children}
    </button>
  )
}

function Motivo({ m }: { m: MotivoReprovacao }) {
  const e = ESTADO[m.estado]
  return (
    <li className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
      <div className="flex items-start gap-2 flex-wrap">
        <span className="flex-1 min-w-[12rem]">{m.motivo}</span>
        {e.rotulo && <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold whitespace-nowrap ${e.cor}`}>{e.rotulo}</span>}
      </div>
      <p className={DICA}>
        <b>Trecho do currículo:</b>{" "}
        {m.trecho_cv === null ? (
          "não aparece no currículo"
        ) : (
          <>
            “{m.trecho_cv}”
            {!m.trecho_ok && <span className="text-amber-700 dark:text-amber-300"> (trecho não encontrado no currículo)</span>}
          </>
        )}
      </p>
      {m.trecho_vaga && (
        <p className={DICA}>
          <b>Frase da vaga:</b> “{m.trecho_vaga}”
        </p>
      )}
      {m.sensivel && <p className={DICA}>Responda na candidatura (a ferramenta não pergunta sobre isso).</p>}
      {m.perguntas.length > 0 && (
        <p className={DICA}>
          {m.perguntas.length > 1 ? "Perguntas " : "Pergunta "}
          {m.perguntas.join(", ")} abaixo
        </p>
      )}
    </li>
  )
}

/** A última análise de reprovação da vaga, abaixo da lista de currículos. */
export function SecaoReprovacao({ vagaId }: { vagaId: string }) {
  const { servidor, podeGravar, tratarErro } = useFerramenta()
  const { estado, ativa, versao, comecou } = useGeracao()
  const [a, setA] = useState<Reprovacao | null>(null)
  const [podeAlterar, setPodeAlterar] = useState(true)
  const [respostas, setRespostas] = useState<Record<string, RespostaReprovacao>>({})
  const [salvo, setSalvo] = useState<"" | "salvando" | "salvo">("")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)
  const pendente = useRef<Record<string, RespostaReprovacao>>({})
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const carregar = useCallback(() => {
    curriculoApi
      .obterReprovacao(vagaId)
      .then((j) => {
        setA(j.analise)
        setPodeAlterar(j.pode_alterar)
        setRespostas(j.analise?.respostas || {})
      })
      .catch(() => {})
  }, [vagaId])

  useEffect(() => {
    if (servidor === "no_ar") carregar()
  }, [carregar, versao, servidor])

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current) }, [])

  const gravar = useCallback(async () => {
    const lote = pendente.current
    pendente.current = {}
    if (!Object.keys(lote).length) return
    setSalvo("salvando")
    try {
      const j = await curriculoApi.gravarRespostasReprovacao(vagaId, lote)
      setA(j.analise)
      setSalvo("salvo")
      setErro("")
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para guardar a resposta."))
      setSalvo("")
    }
  }, [vagaId, tratarErro])

  const responder = (n: number, r: RespostaReprovacao) => {
    const k = String(n)
    setRespostas((x) => ({ ...x, [k]: r }))
    pendente.current[k] = r
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(gravar, 600)
  }

  const gerar = async () => {
    setEnviando(true)
    setErro("")
    try {
      if (timer.current) clearTimeout(timer.current)
      await gravar()
      comecou(await curriculoApi.gerarComReprovacao(vagaId))
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para gerar o currículo."))
    } finally {
      setEnviando(false)
    }
  }

  const minha = Boolean(estado?.alvo?.vaga_id === vagaId && (estado?.tipo === "reprovacao" || estado?.situacao === "reescrevendo"))
  if (!a) return null

  const grupos = ORDEM.map((g) => ({ g, itens: a.motivos.filter((m) => m.grupo === g) })).filter((x) => x.itens.length)
  const respondida = (r?: RespostaReprovacao) =>
    Boolean(r && (r.resposta === "nao" || r.resposta === "pular" || (r.resposta === "tenho" && (r.relato || "").trim())))
  const pronta = a.perguntas.every((p) => respondida(respostas[String(p.n)]))
  const bloqueado = !podeAlterar || !podeGravar
  const nLevados = (a.levados || []).length

  return (
    <section className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-2 flex-wrap">
        <ShieldAlert className="w-4 h-4 text-rose-500" />
        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Análise de reprovação</h4>
        <span className={DICA}>
          {diaMes(a.criada_em)} {horaDe(a.criada_em)} · analisado: {a.curriculo_analisado.rotulo}
        </span>
      </div>
      <p className="text-xs">
        <b>❌ {a.resumo.nao_tenho}</b> não tenho · <b>⚠️ {a.resumo.tenho}</b> tenho, mas o currículo não deixa claro ·{" "}
        {a.resumo.sem_resposta} sem resposta
      </p>
      {a.avisos.map((t, i) => (
        <p key={i} className="text-[11px] text-amber-700 dark:text-amber-300">
          {t}
        </p>
      ))}

      {grupos.map(({ g, itens }) => (
        <div key={g} className="space-y-1.5">
          <h5 className="font-semibold text-xs text-slate-800 dark:text-slate-200">→ {a.grupos[g]}</h5>
          <ul className="space-y-1.5 text-xs">
            {itens.map((m) => (
              <Motivo key={m.i} m={m} />
            ))}
          </ul>
        </div>
      ))}

      {a.perguntas.length > 0 && (
        <div className="space-y-2">
          <h5 className="font-semibold text-xs text-slate-800 dark:text-slate-200">
            Perguntas: você tem essa experiência?{" "}
            <span className={DICA}>{salvo === "salvando" ? "salvando…" : salvo === "salvo" ? "salvo" : ""}</span>
          </h5>
          <ol className="space-y-2.5 text-xs">
            {a.perguntas.map((p) => {
              const r = respostas[String(p.n)]
              const levado = Boolean(r?.levado)
              const travado = bloqueado || levado
              return (
                <li key={p.n} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 space-y-1.5">
                  <p>
                    <b>{p.n}.</b> {p.texto}
                  </p>
                  <div className="flex gap-1.5 flex-wrap">
                    <Opcao ligada={r?.resposta === "nao"} disabled={travado} onClick={() => responder(p.n, { resposta: "nao" })}>
                      ❌ Não tenho
                    </Opcao>
                    <Opcao
                      ligada={r?.resposta === "tenho"}
                      disabled={travado}
                      onClick={() => responder(p.n, { resposta: "tenho", relato: r?.relato || "", destino: r?.destino || "so_aqui" })}
                    >
                      ⚠️ Tenho
                    </Opcao>
                    <Opcao ligada={r?.resposta === "pular"} disabled={travado} onClick={() => responder(p.n, { resposta: "pular" })}>
                      Pular
                    </Opcao>
                  </div>
                  {r?.resposta === "tenho" && (
                    <div className="space-y-1.5">
                      <textarea
                        value={r.relato || ""}
                        disabled={travado}
                        rows={3}
                        maxLength={4000}
                        placeholder="Conte com as suas palavras onde, quando e o que você fez."
                        onChange={(ev) => responder(p.n, { ...r, relato: ev.target.value })}
                        className="w-full p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                      />
                      {levado ? (
                        <p className={DICA}>Levado ao seu perfil. Para mudar, edite em Meu perfil → Seus relatos.</p>
                      ) : (
                        <div className="flex gap-1.5 flex-wrap items-center">
                          <span className={DICA}>Esse relato:</span>
                          <Opcao ligada={r.destino === "perfil"} disabled={travado} onClick={() => responder(p.n, { ...r, destino: "perfil" })}>
                            Levar ao meu perfil
                          </Opcao>
                          <Opcao
                            ligada={(r.destino || "so_aqui") === "so_aqui"}
                            disabled={travado}
                            onClick={() => responder(p.n, { ...r, destino: "so_aqui" })}
                          >
                            Usar só neste currículo
                          </Opcao>
                        </div>
                      )}
                      {!levado && r.destino === "perfil" && (
                        <p className={DICA}>Vai para o seu perfil quando você clicar em Reescrever e gerar (a versão anterior fica guardada).</p>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
        </div>
      )}

      {a.respostas_mudaram && <p className="text-[11px] text-amber-700 dark:text-amber-300">As respostas mudaram desde o último currículo.</p>}
      {nLevados > 0 && <p className={DICA}>Levados ao seu perfil: {nLevados} relato(s).</p>}
      {erro && <p className="text-xs text-rose-700 dark:text-rose-300">{erro}</p>}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          disabled={!pronta || ativa || enviando || bloqueado || servidor !== "no_ar"}
          onClick={gerar}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
        >
          {enviando && <Loader2 className="w-4 h-4 animate-spin" />}
          {a.curriculo_gerado ? "Reescrever e gerar de novo" : "Reescrever e gerar o currículo"}
        </button>
        {!pronta && <span className={DICA}>Responda ou pule as perguntas.</span>}
        {pronta && ativa && !minha && <span className={DICA}>Há outro documento sendo gerado; espere ele terminar.</span>}
        {!podeAlterar && <span className={DICA}>Só dá para responder e gerar no computador onde a ferramenta roda.</span>}
      </div>

      {a.reescritos.length > 0 && (
        <div className="space-y-1.5">
          <h5 className="font-semibold text-xs text-slate-800 dark:text-slate-200">Trechos reescritos (antes → depois)</h5>
          <ul className="space-y-1.5 text-xs">
            {a.reescritos.map((x, i) => (
              <li key={i} className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                <p className="text-slate-500 dark:text-slate-400 line-through decoration-slate-400/60">{x.original}</p>
                <p>→ {x.novo}</p>
                {x.avisos.map((t, j) => (
                  <p key={j} className="text-[11px] text-amber-700 dark:text-amber-300">
                    Confira: {t}
                  </p>
                ))}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
