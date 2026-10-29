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

/** Área do material (spec 037): sai do tipo; o arquivo vale como a área em que foi enviado ou para onde foi movido. */
export type AreaMaterial = "linkedin" | "curriculo" | "documento"

export interface Material {
  id: string
  tipo: "curriculo_pdf" | "curriculo_docx" | "linkedin_pdf" | "linkedin_zip" | "texto" | "documento_pdf" | "documento_docx"
  nome: string
  avisos: string[]
  trecho: string
  tem_texto: boolean
  arquivo: string
  area: AreaMaterial
  /** O aviso de área trocada: a ferramenta só sugere, quem move é a pessoa. */
  sugestao: { area: AreaMaterial; motivo: string } | null
  /** O texto veio do OCR do Windows (PDF só de imagem). */
  ocr: boolean
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
  /** Pergunta de idiomas (spec 036): as opções de idioma, sem "Outro" (que é da página). */
  idiomas?: string[]
  /** Níveis do CEFR (A1 a C2) e Nativo; o `rotulo` vai no texto gravado ("Inglês — B2 (Intermediário superior)"). */
  niveis?: NivelIdioma[]
  /** As respostas já dadas (ou os idiomas do currículo), convertidas em linhas; nível vazio = escolher. */
  linhas?: LinhaIdioma[]
}

export interface NivelIdioma {
  valor: string
  rotulo: string
  descricao: string
}

export interface LinhaIdioma {
  /** Um dos `idiomas` ou "Outro". */
  idioma: string
  /** Nome do idioma quando `idioma` é "Outro". */
  outro: string
  nivel: string
  /** O texto antigo, quando o nível ou o idioma não foi reconhecido (só para mostrar). */
  original: string
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
  /** O OCR do Windows está disponível (botão OCR nos PDFs sem texto). */
  ocr_disponivel?: boolean
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

export const enviarMaterial = (corpo: { nome: string; base64?: string; texto?: string; area?: AreaMaterial }) =>
  pedir<{ material: Material; estado: EstadoPerfil }>("POST", "/api/perfil/material", corpo)

/** Mover para (spec 037): só a área muda; `aviso` quando o arquivo era o Seu currículo e a marcação saiu. */
export const moverMaterial = (id: string, area: AreaMaterial) =>
  pedir<{ estado: EstadoPerfil; aviso: string | null }>("PUT", `/api/perfil/material/${encodeURIComponent(id)}`, { area })

/** Botão OCR (spec 037): lê de novo o PDF que ficou sem texto, com o OCR do Windows. */
export const ocrMaterial = (id: string) =>
  pedir<{ material: Material; estado: EstadoPerfil }>("POST", `/api/perfil/material/${encodeURIComponent(id)}/ocr`, {})

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

/** Relato da pessoa (spec 035): o que ela contou com as próprias palavras na candidatura assistida; vale como fato. */
export interface Relato {
  id: string
  pergunta: string
  relato: string
  resposta: string
  vaga: { id: string; titulo: string; empresa: string } | null
  em: string
  no_perfil: boolean
}

export const relatos = () => pedir<{ relatos: Relato[] }>("GET", "/api/perfil/relatos")
export const editarRelato = (id: string, relato: string) =>
  pedir<{ relatos: Relato[] }>("PUT", `/api/perfil/relatos/${encodeURIComponent(id)}`, { relato })
export const apagarRelato = (id: string) =>
  pedir<{ relatos: Relato[] }>("DELETE", `/api/perfil/relatos/${encodeURIComponent(id)}`, {})
export const levarRelatoAoPerfil = (id: string) =>
  pedir<{ relatos: Relato[]; anterior: string | null }>("POST", `/api/perfil/relatos/${encodeURIComponent(id)}/perfil`, {})
