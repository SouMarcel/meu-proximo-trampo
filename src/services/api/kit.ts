/**
 * Kit da candidatura (dash/API.md §3.9): cartas, mensagens e respostas de formulário. Perguntas sensíveis
 * (autorização de trabalho, visto, salário, deficiência, relocação, diversidade) não vão para a IA.
 */
import { pedir } from "../api"
import type { EstadoGeracao, PontoConferencia } from "./curriculo"

export interface DocumentoCarta {
  nome: string
  tipo: "carta"
  formato: "carta" | "mensagem"
  limite?: number
  respostas?: { tom?: string } & Record<string, unknown>
  idioma?: string
  palavras?: number
  caracteres?: number
  conferencia?: { veredito?: "ok" | "conferir" | "bloquear"; pontos?: PontoConferencia[] }
  pronto?: boolean
  arquivos: { txt?: string; docx?: string | null }
  disponivel: { txt?: boolean; docx?: boolean }
  texto?: string
  criado_em: string
}

export interface ItemResposta {
  pergunta: string
  sensivel: string | null
  resposta: string
  da_pessoa: boolean
  conferir?: string[]
}

export interface DocumentoRespostas {
  nome: string
  tipo: "respostas"
  itens: ItemResposta[]
  arquivos: { txt?: string }
  disponivel: { txt?: boolean }
  criado_em: string
  atualizado_em?: string
}

export type Documento = DocumentoCarta | DocumentoRespostas

export interface RespostasCarta {
  formato: "carta" | "mensagem"
  tom: "direto" | "caloroso" | "formal"
  por_que: string
  problema: string
  primeiro_movimento: string
  limite?: number // 20-3000, padrão 400 (só mensagem)
  idioma?: string // pt, en, es, fr, de, it (só mensagem)
  /** As perguntas são opcionais; o que a pessoa escrever fica nos relatos dela (spec 035), padrão sim. */
  guardar_relatos?: boolean
}

export const lista = (vagaId: string) =>
  pedir<{ documentos: Documento[] }>("GET", `/api/kit/lista?vaga=${encodeURIComponent(vagaId)}`)

export const carta = (vagaId: string, respostas: RespostasCarta) =>
  pedir<EstadoGeracao>("POST", "/api/kit/carta", { vaga_id: vagaId, respostas })

/** perguntas: uma por linha, até 30. */
export const respostas = (vagaId: string, perguntas: string) =>
  pedir<EstadoGeracao>("POST", "/api/kit/respostas", { vaga_id: vagaId, perguntas })

/** As respostas escritas pela pessoa, pelo número da pergunta (a partir de 1); gravadas como ela escreveu. */
export const salvarRespostas = (nome: string, pessoa: Record<string, string>) =>
  pedir<{ documento: DocumentoRespostas }>("PUT", `/api/kit/respostas/${encodeURIComponent(nome)}`, { pessoa })
