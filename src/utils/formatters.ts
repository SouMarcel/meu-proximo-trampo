import { Plataforma, Etapa, ModeloTrabalho, Senioridade } from "../types/job"

export function getPlataformaStyle(
  plataforma: Plataforma,
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
 * Classificacao da nota de aderencia calculada pela IA:
 * - >= 85%: Excelente (Verde / Emerald)
 * - >= 65%: Boa (Azul / Sky)
 * - >= 50%: Media (Ambar / Amber)
 * - < 50%: Baixa (Rosa / Rose)
 * - null/undefined: Pendente / Sem nota (Slate)
 */
export function getAderenciaBadge(
  score?: number,
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
      label: "Pendente",
      scoreColor: "text-slate-500",
      boxBorder: "border-slate-800",
      boxGlow: "",
    }
  }

  if (score >= 85) {
    return {
      bg: "bg-emerald-100 dark:bg-emerald-950/60",
      text: "text-emerald-800 dark:text-emerald-300",
      ring: "border-emerald-300 dark:border-emerald-700",
      label: "Excelente",
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
      label: "Média",
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
  if (!dataString) return "Recentemente"
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
  if (remoto) return "100% Remoto"
  if (modelo === "hibrido") return "Híbrido"
  if (modelo === "presencial") return "Presencial"
  return "Remoto / Flexível"
}

export function formatarSenioridade(sen?: Senioridade[]): string {
  if (!sen || sen.length === 0) return "Não informada"
  return sen
    .map((s) => {
      if (s === "junior") return "Júnior"
      if (s === "pleno") return "Pleno"
      if (s === "senior") return "Sênior"
      if (s === "especialista") return "Especialista / Lead"
      return s
    })
    .join(", ")
}
