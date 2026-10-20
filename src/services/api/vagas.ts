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
