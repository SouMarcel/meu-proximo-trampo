import { useState } from "react"
import { Loader2 } from "lucide-react"
import * as contasApi from "../../services/api/contas"
import type { LeituraEmail } from "../../services/api/contas"
import { useFerramenta } from "../../contexto/Ferramenta"
import { mensagemDeErro } from "../../services/api"
import { BTN_MINI } from "../curriculo/Curriculos"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const MAX_CAIXAS = 20

interface Props {
  textos: string[]
  onTextos: (t: string[]) => void
  leitura: LeituraEmail | null
  onLeitura: (l: LeituraEmail) => void
  disabled?: boolean
}

export default function ColarEmail({ textos, onTextos, leitura, onLeitura, disabled }: Props) {
  const { podeGravar, tratarErro } = useFerramenta()
  const [lendo, setLendo] = useState(false)
  const [erro, setErro] = useState("")
  const temTexto = textos.some((t) => t.trim())

  const ler = async () => {
    setLendo(true)
    setErro("")
    try {
      onLeitura(await contasApi.lerEmails(textos.filter((t) => t.trim())))
    } catch (err) {
      tratarErro(err)
      setErro(mensagemDeErro(err))
    } finally {
      setLendo(false)
    }
  }

  const nIA = leitura ? leitura.itens.filter((i) => i.por_ia).length : 0

  return (
    <section className="space-y-2">
      <h4 className="font-bold text-sm text-slate-900 dark:text-white">Colar e-mail</h4>
      <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs">
        Cole só o corpo do e-mail: sem remetente, destinatários e cabeçalhos. Uma caixa por e-mail. O texto não é guardado.
      </p>
      {textos.map((t, n) => (
        <div key={n} className="flex items-start gap-2">
          <textarea
            rows={4}
            value={t}
            maxLength={20000}
            aria-label={`E-mail ${n + 1}`}
            onChange={(ev) => onTextos(textos.map((x, k) => (k === n ? ev.target.value : x)))}
            className="flex-1 p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
          />
          {textos.length > 1 && (
            <button
              type="button"
              onClick={() => onTextos(textos.filter((_, k) => k !== n))}
              className={BTN_MINI}
              aria-label={`Tirar e-mail ${n + 1}`}
            >
              Tirar
            </button>
          )}
        </div>
      ))}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          disabled={textos.length >= MAX_CAIXAS}
          onClick={() => onTextos([...textos, ""])}
          className={BTN_MINI}
        >
          + outro e-mail
        </button>
        <button
          type="button"
          disabled={!temTexto || !podeGravar || lendo || disabled}
          onClick={ler}
          className="px-3 py-1 rounded-lg text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
        >
          {lendo ? (
            <span className="flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" /> Lendo…
            </span>
          ) : (
            "Ler"
          )}
        </button>
      </div>
      <p className={DICA}>Com a IA ligada, o e-mail que não for reconhecido vai à IA.</p>
      {leitura?.ia.usada && (
        <p className={DICA}>
          {nIA} e-mail(s) lido(s) com a IA{leitura.ia.nome ? ` (${leitura.ia.nome})` : ""}
        </p>
      )}
      {leitura?.ia.erro && <p className="text-[11px] text-rose-600 dark:text-rose-400">{leitura.ia.erro}</p>}
      {erro && (
        <p role="alert" className="text-[11px] text-rose-600 dark:text-rose-400">
          {erro}
        </p>
      )}
    </section>
  )
}
