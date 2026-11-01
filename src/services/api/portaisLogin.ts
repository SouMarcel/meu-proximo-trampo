/**
 * Portais com login (spec 041): portais que só mostram a busca depois do login, feito pela pessoa numa janela do
 * navegador só da ferramenta. Rotas só deste computador (403 de outro aparelho); sem Edge nem Chrome, 409 com {erro}.
 */
import { pedir } from "../api"
import type { PortaisLogin } from "../../types/api"

const p = (nome: string) => encodeURIComponent(nome)

export const portaisLogin = () => pedir<PortaisLogin>("GET", "/api/portais-login")

/** Abre a página de login do portal na janela da ferramenta, na frente. */
export const conectarPortal = (nome: string) => pedir<{ ok: boolean }>("POST", `/api/portais-login/${p(nome)}/conectar`, {})

/** Confere se o login foi feito na janela; false = login não encontrado. */
export const prontoPortal = (nome: string) => pedir<{ conectado: boolean }>("POST", `/api/portais-login/${p(nome)}/pronto`, {})

export const desconectarPortal = (nome: string) =>
  pedir<{ ok: boolean }>("POST", `/api/portais-login/${p(nome)}/desconectar`, {})
