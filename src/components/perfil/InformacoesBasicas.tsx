/**
 * Meu perfil → Informações básicas (spec 036): os dados da pessoa que a ferramenta usa em formulários e na carta,
 * reunidos num lugar só — dados de contato (spec 033), respostas que ela já deu (spec 027/035) e os sites onde a
 * candidatura assistida preenche (spec 027). Mesmas rotas de antes (dash/API.md §3.11b), só deste computador; o login
 * guardado de cada portal continua em Atualizar candidaturas.
 */
import React, { useCallback, useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import * as api from "../../services/api/candidatura"
import type { EstadoCandidatura } from "../../services/api/candidatura"
import { mensagemDeErro, ehErroApi } from "../../services/api"
import { BTN_MINI } from "../curriculo/Curriculos"
import { recarregarCandidatura } from "../../hooks/useCandidatura"
import DadosContato from "./DadosContato"

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const SO_AQUI = "Só dá para ver e mudar estes dados no computador onde a ferramenta roda."

export default function InformacoesBasicas({ so, onAviso }: { so: boolean; onAviso: (m: string, t?: "info" | "erro") => void }) {
  const [e, setE] = useState<EstadoCandidatura | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState("")
  const [soAqui, setSoAqui] = useState(so)

  const carregar = useCallback(
    () =>
      api
        .estado()
        .then(setE)
        .catch((err) => (ehErroApi(err) && err.status === 403 ? setSoAqui(true) : setErro(mensagemDeErro(err)))),
    [],
  )
  useEffect(() => {
    if (!so) carregar()
  }, [so, carregar])

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

  if (so || soAqui) return <p className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs">{SO_AQUI}</p>
  if (!e)
    return erro ? (
      <p role="alert" className="text-rose-600 dark:text-rose-400 text-xs">{erro}</p>
    ) : (
      <p className="flex items-center gap-2 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
      </p>
    )

  return (
    <>
      <p className="text-slate-700 dark:text-slate-300">
        O que a ferramenta usa para preencher formulários de candidatura e o cabeçalho da carta. Fica só neste computador,
        fora do Git.
      </p>

      <section className={SEC}>
        <DadosContato
          inicial={e.contato || {}}
          podeGravar={!so}
          onSalvo={() => {
            carregar()
            recarregarCandidatura()
          }}
          onAviso={onAviso}
        />
      </section>

      <section className={SEC}>
        <h4 className={H}>Respostas que você já deu</h4>
        <p className={DICA}>
          A ferramenta reaproveita estas respostas nas próximas vagas, sem perguntar de novo. A pretensão salarial e a
          relocação nunca ficam guardadas. Apague a que estiver errada ou desatualizada.
        </p>
        {e.memoria.length ? (
          <ul className="space-y-1 text-xs">
            {e.memoria.map((m) => (
              <li key={m.chave} className="flex items-start gap-2">
                <span>
                  {m.pergunta} <b>→ {m.resposta.length > 80 ? m.resposta.slice(0, 80) + "…" : m.resposta}</b>
                  <span className={DICA}> ({m.em.split("-").reverse().join("/")})</span>
                </span>
                <button
                  type="button"
                  className={`${BTN_MINI} ml-auto shrink-0`}
                  disabled={ocupado}
                  onClick={() => acao(async () => { await api.apagarMemoria(m.chave); onAviso("Resposta apagada.") })}
                >
                  Apagar
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className={DICA}>Nenhuma ainda. Elas aparecem aqui depois que você usa a candidatura assistida numa vaga.</p>
        )}
      </section>

      <section className={SEC}>
        <h4 className={H}>Onde a ferramenta preenche</h4>
        <p className={DICA}>
          A candidatura assistida só preenche em sites conhecidos ou liberados por você: {e.dominios.conhecidos.map((d) => d.rotulo).join(", ")}.
        </p>
        {e.dominios.liberados.length > 0 && (
          <ul className="space-y-1 text-xs">
            {e.dominios.liberados.map((d) => (
              <li key={d.dominio} className="flex items-center gap-2 flex-wrap">
                {d.dominio} <span className={DICA}>liberado por você em {d.em}</span>
                <button
                  type="button"
                  className={`${BTN_MINI} ml-auto`}
                  disabled={ocupado}
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
      </section>

      {erro && <p role="alert" className="text-rose-600 dark:text-rose-400 text-xs">{erro}</p>}
    </>
  )
}
