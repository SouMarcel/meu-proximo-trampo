/**
 * Meu perfil / Primeiros passos (dash/API.md §3.6), como no dashboard antigo: o perfil sai do que a pessoa já tem
 * (currículos e LinkedIn) e de perguntas; nada é gravado no perfil.md sem ela conferir e confirmar.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { X, User, Loader2, AlertTriangle, Sparkles } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { AreaMaterial, EstadoPerfil, EtapaPerfil, FiltrosPropostos, Previa, PropostaDoCurriculo, CurriculosDaPasta, Pergunta, LinhaIdioma } from "../../services/api/perfil"
import * as configApi from "../../services/api/config"
import type { Filtros } from "../../services/api/config"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { diaMes } from "../../utils/formatters"
import Analises from "./Analises"
import Relatos from "./Relatos"
import Materiais from "./Materiais"
import InformacoesBasicas from "./InformacoesBasicas"
import PerguntaIdiomas, { LINHA_VAZIA, respostaIdiomas } from "./PerguntaIdiomas"
import { GerarCurriculo, SecaoCurriculos } from "../curriculo/Curriculos"

type Tela = EtapaPerfil | "do-curriculo" | "analises" | "curriculos" | "basicas"
/** Telas fora do passo a passo: não gravam a etapa do perfil e não mostram Recomeçar. */
const FORA_DOS_PASSOS: Tela[] = ["do-curriculo", "analises", "curriculos", "basicas"]
const ehPasso = (t: Tela): t is EtapaPerfil => !FORA_DOS_PASSOS.includes(t)

interface Props {
  /** Abre direto numa tela (ex.: "analises", vindo do painel internacional; "basicas", de Atualizar candidaturas). */
  telaInicial?: Tela
  onClose: () => void
  onAviso: (mensagem: string, tipo?: "info" | "erro") => void
  /** "Ajustar antes": abre os Filtros da busca com a proposta; depois de salvar, volta para cá. */
  onAjustarFiltros: (proposta: Filtros, depois: () => void) => void
  onAbrirFiltrosInt: () => void
  /** "Usar este currículo e ir para as vagas" confirmado: recarregar e abrir a busca. */
  onUsouCurriculo: () => void
  /** O perfil mudou (gravado, recomeçado): o resto da página relê o que depende dele. */
  onPerfilMudou: () => void
}

const PASSOS: { k: EtapaPerfil; label: string }[] = [
  { k: "ia", label: "IA" },
  { k: "materiais", label: "Materiais" },
  { k: "rascunho", label: "Rascunho" },
  { k: "conflitos", label: "Conflitos" },
  { k: "anamnese", label: "Perguntas" },
  { k: "diagnostico", label: "Diagnóstico" },
  { k: "revisao", label: "Revisão" },
  { k: "filtros", label: "Filtros" },
]
const SECOES: [keyof perfilApi.Rascunho, string][] = [
  ["objetivo", "Objetivo"],
  ["resumo", "Resumo"],
  ["formacao", "Formação"],
  ["certificacoes", "Certificações"],
  ["habilidades", "Habilidades"],
  ["idiomas", "Idiomas"],
]
const CONTATOS: [keyof perfilApi.Contato, string, "emails" | "telefones" | "linkedin"][] = [
  ["email", "E-mail", "emails"],
  ["telefone", "Telefone", "telefones"],
  ["linkedin", "LinkedIn", "linkedin"],
]
const MODOS: Record<string, string> = { remoto: "Remoto", hibrido: "Híbrido", presencial: "Presencial" }

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"
const AVISO = "p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs"
const BTN = "px-4 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
const BTN_PRI = `${BTN} text-white bg-indigo-600 hover:bg-indigo-500`
const BTN_SEC = `${BTN} text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700`
const BTN_MINI = "px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"

/** {{conflito:N}} no texto do rascunho vira "⚠ conflito N+1". */
const tok = (s?: string) => String(s ?? "").replace(/\{\{conflito:(\d+)\}\}/g, (_, n) => `⚠ conflito ${Number(n) + 1}`)

function Fonte({ f }: { f?: string }) {
  return f ? <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">{f}</span> : null
}

function Itens({ l }: { l?: perfilApi.ItemComFonte[] }) {
  if (!l || !l.length) return null
  return (
    <ul className="list-disc pl-5 space-y-0.5">
      {l.map((i, k) => (
        <li key={k}>
          {tok(i.texto)}
          <Fonte f={i.fonte} />
        </li>
      ))}
    </ul>
  )
}

function valorLegivel(v: unknown): string {
  if (Array.isArray(v)) return v.length ? v.map((x) => String(x).replace(/"/g, "")).join(", ") : "nenhum"
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>
    if ("ativo" in o) return o.ativo ? `ligada: ${valorLegivel(o.paises)} · ${valorLegivel(o.termos)}` : "desligada"
    if ("cidade" in o) return [o.cidade, o.estado, o.pais].filter(Boolean).join(", ") || "não informado"
    return Object.keys(o).filter((k) => o[k] === true).map((k) => MODOS[k] || k).join(", ") || "nenhum"
  }
  return String(v ?? "")
}

function lerArquivo(f: File): Promise<string> {
  return new Promise((ok, falha) => {
    const r = new FileReader()
    r.onload = () => ok(String(r.result).replace(/^data:[^,]*,/, ""))
    r.onerror = () => falha(new Error("não deu para ler o arquivo"))
    r.readAsDataURL(f)
  })
}

export default function MeuPerfil({
  telaInicial,
  onClose,
  onAviso,
  onAjustarFiltros,
  onAbrirFiltrosInt,
  onUsouCurriculo,
  onPerfilMudou,
}: Props) {
  const { podeGravar, ia, abrirPainelIA, tratarErro } = useFerramenta()
  const [e, setE] = useState<EstadoPerfil | null>(null)
  const [tela, setTela] = useState<Tela>("ia")
  const [q, setQ] = useState(0)
  const [prev, setPrev] = useState<Previa | null>(null)
  const [md, setMd] = useState<string | null>(null)
  const [editado, setEditado] = useState(false)
  const [sujo, setSujo] = useState(false)
  const [dica, setDica] = useState("")
  const [confirmar, setConfirmar] = useState(false)
  const [fp, setFp] = useState<FiltrosPropostos | { erro: string } | null>(null)
  const [cvs, setCvs] = useState<CurriculosDaPasta | null>(null)
  const [dc, setDc] = useState<PropostaDoCurriculo | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [carregando, setCarregando] = useState("")
  const [erro, setErro] = useState("")
  const [gerarBase, setGerarBase] = useState(false)
  const corpoRef = useRef<HTMLDivElement>(null)

  const so = Boolean(e && !e.pode_alterar) || !podeGravar // só leitura
  const falhou = useCallback(
    (err: unknown) => {
      tratarErro(err)
      setErro(mensagemDeErro(err))
    },
    [tratarErro],
  )

  // abertura e quando a IA muda (o passo IA mostra a escolhida; o rascunho depende dela)
  useEffect(() => {
    perfilApi
      .estado()
      .then((j) => {
        setE(j)
        setTela((t) => (t === "ia" ? telaInicial || j.etapa : t))
      })
      .catch((err) => setErro("Não deu para abrir o perfil: " + mensagemDeErro(err)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ia?.nome, ia?.modelo, ia?.disponivel])

  const ir = (t: Tela) => {
    setTela(t)
    setConfirmar(false)
    setErro("")
    if (t === "diagnostico") setPrev(null)
    if (t === "filtros") setFp(null)
    if (t !== "revisao") setDica("")
    if (!so && ehPasso(t)) {
      perfilApi.progresso({ etapa: t }).then(setE).catch(() => undefined)
    }
    corpoRef.current?.scrollTo(0, 0)
  }

  const salvarProgresso = async (corpo: Parameters<typeof perfilApi.progresso>[0]) => {
    const j = await perfilApi.progresso(corpo)
    setE(j)
    setSujo(true)
    setPrev(null)
    return j
  }

  const pedirPrevia = useCallback(
    async (texto: string | null, substituir = false) => {
      setCarregando("Montando o perfil…")
      try {
        const j = await perfilApi.previa(texto)
        setPrev(j)
        if (substituir || texto == null) {
          setMd(j.markdown)
          setEditado(false)
          setSujo(false)
        }
        return j
      } catch (err) {
        falhou(err)
        return null
      } finally {
        setCarregando("")
      }
    },
    [falhou],
  )

  // o que cada tela precisa carregar
  useEffect(() => {
    if (!e || carregando || erro) return // com erro, espera a pessoa agir (trocar de passo limpa o erro)
    if (tela === "diagnostico" && !prev) pedirPrevia(md)
    else if (tela === "revisao" && (md == null || (sujo && !editado))) pedirPrevia(null, true)
    else if (tela === "revisao" && !prev) pedirPrevia(md)
    else if (tela === "filtros" && e.existe_perfil && !fp) {
      setCarregando("Montando a proposta…")
      perfilApi
        .filtrosPropostos()
        .then(setFp)
        .catch((err) => setFp({ erro: mensagemDeErro(err) }))
        .finally(() => setCarregando(""))
    } else if ((tela === "materiais" || tela === "concluido" || tela === "curriculos") && !cvs && e.pode_alterar) {
      perfilApi
        .curriculos()
        .then(setCvs)
        .catch(() => setCvs({ curriculos: [], curriculo_base: { pt: null, en: null }, existe_perfil: e.existe_perfil }))
    }
  }, [tela, e, prev, md, sujo, editado, fp, cvs, carregando, erro, pedirPrevia])

  // ---------- materiais ----------
  /** Envia os arquivos para a área; devolve os materiais que entraram (os recusados já viram aviso). */
  const enviarArquivos = async (files: FileList | File[] | null, area: AreaMaterial): Promise<perfilApi.Material[]> => {
    const novos: perfilApi.Material[] = []
    for (const f of Array.from(files || [])) {
      if (f.size > 10 * 1024 * 1024) {
        onAviso(`${f.name}: arquivo grande demais (o limite é 10 MB).`, "erro")
        continue
      }
      try {
        const b64 = await lerArquivo(f)
        onAviso(`Lendo ${f.name}…`)
        const j = await perfilApi.enviarMaterial({ nome: f.name, base64: b64, area })
        setE(j.estado)
        setSujo(true)
        setPrev(null)
        const comAviso = j.material.avisos.length > 0 && !j.material.ocr // texto lido por OCR: aviso de conferir, não erro
        onAviso(`${f.name} lido${j.material.ocr ? " da imagem (OCR): confira o texto." : comAviso ? ", com aviso." : "."}`, comAviso ? "erro" : "info")
        novos.push(j.material)
      } catch (err) {
        tratarErro(err)
        onAviso(`${f.name}: ${mensagemDeErro(err)}`, "erro")
      }
    }
    return novos
  }

  const usarCurriculo = async (arquivo: string) => {
    setDc(null)
    setTela("do-curriculo")
    setErro("")
    try {
      setDc(await perfilApi.doCurriculo(arquivo))
    } catch (err) {
      setTela("materiais")
      falhou(err)
    }
  }

  // ---------- perguntas ----------
  const perguntas = useMemo<Pergunta[]>(() => {
    if (!e) return []
    const resp = e.respostas || {}
    return e.perguntas.filter((p) => !p.condicao || resp[p.condicao] === true)
  }, [e])

  const recomecar = async (perguntar: boolean) => {
    if (
      perguntar &&
      !window.confirm(
        "Recomeçar apaga o progresso (respostas e rascunho). Os arquivos enviados continuam na pasta anexos. Continuar?",
      )
    )
      return
    try {
      const j = await perfilApi.recomecar()
      setE(j)
      setTela(j.etapa)
      setQ(0)
      setPrev(null)
      setMd(null)
      setEditado(false)
      setFp(null)
      setErro("")
    } catch (err) {
      falhou(err)
    }
  }

  // ---------- telas ----------
  let corpo: React.ReactNode = null
  let pe: React.ReactNode = null

  const botaoIr = (t: Tela, rotulo: string, primario = false) => (
    <button type="button" onClick={() => ir(t)} className={primario ? BTN_PRI : BTN_SEC}>
      {rotulo}
    </button>
  )

  if (!e) {
    corpo = erro ? null : (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
      </p>
    )
  } else if (carregando && tela !== "rascunho") {
    corpo = (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> {carregando}
      </p>
    )
  } else if (tela === "ia") {
    const nome = !ia ? "…" : !ia.nome ? "nenhuma (seguir sem IA)" : `${ia.nome}${ia.modelo ? " · " + ia.modelo : ""}${ia.disponivel ? "" : " (falta a chave)"}`
    corpo = (
      <>
        <p className={AVISO}>
          <b>Já tem um currículo pronto?</b> No próximo passo, envie o arquivo (ou escolha um da pasta anexos) e use{" "}
          <b>Usar este currículo e ir para as vagas</b>: sem perguntas, você confere uma tela só e já vai para a busca.
        </p>
        <p className="text-slate-700 dark:text-slate-300">
          Vamos montar o seu perfil de carreira a partir do que você já tem (currículos e LinkedIn) e de algumas
          perguntas. O perfil é a base da nota de aderência das vagas. Nada é gravado sem você conferir e confirmar; dá
          para parar e continuar depois.
        </p>
        <section className={SEC}>
          <h4 className={H}>IA</h4>
          <p className="flex items-center gap-2 flex-wrap">
            IA escolhida: <b>{nome}</b>
            <button type="button" onClick={abrirPainelIA} className={BTN_MINI}>
              Trocar
            </button>
          </p>
          <ul className="list-disc pl-5 space-y-1 text-slate-700 dark:text-slate-300">
            <li>Com IA, ela lê os seus materiais e propõe um rascunho do perfil, mostrando de onde veio cada item.</li>
            <li>Sem IA, você monta o perfil com o texto dos materiais ao lado; o que vier da exportação do LinkedIn já entra preenchido.</li>
            <li>CPF, RG e data de nascimento são retirados antes de qualquer envio e nunca entram no perfil.</li>
          </ul>
        </section>
      </>
    )
    pe = botaoIr("materiais", "Continuar", true)
  } else if (tela === "materiais") {
    corpo = <Materiais e={e} cvs={cvs} so={so} onEnviar={enviarArquivos} onUsar={usarCurriculo} onEstado={(j) => { setE(j); setSujo(true); setPrev(null) }} onErro={falhou} onAviso={onAviso} onLinkedin={async (li) => {
      const ct = e.contato || {}
      if (so || li === (ct.linkedin || "")) return ir("rascunho")
      try {
        await salvarProgresso({ contato: { ...ct, linkedin: li } })
        ir("rascunho")
      } catch (err) {
        falhou(err)
      }
    }} />
    pe = null // os botões ficam dentro de Materiais (dependem do campo do LinkedIn)
  } else if (tela === "rascunho") {
    const r = e.rascunho
    const comIA = e.ia_disponivel
    const gerar = async (semIA: boolean) => {
      setOcupado(true)
      setErro("")
      try {
        const j = await perfilApi.rascunho(semIA)
        setE(j)
        setSujo(true)
        setPrev(null)
      } catch (err) {
        falhou(err)
      } finally {
        setOcupado(false)
      }
    }
    const acoes = (
      <div className="flex gap-2 flex-wrap">
        {comIA && (
          <button type="button" disabled={so || ocupado} onClick={() => gerar(false)} className={BTN_PRI}>
            {r ? "Gerar de novo com IA" : "Gerar rascunho com IA"}
          </button>
        )}
        <button type="button" disabled={so || ocupado} onClick={() => gerar(true)} className={BTN_SEC}>
          {r && !comIA ? "Montar de novo" : "Montar sem IA"}
        </button>
      </div>
    )
    corpo = ocupado ? (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Gerando o rascunho… pode levar até 2 minutos.
      </p>
    ) : !r ? (
      <>
        <p className="text-slate-700 dark:text-slate-300">
          {comIA
            ? "A IA lê os seus materiais e propõe o perfil, mostrando de onde veio cada item. Ela não inventa: o que não estiver nos materiais fica para as perguntas."
            : "Sem IA disponível: o rascunho traz o que a exportação do LinkedIn tiver; o resto você completa nas perguntas e na revisão, com o texto dos materiais ao lado."}
        </p>
        {comIA && ia?.cobranca === "uso" && <p className={DICA}>{ia.nome}: cobrado por uso, consome créditos.</p>}
        {acoes}
      </>
    ) : (
      <>
        <p className={DICA}>
          {r.origem === "sem_ia"
            ? "Montado sem IA: só o que veio da exportação do LinkedIn. O resto você completa nas perguntas e na revisão."
            : "Cada item mostra de onde veio. O que estiver errado você corrige na revisão."}
        </p>
        {SECOES.map(([k, rot]) =>
          (r[k] as perfilApi.ItemComFonte[] | undefined)?.length ? (
            <section key={k} className={SEC}>
              <h4 className={H}>{rot}</h4>
              <Itens l={r[k] as perfilApi.ItemComFonte[]} />
            </section>
          ) : null,
        )}
        {r.experiencias.length > 0 && (
          <section className={SEC}>
            <h4 className={H}>Experiência</h4>
            {r.experiencias.map((x, i) => (
              <div key={i}>
                <p>
                  <b>{tok([x.cargo, x.empresa].filter(Boolean).join(" — "))}</b>{" "}
                  {x.inicio || x.fim ? `(${tok(x.inicio || "?")}–${tok(x.fim || "atual")})` : ""}
                  <Fonte f={x.fonte} />
                </p>
                <Itens l={x.itens} />
              </div>
            ))}
          </section>
        )}
        {!SECOES.some(([k]) => (r[k] as unknown[] | undefined)?.length) && !r.experiencias.length && (
          <p className={DICA}>Nada encontrado nos materiais. Siga para as perguntas.</p>
        )}
        {r.conflitos.length > 0 && (
          <p className={AVISO}>
            {r.conflitos.length}{" "}
            {r.conflitos.length > 1 ? "pontos em que as fontes discordam" : "ponto em que as fontes discordam"}: você
            escolhe no próximo passo.
          </p>
        )}
        {acoes}
      </>
    )
    pe = (
      <>
        {botaoIr("materiais", "Voltar")}
        <button type="button" disabled={!r || ocupado} onClick={() => ir(r && r.conflitos.length ? "conflitos" : "anamnese")} className={BTN_PRI}>
          Continuar
        </button>
      </>
    )
  } else if (tela === "conflitos") {
    const cf = e.rascunho?.conflitos || []
    corpo = !cf.length ? (
      <p className={DICA}>As fontes não discordam em nada.</p>
    ) : (
      <>
        <p className={DICA}>
          As fontes discordam nestes pontos. Escolha o valor certo de cada um; se nenhum estiver certo, escolha um e corrija
          na revisão.
        </p>
        {cf.map((c, i) => (
          <fieldset key={i} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5">
            <legend className="px-1 font-semibold text-slate-800 dark:text-slate-200">
              {i + 1}. {c.campo || "Conflito"}
            </legend>
            {c.opcoes.map((o, j) => (
              <label key={j} className="flex items-start gap-2 cursor-pointer">
                <input
                  type="radio"
                  name={`cf-${i}`}
                  checked={c.escolha === j}
                  disabled={so}
                  onChange={() => salvarProgresso({ escolhas: { [String(i)]: j } }).catch(falhou)}
                />
                <span>
                  {o.valor}
                  <Fonte f={o.fonte} />
                </span>
              </label>
            ))}
            {!c.opcoes.length && <p className={DICA}>Sem opções: corrija no texto, na revisão.</p>}
          </fieldset>
        ))}
      </>
    )
    pe = (
      <>
        {botaoIr("rascunho", "Voltar")}
        {botaoIr("anamnese", "Continuar", true)}
      </>
    )
  } else if (tela === "anamnese") {
    const idx = Math.max(0, Math.min(q, perguntas.length - 1))
    const p = perguntas[idx]
    corpo = p ? (
      <PerguntaAtual
        key={p.id}
        p={p}
        n={idx}
        total={perguntas.length}
        valor={(e.respostas || {})[p.id]}
        so={so}
        onVoltar={() => (idx > 0 ? setQ(idx - 1) : ir(e.rascunho?.conflitos.length ? "conflitos" : "rascunho"))}
        onResponder={async (valor) => {
          const seguir = () => (idx + 1 >= perguntas.length ? ir("diagnostico") : setQ(idx + 1))
          if (so) return seguir()
          try {
            await salvarProgresso({ respostas: { [p.id]: valor } })
            seguir()
          } catch (err) {
            falhou(err)
          }
        }}
      />
    ) : (
      <p className={DICA}>Nenhuma pergunta. Siga para o diagnóstico.</p>
    )
    pe = p ? null : botaoIr("diagnostico", "Continuar", true)
  } else if (tela === "diagnostico" && prev) {
    const d = prev.diagnostico
    const ac = e.contatos_achados || {}
    const ct = e.contato || {}
    const rot: Record<string, string> = { falta: "Falta", fraco: "Fraco", info: "Atenção" }
    const responder = (a: Previa["diagnostico"][number]) => {
      if (a.ir.startsWith("pergunta:")) {
        const i = perguntas.findIndex((x) => x.id === a.ir.slice(9))
        if (i >= 0) {
          setQ(i)
          return ir("anamnese")
        }
      }
      if (a.ir === "conflitos") return ir("conflitos")
      ir("revisao")
      setDica(`${a.mensagem} ${a.pergunta} Escreva no texto abaixo.`)
    }
    corpo = (
      <>
        {d.length ? (
          <>
            <p className={DICA}>O que ainda falta ou está fraco. Responda o que quiser; o resto pode ficar como está.</p>
            <ul className="space-y-2">
              {d.map((a, i) => (
                <li key={i} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                  <p>
                    <b className={a.tipo === "falta" ? "text-rose-600" : a.tipo === "fraco" ? "text-amber-600" : "text-slate-500"}>
                      {rot[a.tipo] || a.tipo}
                    </b>{" "}
                    {a.mensagem}
                  </p>
                  <p className={DICA}>{a.pergunta}</p>
                  <button type="button" onClick={() => responder(a)} className={BTN_MINI}>
                    Responder
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p>Nada faltando. Siga para a revisão.</p>
        )}
        {CONTATOS.some(([k, , achadosK]) => ct[k] || (k === "linkedin" ? ac.linkedin : (ac[achadosK] as string[] | undefined)?.length)) && (
          <section className={SEC}>
            <h4 className={H}>Contato no perfil</h4>
            <p className={DICA}>
              Achado nos seus materiais. Escolha o que entra no perfil; o perfil vai para a IA escolhida quando ela analisa
              as vagas.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {CONTATOS.map(([k, rotulo, achadosK]) => {
                const achados = k === "linkedin" ? (ac.linkedin ? [ac.linkedin] : []) : [...((ac[achadosK] as string[] | undefined) || [])]
                if (ct[k] && !achados.includes(ct[k] as string)) achados.unshift(ct[k] as string)
                if (!achados.length) return null
                return (
                  <div key={k}>
                    <label htmlFor={`ct-${k}`} className={ROTULO}>{rotulo}</label>
                    <select
                      id={`ct-${k}`}
                      value={ct[k] || ""}
                      disabled={so}
                      onChange={(ev) => {
                        const novo: perfilApi.Contato = { ...ct }
                        if (ev.target.value) novo[k] = ev.target.value
                        else delete novo[k]
                        salvarProgresso({ contato: novo }).catch(falhou)
                      }}
                      className={CAMPO}
                    >
                      <option value="">Não incluir</option>
                      {achados.map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  </div>
                )
              })}
            </div>
          </section>
        )}
      </>
    )
    pe = (
      <>
        {botaoIr("anamnese", "Voltar")}
        {botaoIr("revisao", "Revisar o perfil", true)}
      </>
    )
  } else if (tela === "revisao" && prev && md != null) {
    const pend = (md.match(/\{\{conflito:\d+\}\}/g) || []).length
    const gravar = async () => {
      if (e.existe_perfil && !confirmar) {
        const j = await pedirPrevia(md)
        if (j) setConfirmar(true)
        return
      }
      try {
        const j = await perfilApi.gravar(md)
        onAviso(`Perfil gravado em ${j.gravado}${j.anterior ? `; a versão anterior ficou em ${j.anterior}` : ""}.`)
        setMd(null)
        setEditado(false)
        setConfirmar(false)
        setE(await perfilApi.estado())
        onPerfilMudou()
        ir("filtros")
      } catch (err) {
        falhou(err)
      }
    }
    corpo = (
      <>
        {dica && <p className={AVISO}>{dica}</p>}
        {sujo && editado && (
          <p className={AVISO}>
            Você respondeu mais coisas depois de editar este texto.{" "}
            <button type="button" onClick={() => pedirPrevia(null, true)} className={BTN_MINI}>
              Remontar
            </button>{" "}
            (as suas edições no texto se perdem)
          </p>
        )}
        <div className={`grid gap-3 ${prev.textos.length ? "lg:grid-cols-[1fr_280px]" : ""}`}>
          <div>
            <label htmlFor="pf-md" className={ROTULO}>Seu perfil (edite à vontade; é o texto que será gravado)</label>
            <textarea
              id="pf-md"
              spellCheck
              value={md}
              disabled={so}
              onChange={(ev) => {
                setMd(ev.target.value)
                setEditado(true)
                setConfirmar(false)
              }}
              className={`${CAMPO} min-h-[360px] font-mono text-xs`}
            />
          </div>
          {prev.textos.length > 0 && (
            <aside className="space-y-1">
              <h4 className={H}>Texto dos materiais</h4>
              {prev.textos.map((t) => (
                <details key={t.nome} className="text-xs">
                  <summary className="cursor-pointer font-semibold">{t.nome}</summary>
                  <pre className="whitespace-pre-wrap max-h-64 overflow-y-auto p-2 rounded-lg bg-slate-50 dark:bg-slate-800 text-[11px]">{t.texto}</pre>
                </details>
              ))}
            </aside>
          )}
        </div>
        {pend > 0 && (
          <p className="text-xs text-rose-600 dark:text-rose-400">
            Ainda há {pend} conflito(s) sem escolha ({"{{conflito:N}}"} no texto): escolha no passo Conflitos ou troque no
            texto.
          </p>
        )}
        {confirmar && prev.diferencas && (
          <section className={SEC}>
            <h4 className={H}>O que muda no perfil atual</h4>
            {prev.diferencas.length ? (
              <pre className="whitespace-pre-wrap text-[11px] p-2 rounded-lg bg-slate-50 dark:bg-slate-800 max-h-64 overflow-y-auto">
                {prev.diferencas.map((l, i) => (
                  <span key={i} className={`block ${l.tipo === "+" ? "text-emerald-700 dark:text-emerald-400" : "text-rose-700 dark:text-rose-400"}`}>
                    {l.tipo} {l.texto}
                  </span>
                ))}
              </pre>
            ) : (
              <p className={DICA}>Nada muda em relação ao perfil atual.</p>
            )}
            <p className={DICA}>A versão atual fica guardada em anexos/perfis-anteriores.</p>
          </section>
        )}
      </>
    )
    pe = (
      <>
        {botaoIr("diagnostico", "Voltar")}
        {editado && (
          <button type="button" onClick={() => pedirPrevia(null, true)} className={BTN_SEC}>
            Desfazer edições
          </button>
        )}
        <button type="button" disabled={so} onClick={gravar} className={BTN_PRI}>
          {confirmar ? "Confirmar e gravar" : e.existe_perfil ? "Ver o que muda" : "Gravar perfil"}
        </button>
      </>
    )
  } else if (tela === "filtros") {
    if (!e.existe_perfil) {
      corpo = <p className={DICA}>Grave o perfil antes: os filtros saem dele.</p>
      pe = botaoIr("revisao", "Voltar")
    } else if (fp && "erro" in fp) {
      corpo = (
        <>
          <p className="text-rose-600 dark:text-rose-400">{fp.erro}</p>
          <p className={DICA}>Responda os cargos que você busca para ver a proposta.</p>
        </>
      )
      pe = (
        <>
          {botaoIr("revisao", "Voltar")}
          {botaoIr("concluido", "Pular")}
          <button type="button" onClick={() => { setQ(0); ir("anamnese") }} className={BTN_PRI}>
            Responder os cargos
          </button>
        </>
      )
    } else if (fp) {
      const f = fp.filtros
      const resp = e.respostas || {}
      const temEN = (resp.cargos_alvo_en || []).length > 0 || Boolean(fp.sugestao_en)
      const itens: [string, string][] = [
        ["Cargos", valorLegivel(f.termos)],
        ["Local", valorLegivel(f.localidade)],
        ["Modo de trabalho", valorLegivel(f.modelos)],
        ["Senioridade", f.senioridades.length ? valorLegivel(f.senioridades) : "todas"],
        ["Busca no exterior", valorLegivel(f.internacional)],
      ]
      corpo = (
        <>
          <p>A partir das suas respostas, estes seriam os filtros da busca de vagas. Nada muda até você gravar.</p>
          {fp.avisos.length > 0 && (
            <ul className="list-disc pl-5 space-y-1 text-slate-700 dark:text-slate-300">
              {fp.avisos.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          )}
          <section className={SEC}>
            <h4 className={H}>Proposta</h4>
            <ul className="space-y-1">
              {itens.map(([k, v]) => (
                <li key={k}>
                  <b>{k}:</b> {v}
                </li>
              ))}
            </ul>
            {!temEN && e.ia_disponivel && (
              <button
                type="button"
                disabled={so || ocupado}
                onClick={async () => {
                  setOcupado(true)
                  try {
                    setFp(await perfilApi.sugerirCargosEn())
                  } catch (err) {
                    falhou(err)
                  } finally {
                    setOcupado(false)
                  }
                }}
                className={BTN_SEC}
              >
                {ocupado ? "Pedindo à IA…" : "Sugerir os cargos em inglês com a IA"}
              </button>
            )}
          </section>
          {fp.mudancas.length ? (
            <section className={SEC}>
              <h4 className={H}>O que muda nos filtros atuais</h4>
              <ul className="space-y-1">
                {fp.mudancas.map((m) => (
                  <li key={m.campo}>
                    <b>{m.campo}:</b> {valorLegivel(m.atual)} → {valorLegivel(m.proposto)}
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <p className={DICA}>Iguais aos filtros atuais.</p>
          )}
        </>
      )
      pe = (
        <>
          {botaoIr("revisao", "Voltar")}
          {botaoIr("concluido", "Pular (manter os atuais)")}
          <button type="button" disabled={so} onClick={() => onAjustarFiltros(f, () => ir("concluido"))} className={BTN_SEC}>
            Ajustar antes
          </button>
          <button
            type="button"
            disabled={so}
            onClick={async () => {
              try {
                await configApi.gravar(f)
                onAviso("Filtros gravados. Valem a partir da próxima busca.")
                ir("concluido")
              } catch (err) {
                falhou(err)
              }
            }}
            className={BTN_PRI}
          >
            Gravar filtros
          </button>
        </>
      )
    }
  } else if (tela === "concluido") {
    corpo = (
      <>
        {e.perfil_do_curriculo && (
          <p className={AVISO}>
            Seu perfil veio do currículo <b>{e.perfil_do_curriculo.arquivo.split("/").pop()}</b> em{" "}
            {diaMes(e.perfil_do_curriculo.data)}. A nota das vagas fica mais precisa com o perfil completo (números,
            níveis, idiomas, vagas de fora).{" "}
            <button type="button" disabled={so} onClick={() => ir("rascunho")} className={BTN_MINI}>
              Completar com a anamnese
            </button>
          </p>
        )}
        <p>
          <b>Perfil pronto.</b> Ele é a base da nota de aderência das vagas e dos currículos.
        </p>
        <ul className="list-disc pl-5 space-y-1 text-slate-700 dark:text-slate-300">
          <li>Para buscar vagas, use o botão Buscar vagas, no topo (ou peça no chat do seu assistente).</li>
          <li>Para mudar o perfil depois, abra Meu perfil e escolha Atualizar o perfil: a versão atual fica guardada.</li>
        </ul>
        <SeuCurriculo cvs={cvs} so={so} onMudou={(base) => cvs && setCvs({ ...cvs, curriculo_base: base })} onAviso={onAviso} onErro={falhou} />
        <SecaoCurriculos vagaId={null} onGerar={() => setGerarBase(true)} />
        <Relatos so={so} onAviso={onAviso} onErro={falhou} onPerfilMudou={onPerfilMudou} />
      </>
    )
    pe = (
      <>
        <button type="button" disabled={so} onClick={() => recomecar(false)} className={BTN_SEC}>
          Atualizar o perfil
        </button>
        <button type="button" onClick={onClose} className={BTN_PRI}>
          Fechar
        </button>
      </>
    )
  } else if (tela === "do-curriculo") {
    corpo = dc ? (
      <DoCurriculo
        dc={dc}
        so={so}
        onVoltar={() => ir("materiais")}
        onErro={falhou}
        onPronto={(manter) => {
          onAviso(
            manter
              ? "Pronto: seu currículo marcado; perfil e filtros como estavam."
              : "Pronto: perfil feito do seu currículo e filtros gravados. Agora é só buscar.",
          )
          onPerfilMudou()
          onUsouCurriculo()
        }}
      />
    ) : (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Lendo o currículo…
      </p>
    )
    pe = null
  } else if (tela === "curriculos") {
    corpo = (
      <>
        <SeuCurriculo cvs={cvs} so={so} onMudou={(base) => cvs && setCvs({ ...cvs, curriculo_base: base })} onAviso={onAviso} onErro={falhou} />
        <p className={DICA}>O currículo base gerado pela IA é uma versão nova, voltada para os cargos que procura.</p>
        <SecaoCurriculos vagaId={null} onGerar={() => setGerarBase(true)} />
      </>
    )
    pe = botaoIr(e.etapa && e.etapa !== "concluido" ? e.etapa : "concluido", "Voltar ao perfil")
  } else if (tela === "basicas") {
    corpo = <InformacoesBasicas so={so} onAviso={onAviso} />
    pe = botaoIr(e.etapa && e.etapa !== "concluido" ? e.etapa : "concluido", "Voltar ao perfil")
  } else if (tela === "analises") {
    corpo = (
      <Analises
        so={so}
        onAviso={onAviso}
        onErro={falhou}
        onAbrirFiltrosInt={onAbrirFiltrosInt}
        onCompletarPerfil={() => ir("anamnese")}
        onVerCurriculos={() => setTela("curriculos")}
      />
    )
    pe = (
      <button type="button" onClick={onClose} className={BTN_PRI}>
        Fechar
      </button>
    )
  }

  const mostraRecomecar = e && tela !== "concluido" && !FORA_DOS_PASSOS.includes(tela)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-perfil"
        className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[94vh] overflow-hidden"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h3 id="titulo-perfil" className="flex items-center gap-2 font-bold text-base sm:text-lg text-slate-900 dark:text-white">
              <User className="w-5 h-5 text-indigo-500" />
              {e?.existe_perfil ? "Meu perfil" : "Primeiros passos"}
            </h3>
            <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
              <X className="w-5 h-5" />
            </button>
          </div>
          {e && (
            <nav className="flex gap-1 overflow-x-auto pb-1" aria-label="Passos">
              {PASSOS.map((p) => (
                <button
                  key={p.k}
                  type="button"
                  onClick={() => ir(p.k)}
                  aria-current={tela === p.k ? "step" : undefined}
                  className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                    tela === p.k
                      ? "bg-indigo-600 text-white"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {p.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => {
                  setErro("")
                  setTela("basicas")
                }}
                aria-current={tela === "basicas" ? "step" : undefined}
                className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                  tela === "basicas"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                Informações básicas
              </button>
              {e.existe_perfil && (
                <button
                  type="button"
                  onClick={() => {
                    setErro("")
                    setTela("curriculos")
                  }}
                  aria-current={tela === "curriculos" ? "step" : undefined}
                  className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                    tela === "curriculos"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  Currículo base
                </button>
              )}
              {e.existe_perfil && (
                <button
                  type="button"
                  onClick={() => {
                    setErro("")
                    setTela("analises")
                  }}
                  aria-current={tela === "analises" ? "step" : undefined}
                  className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                    tela === "analises"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <Sparkles className="w-3 h-3" /> Análises
                </button>
              )}
            </nav>
          )}
        </div>

        <div ref={corpoRef} className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          {corpo}
          {e && so && (
            <p className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs">
              Só dá para enviar arquivos e gravar no computador onde a ferramenta roda.
            </p>
          )}
          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{erro}</span>
            </p>
          )}
        </div>

        {(pe || mostraRecomecar) && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 flex-wrap">
            <div>
              {mostraRecomecar && (
                <button type="button" disabled={so} onClick={() => recomecar(true)} className={`${BTN} text-rose-700 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-950/40`}>
                  Recomeçar
                </button>
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">{pe}</div>
          </div>
        )}
      </div>
      {gerarBase && <GerarCurriculo vagaId={null} onClose={() => setGerarBase(false)} onAbrirPerfil={() => setGerarBase(false)} />}
    </div>
  )
}

// ---------- partes ----------

function PerguntaAtual({
  p,
  n,
  total,
  valor,
  so,
  onVoltar,
  onResponder,
}: {
  p: Pergunta
  n: number
  total: number
  valor: any
  so: boolean
  onVoltar: () => void
  onResponder: (valor: unknown) => void
}) {
  const textoLongo = /^(conquista|medida):/.test(p.id)
  const [texto, setTexto] = useState<string>(
    p.tipo === "lista" ? (Array.isArray(valor) ? valor.join("\n") : "") : p.tipo === "texto" ? valor || "" : "",
  )
  const [marcados, setMarcados] = useState<string[]>(
    p.tipo === "multi" ? (Array.isArray(valor) ? valor : []) : p.tipo === "sim_nao" ? (valor === true ? ["sim"] : valor === false ? ["nao"] : []) : valor ? [valor] : [],
  )
  const opcoes = p.tipo === "sim_nao" ? [{ valor: "sim", rotulo: "Sim" }, { valor: "nao", rotulo: "Não" }] : p.opcoes || []
  // idiomas com nível (spec 036): linhas de idioma e nível; sem os campos novos, continua a caixa de texto
  const ehIdiomas = Boolean(p.idiomas?.length && p.niveis?.length)
  const [linhas, setLinhas] = useState<LinhaIdioma[]>(() => (p.linhas?.length ? p.linhas : [{ ...LINHA_VAZIA }]))
  const [aviso, setAviso] = useState("")

  const proxima = () => {
    if (!ehIdiomas) return onResponder(ler())
    const r = respostaIdiomas(linhas, p.niveis || [])
    if (r.erro) return setAviso(r.erro)
    onResponder(r.valor ?? null)
  }

  const ler = (): unknown => {
    if (p.tipo === "texto") return texto.trim() || null
    if (p.tipo === "lista") {
      const l = texto.split(/\r?\n/).map((x) => x.trim()).filter(Boolean)
      return l.length ? l : null
    }
    if (p.tipo === "multi") return marcados.length ? marcados : null
    if (!marcados.length) return null
    return p.tipo === "sim_nao" ? marcados[0] === "sim" : marcados[0]
  }

  return (
    <>
      <p className={DICA}>
        Pergunta {n + 1} de {total}
      </p>
      <div className="space-y-2">
        <label htmlFor={ehIdiomas ? undefined : "pf-resp"} id="pf-perg" className="block font-semibold text-sm text-slate-900 dark:text-white">
          {p.texto}
        </label>
        {ehIdiomas && (
          <div role="group" aria-labelledby="pf-perg" className="space-y-2">
            <PerguntaIdiomas
              idiomas={p.idiomas || []}
              niveis={p.niveis || []}
              linhas={linhas}
              onMudar={(l) => {
                setLinhas(l)
                setAviso("")
              }}
            />
            {aviso && (
              <p role="alert" className="text-xs text-rose-700 dark:text-rose-300">
                {aviso}
              </p>
            )}
          </div>
        )}
        {p.tipo === "texto" &&
          (textoLongo ? (
            <textarea id="pf-resp" rows={4} maxLength={2000} value={texto} onChange={(ev) => setTexto(ev.target.value)} className={CAMPO} />
          ) : (
            <input id="pf-resp" maxLength={300} autoComplete="off" value={texto} onChange={(ev) => setTexto(ev.target.value)} className={CAMPO} />
          ))}
        {p.tipo === "lista" && !ehIdiomas && (
          <>
            <textarea id="pf-resp" rows={5} maxLength={2000} value={texto} onChange={(ev) => setTexto(ev.target.value)} className={CAMPO} />
            <p className={DICA}>Um por linha.</p>
          </>
        )}
        {(p.tipo === "multi" || p.tipo === "opcoes" || p.tipo === "sim_nao") && (
          <div role="group" aria-labelledby="pf-perg" className="space-y-1.5">
            {opcoes.map((o) => (
              <label key={o.valor} className="flex items-center gap-2 cursor-pointer">
                <input
                  type={p.tipo === "multi" ? "checkbox" : "radio"}
                  name="pf-resp"
                  checked={marcados.includes(o.valor)}
                  onChange={() =>
                    setMarcados((m) =>
                      p.tipo === "multi" ? (m.includes(o.valor) ? m.filter((x) => x !== o.valor) : [...m, o.valor]) : [o.valor],
                    )
                  }
                />
                {o.rotulo}
              </label>
            ))}
          </div>
        )}
        {p.id.startsWith("medida:") && (
          <p className={DICA}>Escreva o número só se tiver certeza. Sem número, a conquista entra sem medida.</p>
        )}
      </div>
      <div className="flex justify-end gap-2 pt-3 flex-wrap">
        <button type="button" onClick={onVoltar} className={BTN_SEC}>
          Voltar
        </button>
        <button type="button" onClick={() => onResponder(null)} className={BTN_SEC}>
          Pular
        </button>
        <button type="button" onClick={proxima} className={BTN_PRI}>
          {n + 1 >= total ? "Concluir" : "Próxima"}
        </button>
      </div>
      {so && <p className={DICA}>As respostas não são gravadas neste aparelho.</p>}
    </>
  )
}

function DoCurriculo({
  dc,
  so,
  onVoltar,
  onErro,
  onPronto,
}: {
  dc: PropostaDoCurriculo
  so: boolean
  onVoltar: () => void
  onErro: (err: unknown) => void
  onPronto: (manter: boolean) => void
}) {
  const ed = dc.edicao || ({} as PropostaDoCurriculo["edicao"])
  const m = dc.filtros?.modelos || ({} as Record<string, boolean>)
  const idioma = dc.idioma === "en" ? "inglês" : "português"
  let cargosIni = (ed.cargos || []).join(", ")
  const cargosEnIni = (ed.cargos_en || []).join(", ")
  if (!cargosIni && !cargosEnIni && dc.filtros) cargosIni = dc.filtros.termos.map((t) => t.replace(/"/g, "")).join(", ")
  const [cargos, setCargos] = useState(cargosIni)
  const [cargosEn, setCargosEn] = useState(cargosEnIni)
  const [cidade, setCidade] = useState(ed.cidade || "")
  const [estado, setEstado] = useState(ed.estado || "")
  const [modelos, setModelos] = useState<string[]>(["remoto", "hibrido", "presencial"].filter((k) => (m as Record<string, boolean>)[k]))
  const [manter, setManter] = useState(dc.existe_perfil)
  const [texto, setTexto] = useState(dc.perfil || "")
  const [marcarBase, setMarcarBase] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [aviso, setAviso] = useState("")
  const lista = (v: string) => v.split(",").map((x) => x.trim()).filter(Boolean)

  const confirmar = async () => {
    const edicao = { cargos: lista(cargos), cargos_en: lista(cargosEn), cidade: cidade.trim(), estado: estado.trim(), modelos }
    if (!manter && !edicao.cargos.length && !edicao.cargos_en.length) {
      setAviso("Escreva pelo menos um cargo.")
      return
    }
    setEnviando(true)
    try {
      await perfilApi.confirmarCurriculo({
        arquivo: dc.arquivo,
        idioma: dc.idioma,
        manter_perfil: manter,
        marcar_base: marcarBase,
        perfil: manter ? "" : texto,
        ...(manter ? {} : { edicao }),
      })
      onPronto(manter)
    } catch (err) {
      onErro(err)
      setEnviando(false)
    }
  }

  return (
    <>
      <p>
        Do seu currículo <b>{dc.nome}</b> ({idioma}), direto para as vagas. Confira e ajuste; nada é gravado até você
        confirmar.
      </p>
      {dc.avisos.length > 0 && (
        <ul className="list-disc pl-5 space-y-1">
          {dc.avisos.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
      <section className={SEC}>
        <h4 className={H}>Filtros da busca</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <label htmlFor="dc-cargos" className={ROTULO}>Cargos (separados por vírgula)</label>
            <input id="dc-cargos" value={cargos} disabled={so} onChange={(ev) => setCargos(ev.target.value)} className={CAMPO} />
            <span className={DICA}>{dc.dados?.origem === "ia" ? "Lidos pela IA no currículo" : "Do objetivo ou do cargo mais recente"}</span>
          </div>
          <div>
            <label htmlFor="dc-en" className={ROTULO}>Cargos em inglês</label>
            <input id="dc-en" value={cargosEn} disabled={so} onChange={(ev) => setCargosEn(ev.target.value)} className={CAMPO} />
            <span className={DICA}>Opcional; usados também na busca no exterior</span>
          </div>
          <div>
            <label htmlFor="dc-cidade" className={ROTULO}>Cidade</label>
            <input id="dc-cidade" value={cidade} disabled={so} onChange={(ev) => setCidade(ev.target.value)} className={CAMPO} />
            <span className={DICA}>Para vagas híbridas e presenciais</span>
          </div>
          <div>
            <label htmlFor="dc-uf" className={ROTULO}>Estado</label>
            <input id="dc-uf" value={estado} disabled={so} onChange={(ev) => setEstado(ev.target.value)} className={CAMPO} />
          </div>
        </div>
        <div className="flex gap-4 flex-wrap">
          {["remoto", "hibrido", "presencial"].map((k) => (
            <label key={k} className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                disabled={so}
                checked={modelos.includes(k)}
                onChange={() => setModelos((l) => (l.includes(k) ? l.filter((x) => x !== k) : [...l, k]))}
              />
              {MODOS[k]}
            </label>
          ))}
        </div>
        <p className={DICA}>
          Idiomas, busca no exterior e o resto dos filtros ficam como estão.
          {dc.existe_perfil ? " Se você mantiver o seu perfil, estes filtros também ficam como estão: só o currículo é marcado." : ""}
        </p>
      </section>
      <section className={SEC}>
        <h4 className={H}>Perfil</h4>
        {dc.existe_perfil ? (
          <>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="dc-perfil" disabled={so} checked={manter} onChange={() => setManter(true)} /> Manter o meu perfil e só marcar este como o meu currículo
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="dc-perfil" disabled={so} checked={!manter} onChange={() => setManter(false)} /> Trocar o perfil pelo texto deste currículo (o atual fica guardado)
            </label>
          </>
        ) : (
          <p>O seu perfil será o texto do currículo, sem perguntas. Depois, em Meu perfil, dá para completar com a anamnese.</p>
        )}
        {dc.perfil && (
          <details open={!dc.existe_perfil}>
            <summary className={`cursor-pointer ${DICA}`}>Ver e editar o perfil</summary>
            <textarea value={texto} disabled={so} onChange={(ev) => setTexto(ev.target.value)} className={`${CAMPO} min-h-[220px] font-mono text-xs mt-1`} />
          </details>
        )}
      </section>
      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" disabled={so} checked={marcarBase} onChange={(ev) => setMarcarBase(ev.target.checked)} /> Marcar como o meu currículo em {idioma} (aparece nas vagas, no item Currículo)
      </label>
      {aviso && <p className="text-rose-600 dark:text-rose-400 text-xs">{aviso}</p>}
      <div className="flex justify-end gap-2 pt-2 flex-wrap">
        <button type="button" onClick={onVoltar} className={BTN_SEC}>
          Voltar
        </button>
        <button type="button" disabled={so || enviando} onClick={confirmar} className={BTN_PRI}>
          {enviando ? "Gravando…" : "Confirmar e ir para as vagas"}
        </button>
      </div>
    </>
  )
}

function SeuCurriculo({
  cvs,
  so,
  onMudou,
  onAviso,
  onErro,
}: {
  cvs: CurriculosDaPasta | null
  so: boolean
  onMudou: (base: CurriculosDaPasta["curriculo_base"]) => void
  onAviso: (m: string) => void
  onErro: (err: unknown) => void
}) {
  if (!cvs) {
    return (
      <section className={SEC}>
        <h4 className={H}>Seu currículo</h4>
        <p className={DICA}>{so ? "Só no computador onde a ferramenta roda." : "Carregando…"}</p>
      </section>
    )
  }
  const lista = cvs.curriculos || []
  const sel = (idioma: "pt" | "en", rotulo: string) => (
    <div>
      <label htmlFor={`seu-${idioma}`} className={ROTULO}>{rotulo}</label>
      <select
        id={`seu-${idioma}`}
        value={cvs.curriculo_base[idioma] || ""}
        disabled={so}
        onChange={async (ev) => {
          try {
            const j = await perfilApi.marcarCurriculoBase(idioma, ev.target.value || null)
            onMudou(j.curriculo_base)
            onAviso(ev.target.value ? "Seu currículo marcado." : "Desmarcado.")
          } catch (err) {
            onErro(err)
          }
        }}
        className={CAMPO}
      >
        <option value="">Nenhum</option>
        {lista.map((c) => (
          <option key={c.arquivo} value={c.arquivo}>{c.arquivo}</option>
        ))}
      </select>
    </div>
  )
  return (
    <section className={SEC}>
      <h4 className={H}>Seu currículo</h4>
      <p className={DICA}>
        O currículo que você já tem, para mostrar em cada vaga (item Currículo do checklist). Fica na pasta anexos, neste
        computador; a ferramenta só gera outro se você pedir.
      </p>
      {lista.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {sel("pt", "Em português")}
          {sel("en", "Em inglês")}
        </div>
      ) : (
        <p className={DICA}>Nenhum PDF ou Word na pasta anexos. Envie o arquivo em Materiais.</p>
      )}
    </section>
  )
}
