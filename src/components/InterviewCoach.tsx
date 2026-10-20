/**
 * Preparar entrevista (dash/API.md §3.10), como no dashboard antigo: dossiê (com o texto da empresa colado pela
 * pessoa e o resumo com IA), perguntas prováveis, histórias (rascunhos da IA só salvos na confirmação), simulação,
 * salário (sem valor inventado) e as anotações de como foi. Nada é pesquisado na internet.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react"
import { Loader2, AlertTriangle, MessageSquare } from "lucide-react"
import type { Vaga } from "../types/api"
import * as entrevistaApi from "../services/api/entrevista"
import type { Entrevista, Historia, RetornoSimulacao } from "../services/api/entrevista"
import { mensagemDeErro } from "../services/api"
import { useFerramenta, textoCustoIA } from "../contexto/Ferramenta"
import { diaMes, hoje } from "../utils/formatters"
import { AUTORIZACAO, CONTRATACAO, INGLES } from "../utils/rotulos"
import { BTN_MINI } from "./curriculo/Curriculos"

interface Props {
  /** Vagas do quadro (a página escolhe as em Entrevista primeiro). */
  vagas: Vaga[]
  vagaId: string | null
  onEscolherVaga: (id: string) => void
  onAviso: (m: string, t?: "info" | "erro") => void
  onAbrirPerfil: () => void
}

const ABAS = [
  ["dossie", "Dossiê"],
  ["perguntas", "Perguntas"],
  ["historias", "Histórias"],
  ["simular", "Simular"],
  ["salario", "Salário"],
  ["depois", "Depois"],
] as const
type Aba = (typeof ABAS)[number][0]

const ORIGEM: Record<string, string> = { vaga: "Da vaga", texto: "Do seu texto", deducao: "Dedução: confirme antes de usar" }
const ORIGEM_Q: Record<string, string> = {
  padrao: "Lista padrão",
  requisito: "Requisito da vaga",
  lacuna: "Lacuna da análise",
  rodada: "Caiu antes",
  ia: "Sugerida pela IA",
}
const STAR: [keyof Historia, string][] = [
  ["situacao", "Situação"],
  ["tarefa", "Tarefa"],
  ["acao", "Ação"],
  ["resultado", "Resultado"],
  ["reflexao", "O que você aprendeu"],
]
const SEC = "bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 space-y-3"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const BTN_PRI = "flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
const BTN_SEC =
  "px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"
const BLOCO = "p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1"

function Lista({ itens }: { itens?: string[] }) {
  if (!itens || !itens.length) return null
  return (
    <ul className="list-disc pl-5 space-y-0.5">
      {itens.map((x, i) => (
        <li key={i}>{x}</li>
      ))}
    </ul>
  )
}

/** Formulário de uma história (fora do componente da página, para não perder o que se digita quando ela atualiza). */
function FormHistoria({
  h,
  chave,
  bloq,
  onSalvar,
  onDescartar,
}: {
  h: Historia
  chave: string
  bloq: boolean
  onSalvar: (h: Historia, f: Historia, chave: string) => void
  onDescartar: (chave: string) => void
}) {
  const [f, setF] = useState<Historia>({ ...h })
  return (
    <div className={`${BLOCO} space-y-2`}>
      <label className="block text-xs font-semibold">
        Título
        <input value={f.titulo || ""} maxLength={120} onChange={(ev) => setF({ ...f, titulo: ev.target.value })} className={CAMPO} />
      </label>
      {STAR.map(([k, r]) => (
        <label key={k} className="block text-xs font-semibold">
          {r}
          <textarea rows={2} maxLength={1200} value={String(f[k] || "")} onChange={(ev) => setF({ ...f, [k]: ev.target.value })} className={CAMPO} />
        </label>
      ))}
      {h.conquista && <p className={DICA}>Do perfil: “{h.conquista}”</p>}
      {(h.perguntas || []).length > 0 && <p className={DICA}>Responde: {(h.perguntas || []).join("; ")}</p>}
      {(h.conferir || []).length > 0 && (
        <p className="text-[11px] text-amber-700 dark:text-amber-300">Confira antes de salvar: {(h.conferir || []).join("; ")}</p>
      )}
      <div className="flex gap-2">
        <button type="button" disabled={bloq} onClick={() => onSalvar(h, f, chave)} className={BTN_PRI}>
          Salvar esta história
        </button>
        <button type="button" onClick={() => onDescartar(chave)} className={BTN_SEC}>
          {chave.startsWith("r") ? "Descartar" : "Cancelar"}
        </button>
      </div>
    </div>
  )
}

export default function InterviewCoach({ vagas, vagaId, onEscolherVaga, onAviso, onAbrirPerfil }: Props) {
  const { ia, podeGravar, tratarErro, abrirPainelIA } = useFerramenta()
  const ordenadas = useMemo(
    () => [...vagas].sort((a, b) => Number(b.etapa === "entrevista") - Number(a.etapa === "entrevista")),
    [vagas],
  )
  const atual = vagaId && vagas.some((v) => v.id === vagaId) ? vagaId : ordenadas[0]?.id || null

  const [d, setD] = useState<Entrevista | null>(null)
  const [aba, setAba] = useState<Aba>("dossie")
  const [erro, setErro] = useState("")
  const [ocupado, setOcupado] = useState("")
  const [rascunhos, setRascunhos] = useState<Historia[]>([])
  const [editando, setEditando] = useState<string | null>(null)
  const [rmConfirma, setRmConfirma] = useState<string | null>(null)
  const [textoEmpresa, setTextoEmpresa] = useState("")
  const [sim, setSim] = useState<{
    i: number
    idioma: "pt" | "en"
    rascunho: string
    resposta?: string
    retorno?: RetornoSimulacao | null
    fim?: boolean
  } | null>(null)
  const [idiomaSim, setIdiomaSim] = useState<"pt" | "en">("pt")
  const [rodada, setRodada] = useState({ data: hoje(), etapa: "", perguntas: "", bem: "", mal: "", proximos: "" })

  const carregar = useCallback(async (id: string) => {
    try {
      const j = await entrevistaApi.ler(id)
      setD(j)
      setTextoEmpresa(j.dossie.texto_empresa || "")
      setIdiomaSim(j.simulacao?.idioma || "pt")
      return j
    } catch (e) {
      setErro(mensagemDeErro(e, "Não deu para abrir a preparação."))
      return null
    }
  }, [])

  useEffect(() => {
    setD(null)
    setErro("")
    setRascunhos([])
    setEditando(null)
    setSim(null)
    setAba("dossie")
    if (atual) carregar(atual)
  }, [atual, carregar])

  const pedir = async <T,>(chave: string, fn: () => Promise<T>, depois?: (r: T) => unknown) => {
    setOcupado(chave)
    setErro("")
    try {
      const r = await fn()
      if (depois) await depois(r)
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e))
    } finally {
      setOcupado("")
    }
  }

  if (!ordenadas.length) {
    return (
      <div className={SEC}>
        <h3 className={H}>Preparar entrevista</h3>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Nenhuma vaga no quadro ainda. Siga com uma vaga no Relatório para preparar a entrevista dela.
        </p>
      </div>
    )
  }

  const comIA = Boolean(d?.ia)
  const semIA = (oque: string) =>
    comIA ? null : (
      <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs text-amber-900 dark:text-amber-200">
        {oque} precisa de uma IA: escolha uma no{" "}
        <button type="button" onClick={abrirPainelIA} className="underline font-semibold">
          botão IA
        </button>
        , ou peça no chat do seu assistente (skill preparar-entrevista).
      </p>
    )
  const custo = comIA && ia?.cobranca === "uso" ? <p className={DICA}>{textoCustoIA(ia)}</p> : null
  const bloq = !podeGravar || Boolean(ocupado)

  const salvarHistoria = (h: Historia, f: Historia, chave: string) => {
    const rascunho = chave.startsWith("r") ? Number(chave.slice(1)) : -1
    if (!atual) return
    pedir(
      "salvar",
      () =>
        entrevistaApi.salvarHistoria({
          ...f,
          perguntas: h.perguntas || [],
          conquista: h.conquista || "",
          conferir: h.conferir || [],
          ...(chave !== "nova" && rascunho < 0 ? { id: chave } : {}),
        }),
      async () => {
        if (rascunho >= 0) setRascunhos((l) => l.filter((_, i) => i !== rascunho))
        else setEditando(null)
        onAviso("História salva.")
        await carregar(atual)
      },
    )
  }
  const descartarHistoria = (chave: string) => {
    const rascunho = chave.startsWith("r") ? Number(chave.slice(1)) : -1
    if (rascunho >= 0) setRascunhos((l) => l.filter((_, i) => i !== rascunho))
    else setEditando(null)
  }

  let corpo: React.ReactNode = null
  if (d && atual) {
    const ds = d.dossie
    if (aba === "dossie") {
      const campos: [string, React.ReactNode][] = [
        ["Resumo da análise", ds.resumo],
        ["Faixa da vaga", ds.salario ? `${ds.salario}${ds.moeda ? ` (${ds.moeda})` : ""}` : null],
        ["Autorização de trabalho", ds.autorizacao ? AUTORIZACAO[ds.autorizacao.valor] || ds.autorizacao.valor : null],
        ["Contratação", ds.contratacao?.length ? ds.contratacao.map((c) => CONTRATACAO[c.valor] || c.valor).join(", ") : null],
        ["Inglês", ds.ingles ? INGLES[ds.ingles.nivel] || ds.ingles.nivel : null],
        ["Fuso", ds.fuso?.texto],
        ["Suas anotações", ds.anotacao],
      ]
      const r = ds.resumo_ia
      corpo = (
        <>
          <section className={SEC}>
            <h4 className={H}>O que a ferramenta já tem</h4>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-xs">
              {campos.filter(([, v]) => v).map(([k, v]) => (
                <React.Fragment key={k}>
                  <dt className="font-semibold text-slate-500">{k}</dt>
                  <dd className="whitespace-pre-wrap">{v}</dd>
                </React.Fragment>
              ))}
            </dl>
            {(
              [
                ["Encaixe", ds.encaixe],
                ["Lacunas", ds.lacunas],
                ["Atenção", ds.alertas],
              ] as [string, string[] | undefined][]
            ).map(([t, l]) =>
              l && l.length ? (
                <div key={t} className="text-xs">
                  <b>{t}</b>
                  <Lista itens={l} />
                </div>
              ) : null,
            )}
            {!ds.resumo && !(ds.lacunas || []).length && (
              <p className={DICA}>Esta vaga ainda não tem análise; a descrição dela está no detalhe da vaga.</p>
            )}
          </section>
          <section className={SEC}>
            <h4 className={H}>Sobre a empresa</h4>
            <p className={DICA}>
              Cole o que você leu sobre a empresa (site, notícias, o que o recrutador contou). A ferramenta não pesquisa na
              internet.
            </p>
            <textarea rows={5} maxLength={20000} value={textoEmpresa} disabled={!podeGravar} onChange={(ev) => setTextoEmpresa(ev.target.value)} className={CAMPO} />
            <button
              type="button"
              disabled={bloq}
              onClick={() => pedir("empresa", () => entrevistaApi.salvarEmpresa(atual, textoEmpresa), async () => {
                onAviso("Texto sobre a empresa salvo.")
                await carregar(atual)
              })}
              className={BTN_SEC}
            >
              Salvar o texto
            </button>
          </section>
          <section className={SEC}>
            <h4 className={H}>Resumo com IA</h4>
            {semIA("O resumo")}
            <p className={DICA}>Cada ponto mostra de onde veio: da vaga, do seu texto, ou dedução da IA (confirme antes de usar).</p>
            {r?.itens?.map((i, n) => (
              <div key={n} className={`${BLOCO} text-xs ${i.origem === "deducao" ? "border-amber-300 dark:border-amber-800" : ""}`}>
                <b>{i.ponto}</b>
                <p className={DICA}>
                  {ORIGEM[i.origem] || i.origem}
                  {i.trecho ? `: “${i.trecho}”` : ""}
                </p>
              </div>
            ))}
            {custo}
            <button type="button" disabled={bloq || !comIA} onClick={() => pedir("resumo", () => entrevistaApi.resumir(atual), () => carregar(atual))} className={BTN_MINI}>
              {ocupado === "resumo" ? "Resumindo…" : r ? "Resumir de novo" : "Resumir com IA"}
            </button>
          </section>
        </>
      )
    } else if (aba === "perguntas") {
      corpo = (
        <section className={SEC}>
          <h4 className={H}>Perguntas prováveis ({d.perguntas.length})</h4>
          <p className={DICA}>Pelo que a vaga pede, pelas lacunas da análise e pelo que caiu antes. Treine as respostas na aba Simular.</p>
          {d.perguntas.map((q, n) => (
            <div key={n} className={`${BLOCO} text-xs`}>
              <b>{q.texto}</b>
              {q.texto_en && q.texto_en !== q.texto && <p className="italic text-slate-500">{q.texto_en}</p>}
              <p className={DICA}>
                {q.tipo === "tecnica" ? "Técnica" : "Comportamental"} · {ORIGEM_Q[q.origem] || q.origem} · {q.porque}
              </p>
            </div>
          ))}
          {semIA("Sugerir mais perguntas")}
          {custo}
          <button
            type="button"
            disabled={bloq || !comIA}
            onClick={() => pedir("perguntas", () => entrevistaApi.maisPerguntas(atual), (j) => setD((x) => (x ? { ...x, perguntas: j.perguntas } : x)))}
            className={BTN_MINI}
          >
            {ocupado === "perguntas" ? "Pensando…" : "Mais perguntas com IA"}
          </button>
        </section>
      )
    } else if (aba === "historias") {
      corpo = (
        <>
          <section className={SEC}>
            <h4 className={H}>Suas histórias ({d.historias.length})</h4>
            <p className={DICA}>
              Situação, tarefa, ação, resultado e o que você aprendeu. Ficam guardadas para as próximas entrevistas, só neste
              computador.
            </p>
            {d.historias.map((x) =>
              editando === x.id ? (
                <FormHistoria key={x.id} h={x} chave={x.id || ""} bloq={bloq} onSalvar={salvarHistoria} onDescartar={descartarHistoria} />
              ) : (
                <div key={x.id} className={`${BLOCO} text-xs`}>
                  <b>{x.titulo}</b>
                  {STAR.filter(([k]) => x[k]).map(([k, r]) => (
                    <p key={k}>
                      <b>{r}:</b> {String(x[k])}
                    </p>
                  ))}
                  {(x.perguntas || []).length > 0 && <p className={DICA}>Responde: {(x.perguntas || []).join("; ")}</p>}
                  <div className="flex gap-3">
                    <button type="button" disabled={!podeGravar} onClick={() => { setEditando(x.id || null); setRmConfirma(null) }} className="underline">
                      Editar
                    </button>
                    <button
                      type="button"
                      disabled={bloq}
                      onClick={() => {
                        if (rmConfirma !== x.id) return setRmConfirma(x.id || null)
                        setRmConfirma(null)
                        pedir("remover", () => entrevistaApi.removerHistoria(x.id || ""), async () => {
                          onAviso("História removida.")
                          await carregar(atual)
                        })
                      }}
                      className={rmConfirma === x.id ? "underline font-semibold text-rose-600" : "underline"}
                    >
                      {rmConfirma === x.id ? "Confirmar remoção" : "Remover"}
                    </button>
                  </div>
                </div>
              ),
            )}
            {editando === "nova" && (
              <FormHistoria
                h={{ titulo: "", situacao: "", tarefa: "", acao: "", resultado: "", reflexao: "" }}
                chave="nova"
                bloq={bloq}
                onSalvar={salvarHistoria}
                onDescartar={descartarHistoria}
              />
            )}
            <div className="flex gap-2 flex-wrap items-center">
              <button type="button" disabled={editando === "nova" || !podeGravar} onClick={() => setEditando("nova")} className={BTN_SEC}>
                Escrever uma
              </button>
              {comIA && (
                <button
                  type="button"
                  disabled={bloq}
                  onClick={() => pedir("sugerir", () => entrevistaApi.sugerirHistorias(atual), (j) => setRascunhos(j.rascunhos || []))}
                  className={BTN_MINI}
                >
                  {ocupado === "sugerir" ? "Montando…" : "Sugerir histórias com IA"}
                </button>
              )}
              {custo}
            </div>
            {!d.existe_perfil && (
              <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-xs">
                Sem perfil, a IA não tem conquistas para usar:{" "}
                <button type="button" onClick={onAbrirPerfil} className="underline font-semibold">
                  monte o perfil
                </button>
                .
              </p>
            )}
          </section>
          {rascunhos.length > 0 && (
            <section className={SEC}>
              <h4 className={H}>Rascunhos da IA (não salvos)</h4>
              <p className={DICA}>Só com fatos do seu perfil. Edite e salve os que servirem; os outros somem ao sair.</p>
              {rascunhos.map((r, i) => (
                <FormHistoria key={`r${i}-${r.titulo}`} h={r} chave={`r${i}`} bloq={bloq} onSalvar={salvarHistoria} onDescartar={descartarHistoria} />
              ))}
            </section>
          )}
        </>
      )
    } else if (aba === "simular") {
      const qs = d.perguntas
      const s = sim
      const feitas = d.simulacao?.respostas?.length || 0
      if (!s || s.fim) {
        const treinar = (d.simulacao?.respostas || []).filter((r) => r.retorno?.faltou).map((r) => r.retorno!.faltou)
        corpo = (
          <section className={SEC}>
            <h4 className={H}>Simulação</h4>
            <p className={DICA}>
              Uma pergunta por vez; você responde por escrito{comIA ? " e a IA dá um retorno honesto, sem nota" : ""}. Pode
              pular ou encerrar quando quiser.
            </p>
            {!comIA && (
              <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-xs">
                Sem IA, você treina as respostas e elas ficam salvas para reler; o retorno precisa de uma IA (botão IA).
              </p>
            )}
            <div className="flex gap-4" role="radiogroup" aria-label="Idioma">
              {(
                [
                  ["pt", "Português"],
                  ["en", "Inglês"],
                ] as const
              ).map(([k, r]) => (
                <label key={k} className="flex items-center gap-1.5 cursor-pointer text-sm">
                  <input type="radio" checked={idiomaSim === k} onChange={() => setIdiomaSim(k)} /> {r}
                </label>
              ))}
            </div>
            {custo}
            <button type="button" disabled={!qs.length} onClick={() => setSim({ i: 0, idioma: idiomaSim, rascunho: "" })} className={BTN_PRI}>
              Começar
            </button>
            {feitas > 0 && <p className={DICA}>{feitas} {feitas === 1 ? "resposta treinada" : "respostas treinadas"} nesta vaga.</p>}
            {treinar.length > 0 && (
              <div className="text-xs">
                <b>O que treinar</b>
                <Lista itens={treinar} />
              </div>
            )}
          </section>
        )
      } else {
        const q = qs[s.i] || ({} as (typeof qs)[number])
        const texto = s.idioma === "en" ? q.texto_en || q.texto : q.texto
        const avancar = () => (s.i + 1 >= qs.length ? (setSim({ ...s, fim: true }), carregar(atual)) : setSim({ i: s.i + 1, idioma: s.idioma, rascunho: "" }))
        corpo = (
          <section className={SEC}>
            <h4 className={H}>
              Pergunta {s.i + 1} de {qs.length}
            </h4>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">{texto}</p>
            {s.retorno !== undefined ? (
              <>
                <div className={`${BLOCO} text-xs`}>
                  <b>Sua resposta</b>
                  <p className="whitespace-pre-wrap">{s.resposta}</p>
                </div>
                {s.retorno ? (
                  <>
                    <div className={`${BLOCO} text-xs`}>
                      <b>O que funcionou</b>
                      <p>{s.retorno.funcionou || "—"}</p>
                    </div>
                    <div className={`${BLOCO} text-xs`}>
                      <b>O que faltou</b>
                      <p>{s.retorno.faltou || "—"}</p>
                    </div>
                    <div className={`${BLOCO} text-xs`}>
                      <b>Uma resposta mais forte (só com fatos seus)</b>
                      <p>{s.retorno.mais_forte || "—"}</p>
                      {(s.retorno.conferir || []).length > 0 && (
                        <p className="text-[11px] text-amber-700 dark:text-amber-300">Confira: {(s.retorno.conferir || []).join("; ")}</p>
                      )}
                    </div>
                  </>
                ) : (
                  <p className={DICA}>Resposta salva.</p>
                )}
                <div className="flex gap-2 flex-wrap">
                  <button type="button" onClick={avancar} className={BTN_PRI}>Próxima</button>
                  <button type="button" onClick={() => setSim({ i: s.i, idioma: s.idioma, rascunho: s.resposta || "" })} className={BTN_SEC}>
                    Responder de novo
                  </button>
                  <button type="button" onClick={() => { setSim({ ...s, fim: true }); carregar(atual) }} className={BTN_SEC}>
                    Encerrar
                  </button>
                </div>
              </>
            ) : (
              <>
                <textarea
                  rows={6}
                  maxLength={4000}
                  aria-label="Sua resposta"
                  value={s.rascunho}
                  onChange={(ev) => setSim({ ...s, rascunho: ev.target.value })}
                  className={CAMPO}
                />
                <div className="flex gap-2 flex-wrap">
                  <button
                    type="button"
                    disabled={bloq}
                    onClick={() => {
                      const resp = s.rascunho.trim()
                      if (!resp) return setErro("Escreva a resposta antes de enviar (ou pule a pergunta).")
                      pedir(
                        "responder",
                        () => entrevistaApi.simular(atual, { pergunta: texto, resposta: resp, idioma: s.idioma }),
                        (j) => {
                          setSim({ ...s, resposta: resp, retorno: j.retorno || null })
                          setD((x) => (x ? { ...x, simulacao: j.simulacao } : x))
                        },
                      )
                    }}
                    className={BTN_PRI}
                  >
                    {ocupado === "responder" ? "Lendo a resposta…" : "Enviar resposta"}
                  </button>
                  <button type="button" onClick={avancar} className={BTN_SEC}>Pular</button>
                  <button type="button" onClick={() => { setSim({ ...s, fim: true }); carregar(atual) }} className={BTN_SEC}>
                    Encerrar
                  </button>
                </div>
              </>
            )}
          </section>
        )
      }
    } else if (aba === "salario") {
      const s = d.salario || {}
      corpo = (
        <section className={SEC}>
          <h4 className={H}>Salário</h4>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-xs">
            <dt className="font-semibold text-slate-500">Faixa da vaga</dt>
            <dd>{s.faixa ? `${s.faixa}${s.moeda ? ` (${s.moeda})` : ""}` : "a vaga não informa"}</dd>
            <dt className="font-semibold text-slate-500">Sua pretensão</dt>
            <dd>{s.pretensao || "não está no seu perfil (acrescente em Meu perfil, se quiser)"}</dd>
          </dl>
          {(s.pontos || []).length > 0 && (
            <div className="text-xs">
              <b>Para a conversa</b>
              <Lista itens={s.pontos} />
            </div>
          )}
          <p className={DICA}>A ferramenta não estima valor de mercado: só mostra o que a vaga e o seu perfil dizem.</p>
        </section>
      )
    } else if (aba === "depois") {
      const campo = (k: keyof typeof rodada, rotulo: string, tipo: "input" | "textarea" | "date" = "textarea", max = 2000) => (
        <label className="block text-xs font-semibold">
          {rotulo}
          {tipo === "textarea" ? (
            <textarea rows={2} maxLength={max} value={rodada[k]} onChange={(ev) => setRodada({ ...rodada, [k]: ev.target.value })} className={CAMPO} />
          ) : (
            <input type={tipo === "date" ? "date" : "text"} maxLength={max} value={rodada[k]} onChange={(ev) => setRodada({ ...rodada, [k]: ev.target.value })} className={CAMPO} />
          )}
        </label>
      )
      corpo = (
        <>
          <section className={SEC}>
            <h4 className={H}>Como foi a entrevista</h4>
            <p className={DICA}>O que você anotar aqui entra na próxima preparação: as perguntas que caíram viram perguntas prováveis.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {campo("data", "Data", "date")}
              {campo("etapa", "Etapa (ex.: RH, técnica, gestor)", "input", 80)}
            </div>
            {campo("perguntas", "Perguntas que caíram (uma por linha)", "textarea", 4000)}
            {campo("bem", "O que foi bem")}
            {campo("mal", "O que foi mal")}
            {campo("proximos", "Próximos passos", "textarea", 1000)}
            <button
              type="button"
              disabled={bloq}
              onClick={() =>
                pedir("rodada", () => entrevistaApi.salvarRodada(atual, rodada), async () => {
                  onAviso("Anotação salva: as perguntas entram na próxima preparação.")
                  setRodada({ data: hoje(), etapa: "", perguntas: "", bem: "", mal: "", proximos: "" })
                  await carregar(atual)
                })
              }
              className={BTN_PRI}
            >
              Salvar anotação
            </button>
          </section>
          {d.rodadas.length > 0 && (
            <section className={SEC}>
              <h4 className={H}>Entrevistas anteriores</h4>
              {[...d.rodadas].reverse().map((r, i) => (
                <div key={i} className={`${BLOCO} text-xs`}>
                  <b>
                    {diaMes(r.data)}
                    {r.etapa ? ` · ${r.etapa}` : ""}
                  </b>
                  <Lista itens={r.perguntas} />
                  {r.bem && <p><b>Bem:</b> {r.bem}</p>}
                  {r.mal && <p><b>Mal:</b> {r.mal}</p>}
                  {r.proximos && <p><b>Próximos:</b> {r.proximos}</p>}
                </div>
              ))}
            </section>
          )}
        </>
      )
    }
  }

  const vagaAtual = vagas.find((v) => v.id === atual)
  return (
    <div className="space-y-4">
      <div className={`${SEC} flex flex-col sm:flex-row sm:items-center gap-3`}>
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-violet-500" />
          <h3 className="font-bold text-base text-slate-900 dark:text-white">Preparar entrevista</h3>
        </div>
        <select
          aria-label="Vaga"
          value={atual || ""}
          onChange={(ev) => onEscolherVaga(ev.target.value)}
          className={`${CAMPO} sm:max-w-md`}
        >
          {ordenadas.map((v) => (
            <option key={v.id} value={v.id}>
              {v.titulo} — {v.empresa}
              {v.etapa === "entrevista" ? " (em Entrevista)" : ""}
            </option>
          ))}
        </select>
        {vagaAtual?.entrevista_em && <span className={DICA}>entrevista em {diaMes(vagaAtual.entrevista_em)}</span>}
      </div>

      <nav className="flex gap-1.5 flex-wrap" aria-label="Partes da preparação">
        {ABAS.map(([k, r]) => (
          <button
            key={k}
            type="button"
            aria-pressed={aba === k}
            onClick={() => {
              setAba(k)
              setErro("")
            }}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
              aba === k ? "bg-indigo-600 text-white" : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800"
            }`}
          >
            {r}
          </button>
        ))}
      </nav>

      {!d && !erro && (
        <p className="flex items-center gap-2 text-slate-500 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Carregando a preparação…
        </p>
      )}
      <div className="space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300">{corpo}</div>
      {!podeGravar && d && <p className={DICA}>Só dá para gravar no computador onde a ferramenta roda.</p>}
      {erro && (
        <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {erro}
        </p>
      )}
    </div>
  )
}
