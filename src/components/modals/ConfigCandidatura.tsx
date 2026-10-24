/**
 * Configuração da candidatura assistida (dash/API.md §3.11b; spec 027), dentro de Contas conectadas. O recurso é ligado
 * vaga a vaga, no detalhe da vaga; aqui ficam usuário e senha por portal (vão para o .env; só os 4 últimos caracteres
 * voltam) e os sites que a pessoa liberou. Domínios bloqueados (LinkedIn, Indeed, Nerdin) não podem ser liberados.
 */
import React, { useEffect, useState } from "react"
import { Wand2 } from "lucide-react"
import * as api from "../../services/api/candidatura"
import type { EstadoCandidatura } from "../../services/api/candidatura"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { BTN_MINI } from "../curriculo/Curriculos"
import { recarregarCandidatura } from "../../hooks/useCandidatura"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"

export default function ConfigCandidatura({ onAviso }: { onAviso: (m: string, t?: "info" | "erro") => void }) {
  const { podeGravar } = useFerramenta()
  const [e, setE] = useState<EstadoCandidatura | null>(null)
  const [editando, setEditando] = useState<string | null>(null)
  const [usuario, setUsuario] = useState("")
  const [senha, setSenha] = useState("")
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState("")

  const carregar = () => api.estado().then(setE).catch((err) => setErro(mensagemDeErro(err)))
  useEffect(() => {
    carregar()
  }, [])

  const acao = async (fn: () => Promise<void>) => {
    setOcupado(true)
    setErro("")
    try {
      await fn()
      await Promise.all([carregar(), recarregarCandidatura()])
    } catch (err) {
      setErro(mensagemDeErro(err))
    } finally {
      setOcupado(false)
    }
  }

  if (!e) return erro ? <p className="text-rose-600 text-xs">{erro}</p> : null

  return (
    <section className="space-y-2">
      <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
        <Wand2 className="w-4 h-4" /> Candidatura assistida: logins e sites
      </h4>
      <p className={DICA}>
        A candidatura assistida é ligada vaga a vaga, no detalhe da vaga (aba Candidatura). Aqui ficam o login guardado de cada
        portal e os sites que você liberou. Quem clica em Continuar e Enviar é sempre você.
      </p>

      <>
          <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <b className="text-xs">Login guardado (opcional)</b>
            <p className={DICA}>
              Usuário e senha ficam em texto no arquivo .env deste computador (fora do Git) e só são digitados na tela de login
              do próprio portal. A senha nunca volta para esta página. Sem guardar, você faz o login à mão na janela.
            </p>
            {e.credenciais.map((c) => (
              <div key={c.portal} className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <b>{c.rotulo}</b>
                  <span className={DICA}>({c.login.join(", ")})</span>
                  {c.guardada ? (
                    <span>
                      {c.usuario} · senha terminada em ••{c.final}
                    </span>
                  ) : (
                    <span className={DICA}>nada guardado</span>
                  )}
                  <span className="ml-auto flex gap-1">
                    <button
                      type="button"
                      className={BTN_MINI}
                      disabled={!podeGravar || ocupado}
                      onClick={() => {
                        setEditando(editando === c.portal ? null : c.portal)
                        setUsuario(c.usuario)
                        setSenha("")
                      }}
                    >
                      {c.guardada ? "Trocar" : "Guardar"}
                    </button>
                    {c.guardada && (
                      <button
                        type="button"
                        className={BTN_MINI}
                        disabled={!podeGravar || ocupado || c.no_ambiente}
                        title={c.no_ambiente ? "Definida nas variáveis de ambiente do sistema; remova por lá" : undefined}
                        onClick={() => acao(async () => { await api.apagarCredencial(c.portal); onAviso(`Login da ${c.rotulo} apagado do .env.`) })}
                      >
                        Apagar
                      </button>
                    )}
                  </span>
                </div>
                {editando === c.portal && (
                  <form
                    className="flex flex-wrap gap-2 items-center"
                    onSubmit={(ev) => {
                      ev.preventDefault()
                      acao(async () => {
                        await api.guardarCredencial(c.portal, usuario, senha)
                        setEditando(null)
                        setSenha("")
                        onAviso(`Login da ${c.rotulo} guardado no .env.`)
                      })
                    }}
                  >
                    <input className={CAMPO} placeholder="usuário ou e-mail" autoComplete="off" value={usuario} onChange={(ev) => setUsuario(ev.target.value)} />
                    <input className={CAMPO} type="password" placeholder="senha" autoComplete="new-password" value={senha} onChange={(ev) => setSenha(ev.target.value)} />
                    <button type="submit" className={BTN_MINI} disabled={ocupado || !usuario.trim() || !senha}>
                      Guardar
                    </button>
                  </form>
                )}
              </div>
            ))}
          </div>

          <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1 text-xs">
            <b>Respostas que você já deu</b>
            <p className={DICA}>
              A ferramenta reaproveita estas respostas nas próximas vagas, sem perguntar de novo. Salário e relocação nunca ficam
              guardados. Apague a que estiver errada ou desatualizada.
            </p>
            {e.memoria.length ? (
              <ul className="space-y-1">
                {e.memoria.map((m) => (
                  <li key={m.chave} className="flex items-start gap-2">
                    <span>
                      {m.pergunta} <b>→ {m.resposta.length > 80 ? m.resposta.slice(0, 80) + "…" : m.resposta}</b>
                      <span className={DICA}> ({m.em.split("-").reverse().join("/")})</span>
                    </span>
                    <button
                      type="button"
                      className={`${BTN_MINI} ml-auto`}
                      disabled={!podeGravar || ocupado}
                      onClick={() => acao(async () => { await api.apagarMemoria(m.chave); onAviso("Resposta apagada.") })}
                    >
                      Apagar
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className={DICA}>Nenhuma ainda.</p>
            )}
          </div>

          <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1 text-xs">
            <b>Onde a ferramenta preenche</b>
            <p className={DICA}>Sites de candidatura conhecidos: {e.dominios.conhecidos.map((d) => d.rotulo).join(", ")}.</p>
            {e.dominios.liberados.length > 0 && (
              <ul className="space-y-1">
                {e.dominios.liberados.map((d) => (
                  <li key={d.dominio} className="flex items-center gap-2">
                    {d.dominio} <span className={DICA}>liberado por você em {d.em}</span>
                    <button
                      type="button"
                      className={`${BTN_MINI} ml-auto`}
                      disabled={!podeGravar || ocupado}
                      onClick={() => acao(async () => { await api.dominio(d.dominio, "revogar"); onAviso(`${d.dominio} revogado.`) })}
                    >
                      Revogar
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <p className={DICA}>
              Nunca preenche em: {e.dominios.bloqueados.map((b) => `${b.dominio} (${b.motivo})`).join("; ")}.
            </p>
          </div>
      </>
      {erro && <p role="alert" className="text-rose-600 dark:text-rose-400 text-xs">{erro}</p>}
    </section>
  )
}
