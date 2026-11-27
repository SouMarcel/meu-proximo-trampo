/**
 * Aba Agendamento dos filtros da busca (spec 064): busca diária e retomada do que faltou.
 * Tem fluxo próprio (GET/PUT /api/agendamento) e não entra no Salvar filtros.
 */
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import * as agendamentoApi from "../../services/api/agendamento"
import { mensagemDeErro } from "../../services/api"
import { AvisoSoLeitura } from "../../contexto/Ferramenta"
import type { Agendamento } from "../../types/api"

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"
const AVISO_AMBAR =
  "p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs"
const BOTAO =
  "px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed transition"

export default function AgendamentoAba({ podeSalvar }: { podeSalvar: boolean }) {
  const [valor, setValor] = useState<Agendamento | null>(null)
  const [avisoLogin, setAvisoLogin] = useState<string | null>(null)
  const [podeAlterar, setPodeAlterar] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [salvo, setSalvo] = useState(false)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let vivo = true
    agendamentoApi
      .ler()
      .then((r) => {
        if (!vivo) return
        setValor(r.agendamento)
        setAvisoLogin(r.aviso_login)
        setPodeAlterar(r.pode_alterar)
      })
      .catch((e) => vivo && setErro(mensagemDeErro(e, "Não foi possível ler o agendamento.")))
    return () => {
      vivo = false
    }
  }, [])

  if (!valor) {
    return erro ? (
      <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">
        {erro}
      </p>
    ) : (
      <p className={`${DICA} flex items-center gap-2`}>
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando…
      </p>
    )
  }

  const mudar = (parte: Partial<Agendamento>) => {
    setValor({ ...valor, ...parte })
    setSalvo(false)
  }

  const salvar = async () => {
    setSalvando(true)
    setErro("")
    setSalvo(false)
    try {
      const r = await agendamentoApi.gravar(valor)
      setValor(r.agendamento)
      setAvisoLogin(r.aviso_login)
      setPodeAlterar(r.pode_alterar)
      setSalvo(true)
    } catch (e) {
      setErro(mensagemDeErro(e, "Não foi possível salvar o agendamento."))
    } finally {
      setSalvando(false)
    }
  }

  const livre = podeSalvar && podeAlterar && !salvando

  return (
    <section className={SEC}>
      <h4 className={H}>Busca agendada</h4>
      {!podeSalvar && <AvisoSoLeitura />}
      <label className="flex items-center gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-200">
        <input
          type="checkbox"
          checked={valor.ligado}
          disabled={!livre}
          onChange={(e) => mudar({ ligado: e.target.checked })}
          className="w-4 h-4 accent-indigo-600"
        />
        <b>Buscar todo dia</b>
      </label>
      <div>
        <label htmlFor="agendamento-horario" className={ROTULO}>
          Horário
        </label>
        <input
          id="agendamento-horario"
          type="time"
          value={valor.horario}
          disabled={!livre}
          onChange={(e) => mudar({ horario: e.target.value })}
          className={CAMPO}
        />
      </div>
      <label className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-200">
        <input
          type="checkbox"
          checked={valor.continuar}
          disabled={!livre}
          onChange={(e) => mudar({ continuar: e.target.checked })}
          className="w-4 h-4 mt-0.5 accent-indigo-600"
        />
        <span>
          <b>Continuar de onde parou</b>
          <span className={`block ${DICA}`}>
            Se um portal bloquear, a ferramenta tenta de novo o que faltou a cada 6 horas, até terminar ou até a próxima
            busca agendada.
          </span>
        </span>
      </label>
      <p className={DICA}>
        A busca agendada roda só com o dashboard ligado. Se ele estiver desligado no horário, a busca daquele dia não
        roda. Se você buscar à mão nas 4 horas antes, a agendada do dia é pulada. Portais com login ficam de fora.
      </p>
      {avisoLogin && <p className={AVISO_AMBAR}>{avisoLogin}</p>}
      {erro && (
        <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">
          {erro}
        </p>
      )}
      <div className="flex items-center gap-3">
        <button type="button" onClick={salvar} disabled={!livre} className={BOTAO}>
          {salvando ? "Salvando…" : "Salvar"}
        </button>
        {salvo && (
          <span role="status" className="text-xs text-emerald-700 dark:text-emerald-400">
            Agendamento salvo.
          </span>
        )}
      </div>
    </section>
  )
}
