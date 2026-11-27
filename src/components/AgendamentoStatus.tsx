/** Quadro do agendamento da busca no Relatório (spec 064): próxima busca, situação de hoje e retomadas. */
import { useCallback, useEffect, useState } from "react"
import { CalendarClock } from "lucide-react"
import * as agendamentoApi from "../services/api/agendamento"
import { mensagemDeErro } from "../services/api"
import type { EstadoAgendamento, RetomadaAgendada } from "../types/api"
import { horaDe } from "../utils/formatters"

interface Props {
  /** Muda quando a busca termina, para reler o quadro. */
  gatilho?: string
}

function dia(iso: string): string {
  const d = new Date()
  const hoje = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
  const a = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1)
  const amanha = `${a.getFullYear()}-${String(a.getMonth() + 1).padStart(2, "0")}-${String(a.getDate()).padStart(2, "0")}`
  const data = iso.slice(0, 10)
  if (data === hoje) return "hoje"
  if (data === amanha) return "amanhã"
  return `em ${data.slice(8, 10)}/${data.slice(5, 7)}`
}

function situacaoHoje(h: NonNullable<EstadoAgendamento["hoje"]>, horario: string): string | null {
  const hora = horaDe(h.em) || horario
  switch (h.situacao) {
    case "rodou":
      return `Hoje: rodou às ${hora}`
    case "pulada":
      return `Hoje: pulada${h.motivo ? ` (${h.motivo})` : ""}`
    case "perdida":
      return `Hoje: não rodou (o dashboard não estava ligado às ${horario})`
    case "falha":
      return `Hoje: a busca agendada falhou${h.motivo ? ` (${h.motivo})` : ""}`
    case "rodando":
      return "Hoje: rodando agora"
    case "devida":
      return "Hoje: chegou a hora; começa assim que a tarefa em andamento terminar"
    default:
      return null
  }
}

function plural(n: number, um: string, varios: string) {
  return `${n} ${n === 1 ? um : varios}`
}

function textoRetomada(r: RetomadaAgendada): string {
  const faltam = [
    r.consultas > 0 ? plural(r.consultas, "consulta", "consultas") : "",
    r.descricoes > 0 ? plural(r.descricoes, "descrição", "descrições") : "",
  ].filter(Boolean)
  const quando = horaDe(r.proxima)
  const dia_ = dia(r.proxima) === "hoje" ? "" : ` ${dia(r.proxima)}`
  const resto = faltam.length ? `: faltam ${faltam.join(" e ")}` : ""
  return `${r.portal} retoma${dia_} às ${quando}${resto}`
}

export default function AgendamentoStatus({ gatilho = "" }: Props) {
  const [estado, setEstado] = useState<EstadoAgendamento | null>(null)
  const [erro, setErro] = useState("")
  const [cancelando, setCancelando] = useState("")

  const ler = useCallback(async () => {
    try {
      setEstado(await agendamentoApi.ler())
    } catch {
      // mantém o último quadro; a próxima leitura tenta de novo
    }
  }, [])

  useEffect(() => {
    ler()
    const t = setInterval(ler, 60000)
    return () => clearInterval(t)
  }, [ler, gatilho])

  const cancelar = async (nome: string) => {
    setCancelando(nome)
    setErro("")
    try {
      setEstado(await agendamentoApi.cancelarRetomada(nome))
    } catch (e) {
      setErro(mensagemDeErro(e, "Não foi possível cancelar a retomada."))
      ler()
    } finally {
      setCancelando("")
    }
  }

  if (!estado) return null
  const { agendamento: ag, retomadas } = estado
  if (!ag.ligado && retomadas.length === 0) return null

  const hoje = estado.hoje ? situacaoHoje(estado.hoje, ag.horario) : null

  return (
    <div className="rounded-2xl border p-4 text-xs sm:text-sm space-y-1.5 shadow-2xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300">
      {ag.ligado && (
        <p className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <CalendarClock className="w-4 h-4 text-indigo-500 shrink-0" />
          {estado.proxima
            ? `Próxima busca agendada: ${dia(estado.proxima)} às ${horaDe(estado.proxima)}`
            : "Busca agendada ligada"}
        </p>
      )}
      {ag.ligado && hoje && <p className="text-slate-600 dark:text-slate-400">{hoje}</p>}
      {retomadas.map((r) => (
        <p key={r.nome} className="flex items-center gap-2 flex-wrap">
          <span>{textoRetomada(r)}</span>
          {estado.pode_alterar && (
            <button
              type="button"
              onClick={() => cancelar(r.nome)}
              disabled={cancelando === r.nome}
              className="px-3 py-1 rounded-xl text-xs font-semibold transition disabled:opacity-50 text-rose-700 dark:text-rose-300 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900"
            >
              Cancelar
            </button>
          )}
        </p>
      ))}
      {erro && (
        <p role="alert" className="text-rose-600 dark:text-rose-400">
          {erro}
        </p>
      )}
    </div>
  )
}
