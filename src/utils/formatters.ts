import type { Etapa, ModeloTrabalho, Senioridade, Vaga, Versao } from "../types/api"

export function getPlataformaStyle(
  plataforma: string,
): {
  bg: string
  text: string
  border: string
  accent: string
} {
  switch (plataforma) {
    case "LinkedIn":
      return {
        bg: "bg-blue-50 dark:bg-blue-950/40",
        text: "text-blue-700 dark:text-blue-300",
        border: "border-blue-200 dark:border-blue-800",
        accent: "#0A66C2",
      }
    case "Gupy":
      return {
        bg: "bg-emerald-50 dark:bg-emerald-950/40",
        text: "text-emerald-700 dark:text-emerald-300",
        border: "border-emerald-200 dark:border-emerald-800",
        accent: "#00C389",
      }
    case "Indeed":
      return {
        bg: "bg-indigo-50 dark:bg-indigo-950/40",
        text: "text-indigo-700 dark:text-indigo-300",
        border: "border-indigo-200 dark:border-indigo-800",
        accent: "#2164f3",
      }
    case "Greenhouse":
      return {
        bg: "bg-teal-50 dark:bg-teal-950/40",
        text: "text-teal-700 dark:text-teal-300",
        border: "border-teal-200 dark:border-teal-800",
        accent: "#00b2a9",
      }
    case "Lever":
      return {
        bg: "bg-amber-50 dark:bg-amber-950/40",
        text: "text-amber-700 dark:text-amber-300",
        border: "border-amber-200 dark:border-amber-800",
        accent: "#f5a623",
      }
    case "Ashby":
      return {
        bg: "bg-purple-50 dark:bg-purple-950/40",
        text: "text-purple-700 dark:text-purple-300",
        border: "border-purple-200 dark:border-purple-800",
        accent: "#8b5cf6",
      }
    case "RemoteOK":
    case "Remotive":
    case "Himalayas":
    case "Jobicy":
    case "We Work Remotely":
      return {
        bg: "bg-violet-50 dark:bg-violet-950/40",
        text: "text-violet-700 dark:text-violet-300",
        border: "border-violet-200 dark:border-violet-800",
        accent: "#7c3aed",
      }
    case "InfoJobs":
      return {
        bg: "bg-rose-50 dark:bg-rose-950/40",
        text: "text-rose-700 dark:text-rose-300",
        border: "border-rose-200 dark:border-rose-800",
        accent: "#e11d48",
      }
    case "Vagas.com":
      return {
        bg: "bg-sky-50 dark:bg-sky-950/40",
        text: "text-sky-700 dark:text-sky-300",
        border: "border-sky-200 dark:border-sky-800",
        accent: "#0284c7",
      }
    case "JobGether":
      return {
        bg: "bg-cyan-50 dark:bg-cyan-950/40",
        text: "text-cyan-700 dark:text-cyan-300",
        border: "border-cyan-200 dark:border-cyan-800",
        accent: "#0891b2",
      }
    case "Nerdin":
    case "Startup Jobs":
      return {
        bg: "bg-orange-50 dark:bg-orange-950/40",
        text: "text-orange-700 dark:text-orange-300",
        border: "border-orange-200 dark:border-orange-800",
        accent: "#ea580c",
      }
    default:
      return {
        bg: "bg-slate-50 dark:bg-slate-800/40",
        text: "text-slate-700 dark:text-slate-300",
        border: "border-slate-200 dark:border-slate-700",
        accent: "#64748b",
      }
  }
}

/**
 * Faixas da nota de aderência (as mesmas do servidor e do dashboard antigo):
 * >= 80 forte, >= 65 boa, >= 50 parcial, abaixo baixa; sem número = sem nota.
 */
export function getAderenciaBadge(
  score?: number | null,
): {
  bg: string
  text: string
  ring: string
  label: string
  scoreColor: string
  boxBorder: string
  boxGlow: string
} {
  if (score === undefined || score === null) {
    return {
      bg: "bg-slate-100 dark:bg-slate-800",
      text: "text-slate-600 dark:text-slate-400",
      ring: "border-slate-300 dark:border-slate-700",
      label: "Sem nota",
      scoreColor: "text-slate-500",
      boxBorder: "border-slate-800",
      boxGlow: "",
    }
  }

  if (score >= 80) {
    return {
      bg: "bg-emerald-100 dark:bg-emerald-950/60",
      text: "text-emerald-800 dark:text-emerald-300",
      ring: "border-emerald-300 dark:border-emerald-700",
      label: "Forte",
      scoreColor: "text-emerald-400",
      boxBorder: "border-emerald-500/50 dark:border-emerald-500/60",
      boxGlow: "shadow-emerald-500/10",
    }
  }
  if (score >= 65) {
    return {
      bg: "bg-sky-100 dark:bg-sky-950/60",
      text: "text-sky-800 dark:text-sky-300",
      ring: "border-sky-300 dark:border-sky-700",
      label: "Boa",
      scoreColor: "text-sky-400",
      boxBorder: "border-sky-500/50 dark:border-sky-500/60",
      boxGlow: "shadow-sky-500/10",
    }
  }
  if (score >= 50) {
    return {
      bg: "bg-amber-100 dark:bg-amber-950/60",
      text: "text-amber-800 dark:text-amber-300",
      ring: "border-amber-300 dark:border-amber-700",
      label: "Parcial",
      scoreColor: "text-amber-400",
      boxBorder: "border-amber-500/50 dark:border-amber-500/60",
      boxGlow: "shadow-amber-500/10",
    }
  }
  return {
    bg: "bg-rose-100 dark:bg-rose-950/60",
    text: "text-rose-800 dark:text-rose-300",
    ring: "border-rose-300 dark:border-rose-700",
    label: "Baixa",
    scoreColor: "text-rose-400",
    boxBorder: "border-rose-500/50 dark:border-rose-500/60",
    boxGlow: "shadow-rose-500/10",
  }
}

export function getEtapaInfo(
  etapa: Etapa | null,
): {
  label: string
  color: string
  badgeBg: string
  badgeText: string
  border: string
} {
  switch (etapa) {
    case "salva":
      return {
        label: "Salva",
        color: "#64748b",
        badgeBg: "bg-slate-100 dark:bg-slate-800",
        badgeText: "text-slate-700 dark:text-slate-300",
        border: "border-slate-300 dark:border-slate-700",
      }
    case "aplicada":
      return {
        label: "Aplicação Enviada",
        color: "#3b82f6",
        badgeBg: "bg-blue-100 dark:bg-blue-950/60",
        badgeText: "text-blue-700 dark:text-blue-300",
        border: "border-blue-300 dark:border-blue-800",
      }
    case "entrevista":
      return {
        label: "Entrevista Agendada",
        color: "#8b5cf6",
        badgeBg: "bg-purple-100 dark:bg-purple-950/60",
        badgeText: "text-purple-700 dark:text-purple-300",
        border: "border-purple-300 dark:border-purple-800",
      }
    case "proposta":
      return {
        label: "Proposta Recebida",
        color: "#10b981",
        badgeBg: "bg-emerald-100 dark:bg-emerald-950/60",
        badgeText: "text-emerald-700 dark:text-emerald-300",
        border: "border-emerald-300 dark:border-emerald-800",
      }
    case "encerrada":
      return {
        label: "Encerrada",
        color: "#6b7280",
        badgeBg: "bg-zinc-100 dark:bg-zinc-800",
        badgeText: "text-zinc-600 dark:text-zinc-400",
        border: "border-zinc-300 dark:border-zinc-700",
      }
    default:
      return {
        label: "Não iniciada",
        color: "#94a3b8",
        badgeBg: "bg-slate-100 dark:bg-slate-800",
        badgeText: "text-slate-500",
        border: "border-slate-200",
      }
  }
}

export function formatarDataRelativa(dataString?: string | null): string {
  if (!dataString) return "Data não informada"
  const partes = dataString.split("T")[0].split("-")
  if (partes.length !== 3) return dataString

  const [ano, mes, dia] = partes.map(Number)
  const data = new Date(ano, mes - 1, dia)
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  data.setHours(0, 0, 0, 0)

  const diffTempo = hoje.getTime() - data.getTime()
  const diffDias = Math.floor(diffTempo / (1000 * 60 * 60 * 24))

  if (diffDias === 0) return "Hoje"
  if (diffDias === 1) return "Ontem"
  if (diffDias < 7) return `Há ${diffDias} dias`
  if (diffDias < 30) {
    const sem = Math.floor(diffDias / 7)
    return `Há ${sem} ${sem === 1 ? "semana" : "semanas"}`
  }
  return `${dia.toString().padStart(2, "0")}/${mes.toString().padStart(2, "0")}/${ano}`
}

export function formatarModelo(
  modelo?: ModeloTrabalho,
  remoto?: boolean,
): string {
  if (modelo === "remoto") return "Remoto"
  if (modelo === "hibrido") return "Híbrido"
  if (modelo === "presencial") return "Presencial"
  if (remoto) return "Remoto"
  return "Modelo não informado"
}

export function formatarSenioridade(sen?: Senioridade[]): string {
  if (!sen || sen.length === 0) return "Não informada"
  return sen
    .map((s) => {
      if (s === "junior") return "Júnior"
      if (s === "pleno") return "Pleno"
      if (s === "senior") return "Sênior"
      return s
    })
    .join(", ")
}


/**
 * Área da vaga: a gravada; nas vagas antigas, internacional só quando todos os itens
 * de grupos começam com internacional: ou mudanca:; no resto dos casos, nacional.
 */
export function areaDe(vaga: Partial<Vaga>): "nacional" | "internacional" {
  if (vaga.area === "nacional" || vaga.area === "internacional") {
    return vaga.area
  }
  const g = vaga.grupos || []
  const fora = g.filter((x) => /^(internacional|mudanca):/.test(x))
  return fora.length > 0 && fora.length === g.length ? "internacional" : "nacional"
}

export function paisDe(vaga: Partial<Vaga>): string {
  if (vaga.pais_vaga) return vaga.pais_vaga
  const g = (vaga.grupos || []).filter((x) => /^(internacional|mudanca):/.test(x))[0]
  return g && g !== "internacional:global" ? g.split(":")[1] : ""
}

/** Modo de trabalho da vaga: o da análise ou da fonte vale mais que a marcação "remoto" do portal. */
export function modoDe(vaga: Vaga): ModeloTrabalho {
  if (vaga.modelo_trabalho && vaga.modelo_trabalho !== "nao_informado") return vaga.modelo_trabalho
  return vaga.remoto ? "remoto" : "nao_informado"
}

/** No quadro: tem etapa e (foi adicionada direto no quadro ou a pessoa seguiu com ela). */
export function noQuadro(vaga: Vaga): boolean {
  return Boolean(vaga.etapa) && (vaga.origem === "manual" || vaga.triagem === "seguir")
}

/** No Relatório: tudo o que não foi adicionado direto no quadro. */
export function noRelatorio(vaga: Vaga): boolean {
  return vaga.origem !== "manual"
}

export function temNota(vaga: Vaga): boolean {
  return typeof vaga.aderencia === "number"
}

export type SituacaoNota =
  | { tipo: "verificando" }
  | { tipo: "falha"; motivo: string }
  | { tipo: "nota"; provisoria: boolean }
  | { tipo: "pendente" } // aguardando a IA
  | { tipo: "descricao_pendente" }
  | { tipo: "sem_nota" }

/** Situação da nota para os selos: verificando → falha → o que a vaga diz (data-model "Estado derivado"). */
export function situacaoNota(vaga: Vaga, versao?: Pick<Versao, "verificando" | "falhas"> | null): SituacaoNota {
  if (versao?.verificando?.includes(vaga.id)) return { tipo: "verificando" }
  const falha = versao?.falhas?.[vaga.id]
  if (falha && !temNota(vaga)) return { tipo: "falha", motivo: falha.motivo }
  if (temNota(vaga)) return { tipo: "nota", provisoria: Boolean(vaga.nota_sem_descricao) }
  if (vaga.descricao_pendente) return { tipo: "descricao_pendente" }
  if (vaga.analise_status === "pendente") return { tipo: "pendente" }
  return { tipo: "sem_nota" }
}

/** Forçar verificar: só para vaga sem nota (ou com nota provisória) em Para decidir ou Fora dos critérios. */
export function podeForcar(vaga: Vaga): boolean {
  return (vaga.triagem === "pendente" || vaga.triagem === "fora") && (!temNota(vaga) || Boolean(vaga.nota_sem_descricao))
}

/** Link só se for http/https (texto da internet é texto). */
export function linkSeguro(url?: string | null): string | undefined {
  return url && /^https?:\/\//i.test(url) ? url : undefined
}

/** Data de hoje no formato AAAA-MM-DD, no fuso do computador. */
export function hoje(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

/** "HH:MM" de uma data ISO. */
export function horaDe(iso?: string | null): string {
  return String(iso || "").slice(11, 16)
}

/** "DD/MM" de uma data ISO ou AAAA-MM-DD. */
export function diaMes(iso?: string | null): string {
  const m = String(iso || "").match(/^(\d{4})-(\d{2})-(\d{2})/)
  return m ? `${m[3]}/${m[2]}` : ""
}

/** Portal pelo endereço do link (o mesmo do dashboard antigo); desconhecido = "Outra". */
export function plataformaDoLink(u: string): string {
  let h = ""
  try {
    h = new URL(u).hostname.toLowerCase()
  } catch {
    return "Outra"
  }
  const pares: [string, string][] = [
    ["indeed.", "Indeed"],
    ["linkedin.", "LinkedIn"],
    ["gupy.io", "Gupy"],
    ["inhire", "InHire"],
    ["catho.", "Catho"],
    ["startup.jobs", "Startup Jobs"],
    ["nerdin.", "Nerdin"],
    ["infojobs.com.br", "InfoJobs"],
    ["vagas.com.br", "Vagas.com"],
    ["jobgether.", "JobGether"],
    ["remotive.", "Remotive"],
    ["himalayas.app", "Himalayas"],
    ["remoteok.", "RemoteOK"],
    ["jobicy.", "Jobicy"],
    ["weworkremotely.", "We Work Remotely"],
    ["getonbrd.", "Get on Board"],
    ["getonboard.", "Get on Board"],
    ["greenhouse.io", "Greenhouse"],
    ["lever.co", "Lever"],
    ["ashbyhq.com", "Ashby"],
  ]
  return pares.find(([trecho]) => h.includes(trecho))?.[1] || "Outra"
}

/** mailto: com o destinatário e o assunto da vaga; nada é enviado pela ferramenta. "" se o e-mail não parece válido. */
export function mailtoDe(v: { email_candidatura?: string; assunto_candidatura?: string }): string {
  const email = String(v.email_candidatura || "")
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return ""
  return "mailto:" + encodeURIComponent(email).replace(/%40/g, "@") + (v.assunto_candidatura ? "?subject=" + encodeURIComponent(v.assunto_candidatura) : "")
}

/** Sem acento e em minúsculas, para comparar textos. */
export function semAcento(s: string): string {
  return s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}
