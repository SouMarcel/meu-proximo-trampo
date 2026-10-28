/**
 * Vaga segura (spec 034): o que o filtro de integridade achou no texto da vaga e de quem é o domínio do link.
 * Só avisa: a vaga segue para todos os fluxos.
 */
import React from "react"
import { AlertTriangle, ShieldCheck } from "lucide-react"
import type { Integridade, Vaga } from "../types/api"

const CONTAGENS: Record<keyof Integridade["contagens"], string> = {
  instrucoes: "linha(s) com cara de instrução para a IA",
  adulteracao: "caractere(s) invisível(is) de adulteração, tirado(s)",
  alfabetos: "palavra(s) que misturam alfabetos",
  ocultos: "trecho(s) oculto(s) com sinal, tirado(s)",
  links_ocultos: "link(s) escondido(s), tirado(s)",
  invisiveis: "caractere(s) invisível(is) comum(ns), tirado(s)",
}

const TIPOS: Record<Integridade["citacoes"][number]["tipo"], string> = {
  instrucao: "Instrução",
  alfabetos: "Alfabetos misturados",
  adulteracao: "Texto invisível",
  oculto: "Trecho oculto",
  link_oculto: "Link escondido",
}

export function comAviso(vaga: Vaga): boolean {
  return vaga.integridade?.veredito === "atencao"
}

/** Selos curtos para a lista e o cartão: texto suspeito e fonte não verificada. */
export function SeloIntegridade({ vaga }: { vaga: Vaga }) {
  const naoVerificada = vaga.origem_link?.tipo === "nao_verificada"
  if (!comAviso(vaga) && !naoVerificada) return null
  return (
    <>
      {comAviso(vaga) && (
        <span
          className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[11px] font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800"
          title="O texto desta vaga parece mirar a IA. Veja o que foi achado na aba Descrição."
        >
          <AlertTriangle className="w-3 h-3" />
          <span>Texto suspeito</span>
        </span>
      )}
      {naoVerificada && (
        <span
          className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
          title={`O link é de ${vaga.origem_link?.dominio}, que não é um portal nem um sistema de vagas conhecido.`}
        >
          <AlertTriangle className="w-3 h-3" />
          <span>Fonte não verificada</span>
        </span>
      )}
    </>
  )
}

/** Origem do link em uma linha, para o detalhe e a confirmação do Adicionar Vaga. */
export function OrigemDoLink({ vaga }: { vaga: Vaga }) {
  const o = vaga.origem_link
  if (!o) return null
  if (o.tipo === "nao_verificada") {
    return (
      <p className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs text-amber-900 dark:text-amber-200">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span>
          <b>Fonte não verificada: {o.dominio}.</b> Não é um portal nem um sistema de vagas conhecido. Confira se o site é
          mesmo da empresa antes de passar seus dados.
        </span>
      </p>
    )
  }
  return (
    <p className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
      <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
      <span>
        {o.tipo === "portal" ? "Portal conhecido" : "Sistema de vagas oficial"} ({o.nome}): {o.dominio}
      </span>
    </p>
  )
}

/** O que o filtro achou no texto: citações e contagens. O conteúdo oculto tirado nunca é mostrado (não é guardado). */
export function BlocoIntegridade({ vaga }: { vaga: Vaga }) {
  const i = vaga.integridade
  if (!i) return null
  const contagens = (Object.keys(CONTAGENS) as (keyof Integridade["contagens"])[]).filter((k) => i.contagens[k])
  if (i.veredito !== "atencao") {
    return (
      <p className="text-[11px] text-slate-500 dark:text-slate-400">
        Limpeza do texto: {contagens.map((k) => `${i.contagens[k]} ${CONTAGENS[k]}`).join("; ")}.
      </p>
    )
  }
  return (
    <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 space-y-2">
      <p className="flex items-start gap-2 text-xs text-rose-900 dark:text-rose-200">
        <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
        <span>
          <b>O texto desta vaga parece mirar a IA.</b> A ferramenta tirou o que não aparece na tela e avaliou a vaga sozinha,
          sem misturar com outras. Decida você se segue com ela.
        </span>
      </p>
      {i.citacoes.length > 0 && (
        <ul className="space-y-1 pl-6 text-xs text-rose-900 dark:text-rose-200">
          {i.citacoes.map((c, k) => (
            <li key={k} className="list-disc">
              <span className="font-semibold">{TIPOS[c.tipo] || c.tipo}:</span> <span className="break-words">“{c.trecho}”</span>
            </li>
          ))}
        </ul>
      )}
      <p className="pl-6 text-[11px] text-rose-800/80 dark:text-rose-300/80">
        {contagens.map((k) => `${i.contagens[k]} ${CONTAGENS[k]}`).join("; ")}
      </p>
    </div>
  )
}

/** Lembrete na aba da análise: a nota de uma vaga com texto suspeito merece conferência. */
export function LembreteNota({ vaga }: { vaga: Vaga }) {
  if (!comAviso(vaga)) return null
  return (
    <p className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-900 dark:text-rose-200">
      <AlertTriangle className="w-4 h-4 shrink-0" />O texto desta vaga tinha sinais de mirar a IA; confira a nota (o que foi
      achado está na aba Descrição).
    </p>
  )
}
