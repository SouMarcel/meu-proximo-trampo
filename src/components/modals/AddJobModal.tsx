/**
 * Adicionar vaga (dash/API.md §3.2). Primeiro pelo link; se não der para ler, o formulário pede o resto. Link de post
 * do LinkedIn ou texto colado: a IA escolhida só preenche o formulário, e nada é gravado até a pessoa conferir e
 * clicar em Adicionar.
 */
import React, { useRef, useState } from "react"
import { X, Plus, Link as LinkIcon, FileText, Edit, Loader2, AlertTriangle, Info } from "lucide-react"
import type { Area, Etapa, NovaVaga, ParcialVaga, Vaga, InfoIA } from "../../types/api"
import { PLATAFORMAS } from "../../types/api"
import * as vagasApi from "../../services/api/vagas"
import { ehErroApi, mensagemDeErro } from "../../services/api"
import { useFerramenta, motivoSemGravar } from "../../contexto/Ferramenta"
import { noQuadro, plataformaDoLink } from "../../utils/formatters"

interface AddJobModalProps {
  onClose: () => void
  onVagaAdicionada: (vaga: Vaga) => void
  onAviso: (mensagem: string, tipo?: "info" | "erro") => void
}

type Passo = "inicio" | "colar" | "formulario"

const ETAPAS_DESTINO: { valor: "relatorio" | Etapa; rotulo: string }[] = [
  { valor: "relatorio", rotulo: "Relatório (decidir depois)" },
  { valor: "salva", rotulo: "Quadro: Salva" },
  { valor: "aplicada", rotulo: "Quadro: Aplicação Enviada" },
  { valor: "entrevista", rotulo: "Quadro: Entrevista" },
  { valor: "proposta", rotulo: "Quadro: Proposta Recebida" },
  { valor: "encerrada", rotulo: "Quadro: Encerrada" },
]

const ROTULO_ETAPA: Record<Etapa, string> = {
  salva: "Salva",
  aplicada: "Aplicação Enviada",
  entrevista: "Entrevista",
  proposta: "Proposta Recebida",
  encerrada: "Encerrada",
}

function avisoAdicionada(v: Vaga, automatica?: boolean): string {
  if (v.triagem === "fora") return "Vaga adicionada em Fora dos critérios: " + (v.motivo_fora || []).join("; ")
  if (v.analise_status !== "pendente") return noQuadro(v) ? "Vaga adicionada ao quadro." : "Vaga adicionada ao relatório."
  return automatica
    ? "Vaga adicionada. A IA está analisando a aderência (cerca de 1 minuto)."
    : "Vaga adicionada. Para a nota, escolha uma IA no botão IA ou peça a análise no chat."
}

function jaEstava(v: Vaga): string {
  const onde = noQuadro(v)
    ? `no quadro (${v.etapa ? ROTULO_ETAPA[v.etapa] : ""})`
    : ({ fora: "em Fora dos critérios", visitada: "em Não seguidas", seguir: "em Seguidas" } as Record<string, string>)[
        v.triagem
      ] || "em Para decidir"
  return `Essa vaga já estava no dashboard, ${onde}: ${v.titulo}.`
}

const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
const ROTULO = "text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1"

export default function AddJobModal({ onClose, onVagaAdicionada, onAviso }: AddJobModalProps) {
  const { servidor, podeAlterar, ia, tratarErro } = useFerramenta()
  const gravarBloqueado = servidor !== "no_ar"
  const [passo, setPasso] = useState<Passo>("inicio")
  const [link, setLink] = useState("")
  const [colado, setColado] = useState("")
  const [colarUrl, setColarUrl] = useState("")
  const [status, setStatus] = useState<{ texto: string; erro?: boolean }>({ texto: "" })
  const [ocupado, setOcupado] = useState(false)
  const seq = useRef(0) // respostas que chegam depois de mudar de passo são ignoradas

  // formulário
  const [titulo, setTitulo] = useState("")
  const [empresa, setEmpresa] = useState("")
  const [plataforma, setPlataforma] = useState("LinkedIn")
  const [url, setUrl] = useState("")
  const [local, setLocal] = useState("")
  const [descricao, setDescricao] = useState("")
  const [etapa, setEtapa] = useState<"relatorio" | Etapa>("relatorio")
  const [area, setArea] = useState<Area>("nacional")
  const [pais, setPais] = useState("")
  const [email, setEmail] = useState("")
  const [assunto, setAssunto] = useState("")
  const [extras, setExtras] = useState<{ formato?: "post"; post_id?: string; publicado_por?: string }>({})

  const mostrarFormulario = (destino: "relatorio" | Etapa, parcial: ParcialVaga & Record<string, any> = {}) => {
    setPasso("formulario")
    const u = parcial.url || (parcial.formato ? "" : link.trim())
    setUrl(u)
    if (parcial.titulo) setTitulo(parcial.titulo)
    if (parcial.empresa) setEmpresa(parcial.empresa)
    if (parcial.local) setLocal(parcial.local)
    if (parcial.descricao) setDescricao(String(parcial.descricao).slice(0, 20000))
    if (parcial.email_candidatura) setEmail(parcial.email_candidatura)
    if (parcial.assunto_candidatura) setAssunto(parcial.assunto_candidatura)
    setExtras({
      formato: parcial.formato === "post" ? "post" : undefined,
      post_id: parcial.post_id || undefined,
      publicado_por: parcial.publicado_por || undefined,
    })
    setPlataforma(
      parcial.plataforma && (PLATAFORMAS as string[]).includes(parcial.plataforma)
        ? parcial.plataforma
        : u
          ? plataformaDoLink(u)
          : "LinkedIn",
    )
    setArea(parcial.area === "internacional" ? "internacional" : "nacional")
    setPais(parcial.pais_vaga || "")
    setEtapa(destino)
  }

  // A IA (deste computador) só preenche o formulário; sem IA, o formulário vem direto com o que houver.
  const preencherComIA = async (
    parcial: ParcialVaga & Record<string, any>,
    fonte: { texto: string; autor?: string; autor_tipo?: string },
    infoIA: InfoIA | null,
  ) => {
    const avisos: string[] = []
    if (fonte.autor_tipo !== undefined && (fonte.texto || "").length < 200) {
      avisos.push(
        "o texto do post é curto: a vaga pode estar na imagem do post; se estiver, cole o texto dela na descrição",
      )
    }
    const abrir = (msg: string, erro = false) => {
      mostrarFormulario("relatorio", parcial)
      setStatus({ texto: [msg, ...avisos].filter(Boolean).join(" · "), erro: erro || avisos.length > 0 })
    }
    if (!infoIA || !infoIA.disponivel || !infoIA.local) {
      abrir(
        !infoIA || !infoIA.disponivel
          ? "Sem IA: confira os dados e complete o cargo e o local."
          : "A leitura com IA só funciona no computador onde a ferramenta roda: confira os dados e complete o cargo e o local.",
        true,
      )
      return
    }
    const meu = ++seq.current
    setOcupado(true)
    setStatus({ texto: `Em análise pela IA (${[infoIA.provedor, infoIA.modelo].filter(Boolean).join(" · ")}), aguarde…` })
    try {
      const j = await vagasApi.extrair(fonte.texto, fonte.autor, fonte.autor_tipo)
      if (meu !== seq.current) return
      Object.entries(j.campos || {}).forEach(([k, v]) => {
        if (v) parcial[k] = v
      })
      if (j.parece_vaga === false) avisos.push("a IA achou que o texto não parece uma vaga")
      if (j.vagas > 1) {
        avisos.push(`o texto traz ${j.vagas} vagas e esta é a primeira; para as outras, use Colar texto de post ou mensagem`)
      }
      abrir(`Preenchido pela IA (${[j.provedor, j.modelo].filter(Boolean).join(" · ")}): confira antes de adicionar.`)
    } catch (e) {
      if (meu !== seq.current) return
      tratarErro(e)
      abrir(`A IA não conseguiu ler (${mensagemDeErro(e, "erro")}). Confira os dados e complete o cargo e o local.`, true)
    } finally {
      if (meu === seq.current) setOcupado(false)
    }
  }

  const buscarLink = async () => {
    const u = link.trim()
    if (!u) {
      setStatus({ texto: "Cole o link da vaga.", erro: true })
      return
    }
    const meu = ++seq.current
    setOcupado(true)
    setStatus({ texto: "Lendo a vaga…" })
    try {
      const j = await vagasApi.porLink(u)
      if (meu !== seq.current) return
      if (j.post && j.parcial) {
        setOcupado(false)
        await preencherComIA(
          { ...j.parcial },
          { texto: j.post.texto, autor: j.post.autor, autor_tipo: j.post.autor_tipo },
          j.ia || null,
        )
        return
      }
      if (j.vaga) {
        onVagaAdicionada(j.vaga)
        onAviso(j.nova ? avisoAdicionada(j.vaga, j.analise_automatica) : jaEstava(j.vaga))
        onClose()
      }
    } catch (e) {
      if (meu !== seq.current) return
      tratarErro(e)
      if (ehErroApi(e) && e.status === 422 && e.dados?.sugestao === "colar") {
        setColarUrl(e.dados?.parcial?.url || "")
        setPasso("colar")
        setStatus({
          texto: `Não consegui ler o post (${e.message}). Copie o texto do post e cole abaixo, ou preencha à mão.`,
          erro: true,
        })
      } else if (ehErroApi(e) && e.status === 422) {
        mostrarFormulario("relatorio", e.dados?.parcial || {})
        setStatus({ texto: `Não consegui ler a vaga (${e.message}). Complete os dados abaixo.`, erro: true })
      } else {
        setStatus({ texto: mensagemDeErro(e, "Não deu para ler o link."), erro: true })
      }
    } finally {
      if (meu === seq.current) setOcupado(false)
    }
  }

  const seguirComTexto = () => {
    const texto = colado.trim()
    if (!texto) {
      setStatus({ texto: "Cole o texto.", erro: true })
      return
    }
    if (texto.length >= 20000) onAviso("O texto foi cortado em 20.000 caracteres.", "erro")
    preencherComIA(
      { descricao: texto.slice(0, 20000), plataforma: "LinkedIn", formato: "post", url: colarUrl },
      { texto: texto.slice(0, 20000) },
      ia
        ? { disponivel: ia.disponivel, local: podeAlterar, provedor: ia.nome, modelo: ia.modelo }
        : { disponivel: false, local: false, provedor: "", modelo: "" },
    )
  }

  const adicionar = async (ev: React.FormEvent) => {
    ev.preventDefault()
    const corpo: NovaVaga = {
      titulo: titulo.trim(),
      empresa: empresa.trim(),
      plataforma,
      url: url.trim(),
      local: local.trim(),
      descricao: descricao.trim().slice(0, 20000),
      etapa,
      area,
      pais_vaga: area === "internacional" ? pais.trim() : "",
      email_candidatura: email.trim(),
      assunto_candidatura: assunto.trim(),
      ...(extras.formato ? { formato: extras.formato } : {}),
      ...(extras.post_id ? { post_id: extras.post_id } : {}),
      ...(extras.publicado_por ? { publicado_por: extras.publicado_por } : {}),
    }
    if (!corpo.titulo || !corpo.empresa) {
      setStatus({ texto: "Informe pelo menos o cargo e a empresa.", erro: true })
      return
    }
    if (corpo.url && !/^https?:\/\//i.test(corpo.url)) {
      setStatus({ texto: "O link precisa começar com http:// ou https://.", erro: true })
      return
    }
    setOcupado(true)
    try {
      const j = await vagasApi.criar(corpo)
      onVagaAdicionada(j.vaga)
      onAviso(j.nova === false ? jaEstava(j.vaga) : avisoAdicionada(j.vaga, j.analise_automatica))
      onClose()
    } catch (e) {
      tratarErro(e)
      setStatus({ texto: mensagemDeErro(e, "Não deu para adicionar a vaga."), erro: true })
    } finally {
      setOcupado(false)
    }
  }

  const trocarPasso = (p: Passo, destino?: "relatorio" | Etapa) => {
    seq.current++
    setOcupado(false)
    setStatus({ texto: "" })
    if (p === "formulario") mostrarFormulario(destino || "salva")
    else setPasso(p)
  }

  const motivo = gravarBloqueado ? motivoSemGravar(servidor, podeAlterar) : ""

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-adicionar"
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-adicionar" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Adicionar vaga
              </h3>
              <p className="text-xs text-slate-500">
                Pelo link do anúncio, pelo texto de um post ou mensagem, ou preenchendo os dados.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 gap-1 sm:gap-2 bg-white dark:bg-slate-900 overflow-x-auto">
          {(
            [
              ["inicio", "Pelo link", LinkIcon],
              ["colar", "Colar texto de post ou mensagem", FileText],
              ["formulario", "Preencher à mão", Edit],
            ] as [Passo, string, typeof LinkIcon][]
          ).map(([p, rotulo, Icone]) => (
            <button
              key={p}
              type="button"
              onClick={() => trocarPasso(p)}
              className={`py-3 px-2 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${
                passo === p
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <Icone className="w-3.5 h-3.5" />
              <span>{rotulo}</span>
            </button>
          ))}
        </div>

        <form onSubmit={adicionar} className="p-6 overflow-y-auto flex-1 space-y-4">
          {motivo && (
            <p className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300">{motivo}</p>
          )}

          {passo === "inicio" && (
            <div className="space-y-3 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
              <label htmlFor="add-link" className={ROTULO}>
                Link do anúncio (Indeed, Gupy, LinkedIn, InfoJobs, Vagas.com, JobGether, Greenhouse, Lever, Ashby,
                Nerdin…) ou de um post do LinkedIn
              </label>
              <div className="flex gap-2 flex-col sm:flex-row">
                <input
                  id="add-link"
                  type="url"
                  value={link}
                  maxLength={1000}
                  autoFocus
                  onChange={(e) => setLink(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      buscarLink()
                    }
                  }}
                  placeholder="https://..."
                  className={CAMPO}
                />
                <button
                  type="button"
                  onClick={buscarLink}
                  disabled={ocupado || gravarBloqueado}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs shrink-0"
                >
                  {ocupado ? "Lendo…" : "Buscar dados"}
                </button>
              </div>
              <p className="text-[11px] text-slate-500">
                A vaga vai para o Relatório. O link de um post é lido uma vez, na versão pública, sem login.
              </p>
            </div>
          )}

          {passo === "colar" && (
            <div className="space-y-3 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
              <label htmlFor="add-colar" className={ROTULO}>
                Texto do post, e-mail ou mensagem com a vaga
              </label>
              <textarea
                id="add-colar"
                rows={6}
                value={colado}
                onChange={(e) => setColado(e.target.value)}
                placeholder="Cole aqui o texto inteiro da vaga…"
                className={CAMPO}
              />
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <p className="text-[11px] text-slate-500">
                  {ia?.disponivel
                    ? `A IA (${ia.nome}${ia.modelo ? " · " + ia.modelo : ""}) só preenche o formulário; você confere antes de adicionar.${
                        ia.cobranca === "uso" ? " Cobrado por uso: consome créditos." : ""
                      }`
                    : "Sem IA, o texto vai para a descrição e você completa o resto."}
                </p>
                <button
                  type="button"
                  onClick={seguirComTexto}
                  disabled={ocupado || gravarBloqueado}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-xs"
                >
                  {ocupado ? "Lendo…" : ia?.disponivel ? "Preencher com IA" : "Continuar"}
                </button>
              </div>
            </div>
          )}

          {status.texto && (
            <p
              role="status"
              className={`flex items-start gap-2 text-xs p-3 rounded-xl ${
                status.erro
                  ? "bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 border border-amber-200 dark:border-amber-900"
                  : "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-900"
              }`}
            >
              {ocupado ? (
                <Loader2 className="w-4 h-4 shrink-0 animate-spin" />
              ) : status.erro ? (
                <AlertTriangle className="w-4 h-4 shrink-0" />
              ) : (
                <Info className="w-4 h-4 shrink-0" />
              )}
              <span>{status.texto}</span>
            </p>
          )}

          {passo === "formulario" && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="a-titulo" className={ROTULO}>Cargo *</label>
                  <input id="a-titulo" required value={titulo} onChange={(e) => setTitulo(e.target.value)} className={CAMPO} />
                </div>
                <div>
                  <label htmlFor="a-empresa" className={ROTULO}>Empresa *</label>
                  <input id="a-empresa" required value={empresa} onChange={(e) => setEmpresa(e.target.value)} className={CAMPO} />
                </div>
                <div>
                  <label htmlFor="a-plataforma" className={ROTULO}>Plataforma</label>
                  <select id="a-plataforma" value={plataforma} onChange={(e) => setPlataforma(e.target.value)} className={CAMPO}>
                    {PLATAFORMAS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="a-local" className={ROTULO}>Local</label>
                  <input id="a-local" value={local} onChange={(e) => setLocal(e.target.value)} placeholder="Ex.: Remoto, São Paulo, SP…" className={CAMPO} />
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="a-url" className={ROTULO}>Link da vaga</label>
                  <input id="a-url" type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." className={CAMPO} />
                </div>
                <div>
                  <label htmlFor="a-etapa" className={ROTULO}>Para onde vai</label>
                  <select id="a-etapa" value={etapa} onChange={(e) => setEtapa(e.target.value as "relatorio" | Etapa)} className={CAMPO}>
                    {ETAPAS_DESTINO.map((x) => (
                      <option key={x.valor} value={x.valor}>{x.rotulo}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="a-area" className={ROTULO}>Área</label>
                  <select id="a-area" value={area} onChange={(e) => setArea(e.target.value as Area)} className={CAMPO}>
                    <option value="nacional">Nacional</option>
                    <option value="internacional">Internacional</option>
                  </select>
                </div>
                {area === "internacional" && (
                  <div className="sm:col-span-2">
                    <label htmlFor="a-pais" className={ROTULO}>País da vaga</label>
                    <input id="a-pais" value={pais} onChange={(e) => setPais(e.target.value)} className={CAMPO} />
                  </div>
                )}
                <div>
                  <label htmlFor="a-email" className={ROTULO}>E-mail para candidatura (se a vaga pedir)</label>
                  <input id="a-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={CAMPO} />
                </div>
                <div>
                  <label htmlFor="a-assunto" className={ROTULO}>Assunto do e-mail</label>
                  <input id="a-assunto" value={assunto} onChange={(e) => setAssunto(e.target.value)} className={CAMPO} />
                </div>
              </div>
              <div>
                <label htmlFor="a-descricao" className={ROTULO}>Descrição da vaga</label>
                <textarea
                  id="a-descricao"
                  rows={6}
                  value={descricao}
                  maxLength={20000}
                  onChange={(e) => setDescricao(e.target.value)}
                  placeholder="Requisitos e responsabilidades, para a nota de aderência…"
                  className={CAMPO}
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={ocupado || gravarBloqueado}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition disabled:opacity-50"
                >
                  {ocupado ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Adicionar</span>
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}
