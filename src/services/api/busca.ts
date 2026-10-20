/** Busca de vagas e descrições pendentes (dash/API.md §3.3). */
import { pedir } from "../api"
import type { EstadoBusca, EstadoPendentes, PlanoBusca } from "../../types/api"

export const plano = () => pedir<PlanoBusca>("GET", "/api/busca/plano")

export const iniciar = (opcoes: {
  sem_nota?: boolean
  confirmar_recente?: boolean
  confirmar_espera?: boolean
}) => pedir<EstadoBusca>("POST", "/api/busca", opcoes)

export const estado = () => pedir<EstadoBusca>("GET", "/api/busca")

export const cancelar = () => pedir<EstadoBusca>("DELETE", "/api/busca")

export const tentarNota = () =>
  pedir<{ analise: NonNullable<EstadoBusca["analise"]> }>("POST", "/api/busca/analisar", {})

export const pendentes = () => pedir<EstadoPendentes>("GET", "/api/busca/pendentes")

export const completarPendentes = () => pedir<EstadoPendentes>("POST", "/api/busca/pendentes", {})

/** Situações em que a busca está rodando (a página consulta o andamento a cada 2 s). */
export const SITUACOES_ATIVAS = ["consultando", "descricoes", "gravando", "cancelando", "externa"]
