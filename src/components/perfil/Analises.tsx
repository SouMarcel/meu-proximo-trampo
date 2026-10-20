/**
 * Análises do perfil (dash/API.md §3.7), sempre a pedido: lacunas das vagas (sem IA), plano de estudo e
 * cargos-alvo (com IA, aviso de custo) e prontidão internacional. Cargos só vão para os filtros com confirmação.
 */
import React, { useCallback, useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import * as analisesApi from "../../services/api/analises"
import type { Analises as TAnalises, Cargos, Lacunas } from "../../services/api/analises"
import { useFerramenta, textoCustoIA } from "../../contexto/Ferramenta"
import { diaMes, horaDe } from "../../utils/formatters"

interface Props {
  so: boolean
  onAviso: (m: string, t?: "info" | "erro") => void
  onErro: (err: unknown) => void
  onAbrirFiltrosInt: () => void
  onCompletarPerfil: () => void
}

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const BTN_MINI =
  "px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"
const NIVEL: Record<string, string> = { critica: "Crítica", alta: "Alta", media: "Média" }
const SIT: Record<string, string> = { pronto: "Pronto", falta: "Falta", nao_informado: "Não informado" }
const TIPO: Record<string, string> = { lateral: "Lateral", degrau: "Degrau", vizinho: "Vizinho" }
const COR_SIT: Record<string, string> = {
  pronto: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  falta: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
  nao_informado: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
}

function Data({ x }: { x?: { data?: string } | null }) {
  return x?.data ? <p className={DICA}>Análise de {diaMes(x.data)} às {horaDe(x.data)}</p> : null
}

export default function Analises({ so, onAviso, onErro, onAbrirFiltrosInt, onCompletarPerfil }: Props) {
  const { ia } = useFerramenta()
  const [d, setD] = useState<TAnalises | null>(null)
  const [visao, setVisao] = useState<"todas" | "seguidas">("todas")
  const [lac, setLac] = useState<Lacunas | null>(null)
  const [cargos, setCargos] = useState<Cargos | null>(null)
  const [marcados, setMarcados] = useState<Record<number, boolean>>({})
  const [proposta, setProposta] = useState<Awaited<ReturnType<typeof analisesApi.cargosParaFiltros>> | null>(null)
  const [ocupado, setOcupado] = useState("")

  const carregar = useCallback(async () => {
    try {
      const j = await analisesApi.ler()
      setD(j)
      setLac((l) => l || j.salvas.lacunas || null)
      setCargos((c) => c || j.salvas.cargos || null)
    } catch (err) {
      onErro(err)
    }
  }, [onErro])

  useEffect(() => {
    carregar()
  }, [carregar])

  const rodar = async (chave: string, fn: () => Promise<void>) => {
    setOcupado(chave)
    try {
      await fn()
    } catch (err) {
      onErro(err)
    } finally {
      setOcupado("")
    }
  }

  if (!d) {
    return (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando as análises…
      </p>
    )
  }

  const escolhidos = () =>
    (cargos?.itens || []).filter((_, n) => marcados[n]).map((c) => ({ titulo: c.titulo, titulo_en: c.titulo_en }))
  const plano = d.salvas.plano
  const bloq = so || !d.pode_alterar
  const custo = ia?.cobranca === "uso" ? ` ${textoCustoIA(ia)}` : ""

  return (
    <>
      <p>Análises do seu perfil, sempre a seu pedido. Ficam salvas com a data neste computador.</p>

      <section className={SEC}>
        <h4 className={H}>Lacunas das vagas</h4>
        <p className={DICA}>
          O que as vagas que você analisou pedem e o seu perfil não mostra. Vagas com aderência maior e as que você seguiu
          pesam mais.
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          {(
            [
              ["todas", "Todas as vagas"],
              ["seguidas", "Vagas que você seguiu"],
            ] as const
          ).map(([k, r]) => (
            <button
              key={k}
              type="button"
              aria-pressed={visao === k}
              onClick={() => {
                setVisao(k)
                setLac(null)
              }}
              className={`px-3 py-1 rounded-full text-xs font-medium border ${
                visao === k
                  ? "bg-indigo-100 text-indigo-700 border-indigo-300 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-800"
                  : "bg-white text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700"
              }`}
            >
              {r}
            </button>
          ))}
          <button
            type="button"
            disabled={bloq || ocupado === "lacunas"}
            onClick={() => rodar("lacunas", async () => {
              setLac(await analisesApi.lacunas(visao))
              await carregar()
            })}
            className={BTN_MINI}
          >
            {ocupado === "lacunas" ? "Analisando…" : "Analisar as vagas"}
          </button>
        </div>
        {lac?.faltam ? (
          <p className="text-xs text-amber-700 dark:text-amber-300">
            {lac.vagas} vaga(s) analisada(s) nesta visão; faltam {lac.faltam} para o ranking ficar útil.
          </p>
        ) : lac ? (
          <>
            <Data x={lac} />
            <p className={DICA}>
              Em {lac.vagas} vagas ({lac.visao === "seguidas" ? "que você seguiu" : "todas"}).
            </p>
            {lac.itens.length ? (
              <ul className="space-y-2">
                {lac.itens.map((i) => (
                  <li key={i.rotulo} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                    <p className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                        {NIVEL[i.nivel] || i.nivel}
                      </span>
                      <b>{i.rotulo}</b>
                      <span className={DICA}>
                        {i.vagas} vaga(s) · {Math.round(i.parte * 100)}% do peso
                      </span>
                    </p>
                    {i.variacoes.length > 1 && <p className={DICA}>Também escrito como: {i.variacoes.slice(1).join("; ")}</p>}
                    {i.exemplos?.length > 0 && (
                      <p className={DICA}>Ex.: {i.exemplos.map((x) => `${x.titulo} — ${x.empresa}`).join(", ")}</p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className={DICA}>Nenhuma lacuna aparece em 10% ou mais do peso das vagas.</p>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                disabled={bloq || !d.ia || !lac.itens.length || ocupado === "plano"}
                onClick={() => rodar("plano", async () => {
                  await analisesApi.plano()
                  await carregar()
                })}
                className={BTN_MINI}
                title={`Usa a IA.${custo}`}
              >
                {ocupado === "plano" ? "Escrevendo…" : "Plano de estudo"}
              </button>
              {d.ia ? (
                custo && <span className={DICA}>{custo.trim()}</span>
              ) : (
                <span className={DICA}>O plano precisa de uma IA (botão IA) ou do chat.</span>
              )}
            </div>
          </>
        ) : null}
        {plano?.itens && (
          <>
            <Data x={plano} />
            <ul className="space-y-2">
              {plano.itens.map((p) => (
                <li key={p.lacuna}>
                  <b>{p.lacuna}</b> <span className={DICA}>~{p.semanas} semana(s)</span>
                  <ul className="list-disc pl-5">
                    {p.passos.map((x) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className={SEC}>
        <h4 className={H}>Carreiras e cargos-alvo</h4>
        <p className={DICA}>
          De 5 a 10 cargos que o seu perfil sustenta, com a evidência e o que falta. Marque os que quiser buscar e leve para
          os filtros (só grava quando você confirmar).
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            disabled={bloq || !d.ia || ocupado === "cargos"}
            onClick={() => rodar("cargos", async () => {
              setCargos(await analisesApi.cargos())
              setMarcados({})
              setProposta(null)
            })}
            className={BTN_MINI}
            title={`Usa a IA.${custo}`}
          >
            {ocupado === "cargos" ? "Pensando…" : "Sugerir cargos"}
          </button>
          {d.ia ? custo && <span className={DICA}>{custo.trim()}</span> : <span className={DICA}>Precisa de uma IA (botão IA) ou do chat.</span>}
        </div>
        {cargos?.itens && (
          <>
            <Data x={cargos} />
            {(cargos.avisos || []).length > 0 && <p className={DICA}>{(cargos.avisos || []).join(" ")}</p>}
            <ul className="space-y-2">
              {cargos.itens.map((c, n) => (
                <li key={n} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                  <label className="flex items-center gap-2 flex-wrap cursor-pointer">
                    <input
                      type="checkbox"
                      disabled={bloq}
                      checked={Boolean(marcados[n])}
                      onChange={(ev) => {
                        setMarcados((m) => ({ ...m, [n]: ev.target.checked }))
                        setProposta(null)
                      }}
                    />
                    <b>{c.titulo}</b>
                    {c.titulo_en && <span className={DICA}>/ {c.titulo_en}</span>}
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
                      {TIPO[c.tipo] || c.tipo}
                    </span>
                    {c.conferir && (
                      <span className="text-[10px] font-semibold text-rose-600 dark:text-rose-400">
                        conferir: a evidência não foi achada no perfil
                      </span>
                    )}
                  </label>
                  <p className={DICA}>
                    Evidência: “{c.evidencia}”{c.lacuna ? ` · Falta: ${c.lacuna}` : ""}
                  </p>
                </li>
              ))}
            </ul>
            <button
              type="button"
              disabled={bloq}
              onClick={() => {
                if (!escolhidos().length) return onAviso("Marque pelo menos um cargo.", "erro")
                rodar("propor", async () => setProposta(await analisesApi.cargosParaFiltros(escolhidos())))
              }}
              className={BTN_MINI}
            >
              Levar os marcados para os filtros
            </button>
            {proposta && (
              <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 space-y-2 text-xs">
                {proposta.mudancas.map((m) => (
                  <p key={m.campo}>
                    <b>{m.campo}:</b> {(m.proposto || []).join(", ")}
                  </p>
                ))}
                <button
                  type="button"
                  disabled={bloq || ocupado === "confirmar"}
                  onClick={() =>
                    rodar("confirmar", async () => {
                      await analisesApi.cargosParaFiltros(escolhidos(), true)
                      setProposta(null)
                      setMarcados({})
                      onAviso("Cargos gravados nos filtros da busca.")
                    })
                  }
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
                >
                  Confirmar e gravar nos filtros
                </button>
              </div>
            )}
          </>
        )}
      </section>

      <section className={SEC}>
        <h4 className={H}>Prontidão internacional</h4>
        <p className={DICA}>O que já está pronto e o que falta para se candidatar a vagas de fora.</p>
        <ul className="space-y-2">
          {d.prontidao.map((i) => (
            <li key={i.item} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${COR_SIT[i.situacao] || ""}`}>
                  {SIT[i.situacao] || i.situacao}
                </span>
                <b>{i.rotulo}</b>
                {i.acao === "marcar" ? (
                  <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      disabled={bloq}
                      checked={i.situacao === "pronto"}
                      onChange={(ev) => rodar("marcar", async () => {
                        await analisesApi.marcar(ev.target.checked)
                        await carregar()
                      })}
                    />
                    Meu LinkedIn tem a versão em inglês
                  </label>
                ) : i.situacao !== "pronto" && i.acao === "filtros_int" ? (
                  <button type="button" onClick={onAbrirFiltrosInt} className={BTN_MINI}>
                    Abrir o painel internacional
                  </button>
                ) : i.situacao !== "pronto" && i.acao === "perfil" ? (
                  <button type="button" disabled={bloq} onClick={onCompletarPerfil} className={BTN_MINI}>
                    Completar o perfil
                  </button>
                ) : i.situacao !== "pronto" && i.acao === "curriculo" ? (
                  <span className={DICA}>Currículos: por enquanto, na página de sempre.</span>
                ) : null}
              </div>
              <p className={DICA}>
                {i.detalhe} · {i.origem}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
