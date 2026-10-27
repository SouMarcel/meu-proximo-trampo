/**
 * "Acompanhar empresa" (dash/API.md, spec 031): no detalhe de uma vaga cujo link, ou o de candidatura, é de uma vaga
 * do Greenhouse, do Lever ou do Ashby — inclusive as que vieram do Indeed ou do LinkedIn. Só grava a lista de empresas
 * no clique da pessoa; nenhum pedido vai ao sistema da empresa.
 */
import React, { useEffect, useState } from "react"
import type { Vaga } from "../../types/api"
import * as configApi from "../../services/api/config"
import type { EmpresaAcompanhada } from "../../services/api/config"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta } from "../../contexto/Ferramenta"
import { BTN_MINI } from "../curriculo/Curriculos"

const SISTEMAS: Record<string, string> = { greenhouse: "Greenhouse", lever: "Lever", ashby: "Ashby" }

/** A empresa e o link de onde ela saiu (primeiro o de candidatura); null quando a vaga não é desses sistemas. */
export function empresaDaVaga(v: Vaga): { empresa: EmpresaAcompanhada; link: string } | null {
  for (const link of [v.url_candidatura, v.url]) {
    if (!link) continue
    const empresa = configApi.empresaDoLink(link)
    if (empresa) return { empresa, link }
  }
  return null
}

export default function AcompanharEmpresa({
  vaga,
  onAviso,
}: {
  vaga: Vaga
  onAviso: (m: string, t?: "info" | "erro") => void
}) {
  const { servidor } = useFerramenta()
  const achada = empresaDaVaga(vaga)
  const chave = achada ? `${achada.empresa.sistema}:${achada.empresa.id.toLowerCase()}` : ""
  const [estado, setEstado] = useState<"lendo" | "livre" | "acompanhada" | "gravando">("lendo")

  useEffect(() => {
    if (!chave) return
    let vivo = true
    configApi
      .empresas()
      .then((r) => {
        if (!vivo) return
        const ja = r.empresas.some((x) => `${x.sistema}:${String(x.id).toLowerCase()}` === chave)
        setEstado(ja ? "acompanhada" : "livre")
      })
      .catch(() => vivo && setEstado("livre"))
    return () => {
      vivo = false
    }
  }, [chave])

  if (!achada || estado === "lendo") return null
  const sistema = SISTEMAS[achada.empresa.sistema] || achada.empresa.sistema
  if (estado === "acompanhada") {
    return <span className="text-[11px] text-slate-500 dark:text-slate-400">Acompanhando no {sistema}</span>
  }
  return (
    <button
      type="button"
      className={BTN_MINI}
      disabled={servidor !== "no_ar" || estado === "gravando"}
      title={`A busca passa a trazer as vagas desta empresa no ${sistema}`}
      onClick={async () => {
        setEstado("gravando")
        try {
          const r = await configApi.acompanhar(achada.link)
          setEstado("acompanhada")
          onAviso(`Agora você acompanha a ${r.empresa.nome || r.empresa.id}.`)
        } catch (e) {
          setEstado("livre")
          onAviso(mensagemDeErro(e, "Não deu para acompanhar a empresa."), "erro")
        }
      }}
    >
      Acompanhar empresa
    </button>
  )
}
