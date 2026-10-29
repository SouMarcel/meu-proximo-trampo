/**
 * Kit da candidatura (dash/API.md §3.9), como no dashboard antigo: para se candidatar, o que a candidatura pede
 * (checklist marcável), cartas, mensagens e respostas de formulário, e o lembrete de follow-up. Nada é enviado em
 * nome da pessoa: "Candidatar no…" só abre a página, "Enviar por e-mail" só abre o programa de e-mail.
 */
import React, { useEffect, useState } from "react"
import { X, Loader2, AlertTriangle, Copy, Bell } from "lucide-react"
import type { CamposEditaveis, ItemChecklist, Kit, Vaga } from "../../types/api"
import * as kitApi from "../../services/api/kit"
import type { Documento, DocumentoCarta, DocumentoRespostas, RespostasCarta } from "../../services/api/kit"
import { mensagemDeErro, getApiBaseUrl } from "../../services/api"
import { useFerramenta, textoCustoIA } from "../../contexto/Ferramenta"
import { useGeracao, ehDoAlvo } from "../../contexto/Geracao"
import { areaDe, diaMes, horaDe, linkSeguro, mailtoDe, plataformaDoLink, semAcento } from "../../utils/formatters"
import { AUTORIZACAO, CONTRATACAO, INGLES, RISCOS } from "../../utils/rotulos"
import { BTN_MINI, LinkArquivo } from "../curriculo/Curriculos"
import TextoDaVaga from "../TextoDaVaga"
import CandidaturaAssistida from "./CandidaturaAssistida"
import FaixaSalarial from "./FaixaSalarial"
import AcompanharEmpresa from "./AcompanharEmpresa"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ESTADOS: Record<string, string> = { a_fazer: "A fazer", pronto: "Pronto", nao_se_aplica: "Não se aplica" }
const ROTULOS: Record<string, string> = {
  curriculo: "Currículo",
  carta: "Carta de apresentação",
  formulario: "Respostas de formulário",
  portfolio: "Portfólio",
  teste: "Teste técnico",
  video: "Vídeo de apresentação",
  candidatura: "Enviar a candidatura",
}
const ACOES: Record<string, string> = { curriculo: "Gerar currículo", carta: "Escrever carta", respostas: "Preparar respostas" }
const TONS: Record<string, string> = { direto: "Direto e objetivo", caloroso: "Caloroso e próximo", formal: "Formal" }
const ATS: Record<string, string> = { greenhouse: "Greenhouse", lever: "Lever", ashby: "Ashby" }
const PERGUNTAS: [keyof Pick<RespostasCarta, "por_que" | "problema" | "primeiro_movimento">, string, string][] = [
  ["por_que", "Por que esta vaga?", "O que nesta vaga e nesta empresa chama a sua atenção."],
  ["problema", "Que problema da empresa você resolveria?", "Pelo anúncio, o que eles precisam resolver e como você ajudaria."],
  ["primeiro_movimento", "Qual seria o seu primeiro movimento no cargo?", "O que você faria nas primeiras semanas."],
]
const VEREDITO: Record<string, string> = { ok: "Conferido: ok", conferir: "Conferir", bloquear: "Não pronto" }

function sistemaDe(v: Vaga): string {
  if (!v.ats && !v.url_candidatura && mailtoDe(v)) return "e-mail"
  if (v.ats) return ATS[v.ats] || v.ats
  return v.sistema_candidatura || (v.url_candidatura ? plataformaDoLink(v.url_candidatura) : v.plataforma) || "site da vaga"
}

const idExtra = (t: string) => "x:" + semAcento(t).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40)

function copiar(texto: string, aviso: (m: string, t?: "info" | "erro") => void) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard
      .writeText(texto)
      .then(() => aviso("Copiado. Cole onde precisar; nada foi enviado."))
      .catch(() => aviso("Não deu para copiar.", "erro"))
    return
  }
  aviso("Não deu para copiar.", "erro")
}

function Frase({ f }: { f?: string }) {
  return f ? <span className="block text-[11px] italic text-slate-500 dark:text-slate-400">“{f}”</span> : null
}

// ---------- lembrete de follow-up ----------

export function Lembrete({
  vaga,
  onUpdateVaga,
  compacto = false,
}: {
  vaga: Vaga
  onUpdateVaga: (id: string, campos: CamposEditaveis, sucesso?: string) => Promise<boolean>
  compacto?: boolean
}) {
  const { podeGravar } = useFerramenta()
  const l = (vaga.lembretes_pendentes || [])[0]
  if (!l) return null
  const marcar = (acao: "feito" | "dispensado" | "parar") => {
    const atual = vaga.lembretes && vaga.lembretes.base === l.base ? { ...vaga.lembretes } : { base: l.base }
    if (acao === "parar") atual.parar = true
    else atual[l.tipo] = acao
    onUpdateVaga(vaga.id, { lembretes: atual }, acao === "parar" ? "Lembretes desta vaga encerrados." : "Lembrete marcado.")
  }
  return (
    <div
      className="flex items-center gap-2 flex-wrap p-2.5 rounded-xl bg-violet-50 dark:bg-violet-950/40 border border-violet-200 dark:border-violet-900 text-xs text-violet-900 dark:text-violet-200"
      title="A ferramenta só lembra: a mensagem é você quem escreve e envia"
      onClick={(ev) => ev.stopPropagation()}
    >
      <Bell className="w-3.5 h-3.5 shrink-0" />
      <b>{l.rotulo}</b>
      <span className={DICA}>desde {diaMes(l.desde)}</span>
      <span className="flex gap-1 flex-wrap ml-auto">
        <button type="button" disabled={!podeGravar} onClick={() => marcar("feito")} className={BTN_MINI}>Feito</button>
        <button type="button" disabled={!podeGravar} onClick={() => marcar("dispensado")} className={BTN_MINI}>Dispensar</button>
        {!compacto && (
          <button type="button" disabled={!podeGravar} onClick={() => marcar("parar")} className={BTN_MINI}>Parar lembretes</button>
        )}
      </span>
    </div>
  )
}

// ---------- o kit na aba do detalhe ----------

export function KitDaVaga({
  vaga,
  onUpdateVaga,
  onGerarCurriculo,
  onAviso,
}: {
  vaga: Vaga
  onUpdateVaga: (id: string, campos: CamposEditaveis, sucesso?: string) => Promise<boolean>
  onGerarCurriculo: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
}) {
  const { podeGravar, servidor } = useFerramenta()
  const { estado, ativa, versao, tentar } = useGeracao()
  const [kit, setKit] = useState<Kit>(() => ({ estados: {}, extras: [], removidos: [], ...(vaga.kit || {}) }))
  const [novo, setNovo] = useState("")
  const [docs, setDocs] = useState<Documento[] | null>(null)
  const [dialogo, setDialogo] = useState<{ modo: "carta" | "respostas" | "ver"; doc?: DocumentoRespostas } | null>(null)

  // o servidor devolve a vaga com o kit gravado: a próxima mudança parte dele
  useEffect(() => {
    setKit({ estados: {}, extras: [], removidos: [], ...(vaga.kit || {}) })
  }, [vaga.kit])

  useEffect(() => {
    kitApi
      .lista(vaga.id)
      .then((j) => setDocs(j.documentos || []))
      .catch(() => setDocs((d) => d || []))
  }, [vaga.id, versao])

  const salvarKit = (k: Kit, msg?: string) => {
    setKit(k)
    onUpdateVaga(vaga.id, { kit: k }, msg)
  }
  const copia = (): Required<Kit> => ({
    estados: { ...(kit.estados || {}) },
    extras: [...(kit.extras || [])],
    removidos: [...(kit.removidos || [])],
  })

  const fora = areaDe(vaga) === "internacional"
  const feita = vaga.analise_status === "feita"
  const nada = <span className={DICA}>{feita ? "não informado" : "vem com a análise"}</span>
  const mailto = mailtoDe(vaga)
  const linhas: [string, React.ReactNode, boolean][] = [
    ["Autorização", vaga.autorizacao ? <>{AUTORIZACAO[vaga.autorizacao.valor] || vaga.autorizacao.valor}<Frase f={vaga.autorizacao.frase} /></> : nada, fora || Boolean(vaga.autorizacao)],
    [
      "Contratação",
      (vaga.contratacao || []).length ? (vaga.contratacao || []).map((c, i) => <span key={i} className="block">{CONTRATACAO[c.valor] || c.valor}<Frase f={c.frase} /></span>) : nada,
      fora || Boolean((vaga.contratacao || []).length),
    ],
    ["Inglês", vaga.ingles ? <>{INGLES[vaga.ingles.nivel] || vaga.ingles.nivel}<Frase f={vaga.ingles.frase} /></> : nada, fora || Boolean(vaga.ingles)],
    ["Fuso", vaga.fuso ? <>{vaga.fuso.texto}<Frase f={vaga.fuso.frase} /></> : nada, fora || Boolean(vaga.fuso)],
    ["Candidatura pelo", sistemaDe(vaga), true],
    [
      "Candidatura por e-mail",
      <>{vaga.email_candidatura}{vaga.assunto_candidatura && <span className={`block ${DICA}`}>Assunto: {vaga.assunto_candidatura}</span>}</>,
      Boolean(mailto),
    ],
    [
      "Atenção",
      (vaga.riscos || []).map((r, i) => <span key={i} className="block text-rose-700 dark:text-rose-300">{RISCOS[r.tipo] || r.tipo}<Frase f={r.frase} /></span>),
      Boolean((vaga.riscos || []).length),
    ],
  ]

  const acaoDoItem = (i: ItemChecklist) => {
    let acao: React.ReactNode = null
    if (i.acao === "candidatar" && !vaga.ats && !vaga.url_candidatura && mailto) {
      acao = <a href={mailto} className={BTN_MINI} title="Só abre o seu programa de e-mail; nada é enviado">Enviar por e-mail</a>
    } else if (i.acao === "candidatar") {
      const u = linkSeguro(vaga.url_candidatura) || linkSeguro(vaga.url)
      acao = u ? (
        <span className="inline-flex flex-wrap items-center gap-2">
          <a href={u} target="_blank" rel="noopener noreferrer" className={BTN_MINI} title="Só abre a página; nada é preenchido nem enviado">
            Candidatar no {sistemaDe(vaga)}
          </a>
          <AcompanharEmpresa vaga={vaga} onAviso={onAviso} />
        </span>
      ) : (
        <span className={DICA}>sem link</span>
      )
    } else if (i.acao) {
      acao = (
        <button
          type="button"
          disabled={servidor !== "no_ar"}
          onClick={() => (i.acao === "curriculo" ? onGerarCurriculo() : setDialogo({ modo: i.acao as "carta" | "respostas" }))}
          className={BTN_MINI}
        >
          {ACOES[i.acao]}
        </button>
      )
    }
    return (
      <>
        {i.base && (
          <a href={getApiBaseUrl() + i.base.url} target="_blank" rel="noopener noreferrer" className={BTN_MINI} title={`Seu currículo: ${i.base.nome}`}>
            Abrir o seu
          </a>
        )}
        {acao}
      </>
    )
  }

  const removidos = kit.removidos || []
  const tem = (vaga.checklist || []).map((i) => i.acao)
  const mais = (["carta", "respostas"] as const).filter((a) => !tem.includes(a))
  const meu = ehDoAlvo(estado, vaga.id, ["carta", "respostas"])

  return (
    <div className="space-y-4">
      <section className="space-y-2">
        <h4 className={H}>Para se candidatar</h4>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-xs">
          {linhas.filter(([, , mostrar]) => mostrar).map(([rot, valor]) => (
            <React.Fragment key={rot}>
              <dt className="font-semibold text-slate-500">{rot}</dt>
              <dd className="text-slate-800 dark:text-slate-200">{valor}</dd>
            </React.Fragment>
          ))}
        </dl>
        {!feita && (
          <p className={DICA}>
            Sem a análise da IA, aparecem o sistema de candidatura, a restrição de local e os sinais do anúncio; o resto vem
            com a análise.
          </p>
        )}
      </section>

      <CandidaturaAssistida vaga={vaga} onAviso={onAviso} />

      <FaixaSalarial vagaId={vaga.id} />

      <section className="space-y-2">
        <h4 className={H}>O que esta candidatura pede</h4>
        <ul className="space-y-2">
          {(vaga.checklist || []).map((i) => {
            const origem = ({ analise: "A análise leu: ", anuncio: "No anúncio: " } as Record<string, string>)[i.origem]
            return (
              <li key={i.item} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <select
                    aria-label={`Situação: ${i.rotulo}`}
                    value={i.estado}
                    disabled={!podeGravar}
                    onChange={(ev) => {
                      const k = copia()
                      k.estados[i.item] = ev.target.value as "a_fazer" | "pronto" | "nao_se_aplica"
                      salvarKit(k)
                    }}
                    className="px-2 py-1 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  >
                    {Object.entries(ESTADOS).map(([k, r]) => (
                      <option key={k} value={k}>{r}</option>
                    ))}
                  </select>
                  <b className={i.estado === "pronto" ? "line-through text-slate-400" : "text-slate-800 dark:text-slate-200"}>{i.rotulo}</b>
                  <span className="flex gap-1.5 flex-wrap ml-auto items-center">
                    {acaoDoItem(i)}
                    <button
                      type="button"
                      disabled={!podeGravar}
                      title="Tirar do checklist"
                      aria-label={`Tirar ${i.rotulo} do checklist`}
                      onClick={() => {
                        const k = copia()
                        if (i.extra) k.extras = k.extras.filter((x) => x !== i.extra && idExtra(x) !== i.item)
                        else if (i.item.startsWith("x:")) k.extras = k.extras.filter((x) => idExtra(x) !== i.item)
                        else if (!k.removidos.includes(i.item)) k.removidos.push(i.item)
                        salvarKit(k)
                      }}
                      className="p-1 rounded-md text-slate-400 hover:text-rose-600 disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                </div>
                {i.frase && origem && <p className={DICA}>{origem}“{i.frase}”</p>}
                {i.base && <p className={DICA}>Seu currículo: {i.base.nome}. Gere outro só se quiser uma versão adaptada.</p>}
                {i.falta_base && (
                  <p className={DICA}>
                    Você não marcou um currículo em {i.falta_base === "en" ? "inglês" : "português"} (Meu perfil → Concluído → Seu currículo).
                  </p>
                )}
              </li>
            )
          })}
        </ul>
        {removidos.length > 0 && (
          <p className={DICA}>
            Tirados do checklist:{" "}
            {removidos.map((r, n) => (
              <React.Fragment key={r}>
                {n > 0 && ", "}
                <button
                  type="button"
                  disabled={!podeGravar}
                  onClick={() => {
                    const k = copia()
                    k.removidos = k.removidos.filter((x) => x !== r)
                    salvarKit(k)
                  }}
                  className="underline"
                >
                  {ROTULOS[r] || r} (voltar)
                </button>
              </React.Fragment>
            ))}
          </p>
        )}
        {mais.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className={DICA}>Mesmo que o anúncio não peça (ex.: vaga preferencial no LinkedIn):</span>
            {mais.map((a) => (
              <button key={a} type="button" disabled={servidor !== "no_ar"} onClick={() => setDialogo({ modo: a })} className={BTN_MINI}>
                {ACOES[a]}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            value={novo}
            maxLength={80}
            disabled={!podeGravar}
            onChange={(ev) => setNovo(ev.target.value)}
            onKeyDown={(ev) => {
              if (ev.key === "Enter" && novo.trim()) {
                ev.preventDefault()
                const k = copia()
                k.extras.push(novo.trim())
                setNovo("")
                salvarKit(k, "Item acrescentado.")
              }
            }}
            placeholder="Outro item (ex.: carta de apresentação, referências)"
            aria-label="Novo item do checklist"
            className={`${CAMPO} flex-1`}
          />
          <button
            type="button"
            disabled={!podeGravar || !novo.trim() || (kit.extras || []).length >= 10}
            onClick={() => {
              const k = copia()
              k.extras.push(novo.trim())
              setNovo("")
              salvarKit(k, "Item acrescentado.")
            }}
            className={BTN_MINI}
            title={(kit.extras || []).length >= 10 ? "Até 10 itens acrescentados" : undefined}
          >
            Acrescentar
          </button>
        </div>
      </section>

      {meu && ativa && (
        <p className="flex items-center gap-2 text-xs text-indigo-700 dark:text-indigo-300">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          {estado?.etapa_texto || "Escrevendo…"} Pode levar alguns minutos; dá para fechar e voltar.
        </p>
      )}
      {meu && estado?.situacao === "falha" && (
        <p className="text-xs text-rose-700 dark:text-rose-300">
          {estado.tipo === "carta" ? "A carta" : "As respostas"} não saiu: {estado.mensagem}{" "}
          {estado.pode_tentar && (
            <button type="button" onClick={tentar} className={BTN_MINI}>
              Tentar de novo
            </button>
          )}
        </p>
      )}

      {docs === null ? (
        <p className={DICA}>Carregando cartas e respostas…</p>
      ) : (
        docs.length > 0 && (
          <section className="space-y-2">
            <h4 className={H}>Cartas e respostas</h4>
            <ul className="space-y-2">
              {docs.map((m) =>
                m.tipo === "respostas" ? (
                  <ItemRespostas key={m.nome} m={m} onAbrir={() => setDialogo({ modo: "ver", doc: m })} />
                ) : (
                  <ItemCarta
                    key={m.nome}
                    m={m}
                    vagaId={vaga.id}
                    onAviso={onAviso}
                    onCopiar={() => copiar(m.texto || "", onAviso)}
                    onMudou={() => kitApi.lista(vaga.id).then((j) => setDocs(j.documentos || [])).catch(() => undefined)}
                  />
                ),
              )}
            </ul>
          </section>
        )
      )}

      {dialogo && (
        <DialogoKit
          modo={dialogo.modo}
          vaga={vaga}
          doc={dialogo.doc}
          onClose={() => setDialogo(null)}
          onAviso={onAviso}
          onSalvo={() => kitApi.lista(vaga.id).then((j) => setDocs(j.documentos || [])).catch(() => undefined)}
        />
      )}
    </div>
  )
}

function ItemCarta({
  m,
  vagaId,
  onCopiar,
  onAviso,
  onMudou,
}: {
  m: DocumentoCarta
  vagaId: string
  onCopiar: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
  onMudou: () => void
}) {
  const { podeGravar, ia, tratarErro } = useFerramenta()
  const { comecou } = useGeracao()
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState(m.texto || "")
  const [guardar, setGuardar] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [gerandoPdf, setGerandoPdf] = useState(false)
  const [erro, setErro] = useState("")
  const c = m.conferencia || {}
  const pontos = c.pontos || []
  const pc = c.palavras_chave
  const msg = m.formato === "mensagem"
  const d = m.disponivel || {}
  const gerarPdf = async () => {
    setErro("")
    setGerandoPdf(true)
    try {
      await kitApi.pdfDaCarta(m.nome)
      onAviso("PDF da carta pronto.")
      onMudou()
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e))
    } finally {
      setGerandoPdf(false)
    }
  }
  const verificar = async () => {
    setErro("")
    setEnviando(true)
    try {
      comecou(await kitApi.verificar(vagaId, m.nome, texto, guardar))
      setEditando(false)
      onAviso("Verificando: a versão revisada aparece nesta lista quando ficar pronta; esta continua aqui.")
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e))
    } finally {
      setEnviando(false)
    }
  }
  return (
    <li className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
      <div className="flex items-center gap-2 flex-wrap">
        <b>{diaMes(m.criado_em)} {horaDe(m.criado_em)}</b>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800">
          {msg ? "Mensagem" : "Carta"} · {VEREDITO[c.veredito || ""] || c.veredito || ""}
        </span>
        <span className={DICA}>
          {msg ? `${m.caracteres || 0} de ${m.limite} caracteres · ${(m.idioma || "").toUpperCase()}` : `${m.palavras || 0} palavras`} · tom{" "}
          {(TONS[String(m.respostas?.tom || "")] || "").toLowerCase()}
          {pc && pc.total > 0 && ` · palavras-chave da vaga: ${pc.citadas} de ${pc.total}`}
        </span>
        {m.origem === "verificada" && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300">
            Revisada da sua edição
          </span>
        )}
        <span className="flex gap-1.5 ml-auto items-center">
          <span className={DICA}>Exportar:</span>
          {d.pdf && <LinkArquivo arquivo={m.arquivos.pdf} rotulo=".pdf" />}
          {!msg && !d.pdf && podeGravar && (
            <button
              type="button"
              className={BTN_MINI}
              disabled={gerandoPdf}
              title="Monta o PDF a partir do .docx, pelo LibreOffice ou pelo Word"
              onClick={gerarPdf}
            >
              {gerandoPdf ? "Gerando PDF…" : "Gerar PDF"}
            </button>
          )}
          {d.docx && <LinkArquivo arquivo={m.arquivos.docx} rotulo=".docx" />}
          {d.txt && <LinkArquivo arquivo={m.arquivos.txt} rotulo=".txt" />}
          <button type="button" onClick={onCopiar} className={BTN_MINI}>
            <Copy className="w-3 h-3" /> Copiar
          </button>
        </span>
      </div>
      {c.veredito === "bloquear" && (
        <p className="text-rose-700 dark:text-rose-300">
          Não use {msg ? "esta mensagem" : "esta carta"} ainda:{" "}
          {pontos.filter((p) => p.nivel === "bloquear").map((p) => p.mensagem + (p.valor ? ` (${p.valor})` : "")).join("; ")}. Ajuste o
          texto ou peça de novo.
        </p>
      )}
      {pontos.length > 0 && (
        <details>
          <summary className="cursor-pointer font-semibold">Ver conferência</summary>
          <ul className="list-disc pl-5 mt-1">
            {pontos.map((p, i) => (
              <li key={i}>
                <b>{p.nivel}</b> {p.mensagem}
                {p.valor ? `: ${p.valor}` : ""}
              </li>
            ))}
          </ul>
        </details>
      )}
      {!msg && !d.pdf && m.aviso_pdf && <p className={DICA}>O PDF não saiu: {m.aviso_pdf}</p>}
      {erro && !editando && <p role="alert" className="text-rose-600 dark:text-rose-400">{erro}</p>}
      {(m.mudancas || []).length > 0 && (
        <details>
          <summary className="cursor-pointer font-semibold">O que a IA ajustou na sua edição</summary>
          <ul className="list-disc pl-5 mt-1">
            {(m.mudancas || []).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </details>
      )}
      {pc && pc.faltando.length > 0 && (
        <p className={DICA}>Requisitos que o seu perfil sustenta e a carta não usa: {pc.faltando.slice(0, 5).join("; ")}</p>
      )}
      {editando ? (
        <div className="space-y-1.5">
          <p className={DICA}>
            Edite à vontade: o que você mudar ou acrescentar vale como fato seu. <b>Verificar</b> pede à IA para incorporar as
            suas mudanças, corrigir gramática e ortografia e manter a estrutura, as palavras-chave e o tamanho. Sai uma versão
            nova, e esta continua aqui.
          </p>
          <textarea rows={14} className={CAMPO} value={texto} maxLength={12000} onChange={(ev) => setTexto(ev.target.value)} />
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={guardar} onChange={(ev) => setGuardar(ev.target.checked)} />
            <span className={DICA}>Guardar o que eu acrescentar como relato (Meu perfil → Seus relatos)</span>
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
              disabled={enviando || !texto.trim() || !ia?.disponivel}
              title={ia?.disponivel ? textoCustoIA(ia) : "Verificar precisa de uma IA: escolha uma no botão IA"}
              onClick={verificar}
            >
              {enviando ? "Enviando…" : "Verificar"}
            </button>
            <button type="button" className={BTN_MINI} disabled={enviando} onClick={() => (setEditando(false), setTexto(m.texto || ""))}>
              Cancelar
            </button>
          </div>
          {erro && <p role="alert" className="text-rose-600 dark:text-rose-400">{erro}</p>}
        </div>
      ) : (
        <details>
          <summary className="cursor-pointer font-semibold">Ler {msg ? "a mensagem" : "a carta"}</summary>
          <div className="mt-1 p-2 rounded-lg bg-slate-50 dark:bg-slate-800 space-y-2">
            <TextoDaVaga texto={m.texto} />
            {podeGravar && (
              <button type="button" className={BTN_MINI} onClick={() => (setTexto(m.texto || ""), setEditando(true))}>
                Editar e verificar
              </button>
            )}
          </div>
        </details>
      )}
    </li>
  )
}

function ItemRespostas({ m, onAbrir }: { m: DocumentoRespostas; onAbrir: () => void }) {
  const minhas = (m.itens || []).filter((i) => i.sensivel && !i.da_pessoa).length
  return (
    <li className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-xs flex items-center gap-2 flex-wrap">
      <b>{diaMes(m.criado_em)} {horaDe(m.criado_em)}</b>
      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800">Respostas</span>
      <span className={DICA}>
        {(m.itens || []).length} perguntas{minhas ? ` · ${minhas} para você responder` : ""}
      </span>
      <span className="flex gap-1.5 ml-auto">
        {m.disponivel?.txt && <LinkArquivo arquivo={m.arquivos.txt} rotulo=".txt" />}
        <button type="button" onClick={onAbrir} className={BTN_MINI}>Abrir</button>
      </span>
    </li>
  )
}

// ---------- diálogo: escrever carta, preparar respostas, ver respostas ----------

function DialogoKit({
  modo,
  vaga,
  doc,
  onClose,
  onAviso,
  onSalvo,
}: {
  modo: "carta" | "respostas" | "ver"
  vaga: Vaga
  doc?: DocumentoRespostas
  onClose: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
  onSalvo: () => void
}) {
  const { ia, abrirPainelIA, tratarErro, podeGravar } = useFerramenta()
  const { comecou } = useGeracao()
  const semIA = !ia?.disponivel
  const idiomaVaga = vaga.idioma === "pt" ? "pt" : "en"
  const [formato, setFormato] = useState<"carta" | "mensagem">("carta")
  const [tom, setTom] = useState<RespostasCarta["tom"]>("direto")
  const [limite, setLimite] = useState(400)
  const [idioma, setIdioma] = useState(idiomaVaga)
  const [resp, setResp] = useState({ por_que: "", problema: "", primeiro_movimento: "" })
  const [guardarRelatos, setGuardarRelatos] = useState(true)
  const [perguntas, setPerguntas] = useState("")
  const [pessoa, setPessoa] = useState<Record<string, string>>(() => {
    const p: Record<string, string> = {}
    ;(doc?.itens || []).forEach((i, n) => {
      if (i.sensivel || i.da_pessoa) p[String(n + 1)] = i.resposta || ""
    })
    return p
  })
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  const enviar = async () => {
    setErro("")
    try {
      if (modo === "carta") {
        // as perguntas são opcionais (spec 035): a que ficar em branco a IA responde pelo perfil e pelos relatos
        setEnviando(true)
        const r: RespostasCarta = {
          formato,
          tom,
          por_que: resp.por_que.trim(),
          problema: formato === "carta" ? resp.problema.trim() : "",
          primeiro_movimento: formato === "carta" ? resp.primeiro_movimento.trim() : "",
          guardar_relatos: guardarRelatos,
          ...(formato === "mensagem" ? { limite: Math.min(3000, Math.max(20, limite || 400)), idioma } : {}),
        }
        comecou(await kitApi.carta(vaga.id, r))
      } else if (modo === "respostas") {
        setEnviando(true)
        comecou(await kitApi.respostas(vaga.id, perguntas))
      } else if (doc) {
        setEnviando(true)
        await kitApi.salvarRespostas(doc.nome, pessoa)
        onAviso("Respostas salvas como você escreveu.")
        onSalvo()
      }
      onClose()
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e))
      setEnviando(false)
    }
  }

  const titulo = modo === "carta" ? "Escrever carta ou mensagem" : modo === "respostas" ? "Preparar respostas do formulário" : "Respostas do formulário"
  const desc =
    modo === "carta"
      ? "A IA escreve para vender você logo no primeiro parágrafo, com foco no problema da empresa que você ajuda a resolver, só com os fatos do seu perfil, dos seus relatos e das suas respostas, em formato que o ATS lê. A ferramenta confere antes de você usar."
      : modo === "respostas"
        ? "Cole as perguntas do formulário de candidatura, uma por linha. As perguntas sobre autorização de trabalho, visto, salário, deficiência, relocação e diversidade ficam para você responder: elas não vão para a IA."
        : "Rascunhos com os fatos do seu perfil. As marcadas são só suas: escreva você. Nada é enviado; copie e cole no formulário."

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-kit"
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div>
            <h3 id="titulo-kit" className="font-bold text-base text-slate-900 dark:text-white">{titulo}</h3>
            <p className="text-xs text-slate-500">{desc}</p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          {modo !== "ver" && semIA && (
            <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs">
              Escrever pela página precisa de uma IA: escolha uma no botão IA, ou peça no chat do seu assistente (skill gerar-curriculo).
            </p>
          )}
          {modo !== "ver" && !semIA && <p className={DICA}>{textoCustoIA(ia)}</p>}

          {modo === "carta" && (
            <>
              <div className="space-y-1.5">
                <b>Formato</b>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" checked={formato === "carta"} onChange={() => setFormato("carta")} /> Carta completa (350 a 420 palavras, .pdf e .docx para anexar)
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" checked={formato === "mensagem"} onChange={() => setFormato("mensagem")} /> Mensagem curta (ex.: vaga preferencial no LinkedIn)
                </label>
              </div>
              {formato === "mensagem" && (
                <div className="flex items-center gap-4 flex-wrap">
                  <label className="flex items-center gap-2">
                    <b>Limite de caracteres</b>
                    <input type="number" min={20} max={3000} step={10} value={limite} onChange={(ev) => setLimite(Number(ev.target.value))} className={`${CAMPO} w-28`} />
                    <span className={DICA}>o LinkedIn aceita até 400</span>
                  </label>
                  <span className="flex items-center gap-3">
                    <b>Idioma</b>
                    {(
                      [
                        ["en", "Inglês"],
                        ["pt", "Português"],
                      ] as const
                    ).map(([k, r]) => (
                      <label key={k} className="flex items-center gap-1.5 cursor-pointer">
                        <input type="radio" checked={idioma === k} onChange={() => setIdioma(k)} /> {r}
                        {k === (vaga.idioma || "en") ? " (o da vaga)" : ""}
                      </label>
                    ))}
                  </span>
                </div>
              )}
              <p className={DICA}>
                As perguntas abaixo são opcionais. Deixe em branco e a ferramenta responde pelo seu perfil, pelos seus relatos e
                pela vaga. Se escrever, conte com as suas palavras: vale como relato, entra nesta carta e fica no que a
                ferramenta sabe de você.
              </p>
              {PERGUNTAS.filter(([k]) => formato === "carta" || k === "por_que").map(([k, rotulo, dica]) => (
                <div key={k} className="space-y-1">
                  <label htmlFor={`kc-${k}`} className="font-semibold block">
                    {rotulo} <span className={DICA}>(opcional)</span>
                  </label>
                  <textarea id={`kc-${k}`} rows={3} maxLength={800} placeholder={dica} value={resp[k]} onChange={(ev) => setResp((r) => ({ ...r, [k]: ev.target.value }))} className={CAMPO} />
                </div>
              ))}
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={guardarRelatos} onChange={(ev) => setGuardarRelatos(ev.target.checked)} />
                <span className={DICA}>Guardar o que eu escrever como relato (Meu perfil → Seus relatos)</span>
              </label>
              <div className="space-y-1.5">
                <b>Tom da carta</b>
                <div className="flex gap-3 flex-wrap">
                  {Object.entries(TONS).map(([k, r]) => (
                    <label key={k} className="flex items-center gap-1.5 cursor-pointer">
                      <input type="radio" checked={tom === k} onChange={() => setTom(k as RespostasCarta["tom"])} /> {r}
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}

          {modo === "respostas" && (
            <div className="space-y-1">
              <label htmlFor="kr-perguntas" className="font-semibold block">Perguntas</label>
              <textarea
                id="kr-perguntas"
                rows={8}
                value={perguntas}
                onChange={(ev) => setPerguntas(ev.target.value)}
                placeholder={"1. Why do you want to work here?\n2. Are you authorized to work in the US?"}
                className={CAMPO}
              />
              <p className={DICA}>Uma por linha, até 30.</p>
            </div>
          )}

          {modo === "ver" &&
            (doc?.itens || []).map((i, n) => {
              const chave = String(n + 1)
              const editando = chave in pessoa
              return (
                <div
                  key={n}
                  className={`p-3 rounded-xl border space-y-1 ${i.sensivel ? "border-orange-300 dark:border-orange-800 bg-orange-50/50 dark:bg-orange-950/20" : "border-slate-200 dark:border-slate-800"}`}
                >
                  <p className="font-semibold">
                    {n + 1}. {i.pergunta}
                  </p>
                  {editando ? (
                    <>
                      {i.sensivel && <p className={DICA}>Só você responde ({i.sensivel}).</p>}
                      <textarea
                        aria-label="Sua resposta"
                        rows={3}
                        value={pessoa[chave]}
                        onChange={(ev) => setPessoa((p) => ({ ...p, [chave]: ev.target.value }))}
                        className={CAMPO}
                      />
                    </>
                  ) : (
                    <>
                      <p>{i.resposta || "(sem resposta: o perfil não responde)"}</p>
                      {(i.conferir || []).length > 0 && <p className={DICA}>Conferir: {(i.conferir || []).join("; ")}</p>}
                      <button type="button" onClick={() => setPessoa((p) => ({ ...p, [chave]: i.resposta || "" }))} className="underline text-xs">
                        Escrever a minha
                      </button>
                    </>
                  )}
                </div>
              )
            })}

          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {erro}
            </p>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2 flex-wrap">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
            {modo === "ver" ? "Fechar" : "Cancelar"}
          </button>
          {modo === "ver" && (
            <button
              type="button"
              onClick={() =>
                copiar(
                  (doc?.itens || []).map((i, n) => `${n + 1}. ${i.pergunta}\n${pessoa[String(n + 1)] ?? i.resposta ?? ""}`).join("\n\n"),
                  onAviso,
                )
              }
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            >
              Copiar tudo
            </button>
          )}
          {modo !== "ver" && semIA ? (
            <button type="button" onClick={() => { onClose(); abrirPainelIA() }} className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500">
              Escolher a IA
            </button>
          ) : (
            <button
              type="button"
              disabled={enviando || !podeGravar}
              onClick={enviar}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
            >
              {enviando && <Loader2 className="w-4 h-4 animate-spin" />}
              {modo === "carta" ? "Escrever" : modo === "respostas" ? "Preparar respostas" : "Salvar as suas respostas"}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
