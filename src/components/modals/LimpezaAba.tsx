/**
 * Aba Limpeza dos filtros da busca (spec 054): critérios por grupo, prévia do que seria limpo e arquivamento das vagas
 * marcadas. Tem fluxo próprio (PUT /api/limpeza, GET /api/limpeza/previa, POST /api/limpeza/aplicar).
 */
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import * as limpezaApi from "../../services/api/limpeza"
import { mensagemDeErro } from "../../services/api"
import { AvisoSoLeitura } from "../../contexto/Ferramenta"
import { ETAPAS, GRUPOS_LIMPEZA, RESULTADOS_LIMPEZA } from "../../utils/rotulos"
import type {
  CriteriosLimpeza,
  GrupoLimpeza,
  GrupoRepetido,
  PreviaLimpeza,
  RespostaAplicarLimpeza,
  RespostaJuntar,
  ResultadoLimpeza,
  ResumoRepetida,
} from "../../types/api"

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"
const AVISO_AMBAR =
  "p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs"
const BOTAO =
  "px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed transition"

const GRUPOS: GrupoLimpeza[] = ["fora", "pendente", "dispensadas", "sem_resposta"]

const ORIGEM_DO_PRAZO: Record<GrupoLimpeza, string> = {
  fora: "conta do dia em que a vaga caiu em Fora",
  pendente: "conta do dia em que a vaga foi encontrada",
  dispensadas: "conta do dia em que foi dispensada ou encerrada",
  sem_resposta: "conta do dia em que a candidatura foi enviada; a vaga passa para Encerrada, Sem resposta",
}

function rotuloEtapa(etapa: string | null): string {
  if (!etapa) return ""
  return ETAPAS.find((e) => e.valor === etapa)?.rotulo ?? etapa
}

function formatarLinhaVaga(v: ResumoRepetida): string {
  const partes = [`${v.titulo} · ${v.empresa} · ${v.plataforma}`]
  const rotulo = rotuloEtapa(v.etapa)
  if (rotulo) partes.push(rotulo)
  if (v.aderencia !== null && v.aderencia !== undefined) partes.push(`nota ${v.aderencia}`)
  return partes.join(" · ")
}

export default function LimpezaAba({ podeSalvar }: { podeSalvar: boolean }) {
  const [criterios, setCriterios] = useState<CriteriosLimpeza | null>(null)
  const [arquivadas, setArquivadas] = useState(0)
  const [tamanhoKb, setTamanhoKb] = useState(0)
  const [previa, setPrevia] = useState<PreviaLimpeza | null>(null)
  const [marcadas, setMarcadas] = useState<Set<string>>(new Set())
  const [vendo, setVendo] = useState(false)
  const [aplicando, setAplicando] = useState(false)
  const [erro, setErro] = useState("")
  const [resultado, setResultado] = useState<RespostaAplicarLimpeza | null>(null)

  const [gruposRepetidos, setGruposRepetidos] = useState<GrupoRepetido[] | null>(null)
  const [marcadosRepetidos, setMarcadosRepetidos] = useState<Set<string>>(new Set())
  const [buscandoRepetidas, setBuscandoRepetidas] = useState(false)
  const [juntandoRepetidos, setJuntandoRepetidos] = useState(false)
  const [erroRepetidas, setErroRepetidas] = useState("")
  const [resultadoRepetidas, setResultadoRepetidas] = useState<RespostaJuntar | null>(null)

  useEffect(() => {
    let vivo = true
    limpezaApi
      .ler()
      .then((r) => {
        if (!vivo) return
        setCriterios(r.criterios)
        setArquivadas(r.arquivadas)
        setTamanhoKb(r.tamanho_kb)
      })
      .catch((e) => vivo && setErro(mensagemDeErro(e, "Não foi possível ler os critérios de limpeza.")))
    return () => {
      vivo = false
    }
  }, [])

  if (!criterios) {
    return erro ? (
      <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">
        {erro}
      </p>
    ) : (
      <p className={`${DICA} flex items-center gap-2`}>
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando…
      </p>
    )
  }

  const mudarGrupo = <G extends GrupoLimpeza>(g: G, parte: Partial<CriteriosLimpeza[G]>) =>
    setCriterios({ ...criterios, [g]: { ...criterios[g], ...parte } })

  const alternarResultado = (r: ResultadoLimpeza) => {
    const atuais = criterios.dispensadas.resultados
    mudarGrupo("dispensadas", {
      resultados: atuais.includes(r) ? atuais.filter((x) => x !== r) : [...atuais, r],
    })
  }

  const verPrevia = async () => {
    setVendo(true)
    setErro("")
    setResultado(null)
    try {
      await limpezaApi.gravar(criterios)
      const p = await limpezaApi.previa()
      setPrevia(p)
      const ids = new Set<string>()
      for (const g of GRUPOS) {
        if (!p.grupos[g].ligado) continue
        for (const v of p.grupos[g].vagas) if (!v.destaques?.length) ids.add(v.id)
      }
      setMarcadas(ids)
    } catch (e) {
      setErro(mensagemDeErro(e, "Não foi possível gerar a prévia da limpeza."))
    } finally {
      setVendo(false)
    }
  }

  const alternarVaga = (id: string) =>
    setMarcadas((s) => {
      const novo = new Set(s)
      if (novo.has(id)) novo.delete(id)
      else novo.add(id)
      return novo
    })

  const n = marcadas.size

  const procurarRepetidas = async () => {
    setBuscandoRepetidas(true)
    setErroRepetidas("")
    setResultadoRepetidas(null)
    try {
      const r = await limpezaApi.repetidas()
      setGruposRepetidos(r.grupos)
      setMarcadosRepetidos(new Set(r.grupos.map((g) => g.ids[0])))
    } catch (e) {
      setErroRepetidas(mensagemDeErro(e, "Não foi possível procurar vagas repetidas."))
    } finally {
      setBuscandoRepetidas(false)
    }
  }

  const alternarGrupoRepetido = (idPrincipal: string) => {
    setMarcadosRepetidos((prev) => {
      const prox = new Set(prev)
      if (prox.has(idPrincipal)) prox.delete(idPrincipal)
      else prox.add(idPrincipal)
      return prox
    })
  }

  const gruposRepetidosMarcados = (gruposRepetidos ?? []).filter((g) => marcadosRepetidos.has(g.ids[0]))
  const nRepetidos = gruposRepetidosMarcados.length

  const juntarRepetidas = async () => {
    if (!gruposRepetidos) return
    const gruposParaJuntar = gruposRepetidos.filter((g) => marcadosRepetidos.has(g.ids[0]))
    const nGrupos = gruposParaJuntar.length
    if (nGrupos === 0) return
    if (
      !window.confirm(
        `Juntar ${nGrupos} grupos de vagas repetidas? As outras vagas de cada grupo saem das listas (fica uma cópia do banco de antes).`,
      )
    ) {
      return
    }
    setJuntandoRepetidos(true)
    setErroRepetidas("")
    setResultadoRepetidas(null)
    try {
      const r = await limpezaApi.juntar(gruposParaJuntar.map((g) => g.ids))
      setResultadoRepetidas(r)
      setGruposRepetidos(null)
      setMarcadosRepetidos(new Set())
    } catch (e) {
      setErroRepetidas(mensagemDeErro(e, "Não foi possível juntar as vagas repetidas."))
    } finally {
      setJuntandoRepetidos(false)
    }
  }

  const arquivar = async () => {
    if (
      !window.confirm(
        `Limpar ${n} vagas? As arquivadas perdem a descrição e a análise (fica uma cópia do banco de antes).`,
      )
    )
      return
    setAplicando(true)
    setErro("")
    try {
      const r = await limpezaApi.aplicar([...marcadas])
      setResultado(r)
      setPrevia(null)
      setMarcadas(new Set())
      const estado = await limpezaApi.ler()
      setArquivadas(estado.arquivadas)
      setTamanhoKb(estado.tamanho_kb)
    } catch (e) {
      setErro(mensagemDeErro(e, "Não foi possível arquivar as vagas."))
    } finally {
      setAplicando(false)
    }
  }

  return (
    <>
      <p className={DICA}>
        Arquiva as vagas que ficaram para trás: elas saem das listas e dos contadores, a descrição e a análise são
        apagadas e só fica uma ficha curta, para a busca não trazê-las de novo. As aplicações sem retorno passam para
        Encerrada, com o resultado Sem resposta. Antes de gravar, a ferramenta guarda uma cópia do banco.
      </p>

      {GRUPOS.map((g) => {
        const c = criterios[g]
        return (
          <section key={g} className={SEC}>
            <h4 className={H}>{GRUPOS_LIMPEZA[g]}</h4>
            <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={c.ligado}
                disabled={!podeSalvar}
                onChange={(e) => mudarGrupo(g, { ligado: e.target.checked } as Partial<CriteriosLimpeza[typeof g]>)}
              />
              Entra na limpeza
            </label>
            <div className="flex items-end gap-2">
              <div className="w-32">
                <label className={ROTULO} htmlFor={`limpeza-dias-${g}`}>
                  Sem movimento há pelo menos
                </label>
                <input
                  id={`limpeza-dias-${g}`}
                  type="number"
                  min={1}
                  max={365}
                  value={c.dias}
                  disabled={!podeSalvar}
                  onChange={(e) =>
                    mudarGrupo(g, { dias: Number(e.target.value) } as Partial<CriteriosLimpeza[typeof g]>)
                  }
                  className={CAMPO}
                />
              </div>
              <span className={`${DICA} pb-2.5`}>dias</span>
            </div>
            {g === "pendente" && (
              <div className="w-32">
                <label className={ROTULO} htmlFor="limpeza-nota">
                  Só com nota abaixo de
                </label>
                <input
                  id="limpeza-nota"
                  type="number"
                  min={1}
                  max={100}
                  value={criterios.pendente.nota_abaixo_de ?? ""}
                  disabled={!podeSalvar}
                  onChange={(e) =>
                    mudarGrupo("pendente", {
                      nota_abaixo_de: e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                  className={CAMPO}
                />
                <p className={`${DICA} w-96 max-w-full mt-1`}>
                  vazio: todas; as vagas ainda sem nota ficam de fora quando há um limite
                </p>
              </div>
            )}
            {g === "dispensadas" && (
              <div className="space-y-1">
                {(Object.keys(RESULTADOS_LIMPEZA) as ResultadoLimpeza[]).map((r) => (
                  <label key={r} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <input
                      type="checkbox"
                      checked={criterios.dispensadas.resultados.includes(r)}
                      disabled={!podeSalvar}
                      onChange={() => alternarResultado(r)}
                    />
                    {RESULTADOS_LIMPEZA[r]}
                  </label>
                ))}
                <p className={DICA}>Contratado nunca entra.</p>
              </div>
            )}
            <p className={DICA}>{ORIGEM_DO_PRAZO[g]}</p>
          </section>
        )
      })}

      <div className="space-y-3">
        <button type="button" onClick={verPrevia} disabled={!podeSalvar || vendo || aplicando} className={BOTAO}>
          {vendo ? "Gerando…" : "Ver o que seria limpo"}
        </button>

        {erro && (
          <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">
            {erro}
          </p>
        )}

        {previa && previa.total === 0 && <p className={DICA}>Nada para limpar com estes critérios.</p>}

        {previa && previa.total > 0 && (
          <div className="space-y-3">
            {previa.destacadas > 0 && (
              <p className={AVISO_AMBAR}>
                {previa.destacadas} vaga(s) com currículo, carta ou anotação vêm desmarcadas:                 marque só se quiser limpá-las.
                                Arquivar apaga os currículos, cartas e respostas delas.
              </p>
            )}
            {GRUPOS.filter((g) => previa.grupos[g].ligado && previa.grupos[g].vagas.length > 0).map((g) => {
              const gp = previa.grupos[g]
              return (
                <details key={g} open className="rounded-xl border border-slate-200 dark:border-slate-700 p-2">
                  <summary className="text-xs font-semibold text-slate-800 dark:text-slate-200 cursor-pointer">
                    {GRUPOS_LIMPEZA[g]}: {gp.vagas.length} vaga(s) —{" "}
                    {gp.acao === "encerrar" ? "passam para Encerrada, Sem resposta" : "serão arquivadas"}
                  </summary>
                  <ul className="mt-2 space-y-1">
                    {gp.vagas.map((v) => {
                      const destacada = !!v.destaques?.length
                      return (
                        <li
                          key={v.id}
                          className={`rounded-lg px-2 py-1 ${
                            destacada ? "bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900" : ""
                          }`}
                        >
                          <label className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                            <input
                              type="checkbox"
                              className="mt-0.5"
                              checked={marcadas.has(v.id)}
                              disabled={!podeSalvar}
                              onChange={() => alternarVaga(v.id)}
                            />
                            <span>
                              {v.titulo} · {v.empresa} · {v.plataforma} · há {v.dias} dias
                              {destacada && (
                                <span className="block text-amber-900 dark:text-amber-200">
                                  {v.destaques.join(", ")}
                                </span>
                              )}
                            </span>
                          </label>
                        </li>
                      )
                    })}
                  </ul>
                </details>
              )
            })}
            <button type="button" onClick={arquivar} disabled={n === 0 || !podeSalvar || aplicando} className={BOTAO}>
              {aplicando ? "Arquivando…" : `Arquivar ${n} vagas`}
            </button>
          </div>
        )}

        {resultado && (
          <p className={`${DICA} !text-emerald-700 dark:!text-emerald-400`}>
            {resultado.arquivadas} arquivada(s), {resultado.encerradas} encerrada(s) sem resposta. Banco:{" "}
            {resultado.antes_kb} KB → {resultado.depois_kb} KB. Cópia de antes: {resultado.backup}.
                        {resultado.nao_arquivadas && resultado.nao_arquivadas.length > 0 && (
                          <>
                            <br />
                            {resultado.nao_arquivadas.length} vaga(s) não arquivada(s): {resultado.nao_arquivadas[0].motivo}
                          </>
                        )}          </p>
        )}
      </div>

      <p className={DICA}>
        Já arquivadas: {arquivadas} · banco com {tamanhoKb} KB.
      </p>

      <section className={SEC}>
        <h4 className={H}>Vagas repetidas</h4>
        <p className={DICA}>
          A mesma vaga anunciada em mais de um portal, ou com a empresa escrita de outro jeito. Juntar
          deixa uma vaga só (a principal) com as etiquetas de todos os portais, a etapa mais adiantada, as anotações e os
          currículos das outras; as outras saem das listas. Antes, a ferramenta guarda uma cópia do banco.
        </p>

        <button
          type="button"
          onClick={procurarRepetidas}
          disabled={!podeSalvar || buscandoRepetidas}
          className={BOTAO}
        >
          {buscandoRepetidas ? "Procurando…" : "Procurar repetidas"}
        </button>

        {erroRepetidas && (
          <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">
            {erroRepetidas}
          </p>
        )}

        {gruposRepetidos && gruposRepetidos.length === 0 && (
          <p className={DICA}>Nenhuma vaga repetida.</p>
        )}

        {gruposRepetidos && gruposRepetidos.length > 0 && (
          <div className="space-y-3">
            <div className="space-y-2">
              {gruposRepetidos.map((g) => {
                const idPrincipal = g.ids[0]
                const marcado = marcadosRepetidos.has(idPrincipal)
                return (
                  <div
                    key={idPrincipal}
                    className="rounded-xl border border-slate-200 dark:border-slate-700 p-2"
                  >
                    <label className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                      <input
                        type="checkbox"
                        className="mt-0.5"
                        checked={marcado}
                        disabled={!podeSalvar}
                        onChange={() => alternarGrupoRepetido(idPrincipal)}
                      />
                      <div className="space-y-1">
                        <div>
                          <span className="font-semibold text-slate-800 dark:text-slate-200">Fica:</span>{" "}
                          {formatarLinhaVaga(g.principal)}
                        </div>
                        {g.outras.map((outra) => (
                          <div key={outra.id}>
                            <span className="font-semibold text-slate-800 dark:text-slate-200">Junta:</span>{" "}
                            {formatarLinhaVaga(outra)}
                          </div>
                        ))}
                        {g.etapa_final && g.etapa_final !== g.principal.etapa && (
                          <div className="text-amber-900 dark:text-amber-200 font-medium">
                            Etapa final: {rotuloEtapa(g.etapa_final)}
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                )
              })}
            </div>
            <button
              type="button"
              onClick={juntarRepetidas}
              disabled={nRepetidos === 0 || !podeSalvar || juntandoRepetidos}
              className={BOTAO}
            >
              {juntandoRepetidos ? "Juntando…" : `Juntar ${nRepetidos} grupos`}
            </button>
          </div>
        )}

        {resultadoRepetidas && (
          <p className={`${DICA} !text-emerald-700 dark:!text-emerald-400`}>
            {resultadoRepetidas.juntados} grupo(s) juntado(s), {resultadoRepetidas.vagas} vaga(s) a menos. Cópia de antes: {resultadoRepetidas.backup}.
            {resultadoRepetidas.ignorados.length > 0 &&
              ` ${resultadoRepetidas.ignorados.length} grupo(s) mudaram desde a prévia e ficaram de fora.`}
          </p>
        )}
      </section>

      {!podeSalvar && <AvisoSoLeitura />}
    </>
  )
}
