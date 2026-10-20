/** Análises do perfil (dash/API.md §3.7): todas só no clique; ficam salvas com a data. */
import { pedir } from "../api"
import type { Filtros } from "./config"

export interface ItemLacuna {
  rotulo: string
  termos: string[]
  variacoes: string[]
  peso: number
  parte: number
  nivel: "critica" | "alta" | "media"
  vagas: number
  exemplos: { id: string; titulo: string; empresa: string }[]
}

export interface Lacunas {
  visao: "todas" | "seguidas"
  vagas: number
  faltam?: number
  itens: ItemLacuna[]
  data?: string
}

export interface Plano {
  itens: { lacuna: string; passos: string[]; semanas: number }[]
  ia?: { provedor: string; modelo: string }
  data?: string
}

export interface Cargo {
  titulo: string
  titulo_en: string
  tipo: "lateral" | "degrau" | "vizinho"
  evidencia: string
  lacuna: string
  conferir: boolean
}

export interface Cargos {
  itens: Cargo[]
  avisos?: string[]
  data?: string
}

export interface ItemProntidao {
  item: string
  rotulo: string
  situacao: "pronto" | "falta" | "nao_informado"
  origem: string
  detalhe: string
  acao: "perfil" | "filtros_int" | "curriculo" | "marcar"
}

export interface Analises {
  salvas: { lacunas?: Lacunas; plano?: Plano; cargos?: Cargos; marcas?: { linkedin_en?: boolean } }
  prontidao: ItemProntidao[]
  ia: boolean
  existe_perfil: boolean
  pode_alterar: boolean
}

export const ler = () => pedir<Analises>("GET", "/api/analises-perfil")

export const lacunas = (visao: "todas" | "seguidas") => pedir<Lacunas>("POST", "/api/analises-perfil/lacunas", { visao })

export const plano = () => pedir<Plano>("POST", "/api/analises-perfil/plano", {})

export const cargos = () => pedir<Cargos>("POST", "/api/analises-perfil/cargos", {})

export const cargosParaFiltros = (escolhidos: { titulo: string; titulo_en: string }[], confirmar = false) =>
  pedir<{ filtros: Filtros; mudancas: { campo: string; atual?: unknown; proposto?: string[] }[]; gravado: boolean }>(
    "POST",
    "/api/analises-perfil/cargos/filtros",
    { cargos: escolhidos, ...(confirmar ? { confirmar: true } : {}) },
  )

export const marcar = (linkedinEn: boolean) =>
  pedir<{ marcas: { linkedin_en: boolean } }>("PUT", "/api/analises-perfil/marcas", { linkedin_en: linkedinEn })
