/**
 * Contas conectadas e candidaturas (dash/API.md §3.11). Só leitura da área logada da Gupy e do Indeed, numa janela
 * do navegador da própria ferramenta, com o login feito pela pessoa; nada é gravado até ela aplicar o que marcou.
 */
import { pedir } from "../api"
import type { Etapa, Resultado } from "../../types/api"

export interface Portal {
  nome: string
  plataforma: string
  icone: string // SVG do código do servidor
  conectado: boolean
  aviso_login: string
}

export interface Contas {
  navegador: boolean
  ultima: string | null
  portais: Portal[]
}

export interface ItemCandidatura {
  chave: string
  portal: string
  plataforma: string
  tipo: "mudar" | "quadro" | "nova" | "historico"
  vaga_id: string | null
  titulo: string
  empresa: string
  de: { etapa: Etapa | null; resultado: Resultado | null } | null
  para: { etapa: Etapa | null; resultado: Resultado | null }
  status: string
  nota: string
  avisos: string[]
  data: string
  url: string
  marcado: boolean
}

export interface EstadoCandidaturas {
  situacao: "parada" | "lendo" | "aguardando_login" | "pronta"
  portal?: string
  inicio?: string
  fim?: string
  resultado: {
    itens: ItemCandidatura[]
    historico: ItemCandidatura[]
    sem_mudanca: number
    erros: Record<string, string>
    lidas_em: string
  } | null
}

const p = (nome: string) => encodeURIComponent(nome)

export const contas = () => pedir<Contas>("GET", "/api/contas")
export const estado = () => pedir<EstadoCandidaturas>("GET", "/api/candidaturas/estado")
export const conectar = (portal: string) => pedir<{ ok: boolean }>("POST", `/api/contas/${p(portal)}/conectar`, {})
export const pronto = (portal: string) => pedir<{ conectado: boolean }>("POST", `/api/contas/${p(portal)}/pronto`, {})
export const desconectar = (portal: string) => pedir<{ ok: boolean }>("POST", `/api/contas/${p(portal)}/desconectar`, {})
export const ler = () => pedir<EstadoCandidaturas>("POST", "/api/candidaturas/ler", {})
export const aplicar = (corpo: { chaves: string[] } | { historico: true }) =>
  pedir<{ aplicados: number; erros: string[] }>("POST", "/api/candidaturas/aplicar", corpo)

export const ATIVAS = ["lendo", "aguardando_login"]
