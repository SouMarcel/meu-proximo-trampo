/**
 * Texto da internet (descrição da vaga, post) mostrado como texto (dash/API.md §4.6), com um markdown mínimo
 * montado como elementos React, nunca como HTML: parágrafos, títulos (#), listas (-, *, •, 1.), **negrito**
 * e links http/https soltos no texto, abertos em nova aba.
 */
import React from "react"

const LINK = /(https?:\/\/[^\s<>"')\]]+)/g

function trechoComLinks(texto: string, chave: string): React.ReactNode[] {
  const partes = texto.split(LINK)
  return partes.map((p, i) =>
    /^https?:\/\//i.test(p) ? (
      <a
        key={`${chave}-l${i}`}
        href={p}
        target="_blank"
        rel="noopener noreferrer"
        className="text-indigo-600 dark:text-indigo-400 underline break-all"
      >
        {p}
      </a>
    ) : (
      <React.Fragment key={`${chave}-t${i}`}>{p}</React.Fragment>
    ),
  )
}

function linha(texto: string, chave: string): React.ReactNode[] {
  const limpo = texto.replace(/\\([\\`*_{}\[\]()#+\-.!|>~])/g, "$1")
  return limpo.split(/\*\*(.+?)\*\*/g).map((p, i) =>
    i % 2 === 1 ? (
      <strong key={`${chave}-b${i}`} className="font-semibold text-slate-900 dark:text-white">
        {trechoComLinks(p, `${chave}-b${i}`)}
      </strong>
    ) : (
      <React.Fragment key={`${chave}-n${i}`}>{trechoComLinks(p, `${chave}-n${i}`)}</React.Fragment>
    ),
  )
}

export default function TextoDaVaga({ texto, className = "" }: { texto?: string; className?: string }) {
  if (!texto || !texto.trim()) {
    return <p className="text-xs text-slate-400 italic">Sem descrição.</p>
  }
  const blocos: React.ReactNode[] = []
  let itens: React.ReactNode[] = []
  const fecharLista = (k: number) => {
    if (itens.length) {
      blocos.push(
        <ul key={`ul${k}`} className="list-disc pl-5 space-y-1">
          {itens}
        </ul>,
      )
      itens = []
    }
  }
  texto.split(/\r?\n/).forEach((l, k) => {
    const item = l.match(/^\s*(?:[*\-•]|\d+\.)\s+(.*)/)
    if (item) {
      itens.push(<li key={`li${k}`}>{linha(item[1], `li${k}`)}</li>)
      return
    }
    fecharLista(k)
    const titulo = l.match(/^\s*#{1,6}\s+(.*)/)
    if (titulo) {
      blocos.push(
        <h5 key={`h${k}`} className="font-bold text-slate-900 dark:text-white pt-2">
          {linha(titulo[1], `h${k}`)}
        </h5>,
      )
      return
    }
    if (l.trim()) blocos.push(<p key={`p${k}`}>{linha(l, `p${k}`)}</p>)
  })
  fecharLista(-1)
  return <div className={`space-y-2 leading-relaxed ${className}`}>{blocos}</div>
}
