/**
 * Gerenciamento de preferências de tela (aba aberta, filtros visuais, ordenação).
 * Regra do projeto: localStorage APENAS para preferências de tela, NUNCA para
 * vagas, perfil, configuração ou candidaturas.
 */
import {
  Vaga,
  FiltrosBusca,
  ConfigIA,
  PerfilUsuario,
  PortalConectado,
  ItemSincronizacao,
  HistoricoCandidatura,
} from "../types/job"
import {
  MOCK_VAGAS,
  MOCK_FILTROS_BUSCA,
  MOCK_CONFIG_IA,
  MOCK_PERFIL,
  MOCK_PORTAIS_CONECTADOS,
  MOCK_ITENS_SINCRONIZACAO,
  MOCK_HISTORICO_CANDIDATURAS,
} from "./mockData"

const PREF_KEYS = {
  ACTIVE_TAB: "mpt_pref_active_tab",
  TRIAGE_SUBTAB: "mpt_pref_triage_subtab",
  TRIAGE_ORDEM: "mpt_pref_triage_ordem",
  TRIAGE_FILTROS: "mpt_pref_triage_filtros",
  THEME: "mpt_pref_theme",
}

export interface ScreenPreferences {
  activeTab?: string
  triageSubTab?: string
  triageOrdem?: string
  triageSenioridade?: string
  triageModo?: string
  triageAderenciaMinima?: number
}

export class ScreenPreferencesService {
  public static getActiveTab(defaultTab = "relatorio"): string {
    try {
      return localStorage.getItem(PREF_KEYS.ACTIVE_TAB) || defaultTab
    } catch {
      return defaultTab
    }
  }

  public static setActiveTab(tab: string): void {
    try {
      localStorage.setItem(PREF_KEYS.ACTIVE_TAB, tab)
    } catch {}
  }

  public static getTriagePreferences(): Partial<ScreenPreferences> {
    try {
      const raw = localStorage.getItem(PREF_KEYS.TRIAGE_FILTROS)
      return raw ? JSON.parse(raw) : {}
    } catch {
      return {}
    }
  }

  public static saveTriagePreferences(prefs: Partial<ScreenPreferences>): void {
    try {
      localStorage.setItem(PREF_KEYS.TRIAGE_FILTROS, JSON.stringify(prefs))
    } catch {}
  }

  /** Tema: "sistema" (segue o computador), "claro" ou "escuro". */
  public static getTema(): Tema {
    try {
      const t = localStorage.getItem(PREF_KEYS.THEME)
      return t === "claro" || t === "escuro" ? t : "sistema"
    } catch {
      return "sistema"
    }
  }

  public static setTema(tema: Tema): void {
    try {
      if (tema === "sistema") localStorage.removeItem(PREF_KEYS.THEME)
      else localStorage.setItem(PREF_KEYS.THEME, tema)
    } catch {}
  }
}

export type Tema = "sistema" | "claro" | "escuro"

/** Aplica o tema na página (classe "dark" no <html>); no "sistema", segue o prefers-color-scheme. */
export function aplicarTema(tema: Tema): void {
  if (typeof document === "undefined") return
  const escuroDoSistema =
    typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches
  const escuro = tema === "escuro" || (tema === "sistema" && escuroDoSistema)
  document.documentElement.classList.toggle("dark", Boolean(escuro))
  document.documentElement.style.colorScheme = escuro ? "dark" : "light"
}

/**
 * Compatibilidade legada para transição e suporte às telas ainda não migradas
 * Não grava vagas nem perfil em localStorage.
 */
export class JobStorageService {
  public static checkBackendConnection(): Promise<boolean> {
    return Promise.resolve(false)
  }

  public static getBackendStatus(): boolean | null {
    return null
  }

  public static getVagas(): Vaga[] {
    return MOCK_VAGAS
  }

  public static saveVagas(_vagas: Vaga[]): void {}

  public static updateVaga(id: string, updates: Partial<Vaga>): Vaga | null {
    const v = MOCK_VAGAS.find((item) => item.id === id)
    return v ? { ...v, ...updates } : null
  }

  public static addVaga(vaga: Vaga): Vaga {
    return vaga
  }

  public static deleteVaga(_id: string): void {}

  public static getFiltrosBusca(): FiltrosBusca {
    return MOCK_FILTROS_BUSCA
  }

  public static saveFiltrosBusca(_filtros: FiltrosBusca): void {}

  public static getConfigIA(): ConfigIA {
    return MOCK_CONFIG_IA
  }

  public static saveConfigIA(_config: ConfigIA): void {}

  public static getPerfil(): PerfilUsuario {
    return MOCK_PERFIL
  }

  public static savePerfil(_perfil: PerfilUsuario): void {}

  public static getPortaisConectados(): PortalConectado[] {
    return MOCK_PORTAIS_CONECTADOS
  }

  public static savePortaisConectados(_portais: PortalConectado[]): void {}

  public static getItensSincronizacao(): ItemSincronizacao[] {
    return MOCK_ITENS_SINCRONIZACAO
  }

  public static saveItensSincronizacao(_itens: ItemSincronizacao[]): void {}

  public static getHistoricoCandidaturas(): HistoricoCandidatura[] {
    return MOCK_HISTORICO_CANDIDATURAS
  }

  public static resetToDefaults(): void {}

  public static exportData(): string {
    return JSON.stringify({ version: "2.0.0", exported_at: new Date().toISOString() }, null, 2)
  }

  public static importData(_jsonString: string): boolean {
    return true
  }
}
