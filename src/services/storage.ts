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

const STORAGE_KEYS = {
  VAGAS: "meu_trampo_vagas_v2",
  FILTROS: "meu_trampo_filtros_v2",
  IA: "meu_trampo_ia_v2",
  PERFIL: "meu_trampo_perfil_v2",
  BACKEND_ONLINE: "meu_trampo_backend_online",
  PORTAIS: "meu_trampo_portais_v2",
  ITENS_SYNC: "meu_trampo_itens_sync_v2",
  HISTORICO_SYNC: "meu_trampo_historico_sync_v2",
}

const BACKEND_URL = "http://127.0.0.1:8765"

export class JobStorageService {
  private static isBackendAvailable: boolean | null = null

  public static async checkBackendConnection(): Promise<boolean> {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 1200)
      const res = await fetch(`${BACKEND_URL}/api/versao`, {
        signal: controller.signal,
      })
      clearTimeout(timeout)
      this.isBackendAvailable = res.ok
      return res.ok
    } catch {
      this.isBackendAvailable = false
      return false
    }
  }

  public static getBackendStatus(): boolean | null {
    return this.isBackendAvailable
  }

  public static getVagas(): Vaga[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.VAGAS)
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.VAGAS, JSON.stringify(MOCK_VAGAS))
        return MOCK_VAGAS
      }
      return JSON.parse(raw)
    } catch {
      return MOCK_VAGAS
    }
  }

  public static saveVagas(vagas: Vaga[]): void {
    localStorage.setItem(STORAGE_KEYS.VAGAS, JSON.stringify(vagas))
  }

  public static updateVaga(id: string, updates: Partial<Vaga>): Vaga | null {
    const vagas = this.getVagas()
    const index = vagas.findIndex((v) => v.id === id)
    if (index === -1) return null

    const updated = {
      ...vagas[index],
      ...updates,
    }

    vagas[index] = updated
    this.saveVagas(vagas)

    // Se backend estiver disponível, envia em background
    if (this.isBackendAvailable) {
      fetch(`${BACKEND_URL}/api/vagas/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      }).catch(() => {})
    }

    return updated
  }

  public static addVaga(vaga: Vaga): Vaga {
    const vagas = this.getVagas()
    const existsIndex = vagas.findIndex((v) => v.id === vaga.id)
    if (existsIndex !== -1) {
      vagas[existsIndex] = vaga
    } else {
      vagas.unshift(vaga)
    }
    this.saveVagas(vagas)
    return vaga
  }

  public static deleteVaga(id: string): void {
    const vagas = this.getVagas().filter((v) => v.id !== id)
    this.saveVagas(vagas)

    if (this.isBackendAvailable) {
      fetch(`${BACKEND_URL}/api/vagas/${id}`, {
        method: "DELETE",
      }).catch(() => {})
    }
  }

  public static getFiltrosBusca(): FiltrosBusca {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.FILTROS)
      if (!raw) {
        localStorage.setItem(
          STORAGE_KEYS.FILTROS,
          JSON.stringify(MOCK_FILTROS_BUSCA),
        )
        return MOCK_FILTROS_BUSCA
      }
      return JSON.parse(raw)
    } catch {
      return MOCK_FILTROS_BUSCA
    }
  }

  public static saveFiltrosBusca(filtros: FiltrosBusca): void {
    localStorage.setItem(STORAGE_KEYS.FILTROS, JSON.stringify(filtros))
  }

  public static getConfigIA(): ConfigIA {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.IA)
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.IA, JSON.stringify(MOCK_CONFIG_IA))
        return MOCK_CONFIG_IA
      }
      return JSON.parse(raw)
    } catch {
      return MOCK_CONFIG_IA
    }
  }

  public static saveConfigIA(config: ConfigIA): void {
    localStorage.setItem(STORAGE_KEYS.IA, JSON.stringify(config))
  }

  public static getPerfil(): PerfilUsuario {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.PERFIL)
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.PERFIL, JSON.stringify(MOCK_PERFIL))
        return MOCK_PERFIL
      }
      return JSON.parse(raw)
    } catch {
      return MOCK_PERFIL
    }
  }

  public static savePerfil(perfil: PerfilUsuario): void {
    localStorage.setItem(STORAGE_KEYS.PERFIL, JSON.stringify(perfil))
  }

  public static getPortaisConectados(): PortalConectado[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.PORTAIS);
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.PORTAIS, JSON.stringify(MOCK_PORTAIS_CONECTADOS));
        return MOCK_PORTAIS_CONECTADOS;
      }
      return JSON.parse(raw);
    } catch {
      return MOCK_PORTAIS_CONECTADOS;
    }
  }

  public static savePortaisConectados(portais: PortalConectado[]): void {
    localStorage.setItem(STORAGE_KEYS.PORTAIS, JSON.stringify(portais));
  }

  public static getItensSincronizacao(): ItemSincronizacao[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.ITENS_SYNC);
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.ITENS_SYNC, JSON.stringify(MOCK_ITENS_SINCRONIZACAO));
        return MOCK_ITENS_SINCRONIZACAO;
      }
      return JSON.parse(raw);
    } catch {
      return MOCK_ITENS_SINCRONIZACAO;
    }
  }

  public static saveItensSincronizacao(itens: ItemSincronizacao[]): void {
    localStorage.setItem(STORAGE_KEYS.ITENS_SYNC, JSON.stringify(itens));
  }

  public static getHistoricoCandidaturas(): HistoricoCandidatura[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.HISTORICO_SYNC);
      if (!raw) {
        localStorage.setItem(STORAGE_KEYS.HISTORICO_SYNC, JSON.stringify(MOCK_HISTORICO_CANDIDATURAS));
        return MOCK_HISTORICO_CANDIDATURAS;
      }
      return JSON.parse(raw);
    } catch {
      return MOCK_HISTORICO_CANDIDATURAS;
    }
  }

  public static resetToDefaults(): void {
    localStorage.setItem(STORAGE_KEYS.VAGAS, JSON.stringify(MOCK_VAGAS))
    localStorage.setItem(
      STORAGE_KEYS.FILTROS,
      JSON.stringify(MOCK_FILTROS_BUSCA),
    )
    localStorage.setItem(STORAGE_KEYS.IA, JSON.stringify(MOCK_CONFIG_IA))
    localStorage.setItem(STORAGE_KEYS.PERFIL, JSON.stringify(MOCK_PERFIL))
  }

  public static exportData(): string {
    const data = {
      version: "2.0.0",
      exported_at: new Date().toISOString(),
      vagas: this.getVagas(),
      filtros: this.getFiltrosBusca(),
      ia: this.getConfigIA(),
      perfil: this.getPerfil(),
    }
    return JSON.stringify(data, null, 2)
  }

  public static importData(jsonString: string): boolean {
    try {
      const data = JSON.parse(jsonString)
      if (Array.isArray(data.vagas)) {
        this.saveVagas(data.vagas)
      }
      if (data.filtros) {
        this.saveFiltrosBusca(data.filtros)
      }
      if (data.ia) {
        this.saveConfigIA(data.ia)
      }
      if (data.perfil) {
        this.savePerfil(data.perfil)
      }
      return true
    } catch {
      return false
    }
  }
}
