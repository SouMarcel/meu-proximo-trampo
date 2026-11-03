import React, { useEffect, useRef } from "react"
import { ArrowUpDown, GripVertical } from "lucide-react"
import { ESPACO, type TipoWidget, type WidgetDef } from "./layout"

/**
 * Moldura de um widget do painel (spec 046): o título, que no modo de edição vira a alça de arrastar, e o corpo, que
 * rola quando passa da altura. Na grade, mede a altura natural do conteúdo para a altura automática.
 */
interface Props {
  def: WidgetDef
  /** "grade": ocupa a altura do item da grade; "coluna": a altura do conteúdo (telas estreitas). */
  modo: "grade" | "coluna"
  editando?: boolean
  fixa?: boolean
  onMedida?: (id: string, px: number) => void
  onAlturaConteudo?: (id: string) => void
}

const MOLDURA = "bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xs min-w-0"
/** O padding e o espaço entre o título e o corpo de cada tipo, os mesmos dos cartões de antes. */
const POR_TIPO: Record<TipoWidget, { moldura: string; corpo: string }> = {
  numero: { moldura: "p-5 space-y-2", corpo: "space-y-2" },
  secao: { moldura: "p-5 sm:p-6 space-y-3", corpo: "space-y-3" },
  bloco: { moldura: "p-5 space-y-3", corpo: "space-y-3" },
}

function Titulo({ def }: { def: WidgetDef }) {
  if (def.tipo === "numero") {
    return (
      <div className="flex items-center justify-between gap-2 text-slate-500 min-w-0">
        <span className="text-xs font-semibold break-words min-w-0">{def.titulo}</span>
        <div className={`p-2 rounded-xl shrink-0 ${def.corIcone ?? ""}`}>{def.icone}</div>
      </div>
    )
  }
  if (def.tipo === "secao") {
    return (
      <div className="min-w-0">
        <h3 className="font-bold text-base text-slate-900 dark:text-white">{def.titulo}</h3>
        {def.subtitulo ? <p className="text-xs text-slate-500">{def.subtitulo}</p> : null}
      </div>
    )
  }
  return (
    <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2 min-w-0">
      {def.icone}
      <span className="break-words min-w-0">{def.titulo}</span>
    </h4>
  )
}

export default function Widget({ def, modo, editando = false, fixa = false, onMedida, onAlturaConteudo }: Props) {
  const molduraRef = useRef<HTMLDivElement>(null)
  const tituloRef = useRef<HTMLDivElement>(null)
  const corpoRef = useRef<HTMLDivElement>(null)
  const dentroRef = useRef<HTMLDivElement>(null)
  const ultima = useRef(0)
  const onMedidaRef = useRef(onMedida)
  onMedidaRef.current = onMedida
  const grade = modo === "grade"

  // Altura natural (research D3): a moldura sem o corpo, mais o conteúdo (que não estica), mais o espaço até o de baixo.
  useEffect(() => {
    if (!grade) return
    const medir = () => {
      const moldura = molduraRef.current
      const corpo = corpoRef.current
      const dentro = dentroRef.current
      if (!moldura || !corpo || !dentro) return
      const px = Math.ceil(
        moldura.getBoundingClientRect().height -
          corpo.getBoundingClientRect().height +
          dentro.getBoundingClientRect().height +
          ESPACO,
      )
      if (px === ultima.current) return
      ultima.current = px
      onMedidaRef.current?.(def.id, px)
    }
    const observador = new ResizeObserver(medir)
    if (tituloRef.current) observador.observe(tituloRef.current)
    if (dentroRef.current) observador.observe(dentroRef.current)
    medir()
    return () => observador.disconnect()
  }, [grade, def.id])

  const tipo = POR_TIPO[def.tipo]
  return (
    <div data-widget={def.id} className={grade ? "h-full pb-4" : undefined}>
      <div
        ref={molduraRef}
        className={`${MOLDURA} ${tipo.moldura} ${grade ? "h-full flex flex-col" : ""} ${
          editando ? "outline-2 outline-dashed outline-offset-2 outline-indigo-400 dark:outline-indigo-500" : ""
        }`}
      >
        <div
          ref={tituloRef}
          className={`flex items-start gap-2 ${editando ? "alca-widget cursor-move select-none" : ""}`}
          title={editando ? "Arraste para mudar de lugar" : undefined}
        >
          {editando ? <GripVertical className="w-4 h-4 mt-0.5 shrink-0 text-indigo-400" aria-hidden /> : null}
          <div className="flex-1 min-w-0">
            <Titulo def={def} />
          </div>
          {editando && fixa ? (
            <button
              type="button"
              onClick={() => onAlturaConteudo?.(def.id)}
              title="Voltar a altura a acompanhar o conteúdo"
              className="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[11px] font-semibold border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950"
            >
              <ArrowUpDown className="w-3 h-3" />
              Altura do conteúdo
            </button>
          ) : null}
        </div>
        {/* O corpo é um contêiner: o conteúdo se ajusta à largura do widget, não à da janela (research D5).
            O -mx-1 px-1 deixa à vista o fundo de hover das linhas, que passa 4 px para os lados. */}
        <div
          ref={corpoRef}
          className={`@container min-w-0 ${
            grade ? "flex-1 min-h-0 -mx-1 px-1 overflow-y-auto overflow-x-hidden rolagem-fina" : ""
          }`}
        >
          <div ref={dentroRef} className={tipo.corpo}>
            {def.corpo}
          </div>
        </div>
      </div>
    </div>
  )
}
