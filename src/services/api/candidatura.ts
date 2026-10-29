/**
 * Candidatura assistida (dash/API.md §3.11b; spec 027; constituição VI, "Candidatura assistida"): a ferramenta
 * preenche os campos da página aberta na janela dela, com as respostas que a pessoa conferiu. Nunca clica em botão
 * nem envia: quem avança e envia é a pessoa. A senha guardada nunca volta do servidor.
 */
import { pedir } from "../api"
import type { Vaga } from "../../types/api"

export interface Dominios {
  conhecidos: { portal: string; rotulo: string; dominios: string[]; tem_login: boolean }[]
  bloqueados: { dominio: string; motivo: string }[]
  liberados: { dominio: string; em: string }[]
}

export interface Credencial {
  portal: string
  rotulo: string
  login: string[]
  guardada: boolean
  usuario: string
  final: string
  no_ambiente: boolean
}

export interface EstadoCandidatura {
  aviso: string
  navegador: boolean
  dominios: Dominios
  credenciais: Credencial[]
  /** As respostas que a pessoa já deu, reaproveitadas nas próximas vagas (salvo pretensão salarial e relocação). */
  memoria: { chave: string; pergunta: string; resposta: string; categoria: string | null; em: string }[]
  /** Os dados de contato salvos (spec 033): preenchem os campos de contato em qualquer formulário, sem IA. */
  contato?: DadosContato
  campos_contato?: string[]
}

export interface DadosContato {
  nome?: string
  sobrenome?: string
  email?: string
  telefone?: string
  cidade?: string
  estado?: string
  pais?: string
  linkedin?: string
  portfolio?: string
  endereco?: string
  cep?: string
}

/** Proposta tirada do currículo base, das respostas já dadas e dos filtros da busca; não é gravada. */
export interface PropostaContato {
  dados: DadosContato
  fontes: Record<string, string>
  avisos: string[]
}

export interface Situacao {
  host: string
  permitido: boolean
  portal: string | null
  origem: "conhecido" | "liberado" | null
  bloqueado: string | null
  pode_liberar: boolean
}

export type TipoCampo = "texto" | "area" | "selecao" | "lista" | "unica" | "multipla" | "caixa" | "arquivo" | "senha" | "data" | "outro"
export type Marca = "comum" | "sensivel" | "cadastro" | "consentimento" | "arquivo" | "senha" | "outro"

export interface Campo {
  chave: string
  tipo: TipoCampo
  tipo_html: string
  rotulo: string
  obrigatorio: boolean
  limite: number
  opcoes: { valor: string; texto: string; vazia: boolean }[]
  valor: string
  marca: Marca
  motivo: string
  proposta: string
  conferir: string[]
}

export interface Leitura {
  pagina: {
    url: string
    dominio: Situacao
    etapa: "perguntas" | "login" | "teste" | "bloqueio" | "desconhecida"
    aviso: string
    assinatura: string
  }
  itens: Campo[]
  aviso_ia: string | null
  ia: { provedor: string; modelo: string } | null
}

/** Preencher esta página: o que a ferramenta preencheu sozinha e o que ela pergunta. */
export interface AutoPreenchimento {
  pagina: Leitura["pagina"]
  preenchidos: { chave: string; rotulo: string; texto: string; fonte: string; conferir: string[] }[]
  /** relato: pergunta comum de texto; a resposta é um relato que a IA transforma na resposta (spec 035). */
  perguntas: (Campo & { lembrar: boolean; relato?: boolean })[]
  na_janela: { chave: string; rotulo: string; motivo: string }[]
  aviso_ia: string | null
  aviso: string
  documento?: string
}

export interface Preenchimento {
  /** fonte: "seu relato (adaptado pela IA)", "seu relato" (sem IA) ou "sua resposta" (spec 035). */
  preenchidos: { chave: string; rotulo: string; valor: string; texto: string; fonte?: string }[]
  ficaram: { chave: string; rotulo: string; motivo: string }[]
  aviso: string
  documento?: string
  lembradas?: number
  /** Quantos relatos ficaram guardados no que a ferramenta sabe da pessoa. */
  relatos?: number
  aviso_ia?: string | null
}

const p = (s: string) => encodeURIComponent(s)
const LONGO = { timeoutMs: 10 * 60 * 1000 } // a proposta da IA pode demorar

export const estado = () => pedir<EstadoCandidatura>("GET", "/api/candidatura")

export const propostaContato = () => pedir<PropostaContato>("POST", "/api/candidatura/contato/proposta", {})
export const salvarContato = (dados: DadosContato) =>
  pedir<{ contato: DadosContato }>("PUT", "/api/candidatura/contato", { dados })
export const apagarContato = () => pedir<{ contato: DadosContato }>("DELETE", "/api/candidatura/contato", {})
/** A chave de cada vaga: ligar exige o aviso de risco aceito, a cada vaga. */
export const ligarVaga = (vagaId: string, ligada: boolean, aceitar_aviso = false) =>
  pedir<{ vaga: Vaga }>("PUT", `/api/candidatura/vaga/${p(vagaId)}`, { ligada, aceitar_aviso })
export const dominio = (dominio: string, acao: "liberar" | "revogar") =>
  pedir<{ dominios: Dominios }>("POST", "/api/candidatura/dominios", { dominio, acao })
export const guardarCredencial = (portal: string, usuario: string, senha: string) =>
  pedir<{ credenciais: Credencial[] }>("PUT", `/api/candidatura/credenciais/${p(portal)}`, { usuario, senha })
export const apagarCredencial = (portal: string) =>
  pedir<{ credenciais: Credencial[] }>("DELETE", `/api/candidatura/credenciais/${p(portal)}`, {})
export const preencherLogin = (vagaId: string) =>
  pedir<{ portal: string; rotulo: string; preenchidos: string[]; aviso: string }>("POST", `/api/candidatura/vaga/${p(vagaId)}/login`, {})
export const abrir = (vagaId: string) =>
  pedir<{ ok: boolean; url: string; dominio: Situacao }>("POST", `/api/candidatura/vaga/${p(vagaId)}/abrir`, {})
export const ler = (vagaId: string) => pedir<Leitura>("POST", `/api/candidatura/vaga/${p(vagaId)}/ler`, {}, LONGO)
export const auto = (vagaId: string) => pedir<AutoPreenchimento>("POST", `/api/candidatura/vaga/${p(vagaId)}/auto`, {}, LONGO)
export const preencher = (
  vagaId: string,
  assinatura: string,
  respostas: { chave: string; valor: string; trocar?: boolean }[],
  lembrar = true,
  guardar_relatos = true,
) =>
  pedir<Preenchimento>(
    "POST",
    `/api/candidatura/vaga/${p(vagaId)}/preencher`,
    { assinatura, respostas, lembrar, guardar_relatos },
    LONGO,
  )
export const apagarMemoria = (chave: string) =>
  pedir<{ memoria: EstadoCandidatura["memoria"] }>("DELETE", `/api/candidatura/memoria/${p(chave)}`, {})
