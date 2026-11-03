/** O que as vagas pedem (spec 045, dash/API.md): o resumo da seleção e a leitura dos requisitos pela IA. */
import { pedir } from "../api"
import type { SelecaoRequisitos } from "../storage"

/** Como o item aparece no perfil da pessoa (comparação por nome, sem IA). */
export type MarcaPerfil = "habilidade" | "certificacao" | "citada" | "nao"

export interface ItemPedido {
  nome: string
  chave: string
  tipo: string
  vagas: number
  exigida: number
  parte: number
  perfil: MarcaPerfil
  ids: string[]
}

export interface Contado {
  rotulo: string
  vagas: number
  ids: string[]
}

export interface EstadoLeitura {
  rodando: boolean
  lidas: number
  total: number
  parada: boolean
  erro: { motivo: string; em: string } | null
  selecao: SelecaoRequisitos | null
}

export interface LinhaSua {
  linha: string
  nivel: string
  vagas: number
  destaque: boolean
  ids: string[]
}

export interface ResumoRequisitos {
  selecao: SelecaoRequisitos
  contagem: { selecao: number; com_requisitos: number; a_ler: number; sem_texto: number; sem_analise: number }
  poucas: boolean
  habilidades: { base: number; tecnicas: ItemPedido[]; comportamentais: ItemPedido[] }
  certificacoes: { base: number; itens: ItemPedido[] }
  experiencia: { base: number; destaque: string | null; faixas: (Contado & { faixa: string })[] }
  formacao: {
    base: number
    niveis: (Contado & { nivel: string })[]
    areas: { nome: string; vagas: number; ids: string[] }[]
  }
  idiomas: {
    base: number
    itens: { idioma: string; vagas: number; ids: string[]; niveis: (Contado & { nivel: string })[] }[]
  }
  senioridade: { base: number; itens: (Contado & { valor: string })[] }
  modelo: { base: number; itens: (Contado & { valor: string })[] }
  contratacao: { base: number; itens: (Contado & { valor: string })[] }
  suas: {
    existe_perfil: boolean
    tem_secao: boolean
    habilidades: LinhaSua[]
    certificacoes: LinhaSua[]
    aparecem: number
    total: number
  }
  leitura: EstadoLeitura
  ia: { ligada: boolean; nome: string }
}

export const resumo = (s: SelecaoRequisitos) =>
  pedir<ResumoRequisitos>(
    "GET",
    `/api/requisitos?vagas=${encodeURIComponent(s.vagas)}&area=${encodeURIComponent(s.area)}`,
  )

export const ler = (s: SelecaoRequisitos) => pedir<{ leitura: EstadoLeitura }>("POST", "/api/requisitos/ler", s)

export const parar = () => pedir<{ leitura: EstadoLeitura }>("POST", "/api/requisitos/parar", {})
