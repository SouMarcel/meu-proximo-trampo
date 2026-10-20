/**
 * Pedido único ao servidor local (dash/servidor.py). Regras do dash/API.md §1:
 * - página servida pelo próprio servidor (porta 8765): caminhos relativos; em outro endereço deste computador
 *   (Live Server, Vite), o endereço completo http://127.0.0.1:8765;
 * - escrita (POST, PUT, PATCH, DELETE) sempre com Content-Type: application/json e corpo JSON, mesmo vazio;
 * - erro vem como {"erro": "..."}: a mensagem já serve para mostrar à pessoa.
 */
import type { ErroApi } from "../types/api"

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const origin = window.location.origin
    if (origin === "http://127.0.0.1:8765" || origin === "http://localhost:8765") {
      return ""
    }
  }
  return "http://127.0.0.1:8765"
}

/** Endereço completo de um arquivo servido pelo servidor (/arquivos/...). */
export function urlArquivo(caminho: string): string {
  return getApiBaseUrl() + caminho
}

function criarErro(status: number, mensagem: string, dados: any): ErroApi {
  const erro = new Error(mensagem) as ErroApi
  erro.status = status
  erro.dados = dados
  return erro
}

export function ehErroApi(e: unknown): e is ErroApi {
  return e instanceof Error && typeof (e as ErroApi).status === "number"
}

/** Mensagem para a pessoa, em português, a partir de qualquer erro. */
export function mensagemDeErro(e: unknown, padrao = "Não deu certo."): string {
  if (ehErroApi(e)) return e.message || padrao
  if (e instanceof Error && e.message) return e.message
  return padrao
}

type Metodo = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

export async function pedir<T>(
  metodo: Metodo,
  caminho: string,
  corpo?: unknown,
  opcoes: { timeoutMs?: number } = {},
): Promise<T> {
  const init: RequestInit = { method: metodo, cache: "no-store" }
  if (metodo !== "GET") {
    init.headers = { "Content-Type": "application/json" }
    init.body = JSON.stringify(corpo ?? {})
  }
  let timer: ReturnType<typeof setTimeout> | undefined
  if (opcoes.timeoutMs) {
    const controle = new AbortController()
    init.signal = controle.signal
    timer = setTimeout(() => controle.abort(), opcoes.timeoutMs)
  }
  let res: Response
  try {
    res = await fetch(getApiBaseUrl() + caminho, init)
  } catch {
    throw criarErro(
      0,
      "O servidor da ferramenta não respondeu. Ele está rodando? (python iniciar.py)",
      null,
    )
  } finally {
    if (timer) clearTimeout(timer)
  }
  let dados: any = {}
  try {
    dados = await res.json()
  } catch {
    dados = {}
  }
  if (!res.ok) {
    throw criarErro(res.status, dados?.erro || `Erro no servidor (${res.status})`, dados)
  }
  return dados as T
}
