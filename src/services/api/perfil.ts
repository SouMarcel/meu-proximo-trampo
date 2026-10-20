/** Meu perfil / Primeiros passos e "Já tenho currículo" (dash/API.md §3.6). Nada vai para o perfil.md sem PUT /api/perfil. */
import { pedir } from "../api"
import type { Filtros } from "./config"

export type EtapaPerfil =
  | "ia"
  | "materiais"
  | "rascunho"
  | "conflitos"
  | "anamnese"
  | "diagnostico"
  | "revisao"
  | "filtros"
  | "concluido"

export interface Material {
  id: string
  tipo: "curriculo_pdf" | "curriculo_docx" | "linkedin_pdf" | "linkedin_zip" | "texto"
  nome: string
  avisos: string[]
  trecho: string
  tem_texto: boolean
  arquivo: string
}

export interface ItemComFonte {
  texto: string
  fonte?: string
}

export interface Rascunho {
  objetivo: ItemComFonte[]
  resumo: ItemComFonte[]
  formacao: ItemComFonte[]
  certificacoes: ItemComFonte[]
  habilidades: ItemComFonte[]
  idiomas: ItemComFonte[]
  experiencias: { cargo: string; empresa: string; inicio: string; fim: string; itens: ItemComFonte[]; fonte?: string }[]
  conflitos: { campo: string; opcoes: { valor: string; fonte?: string }[]; escolha: number | null }[]
  origem: "ia" | "sem_ia"
}

export interface Pergunta {
  id: string
  tipo: "texto" | "lista" | "multi" | "opcoes" | "sim_nao"
  texto: string
  opcoes?: { valor: string; rotulo: string }[]
  condicao?: string
}

export interface Contato {
  email?: string
  telefone?: string
  linkedin?: string
}

export interface EstadoPerfil {
  existe_perfil: boolean
  perfil_do_curriculo: { arquivo: string; data: string } | null
  etapa: EtapaPerfil
  materiais: Material[]
  rascunho: Rascunho | null
  respostas: Record<string, any>
  contato: Contato
  contatos_achados: { emails?: string[]; telefones?: string[]; linkedin?: string }
  perguntas: Pergunta[]
  ia_disponivel: boolean
  pode_alterar: boolean
}

export interface Previa {
  markdown: string
  diagnostico: { tipo: "falta" | "fraco" | "info"; mensagem: string; pergunta: string; ir: string }[]
  textos: { nome: string; texto: string }[]
  diferencas: { tipo: "+" | "-"; texto: string }[] | null
  conflitos_pendentes?: number
}

export interface FiltrosPropostos {
  filtros: Filtros
  mudancas: { campo: string; atual: unknown; proposto: unknown }[]
  avisos: string[]
  sugestao_en?: boolean | string[]
}

export interface CurriculosDaPasta {
  curriculos: { arquivo: string; nome: string; idioma: "pt" | "en" | null; data: string }[]
  curriculo_base: { pt: string | null; en: string | null }
  existe_perfil: boolean
}

export interface PropostaDoCurriculo {
  arquivo: string
  nome: string
  texto: string
  idioma: "pt" | "en"
  avisos: string[]
  perfil: string
  dados: { origem?: string } & Record<string, unknown>
  edicao: { cargos: string[]; cargos_en: string[]; cidade: string; estado: string; modelos: string[] }
  filtros: Filtros | null
  mudancas: unknown[]
  existe_perfil: boolean
  curriculo_base: { pt: string | null; en: string | null }
  ja_marcado: boolean
}

export const estado = () => pedir<EstadoPerfil>("GET", "/api/perfil/estado")

export const progresso = (corpo: {
  etapa?: EtapaPerfil
  respostas?: Record<string, unknown>
  escolhas?: Record<string, number>
  contato?: Contato
}) => pedir<EstadoPerfil>("PUT", "/api/perfil/progresso", corpo)

export const recomecar = () => pedir<EstadoPerfil>("DELETE", "/api/perfil/progresso")

export const enviarMaterial = (corpo: { nome: string; base64?: string; texto?: string }) =>
  pedir<{ material: Material; estado: EstadoPerfil }>("POST", "/api/perfil/material", corpo)

export const removerMaterial = (id: string) =>
  pedir<EstadoPerfil>("DELETE", `/api/perfil/material/${encodeURIComponent(id)}`)

export const rascunho = (semIA: boolean) => pedir<EstadoPerfil>("POST", "/api/perfil/rascunho", { sem_ia: semIA })

export const previa = (markdown?: string | null) =>
  pedir<Previa>("POST", "/api/perfil/previa", markdown == null ? {} : { markdown })

export const gravar = (markdown: string) =>
  pedir<{ gravado: string; anterior: string | null }>("PUT", "/api/perfil", { markdown })

export const filtrosPropostos = () => pedir<FiltrosPropostos>("GET", "/api/perfil/filtros-propostos")

export const sugerirCargosEn = () => pedir<FiltrosPropostos>("POST", "/api/perfil/filtros-propostos", { sugerir_en: true })

export const curriculos = () => pedir<CurriculosDaPasta>("GET", "/api/perfil/curriculos")

export const doCurriculo = (arquivo: string) => pedir<PropostaDoCurriculo>("POST", "/api/perfil/do-curriculo", { arquivo })

export const confirmarCurriculo = (corpo: {
  arquivo: string
  idioma: string
  manter_perfil: boolean
  marcar_base: boolean
  perfil: string
  edicao?: { cargos: string[]; cargos_en: string[]; cidade: string; estado: string; modelos: string[] }
}) => pedir<{ perfil: string; anterior: string | null; filtros: Filtros | null }>("POST", "/api/perfil/do-curriculo/confirmar", corpo)

export const marcarCurriculoBase = (idioma: "pt" | "en", arquivo: string | null) =>
  pedir<{ curriculo_base: { pt: string | null; en: string | null } }>("PUT", "/api/curriculo-base", { idioma, arquivo })
