import { Vaga, Triagem, Etapa, Resultado } from "../types/job"

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const origin = window.location.origin
    if (
      origin === "http://127.0.0.1:8765" ||
      origin === "http://localhost:8765"
    ) {
      return ""
    }
  }
  return "http://127.0.0.1:8765"
}

export interface VersaoResponse {
  versao: number
  analisando?: boolean
  ia_erro?: string | null
  busca?: any
  verificando?: string[]
  falhas?: Record<string, string>
}

export interface VagasResponse {
  versao: number
  vagas: Vaga[]
}

export interface PatchVagaPayload {
  triagem?: Triagem
  etapa?: Etapa | null
  resultado?: Resultado | null
  etapa_em?: string | null
  triada_em?: string | null
  anotacao?: string
  kit?: any
  lembretes?: any
  entrevista_em?: string | null
  email_candidatura?: string
  assunto_candidatura?: string
}

async function tratarResposta<T>(res: Response): Promise<T> {
  let dados: any = {}
  try {
    dados = await res.json()
  } catch {
    dados = {}
  }

  if (!res.ok) {
    const mensagem = dados?.erro || `Erro no servidor (${res.status})`
    const erro: any = new Error(mensagem)
    erro.status = res.status
    erro.dados = dados
    throw erro
  }

  return dados as T
}

export const ApiService = {
  /**
   * Checa se o backend Python está respondendo em GET /api/versao
   */
  async getVersao(timeoutMs = 2500): Promise<VersaoResponse> {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/versao`, {
        signal: controller.signal,
        cache: "no-store",
      })
      clearTimeout(timer)
      return await tratarResposta<VersaoResponse>(res)
    } catch (e: any) {
      clearTimeout(timer)
      throw e
    }
  },

  /**
   * Obtém a lista real de vagas do banco SQLite via GET /api/vagas
   */
  async getVagas(): Promise<VagasResponse> {
    const res = await fetch(`${getApiBaseUrl()}/api/vagas`, {
      cache: "no-store",
    })
    return await tratarResposta<VagasResponse>(res)
  },

  /**
   * Atualiza campos editáveis pelo usuário de uma vaga via PATCH /api/vagas/{id}
   */
  async patchVaga(id: string, payload: PatchVagaPayload): Promise<{ vaga: Vaga }> {
    const res = await fetch(`${getApiBaseUrl()}/api/vagas/${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
    return await tratarResposta<{ vaga: Vaga }>(res)
  },

  /**
   * Remove uma vaga do banco de dados via DELETE /api/vagas/{id}
   */
  async deleteVaga(id: string): Promise<{ ok: boolean }> {
    const res = await fetch(`${getApiBaseUrl()}/api/vagas/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })
    return await tratarResposta<{ ok: boolean }>(res)
  },

  /**
   * Pede a análise imediata de uma vaga específica pela IA (Forçar verificar)
   * POST /api/vagas/{id}/analisar
   */
  async forcarAnalisar(id: string): Promise<{ verificando: string[] }> {
    const res = await fetch(`${getApiBaseUrl()}/api/vagas/${encodeURIComponent(id)}/analisar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    })
    return await tratarResposta<{ verificando: string[] }>(res)
  },
}
