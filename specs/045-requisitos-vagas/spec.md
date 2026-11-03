# Feature Specification: O que as vagas pedem, no painel Métricas & Funil

**Feature Branch**: `045-requisitos-vagas` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-03

**Status**: Implementada em 2026-11-03; em teste na branch pessoal

**Input**: User description: "podemos seguir com a melhoria no painel de metricas e funil. colque ali em habilidades
mais desejadas pelas vagas que a pessoa esta aplicando, tbm tempo na atividade mais solicitadas e damais indicadores
mais pedidos para as profissoes que a pessoas esta prcurando. adicione tbm as ccertificações e cursos que sao mais
desejados. obs. experiencia nao é uma habilidade. coloque em um quadro tbm as habilidades do aplicante e identifique as
que mais se identificam com as desejadas." (03/11/2026). Decisões da mesma data em Clarifications.

## Contexto

- **O que o painel Métricas & Funil mostra hoje:**
  - quatro números: Total rastreadas, Conversão para entrevista, Média de aderência e Ofertas & propostas;
  - o funil, de Descobertas a Contratado;
  - a Distribuição por plataforma;
  - o quadro **Habilidades Mais Valorizadas nas Vagas**. Ele pega só a primeira palavra de cada item de Encaixe da
    análise (as frases sobre o que a pessoa já tem). O resultado são palavras soltas ("Experiência", "Conhecimento",
    "Gestão") contadas como habilidades, e nada do que falta à pessoa aparece ali.
- **O que a análise da IA guarda de cada vaga:**
  - a nota, o resumo, o Encaixe, as Lacunas e os alertas, todos em frases;
  - senioridade, modelo de trabalho e tipo de emprego;
  - o nível de inglês pedido e a contratação (CLT, PJ, contractor, EOR, relocation), cada um com a frase do anúncio.

  As habilidades, as certificações e cursos, os anos de experiência e a formação pedidos não ficam guardados à parte:
  estão só no texto do anúncio e nas frases da análise.
- **Análises do perfil** (Meu perfil, spec 012) já lista as lacunas mais frequentes nas vagas, em frases agrupadas,
  sem IA. Essa análise continua como está: esta spec trata do painel de métricas.
- **O perfil da pessoa** (`perfil.md`) tem as seções Habilidades e ferramentas (com nível), Certificações, Formação e
  Idiomas, que são a fonte do quadro com as habilidades dela.
- **Num uso real:** a maior parte das vagas tinha análise e o texto do anúncio, mas em Aplicações perto da metade
  não tinha: foram adicionadas à mão ou trazidas pelas contas conectadas, sem o texto.

## Clarifications

### Session 2026-11-03

- Q: Como o painel obtém as habilidades, certificações e anos de experiência das vagas? → A: A análise da IA passa a
  separar esses requisitos. Para as vagas já analisadas, um botão no painel lê só os requisitos com a IA, em lotes,
  sem mudar a nota.
- Q: De quais vagas o painel conta o que é pedido? → A: A pessoa escolhe no painel: Em Aplicações (o padrão, as vagas a
  que ela se candidata) ou Todas as vagas analisadas (as profissões que ela procura); e Nacionais, Internacionais ou as
  duas.
- Q: Além de habilidades, certificações e cursos e tempo de experiência, que indicadores entram? → A: Formação,
  idiomas, senioridade e modelo de trabalho, e tipo de contratação.
- Pedido da pessoa: experiência não é habilidade. Tempo de experiência vai num indicador à parte e nunca aparece na
  lista de habilidades.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver as habilidades, certificações e o tempo de experiência que as vagas pedem (Priority: P1)

A pessoa abre Métricas & Funil e, numa seção nova, **O que as vagas pedem**, vê:

- as habilidades mais pedidas, em dois grupos: técnicas e ferramentas, e comportamentais;
- as certificações e cursos mais pedidos;
- o tempo de experiência mais pedido.

Cada item diz em quantas vagas aparece e em quantas é exigido (e não só desejável). Um seletor no topo da seção escolhe
as vagas contadas: Em Aplicações (o padrão) ou Todas as vagas analisadas, e Nacionais, Internacionais ou as duas.

As vagas analisadas daqui em diante já trazem os requisitos. Para as já analisadas, a pessoa clica uma vez em **Ler
os requisitos** e a IA lê só os requisitos delas, em lotes, sem mexer na nota.

**Why this priority**: é o pedido central: saber o que o mercado das vagas dela pede, para decidir o que estudar, o que
destacar no currículo e onde se candidatar.

**Independent Test**: com uma IA escolhida, clicar em Ler os requisitos e esperar o fim. As três listas aparecem com as
contagens. Trocar o seletor muda as contagens, e nenhuma nota das vagas muda.

**Acceptance Scenarios**:

1. **Given** vagas já analisadas sem os requisitos lidos, **When** a pessoa abre o painel, **Then** a seção diz quantas
   vagas da seleção ainda não têm os requisitos lidos e oferece o botão Ler os requisitos.
2. **Given** a pessoa clicou em Ler os requisitos, **When** a leitura roda, **Then** o painel mostra o andamento
   ("Lendo 40 de 120 vagas") e um botão Parar. No fim, as listas se atualizam e as notas, os resumos, o Encaixe, as
   Lacunas e a triagem dessas vagas continuam iguais.
3. **Given** uma vaga que pede "5+ anos de experiência em gestão de projetos, Jira e certificação PMP (desejável)",
   **When** os requisitos são lidos, **Then** "Gestão de projetos" e "Jira" entram nas habilidades, "PMP" entra nas
   certificações como desejável, e "5 anos" entra no tempo de experiência. Nenhum item de habilidade fala de anos ou de
   experiência.
4. **Given** a seleção Em Aplicações e Nacionais, **When** 12 de 30 vagas pedem SQL, **Then** a lista mostra "SQL — 12
   de 30 vagas (40%)", com o número das vagas que o exigem.
5. **Given** a pessoa troca para Todas as vagas analisadas, **When** a seleção muda, **Then** as contagens passam a
   valer para todas as vagas analisadas da área escolhida, e a escolha fica guardada para a próxima abertura.
6. **Given** a lista de anos de experiência, **When** as vagas pedem "3 a 5 anos", "5+ anos" e "pelo menos 2 anos",
   **Then** cada vaga entra na faixa do mínimo que pede (3, 5 e 2) e a faixa mais frequente fica em destaque. As vagas
   que não dizem anos entram em "Não diz".

---

### User Story 2 - O quadro com as habilidades da pessoa (Priority: P2)

Ao lado do que as vagas pedem, um quadro **Suas habilidades** mostra as habilidades e ferramentas do perfil dela (com o
nível que ela escreveu) e as certificações dela. Cada uma traz quantas vagas da seleção a pedem. As mais pedidas ficam
no topo, em destaque, porque são as que mais combinam com as vagas. As que nenhuma vaga da seleção pede ficam no fim,
apagadas.

Nas listas do que as vagas pedem, cada item diz se está nas habilidades dela, se só aparece em outro ponto do perfil
(por exemplo, numa experiência) ou se não está no perfil.

**Why this priority**: transforma a lista do mercado num retrato pessoal: o que ela já tem e é pedido (para destacar)
e o que é pedido e ela não mostra (para estudar ou para pôr no perfil, se ela já tem).

**Independent Test**: com o perfil com a seção Habilidades e ferramentas e os requisitos lidos, abrir o painel. O quadro
lista as habilidades do perfil na ordem das mais pedidas, e as marcas nas listas batem com o perfil.

**Acceptance Scenarios**:

1. **Given** o perfil lista "Jira — avançado" e "SQL — consultas básicas", **When** 20 vagas da seleção pedem Jira e 4
   pedem SQL, **Then** o quadro mostra Jira (avançado) em primeiro, com "20 vagas", e SQL depois, com "4 vagas".
2. **Given** uma habilidade do perfil que nenhuma vaga da seleção pede, **When** o quadro aparece, **Then** ela fica no
   fim, apagada, com "nenhuma vaga desta seleção".
3. **Given** que as vagas pedem "Kanban", que não está em Habilidades e ferramentas mas aparece numa experiência do
   perfil, **When** a lista aparece, **Then** Kanban vem marcado "citada no seu perfil, fora das habilidades".
4. **Given** que as vagas pedem "Power BI" e o perfil não cita, **When** a lista aparece, **Then** Power BI vem marcado
   "não está no seu perfil".
5. **Given** um perfil sem a seção de habilidades, **When** o quadro aparece, **Then** ele explica que falta a seção e
   leva para Meu perfil.
6. **Given** o quadro, **When** ele resume, **Then** uma linha diz quantas das habilidades dela aparecem nas vagas da
   seleção ("8 das suas 14 habilidades aparecem nestas vagas").

---

### User Story 3 - Formação, idiomas, senioridade, modelo e contratação (Priority: P2)

Na mesma seção, um bloco de indicadores mostra, para a seleção:

- **Formação**: quantas vagas pedem cada nível (técnico, graduação, pós ou MBA, mestrado, doutorado, não diz) e as
  áreas de curso mais citadas;
- **Idiomas**: cada idioma pedido, com quantas vagas e o nível (básico, intermediário, fluente, nativo);
- **Senioridade** (júnior, pleno, sênior) e **Modelo de trabalho** (remoto, híbrido, presencial);
- **Tipo de contratação**: CLT, PJ, contractor, EOR, relocation e os demais que a análise registra.

**Why this priority**: completa o retrato do que é pedido nas profissões que ela procura. Parte desses dados já existe
nas vagas, então senioridade, modelo, contratação e inglês aparecem mesmo antes de ler os requisitos.

**Independent Test**: abrir o painel com vagas analisadas, sem ler os requisitos. Senioridade, modelo, contratação e
inglês já aparecem. Depois da leitura, formação e os outros idiomas aparecem também.

**Acceptance Scenarios**:

1. **Given** vagas analisadas antes desta spec, **When** o painel abre, **Then** senioridade, modelo, contratação e
   inglês aparecem com os dados que as vagas já têm.
2. **Given** uma vaga que pede "graduação em Administração ou Engenharia" e "espanhol intermediário", **When** os
   requisitos são lidos, **Then** ela conta em Graduação, nas áreas Administração e Engenharia, e em Espanhol
   intermediário.
3. **Given** uma vaga que é CLT ou PJ, **When** a contratação é contada, **Then** ela conta uma vez em CLT e uma vez em
   PJ, e não duas vezes no mesmo tipo.

---

### User Story 4 - Os itens levam às vagas, e o chat e o terminal mostram o mesmo (Priority: P3)

Ao clicar num item (uma habilidade, uma certificação, uma faixa de anos, uma habilidade do quadro dela), a página
mostra as vagas da seleção que o pedem, com cargo e empresa, e abre a vaga escolhida. Pelo terminal, um comando mostra
o mesmo resumo, sem IA. Pelo chat, o assistente responde "o que as vagas pedem?" com esse resumo e, para quem não tem
IA escolhida na página, lê os requisitos das vagas já analisadas e grava sem mexer na nota.

**Why this priority**: dá para conferir de onde vem cada número (as análises citam a fonte, princípio IV) e serve quem
usa a ferramenta pelo chat. O painel já é útil sem isso.

**Independent Test**: clicar em "SQL — 12 vagas" e ver as 12 vagas. Rodar o comando no terminal e ver as mesmas
contagens da página para a mesma seleção.

**Acceptance Scenarios**:

1. **Given** "SQL — 12 de 30 vagas", **When** a pessoa clica no item, **Then** aparecem as 12 vagas, com cargo e
   empresa, e clicar numa delas abre o detalhe da vaga.
2. **Given** a mesma seleção, **When** a pessoa roda o comando do terminal, **Then** ele mostra as mesmas contagens da
   página.
3. **Given** a pessoa sem IA escolhida na página, **When** ela pede no chat para ler os requisitos das vagas, **Then** o
   assistente lê e grava os requisitos, e nenhuma nota muda.

---

### Edge Cases

- **Nenhuma vaga com requisitos lidos na seleção:** a seção diz isso e mostra o botão Ler os requisitos. O quadro dela
  aparece com as habilidades do perfil, sem contagens.
- **Sem IA escolhida na página:** o botão fica desligado com a orientação de escolher uma IA no botão IA ou pedir ao
  assistente no chat. Os indicadores que já existem nas vagas aparecem mesmo assim.
- **A IA falha no meio da leitura** (limite, sem resposta): a leitura para, o que já foi lido fica gravado e o painel
  diz o motivo. Clicar de novo continua das vagas que faltam, e nenhuma é lida duas vezes.
- **A pessoa clica em Parar:** o lote em andamento termina e a leitura para, com o que foi lido gravado.
- **Vaga sem o texto do anúncio** (descrição pendente, JobGether, vaga adicionada sem texto): não entra na leitura. O
  painel conta essas vagas à parte ("5 sem o texto do anúncio").
- **Vaga com texto suspeito de mirar a IA** (spec 034): é lida sozinha, e o texto é dado, nunca instrução.
- **A mesma habilidade escrita de jeitos diferentes** ("Power BI", "PowerBI", "power bi"): conta como uma só.
- **A mesma vaga cita a mesma habilidade duas vezes:** conta uma vez por vaga.
- **Anos sem número** ("experiência sólida", "vivência em"): a vaga entra em "Não diz" no tempo de experiência, e a
  frase não vira habilidade.
- **Anos em faixa** ("3 a 5 anos"): vale o mínimo (3).
- **Vários tempos na mesma vaga** ("5 anos na área, 2 com Python"): vale o tempo pedido na atividade principal do
  cargo.
- **Anúncio em inglês:** a habilidade vem com o nome comum em português quando existe ("Gestão de stakeholders") e com
  o nome próprio quando é ferramenta ou método (Jira, SQL, Scrum), para somar com as vagas em português.
- **Vaga reanalisada** (Forçar verificar ou a descrição que chegou depois): os requisitos são lidos de novo junto com a
  nota.
- **Vaga que sai ou entra em Aplicações:** as contagens de Em Aplicações acompanham na hora.
- **Vaga sem área gravada:** vale a área que a página já deduz para ela.
- **Seleção com poucas vagas** (menos de 5 com requisitos lidos): as listas aparecem com o aviso de que são poucas vagas
  para tirar conclusão.

## Requirements *(mandatory)*

### Functional Requirements

**Leitura dos requisitos**

- **FR-001**: A análise de cada vaga MUST registrar também os requisitos do anúncio:
  - **habilidades**: cada uma com o nome, o tipo (técnica ou ferramenta, ou comportamental) e se é exigida ou desejável;
  - **certificações e cursos**: cada um com o nome, o tipo (certificação ou curso) e se é exigido ou desejável;
  - **tempo de experiência**: o mínimo de anos pedido na atividade principal do cargo, a atividade e a frase do anúncio;
  - **formação**: o nível pedido, as áreas de curso e a frase do anúncio;
  - **idiomas**: cada idioma com o nível pedido e a frase do anúncio.

  Só entra o que o anúncio diz. A IA não deduz requisito que o texto não traz.
- **FR-002**: Experiência não é habilidade. Nenhum item de habilidade ou de certificação MUST falar de tempo ou de
  experiência ("5 anos", "experiência em", "vivência com", "conhecimento em"). O tempo vai para o tempo de experiência,
  e o assunto vira a habilidade pelo nome ("experiência em gestão de projetos" dá a habilidade "Gestão de projetos").
- **FR-003**: Os nomes MUST ser curtos e no mesmo padrão em todas as vagas:
  - o nome comum em português quando existe;
  - ferramentas, linguagens, métodos e certificações pelo nome próprio (Jira, SQL, Scrum, PMP);
  - o nome que o perfil da pessoa usa quando é a mesma habilidade.
- **FR-004**: FR-001 a FR-003 MUST valer nas duas análises: a da IA escolhida na página e a do assistente no chat. A
  reanálise (Forçar verificar, descrição que chegou depois) lê os requisitos de novo.
- **FR-005**: O painel MUST oferecer **Ler os requisitos** para as vagas da seleção (FR-008) que já têm análise e texto
  do anúncio, mas ainda não têm os requisitos lidos ("Ler os requisitos das 30 vagas desta seleção"):
  - a IA escolhida lê só os requisitos, em lotes, com o texto passado pelo filtro de integridade (spec 034); a vaga
    suspeita vai num lote só dela;
  - a leitura MUST NOT mudar a nota, o resumo, o Encaixe, as Lacunas, os alertas, a triagem nem a etapa;
  - o painel mostra o andamento e um botão Parar;
  - se a IA falha, a leitura para, o que foi lido fica gravado e o painel diz o motivo; clicar de novo continua das que
    faltam;
  - cada vaga guarda qual IA leu os requisitos e quando.
- **FR-006**: À IA da leitura vão só o texto de cada anúncio (já sem o conteúdo oculto) e os nomes da lista de
  habilidades e certificações do perfil, para o FR-003. O resto do perfil não vai.
- **FR-007**: Sem IA escolhida na página, o botão MUST aparecer desligado, com a orientação de escolher uma IA no botão
  IA ou de pedir a leitura ao assistente no chat.

**O que as vagas pedem**

- **FR-008**: A seção **O que as vagas pedem** MUST ter um seletor:
  - **Vagas**: Em Aplicações (o padrão) ou Todas as vagas analisadas. Em Aplicações inclui todas as colunas, Encerrada
    também; Todas as vagas analisadas inclui as de Fora dos critérios e as Não seguidas;
  - **Área**: As duas (o padrão), Nacionais ou Internacionais.

  A escolha fica guardada no navegador, e a seção diz quantas vagas está contando: "Contando 30 vagas com requisitos
  lidos, de 35 nesta seleção; 5 sem o texto do anúncio".
- **FR-009**: **Habilidades mais pedidas** MUST mostrar dois grupos, Técnicas e ferramentas e Comportamentais, em ordem
  do número de vagas que pedem cada uma. Cada item mostra:
  - "N de M vagas (x%)" e em quantas é exigida;
  - a marca em relação ao perfil: nas suas habilidades, citada no seu perfil fora das habilidades, ou não está no seu
    perfil.

  Os 15 primeiros de cada grupo aparecem, e "Ver todas" abre o resto.
- **FR-010**: **Certificações e cursos mais pedidos** MUST seguir o FR-009, num grupo só, com a marca de certificação ou
  curso, e a marca em relação ao perfil (nas suas certificações, citada no seu perfil ou não está no seu perfil).
- **FR-011**: **Tempo de experiência** MUST mostrar as faixas até 1 ano, 2 a 3 anos, 4 a 5 anos, 6 a 9 anos, 10 anos ou
  mais e Não diz, com o número de vagas em cada uma e a faixa mais frequente em destaque (sem contar Não diz). Cada
  vaga entra pelo mínimo de anos que pede.
- **FR-012**: **Formação** MUST mostrar quantas vagas pedem cada nível (técnico, graduação, pós ou MBA, mestrado,
  doutorado) e as que não dizem, pelo mínimo que cada vaga pede, e as áreas de curso mais citadas.
- **FR-013**: **Idiomas** MUST mostrar cada idioma pedido, com o número de vagas e quantas pedem cada nível (básico,
  intermediário, fluente, nativo). Para o inglês, a vaga sem os requisitos lidos conta pelo nível de inglês que a
  análise já registrou.
- **FR-014**: **Senioridade**, **Modelo de trabalho** e **Tipo de contratação** MUST contar os campos que as vagas já
  têm (senioridade; modelo de trabalho; tipo de emprego e contratação), cada vaga uma vez por valor, inclusive nas
  vagas sem os requisitos lidos.
- **FR-015**: Na mesma vaga, o mesmo item conta uma vez. Nomes iguais sem diferença de maiúsculas, acentos, espaços e
  pontuação são o mesmo item.

**Suas habilidades**

- **FR-016**: O quadro **Suas habilidades** MUST listar as habilidades e ferramentas do perfil (com o nível que a pessoa
  escreveu) e as certificações do perfil, cada uma com o número de vagas da seleção que a pedem:
  - em ordem das mais pedidas, com as cinco primeiras em destaque;
  - as que nenhuma vaga da seleção pede ficam no fim, apagadas;
  - uma linha de resumo: "8 das suas 14 habilidades aparecem nestas vagas".
- **FR-017**: A habilidade do perfil e a pedida pela vaga MUST ser consideradas a mesma quando:
  - têm o mesmo nome, sem diferença de maiúsculas, acentos, espaços e pontuação;
  - ou o nome de uma está inteiro, em palavras completas, dentro do da outra ("Jira" e "Jira Software").

  Ferramentas parecidas não contam como a mesma (Power BI não é Looker, Jira não é Trello).

  "Citada no seu perfil" vale quando o nome aparece no texto do perfil ou nos relatos da pessoa (spec 035), fora da
  lista de habilidades. A comparação não usa IA e nada é gravado no perfil.
- **FR-018**: Sem a seção de habilidades no perfil, o quadro MUST explicar que ela falta e levar para Meu perfil.

**Rastrear e outros caminhos**

- **FR-019**: Clicar num item (uma habilidade, uma certificação, uma faixa de anos, um nível de formação, um idioma, uma
  habilidade do quadro dela) MUST mostrar as vagas da seleção que o pedem, com cargo e empresa, e abrir o detalhe da
  vaga escolhida.
- **FR-020**: Um comando no terminal MUST mostrar o mesmo resumo da seção (as listas, as faixas, os indicadores e o
  quadro), para a seleção pedida, sem IA.
- **FR-021**: A skill buscar-vagas MUST ensinar o assistente no chat:
  - a registrar os requisitos na análise (FR-001 a FR-003);
  - a ler os requisitos das vagas já analisadas e gravá-los sem mudar a nota, quando a pessoa pedir;
  - a responder "o que as vagas pedem?" com o resumo do FR-020.

**O painel**

- **FR-022**: O quadro **Habilidades Mais Valorizadas nas Vagas** MUST sair, substituído pela seção nova. Os quatro
  números, o funil e a Distribuição por plataforma continuam como estão.
- **FR-023**: A seção MUST funcionar no tema claro e no escuro e a 360 px de largura sem rolagem horizontal.
- **FR-024**: README, README do dashboard, contrato da API, `AGENTS.md` (comandos) e a skill buscar-vagas MUST descrever
  a seção, a leitura dos requisitos e o comando novo.

### Key Entities

- **Requisitos da vaga**: o que o anúncio pede, guardado na vaga: habilidades, certificações e cursos, tempo de
  experiência, formação e idiomas, mais qual IA leu e quando. Ausente = ainda não lido.
- **Habilidade pedida**: nome, tipo (técnica ou comportamental) e se é exigida. Pertence a uma vaga.
- **Certificação ou curso pedido**: nome, tipo (certificação ou curso) e se é exigido. Pertence a uma vaga.
- **Seleção**: vagas (Em Aplicações ou Todas as vagas analisadas) e área (as duas, Nacionais, Internacionais).
  Define quais vagas entram nas contagens.
- **Habilidades da pessoa**: as linhas das seções de habilidades e de certificações do perfil, com o nível que ela
  escreveu. Só leitura.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com os requisitos lidos, a pessoa vê as 10 habilidades mais pedidas da seleção e onde elas estão no perfil
  dela em até 2 cliques depois de abrir Métricas & Funil.
- **SC-002**: Numa amostra de 30 vagas lidas, nenhum item das listas de habilidades e de certificações fala de tempo ou
  de experiência.
- **SC-003**: Em 100% das vagas lidas pelo botão, a nota, o resumo, o Encaixe, as Lacunas, os alertas, a triagem e a
  etapa ficam iguais aos de antes da leitura.
- **SC-004**: Uma leitura parada ou com falha, retomada, termina sem ler nenhuma vaga duas vezes.
- **SC-005**: Para cada item, o número mostrado bate com as vagas que aparecem ao clicar nele, e com o comando do
  terminal na mesma seleção.
- **SC-006**: No quadro Suas habilidades, a pessoa aponta as 5 habilidades dela mais pedidas sem ler a lista inteira.
- **SC-007**: A seção cabe a 360 px de largura sem rolagem horizontal, nos dois temas.

## Assumptions

- Todas as vagas analisadas incluem as de Fora dos critérios: num uso real, a maior parte delas é da mesma profissão e
  ficou de fora pelo local ou pelo modelo de trabalho.
- Em Aplicações inclui as encerradas: são vagas a que a pessoa se candidatou.
- O tempo de experiência conta o mínimo pedido na atividade principal do cargo. O painel não calcula os anos de
  experiência da pessoa: isso seria estimar um número que ela não deu (princípio IV).
- As habilidades comportamentais ficam num grupo à parte, para não esconder as técnicas, que aparecem menos vezes por
  vaga.
- Nas listas de habilidades e de certificações, cada item é só o nome, sem a frase do anúncio. A fonte de cada número é
  a lista de vagas que se abre ao clicar (FR-019). O tempo de experiência, a formação e os idiomas guardam a frase.
- A leitura de algumas centenas de vagas leva alguns minutos e vários pedidos à IA. Com a IA gratuita, o limite pode parar a
  leitura no meio, e por isso ela continua de onde parou.
- A comparação com o perfil é por nome (FR-017). Habilidades equivalentes com nomes diferentes (por exemplo, "Gestão
  ágil" e "Scrum") não se juntam, e ferramentas parecidas também não: dizer que a pessoa tem Power BI porque tem
  Looker seria afirmar o que ela não disse (princípio IV). O FR-003 diminui esse caso, porque a IA usa o nome do perfil quando é a mesma
  habilidade.
- As seções do perfil são reconhecidas pelo título: começa com "Habilidades", "Competências" ou "Skills", e
  "Certificações" ou "Cursos".
- Fica de fora: faixa salarial (spec 028), sugestão de cursos, plano de estudo (já existe em Análises do perfil) e
  qualquer mudança no perfil.
