/** Preparar entrevista (dash/API.md §3.10). Todas só no computador da ferramenta. */
import { pedir } from "../api"
import type { Vaga } from "../../types/api"

export interface PerguntaProvavel {
  texto: string
  texto_en: string
  tipo: "comportamental" | "tecnica"
  porque: string
  origem: "padrao" | "requisito" | "lacuna" | "rodada" | "ia"
}

export interface Historia {
  id?: string
  titulo: string
  situacao: string
  tarefa: string
  acao: string
  resultado: string
  reflexao: string
  conquista?: string
  perguntas?: string[]
  conferir?: string[]
  criada_em?: string
  atualizada_em?: string
}

export interface RetornoSimulacao {
  funcionou: string
  faltou: string
  mais_forte: string
  conferir?: string[]
}

export interface Rodada {
  data: string
  etapa: string
  perguntas: string[]
  bem: string
  mal: string
  proximos: string
}

export interface Simulacao {
  idioma?: "pt" | "en"
  respostas: { pergunta: string; resposta: string; retorno: RetornoSimulacao | null; data: string }[]
}

export interface Entrevista {
  vaga: { id: string; titulo: string; empresa: string; etapa: string | null; entrevista_em: string | null }
  dossie: Partial<
    Pick<
      Vaga,
      | "titulo"
      | "empresa"
      | "local"
      | "plataforma"
      | "salario"
      | "moeda"
      | "url"
      | "url_candidatura"
      | "resumo"
      | "encaixe"
      | "lacunas"
      | "alertas"
      | "autorizacao"
      | "contratacao"
      | "ingles"
      | "fuso"
      | "riscos"
      | "anotacao"
      | "aderencia"
    >
  > & {
    texto_empresa: string
    resumo_ia: { itens: { ponto: string; origem: "vaga" | "texto" | "deducao"; trecho?: string }[]; data: string } | null
  }
  perguntas: PerguntaProvavel[]
  historias: Historia[]
  salario: { faixa?: string; moeda?: string; pretensao?: string; pontos?: string[] }
  simulacao: Simulacao
  rodadas: Rodada[]
  existe_perfil: boolean
  ia: boolean
}

const vid = (id: string) => encodeURIComponent(id)

export const ler = (vagaId: string) => pedir<Entrevista>("GET", `/api/entrevista/${vid(vagaId)}`)

export const salvarEmpresa = (vagaId: string, texto: string) =>
  pedir<{ texto_empresa: string }>("PUT", `/api/entrevista/${vid(vagaId)}/empresa`, { texto })

export const resumir = (vagaId: string) => pedir<{ resumo: Entrevista["dossie"]["resumo_ia"] }>("POST", `/api/entrevista/${vid(vagaId)}/resumo`, {})

export const maisPerguntas = (vagaId: string) =>
  pedir<{ perguntas: PerguntaProvavel[] }>("POST", `/api/entrevista/${vid(vagaId)}/perguntas`, {})

/** Rascunhos da IA: não grava. */
export const sugerirHistorias = (vagaId: string) =>
  pedir<{ rascunhos: Historia[] }>("POST", `/api/entrevista/${vid(vagaId)}/historias`, {})

export const salvarHistoria = (historia: Historia) => pedir<{ historia: Historia }>("POST", "/api/entrevista/historias", { historia })

export const removerHistoria = (id: string) => pedir<{ ok: boolean }>("DELETE", `/api/entrevista/historias/${vid(id)}`)

export const simular = (vagaId: string, corpo: { pergunta: string; resposta: string; idioma: "pt" | "en" }) =>
  pedir<{ retorno: RetornoSimulacao | null; simulacao: Simulacao; treinar: string[] }>(
    "POST",
    `/api/entrevista/${vid(vagaId)}/simulacao`,
    corpo,
  )

export const salvarRodada = (
  vagaId: string,
  corpo: { data: string; etapa: string; perguntas: string; bem: string; mal: string; proximos: string },
) => pedir<{ rodada: Rodada }>("POST", `/api/entrevista/${vid(vagaId)}/rodada`, corpo)
