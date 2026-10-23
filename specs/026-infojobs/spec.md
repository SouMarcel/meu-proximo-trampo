# Feature Specification: InfoJobs na busca de vagas e pausa por portal

**Feature Branch**: `026-infojobs` (worktree `../meu-proximo-trampo-026`, saída da `master`)

**Created**: 2026-10-23

**Status**: Implementada (aguarda o teste da pessoa)

**Input**: User description: "Criar um processo de onboarding de novas plataformas e, com ele, pôr o infojobs.com.br
na busca: leitura própria da busca pública, ligado por padrão, pausa própria configurável no .env como
<PORTAL>_PAUSA para cada portal (com o padrão e o mínimo de 3 s comentados), e espera de horas depois de um
bloqueio, como o LinkedIn."

## Contexto

O InfoJobs é um portal brasileiro generalista: tem vagas de todas as áreas, muitas presenciais e de cidades fora das
capitais. Isso completa o Indeed, a Gupy e a Nerdin (que é só de TI). Ele não tem API oficial para candidatos no
Brasil, nem RSS ou sitemap. A busca e as páginas das vagas são públicas, sem login, e as regras do site para robôs
permitem ler a lista e as vagas (bloqueiam só login, área do candidato, área da empresa e páginas internas). Vale a
regra da constituição (princípio VI) para portais sem API aberta: só a parte pública, pausa entre consultas e parar
no primeiro bloqueio. Serviços pagos de terceiros que leem o InfoJobs (ex.: Apify) foram descartados porque exigiriam
conta e token de cada pessoa e mandariam os cargos e as cidades dela para fora.

Esta é a primeira spec que segue o roteiro `docs/novo-portal.md`. Ela também cria dois mecanismos que os próximos
portais vão reaproveitar:
- **pausa ajustável por portal** no `.env`;
- **espera depois de um bloqueio**, que hoje só o LinkedIn tem.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas do InfoJobs na busca de sempre (Priority: P1)

A pessoa clica em "Buscar vagas" (ou pede no chat, ou roda no terminal). Com os mesmos cargos, local e janela de tempo
que já configurou, a busca traz também as vagas do InfoJobs, com a etiqueta do portal, para o Relatório de Vagas.

**Why this priority**: é o pedido central; o InfoJobs reúne vagas, principalmente presenciais e de outras áreas além de
TI, que nem sempre estão nos outros portais.

**Independent Test**: com respostas do portal simuladas, rodar a busca e ver as vagas do InfoJobs no relatório com
título, empresa, local, data, modelo de trabalho, salário (quando há) e o link para a vaga original.

**Acceptance Scenarios**:

1. **Given** o InfoJobs ligado, **When** a pessoa busca, **Then** as vagas do InfoJobs aparecem no relatório com a
   etiqueta "InfoJobs" e o link da vaga original.
2. **Given** o InfoJobs desligado, **When** a pessoa busca, **Then** nenhuma consulta vai ao InfoJobs e o resultado é
   o mesmo de antes desta funcionalidade.
3. **Given** a mesma vaga no InfoJobs e em outro portal, **When** a busca encontra as duas, **Then** o relatório
   mostra uma vaga só, com os dois portais, como já acontece entre os outros.
4. **Given** uma vaga do InfoJobs que já está no quadro, **When** a busca a encontra de novo, **Then** ela não
   aparece como nova.
5. **Given** a janela de tempo da busca, **When** a busca roda, **Then** só entram vagas publicadas dentro dela, e a
   ferramenta não pede páginas de vagas mais antigas que ela.

---

### User Story 2 - Ligado por padrão, desligável no painel (Priority: P1)

Quem começa a usar a ferramenta já busca no InfoJobs sem configurar nada. No painel "Filtros da busca", a seção
Portais mostra o InfoJobs marcado, com uma linha sobre o que ele é; a pessoa desmarca se não quiser.

**Why this priority**: foi pedido que o portal venha ativo; a pessoa precisa conseguir desligar sem editar arquivo.

**Independent Test**: com uma configuração nova, abrir o painel e ver o InfoJobs marcado; desmarcar, salvar e ver o
contador de consultas cair.

**Acceptance Scenarios**:

1. **Given** uma configuração nova (ou sem a lista de portais), **When** a pessoa busca, **Then** o InfoJobs é
   consultado junto com os outros portais padrão.
2. **Given** uma configuração que já tem a lista de portais escolhida pela pessoa, **When** a ferramenta é
   atualizada, **Then** a lista dela não muda sozinha; o InfoJobs aparece desmarcado no painel para ela ligar.
3. **Given** o painel de filtros, **When** a pessoa desmarca o InfoJobs e salva, **Then** a próxima busca não o
   consulta, e o contador de consultas deixa de somar as dele.

---

### User Story 3 - Respeito ao portal: pausa, bloqueio e espera (Priority: P1)

A busca no InfoJobs usa só a parte pública do site, com pausa entre os pedidos, e lê a página da vaga só quando
precisa. Se o InfoJobs recusar os pedidos, limitar as consultas ou pedir login, a ferramenta para de consultá-lo na
hora, sem nova tentativa, e ele fica em espera por algumas horas. Nas buscas feitas durante a espera, a ferramenta
avisa e pergunta antes de seguir sem ele, como já faz com o LinkedIn.

**Why this priority**: segue a constituição (princípio VI); um portal grande e não oficial precisa parar cedo para não
ser bloqueado de vez.

**Independent Test**: simular o InfoJobs respondendo "muitas consultas" na segunda página; conferir que não há nova
tentativa, que a espera é gravada, que a busca seguinte avisa e pergunta, e que as vagas dos outros portais chegam ao
relatório.

**Acceptance Scenarios**:

1. **Given** uma busca com vários cargos, **When** ela roda, **Then** há pausa entre os pedidos ao InfoJobs e nenhum
   pedido usa login, conta ou cookies da pessoa.
2. **Given** o InfoJobs bloqueando no meio da busca, **When** a ferramenta recebe o bloqueio, **Then** não tenta de
   novo, pula os pedidos restantes ao InfoJobs, mostra o aviso com a hora em que a espera termina e entrega as vagas
   das outras fontes e as do InfoJobs já lidas.
3. **Given** o InfoJobs em espera, **When** a pessoa inicia uma busca (página, terminal ou chat), **Then** a ferramenta
   avisa até quando dura a espera e pergunta antes de seguir sem ele; sem confirmação, a busca não começa.
4. **Given** a espera terminada, **When** a pessoa busca, **Then** o InfoJobs volta a ser consultado sem pergunta.
5. **Given** o InfoJobs em espera, **When** a ferramenta precisaria ler a descrição de uma vaga dele, **Then** não faz
   o pedido e a vaga fica com descrição pendente.

---

### User Story 4 - Pausa ajustável por portal no `.env` (Priority: P2)

A pessoa que está sendo bloqueada num portal aumenta a pausa só dele, com uma linha no `.env` no formato
`<PORTAL>_PAUSA=N` (ex.: `INFOJOBS_PAUSA=10`), sem mexer nos outros. O arquivo de exemplo traz uma linha comentada
para cada portal que consulta páginas, com o valor padrão e o mínimo daquele portal, para ela saber o que pode usar.

**Why this priority**: hoje só o LinkedIn tem pausa ajustável; com mais portais lendo páginas, cada um precisa da sua.

**Independent Test**: sem a variável, conferir que a pausa é a padrão do portal; com `INFOJOBS_PAUSA=10`, que a pausa
do InfoJobs muda e a dos outros portais não; com valor abaixo do mínimo, que vale o mínimo, com aviso.

**Acceptance Scenarios**:

1. **Given** nenhuma variável de pausa no `.env`, **When** a busca roda, **Then** cada portal usa a pausa padrão dele
   e o comportamento é o mesmo de antes desta funcionalidade.
2. **Given** `INFOJOBS_PAUSA=10`, **When** a busca roda, **Then** a pausa entre os pedidos ao InfoJobs é de pelo menos
   10 segundos, e o começo da busca mostra a pausa em uso e uma estimativa do tempo de pausa no InfoJobs.
3. **Given** um valor abaixo do mínimo do portal (ex.: `INFOJOBS_PAUSA=1`), **When** a busca roda, **Then** vale o
   mínimo, e o aviso do começo da busca diz que o valor foi trocado.
4. **Given** um valor que não é número, **When** a busca roda, **Then** ele é ignorado, vale o padrão do portal e o
   aviso diz isso.
5. **Given** `LINKEDIN_PAUSA` já configurada por quem usa a ferramenta, **When** a ferramenta é atualizada, **Then** a
   pausa do LinkedIn continua exatamente como antes.
6. **Given** o arquivo de exemplo do `.env`, **When** a pessoa o abre, **Then** vê uma linha comentada para cada portal
   com pausa ajustável, com o padrão e o mínimo daquele portal.

---

### User Story 5 - Descrição completa para a nota de aderência (Priority: P2)

A lista do InfoJobs traz só um trecho do texto. Para as vagas que vão para o relatório, a ferramenta lê a página da
vaga e guarda a descrição completa, que a análise com IA usa para dar a nota.

**Why this priority**: sem a descrição a nota fica pobre; mas a vaga já é útil só com o que a lista mostra.

**Independent Test**: com uma página de vaga simulada, conferir que a vaga do relatório recebe a descrição completa e
que vagas fora dos critérios ou já no quadro não geram leitura da página.

**Acceptance Scenarios**:

1. **Given** uma vaga do InfoJobs que vai para o relatório, **When** a busca termina, **Then** ela tem a descrição
   completa da página da vaga.
2. **Given** uma vaga fora dos critérios pelo título ou já no quadro, **When** a busca termina, **Then** a página dela
   não foi lida.
3. **Given** a leitura da página falhar ou o limite de leituras da busca acabar, **When** a busca termina, **Then** a
   vaga entra com o que veio da lista e fica marcada com descrição pendente, como nas outras fontes.

---

### User Story 6 - Adicionar uma vaga do InfoJobs pelo link (Priority: P3)

A pessoa cola o link de uma vaga do InfoJobs no Adicionar Vaga do dashboard. A ferramenta reconhece o portal, preenche
título, empresa, local, modelo e descrição, e a vaga não se repete quando a busca a encontra depois.

**Why this priority**: completa a integração; hoje esse link cairia como portal "Outra".

**Independent Test**: colar um link `infojobs.com.br/vaga-de-…` e ver a vaga com a etiqueta "InfoJobs" e os dados
preenchidos; rodar uma busca que a encontra e ver que ela não volta como nova.

**Acceptance Scenarios**:

1. **Given** um link de vaga do InfoJobs, **When** a pessoa adiciona, **Then** a vaga entra com a etiqueta "InfoJobs" e
   os dados da página.
2. **Given** a vaga adicionada pelo link, **When** a busca a encontra, **Then** ela é reconhecida como a mesma vaga.
3. **Given** o InfoJobs em espera, **When** a pessoa cola o link, **Then** a ferramenta não faz o pedido e avisa até
   quando dura a espera.

---

### Edge Cases

- **Busca sem nenhuma vaga** (cargo raro): segue normalmente, sem erro.
- **Empresa confidencial**: o InfoJobs esconde o nome de algumas empresas; a vaga entra com a empresa como o portal
  mostra ("Confidencial"), e o filtro de empresas excluídas não se aplica a ela.
- **Data sem ano** (o card mostra "20 out"): a ferramenta deduz o ano; uma vaga de dezembro vista em janeiro é do ano
  anterior. "Hoje" e "Ontem" também são reconhecidos.
- **Salário "a combinar"** ou ausente: a vaga entra sem salário (nada é estimado).
- **Vaga sem modelo de trabalho informado**: entra sem modelo; a análise com IA pode corrigir depois.
- **Busca na cidade**: ficam as vagas da cidade e do estado da pessoa; as outras cidades ficam de fora. As remotas
  ("Home office") chegam pela consulta remota, se ela aceita remoto.
- **Busca ampla do site**: o InfoJobs pode trazer vagas que só citam o cargo no texto; ficam só as vagas cujo título
  bate com o cargo, como na Nerdin.
- **Página do InfoJobs mudou e nada é reconhecido**: a busca avisa "não consegui ler as vagas do InfoJobs" e segue com
  as outras fontes, sem quebrar e sem entrar em espera.
- **País da busca nacional diferente do Brasil**: o InfoJobs não é consultado.
- **Busca internacional**: o InfoJobs não entra nas consultas de fora do país.
- **Mesma vaga em duas páginas da lista** (a lista mudou entre os pedidos): aparece uma vez.
- **Todos os portais escolhidos em espera**: a busca avisa que não há portal disponível até a hora indicada, como hoje
  com o LinkedIn.
- **Relógio do computador mudou** e a hora da espera gravada ficou no futuro: a espera dura no máximo o período normal
  a partir de agora, como hoje no LinkedIn.
- **Arquivo da espera ilegível ou apagado**: a ferramenta segue como se não houvesse espera.
- **Busca pelo terminal com `--fontes infojobs`**: funciona sem passar pelo painel.
- **Variável de pausa com espaço, aspas ou vírgula decimal** (ex.: `INFOJOBS_PAUSA="4,5"`): é lida como 4,5 segundos.

## Requirements *(mandatory)*

### Functional Requirements

**Portal InfoJobs**

- **FR-001**: O InfoJobs MUST ser um portal da busca nacional, ligado ou desligado pela pessoa, e MUST vir ligado em
  configuração nova ou sem a lista de portais, junto com os outros portais padrão.
- **FR-002**: Uma configuração que já tem a lista de portais escolhida MUST continuar com essa lista; o InfoJobs só
  entra nela quando a pessoa marca.
- **FR-003**: Com o InfoJobs ligado, cada cargo da busca nacional MUST gerar consultas à busca pública do InfoJobs, só
  quando o país da busca é o Brasil, e a lista de cada cargo MUST ser lida uma vez por busca e servir às consultas do
  mesmo cargo (remoto, país e cidade).
- **FR-004**: A ferramenta MUST pedir ao InfoJobs só as vagas da janela de tempo da busca, usando o filtro de data do
  próprio site quando ele existir, e MUST parar de pedir páginas ao chegar ao número de vagas por cargo, a uma vaga
  mais antiga que a janela ou a um teto de páginas por cargo.
- **FR-005**: Cada vaga do InfoJobs MUST trazer:
  - título, empresa, local (quando houver) e data de publicação;
  - modelo de trabalho (remoto, híbrido ou presencial, quando informado);
  - tipo de contratação (quando informado);
  - salário só quando houver valor;
  - o link da vaga original.

  O identificador MUST vir do número da vaga no InfoJobs e ser o mesmo da vaga adicionada pelo link.
- **FR-006**: A consulta remota MUST ficar só com as vagas remotas; a consulta da cidade MUST ficar só com as vagas da
  cidade ou do estado da pessoa, nos modelos que ela marcou; a consulta do país inteiro fica com todas, nos modelos
  marcados.
- **FR-007**: A vaga do InfoJobs MUST passar pelos mesmos passos das outras:
  - critérios de título, senioridade, tipo de emprego e empresas excluídas;
  - Fora dos critérios, com o motivo;
  - junção com o mesmo anúncio em outro portal;
  - análise com IA.
- **FR-008**: A descrição MUST ser lida da página da vaga só para as vagas que vão para o relatório, com um limite de
  leituras por busca; as que ficarem sem texto saem com descrição pendente e são completadas depois pelo botão de
  completar descrições, como nas outras fontes.

**Respeito ao portal**

- **FR-009**: Os pedidos ao InfoJobs MUST usar só a parte pública do site, sem login nem conta, senhas ou cookies da
  pessoa, MUST respeitar as regras do site para robôs e MUST ter pausa entre um pedido e outro.
- **FR-010**: Ao receber um sinal de bloqueio (recusa, limite de consultas ou pedido de login), a ferramenta MUST:
  - parar de consultar o InfoJobs na hora, sem nova tentativa;
  - pôr o InfoJobs em espera por 24 horas;
  - mostrar o aviso com a hora em que a espera termina no resumo da busca (página, terminal e chat);
  - continuar com as outras fontes.
- **FR-011**: Durante a espera, a ferramenta MUST:
  - não fazer nenhum pedido ao InfoJobs (busca, descrição, Adicionar Vaga);
  - avisar até quando dura a espera;
  - perguntar antes de começar uma busca sem ele, pelo mesmo caminho que já existe para o LinkedIn (pergunta na
    página e no terminal; sem terminal interativo, a busca sai sem buscar até receber a confirmação).

**Pausa por portal**

- **FR-012**: Cada portal que consulta páginas públicas MUST ter uma pausa padrão e um mínimo próprios, e a pessoa
  MUST poder ajustar a pausa de cada um pela variável `<PORTAL>_PAUSA` no `.env` ou no ambiente. A variável vale para
  os portais sem API que leem páginas (hoje LinkedIn, Nerdin e InfoJobs) e para os próximos desse tipo; os portais
  com API (Gupy, startup.jobs, os do exterior) e o Indeed seguem com a pausa fixa de hoje. Nerdin: padrão e mínimo
  de 3 segundos, sem sorteio, como hoje.
- **FR-013**: O mínimo de qualquer portal sem API MUST ser de pelo menos 3 segundos, e o máximo de 60.
  - Valor abaixo do mínimo vira o mínimo; acima do máximo vira o máximo.
  - Valor que não é número é ignorado e vale o padrão.
  - Nos três casos, o aviso do começo da busca diz o que aconteceu.
- **FR-014**: A pausa do InfoJobs MUST ser sorteada a cada pedido, como a do LinkedIn: de 3 a 7 segundos por padrão
  e, com `INFOJOBS_PAUSA=N`, de N a N+4 segundos, com mínimo de 3.
- **FR-015**: Com a variável de um portal definida, o começo da busca MUST mostrar a pausa em uso e a estimativa do
  tempo de pausa daquele portal, na página e no terminal, como já acontece com o LinkedIn.
- **FR-016**: `LINKEDIN_PAUSA` MUST continuar valendo como hoje: mesmo padrão, mesmo mínimo e máximo, mesmo sorteio
  entre N e N+4 segundos e mesmo aviso. A pausa padrão de cada portal que já existe MUST continuar a mesma.
- **FR-017**: O repositório MUST ter um arquivo de exemplo do `.env`, sem nenhuma chave preenchida, com uma linha
  comentada para cada portal com pausa ajustável, no formato
  `# INFOJOBS_PAUSA=3   # padrão 3 a 7 s (sorteado); mínimo 3 s para este portal`.

**Superfície**

- **FR-018**: O painel "Filtros da busca" MUST mostrar o InfoJobs na seção Portais, com uma linha sobre o que ele é
  (portal generalista, busca pública, consulta não oficial, pausa e espera), e o contador de consultas MUST somar as
  dele.
- **FR-019**: O Adicionar Vaga MUST reconhecer links de vaga do InfoJobs, com a etiqueta "InfoJobs" e os dados da
  página.
- **FR-020**: O dashboard MUST mostrar a etiqueta "InfoJobs" com cor própria e aceitar "InfoJobs" no filtro e no
  formulário de portal.
- **FR-021**: A busca pelo terminal e pela skill MUST aceitar o InfoJobs como as outras fontes.
- **FR-022**: AGENTS.md, o README (portais, termos, pausa por portal, espera e avisos), o README do dashboard, o
  contrato da API e a skill buscar-vagas MUST citar o novo portal e a pausa por portal; o roteiro
  `docs/novo-portal.md` MUST descrever a pausa e a espera como ficaram.

### Key Entities

- **Portal InfoJobs**: fonte nacional e generalista de vagas, ligada por padrão, com a linha de aviso do painel, pausa
  sorteada de 3 a 7 segundos e espera de 24 horas depois de um bloqueio.
- **Consulta ao InfoJobs**: um cargo, a janela de tempo e, na busca na cidade, a cidade e o estado da pessoa.
- **Vaga do InfoJobs**: uma vaga como as outras, identificada pelo número da vaga no portal.
- **Pausa do portal**: padrão, mínimo, máximo e o valor que a pessoa definiu no `.env` (se houver).
- **Espera do portal**: desde quando e por quê o portal está de fora, e até quando; guardada no computador da pessoa,
  fora do Git.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa configuração nova, a primeira busca já traz vagas do InfoJobs, sem a pessoa mexer em nada.
- **SC-002**: 100% das vagas do InfoJobs no relatório têm título, data e link que abrem a vaga certa no portal
  (conferido em amostra de 10 vagas).
- **SC-003**: Nenhuma vaga do InfoJobs aparece duas vezes no relatório, nem quando já está no quadro.
- **SC-004**: Com o InfoJobs desligado e sem nenhuma variável de pausa nova, a saída e o tempo de pausa da busca são
  os mesmos de antes desta funcionalidade.
- **SC-005**: Num bloqueio simulado, há zero novas tentativas ao InfoJobs depois do primeiro sinal e zero pedidos ao
  InfoJobs durante a espera; o aviso aparece e 100% das vagas das outras fontes chegam ao relatório.
- **SC-006**: Uma busca com 5 cargos faz ao InfoJobs no máximo 5 × o teto de páginas pedidos de lista, mais o limite de
  leituras de vaga.
- **SC-007**: A pessoa desliga o InfoJobs pelo painel em menos de 1 minuto, sem editar arquivos.
- **SC-008**: A pessoa ajusta a pausa de um portal com uma única linha no `.env`, copiando do arquivo de exemplo, e a
  próxima busca mostra a pausa nova.

## Assumptions

- **Formato do site** (visto em 23/10/2026):
  - lista pública renderizada no site, 20 vagas por página, com filtros de data na própria URL (hoje, 3 dias,
    semana, 15 dias, mês);
  - a página seguinte não tem endereço próprio, então a ferramenta lê só a primeira página de cada cargo (e a da
    cidade, na consulta da cidade);
  - páginas de vaga com os dados estruturados da vaga.
  Quando isso mudar, a ferramenta avisa e segue com as outras fontes.
- **Termos de uso**: os termos do InfoJobs proíbem "mecanismos, software ou scripts" e cópias por "Robot/Crawler"
  sem autorização expressa (research R1). Em 23/10/2026 a pessoa decidiu seguir mesmo assim, como no LinkedIn, ciente
  disso. Por isso a linha do painel e o README dizem que é uma consulta não oficial, e valem a pausa sorteada, a
  leitura mínima e a espera de 24 horas. As alternativas oferecidas e recusadas foram: só o link no Adicionar Vaga,
  pedir autorização ao InfoJobs e desistir do portal.
- **Janela de tempo**: segue a do painel (até 30 dias), convertida no menor filtro de data do site que a cobre.
- **Teto de leitura**: uma página de lista por cargo (mais uma da cidade) e até 30 leituras de vaga por busca.
- **Portais que não mudam**:
  - a Nerdin continua saindo só do resto da busca no bloqueio, sem espera; ganhar espera seria outra decisão;
  - o LinkedIn mantém a espera de 6 horas, o registro de pedidos e os avisos de hoje.
- **Ligado por padrão**: vale para configuração nova ou sem a lista de portais (mesma regra da Nerdin).
- **Fora do escopo**: o InfoJobs como conta conectada (leitura das candidaturas na área logada); seria outra spec,
  com análise de risco (constituição VI).
- **Constituição**: não há emenda; o InfoJobs segue a regra que já existe para portais sem API aberta.
- **Verificação**: só no Windows, como nas specs anteriores.
