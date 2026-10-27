/**
 * Tipos do servidor local (dash/servidor.py), copiados do contrato dash/API.md da ferramenta.
 * Regra: nenhum campo aqui que não esteja no dash/API.md. O que é só da tela fica em tipos à parte.
 */

// ---------- §2 Objeto vaga ----------

export type Plataforma =
  | "Indeed"
  | "LinkedIn"
  | "Gupy"
  | "InHire"
  | "Catho"
  | "Startup Jobs"
  | "Nerdin"
  | "InfoJobs"
  | "Vagas.com"
  | "JobGether"
  | "Remotive"
  | "Himalayas"
  | "RemoteOK"
  | "Jobicy"
  | "We Work Remotely"
  | "Get on Board"
  | "Greenhouse"
  | "Lever"
  | "Ashby"
  | "Outra"

export const PLATAFORMAS: Plataforma[] = [
  "Indeed",
  "LinkedIn",
  "Gupy",
  "InHire",
  "Catho",
  "Startup Jobs",
  "Nerdin",
  "InfoJobs",
  "Vagas.com",
  "JobGether",
  "Remotive",
  "Himalayas",
  "RemoteOK",
  "Jobicy",
  "We Work Remotely",
  "Get on Board",
  "Greenhouse",
  "Lever",
  "Ashby",
  "Outra",
]

export type Origem = "busca" | "link" | "manual"
export type Triagem = "pendente" | "seguir" | "visitada" | "fora"
export type Etapa = "salva" | "aplicada" | "entrevista" | "proposta" | "encerrada"
export type Resultado = "nao_aprovado" | "desisti" | "cancelada" | "contratado"
export type ModeloTrabalho = "remoto" | "hibrido" | "presencial" | "nao_informado"
export type Senioridade = "junior" | "pleno" | "senior"
export type Area = "nacional" | "internacional"
export type TipoEmprego = "tempo_integral" | "pj" | "meio_periodo" | "estagio" | "temporario"
export type AnaliseStatus = "pendente" | "feita" | "sem_dados" | "sem_analise"
export type EstadoKit = "a_fazer" | "pronto" | "nao_se_aplica"

export interface Frase {
  frase?: string
}

export interface Kit {
  estados?: Record<string, EstadoKit>
  extras?: string[]
  removidos?: string[]
}

export interface Lembretes {
  base?: string
  parar?: boolean
  follow1?: "feito" | "dispensado"
  follow2?: "feito" | "dispensado"
  agradecimento?: "feito" | "dispensado"
}

export interface ItemChecklist {
  item: string
  rotulo: string
  origem: "vaga" | "analise" | "anuncio" | "pessoa"
  estado: EstadoKit
  frase?: string
  acao: "curriculo" | "carta" | "respostas" | "candidatar" | null
  extra?: string // o texto do item que a pessoa acrescentou
  base?: { nome: string; url: string; idioma: string }
  falta_base?: "pt" | "en"
}

export interface LembretePendente {
  tipo: "follow1" | "follow2" | "agradecimento"
  rotulo: string
  desde: string
  base: string
}

export interface Vaga {
  // identidade e origem
  id: string // ^[A-Za-z0-9_.:-]{1,64}$
  origem?: Origem
  plataforma: Plataforma | string
  outras_plataformas?: string[]
  formato?: "post"
  busca_id?: string
  termos?: string[]
  grupos?: string[]
  encontrada_em?: string
  criada_em?: string
  atualizada_em?: string
  // anúncio
  titulo: string
  empresa: string
  local?: string
  url?: string
  url_candidatura?: string
  /** Candidatura assistida ligada nesta vaga (spec 027, chave por vaga). */
  candidatura_assistida?: { ligada: boolean; em: string }
  ats?: "greenhouse" | "lever" | "ashby"
  publicada_em?: string | null
  descricao?: string
  descricao_pendente?: boolean
  salario?: string
  moeda?: string
  idioma?: string
  tipo?: string
  remoto?: boolean
  modelo_trabalho?: ModeloTrabalho
  tipo_emprego?: TipoEmprego[]
  area?: Area
  pais_vaga?: string
  restricao_local?: string
  sinais?: string[]
  // triagem e quadro
  triagem: Triagem
  triada_em?: string | null
  motivo_fora?: string[]
  etapa: Etapa | null
  etapa_em?: string | null
  resultado?: Resultado | null
  entrevista_em?: string | null
  anotacao?: string // até 5.000
  email_candidatura?: string
  assunto_candidatura?: string
  kit?: Kit
  lembretes?: Lembretes
  curriculos?: string[]
  documentos?: { tipo: string; nome: string; criado_em: string }[]
  post_id?: string
  publicado_por?: string
  // análise
  analise_status?: AnaliseStatus
  aderencia?: number // 0-100
  nota_sem_descricao?: boolean
  resumo?: string
  encaixe?: string[]
  lacunas?: string[]
  alertas?: string[]
  senioridade?: Senioridade[]
  senioridade_origem?: "declarada" | "sugerida"
  analise_provedor?: string
  analise_modelo?: string
  analisada_em?: string
  autorizacao?: { valor: "patrocina" | "nao_precisa" | "omisso" | "nao_patrocina" } & Frase
  ingles?: { nivel: "nao_pede" | "basico" | "intermediario" | "fluente" | "nativo" } & Frase
  contratacao?: ({
    valor: "contractor" | "eor" | "empregado_brasil" | "relocation" | "clt" | "pj"
  } & Frase)[]
  fuso?: { texto: string } & Frase
  riscos?: ({ tipo: "remuneracao" | "remoto_hibrido" } & Frase)[]
  pede?: ({
    item: "curriculo_ingles" | "carta" | "formulario" | "portfolio" | "teste" | "video"
  } & Frase)[]
  sistema_candidatura?: string
  // calculados
  checklist?: ItemChecklist[]
  lembretes_pendentes?: LembretePendente[]
}

/** Campos que o PATCH /api/vagas/{id} aceita (§3.1). Outro campo = 400 "campo não editável". */
export interface CamposEditaveis {
  triagem?: Triagem
  etapa?: Etapa | null
  resultado?: Resultado | null
  etapa_em?: string | null
  triada_em?: string | null
  entrevista_em?: string | null
  anotacao?: string
  email_candidatura?: string
  assunto_candidatura?: string
  kit?: Kit
  lembretes?: Lembretes
}

// ---------- §1 e §3.13 ----------

export interface ErroApi extends Error {
  status: number // 0 = sem resposta (servidor fora do ar)
  dados: any
}

export interface Versao {
  versao: number
  analisando?: boolean
  ia_erro?: { motivo: string; em: string } | null
  busca?: { situacao: SituacaoBusca; origem?: string }
  verificando?: string[]
  falhas?: Record<string, { motivo: string; em: string }>
}

// ---------- §3.1 última busca ----------

export interface UltimaBusca {
  id?: string
  data?: string
  termos?: string[]
  brutas?: number
  avaliadas?: number
  fora_criterios?: number
  com_nota?: boolean
  fontes?: string[]
  janela_horas?: number
  resumo?: string
  consultas?: number
  excluidas_titulo?: number
  ja_vistas?: number
  candidatas?: number
  fortes?: number
  boas?: number
  parciais?: number
  baixas?: number
  origem?: string
  situacao?: string
}

// ---------- §3.2 adicionar vaga ----------

export interface InfoIA {
  disponivel: boolean
  local: boolean
  provedor: string
  modelo: string
}

export interface ParcialVaga {
  url?: string
  plataforma?: string
  formato?: "post"
  post_id?: string
  descricao?: string
  empresa?: string
  publicado_por?: string
  area?: Area
  pais_vaga?: string
  titulo?: string
  local?: string
}

export interface RespostaLink {
  vaga?: Vaga
  nova?: boolean
  analise_automatica?: boolean
  post?: { id: string; url: string; texto: string; autor?: string; autor_tipo?: string }
  parcial?: ParcialVaga
  ia?: InfoIA
  /** Link de vaga do Greenhouse, do Lever ou do Ashby: a empresa e se ela já é acompanhada (spec 031). */
  empresa?: { sistema: string; id: string; nome: string; url: string; acompanhada: boolean }
}

export interface CamposExtraidos {
  campos: {
    titulo?: string
    empresa?: string
    local?: string
    url?: string
    email_candidatura?: string
    assunto_candidatura?: string
  }
  parece_vaga: boolean
  vagas: number
  provedor: string
  modelo: string
}

export interface NovaVaga {
  titulo: string
  empresa: string
  plataforma?: string
  url?: string
  local?: string
  descricao?: string // até 20.000
  etapa?: "relatorio" | Etapa
  area?: Area
  pais_vaga?: string
  email_candidatura?: string
  assunto_candidatura?: string
  formato?: "post"
  post_id?: string
  publicado_por?: string
}

export interface RespostaNovaVaga {
  vaga: Vaga
  nova: boolean
  analise_automatica?: boolean
}

// ---------- §3.3 busca e descrições pendentes ----------

export type SituacaoBusca =
  | "ociosa"
  | "consultando"
  | "descricoes"
  | "gravando"
  | "cancelando"
  | "concluida"
  | "cancelada"
  | "falha"
  | "interrompida"
  | "externa"

export interface EsperaPortal {
  portal: string
  ate: string
  motivo: string
}

export interface CobrancaIA {
  ligada: boolean
  nome: string
  modelo: string
  cobranca: "uso" | "assinatura" | "gratuito" | ""
}

export interface PlanoBusca {
  filtros_ok: boolean
  perfil_ok: boolean
  consultas: number
  portais: string[]
  cargos: string[]
  janela_horas: number
  resumo: string
  estimativa_min: number
  ia: CobrancaIA
  ultima: { origem?: string; situacao?: string; inicio?: string; fim?: string } | null
  proxima_em: string | null
  recente: boolean
  espera: EsperaPortal[]
  so_espera: boolean
  aviso_cargos?: string
  aviso_pausa?: string
}

export interface EstadoBusca {
  situacao: SituacaoBusca
  origem?: string
  inicio?: string
  fim?: string
  com_nota?: boolean
  feitas?: number
  total?: number
  encontradas?: number
  consulta?: { portal: string; cargo: string; grupo?: string } | null
  descricoes?: { lidas: number; total: number } | null
  erros?: string[]
  mensagem?: string
  resumo?: {
    brutas: number
    novas: number
    fora_criterios: number
    ja_vistas: number
    excluidas_titulo: number
    fora_da_janela: number
    busca_id?: string
    com_nota: boolean
    pendentes?: number
    completadas?: number
  } | null
  analise?: { rodando: boolean; faltam: number; erro: { motivo: string; em: string } | null }
  pode_alterar?: boolean
}

export interface EstadoPendentes {
  situacao: "parada" | "lendo" | "pronta" | "erro"
  lidas?: number
  total?: number
  inicio?: string
  completadas?: number
  restantes?: number
  erros?: string[]
  fim?: string
  mensagem?: string
  pendentes?: number
  espera?: EsperaPortal[]
  pode_alterar?: boolean
}
