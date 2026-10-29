/** Currículo por vaga e currículo base (dash/API.md §3.8). Uma geração por vez (currículo, carta ou respostas). */
import { pedir } from "../api"

export interface Catalogo {
  tecnicas: Record<string, { nome: string; padrao: boolean; explicacao: string }>
  escolhas: Record<string, { nome: string; padrao: string | number; opcoes: Record<string, string> }>
  sugestao: Record<string, unknown> & { motivo?: string }
  ia: { ligada: boolean; nome: string; modelo: string; cobranca: "uso" | "assinatura" | "gratuito" | "" }
  perfil_ok: boolean
  pode_alterar: boolean
}

export type SituacaoGeracao = "ociosa" | "escrevendo" | "gerando" | "conferindo" | "pronto" | "falha"

export interface EstadoGeracao {
  situacao: SituacaoGeracao
  tipo?: "curriculo" | "carta" | "respostas" | "verificar"
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
  criado_em: string
}

export const SITUACOES_ATIVAS: SituacaoGeracao[] = ["escrevendo", "gerando", "conferindo"]

const consulta = (vagaId: string | null) => (vagaId ? `?vaga=${encodeURIComponent(vagaId)}` : "")

export const catalogo = (vagaId: string | null) => pedir<Catalogo>("GET", `/api/curriculo/catalogo${consulta(vagaId)}`)

export const gerar = (vagaId: string | null, tecnicas: Record<string, unknown>) =>
  pedir<EstadoGeracao>("POST", "/api/curriculo", { vaga_id: vagaId, tecnicas })

export const tentar = () => pedir<EstadoGeracao>("POST", "/api/curriculo/tentar", {})

export const estado = () => pedir<EstadoGeracao>("GET", "/api/curriculo/estado")

export const lista = (vagaId: string | null) =>
  pedir<{ curriculos: MetaCurriculo[] }>("GET", `/api/curriculo/lista${vagaId ? `?vaga=${encodeURIComponent(vagaId)}` : "?base=1"}`)
