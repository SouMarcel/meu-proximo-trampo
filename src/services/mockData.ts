import {
  Vaga,
  FiltrosBusca,
  ConfigIA,
  PerfilUsuario,
  PortalConectado,
  ItemSincronizacao,
  HistoricoCandidatura,
} from "../types/job"

export const MOCK_PERFIL: PerfilUsuario = {
  nome: "Lucas Ferreira",
  cargo_atual: "Engenheiro de Software Pleno / Frontend",
  cargos_alvo: [
    "Senior Frontend Engineer",
    "Fullstack React / Node Developer",
    "Tech Lead Frontend",
    "Engenheiro de Software Sênior",
  ],
  anos_experiencia: 5,
  nivel_ingles: "avancado",
  competencias_chave: [
    "React",
    "TypeScript",
    "Next.js",
    "Tailwind CSS",
    "Node.js",
    "GraphQL",
    "Testes (Jest, Cypress)",
    "Design Systems",
    "Web Performance (Core Web Vitals)",
    "CI/CD (GitHub Actions)",
  ],
  pretensao_salarial_brl: "R$ 14.000 - R$ 18.000 CLT",
  pretensao_salarial_usd: "$5,000 - $7,000 USD / mês Contractor",
  bio: "Engenheiro de Software com 5 anos de experiência focado no ecossistema TypeScript e React. Experiência sólida em arquitetura de microsserviços frontend, otimização de performance e liderança técnica de equipes ágeis.",
  linkedin_url: "https://linkedin.com/in/lucasferreira-dev",
  github_url: "https://github.com/lucasferreira",
  curriculo_atualizado_em: "2025-02-15",
}

export const MOCK_FILTROS_BUSCA: FiltrosBusca = {
  termos: [
    '"frontend engineer"',
    '"desenvolvedor frontend"',
    '"react developer"',
    '"fullstack typescript"',
    '"tech lead frontend"',
  ],
  fontes: [
    "gupy",
    "indeed",
    "linkedin",
    "greenhouse",
    "lever",
    "remoteok",
    "nerdin",
  ],
  localidade: {
    pais: "Brasil",
    estado: "SP",
    cidade: "São Paulo",
    raio_km: 30,
  },
  modelos: {
    remoto: true,
    hibrido: true,
    presencial: false,
  },
  internacional: {
    ativo: true,
    paises: ["Estados Unidos", "Canadá", "Portugal", "Alemanha", "Reino Unido"],
    termos: [
      "Senior Frontend Engineer",
      "Staff Software Engineer",
      "Fullstack TypeScript",
    ],
    regioes: ["Américas", "Global / Worldwide", "Europa"],
    salario_min_anual_usd: 65000,
    fuso_horas: 3,
    contratacao: ["contractor", "eor", "relocation"],
    precisa_sponsor: false,
    fontes: [
      "remoteok",
      "remotive",
      "himalayas",
      "greenhouse",
      "lever",
      "ashby",
    ],
    empresas: ["Automattic", "GitLab", "Stripe", "Vercel", "Shopify"],
  },
  janela_horas: 168,
  tipos_emprego: ["Tempo Integral", "Contractor (PJ)"],
  senioridades: ["pleno", "senior", "especialista"],
  moedas_aceitas: ["BRL", "USD", "EUR"],
  idiomas_aceitos: ["pt", "en"],
  empresas_excluir: ["Consultoria Fake Ltda", "Spam Jobs Inc"],
  analise_automatica: true,
}

export const MOCK_CONFIG_IA: ConfigIA = {
  provedor: "claude",
  modelo: "claude-3-7-sonnet",
  status_conexao: "conectado",
  ultima_verificacao: "Há 12 minutos",
}

export const MOCK_VAGAS: Vaga[] = [
  {
    id: "gupy-nubank-01",
    titulo: "Senior Frontend Engineer - Design System & Core UI",
    empresa: "Nubank",
    plataforma: "Gupy",
    outras_plataformas: ["LinkedIn"],
    local: "São Paulo, SP (Híbrido flexível - 1x/semana)",
    remoto: false,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://nubank.gupy.io/jobs/1029384",
    url_candidatura: "https://nubank.gupy.io/jobs/1029384/apply",
    salario: "R$ 16.500 - R$ 19.500 CLT + RSU",
    tipo: "Tempo Integral (CLT)",
    descricao: `Sobre a oportunidade:
Como Senior Frontend Engineer no Nubank, você atuará no time de Core UI & Design System, construindo componentes acessíveis, de altíssima performance e consistentes utilizados por mais de 100 milhões de clientes na América Latina.

Requisitos essenciais:
- Sólida experiência profissional com React, TypeScript e modernos padrões de JavaScript/CSS.
- Experiência em desenvolvimento e sustentação de Design Systems escaláveis e documentação (Storybook).
- Conhecimento aprofundado em Acessibilidade Web (WCAG 2.1 AA) e Core Web Vitals.
- Foco em testes automatizados (Jest, Testing Library, Cypress ou Playwright).
- Boa comunicação e facilidade para mentoria técnica de pares.

Benefícios:
- Salário competitivo e participação nos lucros (RSUs)
- Vale Alimentação e Vale Refeição flexíveis
- Plano de Saúde Bradesco Top Nacional e Odontológico
- Auxílio Creche e Licença parental estendida
- Gympass / TotalPass
- Subsídio mensal para trabalho remoto`,
    publicada_em: "2025-02-18",
    encontrada_em: "2025-02-19",
    triagem: "seguir",
    etapa: "entrevista",
    etapa_em: "2025-02-21",
    entrevista_em: "2025-02-26 14:00",
    resultado: null,
    anotacao:
      "Primeira conversa com a Talent Partner (Renata) foi ótima! Ela destacou que o time precisa de alguém forte em Storybook e acessibilidade. Entrevista técnica marcada com Tech Lead para quarta-feira.",
    aderencia: 96,
    analise_status: "feita",
    resumo:
      "Excelente compatibilidade (96%). Seu histórico prático em React, TypeScript e criação de Design Systems atende com precisão os requisitos centrais do Nubank.",
    encaixe: [
      "Domínio pleno de React 19, TypeScript e arquitetura de componentes",
      "Experiência com Design Systems e Storybook documentado",
      "Cultura forte de testes unitários e testes de integração",
      "Pretensão salarial perfeitamente alinhada com a faixa oferecida",
    ],
    lacunas: [
      "A vaga menciona uso esporádico de Clojure em serviços de apoio BFF, embora não seja mandatório",
    ],
    alertas: [
      "Exige presença física 1 dia por semana no escritório de Pinheiros/SP",
    ],
    sinais: [
      "Faixa salarial explícita e atraente",
      "Empresa sólida e premiada em satisfação de colaboradores",
      "Equipamento de última geração (MacBook Pro M3 Max) fornecido",
    ],
    ats: null,
    senioridade: ["senior"],
    modelo_trabalho: "hibrido",
    termos: ['"frontend engineer"', '"react developer"'],
    checklist: [
      {
        id: "c1",
        texto:
          "Currículo customizado com foco em Design System & Acessibilidade",
        estado: "pronto",
        categoria: "documentos",
      },
      {
        id: "c2",
        texto:
          "Revisar princípios de Web Accessibility (ARIA roles, contraste, navegação por teclado)",
        estado: "pronto",
        categoria: "preparacao",
      },
      {
        id: "c3",
        texto:
          "Preparar exemplos de decisões arquiteturais do Design System anterior",
        estado: "a_fazer",
        categoria: "entrevista",
      },
    ],
    perguntas_frequentes: [
      {
        id: "p1",
        pergunta:
          "Como você aborda a governança e o versionamento de um Design System compartilhado por dezenas de squads?",
        tipo: "tecnica",
        dica: "Cite versionamento semântico (SemVer), testes visuais de regressão com Chromatic, deprecation warnings controlados e canal direto de contribuição com RFCs.",
      },
      {
        id: "p2",
        pergunta:
          "Conte sobre um desafio complexo de acessibilidade ou performance que você solucionou em produção.",
        tipo: "comportamental",
        dica: "Use o método STAR: mostre a situação de gargalo em Core Web Vitals (ex.: INP ou LCP elevado) e como sua solução reduziu o tempo de interação de 800ms para 90ms.",
      },
    ],
    historias_star: [
      {
        id: "h1",
        titulo:
          "Redução de 45% no tempo de carregamento com Server Components e refatoração do Design System",
        situacao:
          "A plataforma do cliente anterior sofria com TBT (Total Blocking Time) de 1.4s no carregamento do checkout.",
        tarefa:
          "Identificar gargalos nos pacotes de ícones e dependências pesadas do bundle de componentes.",
        acao: "Implementei tree-shaking dinâmico, migrei componentes estáticos para Server Components e adotei lazy loading de SVGs com SVGR.",
        resultado:
          "O bundle inicial caiu de 480kb para 165kb e a pontuação no Google Lighthouse subiu de 62 para 94.",
        competencias: ["React", "Performance", "Webpack/Vite", "Métricas"],
      },
    ],
  },
  {
    id: "gh-vercel-02",
    titulo: "Staff Frontend Platform Engineer",
    empresa: "Vercel",
    plataforma: "Greenhouse",
    outras_plataformas: ["LinkedIn"],
    local: "Remote - Americas (Worldwide)",
    remoto: true,
    area: "internacional",
    pais_vaga: "Estados Unidos",
    idioma: "en",
    url: "https://job-boards.greenhouse.io/vercel/jobs/5918231",
    url_candidatura:
      "https://job-boards.greenhouse.io/vercel/jobs/5918231#apply",
    salario: "$140,000 - $175,000 USD / ano ($11,600 - $14,500/mês)",
    tipo: "Contractor B2B / Full Remote",
    descricao: `About Vercel:
Vercel’s mission is to enable developers to build the open web. We are the creators of Next.js and host millions of high-impact websites worldwide.

The Role:
We are seeking an experienced Staff Frontend Platform Engineer to advance our developer tools, Next.js framework integrations, and edge-first dashboard experiences.

What you'll do:
- Architect resilient, lightning-fast web applications built on Next.js, React Server Components and Turbopack.
- Collaborate across distributed engineering teams across North America, South America, and Europe.
- Drive best practices around telemetry, bundle size constraints, and client-side observability.

Qualifications:
- 5+ years of deep frontend engineering experience in production.
- Mastery of TypeScript, React internals, and HTTP/Web standards.
- Fluent English communication skills (written and spoken).
- Track record of open-source contributions or impactful web platform libraries.`,
    publicada_em: "2025-02-17",
    encontrada_em: "2025-02-18",
    triagem: "seguir",
    etapa: "proposta",
    etapa_em: "2025-02-22",
    resultado: null,
    anotacao:
      "Recebi a carta de oferta! $145,000 USD/ano via Deel. Conversando sobre detalhes do bônus de assinatura e pacote de stock options.",
    aderencia: 92,
    analise_status: "feita",
    resumo:
      "Altíssima compatibilidade internacional (92%). Seu portfólio no GitHub com Next.js e contribuições para bibliotecas TypeScript chamou grande atenção.",
    encaixe: [
      "Experiência aprofundada com Next.js App Router e Server Actions",
      "Inglês fluente para conversação e documentação técnica",
      "Compatibilidade perfeita de fuso horário (UTC-3 encaixa no horário dos EUA/ET)",
    ],
    lacunas: [
      "Requisitos de Staff costumam cobrar mais histórico de publicações ou palestras em conferências",
    ],
    alertas: [
      "Contrato em USD como Contractor internacional (necessário PJ no Brasil via Simples Nacional/Anexo III)",
    ],
    sinais: [
      "Totalmente remoto para candidatos de qualquer lugar do mundo (Worldwide Remote)",
      "Contrato em dólar com estabilidade e plano de saúde internacional incluso",
      "Bônus de home-office de $2,000 USD para montagem do setup",
    ],
    ats: "greenhouse",
    senioridade: ["senior", "especialista"],
    modelo_trabalho: "remoto",
    termos: ['"frontend engineer"', '"react developer"'],
    checklist: [
      {
        id: "cv1",
        texto: "Análise contratual do contrato B2B internacional",
        estado: "pronto",
        categoria: "juridico",
      },
      {
        id: "cv2",
        texto:
          "Consulta com contador especializado em remessas internacionais (Husky/Travelex)",
        estado: "pronto",
        categoria: "financeiro",
      },
      {
        id: "cv3",
        texto: "Enviar resposta de aceite e documentação de identificação",
        estado: "a_fazer",
        categoria: "proposta",
      },
    ],
  },
  {
    id: "li-stone-03",
    titulo: "Tech Lead Frontend - Soluções Bancárias",
    empresa: "Stone",
    plataforma: "LinkedIn",
    outras_plataformas: ["Gupy"],
    local: "Rio de Janeiro, RJ (Remoto elegível para todo o Brasil)",
    remoto: true,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://www.linkedin.com/jobs/view/389102481",
    url_candidatura: "https://stone.gupy.io/jobs/992144",
    salario: "R$ 18.000 - R$ 22.000 CLT",
    tipo: "Tempo Integral (CLT)",
    descricao: `A Stone está em busca de uma liderança técnica para impulsionar a experiência de ponta dos nossos sistemas de pagamentos e banking.

Responsabilidades:
- Liderar tecnicamente um time multidisciplinar de 7 desenvolvedores frontend.
- Definir diretrizes técnicas, boas práticas de código e estratégias de observabilidade com Datadog.
- Planejar ciclos técnicos de redução de débito técnico em conjunto com gerentes de produto.

O que esperamos:
- Experiência prévia em papel de liderança ou senioridade consolidada.
- Vivência em sistemas de alta volumetria e tolerância a falhas.
- Excelente didática e habilidade para negociar prazos técnicos com stakeholders.`,
    publicada_em: "2025-02-16",
    encontrada_em: "2025-02-17",
    triagem: "seguir",
    etapa: "aplicada",
    etapa_em: "2025-02-18",
    resultado: null,
    anotacao:
      "Candidatura enviada pelo LinkedIn com carta de apresentação destacando experiências como mentor e liderança técnica de squads.",
    aderencia: 88,
    analise_status: "feita",
    resumo:
      "Forte aderência (88%). Excelente oportunidade de transição/consolidação do papel de Tech Lead com excelente pacote de benefícios.",
    encaixe: [
      "Trajetória sólida com TypeScript, React e boas práticas",
      "Perfil colaborativo com foco em mentoria técnica",
      "Totalmente remoto sem obrigatoriedade de residir no RJ",
    ],
    lacunas: [
      "Pede vivência comprovada com Datadog e Sentry em ambientes de alta criticidade bancária",
    ],
    alertas: [],
    sinais: [
      "Vaga 100% remota com auxílio alimentação generoso",
      "Empresa em forte expansão no setor financeiro",
    ],
    ats: null,
    senioridade: ["senior", "especialista"],
    modelo_trabalho: "remoto",
    termos: ['"tech lead frontend"', '"frontend engineer"'],
    checklist: [
      {
        id: "s1",
        texto: "Acompanhar status no portal da Stone",
        estado: "pronto",
        categoria: "follow-up",
      },
      {
        id: "s2",
        texto: "Fazer conexão no LinkedIn com o Head de Engenharia da Stone",
        estado: "pronto",
        categoria: "networking",
      },
      {
        id: "s3",
        texto: "Follow-up após 7 dias se não houver resposta",
        estado: "a_fazer",
        categoria: "follow-up",
      },
    ],
  },
  {
    id: "rok-gitlab-04",
    titulo: "Senior Fullstack Engineer (React / Ruby on Rails)",
    empresa: "GitLab",
    plataforma: "RemoteOK",
    outras_plataformas: ["Greenhouse"],
    local: "Worldwide (Anywhere)",
    remoto: true,
    area: "internacional",
    pais_vaga: "Global",
    idioma: "en",
    url: "https://remoteok.com/remote-jobs/gitlab-senior-fullstack",
    url_candidatura: "https://boards.greenhouse.io/gitlab/jobs/4829102",
    salario: "$120,000 - $150,000 USD / ano",
    tipo: "Full-time Remote",
    descricao: `GitLab is an all-remote pioneer company with team members in over 65 countries.

You will work on the Create Stage, improving code review features, merge request performance, and real-time collaboration.

We look for:
- Deep experience in modern JavaScript/TypeScript and Vue or React.
- Working knowledge of backend frameworks (Ruby on Rails, Node or Go).
- Self-driven and autonomous workflow with asynchronous communication.`,
    publicada_em: "2025-02-15",
    encontrada_em: "2025-02-16",
    triagem: "seguir",
    etapa: "salva",
    etapa_em: "2025-02-16",
    resultado: null,
    anotacao:
      "Vaga incrível pela cultura assíncrona do GitLab. Preciso revisar meu resumo em inglês antes de enviar.",
    aderencia: 84,
    analise_status: "feita",
    resumo:
      "Boa aderência (84%). O foco principal é frontend, embora mencione Ruby on Rails como diferencial para fullstack.",
    encaixe: [
      "Cultura assíncrona e forte independência",
      "Experiência com ferramentas de CI/CD e Git internals",
      "Salário em moeda forte com benefícios globais",
    ],
    lacunas: ["Requer experiência prática com Ruby on Rails no backend"],
    alertas: [],
    sinais: [
      "Pioneira em trabalho 100% remoto assíncrono",
      "Transparência total em salários e planos de carreira",
    ],
    ats: "greenhouse",
    senioridade: ["senior"],
    modelo_trabalho: "remoto",
    termos: ["Senior Frontend Engineer", "Fullstack TypeScript"],
  },
  {
    id: "gupy-picpay-05",
    titulo: "Engenheiro de Software Frontend Sênior",
    empresa: "PicPay",
    plataforma: "Gupy",
    local: "São Paulo, SP (Remoto Brasil)",
    remoto: true,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://picpay.gupy.io/jobs/774812",
    url_candidatura: "https://picpay.gupy.io/jobs/774812/candidatar",
    salario: "R$ 15.000 - R$ 18.000 CLT",
    tipo: "Tempo Integral",
    descricao: `No PicPay, buscamos pessoas apaixonadas por tecnologia para revolucionar a forma como as pessoas lidam com dinheiro.

O que você fará:
- Desenvolver interfaces modernas e responsivas para o app e web do PicPay Empresas.
- Trabalhar com React Native e React web em arquitetura modularizada.
- Monitorar métricas de adoção e qualidade técnica.`,
    publicada_em: "2025-02-10",
    encontrada_em: "2025-02-11",
    triagem: "seguir",
    etapa: "encerrada",
    etapa_em: "2025-02-19",
    resultado: "nao_aprovado",
    anotacao:
      "Processo encerrado. Deram feedback educado dizendo que optaram por alguém com maior vivência em React Native para mobile nativo.",
    aderencia: 76,
    analise_status: "feita",
    resumo:
      "Aderência moderada (76%). Vaga pedia forte atuação em React Native além da web.",
    encaixe: ["React web", "TypeScript", "Trabalho remoto"],
    lacunas: ["React Native avançado para Android/iOS"],
    alertas: [],
    sinais: [],
    ats: null,
    senioridade: ["senior"],
    modelo_trabalho: "remoto",
    termos: ['"desenvolvedor frontend"'],
  },
  {
    id: "nerdin-totvs-06",
    titulo: "Desenvolvedor React / Node Pleno",
    empresa: "TOTVS",
    plataforma: "Nerdin",
    outras_plataformas: ["Catho"],
    local: "São Paulo, SP (Híbrido - Zona Norte)",
    remoto: false,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://nerdin.com.br/vaga/desenvolvedor-react-totvs-491",
    url_candidatura: "https://nerdin.com.br/vaga/desenvolvedor-react-totvs-491",
    salario: "R$ 9.000 - R$ 11.000 CLT",
    tipo: "Tempo Integral",
    descricao: `Vaga para atuação no ecossistema ERP da TOTVS em São Paulo.
Requisitos:
- Experiência em React, JavaScript moderno e Node.js.
- Familiaridade com bancos de dados relacionais (PostgreSQL ou SQL Server).
- Disponibilidade para atuação presencial 3 dias por semana.`,
    publicada_em: "2025-02-18",
    encontrada_em: "2025-02-19",
    triagem: "pendente",
    etapa: null,
    resultado: null,
    aderencia: 68,
    analise_status: "feita",
    resumo:
      "Aderência mediana (68%). Salário e modelo híbrido estão abaixo dos seus critérios ideais, mas o stack bate.",
    encaixe: ["React", "Node.js", "Bancos de dados relacionais"],
    lacunas: ["Senioridade buscada é Pleno, perfil do candidato é Sênior"],
    alertas: [
      "Exige 3 dias presenciais na Zona Norte de SP",
      "Remuneração abaixo da faixa pretendida",
    ],
    sinais: ["Estabilidade da empresa"],
    ats: null,
    senioridade: ["pleno"],
    modelo_trabalho: "hibrido",
    termos: ['"react developer"'],
  },
  {
    id: "remotive-shopify-07",
    titulo: "Senior Frontend Developer - Merchant Experience",
    empresa: "Shopify",
    plataforma: "Remotive",
    outras_plataformas: ["We Work Remotely", "Greenhouse"],
    local: "Americas / Remote",
    remoto: true,
    area: "internacional",
    pais_vaga: "Canadá / Américas",
    idioma: "en",
    url: "https://remotive.com/remote-jobs/software-development/senior-frontend-shopify-1029",
    url_candidatura: "https://shopify.com/careers/merchant-experience-1029",
    salario: "$130,000 - $160,000 USD / ano",
    tipo: "Contractor B2B / EOR",
    descricao: `Shopify powers millions of merchants in over 175 countries.
We are digital by default!

As a Senior Frontend Developer:
- Build robust storefront management tools with React, TypeScript and GraphQL.
- Maintain Polaris (Shopify’s open source Design System).
- Contribute to performance enhancements across the entire administrative dashboard.

Benefits:
- Work from anywhere in the Americas
- Home office allowance and equipment
- Annual wellness and learning stipend`,
    publicada_em: "2025-02-19",
    encontrada_em: "2025-02-19",
    triagem: "pendente",
    etapa: null,
    resultado: null,
    aderencia: 95,
    analise_status: "feita",
    resumo:
      "Excepcional compatibilidade (95%). O trabalho envolve manutenção do Polaris Design System da Shopify, perfeitamente alinhado com suas competências-chave.",
    encaixe: [
      "Contribuição direta em Design System aberto (Polaris)",
      "TypeScript e GraphQL no dia a dia",
      "Trabalho remoto internacional sem exigência de visto local",
    ],
    lacunas: [],
    alertas: [],
    sinais: [
      "Oferece patrocínio de visto se o candidato desejar realocação futura para o Canadá",
      "Remuneração de topo de mercado em dólar americano",
      "Subsídio anual de aprendizagem de $3,000 USD",
    ],
    ats: "greenhouse",
    senioridade: ["senior"],
    modelo_trabalho: "remoto",
    termos: ['"frontend engineer"', "Senior Frontend Engineer"],
  },
  {
    id: "indeed-banco-safra-08",
    titulo: "Especialista Frontend Angular / Java",
    empresa: "Banco Safra",
    plataforma: "Indeed",
    local: "São Paulo, SP (Presencial na Av. Paulista)",
    remoto: false,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://br.indeed.com/viewjob?jk=abcdef0123456789",
    salario: "R$ 17.000 CLT",
    tipo: "Presencial 5x na semana",
    descricao: `Vaga 100% presencial na sede da Avenida Paulista.
Requisitos:
- Domínio profundo de Angular 14+ e Java Spring Boot.
- Experiência em desenvolvimento legado e migração de monolitos.
- Traje social completo e atuação das 9h às 18h no escritório.`,
    publicada_em: "2025-02-14",
    encontrada_em: "2025-02-16",
    triagem: "fora",
    motivo_fora: [
      "Modelo de trabalho presencial 100% (filtros exigem Remoto ou Híbrido flexível)",
      "Tecnologia primária é Angular e Java (seu perfil é especialista em React e TypeScript)",
    ],
    etapa: null,
    resultado: null,
    aderencia: 38,
    analise_status: "feita",
    resumo:
      "Fora dos critérios (38%). Modelo presencial rígido e stack tecnológica desalinhada (Angular/Java).",
    encaixe: ["Setor financeiro bancário"],
    lacunas: [
      "Falta de experiência recente com Angular corporativo e backend Java",
    ],
    alertas: ["100% presencial na Av. Paulista", "Código de vestimenta rígido"],
    sinais: [],
    ats: null,
    senioridade: ["especialista"],
    modelo_trabalho: "presencial",
    termos: ['"frontend engineer"'],
  },
  {
    id: "jobicy-deva-09",
    titulo: "Remote React Developer (Bilingual)",
    empresa: "Deva Solutions Inc",
    plataforma: "Jobicy",
    outras_plataformas: ["RemoteOK"],
    local: "Worldwide / LATAM",
    remoto: true,
    area: "internacional",
    pais_vaga: "Estados Unidos",
    idioma: "en",
    url: "https://jobicy.com/jobs/react-developer-deva",
    url_candidatura: "https://jobicy.com/jobs/react-developer-deva/apply",
    salario: "$5,500 - $6,500 USD / month ($66k - $78k/yr)",
    tipo: "Contractor B2B",
    descricao: `Deva Solutions is looking for a talented React Developer based in Latin America to join our client team in fintech.
Requirements:
- 4+ years of hands-on React development.
- Fluent English communication.
- Overlap with US Eastern Time.`,
    publicada_em: "2025-02-18",
    encontrada_em: "2025-02-19",
    triagem: "pendente",
    etapa: null,
    resultado: null,
    aderencia: 89,
    analise_status: "feita",
    resumo:
      "Ótima oportunidade (89%). Vaga remota com salário em dólar dentro da sua faixa de pretensão, com requisitos que batem exatamente com seu perfil.",
    encaixe: [
      "React",
      "TypeScript",
      "Fuso horário alinhado",
      "Inglês avançado",
    ],
    lacunas: [],
    alertas: [],
    sinais: [
      "Pagamento pontual em USD via Deel ou wire transfer",
      "Empresa focada em desenvolvedores da América Latina",
    ],
    ats: null,
    senioridade: ["pleno", "senior"],
    modelo_trabalho: "remoto",
    termos: ['"react developer"', "Senior Frontend Engineer"],
  },
  {
    id: "gupy-itau-10",
    titulo: "Engenheira / Engenheiro de Software Sênior (Design Ops & Web)",
    empresa: "Itaú Unibanco",
    plataforma: "Gupy",
    local: "São Paulo, SP (Híbrido 2x/mês)",
    remoto: false,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://itau.gupy.io/jobs/881293",
    url_candidatura: "https://itau.gupy.io/jobs/881293",
    salario: "R$ 15.800 - R$ 18.200 CLT + PLR Robusto",
    tipo: "Tempo Integral CLT",
    descricao: `Venha fazer parte do maior banco da América Latina!
Atuação no time de Design Ops criando pontes automatizadas entre o Figma e código React.

Requisitos:
- Conhecimento profundo na API de plugins do Figma e Tokens Studio.
- Desenvolvimento de componentes React acessíveis e documentados.
- Boas práticas de CI/CD para publicação de pacotes NPM internos.`,
    publicada_em: "2025-02-17",
    encontrada_em: "2025-02-18",
    triagem: "visitada",
    etapa: null,
    resultado: null,
    anotacao:
      "Optei por não seguir no momento porque prefiro focar nas vagas de trabalho 100% remoto.",
    aderencia: 85,
    analise_status: "feita",
    resumo:
      "Aderência alta (85%). Grande sinergia com design tokens e automação de Design System.",
    encaixe: ["React", "Design Tokens", "Design System", "TypeScript"],
    lacunas: ["Exige familiaridade prévia com a API interna do Figma"],
    alertas: [],
    sinais: ["Participação nos Lucros (PLR) de até 2.5 salários"],
    ats: null,
    senioridade: ["senior"],
    modelo_trabalho: "hibrido",
    termos: ['"frontend engineer"'],
  },
  {
    id: "nerdin-cloud-11",
    titulo: "Desenvolvedor React / Next.js Sênior",
    empresa: "Nubank (via Nerdin Tech)",
    plataforma: "Nerdin",
    local: "São Paulo, SP (100% Remoto)",
    remoto: true,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://nerdin.com.br/vaga/desenvolvedor-react-nubank-980",
    url_candidatura: "https://nerdin.com.br/vaga/desenvolvedor-react-nubank-980",
    salario: "R$ 16.500 - R$ 19.000 CLT",
    tipo: "Tempo Integral (Remoto)",
    descricao: "Vaga publicada recentemente no portal Nerdin Tech. Atuação no ecossistema de cartões de crédito e conta digital.\nRequisitos:\n- Experiência avançada em React, Next.js e TypeScript.\n- Arquitetura de microfrontends e design system em escala.\n- Testes automatizados (Jest, React Testing Library, Cypress).",
    publicada_em: "2025-02-19",
    encontrada_em: "2025-02-19",
    triagem: "pendente",
    etapa: null,
    resultado: null,
    aderencia: undefined,
    analise_status: "pendente",
    resumo: undefined,
    encaixe: [],
    lacunas: [],
    alertas: [],
    sinais: ["Vaga 100% remota com pacote CLT atrativo", "Publicação no portal Nerdin"],
    ats: null,
    senioridade: ["senior"],
    modelo_trabalho: "remoto",
    termos: ["\"react developer\"", "\"frontend engineer\""],
  },
  {
    id: "gupy-picpay-12",
    titulo: "Tech Lead Frontend / Core Banking",
    empresa: "PicPay",
    plataforma: "Gupy",
    local: "São Paulo, SP (100% Remoto)",
    remoto: true,
    area: "nacional",
    pais_vaga: "Brasil",
    idioma: "pt",
    url: "https://picpay.gupy.io/job/eyJqb2JJZCI6OTg1MjAwfQ==",
    url_candidatura: "https://picpay.gupy.io/job/eyJqb2JJZCI6OTg1MjAwfQ==",
    salario: "R$ 19.000 - R$ 23.000 CLT",
    tipo: "Tempo Integral",
    descricao: "Resumo preliminar capturado pelo feed. Descrição completa da vaga ainda está sendo indexada pelo robô de leitura.",
    descricao_pendente: true,
    publicada_em: "2025-02-19",
    encontrada_em: "2025-02-19",
    triagem: "pendente",
    etapa: null,
    resultado: null,
    aderencia: undefined,
    analise_status: "pendente",
    resumo: undefined,
    encaixe: [],
    lacunas: [],
    alertas: ["Descrição completa pendente de extração"],
    sinais: ["Remoto nacional", "Salário acima da média"],
    ats: null,
    senioridade: ["senior", "especialista"],
    modelo_trabalho: "remoto",
    termos: ["\"tech lead frontend\""],
  },
]

export const MOCK_PORTAIS_CONECTADOS: PortalConectado[] = [
  {
    id: "gupy",
    nome: "Gupy",
    plataforma: "Gupy",
    conectado: true,
    aviso_login: "Sessão ativa vinculada via navegador. Candidaturas lidas automaticamente.",
    ultima_sincronizacao: "Hoje às 14:32",
    candidaturas_encontradas: 4,
  },
  {
    id: "indeed",
    nome: "Indeed",
    plataforma: "Indeed",
    conectado: true,
    aviso_login: "Sessão ativa no Indeed Brasil. Candidaturas salvas e enviadas sincronizadas.",
    ultima_sincronizacao: "Hoje às 14:30",
    candidaturas_encontradas: 2,
  },
  {
    id: "linkedin",
    nome: "LinkedIn",
    plataforma: "LinkedIn",
    conectado: false,
    aviso_login: "Faça login com seu perfil do LinkedIn na janela auxiliar da ferramenta.",
    ultima_sincronizacao: undefined,
    candidaturas_encontradas: 0,
  },
];

export const MOCK_ITENS_SINCRONIZACAO: ItemSincronizacao[] = [
  {
    id: "sync-1",
    titulo: "Senior Frontend Engineer (React/TypeScript)",
    empresa: "Nubank",
    plataforma: "Gupy",
    etapa_atual: "aplicada",
    etapa_nova: "entrevista",
    alteracao: "Avançou para: Entrevista com a liderança técnica",
    selecionado: true,
    data_portal: "Ontem às 18:20",
  },
  {
    id: "sync-2",
    titulo: "Desenvolvedor React / Node Pleno",
    empresa: "TOTVS",
    plataforma: "Indeed",
    etapa_atual: "salva",
    etapa_nova: "aplicada",
    alteracao: "Candidatura concluída no portal Indeed",
    selecionado: true,
    data_portal: "Hoje às 09:15",
  },
];

export const MOCK_HISTORICO_CANDIDATURAS: HistoricoCandidatura[] = [
  {
    id: "hist-1",
    titulo: "Frontend Specialist",
    empresa: "Mercado Livre",
    plataforma: "Gupy",
    data: "10/02/2025",
    etapa: "encerrada",
    resultado: "nao_aprovado",
  },
  {
    id: "hist-2",
    titulo: "React Developer",
    empresa: "Itaú Unibanco",
    plataforma: "Indeed",
    data: "05/02/2025",
    etapa: "aplicada",
  },
];
