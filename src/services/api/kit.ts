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
  conferencia?: {
    veredito?: "ok" | "conferir" | "bloquear"
    pontos?: PontoConferencia[]
    /** Requisitos da vaga que o perfil sustenta e quantos a carta usa (ATS, spec 035). */
    palavras_chave?: { citadas: number; total: number; faltando: string[] }
  }
  pronto?: boolean
  arquivos: { txt?: string; docx?: string | null; pdf?: string | null }
  disponivel: { txt?: boolean; docx?: boolean; pdf?: boolean }
  /** Sem os dados de contato salvos, a carta sai sem cabeçalho e sem o nome na despedida (spec 035). */
  aviso_cabecalho?: string
  /** Por que o PDF não saiu (sem LibreOffice nem Word, arquivo aberto…); "Gerar PDF" tenta de novo. */
  aviso_pdf?: string
  texto?: string
  criado_em: string
  /** "verificada": versão revisada pela IA a partir da edição da pessoa (botão Verificar, spec 035). */
  origem?: "verificada"
  base?: string
  mudancas?: string[]
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

/** A carta editada pela pessoa: a IA incorpora as mudanças, corrige a língua e grava uma versão nova (spec 035). */
export const verificar = (vagaId: string, nome: string, texto: string, guardar_relatos = true) =>
  pedir<EstadoGeracao>("POST", "/api/kit/verificar", { vaga_id: vagaId, nome, texto, guardar_relatos })

/** O PDF de uma carta que ficou sem ele (spec 035); a conversão pelo Word pode levar alguns segundos. */
export const pdfDaCarta = (nome: string) =>
  pedir<{ documento: DocumentoCarta }>("POST", `/api/kit/carta/${encodeURIComponent(nome)}/pdf`, {}, { timeoutMs: 5 * 60 * 1000 })

/** perguntas: uma por linha, até 30. */
export const respostas = (vagaId: string, perguntas: string) =>
  pedir<EstadoGeracao>("POST", "/api/kit/respostas", { vaga_id: vagaId, perguntas })

/** As respostas escritas pela pessoa, pelo número da pergunta (a partir de 1); gravadas como ela escreveu. */
export const salvarRespostas = (nome: string, pessoa: Record<string, string>) =>
  pedir<{ documento: DocumentoRespostas }>("PUT", `/api/kit/respostas/${encodeURIComponent(nome)}`, { pessoa })
