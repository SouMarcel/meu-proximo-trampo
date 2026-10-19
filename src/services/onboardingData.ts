import {
  PerguntaAnamnese,
  ItemDiagnostico,
  ConflitoMaterial,
  EstadoOnboarding,
} from "../types/job"

export const ONBOARDING_PERGUNTAS: PerguntaAnamnese[] = [
  {
    id: "cargos_alvo",
    tipo: "lista",
    texto:
      "Quais cargos você busca? Um por linha (ex.: Senior Frontend Engineer, Tech Lead React).",
    dica: "Seja específico. Quanto mais preciso o cargo, mais certeira é a análise de aderência da IA.",
  },
  {
    id: "cargos_alvo_en",
    tipo: "lista",
    texto:
      "E como esses cargos aparecem em inglês, para vagas internacionais? Um por linha.",
    dica: "Ex.: Senior Frontend Developer, Staff Engineer, Fullstack React Specialist. Deixe em branco se não busca vagas em inglês.",
  },
  {
    id: "senioridade",
    tipo: "multi",
    texto: "Em que níveis de senioridade você deseja buscar vagas?",
    opcoes: [
      { valor: "junior", rotulo: "Júnior" },
      { valor: "pleno", rotulo: "Pleno" },
      { valor: "senior", rotulo: "Sênior" },
      { valor: "especialista", rotulo: "Especialista / Tech Lead" },
    ],
  },
  {
    id: "modelos",
    tipo: "multi",
    texto: "Quais modelos de trabalho você aceita?",
    opcoes: [
      { valor: "remoto", rotulo: "100% Remoto" },
      { valor: "hibrido", rotulo: "Híbrido (1 a 3 dias no escritório)" },
      { valor: "presencial", rotulo: "100% Presencial" },
    ],
  },
  {
    id: "cidade",
    tipo: "texto",
    texto:
      "Em que cidade você reside atualmente (relevante para vagas híbridas/presenciais)?",
    dica: "Ex.: São Paulo, Campinas, Curitiba, Belo Horizonte",
  },
  {
    id: "estado",
    tipo: "texto",
    texto: "E qual o Estado? Use a sigla de 2 letras.",
    dica: "Ex.: SP, RJ, MG, PR, SC",
  },
  {
    id: "pretensao",
    tipo: "texto",
    texto: "Qual a sua pretensão salarial e modelo de contratação preferido?",
    dica: "Ex.: R$ 15.000 a R$ 18.000 CLT ou R$ 22.000 PJ. Se não quiser definir agora, pode pular.",
  },
  {
    id: "nao_aceita",
    tipo: "texto",
    texto: "O que você NÃO ACEITA de forma alguma em uma proposta de emprego?",
    dica: "Ex.: Trabalho presencial obrigatório, regime PJ sem benefícios, escala de sobreaviso aos finais de semana, viagens frequentes.",
  },
  {
    id: "conquista:0",
    tipo: "texto",
    texto: "Qual foi a sua MAIOR CONQUISTA no seu cargo mais recente?",
    dica: "Foque na ação que você liderou ou implementou diretamente (ex.: liderei a reformulação da arquitetura frontend reduzindo o tempo de carregamento).",
  },
  {
    id: "medida:0",
    tipo: "texto",
    texto: "Como essa conquista foi MEDIDA em números ou impacto prático?",
    dica: "Escreva números se tiver certeza (ex.: latência caiu de 800ms para 120ms, conversão aumentou 18%, economia de R$ 40k/mês). Se não houve medição, pode deixar em branco.",
  },
  {
    id: "conquista:1",
    tipo: "texto",
    texto:
      "E no seu cargo ou experiência anterior, qual projeto ou entrega trouxe maior destaque?",
    dica: "Pense em processos que você otimizou, bugs críticos resolvidos ou mentoria de pessoas.",
  },
  {
    id: "medida:1",
    tipo: "texto",
    texto: "Como ela foi mensurada ou avaliada?",
    dica: "Ex.: equipe entregou 3 sprints no prazo sem bugs críticos, adoção de testes aumentou de 30% para 85%.",
  },
  {
    id: "ferramentas",
    tipo: "lista",
    texto:
      "Quais ferramentas, frameworks e métodos você domina e em que nível? Um por linha.",
    dica: "Ex.: React — avançado\nTypeScript — avançado\nNext.js — avançado\nJest / Testing Library — intermediário\nGraphQL — intermediário\nTailwind CSS — avançado",
  },
  {
    id: "idiomas",
    tipo: "lista",
    texto: "Quais idiomas você fala e em que nível? Um por linha.",
    dica: "Ex.: Português — nativo\nInglês — avançado\nEspanhol — básico",
  },
  {
    id: "ingles",
    tipo: "opcoes",
    texto:
      "Qual o seu nível de comunicação em inglês para entrevistas e reuniões?",
    opcoes: [
      { valor: "nenhum", rotulo: "Não falo" },
      { valor: "basico", rotulo: "Básico (leitura técnica apenas)" },
      {
        valor: "intermediario",
        rotulo: "Intermediário (compreendo e falo com esforço)",
      },
      {
        valor: "avancado",
        rotulo: "Avançado (participo de reuniões e debates técnicos)",
      },
      {
        valor: "fluente",
        rotulo: "Fluente ou Nativo (comunicação plena e negociações)",
      },
    ],
  },
  {
    id: "interesse_exterior",
    tipo: "sim_nao",
    texto:
      "Você tem interesse em vagas de empresas do exterior (remoto ou internacional)?",
  },
  {
    id: "exterior_remoto",
    tipo: "sim_nao",
    condicao: "interesse_exterior",
    texto:
      "Trabalhando de forma remota, residindo no Brasil com pagamento em moeda forte?",
  },
  {
    id: "exterior_paises",
    tipo: "lista",
    condicao: "interesse_exterior",
    texto: "De quais países ou regiões você aceitaria vagas? Um por linha.",
    dica: "Ex.: Estados Unidos\nCanadá\nPortugal\nAlemanha\nReino Unido\nAmérica Latina",
  },
  {
    id: "morar_fora",
    tipo: "texto",
    condicao: "interesse_exterior",
    texto:
      "Aceitaria morar fora do Brasil se a empresa oferecer pacote de realocação?",
    dica: "Ex.: Sim, aceitaria para Europa ou Canadá. Deixe em branco se só aceita posições 100% remotas sem mudança.",
  },
  {
    id: "passaporte",
    tipo: "sim_nao",
    condicao: "interesse_exterior",
    texto: "Possui passaporte com validade de pelo menos 6 meses?",
  },
  {
    id: "autorizacao",
    tipo: "texto",
    condicao: "interesse_exterior",
    texto:
      "Possui cidadania estrangeira ou visto de trabalho liberado para algum país?",
    dica: "Ex.: Cidadania italiana/europeia, visto H1-B, etc. Deixe vazio se não possui.",
  },
  {
    id: "sponsor",
    tipo: "sim_nao",
    condicao: "interesse_exterior",
    texto:
      "Para posições com realocação física, precisaria de patrocínio de visto (sponsor)?",
  },
  {
    id: "fuso",
    tipo: "texto",
    condicao: "interesse_exterior",
    texto: "Quantas horas de diferença de fuso horário você aceita tolerar?",
    dica: "Ex.: Até 3 horas de sobreposição com US Eastern Time (UTC-5), ou até 4 horas com Londres.",
  },
  {
    id: "contratacao",
    tipo: "multi",
    condicao: "interesse_exterior",
    texto: "Quais modelos de contratação internacional você aceita?",
    opcoes: [
      {
        valor: "contractor",
        rotulo: "Contractor B2B (você abre PJ no Brasil e emite nota)",
      },
      {
        valor: "eor",
        rotulo: "EOR (contrato CLT via intermediadora como Deel ou Remote)",
      },
      { valor: "pj", rotulo: "PJ direto no Brasil" },
      {
        valor: "relocation",
        rotulo: "Contrato local no país de destino com visto de trabalho",
      },
    ],
  },
]

export const MOCK_CONFLITOS: ConflitoMaterial[] = [
  {
    id: "c1",
    campo: "Data de término do último cargo",
    opcoes: [
      {
        valor: "Até o momento (Emprego Atual)",
        fonte: "LinkedIn Export (ZIP)",
      },
      { valor: "Novembro de 2024", fonte: "Curriculo_Lucas_Ferreira.pdf" },
    ],
    escolha: 0,
  },
]

export function diagnosticarPerfil(
  respostas: Record<string, any>,
): ItemDiagnostico[] {
  const diag: ItemDiagnostico[] = []

  const cargos = respostas["cargos_alvo"]
  if (!cargos || (Array.isArray(cargos) && cargos.length === 0)) {
    diag.push({
      tipo: "falta",
      mensagem: "Falta definir pelo menos um cargo-alvo.",
      pergunta:
        "Defina os cargos que você busca para que a IA possa classificar as vagas com precisão.",
      pergunta_id: "cargos_alvo",
    })
  }

  const medida0 = respostas["medida:0"]
  if (!medida0 || String(medida0).trim().length === 0) {
    diag.push({
      tipo: "fraco",
      mensagem:
        "Sua conquista mais recente não possui número ou métrica de impacto mensurável.",
      pergunta:
        "Recrutadores de elite e filtros de IA priorizam candidatos com resultados tangíveis (ex.: %, tempo, R$).",
      pergunta_id: "medida:0",
    })
  }

  const ingles = respostas["ingles"]
  if (!ingles) {
    diag.push({
      tipo: "falta",
      mensagem: "Nível de proficiência em inglês não informado.",
      pergunta:
        "Indispensável para o cálculo de aderência em vagas internacionais e multinacionais.",
      pergunta_id: "ingles",
    })
  }

  const naoAceita = respostas["nao_aceita"]
  if (!naoAceita || String(naoAceita).trim().length === 0) {
    diag.push({
      tipo: "info",
      mensagem: "Você não definiu critérios inegociáveis de exclusão.",
      pergunta:
        "Adicionar critérios como 'PJ sem benefícios' ou 'presencial diário' impede que você perca tempo com vagas indesejadas.",
      pergunta_id: "nao_aceita",
    })
  }

  const ferramentas = respostas["ferramentas"]
  if (!ferramentas || (Array.isArray(ferramentas) && ferramentas.length < 3)) {
    diag.push({
      tipo: "fraco",
      mensagem: "Poucas ferramentas e frameworks cadastrados.",
      pergunta: "Cadastre pelo menos 4 a 6 tecnologias centrais do seu stack.",
      pergunta_id: "ferramentas",
    })
  }

  return diag
}

export function gerarMarkdownPerfil(
  nome: string,
  respostas: Record<string, any>,
  contato: { email?: string; telefone?: string; linkedin?: string },
): string {
  const cargos = (respostas["cargos_alvo"] || ["Engenheiro de Software"]).join(
    ", ",
  )
  const senioridades = (respostas["senioridade"] || ["senior"]).join(", ")
  const modelos = (respostas["modelos"] || ["remoto"]).join(", ")
  const cidade = respostas["cidade"] || "São Paulo"
  const estado = respostas["estado"] || "SP"
  const pretensao = respostas["pretensao"] || "A combinar"
  const naoAceita = respostas["nao_aceita"] || "Nenhum"
  const ingles = respostas["ingles"] || "avancado"
  const conquista =
    respostas["conquista:0"] ||
    "Desenvolvimento e liderança técnica de soluções web de alta escala."
  const medida = respostas["medida:0"] || ""

  return `# Perfil Profissional: ${nome}

## Dados de Contato e Presença
- E-mail: ${contato.email || "lucas.ferreira@email.com"}
- Telefone: ${contato.telefone || "+55 11 98765-4321"}
- LinkedIn: ${contato.linkedin || "linkedin.com/in/lucasferreira-dev"}
- Localidade: ${cidade}, ${estado} - Brasil

## Objetivos e Critérios de Busca
- **Cargos-alvo**: ${cargos}
- **Senioridade pretendida**: ${senioridades}
- **Modelos de trabalho aceitos**: ${modelos}
- **Pretensão salarial**: ${pretensao}
- **Critérios de corte (Não aceita)**: ${naoAceita}

## Competências Linguísticas & Prontidão Internacional
- **Nível de Inglês**: ${ingles}
- **Interesse Internacional**: ${
    respostas["interesse_exterior"] ? "Sim (Remoto ou Relocation)" : "Não"
  }
- **Países aceitos**: ${(respostas["exterior_paises"] || []).join(", ") || "Global"}
- **Passaporte válido**: ${respostas["passaporte"] ? "Sim" : "Não informado"}

## Destaques de Impacto & Conquistas Principais
### Experiência Recente
- **Conquista**: ${conquista}
${medida ? `- **Métrica mensurável**: ${medida}` : ""}

## Principais Ferramentas e Domínio Técnico
${(respostas["ferramentas"] || ["React — avançado", "TypeScript — avançado", "Next.js — avançado"]).map((f: string) => `- ${f}`).join("\n")}

---
*Perfil estruturado para consumo de agentes de IA na triagem de aderência e preparação de entrevistas.*
`
}
