/** IA (dash/API.md §3.5). A chave nunca volta para a página: só se existe, os 4 últimos caracteres e a origem. */
import { pedir } from "../api"

export interface Provedor {
  id: string
  nome: string
  precisa_chave: boolean
  aceita_chave: boolean
  cobranca: "uso" | "assinatura" | "gratuito" | ""
  modelo_padrao: string
  url_padrao: string
  onde_obter_chave: string
  dica: string
}

export interface EstadoIA {
  escolha: { provedor: string; modelo: string; url_base: string } | null
  efetiva: string
  modelo_efetivo: string
  /** A da escolha: "gratuito" = openrouter/free ou um modelo :free do OpenRouter. */
  cobranca_efetiva?: "uso" | "assinatura" | "gratuito" | ""
  url_efetiva: string
  provedores: Provedor[]
  chaves: Record<string, { cadastrada: boolean; final: string; origem: "arquivo" | "ambiente" | null }>
  claude_instalado: boolean
  pode_alterar: boolean
  disponivel: boolean
  ultimo_erro: { motivo: string; em: string } | null
}

export const estado = () => pedir<EstadoIA>("GET", "/api/ia")

export interface EscolhaIA {
  provedor: string
  modelo?: string
  url_base?: string
  /** Só vai quando a pessoa digita; nunca volta do servidor. */
  chave?: string
}

export const salvar = (escolha: EscolhaIA) => pedir<EstadoIA>("PUT", "/api/ia", escolha)

/** Testa a conexão; a chave passada não é gravada. */
export const testar = (escolha: EscolhaIA) => pedir<{ ok: boolean; mensagem: string }>("POST", "/api/ia/testar", escolha)

export const removerChave = (provedor: string) =>
  pedir<EstadoIA & { aviso?: string }>("DELETE", `/api/ia/chave/${encodeURIComponent(provedor)}`)
