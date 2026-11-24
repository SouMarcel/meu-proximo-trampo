import type { Vaga } from "../types/api"

export type OrdemVaga =
  | "aderencia"
  | "menor_nota"
  | "publicacao"
  | "encontrada"
  | "empresa"
  | "plataforma"
  | "modo"
  | "etapa_recente"
  | "etapa_antiga"

export const ORDENS_VAGAS: Record<OrdemVaga, string> = {
  aderencia: "Maior Aderência",
  menor_nota: "Menor Aderência",
  publicacao: "Anúncio mais recente",
  encontrada: "Encontrada mais recente",
  empresa: "Empresa (A–Z)",
  plataforma: "Por Plataforma",
  modo: "Modo de Trabalho",
  etapa_recente: "Na etapa há menos tempo",
  etapa_antiga: "Na etapa há mais tempo",
}

function compararMaiorNota(a: Vaga, b: Vaga): number {
  const temA = typeof a.aderencia === "number"
  const temB = typeof b.aderencia === "number"
  if (!temA && !temB) return 0
  if (!temA) return 1
  if (!temB) return -1
  return b.aderencia! - a.aderencia!
}

function compararMenorNota(a: Vaga, b: Vaga): number {
  const temA = typeof a.aderencia === "number"
  const temB = typeof b.aderencia === "number"
  if (!temA && !temB) return 0
  if (!temA) return 1
  if (!temB) return -1
  return a.aderencia! - b.aderencia!
}

function compararDataRecente(da?: string | null, db?: string | null): number {
  const aVal = String(da || "").slice(0, 10)
  const bVal = String(db || "").slice(0, 10)
  if (!aVal && !bVal) return 0
  if (!aVal) return 1
  if (!bVal) return -1
  return bVal.localeCompare(aVal)
}

function compararDataAntiga(da?: string | null, db?: string | null): number {
  const aVal = String(da || "").slice(0, 10)
  const bVal = String(db || "").slice(0, 10)
  if (!aVal && !bVal) return 0
  if (!aVal) return 1
  if (!bVal) return -1
  return aVal.localeCompare(bVal)
}

function desempate(a: Vaga, b: Vaga): number {
  const notaDiff = compararMaiorNota(a, b)
  if (notaDiff !== 0) return notaDiff
  return compararDataRecente(a.publicada_em, b.publicada_em)
}

const ORDEM_MODO = ["remoto", "hibrido", "presencial", "ni"]

export function ordenar(
  vagas: Vaga[],
  ordem: OrdemVaga,
  modo: (v: Vaga) => string = () => "",
): Vaga[] {
  return [...vagas].sort((a, b) => {
    let diff = 0
    switch (ordem) {
      case "aderencia":
        diff = compararMaiorNota(a, b)
        break
      case "menor_nota":
        diff = compararMenorNota(a, b)
        break
      case "publicacao":
        diff = compararDataRecente(a.publicada_em, b.publicada_em)
        break
      case "encontrada":
        diff = compararDataRecente(a.encontrada_em || a.criada_em, b.encontrada_em || b.criada_em)
        break
      case "etapa_recente":
        diff = compararDataRecente(a.etapa_em, b.etapa_em)
        break
      case "etapa_antiga":
        diff = compararDataAntiga(a.etapa_em, b.etapa_em)
        break
      case "empresa":
        diff = (a.empresa || "").localeCompare(b.empresa || "", "pt-BR", { sensitivity: "base" })
        break
      case "plataforma": {
        const pa = a.plataforma || "Outra"
        const pb = b.plataforma || "Outra"
        diff = Number(pa === "Outra") - Number(pb === "Outra") || pa.localeCompare(pb, "pt-BR")
        break
      }
      case "modo": {
        const getIdx = (v: Vaga) => {
          const m = modo(v)
          const mapped = m === "nao_informado" ? "ni" : m
          const idx = ORDEM_MODO.indexOf(mapped)
          return idx === -1 ? ORDEM_MODO.length : idx
        }
        diff = getIdx(a) - getIdx(b)
        break
      }
    }
    return diff !== 0 ? diff : desempate(a, b)
  })
}
