/** IA (dash/API.md §3.5). A chave nunca volta para a página: só se existe, os 4 últimos caracteres e a origem. */
import { pedir } from "../api"

export interface Provedor {
  id: string
  nome: string
  precisa_chave: boolean
  aceita_chave: boolean
  cobranca: "uso" | "assinatura" | ""
  modelo_padrao: string
  url_padrao: string
  onde_obter_chave: string
  dica: string
}

export interface EstadoIA {
  escolha: { provedor: string; modelo: string; url_base: string } | null
  efetiva: string
  modelo_efetivo: string
  url_efetiva: string
  provedores: Provedor[]
  chaves: Record<string, { cadastrada: boolean; final: string; origem: "arquivo" | "ambiente" | null }>
  claude_instalado: boolean
  pode_alterar: boolean
  disponivel: boolean
  ultimo_erro: { motivo: string; em: string } | null
}

export const estado = () => pedir<EstadoIA>("GET", "/api/ia")
