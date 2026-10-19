export type Plataforma = "Gupy" | "Indeed" | "LinkedIn" | "Greenhouse" | "Lever" | "Ashby" | "RemoteOK" | "Remotive" | "Himalayas" | "Jobicy" | "We Work Remotely" | "Startup Jobs" | "Nerdin" | "Get on Board" | "InHire" | "Catho" | "Outra"

export type Etapa = "salva" | "aplicada" | "entrevista" | "proposta" | "encerrada"

export type Resultado = "nao_aprovado" | "desisti" | "cancelada" | "contratado"

export type Triagem = "pendente" | "seguir" | "visitada" | "fora"

export type ModeloTrabalho = "remoto" | "hibrido" | "presencial" | "nao_informado"

export type Senioridade = "junior" | "pleno" | "senior" | "especialista"

export type Area = "nacional" | "internacional"

export interface ChecklistItem {
  id: string
  texto: string
  estado: "a_fazer" | "pronto" | "nao_se_aplica"
  obrigatorio?: boolean
  categoria?: string
}

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

export interface Vaga {
  id: string
  titulo: string
  empresa: string
  plataforma: Plataforma
  outras_plataformas?: string[]
  local: string
  remoto: boolean
  area: Area
  pais_vaga?: string
  idioma?: string
  url: string
  url_candidatura?: string | null
  salario?: string | null
  tipo?: string | null
  descricao: string
  publicada_em: string
  encontrada_em: string
  triagem: Triagem
  motivo_fora?: string[]
  etapa: Etapa | null
  etapa_em?: string | null
  resultado?: Resultado | null
  anotacao?: string
  entrevista_em?: string | null
  aderencia?: number
  analise_status?: "feita" | "pendente" | "sem_dados"
  resumo?: string
  encaixe?: string[]
  lacunas?: string[]
  alertas?: string[]
  sinais?: string[]
  ats?: "greenhouse" | "lever" | "ashby" | null
  senioridade?: Senioridade[]
  modelo_trabalho?: ModeloTrabalho
  termos?: string[]
  checklist?: ChecklistItem[]
  email_candidatura?: string
  assunto_candidatura?: string
  perguntas_frequentes?: PerguntaEntrevista[]
  historias_star?: HistoriaSTAR[]
}

export interface FiltrosBusca {
  termos: string[]
  fontes: string[]
  localidade: {
    pais: string
    estado: string
    cidade: string
    raio_km: number
  }
  modelos: {
    remoto: boolean
    hibrido: boolean
    presencial: boolean
  }
  internacional: {
    ativo: boolean
    paises: string[]
    termos: string[]
    regioes: string[]
    salario_min_anual_usd: number
    fuso_horas: number
    contratacao: string[]
    precisa_sponsor: boolean
    fontes: string[]
    empresas: string[]
  }
  janela_horas: number
  tipos_emprego: string[]
  senioridades: Senioridade[]
  moedas_aceitas: string[]
  idiomas_aceitos: string[]
  empresas_excluir: string[]
  analise_automatica: boolean
}

export interface ConfigIA {
  provedor: "claude" | "openai" | "gemini" | "ollama" | "deepseek" | "openrouter"
  modelo: string
  chave_api?: string
  url_base?: string
  status_conexao?: "conectado" | "erro" | "nao_configurado"
  ultima_verificacao?: string
}

export interface PerfilUsuario {
  nome: string
  cargo_atual: string
  cargos_alvo: string[]
  anos_experiencia: number
  nivel_ingles: "basico" | "intermediario" | "avancado" | "fluente" | "nativo"
  competencias_chave: string[]
  pretensao_salarial_brl?: string
  pretensao_salarial_usd?: string
  bio?: string
  linkedin_url?: string
  github_url?: string
  curriculo_atualizado_em?: string
}
