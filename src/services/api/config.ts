/** Configuração da busca (dash/API.md §3.4): os filtros do config.json e as opções que o servidor aceita. */
import { pedir } from "../api"

export interface EmpresaAcompanhada {
  sistema: "greenhouse" | "lever" | "ashby" | string
  id: string
  nome: string
  url: string
}

export interface FiltrosInternacional {
  ativo: boolean
  paises: string[]
  termos: string[]
  regioes: string[]
  salario_min_anual_usd: number
  fuso_horas: number
  contratacao: string[]
  aceita_mudar: boolean
  paises_mudanca: string[]
  passaporte: boolean
  autorizacao_trabalho: string[]
  precisa_sponsor: boolean
  fontes: string[]
  empresas: EmpresaAcompanhada[]
  frases_restricao: string[]
  frases_positivas: string[]
}

export interface Filtros {
  termos: string[]
  localidade: { pais: string; estado: string; cidade: string; raio_km: number }
  modelos: { remoto: boolean; hibrido: boolean; presencial: boolean }
  internacional: FiltrosInternacional
  idiomas_aceitos: string[]
  janela_horas: number
  tipos_emprego: string[]
  senioridades: string[]
  moedas_aceitas: string[]
  empresas_excluir: string[]
  fontes: string[]
}

export interface Fonte {
  nome: string
  rotulo: string
  termos: string
  precisa?: string
}

export interface Opcoes {
  paises: string[]
  modelos: Record<string, string>
  tipos_emprego: Record<string, string>
  senioridades: Record<string, string>
  moedas: Record<string, string>
  moeda_do_pais: Record<string, string>
  janelas: Record<string, string>
  raios_km: number[]
  idiomas: Record<string, string>
  regioes: Record<string, string>
  contratacao: Record<string, string>
  fontes_int: Fonte[]
  fontes_nac: Fonte[]
}

export interface Config {
  filtros: Filtros
  consultas: number
  opcoes: Opcoes
  existe?: boolean
}

export const ler = () => pedir<Config>("GET", "/api/config")

/** Grava o objeto de filtros inteiro; erro 400 traz a regra que falhou. */
export const gravar = (filtros: Filtros) => pedir<Config>("PUT", "/api/config", filtros)

// ---------- contas que o dashboard antigo mostra antes de salvar (as mesmas de filtros.consultas()) ----------

/** Consultas por portal; porGrupo: os cargos numa consulta só (LinkedIn). */
export function contarConsultas(d: Filtros, porGrupo = false): number {
  const m = d.modelos
  let t = d.termos.length
  const locais = m.hibrido || m.presencial
  const cidade = Boolean(d.localidade.cidade)
  const it = d.internacional
  let ti = it.termos.length || t // a busca de fora não depende do remoto no país
  if (porGrupo) {
    t = Math.min(t, 1)
    ti = Math.min(ti, 1)
  }
  let n = m.remoto || (locais && !cidade) ? t : 0
  if (locais && cidade) n += t
  if (it.ativo) n += it.paises.length * ti + (it.aceita_mudar ? ((it.paises_mudanca || []).length || it.paises.length) * ti : 0)
  if (it.ativo && ((it.fontes || []).length || (it.empresas || []).length)) n += ti // fontes do exterior: uma por cargo
  return n
}

/** O LinkedIn roda em todos os grupos (cargos juntos) e, com a busca internacional, também no "mundo todo". */
export function contarLinkedin(d: Filtros): number {
  const it = d.internacional
  const ti = Math.min(it.termos.length || d.termos.length, 1)
  return contarConsultas(d, true) + (it.ativo && !((it.fontes || []).length || (it.empresas || []).length) ? ti : 0)
}

/** Empresa acompanhada pelo link da página de vagas (Greenhouse, Lever ou Ashby); o servidor confere de novo ao salvar. */
export function empresaDoLink(url: string): EmpresaAcompanhada | null {
  const m =
    /^(?:https?:\/\/)?(boards|job-boards)(?:\.eu)?\.greenhouse\.io\/(?:embed\/job_board\?for=)?([A-Za-z0-9._-]+)|^(?:https?:\/\/)?jobs(?:\.eu)?\.lever\.co\/([A-Za-z0-9._-]+)|^(?:https?:\/\/)?jobs\.ashbyhq\.com\/([A-Za-z0-9._-]+)/i.exec(
      url,
    )
  if (!m) return null
  const sistema = m[2] ? "greenhouse" : m[3] ? "lever" : "ashby"
  return { sistema, id: m[2] || m[3] || m[4], nome: "", url } // o nome sai do link ao salvar
}
