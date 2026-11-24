/** Uma etiqueta por portal em que a vaga foi anunciada: o principal primeiro, depois os outros. */
import type { Vaga } from "../types/api"
import { getPlataformaStyle } from "../utils/formatters"

export default function EtiquetasPortais({ vaga, tamanho = "sm" }: { vaga: Vaga; tamanho?: "sm" | "md" }) {
  const outras = (vaga.outras_plataformas || []).filter(
    (p, i, todas) => p && p !== vaga.plataforma && todas.indexOf(p) === i,
  )
  const px = tamanho === "md" ? "px-2.5" : "px-2"

  const etiqueta = (p: string, outra: boolean) => {
    const estilo = getPlataformaStyle(p)
    return (
      <span
        key={p}
        title={outra ? `Também anunciada em ${p}` : undefined}
        className={`${px} py-0.5 rounded-lg text-xs font-semibold border ${estilo.bg} ${estilo.text} ${estilo.border}`}
      >
        {p}
      </span>
    )
  }

  return (
    <span className="inline-flex flex-wrap gap-1">
      {etiqueta(vaga.plataforma, false)}
      {outras.map((p) => etiqueta(p, true))}
    </span>
  )
}
