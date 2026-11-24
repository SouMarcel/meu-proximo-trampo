/** Limpeza de vagas antigas (dash/API.md, spec 054). */
import { pedir } from "../api"
import type {
  CriteriosLimpeza,
  EstadoLimpeza,
  PreviaLimpeza,
  RespostaAplicarLimpeza,
} from "../../types/api"

export const ler = () => pedir<EstadoLimpeza>("GET", "/api/limpeza")
export const gravar = (criterios: CriteriosLimpeza) => pedir<EstadoLimpeza>("PUT", "/api/limpeza", { criterios })
export const previa = () => pedir<PreviaLimpeza>("GET", "/api/limpeza/previa")
export const aplicar = (ids: string[]) => pedir<RespostaAplicarLimpeza>("POST", "/api/limpeza/aplicar", { ids })
