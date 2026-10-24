/**
 * Faixa salarial da vaga (dash/API.md §3.1b; spec 028): o que a vaga informa, as vagas parecidas do banco que
 * informam salário (cada número com a vaga de origem), as faixas que a pessoa anotou e links de pesquisa (Glassdoor,
 * Indeed) que abrem no navegador dela. A ferramenta não lê essas páginas nem estima valores.
 */
import React, { useEffect, useState } from "react"
import { Loader2, Banknote, ExternalLink, Trash2 } from "lucide-react"
import * as vagasApi from "../../services/api/vagas"
import type { FaixaSalarial as Faixa } from "../../services/api/vagas"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { linkSeguro } from "../../utils/formatters"
import { BTN_MINI } from "../curriculo/Curriculos"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
const SIMBOLO: Record<string, string> = { BRL: "R$", USD: "US$", EUR: "€", GBP: "£" }
const PERIODO: Record<string, string> = { mes: "por mês", ano: "por ano", hora: "por hora", dia: "por dia", semana: "por semana" }

function dinheiro(v: number, moeda: string | null): string {
  const s = moeda ? SIMBOLO[moeda] || moeda : ""
  return `${s} ${Math.round(v).toLocaleString("pt-BR")}`.trim()
}

export default function FaixaSalarial({ vagaId, semTitulo = false }: { vagaId: string; semTitulo?: boolean }) {
  const { podeGravar, servidor } = useFerramenta()
  const [f, setF] = useState<Faixa | null>(null)
  const [erro, setErro] = useState("")
  const [texto, setTexto] = useState("")
  const [fonte, setFonte] = useState("Glassdoor")
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    if (servidor !== "no_ar") return
    vagasApi
      .salario(vagaId)
      .then(setF)
      .catch((e) => setErro(mensagemDeErro(e)))
  }, [vagaId, servidor])

  const acao = async (fn: () => Promise<Faixa>) => {
    setOcupado(true)
    setErro("")
    try {
      setF(await fn())
    } catch (e) {
      setErro(mensagemDeErro(e))
    } finally {
      setOcupado(false)
    }
  }

  const titulo = !semTitulo && (
    <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
      <Banknote className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> Faixa salarial
    </h4>
  )
  if (!f)
    return (
      <section className="space-y-2">
        {titulo}
        {erro ? <p className="text-rose-600 text-xs">{erro}</p> : <p className={`flex items-center gap-2 ${DICA}`}><Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando…</p>}
      </section>
    )

  const v = f.vaga.valor
  const r = f.resumo
  return (
    <section className="space-y-3 text-xs">
      {titulo}
      <p>
        <span className="font-semibold text-slate-500">A vaga informa: </span>
        {f.vaga.salario ? (
          <>
            {f.vaga.salario}
            {v && v.periodo !== "mes" && <span className={DICA}> (≈ {dinheiro(v.mensal_min, v.moeda)}{v.mensal_max !== v.mensal_min ? ` a ${dinheiro(v.mensal_max, v.moeda)}` : ""} por mês)</span>}
          </>
        ) : (
          <span className={DICA}>não informa</span>
        )}
      </p>

      <div className="space-y-1">
        <span className="font-semibold text-slate-500">Vagas parecidas no seu banco</span>
        {r ? (
          <>
            <p>
              <b>
                {dinheiro(r.minimo, r.moeda)} a {dinheiro(r.maximo, r.moeda)} por mês
              </b>
              {r.mediana != null && <> · mediana {dinheiro(r.mediana, r.moeda)}</>}{" "}
              <span className={DICA}>({r.n} vaga(s); {f.conversao})</span>
            </p>
            <ul className="space-y-0.5">
              {f.parecidas.slice(0, 8).map((p) => {
                const link = linkSeguro(p.url)
                return (
                  <li key={p.id} className={DICA}>
                    {p.titulo} — {p.empresa} ({p.plataforma}): <span className="text-slate-700 dark:text-slate-300">{p.salario}</span>
                    {p.periodo !== "mes" && ` ${PERIODO[p.periodo]}`}
                    {link && (
                      <>
                        {" · "}
                        <a href={link} target="_blank" rel="noopener noreferrer" className="underline">
                          ver vaga
                        </a>
                      </>
                    )}
                  </li>
                )
              })}
            </ul>
          </>
        ) : (
          <p className={DICA}>Nenhuma vaga parecida do seu banco informa salário (no Brasil, poucas vagas publicam). Pesquise nos links abaixo.</p>
        )}
      </div>

      <div className="space-y-1">
        <span className="font-semibold text-slate-500">Pesquisar</span>
        <div className="flex flex-wrap gap-2">
          {f.links.map((l) => (
            <a key={l.url} href={l.url} target="_blank" rel="noopener noreferrer" className={`${BTN_MINI} inline-flex items-center gap-1`} title="Abre no seu navegador; a ferramenta não lê essa página">
              {l.rotulo} <ExternalLink className="w-3 h-3" />
            </a>
          ))}
        </div>
        <p className={DICA}>Os links abrem no seu navegador. O Glassdoor pode pedir login para mostrar as faixas.</p>
      </div>

      <div className="space-y-1">
        <span className="font-semibold text-slate-500">O que você viu</span>
        {f.pesquisas.length > 0 && (
          <ul className="space-y-0.5">
            {f.pesquisas.map((a, i) => (
              <li key={i} className="flex items-center gap-2">
                <span>
                  {a.texto} <span className={DICA}>— {a.fonte}, {a.em.split("-").reverse().join("/")}</span>
                </span>
                <button
                  type="button"
                  className="p-1 rounded-md text-slate-400 hover:text-rose-600 disabled:opacity-50"
                  disabled={!podeGravar || ocupado}
                  aria-label={`Apagar a anotação de ${a.fonte}`}
                  onClick={() => acao(() => vagasApi.apagarSalario(vagaId, i))}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
          </ul>
        )}
        <form
          className="flex flex-wrap gap-2 items-center"
          onSubmit={(e) => {
            e.preventDefault()
            acao(async () => {
              const j = await vagasApi.anotarSalario(vagaId, texto, fonte)
              setTexto("")
              return j
            })
          }}
        >
          <input className={`${CAMPO} flex-1 min-w-[180px]`} placeholder="ex.: R$ 6 mil a R$ 9 mil por mês" value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={300} />
          <input className={`${CAMPO} w-32`} placeholder="fonte" value={fonte} onChange={(e) => setFonte(e.target.value)} maxLength={120} aria-label="Fonte" />
          <button type="submit" className={BTN_MINI} disabled={!podeGravar || ocupado || !texto.trim() || !fonte.trim()}>
            Guardar
          </button>
        </form>
        <p className={DICA}>Fica guardado nesta vaga e aparece na preparação de entrevista, na parte de salário.</p>
      </div>
      {erro && <p role="alert" className="text-rose-600 dark:text-rose-400">{erro}</p>}
    </section>
  )
}
