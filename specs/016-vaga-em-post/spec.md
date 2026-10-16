# Feature Specification: Vaga publicada em post

**Feature Branch**: `016-vaga-em-post` (o trabalho acontece numa worktree saída da `master`, conforme a constituição)

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "Vagas publicadas como post no LinkedIn (e texto colado de outros lugares) no botão Adicionar
Vaga do dashboard. Hoje um link de post falha porque o leitor procura o número da vaga e abre o formulário vazio.
Queremos: (1) reconhecer link de post do LinkedIn e ler a versão pública de incorporação, sem login, uma consulta por
link, parando no primeiro bloqueio e sem tentar se o LinkedIn estiver nas 6 horas de espera; (2) extrair cargo,
empresa, local e o contato de candidatura do texto do post com a IA configurada pela pessoa, com o formulário como
fallback; o formulário sempre abre preenchido para a pessoa conferir antes de salvar; (3) novo campo de e-mail de
candidatura, editável no card expandido do dashboard, com link mailto, sem nunca enviar nada pela pessoa; (4) opção
'Colar texto de post ou mensagem' ao lado de 'Preencher à mão'. Fora do escopo: buscar posts automaticamente."

## Clarifications

### Session 2026-10-16

- Q: Um bloqueio ao ler um post deve gravar a espera de 6 horas do LinkedIn, e a leitura de post deve respeitar essa
  espera? → A: Não. A leitura de post é um pedido pontual feito pela pessoa, como o link de vaga do LinkedIn na spec
  015: não grava espera e não é barrada por ela. Continua parando no primeiro bloqueio, sem nova tentativa.
- Q: Com IA, o formulário abre na hora e a IA preenche depois, ou a tela espera a IA? → A: Com IA, a tela mostra "Em
  análise pela IA, aguarde…" e só abre o formulário já preenchido. Sem IA, segue direto para o formulário (fallback).

## Contexto

Muitas vagas não são publicadas na área de vagas do LinkedIn, mas como um post comum, no feed. Quem publica é a
página da empresa ou uma pessoa (recrutador, gestor). O post é texto livre: o cargo aparece no meio da frase, a
candidatura costuma ser por e-mail ("envie seu currículo para … com o assunto …") e quase nunca há local, salário ou
data. Hoje, ao colar o link de um post no Adicionar Vaga, a ferramenta procura o número da vaga, não acha, e abre o
formulário vazio. A pessoa precisa copiar o texto e digitar tudo à mão.

Exemplo real analisado (2026-10-16): post de uma página de empresa, "Oportunidade na [empresa] | Coordenador(a) de
Projetos", com os requisitos em lista, candidatura por e-mail com assunto definido, sem local e com a data só como
"1 d". A versão pública de incorporação do post abriu sem login e trouxe o texto inteiro, o autor (página de empresa)
e o e-mail. Não trouxe os dados estruturados de vaga que o leitor de hoje usa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adicionar uma vaga pelo link de um post (Priority: P1)

A pessoa vê uma vaga num post do LinkedIn, copia o link do post e cola no Adicionar Vaga. A ferramenta lê o post
público, sem login, e a IA configurada pela pessoa tira do texto o cargo, a empresa, o local e o contato de
candidatura. O formulário abre preenchido, com o texto inteiro do post na descrição. A pessoa confere, corrige o que
precisar e clica em Adicionar. A vaga vai para o Relatório de Vagas com a etiqueta Post e recebe a nota de aderência
como as outras.

**Why this priority**: é o pedido central; sem isso a pessoa digita tudo à mão.

**Independent Test**: com a IA ligada e a página pública do post simulada (um post fictício com a mesma estrutura do
exemplo real: empresa, nomes e e-mail inventados), colar o link e conferir o formulário: o cargo do post, a empresa do
autor, local vazio, o e-mail e o assunto pedidos no post e a descrição com o texto inteiro. Salvar e conferir a vaga no relatório, com a etiqueta
Post e a análise de aderência pedida.

**Acceptance Scenarios**:

1. **Given** um link de post público do LinkedIn em qualquer dos formatos aceitos, **When** a pessoa clica em Buscar
   dados, **Then** a ferramenta faz uma única consulta à versão pública do post, sem login, e abre o formulário
   preenchido para conferir, sem gravar a vaga.
2. **Given** o post lido e a IA configurada, **When** o formulário abre, **Then** cargo, empresa, local e o contato de
   candidatura vêm do texto do post, e o que o post não diz fica em branco.
3. **Given** um post publicado por uma página de empresa, **When** o formulário abre, **Then** a empresa é o nome da
   página, se a IA não achar outra empresa no texto.
4. **Given** um post publicado por uma pessoa (ex.: recrutador), **When** o formulário abre, **Then** a empresa vem do
   texto (ou fica em branco para a pessoa digitar), e o nome de quem publicou entra nas anotações da vaga como
   "Publicado por".
5. **Given** o formulário conferido, **When** a pessoa clica em Adicionar, **Then** a vaga vai para o Relatório de
   Vagas com plataforma LinkedIn e a etiqueta Post, o link do post como link da vaga, e a análise de aderência segue
   como nas vagas adicionadas pelo link.
6. **Given** o mesmo post adicionado de novo, **When** a pessoa busca os dados, **Then** a ferramenta avisa que a vaga
   já está no dashboard e onde, como faz hoje com links repetidos.

---

### User Story 2 - E-mail de candidatura na vaga (Priority: P1)

A vaga pede o currículo por e-mail. O cartão expandido da vaga, no dashboard, tem o campo "E-mail de candidatura" e o
campo "Assunto". Os dois chegam preenchidos quando a vaga veio de um post que pedia isso, e a pessoa pode preencher
ou corrigir em qualquer vaga. Com o e-mail preenchido, o cartão mostra um link que abre o programa de e-mail da pessoa
com o destinatário e o assunto já postos. A ferramenta nunca envia nada.

**Why this priority**: em post, o e-mail costuma ser o único jeito de se candidatar; sem ele à vista, a pessoa perde
o caminho da candidatura.

**Independent Test**: abrir o cartão de uma vaga qualquer, preencher e-mail e assunto, salvar, recarregar a página e
conferir os dois salvos e o link de e-mail com o assunto. Colocar um e-mail inválido e conferir o aviso sem salvar.

**Acceptance Scenarios**:

1. **Given** uma vaga no dashboard, **When** a pessoa abre o cartão, **Then** ela vê os campos "E-mail de candidatura"
   e "Assunto", vazios ou preenchidos.
2. **Given** um e-mail válido salvo, **When** o cartão é exibido, **Then** aparece um link de e-mail com o destinatário
   e o assunto, que só abre o programa de e-mail da pessoa, sem enviar nada.
3. **Given** um texto que não é e-mail, **When** a pessoa salva, **Then** o cartão avisa que o e-mail é inválido e não
   grava o campo.
4. **Given** uma vaga com e-mail de candidatura, **When** a pessoa abre o kit da candidatura, **Then** o kit mostra o
   e-mail e o assunto como o lugar onde se candidatar.
5. **Given** uma vaga que veio de um post com e-mail, **When** ela é salva, **Then** o e-mail e o assunto do formulário
   ficam gravados na vaga.

---

### User Story 3 - Colar o texto de um post ou mensagem (Priority: P2)

O post é privado (só para conexões), o LinkedIn bloqueou, ou a vaga veio de um grupo de WhatsApp, do Instagram ou de
um e-mail. Ao lado de "Preencher à mão" há a opção "Colar texto de post ou mensagem". A pessoa cola o texto, e a
ferramenta usa a mesma extração da US1 para abrir o formulário preenchido.

**Why this priority**: cobre o que a leitura do link não alcança e vale para qualquer origem; depende da extração da
US1.

**Independent Test**: com a IA ligada, colar o texto do post fictício de teste e conferir o mesmo formulário da US1 (menos o
autor, que o texto colado não tem). Colar um texto com link de candidatura e conferir que o link vai para o formulário.

**Acceptance Scenarios**:

1. **Given** o Adicionar Vaga aberto, **When** a pessoa escolhe "Colar texto de post ou mensagem" e cola o texto,
   **Then** o formulário abre preenchido com o que a IA tirou do texto e com o texto inteiro na descrição.
2. **Given** um texto colado com um link (ex.: página de candidatura), **When** o formulário abre, **Then** o link vai
   para o campo de link da vaga.
3. **Given** um texto colado, **When** a pessoa salva, **Then** a plataforma é a que ela escolher no formulário
   (LinkedIn, Outra…), com a etiqueta Post.

---

### User Story 4 - Sem IA, com falha ou com bloqueio: o formulário resolve (Priority: P2)

A pessoa não configurou IA, a IA falhou, o post não abre ou o LinkedIn recusou o pedido. A ferramenta não trava: abre o formulário com o que tiver (o texto do post na descrição, o autor e o link) e diz o que aconteceu, para
a pessoa completar à mão.

**Why this priority**: a constituição exige que o Adicionar Vaga funcione sem IA; é o caminho de reserva das US1 e
US3.

**Independent Test**: com a IA desligada, colar o link do post simulado e conferir o formulário com a descrição, o
link e a empresa do autor, e cargo em branco. Simular uma recusa do LinkedIn e conferir um único pedido, o motivo, a
sugestão de colar o texto e que a espera de 6 horas da busca não foi gravada.

**Acceptance Scenarios**:

1. **Given** nenhuma IA configurada, **When** o post é lido, **Then** o formulário abre com a descrição (texto inteiro),
   o link do post e a empresa do autor quando for página de empresa, e um aviso de que cargo e local ficam para a
   pessoa preencher.
2. **Given** a IA configurada mas com erro ou resposta que não dá para usar, **When** o post é lido, **Then** o
   formulário abre como no cenário 1, com o motivo do erro da IA.
3. **Given** o LinkedIn bloqueando a leitura do post (limite de pedidos, recusa ou pedido de login), **When** isso
   acontece, **Then** a ferramenta não tenta de novo, avisa o motivo e sugere "Colar texto de post ou mensagem", sem
   gravar a espera de 6 horas da busca.
4. **Given** o LinkedIn na espera de 6 horas da busca, **When** a pessoa cola um link de post, **Then** a leitura
   acontece normalmente, como no link de vaga do LinkedIn.
5. **Given** um post privado, apagado ou que não abre, **When** a pessoa busca os dados, **Then** a ferramenta diz que
   não conseguiu ler o post e sugere colar o texto.

---

### Edge Cases

- **Post sem vaga** (opinião, notícia): a IA indica que não parece vaga; o formulário abre mesmo assim, com o texto na
  descrição e o aviso, e a pessoa decide.
- **Post com várias vagas**: o formulário vem com a primeira, a descrição com o texto inteiro e um aviso de que o post
  traz mais de uma vaga; para as outras, a pessoa repete com "Colar texto de post ou mensagem".
- **Vaga só na imagem do post** (texto curto, "vaga na imagem"): o formulário abre com o pouco que houver e sugere
  colar o texto da imagem. A ferramenta não lê imagens.
- **Texto do post com instruções** ("ignore as instruções anteriores…"): é dado, nunca instrução. A IA só extrai
  campos, e o resultado passa pelo formulário que a pessoa confere.
- **Mais de um e-mail no texto**: vai o que o post pede para a candidatura; se não der para saber, o primeiro, e a
  pessoa confere.
- **Link de candidatura e e-mail no mesmo post**: os dois entram (link da vaga e e-mail de candidatura).
- **Post repetido com outro formato de link** (feed, posts, share): é reconhecido como o mesmo post e não duplica.
- **Vaga do post igual a uma vaga já trazida pela busca** (mesmo cargo e empresa): vale a regra de repetidas de hoje.
- **LinkedIn na espera da busca**: a leitura de post não é afetada, como o link de vaga na spec 015. A espera vale só
  para a busca, que faz muitos pedidos seguidos.
- **Texto colado muito longo**: limitado ao mesmo tamanho máximo da descrição de hoje, com aviso se for cortado.
- **IA lenta** (ex.: Claude Code): a tela mostra "Em análise pela IA, aguarde…" até a resposta. Passado o tempo
  limite, o formulário abre como sem IA, com o aviso. Cancelar fecha o Adicionar Vaga, como hoje.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O Adicionar Vaga MUST reconhecer como link de post do LinkedIn os formatos de atividade no feed, de post
  compartilhado e de publicação (`feed/update/urn:li:activity:…`, `/posts/…-activity-…`, `urn:li:share:…`,
  `urn:li:ugcPost:…`), e tratar formatos diferentes do mesmo post como o mesmo post.
- **FR-002**: Para um link de post, a ferramenta MUST fazer uma única consulta à versão pública do post, sem login e
  sem conta, cookies ou senha da pessoa, e MUST tirar dela o texto inteiro do post, o nome de quem publicou e se é uma
  página de empresa ou uma pessoa.
- **FR-003**: A leitura de post MUST seguir a regra do link de vaga do LinkedIn (spec 015): é um pedido pontual da
  pessoa, não é barrada pela espera de 6 horas da busca e não grava essa espera.
- **FR-004**: Num bloqueio ao ler o post, a ferramenta MUST parar sem nova tentativa, avisar o motivo e sugerir colar
  o texto.
- **FR-005**: Com a IA configurada, a ferramenta MUST pedir a ela só a extração de campos do texto: cargo, empresa,
  local ou modelo de trabalho, link de candidatura, e-mail de candidatura, assunto pedido e se o texto parece uma vaga
  (e quantas). O texto vai como dado, com a instrução de não seguir ordens contidas nele e de deixar em branco o que o
  texto não diz.
- **FR-006**: A tela MUST dizer qual provedor de IA lê o texto antes ou durante a leitura.
- **FR-007**: O resultado da extração MUST abrir o formulário do Adicionar Vaga preenchido para a pessoa conferir. A
  vaga MUST NOT ser gravada sem o clique da pessoa em Adicionar.
- **FR-008**: A descrição do formulário MUST receber o texto inteiro do post ou do texto colado, sem resumo.
- **FR-009**: Quando quem publicou é uma página de empresa, a empresa MUST ser o nome da página se a extração não
  trouxer outra. Quando é uma pessoa, o nome dela MUST ir para as anotações da vaga como "Publicado por: [nome]".
- **FR-010**: Sem IA, com erro da IA ou com resposta que não dá para usar, o formulário MUST abrir com a descrição, o
  link e o autor (quando for página de empresa), e com um aviso do motivo. O Adicionar Vaga MUST funcionar sem IA.
- **FR-011**: O Adicionar Vaga MUST ter a opção "Colar texto de post ou mensagem" ao lado de "Preencher à mão", com a
  mesma extração e o mesmo formulário da leitura pelo link.
- **FR-012**: Vagas vindas de post ou de texto colado MUST ser marcadas como Post e mostrar essa etiqueta no relatório
  e no quadro. A plataforma é LinkedIn para link de post e a escolhida no formulário para texto colado.
- **FR-013**: Uma vaga vinda de link de post MUST ter identificação estável a partir do post, para que o mesmo post
  adicionado de novo seja reconhecido como repetido; as regras de vaga repetida de hoje continuam valendo.
- **FR-014**: Toda vaga MUST aceitar "E-mail de candidatura" e "Assunto". O e-mail MUST ser validado antes de gravar.
  Os dois MUST ser editáveis no cartão expandido da vaga.
- **FR-015**: Com o e-mail preenchido, o cartão expandido e o kit da candidatura MUST mostrar um link de e-mail com o
  destinatário e o assunto. A ferramenta MUST NOT enviar e-mail nem abrir o envio sem o clique da pessoa.
- **FR-016**: Vagas de post ou texto colado salvas com descrição MUST seguir para a análise de aderência como as vagas
  adicionadas pelo link hoje.
- **FR-017**: README, AGENTS.md e a skill buscar-vagas MUST explicar como adicionar vaga de post (link ou texto colado),
  que a leitura é uma consulta pública sem login, e o e-mail de candidatura.
- **FR-018**: Links de vaga do LinkedIn (área de vagas) e de outros portais MUST continuar como hoje.

### Key Entities

- **Post de vaga**: texto inteiro, quem publicou (nome e se é página de empresa ou pessoa), link do post e a
  identificação do post.
- **Extração do texto**: cargo, empresa, local ou modelo, link de candidatura, e-mail de candidatura, assunto, se
  parece vaga e quantas vagas o texto traz. Serve só para preencher o formulário; não é gravada sozinha.
- **Contato de candidatura por e-mail**: e-mail e assunto, gravados na vaga, editáveis no cartão.
- **Etiqueta Post**: marca na vaga de que ela veio de um post ou de texto colado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o post fictício de teste (mesma estrutura do exemplo real) e a IA ligada, o formulário abre com
  cargo, empresa, e-mail e assunto certos, e local em branco, sem a pessoa digitar nada.
- **SC-002**: Ler um link de post faz no máximo 1 pedido ao LinkedIn, e um bloqueio nessa leitura não muda a espera da
  busca.
- **SC-003**: Em 100% dos caminhos (com IA, sem IA, erro da IA, bloqueio, post privado), a pessoa termina com o
  formulário aberto ou com uma mensagem que diz o que fazer, e nenhuma vaga é gravada sem o clique dela.
- **SC-004**: Sem IA, o formulário abre preenchido com o texto do post em até 5 segundos depois da leitura.
- **SC-005**: Com a IA, a pessoa vê "Em análise pela IA, aguarde…" e depois o formulário já preenchido, em até 1
  minuto. Se a IA falhar ou passar do tempo, o formulário abre como sem IA.
- **SC-006**: O e-mail e o assunto salvos no cartão continuam lá depois de recarregar a página, e o link de e-mail abre
  com os dois.
- **SC-007**: Links de vaga do LinkedIn, Indeed, Gupy e dos outros portais dão o mesmo resultado de antes.

## Assumptions

- A versão pública de incorporação dos posts do LinkedIn abre sem login para posts públicos, como no exemplo real de
  2026-10-16. Posts só para conexões não abrem e caem na US3.
- Essa consulta segue o princípio VI: é uma página pública, uma consulta por pedido da pessoa, com parada no primeiro
  bloqueio, sem nova tentativa. Ela não amplia a busca automática.
- A extração usa a IA que a pessoa configurou no painel IA, qualquer provedor. Com modelo gratuito, o limite de uso do
  provedor pode fazer a extração falhar; nesse caso vale a US4.
- O texto do post é sobre a vaga, não sobre a pessoa; mandar esse texto ao provedor de IA não expõe dados pessoais
  dela. O perfil não vai junto na extração.
- A data do post vem só como tempo relativo ("1 d") e não é usada; a vaga fica com a data em que foi adicionada.
- Comentários do post não são lidos.
- O tamanho máximo da descrição é o de hoje no Adicionar Vaga.
- Buscar posts automaticamente fica fora do escopo: a pesquisa de posts do LinkedIn exige login.
- Verificação só no Windows, como nas specs anteriores.
