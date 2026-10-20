/**
 * Gerenciamento de preferências de tela (aba aberta, filtros visuais, ordenação).
 * Regra do projeto: localStorage APENAS para preferências de tela, NUNCA para
 * vagas, perfil, configuração ou candidaturas.
 */

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
}

export class JobStorageService {
  public static exportData(): string {
    return JSON.stringify({ version: "2.0.0", exported_at: new Date().toISOString() }, null, 2)
  }

  public static importData(_jsonString: string): boolean {
    return true
  }

  public static resetToDefaults(): void {}
}
