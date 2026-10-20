/**
 * Currículos (dash/API.md §3.8): o diálogo Gerar currículo (técnicas, opções, qual IA vai rodar e o custo) e a
 * seção com o andamento e os currículos gerados para uma vaga ou o currículo base, com a conferência sem IA.
 */
import React, { useEffect, useState } from "react"
import { X, FileText, Loader2, AlertTriangle } from "lucide-react"
import * as curriculoApi from "../../services/api/curriculo"
import type { Catalogo, MetaCurriculo } from "../../services/api/curriculo"
import { mensagemDeErro, urlArquivo } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { useGeracao, ehDoAlvo } from "../../contexto/Geracao"
import { diaMes, horaDe } from "../../utils/formatters"

const FORMATOS: Record<string, string> = { br: "Brasil", us: "Estados Unidos", eu: "Europa" }
const ESTILOS: Record<string, string> = { padrao: "padrão", compacto: "compacto", executivo: "executivo" }
const VEREDITO: Record<string, string> = { ok: "Conferido: ok", conferir: "Conferir", bloquear: "Não pronto" }
const TECNICAS: Record<string, string> = {
  ats: "ATS",
  foco: "foco",
  xyz: "XYZ",
  resultado_primeiro: "resultado primeiro",
  competencias_primeiro: "competências primeiro",
}
const COR_VEREDITO: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  conferir: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  bloquear: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
}
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
export const BTN_MINI =
  "inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 disabled:opacity-50"

export function LinkArquivo({ arquivo, rotulo }: { arquivo?: string | null; rotulo: string }) {
  if (!arquivo) return null
  return (
    <a href={urlArquivo("/arquivos/curriculos/" + encodeURIComponent(arquivo))} target="_blank" rel="noopener noreferrer" className={BTN_MINI}>
      {rotulo}
    </a>
  )
}

// ---------- diálogo Gerar currículo ----------

export function GerarCurriculo({
  vagaId,
  onClose,
  onAbrirPerfil,
}: {
  vagaId: string | null
  onClose: () => void
  onAbrirPerfil: () => void
}) {
  const { abrirPainelIA, tratarErro, podeGravar } = useFerramenta()
  const { comecou } = useGeracao()
  const [c, setC] = useState<Catalogo | null>(null)
  const [escolha, setEscolha] = useState<Record<string, unknown>>({})
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    curriculoApi
      .catalogo(vagaId)
      .then((j) => {
        setC(j)
        const s = j.sugestao || {}
        const ini: Record<string, unknown> = {}
        Object.keys(j.tecnicas).forEach((k) => (ini[k] = Boolean(s[k])))
        Object.entries(j.escolhas).forEach(([k, es]) => (ini[k] = s[k] ?? es.padrao))
        setEscolha(ini)
      })
      .catch((e) => setErro(mensagemDeErro(e, "Não deu para abrir o diálogo do currículo.")))
  }, [vagaId])

  const gerar = async () => {
    setEnviando(true)
    setErro("")
    try {
      const tec: Record<string, unknown> = { ...escolha }
      if ("paginas" in tec) tec.paginas = Number(tec.paginas)
      comecou(await curriculoApi.gerar(vagaId, tec))
      onClose()
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para gerar."))
      setEnviando(false)
    }
  }

  const ia = c?.ia
  let corpo: React.ReactNode
  let pe: React.ReactNode
  if (!c) {
    corpo = erro ? null : (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
      </p>
    )
  } else if (!ia?.ligada) {
    corpo = (
      <p>
        Escrever o currículo pela página precisa de uma IA. Escolha uma no painel <b>IA</b> (a assinatura do Claude Code
        serve), ou peça o currículo no chat do seu assistente ("monta meu currículo").
      </p>
    )
    pe = (
      <button type="button" onClick={() => { onClose(); abrirPainelIA() }} className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500">
        Escolher a IA
      </button>
    )
  } else if (!c.perfil_ok) {
    corpo = <p>O currículo sai só dos fatos do seu perfil, e ele ainda não existe. Monte o perfil primeiro.</p>
    pe = (
      <button type="button" onClick={() => { onClose(); onAbrirPerfil() }} className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500">
        Montar meu perfil
      </button>
    )
  } else {
    corpo = (
      <>
        <section className="space-y-2">
          <h4 className="font-bold text-sm text-slate-900 dark:text-white">Técnicas</h4>
          {Object.entries(c.tecnicas).map(([k, t]) => (
            <label key={k} className="flex items-start gap-2 cursor-pointer">
              <input type="checkbox" className="mt-0.5" checked={Boolean(escolha[k])} onChange={(ev) => setEscolha((x) => ({ ...x, [k]: ev.target.checked }))} />
              <span>
                <b>{t.nome}</b> <span className={DICA}>{t.explicacao}</span>
              </span>
            </label>
          ))}
        </section>
        {Object.entries(c.escolhas).map(([k, es]) => (
          <section key={k} className="space-y-1.5">
            <h4 className="font-bold text-sm text-slate-900 dark:text-white">{es.nome}</h4>
            <div className="flex flex-wrap gap-3">
              {Object.entries(es.opcoes).map(([o, rotulo]) => (
                <label key={o} className="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" name={`cv-${k}`} checked={String(escolha[k]) === o} onChange={() => setEscolha((x) => ({ ...x, [k]: o }))} />
                  {rotulo}
                </label>
              ))}
            </div>
          </section>
        ))}
        {c.sugestao?.motivo && <p className={DICA}>Sugestão marcada: {c.sugestao.motivo}.</p>}
        <ul className="list-disc pl-5 space-y-1">
          <li>
            Quem escreve: {ia.nome}
            {ia.modelo ? ` · ${ia.modelo}` : ""}, só com os fatos do seu perfil; depois a ferramenta confere sem IA.
          </li>
          {ia.cobranca === "uso" && <li>Cobrado por uso na sua conta do provedor (uma chamada por currículo).</li>}
          <li>Nada é enviado antes de você confirmar. Os arquivos ficam na pasta curriculos, sem apagar versões anteriores.</li>
        </ul>
        {c.pode_alterar === false && <p className="text-rose-600 text-xs">Só dá para gerar no computador onde a ferramenta roda.</p>}
      </>
    )
    pe = (
      <button
        type="button"
        disabled={enviando || c.pode_alterar === false || !podeGravar}
        onClick={gerar}
        className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
      >
        {enviando && <Loader2 className="w-4 h-4 animate-spin" />}
        Gerar
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-cv"
        className="relative w-full max-w-xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <h3 id="titulo-cv" className="flex items-center gap-2 font-bold text-base text-slate-900 dark:text-white">
            <FileText className="w-5 h-5 text-indigo-500" />
            {vagaId ? "Gerar currículo para esta vaga" : "Gerar o currículo base"}
          </h3>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-5 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
          {corpo}
          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {erro}
            </p>
          )}
        </div>
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
            {c?.ia?.ligada && c.perfil_ok ? "Cancelar" : "Fechar"}
          </button>
          {pe}
        </div>
      </div>
    </div>
  )
}

// ---------- seção com o andamento e a lista ----------

function ItemCurriculo({ m }: { m: MetaCurriculo }) {
  const c = m.conferencia || {}
  const t = m.tecnicas || {}
  const d = m.disponivel || {}
  const nomes = Object.keys(t).filter((k) => t[k] === true).map((k) => TECNICAS[k] || k)
  const pontos = [...(c.fatos || []), ...(c.ats || [])]
  const bloqueios = pontos.filter((p) => p.nivel === "bloquear")
  return (
    <li className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5">
      <div className="flex items-center gap-2 flex-wrap">
        <b>
          {diaMes(m.criado_em)} {horaDe(m.criado_em)}
        </b>
        {c.veredito && (
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${COR_VEREDITO[c.veredito] || ""}`}>
            {VEREDITO[c.veredito] || c.veredito}
          </span>
        )}
        <span className={DICA}>
          {FORMATOS[String(t.formato)] || String(t.formato || "")} · {ESTILOS[String(t.estilo)] || String(t.estilo || "")} ·{" "}
          {m.paginas ? `${m.paginas} página(s)${m.acima_do_limite ? ` (acima do limite de ${t.paginas})` : ""}` : "páginas não medidas"}
        </span>
        <span className="flex gap-1.5 ml-auto">
          {d.pdf ? <LinkArquivo arquivo={m.arquivos.pdf} rotulo="PDF" /> : <span className={DICA}>PDF indisponível</span>}
          {d.docx ? <LinkArquivo arquivo={m.arquivos.docx} rotulo=".docx" /> : <span className={DICA}>.docx indisponível</span>}
        </span>
      </div>
      {nomes.length > 0 && <p className={DICA}>Técnicas: {nomes.join(", ")}</p>}
      {bloqueios.length > 0 && (
        <p className="text-xs text-rose-700 dark:text-rose-300">
          Não envie este currículo ainda: {bloqueios.map((p) => p.mensagem + (p.valor ? ` (${p.valor})` : "")).join("; ")}. Confirme o
          fato no perfil (Meu perfil) ou gere de novo.
        </p>
      )}
      {(m.sugestoes_corte || []).length > 0 && <p className={DICA}>Para caber: {(m.sugestoes_corte || []).join("; ")}.</p>}
      {(pontos.length > 0 || (c.requisitos || []).length > 0) && (
        <details className="text-xs">
          <summary className="cursor-pointer font-semibold">Ver conferência</summary>
          {pontos.length ? (
            <ul className="list-disc pl-5 mt-1 space-y-0.5">
              {pontos.map((p, i) => (
                <li key={i}>
                  <b>{p.nivel}</b> {p.mensagem}
                  {p.valor ? `: ${p.valor}` : p.trecho ? `: ${p.trecho}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1">Fatos e ATS sem pontos.</p>
          )}
          {(c.requisitos || []).length > 0 && (
            <>
              <p className="mt-1 font-semibold">Requisitos da vaga</p>
              <ul className="list-disc pl-5 space-y-0.5">
                {(c.requisitos || []).map((r, i) => (
                  <li key={i}>
                    [{r.situacao}] {r.texto}
                  </li>
                ))}
              </ul>
            </>
          )}
          {c.cobertura && c.cobertura.total > 0 && (
            <p className="mt-1">
              Palavras-chave da vaga no currículo: {c.cobertura.achadas} de {c.cobertura.total}
              {c.cobertura.faltando.length ? ` (faltando: ${c.cobertura.faltando.join(", ")})` : ""}
            </p>
          )}
        </details>
      )}
    </li>
  )
}

/** Andamento e lista de currículos de uma vaga (vagaId) ou do currículo base (null). */
export function SecaoCurriculos({ vagaId, onGerar }: { vagaId: string | null; onGerar: () => void }) {
  const { servidor } = useFerramenta()
  const { estado, ativa, versao, tentar } = useGeracao()
  const [lista, setLista] = useState<MetaCurriculo[] | null>(null)

  useEffect(() => {
    curriculoApi
      .lista(vagaId)
      .then((j) => setLista(j.curriculos || []))
      .catch(() => setLista((l) => l || []))
  }, [vagaId, versao])

  const meu = ehDoAlvo(estado, vagaId, ["curriculo"])
  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h4 className="font-bold text-sm text-slate-900 dark:text-white">{vagaId ? "Currículos para esta vaga" : "Currículo base"}</h4>
        <button type="button" disabled={ativa || servidor !== "no_ar"} onClick={onGerar} className={BTN_MINI}>
          {vagaId ? "Gerar currículo" : "Gerar currículo base"}
        </button>
      </div>
      {meu && ativa && (
        <p className="flex items-center gap-2 text-xs text-indigo-700 dark:text-indigo-300">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          {estado?.etapa_texto || "Gerando…"} Pode levar alguns minutos; dá para fechar e voltar.
        </p>
      )}
      {!meu && ativa && <p className={DICA}>Há outro documento sendo gerado; espere ele terminar.</p>}
      {meu && estado?.situacao === "falha" && (
        <p className="text-xs text-rose-700 dark:text-rose-300">
          O currículo não saiu: {estado.mensagem}{" "}
          {estado.pode_tentar && (
            <button type="button" onClick={tentar} className={BTN_MINI}>
              Tentar de novo
            </button>
          )}
        </p>
      )}
      {!lista ? (
        <p className={DICA}>Carregando…</p>
      ) : !lista.length ? (
        <p className={DICA}>Nenhum currículo gerado pela página ainda.</p>
      ) : (
        <ul className="space-y-2">
          {lista.map((m) => (
            <ItemCurriculo key={m.nome} m={m} />
          ))}
        </ul>
      )}
    </section>
  )
}
