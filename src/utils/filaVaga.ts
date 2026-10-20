/**
 * Uma escrita por vez na mesma vaga (dash/API.md §3.1): cada tarefa espera a anterior do mesmo id terminar,
 * mesmo que ela tenha falhado.
 */
const filas = new Map<string, Promise<unknown>>()

export function naFila<T>(vagaId: string, tarefa: () => Promise<T>): Promise<T> {
  const anterior = filas.get(vagaId) ?? Promise.resolve()
  const proxima = anterior.catch(() => undefined).then(tarefa)
  filas.set(vagaId, proxima)
  proxima
    .catch(() => undefined)
    .then(() => {
      if (filas.get(vagaId) === proxima) filas.delete(vagaId)
    })
  return proxima
}
