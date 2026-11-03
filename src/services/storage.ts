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
  /** Ordem e filtros da aba Internacional (spec 044), à parte dos do Relatório de Vagas. */
  TRIAGE_FILTROS_INT: "mpt_pref_internacional_filtros",
  /** Seleção da seção O que as vagas pedem, em Métricas & Funil (spec 045). */
  METRICAS_REQUISITOS: "mpt_pref_metricas_requisitos",
  /** Posição e tamanho dos widgets de Métricas & Funil (spec 046); o formato está em components/painel/layout.ts. */
  METRICAS_LAYOUT: "mpt_pref_metricas_layout",
  THEME: "mpt_pref_theme",
}

/** Área do relatório: a aba Relatório de Vagas (nacional) ou a aba Internacional (spec 044). */
export type AreaRelatorio = "nacional" | "internacional"

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
  /** Só na aba Internacional (spec 044): moeda do salário e sinal de visto ou relocation. */
  moeda?: "todas" | "usd" | "eur"
  visto?: boolean
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

  public static getTriagePreferences(area: AreaRelatorio = "nacional"): Partial<ScreenPreferences> {
    try {
      const raw = localStorage.getItem(area === "internacional" ? PREF_KEYS.TRIAGE_FILTROS_INT : PREF_KEYS.TRIAGE_FILTROS)
      const prefs = raw ? JSON.parse(raw) : {}
      return prefs && typeof prefs === "object" ? prefs : {}
    } catch {
      return {}
    }
  }

  public static saveTriagePreferences(prefs: Partial<ScreenPreferences>, area: AreaRelatorio = "nacional"): void {
    try {
      localStorage.setItem(
        area === "internacional" ? PREF_KEYS.TRIAGE_FILTROS_INT : PREF_KEYS.TRIAGE_FILTROS,
        JSON.stringify(prefs),
      )
    } catch {}
  }

  /** Seleção de O que as vagas pedem (spec 045); valor que não vale volta ao padrão. */
  public static getSelecaoRequisitos(): SelecaoRequisitos {
    try {
      const raw = JSON.parse(localStorage.getItem(PREF_KEYS.METRICAS_REQUISITOS) || "{}")
      return {
        vagas: raw?.vagas === "todas" ? "todas" : "aplicacoes",
        area: raw?.area === "nacional" || raw?.area === "internacional" ? raw.area : "todas",
      }
    } catch {
      return { vagas: "aplicacoes", area: "todas" }
    }
  }

  public static saveSelecaoRequisitos(selecao: SelecaoRequisitos): void {
    try {
      localStorage.setItem(PREF_KEYS.METRICAS_REQUISITOS, JSON.stringify(selecao))
    } catch {}
  }

  /** Layout dos widgets de Métricas & Funil (spec 046), como texto; quem lê é o lerLayout, tolerante. */
  public static getLayoutMetricas(): string | null {
    try {
      return localStorage.getItem(PREF_KEYS.METRICAS_LAYOUT)
    } catch {
      return null
    }
  }

  public static saveLayoutMetricas(texto: string): void {
    try {
      localStorage.setItem(PREF_KEYS.METRICAS_LAYOUT, texto)
    } catch {}
  }

  public static apagarLayoutMetricas(): void {
    try {
      localStorage.removeItem(PREF_KEYS.METRICAS_LAYOUT)
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

/** Quais vagas a seção O que as vagas pedem conta (spec 045). */
export interface SelecaoRequisitos {
  vagas: "aplicacoes" | "todas"
  area: "todas" | "nacional" | "internacional"
}

/** Aplica o tema na página (classe "dark" no <html>); no "sistema", segue o prefers-color-scheme. */
export function aplicarTema(tema: Tema): void {
  if (typeof document === "undefined") return
  const escuroDoSistema =
    typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches
  const escuro = tema === "escuro" || (tema === "sistema" && escuroDoSistema)
  document.documentElement.classList.toggle("dark", Boolean(escuro))
  document.documentElement.style.colorScheme = escuro ? "dark" : "light"
}

