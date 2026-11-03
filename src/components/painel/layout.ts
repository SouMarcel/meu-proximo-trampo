import type { ReactNode } from "react"
import type { Layout, LayoutItem } from "react-grid-layout"

/**
 * Widgets do painel Métricas & Funil (spec 046): a lista fixa, o layout padrão, os limites e a leitura tolerante do
 * layout guardado no navegador. Tudo aqui é função pura; a grade fica no PainelWidgets.
 */

export const COLUNAS = 12
/** Altura de uma linha da grade, em px: a altura automática encaixa no conteúdo com no máximo 3 px de sobra. */
export const LINHA = 4
/** Espaço até o widget de baixo, em px: fica dentro do item da grade (pb-4), porque a grade não tem espaço entre linhas. */
export const ESPACO = 16
/** Abaixo desta largura do painel, os widgets ficam numa coluna, sem edição (FR-014). */
export const LARGURA_MINIMA_GRADE = 768

export type TipoWidget = "numero" | "secao" | "bloco"

export interface WidgetDef {
  id: string
  titulo: string
  tipo: TipoWidget
  icone?: ReactNode
  /** Classes do quadrado colorido do ícone, nos widgets de número. */
  corIcone?: string
  subtitulo?: string
  corpo: ReactNode
}

/** Posição e tamanho de um widget, em colunas e linhas; `fixa` quando a pessoa mudou a altura (data-model §2). */
export interface ItemLayout {
  i: string
  x: number
  y: number
  w: number
  h: number
  fixa: boolean
}

interface Limites {
  minW: number
  maxW: number
  minH: number
  maxH: number
}

const linhas = (px: number) => Math.ceil(px / LINHA)
const limites = (minW: number, maxW: number, minPx: number, maxPx: number): Limites => ({
  minW,
  maxW,
  minH: linhas(minPx),
  maxH: linhas(maxPx),
})

/** Largura em colunas e altura em px (convertida para linhas), da tabela do data-model §1. */
export const LIMITES: Record<string, Limites> = {
  total: limites(2, 6, 112, 320),
  conversao: limites(2, 6, 112, 320),
  aderencia: limites(2, 6, 112, 320),
  ofertas: limites(2, 6, 112, 320),
  funil: limites(4, 12, 176, 640),
  requisitos: limites(4, 12, 136, 640),
  habilidades: limites(3, 12, 136, 2400),
  "suas-habilidades": limites(3, 12, 136, 2400),
  certificacoes: limites(3, 12, 136, 2400),
  experiencia: limites(3, 12, 136, 1600),
  formacao: limites(3, 12, 136, 1600),
  idiomas: limites(3, 12, 136, 1600),
  senioridade: limites(3, 12, 136, 1200),
  modelo: limites(3, 12, 136, 1200),
  contratacao: limites(3, 12, 136, 1200),
  plataformas: limites(3, 12, 136, 800),
}

const item = (i: string, x: number, y: number, w: number, h: number): ItemLayout => ({ i, x, y, w, h, fixa: false })

/** O painel da spec 045. As alturas são estimativas: a medida acerta cada uma, e a compactação acerta o y. */
export const LAYOUT_PADRAO: readonly ItemLayout[] = [
  item("total", 0, 0, 3, 34),
  item("conversao", 3, 0, 3, 34),
  item("aderencia", 6, 0, 3, 34),
  item("ofertas", 9, 0, 3, 34),
  item("funil", 0, 34, 12, 54),
  item("requisitos", 0, 88, 12, 47),
  item("habilidades", 0, 135, 8, 150),
  item("suas-habilidades", 8, 135, 4, 150),
  item("certificacoes", 0, 285, 4, 75),
  item("experiencia", 4, 285, 4, 75),
  item("formacao", 8, 285, 4, 75),
  item("idiomas", 0, 360, 4, 75),
  item("senioridade", 4, 360, 4, 75),
  item("modelo", 8, 360, 4, 75),
  item("contratacao", 0, 435, 4, 75),
  item("plataformas", 0, 510, 12, 55),
]

const entre = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n))
const inteiro = (v: unknown, padrao: number) => (typeof v === "number" && Number.isFinite(v) ? Math.round(v) : padrao)

/** A altura medida, em px, convertida para linhas e posta entre o mínimo e o máximo do widget. */
export function alturaEmLinhas(id: string, px: number): number {
  const lim = LIMITES[id]
  return lim ? entre(linhas(px), lim.minH, lim.maxH) : linhas(px)
}

/**
 * Compactação vertical estável (o que fica embaixo sobe): na ordem da posição (y, depois x), cada widget sobe até
 * encostar no mais baixo dos que já estão no lugar e se cruzam com ele na horizontal. Ninguém passa à frente de ninguém
 * na mesma coluna, então o mesmo layout com as mesmas alturas dá sempre o mesmo resultado, mesmo que as alturas mudem
 * no caminho (o resumo carregando, uma lista aberta). A compactação da biblioteca depende do caminho e embaralhava o
 * layout ao recarregar a página.
 */
export function compactar(itens: readonly ItemLayout[]): ItemLayout[] {
  const postos: ItemLayout[] = []
  const novos = new Map<string, ItemLayout>()
  for (const it of [...itens].sort((a, b) => a.y - b.y || a.x - b.x)) {
    const y = postos.reduce((m, p) => (p.x < it.x + it.w && it.x < p.x + p.w ? Math.max(m, p.y + p.h) : m), 0)
    const n = { ...it, y }
    postos.push(n)
    novos.set(it.i, n)
  }
  return itens.map((it) => novos.get(it.i) ?? it)
}

export const layoutPadrao = (): ItemLayout[] => compactar(LAYOUT_PADRAO)

/**
 * Lê o layout guardado sem lançar erro (research D7): o ilegível dá o padrão; o widget que não existe mais sai; os
 * números são corrigidos; o widget que falta entra no fim, no tamanho padrão; e tudo passa pela compactação.
 */
export function lerLayout(texto: string | null): ItemLayout[] {
  let bruto: unknown = null
  try {
    bruto = texto ? JSON.parse(texto) : null
  } catch {
    bruto = null
  }
  const obj = bruto && typeof bruto === "object" ? (bruto as { versao?: unknown; itens?: unknown }) : null
  if (!obj || obj.versao !== 1 || !Array.isArray(obj.itens) || obj.itens.length === 0) return layoutPadrao()

  const padrao = new Map(LAYOUT_PADRAO.map((p) => [p.i, p]))
  const vistos = new Set<string>()
  const itens: ItemLayout[] = []
  for (const cru of obj.itens as unknown[]) {
    if (!cru || typeof cru !== "object") continue
    const c = cru as Record<string, unknown>
    const i = typeof c.i === "string" ? c.i : ""
    const lim = LIMITES[i]
    const p = padrao.get(i)
    if (!lim || !p || vistos.has(i)) continue
    vistos.add(i)
    const w = entre(inteiro(c.w, p.w), lim.minW, lim.maxW)
    itens.push({
      i,
      x: entre(inteiro(c.x, p.x), 0, COLUNAS - w),
      y: Math.max(0, inteiro(c.y, p.y)),
      w,
      h: entre(inteiro(c.h, p.h), lim.minH, lim.maxH),
      fixa: c.fixa === true,
    })
  }
  const fundo = itens.reduce((m, it) => Math.max(m, it.y + it.h), 0)
  for (const p of LAYOUT_PADRAO) {
    if (!vistos.has(p.i)) itens.push({ ...p, y: fundo + p.y })
  }
  return compactar(itens)
}

export const paraTexto = (itens: readonly ItemLayout[]): string =>
  JSON.stringify({ versao: 1, itens: itens.map(({ i, x, y, w, h, fixa }) => ({ i, x, y, w, h, fixa })) })

/**
 * Ordem da coluna única (research D6): de cima para baixo e, na mesma linha, da esquerda para a direita. Sem layout da
 * pessoa, a ordem padrão: a compactação sobe cada widget na sua coluna e trocaria a ordem de hoje no celular.
 */
export const ordemDaColuna = (itens: readonly ItemLayout[], daPessoa: boolean): string[] =>
  daPessoa ? [...itens].sort((a, b) => a.y - b.y || a.x - b.x).map((it) => it.i) : LAYOUT_PADRAO.map((p) => p.i)

/** O layout que a grade recebe: a posição e o tamanho, com os limites de cada widget. */
export const paraGrade = (itens: readonly ItemLayout[]): LayoutItem[] =>
  itens.map(({ i, x, y, w, h }) => ({ i, x, y, w, h, ...LIMITES[i] }))

/** Copia a posição e o tamanho que vieram da grade (no fim de arrastar ou redimensionar), mantendo o `fixa`. */
export function juntarGeometria(itens: readonly ItemLayout[], grade: Layout): ItemLayout[] {
  const porId = new Map(grade.map((g) => [g.i, g]))
  return itens.map((it) => {
    const g = porId.get(it.i)
    return g ? { ...it, x: g.x, y: g.y, w: g.w, h: g.h } : it
  })
}

/**
 * O que a tela mostra: o layout da pessoa com a altura medida nos widgets de altura automática, compactado. As alturas
 * em linhas vêm de `alturaEmLinhas`.
 */
export const comAlturas = (base: readonly ItemLayout[], alturas: Readonly<Record<string, number>>): ItemLayout[] =>
  compactar(base.map((it) => (it.fixa || alturas[it.i] === undefined ? it : { ...it, h: alturas[it.i] })))
