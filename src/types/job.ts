/**
 * Tipos antigos do protótipo. A vaga e seus campos vêm de types/api.ts (o contrato do servidor); o resto
 * (filtros, IA, perfil, contas) sai à medida que cada tela passa a usar o servidor (spec 025).
 */
export type {
  Plataforma,
  Etapa,
  Resultado,
  Triagem,
  ModeloTrabalho,
  Area,
  Vaga,
} from "./api"
import type { Plataforma, Etapa, Resultado } from "./api"

export interface HistoriaSTAR {
  id: string
  titulo: string
  situacao: string
  tarefa: string
  acao: string
  resultado: string
  competencias: string[]
}

export interface PerguntaEntrevista {
  id: string
  pergunta: string
  tipo: "comportamental" | "tecnica" | "situacional"
  dica: string
  sugestao_resposta?: string
}

export interface PortalConectado {
  id: "gupy" | "indeed" | "linkedin"
  nome: string
  plataforma: Plataforma
  conectado: boolean
  aviso_login: string
  icone?: string
  ultima_sincronizacao?: string
  candidaturas_encontradas?: number
}

export interface ItemSincronizacao {
  id: string
  titulo: string
  empresa: string
  plataforma: Plataforma
  etapa_atual?: Etapa | null
  etapa_nova: Etapa
  resultado_novo?: Resultado | null
  alteracao: string
  selecionado: boolean
  data_portal?: string
}

export interface HistoricoCandidatura {
  id: string
  titulo: string
  empresa: string
  plataforma: Plataforma
  data: string
  etapa: Etapa
  resultado?: Resultado | null
}
