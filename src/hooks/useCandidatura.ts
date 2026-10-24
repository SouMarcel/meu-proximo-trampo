/**
 * Estado da candidatura assistida (dash/API.md §3.11b) compartilhado entre os cards do quadro, o kit da vaga e a
 * configuração: um pedido só ao servidor, relido quando a pessoa liga, desliga ou muda o login guardado.
 */
import { useEffect, useState } from "react"
import * as api from "../services/api/candidatura"
import type { EstadoCandidatura } from "../services/api/candidatura"

let atual: EstadoCandidatura | null = null
let pedido: Promise<void> | null = null
const ouvintes = new Set<(e: EstadoCandidatura | null) => void>()

export function recarregarCandidatura(): Promise<void> {
  pedido = api
    .estado()
    .then((e) => {
      atual = e
    })
    .catch(() => {
      atual = null
    })
    .then(() => ouvintes.forEach((f) => f(atual)))
  return pedido
}

export function useCandidatura(ativo = true): EstadoCandidatura | null {
  const [e, setE] = useState<EstadoCandidatura | null>(atual)
  useEffect(() => {
    if (!ativo) return
    ouvintes.add(setE)
    if (!pedido) recarregarCandidatura()
    else setE(atual)
    return () => {
      ouvintes.delete(setE)
    }
  }, [ativo])
  return ativo ? e : null
}
