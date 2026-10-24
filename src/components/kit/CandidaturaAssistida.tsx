/**
 * Candidatar com ajuda (dash/API.md §3.11b; spec 027): abre a vaga na janela da ferramenta, preenche o login guardado
 * e, página por página, preenche o que sabe (respostas que a pessoa já deu e o perfil) e pergunta o resto. Nunca clica
 * em botão nem envia: quem confere na janela, avança e envia é a pessoa. A chave é por vaga: a pessoa liga nesta vaga, com o aviso de risco.
 */
import React, { useEffect, useRef, useState } from "react"
import { Loader2, AlertTriangle, Wand2 } from "lucide-react"
import type { Vaga } from "../../types/api"
import * as api from "../../services/api/candidatura"
import type { AutoPreenchimento, Campo, Preenchimento } from "../../services/api/candidatura"
import { useCandidatura } from "../../hooks/useCandidatura"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta, textoCustoIA } from "../../contexto/Ferramenta"
import { BTN_MINI } from "../curriculo/Curriculos"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const LEMBRETE = "A ferramenta só preenche campos. Quem clica em Entrar, Continuar e Enviar é você, na janela."

interface Resposta {
  valor: string
  trocar: boolean
}

function Controle({ c, r, onChange, disabled }: { c: Campo; r: Resposta; onChange: (r: Resposta) => void; disabled: boolean }) {
  const set = (valor: string) => onChange({ ...r, valor })
  const opcoes = c.opcoes.filter((o) => !o.vazia)
  if (c.tipo === "area")
    return (
      <>
        <textarea rows={3} className={CAMPO} value={r.valor} maxLength={c.limite || undefined} disabled={disabled} onChange={(e) => set(e.target.value)} />
        {c.limite > 0 && <span className={DICA}>{r.valor.length} de {c.limite} caracteres</span>}
      </>
    )
  if (c.tipo === "texto")
    return (
      <input
        className={CAMPO}
        value={r.valor}
        inputMode={c.tipo_html === "number" ? "numeric" : undefined}
        maxLength={c.limite || undefined}
        disabled={disabled}
        onChange={(e) => set(e.target.value)}
      />
    )
  if (c.tipo === "selecao" || c.tipo === "unica" || c.tipo === "lista")
    return (
      <select className={CAMPO} value={r.valor} disabled={disabled} onChange={(e) => set(e.target.value)}>
        <option value="">(não preencher)</option>
        {opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto || `Opção ${Number(o.valor) + 1}`}
          </option>
        ))}
      </select>
    )
  if (c.tipo === "multipla") {
    const marcadas = r.valor ? r.valor.split(",") : []
    return (
      <span className="flex flex-wrap gap-x-4 gap-y-1">
        {opcoes.map((o) => (
          <label key={o.valor} className="flex items-center gap-1.5 text-xs">
            <input
              type="checkbox"
              disabled={disabled}
              checked={marcadas.includes(o.valor)}
              onChange={(e) => set((e.target.checked ? [...marcadas, o.valor] : marcadas.filter((x) => x !== o.valor)).sort().join(","))}
            />
            {o.texto}
          </label>
        ))}
      </span>
    )
  }
  if (c.tipo === "caixa")
    return (
      <select className={CAMPO} value={r.valor} disabled={disabled} onChange={(e) => set(e.target.value)}>
        <option value="">(não preencher)</option>
        <option value="sim">Sim (marcar)</option>
        <option value="nao">Não (deixar desmarcada)</option>
      </select>
    )
  return null
}

/** Vaga no funil e ainda sem candidatura enviada (ou enviada há pouco, com etapas do formulário pela frente). */
export const podeCandidatar = (v: Vaga) => v.etapa === "salva" || v.etapa === "aplicada" || (!v.etapa && v.triagem === "seguir")

export default function CandidaturaAssistida({
  vaga,
  onAviso,
  abrirAoMontar = false,
  semMoldura = false,
}: {
  vaga: Vaga
  onAviso: (m: string, t?: "info" | "erro") => void
  /** Vindo do botão do card: já abre a vaga na janela da ferramenta (o clique da pessoa foi esse). */
  abrirAoMontar?: boolean
  semMoldura?: boolean
}) {
  const { podeGravar, ia } = useFerramenta()
  const estado = useCandidatura(podeGravar)
  const abriu = useRef(false)
  const [auto, setAuto] = useState<AutoPreenchimento | null>(null)
  const [respostas, setRespostas] = useState<Record<string, Resposta>>({})
  const [lembrar, setLembrar] = useState(true)
  const [resultado, setResultado] = useState<Preenchimento | null>(null)
  const [ocupado, setOcupado] = useState("")
  const [erro, setErro] = useState("")
  const [ligada, setLigada] = useState(Boolean(vaga.candidatura_assistida?.ligada))
  const [aceitar, setAceitar] = useState(false)
  useEffect(() => setLigada(Boolean(vaga.candidatura_assistida?.ligada)), [vaga.candidatura_assistida?.ligada])

  const pronto = Boolean(podeGravar && estado && ligada && podeCandidatar(vaga))
  useEffect(() => {
    if (pronto && abrirAoMontar && !abriu.current) {
      abriu.current = true
      abrirVaga()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pronto, abrirAoMontar])

  const acao = async (chave: string, fn: () => Promise<void>) => {
    setOcupado(chave)
    setErro("")
    try {
      await fn()
    } catch (e) {
      setErro(mensagemDeErro(e))
    } finally {
      setOcupado("")
    }
  }

  const chave = (ligar: boolean) =>
    acao("chave", async () => {
      const j = await api.ligarVaga(vaga.id, ligar, ligar && aceitar)
      setLigada(Boolean(j.vaga.candidatura_assistida?.ligada))
      setAceitar(false)
      setAuto(null)
      setResultado(null)
      onAviso(ligar ? "Candidatura assistida ligada nesta vaga." : "Candidatura assistida desligada nesta vaga.")
    })

  if (!podeGravar || !estado || !podeCandidatar(vaga)) return null

  if (!ligada)
    return (
      <section className={semMoldura ? "space-y-2" : "space-y-2 p-3 rounded-2xl border border-slate-200 dark:border-slate-800"}>
        {!semMoldura && (
          <h4 className={`${H} flex items-center gap-2`}>
            <Wand2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Candidatar com ajuda
          </h4>
        )}
        <p className={DICA}>
          A ferramenta abre esta vaga numa janela dela, preenche o formulário com o que sabe de você (perfil e respostas que
          você já deu) e pergunta o que não souber. Quem clica em Continuar e Enviar é você. Vale só para esta vaga.
        </p>
        <p className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs">{estado.aviso}</p>
        <label className="flex items-center gap-2 text-xs">
          <input type="checkbox" checked={aceitar} onChange={(e) => setAceitar(e.target.checked)} />
          Entendi; usar a candidatura assistida nesta vaga
        </label>
        <button
          type="button"
          className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
          disabled={!aceitar || Boolean(ocupado)}
          onClick={() => chave(true)}
        >
          {ocupado === "chave" ? "Ligando…" : "Ligar nesta vaga"}
        </button>
        {erro && <p role="alert" className="text-rose-600 dark:text-rose-400 text-xs">{erro}</p>}
      </section>
    )

  const preencherPagina = () =>
    acao("auto", async () => {
      setResultado(null)
      const j = await api.auto(vaga.id)
      setAuto(j)
      const r: Record<string, Resposta> = {}
      j.perguntas.forEach((c) => (r[c.chave] = { valor: "", trocar: false }))
      setRespostas(r)
      if (j.preenchidos.length) onAviso(`${j.preenchidos.length} campo(s) preenchido(s). Confira na janela.`)
    })

  function abrirVaga() {
    acao("abrir", async () => {
      const j = await api.abrir(vaga.id)
      if (!j.dominio.permitido)
        onAviso(
          j.dominio.bloqueado
            ? `Aberta, mas aqui a ferramenta não preenche: ${j.dominio.bloqueado}.`
            : `Aberta. ${j.dominio.host} ainda não está liberado: a ferramenta pergunta quando você pedir o preenchimento.`,
        )
      else onAviso("Vaga aberta na janela da ferramenta.")
    })
  }

  const comLogin = estado.credenciais.some((c) => c.guardada)
  const pag = auto?.pagina
  const aResponder = (auto?.perguntas || []).filter((c) => respostas[c.chave]?.valor)

  return (
    <section className={semMoldura ? "space-y-2" : "space-y-2 p-3 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/40 dark:bg-indigo-950/20"}>
      {!semMoldura && (
        <h4 className={`${H} flex items-center gap-2`}>
          <Wand2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Candidatar com ajuda
        </h4>
      )}
      <p className={DICA}>
        Abra a vaga na janela da ferramenta, avance no portal até as perguntas e clique em <b>Preencher esta página</b>. A
        ferramenta preenche o que sabe e pergunta aqui o que não souber.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={BTN_MINI} disabled={Boolean(ocupado) || !estado.navegador} onClick={abrirVaga}>
          {ocupado === "abrir" ? "Abrindo…" : "Abrir a vaga na janela"}
        </button>
        {comLogin && (
          <button
            type="button"
            className={BTN_MINI}
            disabled={Boolean(ocupado)}
            title="Digita o usuário e a senha guardados só na tela de login do portal; quem clica em Entrar é você"
            onClick={() =>
              acao("login", async () => {
                const j = await api.preencherLogin(vaga.id)
                onAviso(j.aviso)
              })
            }
          >
            {ocupado === "login" ? "Preenchendo…" : "Preencher login"}
          </button>
        )}
        <button
          type="button"
          className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
          disabled={Boolean(ocupado) || !estado.navegador}
          title={ia?.disponivel ? textoCustoIA(ia) : "Sem IA: a ferramenta usa só as respostas que você já deu e pergunta o resto"}
          onClick={preencherPagina}
        >
          {ocupado === "auto" ? "Preenchendo…" : "Preencher esta página"}
        </button>
      </div>
      {!estado.navegador && <p className="text-rose-600 dark:text-rose-400 text-xs">Precisa do Edge ou do Chrome neste computador.</p>}

      {ocupado === "auto" && (
        <p role="status" className="flex items-center gap-2 text-xs text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Lendo a página e preenchendo com o que a ferramenta sabe de você…
        </p>
      )}

      {pag && !ocupado && (
        <div className="space-y-3 text-xs">
          {pag.dominio.bloqueado && (
            <p className="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200">
              Aqui a ferramenta não preenche: {pag.dominio.bloqueado}.
            </p>
          )}
          {!pag.dominio.permitido && pag.dominio.pode_liberar && (
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 space-y-1">
              <p>
                Este endereço (<b>{pag.dominio.host}</b>) não está na lista de sites de candidatura. Liberar o preenchimento
                nele? Você pode revogar depois em Contas conectadas.
              </p>
              <button
                type="button"
                className={BTN_MINI}
                onClick={() =>
                  acao("liberar", async () => {
                    await api.dominio(pag.dominio.host, "liberar")
                    onAviso(`${pag.dominio.host} liberado.`)
                  }).then(preencherPagina)
                }
              >
                Liberar {pag.dominio.host}
              </button>
            </div>
          )}
          {pag.dominio.permitido && pag.etapa !== "perguntas" && pag.aviso && (
            <p className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40">{pag.aviso}</p>
          )}
          {auto?.aviso_ia && <p className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40">{auto.aviso_ia}</p>}

          {auto && auto.preenchidos.length > 0 && (
            <div className="space-y-1">
              <span className="font-semibold text-emerald-700 dark:text-emerald-400">Preenchi {auto.preenchidos.length} campo(s):</span>
              <ul className="space-y-0.5">
                {auto.preenchidos.map((x) => (
                  <li key={x.chave}>
                    {x.rotulo}: <b>{x.texto.length > 120 ? x.texto.slice(0, 120) + "…" : x.texto}</b>{" "}
                    <span className={DICA}>({x.fonte})</span>
                    {x.conferir.length > 0 && <span className="block text-[11px] text-amber-700 dark:text-amber-300">Conferir: {x.conferir.join(" · ")}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {auto && auto.perguntas.length > 0 && (
            <div className="space-y-3">
              <span className="font-semibold text-slate-800 dark:text-slate-200">Preciso da sua resposta ({auto.perguntas.length}):</span>
              <ul className="space-y-3">
                {auto.perguntas.map((c) => {
                  const r = respostas[c.chave] || { valor: "", trocar: false }
                  return (
                    <li key={c.chave} className="space-y-1">
                      <span className="block font-semibold text-slate-800 dark:text-slate-200">
                        {c.rotulo || "(pergunta sem texto)"}
                        {c.obrigatorio && <span className="text-rose-600"> *</span>}
                      </span>
                      <Controle c={c} r={r} disabled={!podeGravar} onChange={(n) => setRespostas((x) => ({ ...x, [c.chave]: n }))} />
                      <span className={DICA}>
                        {c.motivo}
                        {!c.lembrar && " · esta resposta não fica guardada: muda de vaga para vaga"}
                      </span>
                    </li>
                  )
                })}
              </ul>
              <label className={`flex items-center gap-1.5 ${DICA}`}>
                <input type="checkbox" checked={lembrar} onChange={(e) => setLembrar(e.target.checked)} />
                Lembrar estas respostas para as próximas vagas (salário e relocação nunca ficam guardados)
              </label>
              <button
                type="button"
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
                disabled={Boolean(ocupado) || !aResponder.length}
                onClick={() =>
                  acao("preencher", async () => {
                    const j = await api.preencher(
                      vaga.id,
                      pag.assinatura,
                      aResponder.map((c) => ({ chave: c.chave, valor: respostas[c.chave].valor })),
                      lembrar,
                    )
                    setResultado(j)
                    setAuto((a) => (a ? { ...a, perguntas: a.perguntas.filter((c) => !j.preenchidos.some((p) => p.chave === c.chave)) } : a))
                    onAviso(`${j.preenchidos.length} resposta(s) sua(s) preenchida(s). ${j.aviso}`)
                  })
                }
              >
                {aResponder.length ? `Preencher minhas ${aResponder.length} resposta(s)` : "Responda acima para preencher"}
              </button>
            </div>
          )}

          {auto && auto.na_janela.length > 0 && (
            <div className="space-y-1">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Na janela, com você:</span>
              <ul className="list-disc pl-5 space-y-0.5">
                {auto.na_janela.map((c) => (
                  <li key={c.chave}>
                    {c.rotulo || "(campo sem rótulo)"} <span className={DICA}>— {c.motivo}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {auto && pag.etapa === "perguntas" && pag.dominio.permitido && (
            <p className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800">
              {auto.aviso} Na próxima etapa do formulário, clique em Preencher esta página de novo.
            </p>
          )}
        </div>
      )}

      {resultado && resultado.ficaram.some((f) => f.motivo.startsWith("não consegui")) && !ocupado && (
        <p className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-xs">
          Não consegui preencher: {resultado.ficaram.filter((f) => f.motivo.startsWith("não consegui")).map((f) => f.rotulo).join("; ")}. Preencha
          você na janela.
        </p>
      )}

      {erro && (
        <p role="alert" className="flex items-start gap-2 p-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {erro}
        </p>
      )}
      <p className={DICA}>
        {LEMBRETE}{" "}
        <button type="button" className="underline disabled:opacity-50" disabled={Boolean(ocupado)} onClick={() => chave(false)}>
          Desligar nesta vaga
        </button>
      </p>
    </section>
  )
}
