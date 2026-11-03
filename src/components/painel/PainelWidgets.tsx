import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import ReactGridLayout, { useContainerWidth, verticalCompactor, type Layout, type LayoutItem } from "react-grid-layout"
import "react-grid-layout/css/styles.css"
import { LayoutDashboard } from "lucide-react"
import { ScreenPreferencesService } from "../../services/storage"
import Widget from "./Widget"
import {
  COLUNAS,
  LARGURA_MINIMA_GRADE,
  LINHA,
  alturaEmLinhas,
  comAlturas,
  juntarGeometria,
  layoutPadrao,
  lerLayout,
  ordemDaColuna,
  paraGrade,
  paraTexto,
  type ItemLayout,
  type WidgetDef,
} from "./layout"

/**
 * Painel de widgets (spec 046): a grade de 12 colunas com Organizar painel (arrastar pelo título, redimensionar pelo
 * canto), o layout guardado neste navegador e, em telas estreitas, uma coluna na ordem do layout. Não sabe o que há
 * dentro dos widgets.
 *
 * O estado é o layout da pessoa (posição, largura, altura fixa) e, à parte, a altura medida de cada widget; a tela é
 * sempre calculada dos dois (`comAlturas`), então o resumo carregando ou uma lista aberta não mudam o layout dela.
 */

const GRADE = { cols: COLUNAS, rowHeight: LINHA, margin: [16, 0] as const, containerPadding: [0, 0] as const }
/** No modo de edição só o título arrasta; botões e campos dentro dele continuam com o clique (FR-007). */
const NAO_ARRASTA = "button, a, input, select, textarea, label"
/**
 * Mudança de altura abaixo disto (3 linhas, 12 px) é o tremor da mão ao puxar o canto para o lado: não fixa a altura,
 * porque mudar só a largura não fixa (FR-006).
 */
const TREMOR = 3
const CONFIRMAR_RESTAURAR = "Voltar o painel ao layout padrão? A posição e o tamanho que você escolheu serão perdidos."

const mesmasAlturas = (a: Record<string, number>, b: Record<string, number>) =>
  Object.keys(a).length === Object.keys(b).length && Object.keys(b).every((k) => a[k] === b[k])

export default function PainelWidgets({ widgets }: { widgets: WidgetDef[] }) {
  const { width, mounted, containerRef } = useContainerWidth()
  const [base, setBase] = useState<ItemLayout[]>(() => lerLayout(ScreenPreferencesService.getLayoutMetricas()))
  const [alturas, setAlturas] = useState<Record<string, number>>({})
  const [editando, setEditando] = useState(false)
  /** Há layout guardado pela pessoa (sem ele, a coluna única segue a ordem padrão). */
  const [daPessoa, setDaPessoa] = useState(() => ScreenPreferencesService.getLayoutMetricas() !== null)
  /** A última altura natural de cada widget, em px (research D3). */
  const medidas = useRef(new Map<string, number>())
  const quadro = useRef(0)
  /** Arrastando ou redimensionando: a medida espera o fim, para não brigar com a mão da pessoa. */
  const mexendo = useRef(false)

  const itens = useMemo(() => comAlturas(base, alturas), [base, alturas])
  const itensRef = useRef(itens)
  itensRef.current = itens
  const layout = useMemo(() => paraGrade(itens), [itens])
  const grade = mounted && width >= LARGURA_MINIMA_GRADE
  const porId = useMemo(() => new Map(widgets.map((w) => [w.id, w])), [widgets])

  useEffect(() => {
    if (!grade) setEditando(false)
  }, [grade])
  useEffect(() => () => cancelAnimationFrame(quadro.current), [])

  const alturasMedidas = useCallback(() => {
    const r: Record<string, number> = {}
    medidas.current.forEach((px, id) => {
      r[id] = alturaEmLinhas(id, px)
    })
    return r
  }, [])

  const aplicarMedidas = useCallback(
    () => setAlturas((atual) => {
      const novas = alturasMedidas()
      return mesmasAlturas(atual, novas) ? atual : novas
    }),
    [alturasMedidas],
  )

  /** As medidas do mesmo quadro vão juntas; a altura automática não grava no navegador, só a mão da pessoa grava. */
  const onMedida = useCallback(
    (id: string, px: number) => {
      medidas.current.set(id, px)
      if (mexendo.current || quadro.current) return
      quadro.current = requestAnimationFrame(() => {
        quadro.current = 0
        if (!mexendo.current) aplicarMedidas()
      })
    },
    [aplicarMedidas],
  )

  /** Uma mudança da pessoa: vira o layout dela e fica guardada como a tela mostra. */
  const mudar = useCallback(
    (novos: ItemLayout[]) => {
      setBase(novos)
      setDaPessoa(true)
      aplicarMedidas()
      ScreenPreferencesService.saveLayoutMetricas(paraTexto(comAlturas(novos, alturasMedidas())))
    },
    [aplicarMedidas, alturasMedidas],
  )

  const comecar = () => {
    mexendo.current = true
  }

  const aoArrastar = (final: Layout) => {
    mexendo.current = false
    mudar(juntarGeometria(itensRef.current, final))
  }

  const aoRedimensionar = (final: Layout, antes: LayoutItem | null, depois: LayoutItem | null) => {
    mexendo.current = false
    let novos = juntarGeometria(itensRef.current, final)
    if (antes && depois && Math.abs(depois.h - antes.h) >= TREMOR) {
      novos = novos.map((it) => (it.i === depois.i ? { ...it, fixa: true } : it))
    }
    // O widget de altura automática volta à altura do conteúdo, medida na largura nova.
    mudar(novos)
  }

  const alturaDoConteudo = useCallback(
    (id: string) => mudar(itensRef.current.map((it) => (it.i === id ? { ...it, fixa: false } : it))),
    [mudar],
  )

  const restaurar = () => {
    if (!window.confirm(CONFIRMAR_RESTAURAR)) return
    ScreenPreferencesService.apagarLayoutMetricas()
    setDaPessoa(false)
    setBase(layoutPadrao())
    aplicarMedidas()
  }

  const topo = editando ? (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/60 px-4 py-3 text-xs">
      <p className="flex-1 min-w-[12rem] font-semibold text-indigo-800 dark:text-indigo-200">
        Organizando o painel: arraste pelo título e puxe o canto para mudar o tamanho
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={restaurar}
          className="px-3 py-1.5 rounded-xl font-semibold border border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300 hover:bg-white dark:hover:bg-indigo-900"
        >
          Restaurar o padrão
        </button>
        <button
          type="button"
          onClick={() => setEditando(false)}
          className="px-3 py-1.5 rounded-xl font-semibold bg-indigo-600 text-white hover:bg-indigo-700"
        >
          Concluir
        </button>
      </div>
    </div>
  ) : (
    <div className="flex justify-end">
      <button
        type="button"
        onClick={() => setEditando(true)}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800"
      >
        <LayoutDashboard className="w-3.5 h-3.5" />
        Organizar painel
      </button>
    </div>
  )

  return (
    <div ref={containerRef} className={`painel-widgets space-y-4 ${editando ? "painel-editando" : ""}`}>
      {!mounted ? null : grade ? (
        <>
          {topo}
          <ReactGridLayout
            width={width}
            layout={layout}
            gridConfig={GRADE}
            compactor={verticalCompactor}
            dragConfig={{ enabled: editando, handle: ".alca-widget", cancel: NAO_ARRASTA }}
            resizeConfig={{ enabled: editando, handles: ["se"] }}
            onDragStart={comecar}
            onResizeStart={comecar}
            onDragStop={aoArrastar}
            onResizeStop={aoRedimensionar}
          >
            {itens.map((it) => {
              const def = porId.get(it.i)
              return def ? (
                <div key={it.i}>
                  <Widget
                    def={def}
                    modo="grade"
                    editando={editando}
                    fixa={it.fixa}
                    onMedida={onMedida}
                    onAlturaConteudo={alturaDoConteudo}
                  />
                </div>
              ) : null
            })}
          </ReactGridLayout>
        </>
      ) : (
        // Tela estreita (FR-014): uma coluna, na ordem do layout, cada widget na altura do conteúdo; o layout não muda.
        <div className="flex flex-col gap-4">
          {ordemDaColuna(itens, daPessoa).map((id) => {
            const def = porId.get(id)
            return def ? <Widget key={id} def={def} modo="coluna" /> : null
          })}
        </div>
      )}
    </div>
  )
}
