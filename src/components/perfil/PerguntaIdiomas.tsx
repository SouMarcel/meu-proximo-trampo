/**
 * Pergunta de idiomas do Meu perfil (spec 036; dash/API.md §3.6): uma linha por idioma, com o idioma (lista do servidor
 * + Outro) e o nível do CEFR (A1 a C2) ou Nativo, a descrição do nível, × para remover e + para adicionar. Cada linha é
 * gravada como texto "Inglês — B2 (Intermediário superior)", a mesma lista de textos de antes. As linhas iniciais vêm
 * do servidor (respostas antigas ou idiomas do currículo); nível em branco = a pessoa escolhe (nada de estimar nível).
 */
import React from "react"
import { Plus, X } from "lucide-react"
import type { LinhaIdioma, NivelIdioma } from "../../services/api/perfil"

export const OUTRO = "Outro"
export const LINHA_VAZIA: LinhaIdioma = { idioma: "", outro: "", nivel: "", original: "" }

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const BTN_MINI =
  "px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"

/** O nome que vai para o perfil: o idioma da lista, ou o que a pessoa escreveu em Outro. */
export function nomeDaLinha(l: LinhaIdioma): string {
  return l.idioma === OUTRO ? l.outro.trim() : l.idioma
}

const MESMO: Record<string, string> = {
  "portugues (br)": "portugues", "portugues brasileiro": "portugues", portuguese: "portugues", english: "ingles",
  french: "frances", francais: "frances", german: "alemao", deutsch: "alemao", spanish: "espanhol", espanol: "espanhol",
  castelhano: "espanhol",
}

/** Para achar repetição: sem acento e sem maiúsculas; "Outro: português" conta igual a Português (BR). */
function chaveIdioma(nome: string): string {
  const k = nome.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim()
  return MESMO[k] || k
}

/** Confere as linhas e monta a resposta: {erro} para mostrar, ou {valor} (null = nenhum idioma). */
export function respostaIdiomas(linhas: LinhaIdioma[], niveis: NivelIdioma[]): { erro?: string; valor?: string[] | null } {
  const rotulo = new Map(niveis.map((n) => [n.valor, n.rotulo]))
  const vistos = new Set<string>()
  const valor: string[] = []
  for (const [i, l] of linhas.entries()) {
    if (!l.idioma && !l.nivel) continue // linha vazia
    const nome = nomeDaLinha(l)
    if (!l.idioma) return { erro: `Escolha o idioma na linha ${i + 1}.` }
    if (!nome) return { erro: `Escreva o nome do idioma na linha ${i + 1}.` }
    if (!rotulo.has(l.nivel)) return { erro: `Escolha o nível de ${nome}.` }
    const k = chaveIdioma(nome)
    if (vistos.has(k)) return { erro: `${nome} aparece duas vezes. Deixe uma linha só para cada idioma.` }
    vistos.add(k)
    valor.push(`${nome} — ${rotulo.get(l.nivel)}`)
  }
  return { valor: valor.length ? valor : null }
}

export default function PerguntaIdiomas({
  idiomas,
  niveis,
  linhas,
  onMudar,
}: {
  idiomas: string[]
  niveis: NivelIdioma[]
  linhas: LinhaIdioma[]
  onMudar: (linhas: LinhaIdioma[]) => void
}) {
  const mudar = (i: number, parte: Partial<LinhaIdioma>) => onMudar(linhas.map((l, k) => (k === i ? { ...l, ...parte } : l)))

  return (
    <div className="space-y-2">
      {linhas.map((l, i) => {
        const nivel = niveis.find((n) => n.valor === l.nivel)
        const nome = nomeDaLinha(l) || `o idioma da linha ${i + 1}`
        return (
          <div key={i} className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <label htmlFor={`idioma-${i}`} className="sr-only">
                Idioma da linha {i + 1}
              </label>
              <select
                id={`idioma-${i}`}
                value={l.idioma}
                onChange={(ev) => mudar(i, { idioma: ev.target.value, outro: ev.target.value === OUTRO ? l.outro : "" })}
                className={`${CAMPO} flex-1 min-w-[9rem]`}
              >
                <option value="">Idioma</option>
                {idiomas.map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
                <option value={OUTRO}>Outro</option>
              </select>
              {l.idioma === OUTRO && (
                <>
                  <label htmlFor={`idioma-outro-${i}`} className="sr-only">
                    Nome do idioma da linha {i + 1}
                  </label>
                  <input
                    id={`idioma-outro-${i}`}
                    maxLength={60}
                    autoComplete="off"
                    placeholder="Qual idioma?"
                    value={l.outro}
                    onChange={(ev) => mudar(i, { outro: ev.target.value })}
                    className={`${CAMPO} flex-1 min-w-[8rem]`}
                  />
                </>
              )}
              <label htmlFor={`nivel-${i}`} className="sr-only">
                Nível de {nome}
              </label>
              <select
                id={`nivel-${i}`}
                value={l.nivel}
                onChange={(ev) => mudar(i, { nivel: ev.target.value })}
                className={`${CAMPO} flex-[2] min-w-[12rem]`}
              >
                <option value="">Nível</option>
                {niveis.map((n) => (
                  <option key={n.valor} value={n.valor}>
                    {n.rotulo}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => onMudar(linhas.filter((_, k) => k !== i))}
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                aria-label={`Remover ${nome}`}
                title="Remover"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {nivel && <p className={DICA}>{nivel.descricao}</p>}
            {l.original && <p className={DICA}>Você tinha escrito: “{l.original}”</p>}
          </div>
        )
      })}
      <button type="button" onClick={() => onMudar([...linhas, { ...LINHA_VAZIA }])} className={`${BTN_MINI} inline-flex items-center gap-1`}>
        <Plus className="w-3.5 h-3.5" /> Adicionar idioma
      </button>
    </div>
  )
}
