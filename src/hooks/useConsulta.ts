import { useEffect, useRef } from "react"

/**
 * Consulta periódica (dash/API.md §1): chama `fn` a cada `intervaloMs` enquanto `ativo`.
 * Com a aba escondida não consulta; ao voltar para a aba, consulta na hora.
 * Uma consulta por vez: a próxima só é marcada depois que a anterior termina.
 */
export function useConsulta(fn: () => unknown, intervaloMs: number, ativo: boolean) {
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    if (!ativo) return
    let parado = false
    let timer: ReturnType<typeof setTimeout> | undefined

    const rodar = async () => {
      if (parado) return
      if (typeof document === "undefined" || !document.hidden) {
        try {
          await fnRef.current()
        } catch {
          // o erro é tratado em quem chamou; a consulta segue
        }
      }
      if (!parado) timer = setTimeout(rodar, intervaloMs)
    }

    const aoVoltar = () => {
      if (!document.hidden) {
        if (timer) clearTimeout(timer)
        rodar()
      }
    }

    timer = setTimeout(rodar, intervaloMs)
    document.addEventListener("visibilitychange", aoVoltar)
    return () => {
      parado = true
      if (timer) clearTimeout(timer)
      document.removeEventListener("visibilitychange", aoVoltar)
    }
  }, [intervaloMs, ativo])
}
