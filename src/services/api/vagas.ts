/** Vagas, quadro e Adicionar vaga (dash/API.md §3.1, §3.2 e §3.13). */
import { pedir } from "../api"
import type {
  CamposEditaveis,
  CamposExtraidos,
  NovaVaga,
  RespostaLink,
  RespostaNovaVaga,
  UltimaBusca,
  Vaga,
  Versao,
} from "../../types/api"

const id = (v: string) => encodeURIComponent(v)

export const versao = () => pedir<Versao>("GET", "/api/versao", undefined, { timeoutMs: 2500 })

export const listar = () => pedir<{ versao: number; vagas: Vaga[] }>("GET", "/api/vagas")

export const ultimaBusca = () => pedir<{ busca: UltimaBusca | null }>("GET", "/api/buscas/ultima")

export const atualizar = (vagaId: string, campos: CamposEditaveis) =>
  pedir<{ vaga: Vaga }>("PATCH", `/api/vagas/${id(vagaId)}`, campos)

export const remover = (vagaId: string) => pedir<{ ok: boolean }>("DELETE", `/api/vagas/${id(vagaId)}`)

export const analisar = (vagaId: string) =>
  pedir<{ verificando: string[] }>("POST", `/api/vagas/${id(vagaId)}/analisar`, {})

export const porLink = (url: string) => pedir<RespostaLink>("POST", "/api/vagas/link", { url })

export const extrair = (texto: string, autor?: string, autor_tipo?: string) =>
  pedir<CamposExtraidos>("POST", "/api/vagas/extrair", { texto, autor, autor_tipo })

export const criar = (campos: NovaVaga) => pedir<RespostaNovaVaga>("POST", "/api/vagas", campos)

/** Faixa salarial (dash/API.md §3.1b; spec 028): só números com fonte e links para a pessoa pesquisar. */
export interface ValorSalario {
  min: number
  max: number
  moeda: string | null
  periodo: "mes" | "ano" | "hora" | "dia" | "semana"
  mensal_min: number
  mensal_max: number
}

export interface FaixaSalarial {
  vaga: { id: string; titulo: string; empresa: string; salario: string; valor: ValorSalario | null }
  moeda: string | null
  parecidas: (ValorSalario & { id: string; titulo: string; empresa: string; plataforma: string; salario: string; url: string; semelhanca: number })[]
  resumo: { n: number; moeda: string | null; minimo: number; maximo: number; mediana: number | null } | null
  pesquisas: { texto: string; fonte: string; em: string }[]
  links: { rotulo: string; url: string }[]
  conversao: string
}

export const salario = (vagaId: string) => pedir<FaixaSalarial>("GET", `/api/vagas/${id(vagaId)}/salario`)
export const anotarSalario = (vagaId: string, texto: string, fonte: string) =>
  pedir<FaixaSalarial>("POST", `/api/vagas/${id(vagaId)}/salario`, { texto, fonte })
export const apagarSalario = (vagaId: string, indice: number) =>
  pedir<FaixaSalarial>("DELETE", `/api/vagas/${id(vagaId)}/salario/${indice}`, {})
