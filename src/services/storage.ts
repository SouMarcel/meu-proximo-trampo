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
  /** Filtros do Relatório ("ni" = não informado), lembrados neste navegador como no dashboard antigo. */
  niveis?: string[]
  modos?: string[]
  ader?: number | null
  dias?: number | null
  /** Caixa "Analisadas" (spec 038): marcada, o Relatório oculta as vagas ainda sem nota em todas as abas. */
  analisadas?: boolean
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

  /** Primeiros passos abertos sozinhos (sem perfil) só uma vez por sessão do navegador. */
  public static primeirosPassosJaAbertos(): boolean {
    try {
      return sessionStorage.getItem("mpt_sessao_primeiros_passos") === "1"
    } catch {
      return false
    }
  }

  public static marcarPrimeirosPassosAbertos(): void {
    try {
      sessionStorage.setItem("mpt_sessao_primeiros_passos", "1")
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

