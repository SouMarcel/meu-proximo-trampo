/** Rótulos dos códigos do servidor (os mesmos de dash/kit.py e do dashboard antigo). */
import type { Etapa, Resultado } from "../types/api"

export const ETAPAS: { valor: Etapa; rotulo: string }[] = [
  { valor: "salva", rotulo: "Salva" },
  { valor: "aplicada", rotulo: "Aplicação Enviada" },
  { valor: "entrevista", rotulo: "Entrevista" },
  { valor: "proposta", rotulo: "Proposta Recebida" },
  { valor: "encerrada", rotulo: "Encerrada" },
]

export const RESULTADOS: Record<Resultado, string> = {
  nao_aprovado: "Não aprovado",
  desisti: "Desisti",
  cancelada: "Vaga cancelada",
  contratado: "Contratado",
}

export const AUTORIZACAO: Record<string, string> = {
  patrocina: "Patrocina visto",
  nao_precisa: "Você não precisa de patrocínio",
  omisso: "O anúncio não diz",
  nao_patrocina: "Não patrocina visto",
}

export const CONTRATACAO: Record<string, string> = {
  contractor: "Contractor (você emite nota)",
  eor: "Por EOR (Deel, Remote…)",
  empregado_brasil: "Empregado no Brasil",
  relocation: "Com relocation",
  clt: "CLT",
  pj: "PJ",
}

export const INGLES: Record<string, string> = {
  nao_pede: "Não pede",
  basico: "Básico",
  intermediario: "Intermediário",
  fluente: "Fluente",
  nativo: "Nativo",
}

export const PEDE: Record<string, string> = {
  curriculo_ingles: "Currículo em inglês",
  carta: "Carta de apresentação",
  formulario: "Respostas de formulário",
  portfolio: "Portfólio",
  teste: "Teste técnico",
  video: "Vídeo de apresentação",
}

export const RISCOS: Record<string, string> = {
  remuneracao: "Remuneração pouco confiável",
  remoto_hibrido: "“Remoto” que é híbrido",
}

export const ESTADOS_KIT: Record<string, string> = {
  a_fazer: "A fazer",
  pronto: "Pronto",
  nao_se_aplica: "Não se aplica",
}

export const TIPOS_EMPREGO: Record<string, string> = {
  tempo_integral: "Tempo integral",
  pj: "PJ",
  meio_periodo: "Meio período",
  estagio: "Estágio",
  temporario: "Temporário",
}
