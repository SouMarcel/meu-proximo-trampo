/**
 * Painel IA (dash/API.md §3.5): provedor, modelo, endereço (compatível) e chave. A chave nunca volta para a página
 * (só os 4 últimos caracteres e a origem) e não fica guardada no navegador: o campo começa sempre vazio.
 */
import React, { useEffect, useState } from "react"
import { X, Sparkles, Loader2, AlertTriangle, CheckCircle2, XCircle } from "lucide-react"
import * as iaApi from "../../services/api/ia"
import type { EstadoIA, Provedor, EscolhaIA } from "../../services/api/ia"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { linkSeguro } from "../../utils/formatters"

interface Props {
  onClose: () => void
  onSalvo: (mensagem: string) => void
  onAviso: (mensagem: string, tipo?: "info" | "erro") => void
}

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"

/** O que a pessoa precisa saber antes de salvar (o mesmo texto do dashboard antigo). */
/** Modelo gratuito do OpenRouter (o roteador openrouter/free ou um modelo :free): sem custo, com limite de pedidos. */
function ehGratuito(p: Provedor | undefined, modelo: string): boolean {
  const m = (modelo || p?.modelo_padrao || "").trim().toLowerCase()
  return p?.id === "openrouter" && (m === "openrouter/free" || m.endsWith(":free"))
}

function avisos(p: Provedor | undefined, modelo: string): string[] {
  if (!p || p.id === "nenhum") {
    return ["Nada é enviado a provedores de IA. Busca, relatório e quadro funcionam normalmente; as vagas ficam sem nota."]
  }
  const l = [
    ehGratuito(p, modelo)
      ? "Modelo gratuito: sem custo, com limite de pedidos por dia no OpenRouter (veja a dica abaixo)."
      : p.cobranca === "assinatura"
        ? "Usa a sua assinatura do Claude: não há cobrança por chamada além do plano."
        : "Cobrado por uso, na sua conta do provedor: cada análise de vaga consome créditos.",
    "Notas de modelos diferentes podem variar para a mesma vaga.",
    `O seu perfil e o texto das vagas vão para ${p.nome} a cada análise.`,
  ]
  if (p.cobranca === "uso") {
    l.push("Em planos gratuitos, alguns provedores podem usar os dados enviados para melhorar os produtos deles. Confira os termos antes.")
  }
  if (p.dica) l.push(p.dica)
  return l
}

export default function AISettingsModal({ onClose, onSalvo, onAviso }: Props) {
  const { servidor, tratarErro, recarregarIA, registrarPodeAlterar } = useFerramenta()
  const [e, setE] = useState<EstadoIA | null>(null)
  const [provedor, setProvedor] = useState("")
  const [modelo, setModelo] = useState("")
  const [urlBase, setUrlBase] = useState("")
  const [chave, setChave] = useState("")
  const [erro, setErro] = useState("")
  const [teste, setTeste] = useState<{ ok: boolean; mensagem: string } | null>(null)
  const [ocupado, setOcupado] = useState<"" | "testar" | "salvar" | "remover">("")

  const escolher = (estado: EstadoIA, prov: string) => {
    const g = estado.escolha
    setProvedor(prov)
    setModelo(g && g.provedor === prov ? g.modelo || "" : "")
    setUrlBase(g && g.provedor === prov ? g.url_base || "" : "")
    setChave("")
    setTeste(null)
  }

  useEffect(() => {
    iaApi
      .estado()
      .then((j) => {
        setE(j)
        registrarPodeAlterar(j.pode_alterar)
        escolher(j, j.escolha?.provedor || j.efetiva)
      })
      .catch((err) => setErro("Não deu para abrir o painel de IA: " + mensagemDeErro(err)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const p = e?.provedores.find((x) => x.id === provedor)
  const podeMudar = Boolean(e?.pode_alterar) && servidor === "no_ar"
  const c = (p && e?.chaves?.[p.id]) || null

  const corpo = (): EscolhaIA => {
    const x: EscolhaIA = { provedor, modelo: modelo.trim(), url_base: urlBase.trim() }
    if (chave.trim()) x.chave = chave.trim()
    return x
  }

  const testar = async () => {
    setOcupado("testar")
    setTeste(null)
    try {
      setTeste(await iaApi.testar(corpo()))
    } catch (err) {
      tratarErro(err)
      setTeste({ ok: false, mensagem: mensagemDeErro(err) })
    } finally {
      setOcupado("")
    }
  }

  const salvar = async (ev: React.FormEvent) => {
    ev.preventDefault()
    setOcupado("salvar")
    setErro("")
    try {
      const j = await iaApi.salvar(corpo())
      setChave("")
      await recarregarIA()
      onSalvo(`IA salva: ${j.provedores.find((x) => x.id === j.efetiva)?.nome || j.efetiva}.`)
    } catch (err) {
      tratarErro(err)
      setErro(mensagemDeErro(err, "Não deu para salvar a IA."))
    } finally {
      setOcupado("")
    }
  }

  const removerChave = async () => {
    if (!p) return
    setOcupado("remover")
    try {
      const j = await iaApi.removerChave(p.id)
      setE(j)
      await recarregarIA()
      onAviso(j.aviso || "Chave removida do arquivo .env.", j.aviso ? "erro" : "info")
    } catch (err) {
      tratarErro(err)
      onAviso(mensagemDeErro(err, "Não deu para remover a chave."), "erro")
    } finally {
      setOcupado("")
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-ia"
        onSubmit={salvar}
        className="relative w-full max-w-xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(ev) => ev.stopPropagation()}
      >
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-violet-50 dark:bg-violet-950 text-violet-600 dark:text-violet-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 id="titulo-ia" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">IA</h3>
              <p className="text-xs text-slate-500">
                A IA dá a nota de aderência e ajuda no currículo e na entrevista. Sem IA, busca, relatório e quadro
                continuam funcionando.
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm">
          {!e && !erro && (
            <p className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
            </p>
          )}

          {e && (
            <>
              <section className={SEC}>
                <h4 className={H}>Provedor</h4>
                <label htmlFor="ia-prov" className={ROTULO}>IA usada pela ferramenta</label>
                <select id="ia-prov" value={provedor} disabled={!podeMudar} onChange={(ev) => escolher(e, ev.target.value)} className={CAMPO}>
                  {e.provedores.map((x) => (
                    <option key={x.id} value={x.id}>{x.nome}</option>
                  ))}
                </select>
                {provedor === "claude_code" && (
                  <p className={DICA}>
                    {e.claude_instalado ? (
                      "Claude Code encontrado neste computador."
                    ) : (
                      <>
                        Claude Code não encontrado neste computador. Instale em{" "}
                        <a href="https://claude.com/claude-code" target="_blank" rel="noopener noreferrer" className="underline">
                          claude.com/claude-code
                        </a>{" "}
                        ou escolha outro provedor.
                      </>
                    )}
                  </p>
                )}
                {e.ultimo_erro && (
                  <p className="text-[11px] text-rose-600 dark:text-rose-400">Último erro: {e.ultimo_erro.motivo}</p>
                )}
              </section>

              {provedor !== "nenhum" && (
                <section className={SEC}>
                  <h4 className={H}>Modelo</h4>
                  <label htmlFor="ia-modelo" className={ROTULO}>Nome do modelo</label>
                  <input
                    id="ia-modelo"
                    maxLength={120}
                    autoComplete="off"
                    spellCheck={false}
                    value={modelo}
                    disabled={!podeMudar}
                    onChange={(ev) => setModelo(ev.target.value)}
                    placeholder={p?.modelo_padrao ? `${p.modelo_padrao} (padrão)` : "modelo padrão da sua conta"}
                    className={CAMPO}
                  />
                  {provedor === "compativel" && (
                    <>
                      <label htmlFor="ia-url" className={ROTULO}>Endereço do serviço</label>
                      <input
                        id="ia-url"
                        maxLength={300}
                        autoComplete="off"
                        spellCheck={false}
                        value={urlBase}
                        disabled={!podeMudar}
                        onChange={(ev) => setUrlBase(ev.target.value)}
                        placeholder={p?.url_padrao || "https://…/v1"}
                        className={CAMPO}
                      />
                    </>
                  )}
                </section>
              )}

              {p?.aceita_chave && (
                <section className={SEC}>
                  <h4 className={H}>Chave de API</h4>
                  <p className="text-slate-700 dark:text-slate-300">
                    {c?.cadastrada ? (
                      <>
                        Chave cadastrada, terminada em <b>{c.final || "…"}</b>{" "}
                        {c.origem === "ambiente" ? "(nas variáveis de ambiente do sistema)" : "(no arquivo .env deste computador)"}
                        {c.origem === "arquivo" && (
                          <button
                            type="button"
                            onClick={removerChave}
                            disabled={!podeMudar || Boolean(ocupado)}
                            className="ml-2 px-2 py-0.5 rounded-lg text-[11px] font-semibold text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 disabled:opacity-50"
                          >
                            Remover
                          </button>
                        )}
                      </>
                    ) : p.precisa_chave ? (
                      "Nenhuma chave cadastrada."
                    ) : (
                      "Chave opcional para este serviço."
                    )}
                  </p>
                  <label htmlFor="ia-chave" className={ROTULO}>
                    {c?.cadastrada ? "Trocar a chave (em branco, mantém a atual)" : "Cole a chave"}
                  </label>
                  <input
                    id="ia-chave"
                    type="password"
                    autoComplete="off"
                    spellCheck={false}
                    maxLength={400}
                    value={chave}
                    disabled={!podeMudar}
                    onChange={(ev) => setChave(ev.target.value)}
                    placeholder="fica só no arquivo .env deste computador"
                    className={CAMPO}
                  />
                  {linkSeguro(p.onde_obter_chave) && (
                    <p className={DICA}>
                      Onde conseguir:{" "}
                      <a href={linkSeguro(p.onde_obter_chave)} target="_blank" rel="noopener noreferrer" className="underline break-all">
                        {p.onde_obter_chave}
                      </a>
                    </p>
                  )}
                </section>
              )}

              <section className={SEC}>
                <h4 className={H}>Antes de salvar</h4>
                <ul className="list-disc pl-5 space-y-1 text-slate-700 dark:text-slate-300">
                  {avisos(p, modelo).map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              </section>

              {teste && (
                <p
                  role="status"
                  className={`flex items-start gap-2 p-3 rounded-xl border text-xs ${
                    teste.ok
                      ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-200"
                      : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200"
                  }`}
                >
                  {teste.ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <XCircle className="w-4 h-4 shrink-0" />}
                  <span>{teste.mensagem}</span>
                </p>
              )}
              {!e.pode_alterar && (
                <p className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs">
                  Só dá para mudar a IA no computador onde a ferramenta roda.
                </p>
              )}
            </>
          )}

          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{erro}</span>
            </p>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-3 flex-wrap">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            Cancelar
          </button>
          <button
            type="button"
            onClick={testar}
            disabled={!e || !podeMudar || provedor === "nenhum" || Boolean(ocupado)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition disabled:opacity-50"
            title="Testa a conexão com o que está no painel; a chave digitada não é gravada"
          >
            {ocupado === "testar" && <Loader2 className="w-4 h-4 animate-spin" />}
            <span>{ocupado === "testar" ? "Testando a conexão…" : "Testar conexão"}</span>
          </button>
          <button
            type="submit"
            disabled={!e || !podeMudar || Boolean(ocupado)}
            className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition disabled:opacity-50"
          >
            {ocupado === "salvar" && <Loader2 className="w-4 h-4 animate-spin" />}
            <span>Salvar</span>
          </button>
        </div>
      </form>
    </div>
  )
}
