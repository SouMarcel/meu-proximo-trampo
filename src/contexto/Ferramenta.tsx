/**
 * Estado que todas as telas precisam (research R6): se o servidor está no ar, se este aparelho pode gravar
 * (dash/API.md §1, pode_alterar) e qual IA está escolhida (para "IA só no clique, com o aviso de custo").
 */
import React, { createContext, useCallback, useContext, useMemo, useState } from "react"
import { Lock } from "lucide-react"
import { ehErroApi } from "../services/api"
import * as iaApi from "../services/api/ia"

export type SituacaoServidor = "conectando" | "no_ar" | "fora" | "demo"

export interface ResumoIA {
  disponivel: boolean
  nome: string
  modelo: string
  cobranca: "uso" | "assinatura" | "gratuito" | ""
}

interface ValorFerramenta {
  servidor: SituacaoServidor
  setServidor: (s: SituacaoServidor) => void
  /** Pode gravar: servidor no ar (não demonstração) e este aparelho é o computador da ferramenta. */
  podeGravar: boolean
  podeAlterar: boolean
  registrarPodeAlterar: (valor: boolean | undefined) => void
  /** Trata um erro de API: 403 numa rota [local] vira modo só leitura. */
  tratarErro: (e: unknown) => void
  ia: ResumoIA | null
  recarregarIA: () => Promise<void>
  /** Sem IA disponível, abre o painel IA e devolve false. */
  exigirIA: () => boolean
  abrirPainelIA: () => void
}

const Contexto = createContext<ValorFerramenta | null>(null)

const MOTIVO_SO_LEITURA = "Só dá para fazer isso no computador onde a ferramenta roda."

export function FerramentaProvider({
  children,
  onAbrirPainelIA,
}: {
  children: React.ReactNode
  onAbrirPainelIA: () => void
}) {
  const [servidor, setServidor] = useState<SituacaoServidor>("conectando")
  const [podeAlterar, setPodeAlterar] = useState(true)
  const [ia, setIa] = useState<ResumoIA | null>(null)

  const registrarPodeAlterar = useCallback((valor: boolean | undefined) => {
    if (typeof valor === "boolean") setPodeAlterar(valor)
  }, [])

  const tratarErro = useCallback((e: unknown) => {
    if (ehErroApi(e) && e.status === 403 && /computador onde a ferramenta roda/.test(e.message)) {
      setPodeAlterar(false)
    }
  }, [])

  const recarregarIA = useCallback(async () => {
    try {
      const e = await iaApi.estado()
      const p = e.provedores.find((x) => x.id === e.efetiva)
      setIa({
        disponivel: e.disponivel,
        nome: p?.nome || "",
        modelo: e.modelo_efetivo || "",
        cobranca: e.cobranca_efetiva ?? p?.cobranca ?? "",
      })
      setPodeAlterar(e.pode_alterar)
    } catch {
      setIa(null)
    }
  }, [])

  const exigirIA = useCallback(() => {
    if (ia?.disponivel) return true
    onAbrirPainelIA()
    return false
  }, [ia, onAbrirPainelIA])

  const valor = useMemo<ValorFerramenta>(
    () => ({
      servidor,
      setServidor,
      podeGravar: servidor === "no_ar" && podeAlterar,
      podeAlterar,
      registrarPodeAlterar,
      tratarErro,
      ia,
      recarregarIA,
      exigirIA,
      abrirPainelIA: onAbrirPainelIA,
    }),
    [servidor, podeAlterar, registrarPodeAlterar, tratarErro, ia, recarregarIA, exigirIA, onAbrirPainelIA],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useFerramenta(): ValorFerramenta {
  const v = useContext(Contexto)
  if (!v) throw new Error("useFerramenta fora do FerramentaProvider")
  return v
}

/** Motivo de um botão de gravar estar desligado, ou "" quando pode gravar. */
export function motivoSemGravar(servidor: SituacaoServidor, podeAlterar: boolean): string {
  if (servidor === "demo") return "Modo demonstração: nada é gravado."
  if (servidor === "fora" || servidor === "conectando") return "O servidor da ferramenta não está respondendo."
  if (!podeAlterar) return MOTIVO_SO_LEITURA
  return ""
}

/** Aviso curto ao lado de botões desligados (só leitura, demonstração ou servidor fora). */
export function AvisoSoLeitura({ className = "" }: { className?: string }) {
  const { servidor, podeAlterar } = useFerramenta()
  const motivo = motivoSemGravar(servidor, podeAlterar)
  if (!motivo) return null
  return (
    <p className={`flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400 ${className}`}>
      <Lock className="w-3 h-3 shrink-0" />
      <span>{motivo}</span>
    </p>
  )
}

/** Texto do aviso de custo da IA, para os diálogos que chamam a IA. */
export function textoCustoIA(ia: { nome: string; modelo: string; cobranca: string } | null): string {
  if (!ia || !ia.nome) return "Nenhuma IA escolhida."
  const quem = ia.nome + (ia.modelo ? " · " + ia.modelo : "")
  if (ia.cobranca === "uso") return `Vai rodar: ${quem}. Cobrado por uso na sua conta do provedor: consome créditos.`
  if (ia.cobranca === "gratuito") return `Vai rodar: ${quem}. Modelo gratuito: sem custo, com limite de pedidos por dia no provedor.`
  return `Vai rodar: ${quem}.`
}
