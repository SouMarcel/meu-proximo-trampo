/**
 * Candidatar com ajuda (dash/API.md §3.11b; spec 027): abre a vaga na janela da ferramenta, preenche o login guardado
 * e, página por página, propõe respostas que a pessoa confere antes de a ferramenta preencher os campos. Nunca clica
 * em botão nem envia: quem avança e envia é a pessoa. Só aparece com o recurso ligado (Contas conectadas).
 */
import React, { useEffect, useState } from "react"
import { Loader2, AlertTriangle, Wand2 } from "lucide-react"
import type { Vaga } from "../../types/api"
import * as api from "../../services/api/candidatura"
import type { Campo, EstadoCandidatura, Leitura, Preenchimento } from "../../services/api/candidatura"
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
  if (c.tipo === "selecao" || c.tipo === "unica")
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

function valorAtual(c: Campo): string {
  if (!c.valor) return ""
  if (c.opcoes.length) return c.valor.split(",").map((v) => c.opcoes.find((o) => o.valor === v)?.texto || v).join("; ")
  if (c.tipo === "caixa") return c.valor === "sim" ? "marcada" : ""
  return c.valor
}

export default function CandidaturaAssistida({ vaga, onAviso }: { vaga: Vaga; onAviso: (m: string, t?: "info" | "erro") => void }) {
  const { podeGravar, ia } = useFerramenta()
  const [estado, setEstado] = useState<EstadoCandidatura | null>(null)
  const [leitura, setLeitura] = useState<Leitura | null>(null)
  const [respostas, setRespostas] = useState<Record<string, Resposta>>({})
  const [resultado, setResultado] = useState<Preenchimento | null>(null)
  const [ocupado, setOcupado] = useState("")
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!podeGravar) return
    api.estado().then(setEstado).catch(() => setEstado(null))
  }, [podeGravar])

  if (!podeGravar || !estado?.ligado || vaga.triagem !== "seguir") return null

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

  const lerPagina = () =>
    acao("ler", async () => {
      setResultado(null)
      const l = await api.ler(vaga.id)
      setLeitura(l)
      const r: Record<string, Resposta> = {}
      l.itens.filter((c) => c.marca === "comum").forEach((c) => (r[c.chave] = { valor: c.proposta || "", trocar: false }))
      setRespostas(r)
    })

  const comLogin = estado.credenciais.some((c) => c.guardada)
  const pag = leitura?.pagina
  const comuns = (leitura?.itens || []).filter((c) => c.marca === "comum")
  const daPessoa = (leitura?.itens || []).filter((c) => c.marca !== "comum")
  const aPreencher = comuns.filter((c) => respostas[c.chave]?.valor && (!c.valor || respostas[c.chave]?.trocar))

  return (
    <section className="space-y-2 p-3 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/40 dark:bg-indigo-950/20">
      <h4 className={`${H} flex items-center gap-2`}>
        <Wand2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Candidatar com ajuda
      </h4>
      <p className={DICA}>
        Abra a vaga na janela da ferramenta, avance no portal até as perguntas e clique em <b>Preencher esta página</b>. Você
        confere as respostas antes; depois, confere na janela e clica você em Continuar ou Enviar.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={BTN_MINI}
          disabled={Boolean(ocupado) || !estado.navegador}
          onClick={() =>
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
        >
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
                const j = await api.preencherLogin()
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
          title={ia?.disponivel ? textoCustoIA(ia) : "Sem IA: você escreve as respostas e a ferramenta preenche igual"}
          onClick={lerPagina}
        >
          {ocupado === "ler" ? "Lendo a página…" : "Preencher esta página"}
        </button>
      </div>
      {!estado.navegador && <p className="text-rose-600 dark:text-rose-400 text-xs">Precisa do Edge ou do Chrome neste computador.</p>}

      {ocupado === "ler" && (
        <p role="status" className="flex items-center gap-2 text-xs text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Lendo a página e escrevendo as propostas com o seu perfil…
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
                  }).then(lerPagina)
                }
              >
                Liberar {pag.dominio.host}
              </button>
            </div>
          )}
          {pag.dominio.permitido && pag.aviso && (
            <p className={`p-2 rounded-xl ${pag.etapa === "perguntas" ? "bg-slate-100 dark:bg-slate-800" : "bg-amber-50 dark:bg-amber-950/40"}`}>
              {pag.aviso}
            </p>
          )}
          {leitura?.aviso_ia && <p className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40">{leitura.aviso_ia}</p>}

          {comuns.length > 0 && (
            <ul className="space-y-3">
              {comuns.map((c) => {
                const r = respostas[c.chave] || { valor: "", trocar: false }
                const atual = valorAtual(c)
                return (
                  <li key={c.chave} className="space-y-1">
                    <span className="block font-semibold text-slate-800 dark:text-slate-200">
                      {c.rotulo}
                      {c.obrigatorio && <span className="text-rose-600"> *</span>}
                    </span>
                    <Controle c={c} r={r} disabled={!podeGravar} onChange={(n) => setRespostas((x) => ({ ...x, [c.chave]: n }))} />
                    {!c.proposta && !r.valor && <span className={DICA}>Sem base no perfil: escreva você, se quiser.</span>}
                    {c.conferir.length > 0 && (
                      <span className="block text-[11px] text-amber-700 dark:text-amber-300">Conferir: {c.conferir.join(" · ")}</span>
                    )}
                    {atual && (
                      <label className={`flex items-center gap-1.5 ${DICA}`}>
                        <input
                          type="checkbox"
                          checked={r.trocar}
                          onChange={(e) => setRespostas((x) => ({ ...x, [c.chave]: { ...r, trocar: e.target.checked } }))}
                        />
                        Já está preenchido na página ({atual.slice(0, 80)}). Trocar pelo que está aqui
                      </label>
                    )}
                  </li>
                )
              })}
            </ul>
          )}

          {daPessoa.length > 0 && (
            <div className="space-y-1">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Ficam com você, na janela:</span>
              <ul className="list-disc pl-5 space-y-0.5">
                {daPessoa.map((c) => (
                  <li key={c.chave}>
                    {c.rotulo || "(campo sem rótulo)"} <span className={DICA}>— {c.motivo}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {comuns.length > 0 && pag.dominio.permitido && (
            <button
              type="button"
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
              disabled={Boolean(ocupado) || !aPreencher.length}
              onClick={() =>
                acao("preencher", async () => {
                  const j = await api.preencher(
                    vaga.id,
                    pag.assinatura,
                    aPreencher.map((c) => ({ chave: c.chave, valor: respostas[c.chave].valor, trocar: respostas[c.chave].trocar })),
                  )
                  setResultado(j)
                  setLeitura(null)
                  onAviso(`${j.preenchidos.length} campo(s) preenchido(s). ${j.aviso}`)
                })
              }
            >
              {aPreencher.length ? `Preencher ${aPreencher.length} campo(s) no formulário` : "Nada para preencher"}
            </button>
          )}
        </div>
      )}

      {resultado && !ocupado && (
        <div role="status" className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-xs space-y-1">
          <b>{resultado.preenchidos.length} campo(s) preenchido(s).</b> {resultado.aviso}
          {resultado.ficaram.length > 0 && (
            <ul className="list-disc pl-5">
              {resultado.ficaram.map((f) => (
                <li key={f.chave}>
                  {f.rotulo || "(campo sem rótulo)"} <span className={DICA}>— {f.motivo}</span>
                </li>
              ))}
            </ul>
          )}
          {resultado.documento && <span className={`block ${DICA}`}>As respostas ficaram guardadas no kit desta vaga.</span>}
          <span className={`block ${DICA}`}>Na próxima etapa do formulário, clique em Preencher esta página de novo.</span>
        </div>
      )}

      {erro && (
        <p role="alert" className="flex items-start gap-2 p-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {erro}
        </p>
      )}
      <p className={DICA}>{LEMBRETE}</p>
    </section>
  )
}
