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

/** Reserva (spec 032): tentada, na ordem, quando a IA principal falha. A chave só vai quando a pessoa digita. */
export interface ReservaIA {
  provedor: string
  modelo?: string
  url_base?: string
  chave?: string
}

/** Último sucesso ou falha de uma IA, com hora ("AAAA-MM-DDTHH:MM") e motivo. */
export interface SituacaoIA {
  ok: boolean
  em: string
  motivo: string
}

export interface ItemSequencia {
  provedor: string
  nome: string
  modelo: string
  url_base: string
  gratuito: boolean
  chave_ok: boolean
  principal: boolean
  situacao: SituacaoIA | null
}

/** A IA principal falhou na última tentativa. */
export interface AlertaIA {
  nome: string
  modelo: string
  motivo: string
  em: string
}

export interface EstadoIA {
  escolha: { provedor: string; modelo: string; url_base: string; reservas?: ReservaIA[] } | null
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
  /** A principal e as reservas, com a situação de cada uma (spec 032). */
  sequencia?: ItemSequencia[]
  alerta?: AlertaIA | null
}

export const estado = () => pedir<EstadoIA>("GET", "/api/ia")

export interface EscolhaIA {
  provedor: string
  modelo?: string
  url_base?: string
  /** Só vai quando a pessoa digita; nunca volta do servidor. */
  chave?: string
  /** Vazia apaga as reservas; ausente mantém as gravadas. */
  reservas?: ReservaIA[]
}

export const salvar = (escolha: EscolhaIA) => pedir<EstadoIA>("PUT", "/api/ia", escolha)

/** Testa a conexão; a chave passada não é gravada. */
export const testar = (escolha: EscolhaIA) => pedir<{ ok: boolean; mensagem: string }>("POST", "/api/ia/testar", escolha)

export const removerChave = (provedor: string) =>
  pedir<EstadoIA & { aviso?: string }>("DELETE", `/api/ia/chave/${encodeURIComponent(provedor)}`)
