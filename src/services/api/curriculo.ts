/** Currículo por vaga e currículo base (dash/API.md §3.8). Uma geração por vez (currículo, carta ou respostas). */
import { pedir } from "../api"

export interface Catalogo {
  tecnicas: Record<string, { nome: string; padrao: boolean; explicacao: string }>
  escolhas: Record<string, { nome: string; padrao: string | number; opcoes: Record<string, string> }>
  sugestao: Record<string, unknown> & { motivo?: string }
  ia: { ligada: boolean; nome: string; modelo: string; cobranca: "uso" | "assinatura" | "gratuito" | "" }
  perfil_ok: boolean
  pode_alterar: boolean
  /** Só com vaga: o checkbox Análise de reprovação (spec 049); anterior = data da análise que será substituída. */
  reprovacao?: { disponivel: boolean; motivo: string; anterior: string | null }
}

export type SituacaoGeracao =
  | "ociosa"
  | "analisando"
  | "reescrevendo"
  | "escrevendo"
  | "gerando"
  | "conferindo"
  | "pronto"
  | "falha"

export interface EstadoGeracao {
  situacao: SituacaoGeracao
  tipo?: "curriculo" | "carta" | "respostas" | "verificar" | "reprovacao"
  alvo?: { vaga_id?: string; titulo?: string; empresa?: string; base?: boolean }
  tecnicas?: Record<string, unknown>
  inicio?: string
  fim?: string
  nome?: string
  mensagem?: string
  veredito?: "ok" | "conferir" | "bloquear"
  pronto?: boolean
  pode_tentar?: boolean
  etapa_texto?: string
  pode_alterar?: boolean
}

export interface PontoConferencia {
  nivel: string
  mensagem: string
  valor?: string
  trecho?: string
}

export interface MetaCurriculo {
  nome: string
  alvo: unknown
  tecnicas: Record<string, unknown> & { formato?: string; estilo?: string; paginas?: number }
  arquivos: { json?: string; docx?: string; pdf?: string | null }
  disponivel: { pdf?: boolean; docx?: boolean; json?: boolean }
  paginas: number | null
  acima_do_limite?: boolean
  sugestoes_corte?: string[]
  conferencia: {
    veredito?: "ok" | "conferir" | "bloquear"
    fatos?: PontoConferencia[]
    ats?: PontoConferencia[]
    requisitos?: { situacao: string; texto: string }[]
    cobertura?: { achadas: number; total: number; faltando: string[] } | null
  }
  pronto?: boolean
  /** A IA que escreveu; com reserva, o aviso de qual falhou e por quê (spec 032). */
  ia?: { provedor: string; modelo: string; reserva?: boolean; aviso?: string }
  /** Saiu da análise de reprovação (spec 049). */
  reprovacao?: boolean
  criado_em: string
}

// ---------- análise de reprovação (spec 049) ----------

export type GrupoReprovacao =
  | "requisito_nao_comprovado"
  | "experiencia_generica"
  | "competencia_sem_evidencia"
  | "resultado_pouco_claro"
  | "informacao_ausente"

export interface MotivoReprovacao {
  i: number
  grupo: GrupoReprovacao
  motivo: string
  /** null = não aparece no currículo. */
  trecho_cv: string | null
  /** false = o trecho citado não foi achado no currículo analisado. */
  trecho_ok: boolean
  trecho_vaga: string
  perguntas: number[]
  sensivel: boolean
  estado: "nao_tenho" | "tenho" | "sem_resposta" | "sem_pergunta"
}

export interface PerguntaReprovacao {
  n: number
  texto: string
}

export interface RespostaReprovacao {
  resposta: "nao" | "tenho" | "pular"
  relato?: string
  destino?: "perfil" | "so_aqui"
  /** Id do relato quando já foi para o perfil: o destino não muda mais. */
  levado?: string
}

export interface Reescrito {
  original: string
  novo: string
  motivos: number[]
  avisos: string[]
}

export interface Reprovacao {
  vaga: { id: string; titulo: string; empresa: string }
  criada_em: string
  tecnicas: Record<string, unknown>
  curriculo_analisado: { tipo: "vaga" | "base_arquivo" | "base_gerado" | "perfil"; nome: string | null; rotulo: string }
  avisos: string[]
  motivos: MotivoReprovacao[]
  perguntas: PerguntaReprovacao[]
  respostas: Record<string, RespostaReprovacao>
  respostas_em: string | null
  reescritos: Reescrito[]
  curriculo_gerado: string | null
  gerado_em: string | null
  levados: string[]
  resumo: { nao_tenho: number; tenho: number; sem_resposta: number }
  pronta_para_gerar: boolean
  respostas_mudaram: boolean
  grupos: Record<GrupoReprovacao, string>
}

export const SITUACOES_ATIVAS: SituacaoGeracao[] = ["analisando", "reescrevendo", "escrevendo", "gerando", "conferindo"]

const consulta = (vagaId: string | null) => (vagaId ? `?vaga=${encodeURIComponent(vagaId)}` : "")

export const catalogo = (vagaId: string | null) => pedir<Catalogo>("GET", `/api/curriculo/catalogo${consulta(vagaId)}`)

export const gerar = (vagaId: string | null, tecnicas: Record<string, unknown>) =>
  pedir<EstadoGeracao>("POST", "/api/curriculo", { vaga_id: vagaId, tecnicas })

export const tentar = () => pedir<EstadoGeracao>("POST", "/api/curriculo/tentar", {})

export const estado = () => pedir<EstadoGeracao>("GET", "/api/curriculo/estado")

/** "Gerar" com o checkbox Análise de reprovação: só a análise; o currículo espera as respostas. */
export const reprovacao = (vagaId: string, tecnicas: Record<string, unknown>) =>
  pedir<EstadoGeracao>("POST", "/api/curriculo/reprovacao", { vaga_id: vagaId, tecnicas })

export const obterReprovacao = (vagaId: string) =>
  pedir<{ analise: Reprovacao | null; pode_alterar: boolean }>("GET", `/api/curriculo/reprovacao${consulta(vagaId)}`)

export const gravarRespostasReprovacao = (vagaId: string, respostas: Record<string, RespostaReprovacao>) =>
  pedir<{ analise: Reprovacao }>("PUT", `/api/curriculo/reprovacao/${encodeURIComponent(vagaId)}/respostas`, { respostas })

/** Reescrever e gerar o currículo com as respostas da análise. */
export const gerarComReprovacao = (vagaId: string) =>
  pedir<EstadoGeracao>("POST", `/api/curriculo/reprovacao/${encodeURIComponent(vagaId)}/gerar`, {})

export const lista = (vagaId: string | null) =>
  pedir<{ curriculos: MetaCurriculo[] }>("GET", `/api/curriculo/lista${vagaId ? `?vaga=${encodeURIComponent(vagaId)}` : "?base=1"}`)
