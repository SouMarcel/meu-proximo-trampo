/**
 * Revisão do perfil ao levar relatos (spec 050, dash/API.md): a IA propôs onde cada relato entra no perfil (o cargo
 * certo, Habilidades, Formação…), escrito como item de currículo e só com o que a pessoa contou. Aqui ela aceita ou
 * recusa item a item, escolhe nas discordâncias (manter o perfil, usar o relato ou escrever a correção) e grava; só
 * então o perfil muda, com a versão anterior guardada. Aparece no fim da análise de reprovação (origem "vaga:<id>") e
 * em Meu perfil → Seus relatos (origem "relatos").
 */
import React, { useCallback, useEffect, useRef, useState } from "react"
import { ClipboardCheck, Loader2 } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { DecisoesRevisao, DiscordanciaRevisao, ItemRevisao, RevisaoPerfil } from "../../services/api/perfil"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { ehDoAlvo, useGeracao } from "../../contexto/Geracao"
import { diaMes, horaDe } from "../../utils/formatters"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const AVISO = "text-[11px] text-amber-700 dark:text-amber-300"
const CAIXA = "p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1"
const CAMPO =
  "w-full p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs disabled:opacity-60"
const BTN = "px-4 py-2 rounded-xl text-xs font-semibold disabled:opacity-50"
const TIPO: Record<ItemRevisao["tipo"], { rotulo: string; cor: string }> = {
  entra: { rotulo: "entra", cor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" },
  muda: { rotulo: "muda", cor: "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300" },
  sai: { rotulo: "sai", cor: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300" },
}

/** O alvo da geração desta origem, para o andamento (ehDoAlvo). */
export const alvoDaOrigem = (origem: string) => (origem.startsWith("vaga:") ? origem.slice(5) : "perfil")

const lugarDe = (i: ItemRevisao) => (i.cargo ? `${i.secao} › ${i.cargo}` : i.secao)

function Item({
  i,
  r,
  travado,
  onAceitar,
}: {
  i: ItemRevisao
  r: RevisaoPerfil
  travado: boolean
  onAceitar: (aceito: boolean) => void
}) {
  const t = TIPO[i.tipo]
  const origens = r.relatos_info.filter((x) => i.relatos.includes(x.id))
  return (
    <li className={`${CAIXA} ${i.aceito ? "" : "opacity-75"}`}>
      <label className="flex items-start gap-2 cursor-pointer">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={i.aceito}
          disabled={travado || !i.valido}
          onChange={(ev) => onAceitar(ev.target.checked)}
          title={i.valido ? "" : "Não dá para aceitar: a linha não foi encontrada no perfil"}
        />
        <span className="flex-1 min-w-0 space-y-0.5">
          <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold mr-1.5 ${t.cor}`}>{t.rotulo}</span>
          {i.tipo === "entra" && <span>{i.novo}</span>}
          {i.tipo === "muda" && (
            <>
              <span className="block text-slate-500 dark:text-slate-400 line-through decoration-slate-400/60">{i.atual}</span>
              <span className="block">→ {i.novo}</span>
            </>
          )}
          {i.tipo === "sai" && <span className="text-slate-500 dark:text-slate-400 line-through decoration-slate-400/60">{i.atual}</span>}
        </span>
      </label>
      {i.avisos.map((a, k) => (
        <p key={k} className={AVISO}>
          Confira: {a}
        </p>
      ))}
      {origens.length > 0 && (
        <p className={DICA}>
          De: {origens.map((x) => x.pergunta || "relato sem pergunta").join(" · ")}
        </p>
      )}
      {i.origem === "ferramenta" && <p className={DICA}>A linha crua da seção Relatos sai, porque o fato entra no lugar certo.</p>}
    </li>
  )
}

function Discordancia({
  d,
  travado,
  onEscolher,
}: {
  d: DiscordanciaRevisao
  travado: boolean
  onEscolher: (escolha: "perfil" | "relato" | "correcao", correcao?: string) => void
}) {
  const [correcao, setCorrecao] = useState(d.correcao || "")
  const semRelato = !d.valido || !d.opcao_relato || !d.opcao_relato.valido
  return (
    <li className={CAIXA}>
      <p className="font-semibold">{d.assunto}</p>
      <p className={DICA}>
        <b>No relato:</b> “{d.trecho_relato}”
      </p>
      <p className={DICA}>
        <b>No perfil:</b> {d.trecho_perfil ? `“${d.trecho_perfil}”` : "não ficou claro em qual cargo isso aconteceu"}
      </p>
      {d.avisos.map((a, k) => (
        <p key={k} className={AVISO}>
          {a}
        </p>
      ))}
      <div className="space-y-1 pt-1">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="radio" name={`disc-${d.id}`} checked={d.escolha === "perfil"} disabled={travado} onChange={() => onEscolher("perfil")} />
          Manter o perfil como está
        </label>
        <label className={`flex items-start gap-2 ${semRelato ? "opacity-60" : "cursor-pointer"}`}>
          <input
            type="radio"
            name={`disc-${d.id}`}
            className="mt-0.5"
            checked={d.escolha === "relato"}
            disabled={travado || semRelato}
            onChange={() => onEscolher("relato")}
          />
          <span>
            Usar o relato
            {d.opcao_relato && (
              <span className={`block ${DICA}`}>
                {d.opcao_relato.tipo === "muda" ? "→ " : "+ "}
                {d.opcao_relato.novo}
                {d.opcao_relato.cargo ? ` (${lugarDe(d.opcao_relato)})` : ""}
              </span>
            )}
          </span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="radio" name={`disc-${d.id}`} checked={d.escolha === "correcao"} disabled={travado} onChange={() => onEscolher("correcao", correcao)} />
          Escrever a correção
        </label>
        {d.escolha === "correcao" && (
          <textarea
            value={correcao}
            rows={2}
            maxLength={600}
            disabled={travado}
            placeholder={d.trecho_perfil ? "O texto que substitui a linha do perfil." : "O item como deve entrar no perfil."}
            onChange={(ev) => {
              setCorrecao(ev.target.value)
              onEscolher("correcao", ev.target.value)
            }}
            className={CAMPO}
          />
        )}
      </div>
    </li>
  )
}

/** A proposta da revisão desta origem, com o andamento, as decisões (gravadas sozinhas) e o botão Gravar no perfil. */
export function SecaoRevisaoPerfil({ origem, onGravado }: { origem: string; onGravado?: () => void }) {
  const { servidor, podeGravar, tratarErro } = useFerramenta()
  const { estado, ativa, versao, tentar } = useGeracao()
  const [r, setR] = useState<RevisaoPerfil | null>(null)
  const [erro, setErro] = useState("")
  const [salvo, setSalvo] = useState<"" | "salvando" | "salvo">("")
  const [enviando, setEnviando] = useState(false)
  const pendente = useRef<DecisoesRevisao>({})
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const carregar = useCallback(() => {
    perfilApi
      .obterRevisao(origem)
      .then((j) => setR(j.revisao))
      .catch(() => {})
  }, [origem])

  useEffect(() => {
    if (servidor === "no_ar") carregar()
  }, [carregar, versao, servidor])

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current) }, [])

  const gravarDecisoes = useCallback(async () => {
    const lote = pendente.current
    pendente.current = {}
    if (!Object.keys(lote.itens || {}).length && !Object.keys(lote.discordancias || {}).length) return
    setSalvo("salvando")
    try {
      const j = await perfilApi.decidirRevisao(origem, lote)
      setR(j.revisao)
      setSalvo("salvo")
      setErro("")
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para guardar a decisão."))
      setSalvo("")
      carregar()
    }
  }, [origem, tratarErro, carregar])

  const agendar = () => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(gravarDecisoes, 600)
  }

  const aceitar = (id: string, aceito: boolean) => {
    setR((x) => x && { ...x, itens: x.itens.map((i) => (i.id === id ? { ...i, aceito } : i)) })
    pendente.current.itens = { ...(pendente.current.itens || {}), [id]: aceito }
    agendar()
  }

  const escolher = (id: string, escolha: "perfil" | "relato" | "correcao", correcao?: string) => {
    setR((x) => x && { ...x, discordancias: x.discordancias.map((d) => (d.id === id ? { ...d, escolha, correcao: correcao ?? d.correcao } : d)) })
    pendente.current.discordancias = { ...(pendente.current.discordancias || {}), [id]: { escolha, correcao } }
    agendar()
  }

  const gravar = async () => {
    setEnviando(true)
    setErro("")
    try {
      if (timer.current) clearTimeout(timer.current)
      await gravarDecisoes()
      const j = await perfilApi.gravarRevisao(origem)
      setR(j.revisao)
      if (onGravado) onGravado()
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para gravar no perfil."))
      carregar()
    } finally {
      setEnviando(false)
    }
  }

  const descartar = async () => {
    try {
      await perfilApi.descartarRevisao(origem)
      setR(null)
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para descartar."))
    }
  }

  const minha = ehDoAlvo(estado, alvoDaOrigem(origem), ["revisao_perfil"])
  const rodando = minha && ativa
  const falhou = minha && estado?.situacao === "falha"
  if (!r && !rodando && !falhou) return null

  const travado = !podeGravar || Boolean(r?.gravada_em) || enviando
  const grupos: { chave: string; rotulo: string; itens: ItemRevisao[] }[] = []
  for (const i of r?.itens || []) {
    const chave = `${i.secao}|${i.cargo || ""}`
    const g = grupos.find((x) => x.chave === chave)
    if (g) g.itens.push(i)
    else grupos.push({ chave, rotulo: lugarDe(i), itens: [i] })
  }
  const semFato = (r?.relatos_info || []).filter((x) => (r?.sem_fato || []).includes(x.id))

  return (
    <section className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-800 text-xs">
      <div className="flex items-center gap-2 flex-wrap">
        <ClipboardCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Revisão do perfil</h4>
        {r && (
          <span className={DICA}>
            proposta de {diaMes(r.criada_em)} {horaDe(r.criada_em)}
          </span>
        )}
      </div>

      {rodando && (
        <p className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          {estado?.etapa_texto || "Revisando o seu perfil…"} Pode levar alguns minutos; dá para fechar e voltar.
        </p>
      )}
      {falhou && (
        <p className="text-rose-700 dark:text-rose-300">
          A revisão não saiu: {estado?.mensagem || "falha"}{" "}
          {estado?.pode_tentar && podeGravar && (
            <button type="button" className="underline font-semibold" onClick={() => tentar()}>
              Tentar de novo
            </button>
          )}
        </p>
      )}

      {r && (
        <>
          {r.gravada_em ? (
            <p className="text-emerald-700 dark:text-emerald-300">
              Levadas ao perfil em {diaMes(r.gravada_em)} {horaDe(r.gravada_em)} · {r.aceitos} item(ns).
              {r.anterior ? ` A versão anterior do perfil ficou guardada (${r.anterior}).` : ""}
            </p>
          ) : (
            <p className={DICA}>
              A IA propôs onde cada fato entra; nada muda no perfil até você clicar em Gravar no perfil. Os itens com
              aviso vêm desmarcados: aceite só o que estiver certo.
            </p>
          )}
          {r.ia?.aviso && <p className={AVISO}>{r.ia.aviso}</p>}
          {r.avisos.map((a, k) => (
            <p key={k} className={AVISO}>
              {a}
            </p>
          ))}

          {grupos.map((g) => (
            <div key={g.chave} className="space-y-1.5">
              <h5 className="font-semibold text-slate-800 dark:text-slate-200">→ {g.rotulo}</h5>
              <ul className="space-y-1.5">
                {g.itens.map((i) => (
                  <Item key={i.id} i={i} r={r} travado={travado} onAceitar={(a) => aceitar(i.id, a)} />
                ))}
              </ul>
            </div>
          ))}

          {r.discordancias.length > 0 && (
            <div className="space-y-1.5">
              <h5 className="font-semibold text-slate-800 dark:text-slate-200">Discordâncias com o seu perfil: qual vale?</h5>
              <ul className="space-y-1.5">
                {r.discordancias.map((d) => (
                  <Discordancia key={d.id} d={d} travado={travado} onEscolher={(e, c) => escolher(d.id, e, c)} />
                ))}
              </ul>
            </div>
          )}

          {semFato.length > 0 && (
            <p className={DICA}>
              Sem fato para o perfil: {semFato.map((x) => `“${x.pergunta || x.relato.slice(0, 60)}”`).join(", ")}.
            </p>
          )}

          {erro && <p className="text-rose-700 dark:text-rose-300">{erro}</p>}
          {!r.gravada_em && (
            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                disabled={!r.pode_gravar || travado || servidor !== "no_ar"}
                onClick={gravar}
                className={`${BTN} flex items-center gap-1.5 text-white bg-indigo-600 hover:bg-indigo-500`}
                title={r.pode_gravar ? "" : r.motivo}
              >
                {enviando && <Loader2 className="w-4 h-4 animate-spin" />}
                Gravar no perfil
              </button>
              <button
                type="button"
                disabled={travado}
                onClick={descartar}
                className={`${BTN} border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200`}
              >
                Descartar
              </button>
              <span className={DICA}>
                {salvo === "salvando" ? "salvando…" : salvo === "salvo" ? "decisões guardadas" : ""}
                {!r.pode_gravar && r.motivo ? ` ${r.motivo}.` : ""}
                {!podeGravar ? " Só dá para gravar no computador onde a ferramenta roda." : ""}
              </span>
            </div>
          )}
        </>
      )}
    </section>
  )
}
