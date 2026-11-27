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

export type TipoEmail = "recebida" | "entrevista" | "proposta" | "negativa" | "cancelada" | "desistencia" | "contratacao"

export const TIPOS_EMAIL: { valor: TipoEmail; rotulo: string }[] = [
  { valor: "recebida", rotulo: "candidatura recebida" },
  { valor: "entrevista", rotulo: "convite para entrevista ou teste" },
  { valor: "proposta", rotulo: "proposta" },
  { valor: "negativa", rotulo: "negativa" },
  { valor: "cancelada", rotulo: "vaga cancelada" },
  { valor: "desistencia", rotulo: "desistência" },
  { valor: "contratacao", rotulo: "contratação" },
]

export interface VagaOpcao {
  id: string
  titulo: string
  empresa: string
  etapa: string
}

export interface ItemEmail extends Omit<ItemCandidatura, "portal" | "plataforma" | "tipo" | "para"> {
  portal: "email"
  plataforma: "E-mail"
  tipo: "mudar" | "quadro" | "anotar" | "escolher" | "nao_reconhecido"
  para: ItemCandidatura["para"] | null
  tipo_email: TipoEmail | null
  rotulo: string
  trecho: string
  opcoes: VagaOpcao[]
  alerta: { veredito: string } | null
  por_ia: boolean
}

export interface LeituraEmail {
  itens: ItemEmail[]
  ia: { usada: boolean; nome: string | null; erro: string | null }
  lidas_em: string
}

export const lerEmails = (emails: string[]) => pedir<LeituraEmail>("POST", "/api/candidaturas/email/ler", { emails })
export const aplicarEmails = (itens: { chave: string; vaga_id?: string; tipo_email?: string }[]) =>
  pedir<{ aplicados: number; anotados: number; erros: string[] }>("POST", "/api/candidaturas/email/aplicar", { itens })
export const vagasParaEscolher = (q: string) =>
  pedir<{ vagas: VagaOpcao[] }>("GET", `/api/candidaturas/email/vagas?q=${encodeURIComponent(q)}`)
