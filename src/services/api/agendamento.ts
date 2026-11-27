/** Agendamento da busca (spec 064): GET/PUT /api/agendamento e DELETE das retomadas. */
import { pedir } from "../api"
import type { Agendamento, EstadoAgendamento } from "../../types/api"

export const ler = () => pedir<EstadoAgendamento>("GET", "/api/agendamento")
export const gravar = (parcial: Partial<Agendamento>) => pedir<EstadoAgendamento>("PUT", "/api/agendamento", parcial)
export const cancelarRetomada = (nome: string) =>
  pedir<EstadoAgendamento>("DELETE", `/api/agendamento/retomadas/${encodeURIComponent(nome)}`)
