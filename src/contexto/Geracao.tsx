/**
 * A geração de documentos (currículo, carta, respostas): uma por vez no servidor (dash/API.md §3.8). Consulta o
 * andamento a cada 2 s enquanto escreve, gera ou confere; quando termina, avisa e faz as listas abertas relerem.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import * as curriculoApi from "../services/api/curriculo"
import type { EstadoGeracao } from "../services/api/curriculo"
import { useConsulta } from "../hooks/useConsulta"
import { mensagemDeErro } from "../services/api"
import { useFerramenta } from "./Ferramenta"

interface ValorGeracao {
  estado: EstadoGeracao | null
  ativa: boolean
  /** Sobe quando uma geração termina: as listas de currículos e documentos releem. */
  versao: number
  /** Depois de um POST que começou uma geração (currículo, carta, respostas). */
  comecou: (e: EstadoGeracao) => void
  tentar: () => Promise<void>
}

const Contexto = createContext<ValorGeracao | null>(null)

const NOMES: Record<string, string> = { carta: "A carta", respostas: "As respostas" }

export function GeracaoProvider({
  children,
  onAviso,
}: {
  children: React.ReactNode
  onAviso: (m: string, t?: "info" | "erro") => void
}) {
  const { servidor, tratarErro } = useFerramenta()
  const [estado, setEstado] = useState<EstadoGeracao | null>(null)
  const [versao, setVersao] = useState(0)
  const antes = useRef<EstadoGeracao | null>(null)
  const aviso = useRef(onAviso)
  aviso.current = onAviso

  const ativa = Boolean(estado && curriculoApi.SITUACOES_ATIVAS.includes(estado.situacao))

  const consultar = useCallback(async () => {
    try {
      const j = await curriculoApi.estado()
      const a = antes.current
      antes.current = j
      setEstado(j)
      if (a && curriculoApi.SITUACOES_ATIVAS.includes(a.situacao) && !curriculoApi.SITUACOES_ATIVAS.includes(j.situacao)) {
        setVersao((n) => n + 1)
        const nome = NOMES[j.tipo || ""] || "O currículo"
        if (j.situacao === "pronto") {
          if (j.pronto) {
            aviso.current(
              nome + (j.tipo === "respostas" ? " estão prontas: confira e responda as que são só suas." : " saiu e foi conferido."),
            )
          } else {
            aviso.current(nome + " saiu, mas a conferência bloqueou: veja os pontos.", "erro")
          }
        } else if (j.situacao === "falha") {
          aviso.current(`${nome} não saiu: ${j.mensagem || "falha"}`, "erro")
        }
      }
    } catch {
      // sem resposta: o aviso de servidor fora vem da consulta da versão
    }
  }, [])

  useEffect(() => {
    if (servidor === "no_ar") consultar()
  }, [servidor, consultar])

  useConsulta(consultar, 2000, servidor === "no_ar" && ativa)

  const comecou = useCallback((e: EstadoGeracao) => {
    antes.current = e
    setEstado(e)
  }, [])

  const tentar = useCallback(async () => {
    try {
      comecou(await curriculoApi.tentar())
    } catch (e) {
      tratarErro(e)
      aviso.current(mensagemDeErro(e, "Não deu para tentar de novo."), "erro")
    }
  }, [comecou, tratarErro])

  const valor = useMemo(() => ({ estado, ativa, versao, comecou, tentar }), [estado, ativa, versao, comecou, tentar])
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useGeracao(): ValorGeracao {
  const v = useContext(Contexto)
  if (!v) throw new Error("useGeracao fora do GeracaoProvider")
  return v
}

/** A geração em curso (ou a última) é deste alvo? alvo: id da vaga, ou null para o currículo base. */
export function ehDoAlvo(e: EstadoGeracao | null, alvo: string | null, tipos: string[]): boolean {
  if (!e || !e.alvo) return false
  if (!tipos.includes(e.tipo || "curriculo")) return false
  return alvo ? e.alvo.vaga_id === alvo : Boolean(e.alvo.base)
}
