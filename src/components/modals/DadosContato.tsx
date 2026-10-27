/**
 * Seus dados de contato (dash/API.md §3.11b; spec 033): nome, e-mail, telefone, cidade e links que a candidatura
 * assistida usa em qualquer formulário, sem IA. "Propor a partir do currículo" só preenche o formulário daqui; nada é
 * gravado até a pessoa clicar em Salvar. Os dados ficam só neste computador e nunca vão para a IA.
 */
import React, { useEffect, useState } from "react"
import * as api from "../../services/api/candidatura"
import type { DadosContato as Dados } from "../../services/api/candidatura"
import { mensagemDeErro } from "../../services/api"
import { BTN_MINI } from "../curriculo/Curriculos"

const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"

const CAMPOS: { id: keyof Dados; rotulo: string; dica?: string; tipo?: string }[] = [
  { id: "nome", rotulo: "Nome" },
  { id: "sobrenome", rotulo: "Sobrenome" },
  { id: "email", rotulo: "E-mail", tipo: "email" },
  { id: "telefone", rotulo: "Telefone", dica: "como você quer que apareça, ex.: +55 11 90000-0000", tipo: "tel" },
  { id: "cidade", rotulo: "Cidade" },
  { id: "estado", rotulo: "Estado", dica: "sigla ou nome" },
  { id: "pais", rotulo: "País" },
  { id: "linkedin", rotulo: "LinkedIn", dica: "linkedin.com/in/…" },
  { id: "portfolio", rotulo: "Portfólio, site ou GitHub" },
  { id: "endereco", rotulo: "Endereço (opcional)" },
  { id: "cep", rotulo: "CEP (opcional)" },
]

export default function DadosContato({
  inicial,
  podeGravar,
  onSalvo,
  onAviso,
}: {
  inicial: Dados
  podeGravar: boolean
  onSalvo: () => void
  onAviso: (m: string, t?: "info" | "erro") => void
}) {
  const [form, setForm] = useState<Dados>(inicial)
  const [fontes, setFontes] = useState<Record<string, string>>({})
  const [avisos, setAvisos] = useState<string[]>([])
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState("")

  const chaveInicial = JSON.stringify(inicial)
  // só quando os dados salvos mudam, sem apagar o que está sendo digitado
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setForm(inicial), [chaveInicial])

  const salvos = Object.keys(inicial).length > 0
  const mudar = (id: keyof Dados, v: string) => setForm((f) => ({ ...f, [id]: v }))

  const rodar = async (fn: () => Promise<void>) => {
    setOcupado(true)
    setErro("")
    try {
      await fn()
    } catch (err) {
      setErro(mensagemDeErro(err))
    } finally {
      setOcupado(false)
    }
  }

  /** Preenche só os campos vazios do formulário com a proposta; nada é gravado. */
  const propor = () =>
    rodar(async () => {
      const p = await api.propostaContato()
      setForm((f) => {
        const n: Dados = { ...f }
        for (const [k, v] of Object.entries(p.dados)) if (!(n as Record<string, string>)[k]) (n as Record<string, string>)[k] = v
        return n
      })
      setFontes(p.fontes)
      setAvisos(p.avisos)
      onAviso("Proposta pronta: confira os campos e clique em Salvar.")
    })

  const salvar = (ev: React.FormEvent) => {
    ev.preventDefault()
    rodar(async () => {
      await api.salvarContato(form)
      setFontes({})
      setAvisos([])
      onAviso("Dados de contato salvos neste computador.")
      onSalvo()
    })
  }

  const apagar = () =>
    rodar(async () => {
      await api.apagarContato()
      setForm({})
      setFontes({})
      onAviso("Dados de contato apagados.")
      onSalvo()
    })

  return (
    <form onSubmit={salvar} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
      <b className="text-xs">Seus dados de contato</b>
      <p className={DICA}>
        Usados para preencher nome, e-mail, telefone e links em qualquer formulário, sem IA. Ficam só neste computador (fora
        do Git) e nunca vão para a IA. Não coloque documentos (CPF, RG, data de nascimento).
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {CAMPOS.map((c) => (
          <label key={c.id} className="text-xs space-y-0.5">
            <span className="font-semibold text-slate-600 dark:text-slate-300">{c.rotulo}</span>
            <input
              className={CAMPO}
              type={c.tipo || "text"}
              autoComplete="off"
              maxLength={c.id === "telefone" ? 40 : 200}
              value={form[c.id] || ""}
              disabled={!podeGravar || ocupado}
              placeholder={c.dica || ""}
              onChange={(ev) => mudar(c.id, ev.target.value)}
            />
            {fontes[c.id] && <span className={DICA}>proposto: {fontes[c.id]}</span>}
          </label>
        ))}
      </div>
      {avisos.length > 0 && (
        <ul className="list-disc pl-5 text-[11px] text-amber-700 dark:text-amber-300">
          {avisos.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
      <div className="flex gap-2 flex-wrap">
        <button type="button" className={BTN_MINI} disabled={!podeGravar || ocupado} onClick={propor}>
          Propor a partir do currículo
        </button>
        <button type="submit" className={BTN_MINI} disabled={!podeGravar || ocupado}>
          Salvar
        </button>
        {salvos && (
          <button type="button" className={BTN_MINI} disabled={!podeGravar || ocupado} onClick={apagar}>
            Apagar
          </button>
        )}
      </div>
      {erro && <p role="alert" className="text-rose-600 dark:text-rose-400 text-xs">{erro}</p>}
    </form>
  )
}
