# Feature Specification: Contas conectadas (candidaturas nos portais)

**Feature Branch**: `018-contas-conectadas` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Na área logada dos portais (Gupy: portal.gupy.io/my/applications; Indeed:
myjobs.indeed.com/applied; LinkedIn: linkedin.com/jobs-tracker) aparecem os status das minhas candidaturas. Isso pode
automatizar o dashboard. Um botão geral no dashboard, com o ícone de cada portal: ao clicar, abre a página para a
pessoa logar e o sistema usa essa sessão. Gupy e Indeed agora; o LinkedIn fica criado, mas desativado. Leitura só no
clique, com a janela minimizada."

## Contexto

O quadro de candidaturas do dashboard depende de a pessoa mover cada vaga à mão. Os portais já sabem o andamento: a
Gupy mostra a etapa de cada processo, o Indeed mostra se o currículo foi enviado ou recusado, e o LinkedIn lista as
candidaturas enviadas. Na prática, o quadro fica atrás dos portais: candidaturas feitas que nunca saíram do
Relatório, reprovações que continuam em "Aplicação Enviada" e desistências que ninguém marcou.

O MCP público da Gupy não tem login nem as candidaturas. A constituição 3.0.0 (princípio VI, "Conta conectada")
passou a permitir ler a área da própria pessoa numa janela do navegador da ferramenta, com o login feito por ela, só
leitura e só no clique, portal por portal.

## Clarifications

### Session 2026-10-17

- Q: Um botão por portal ou um geral? → A: Um botão geral "Atualizar candidaturas", que lê todos os portais
  conectados; o painel mostra os portais com o ícone de cada um.
- Q: Quais portais? → A: Gupy e Indeed ativos. LinkedIn criado, mas desativado.
- Q: Quando lê? → A: Só no clique. Nada agendado.
- Q: A janela aparece? → A: Minimizada durante a leitura; vem para a frente só para login, captcha ou verificação.
  Sem navegador invisível.
- Q: E se a Gupy lançar um MCP com login? → A: Ele substitui a leitura pela janela, sem mudar o resto.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conectar um portal (Priority: P1)

A pessoa clica em "Atualizar candidaturas". O painel lista os portais disponíveis (Gupy e Indeed), cada um com o
ícone, e diz se está conectado. Ela clica em "Conectar" na Gupy. Abre uma janela do navegador da ferramenta, separada
do navegador do dia a dia, na página de login da Gupy. Ela entra na conta, volta ao dashboard e clica em "Pronto". O
painel mostra "Gupy · Conectado". Nas próximas vezes, não precisa logar de novo enquanto a sessão durar.

**Why this priority**: sem conexão não há leitura; é a base de todo o resto.

**Independent Test**: com o navegador simulado, clicar em Conectar e conferir que a janela abre com o perfil da
ferramenta na URL de login do portal, e que o estado vira "Conectado" quando a página de candidaturas responde
logada. Desconectar e conferir que o perfil foi apagado.

**Acceptance Scenarios**:

1. **Given** nenhum portal conectado, **When** a pessoa clica em "Atualizar candidaturas", **Then** o painel abre com
   Gupy e Indeed, cada um com "Conectar".
2. **Given** o painel aberto, **When** a pessoa clica em "Conectar" na Gupy, **Then** abre a janela do navegador da
   ferramenta na página de login da Gupy, e a tela diz "Faça o login na janela que abriu e clique em Pronto".
3. **Given** o login feito, **When** a pessoa clica em "Pronto", **Then** a ferramenta confere a página de
   candidaturas e mostra "Conectado"; se a página ainda pede login, diz que o login não foi concluído.
4. **Given** um portal conectado, **When** a pessoa clica em "Desconectar", **Then** a sessão daquele navegador é
   apagada, e a próxima leitura pede login de novo.
5. **Given** nenhum Edge nem Chrome no computador, **When** a pessoa abre o painel, **Then** ele diz que precisa de
   um dos dois navegadores, sem quebrar.

---

### User Story 2 - Atualizar o quadro com o que os portais mostram (Priority: P1)

Com a Gupy e o Indeed conectados, a pessoa clica em "Atualizar agora". A tela mostra "Lendo suas candidaturas
(Gupy, Indeed), aguarde…". A janela abre minimizada, lê as páginas e fecha. Aparece uma lista agrupada por portal,
com caixas de marcar:
- mudanças de etapa ("Aplicação Enviada → Encerrada · não aprovado");
- vagas que estão no Relatório e devem ir ao quadro;
- candidaturas que não estão no dashboard.

A pessoa desmarca o que não quer e clica em "Aplicar marcadas". O quadro muda só no que foi marcado.

**Why this priority**: é o valor pedido, o quadro em dia sem mover vaga por vaga.

**Independent Test**: com páginas fictícias dos dois portais e um banco temporário, rodar a leitura e conferir a
proposta (mudanças, para o quadro, novas e sem mudança); aplicar só parte dela e conferir que o resto não mudou.

**Acceptance Scenarios**:

1. **Given** portais conectados, **When** a pessoa clica em "Atualizar agora", **Then** nada é gravado até ela clicar
   em "Aplicar marcadas".
2. **Given** uma vaga do quadro em "Aplicação Enviada" que o portal mostra como recusada, **When** a proposta aparece,
   **Then** ela sugere "Encerrada · não aprovado".
3. **Given** uma vaga no Relatório (sem etapa) da qual a pessoa já se candidatou, **When** a proposta aparece,
   **Then** ela sugere levar a vaga ao quadro na etapa do portal.
4. **Given** uma candidatura que não está no dashboard, **When** a proposta aparece, **Then** ela sugere adicionar a
   vaga, com cargo, empresa, link e a etapa do portal.
5. **Given** uma vaga do quadro numa etapa mais avançada que a do portal (ex.: a pessoa já marcou "Entrevista" e o
   portal ainda mostra "Currículo enviado"), **When** a proposta aparece, **Then** ela não sugere voltar a etapa.
6. **Given** uma vaga "Encerrada" no quadro, **When** a proposta aparece, **Then** ela não sugere mudar a etapa.
7. **Given** a pessoa aplicou uma mudança, **When** ela abre o cartão da vaga, **Then** a anotação tem uma linha "Etapa
   atualizada pela [portal] em AAAA-MM-DD: [status]", e a data da etapa é a do portal (ou hoje, se o portal não diz).
8. **Given** um portal com erro, bloqueio ou pedido de login, **When** a leitura roda, **Then** só aquele portal fica
   de fora, com o motivo; os outros seguem.
9. **Given** a leitura terminou, **When** a pessoa olha a tela, **Then** a janela do navegador fechou.

---

### User Story 3 - Status da Gupy e do Indeed traduzidos para o quadro (Priority: P1)

Cada portal mostra a situação de um jeito. A ferramenta traduz para as etapas do quadro, e o que não reconhece vira
só informação.

**Why this priority**: sem a tradução certa, a proposta erra; é parte do valor da US2.

**Independent Test**: com páginas fictícias que tenham cada status conhecido e um desconhecido, conferir a etapa
proposta de cada um.

**Acceptance Scenarios**:

1. **Given** a Gupy com uma candidatura em "Em andamento" numa etapa comum (ex.: 2 de 5, triagem), **When** a
   proposta aparece, **Then** a etapa é "Aplicação Enviada", com "Gupy: etapa 2 de 5 (nome da etapa)" na anotação.
2. **Given** a etapa atual da Gupy com "entrevista", "bate-papo" ou "conversa" no nome, **Then** a etapa é
   "Entrevista"; com "proposta", "oferta" ou "contratação", **Then** é "Proposta".
3. **Given** uma candidatura na aba "Em banco de talentos" da Gupy, **Then** a proposta sugere "Encerrada · não
   aprovado", com a anotação "foi para o banco de talentos da empresa", para a pessoa decidir.
4. **Given** uma candidatura em "Finalizadas" na Gupy, **Then** a etapa é "Encerrada", com o resultado pelo motivo
   mostrado (reprovado, desistência, vaga cancelada, contratado).
5. **Given** o Indeed com "Currículo enviado", **Then** a etapa é "Aplicação Enviada"; com "Reprovação pela empresa",
   "Encerrada · não aprovado"; com "Não tenho mais interesse", "Encerrada · desisti"; na aba Entrevistas,
   "Entrevista".
6. **Given** o aviso "Vaga fechada ou expirada no Indeed", **Then** a etapa não muda; o aviso aparece como informação.
7. **Given** um status que a ferramenta não conhece, **Then** a proposta não muda a etapa e mostra "status no
   [portal]: [texto]".
8. **Given** uma data sem ano ("4 de out"), **Then** vale o ano atual, ou o anterior se a data ficar no futuro;
   "hoje" vale a data do dia.

---

### User Story 4 - LinkedIn pronto, mas desligado (Priority: P3)

O leitor do LinkedIn (Rastreador de vagas) fica pronto e testado, mas não aparece no painel nem é lido. Ligar depende
de uma decisão futura da pessoa.

**Why this priority**: a pessoa pediu para criar sem ativar; o LinkedIn restringe contas automatizadas.

**Independent Test**: conferir que o LinkedIn não aparece no painel nem é lido, e que a leitura e a tradução dele
funcionam com uma página fictícia.

**Acceptance Scenarios**:

1. **Given** a ferramenta como entregue, **When** a pessoa abre o painel, **Then** o LinkedIn não aparece.
2. **Given** uma página fictícia do Rastreador de vagas, **When** o leitor do LinkedIn roda nos testes, **Then**:
   - "Candidaturas enviadas" vira "Aplicação Enviada" e "Entrevistas" vira "Entrevista";
   - "Não aceita mais candidaturas" e "Arquivadas" só informam;
   - "há 1 sem" e "há 1 m" viram datas aproximadas, marcadas como aproximadas.

---

### Edge Cases

- **Botões do portal**: a leitura nunca clica em "Desistir", "Atualizar status", "Recebeu resposta? Sim/Não",
  "Adicionar nota" nem em nada que mude a candidatura.
- **Paginação**: todas as páginas de candidaturas são lidas, com uma pausa curta entre elas e um limite de 10 páginas
  por portal.
- **Página do portal mudou**: o leitor não acha os cartões e avisa "não consegui ler as candidaturas da [portal]";
  nada é gravado.
- **Mesma vaga em dois portais** (ex.: Indeed e Gupy): o casamento usa os ids que o banco já junta; a proposta mostra
  um item só, com o portal mais avançado.
- **Vaga sem id reconhecível no link**: o casamento usa cargo + empresa, só para vagas recentes, como o banco já faz.
- **Vaga nova sem descrição**: entra com cargo, empresa e link; a nota de aderência fica pendente até ter texto.
- **Dashboard aberto de outro aparelho** (`--rede`): o painel avisa que contas conectadas só funcionam no computador
  onde a ferramenta roda.
- **Navegador já aberto pela pessoa**: a janela da ferramenta usa outro perfil e não mexe no navegador do dia a dia.
- **Sessão expirada**: a leitura daquele portal para com "faça o login de novo", e a janela vem para a frente.
- **Duas leituras ao mesmo tempo**: a segunda espera a primeira ou avisa que já há uma leitura em andamento.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O dashboard MUST ter um botão geral "Atualizar candidaturas" que abre o painel de contas conectadas,
  com cada portal ativo, o ícone dele e o estado (conectado ou não).
- **FR-002**: "Conectar" MUST abrir uma janela do Edge ou do Chrome com um perfil só da ferramenta, guardado
  localmente fora do Git, na página de login do portal. A ferramenta MUST NOT pedir, guardar ou ler senha, nem copiar
  cookies para fora do navegador.
- **FR-003**: "Desconectar" MUST fechar a janela e apagar a sessão do perfil da ferramenta.
- **FR-004**: A leitura MUST acontecer só no clique em "Atualizar agora", com a janela minimizada, e MUST fechar a
  janela ao terminar. Login, captcha ou verificação MUST trazer a janela para a frente e parar a leitura daquele
  portal, com aviso.
- **FR-005**: A leitura MUST ser só leitura: nunca clicar em botões que mudem a candidatura nem enviar nada ao
  portal.
- **FR-006**: Cada portal MUST seguir um contrato comum (conectar, ler as candidaturas com id, cargo, empresa, status,
  data e link, e traduzir status em etapa), para que um portal novo seja só um módulo a mais.
- **FR-007**: A leitura MUST devolver uma proposta sem gravar nada, agrupada por portal: mudanças de etapa, vagas para
  o quadro, vagas novas e sem mudança.
- **FR-008**: A proposta MUST NOT rebaixar a etapa de uma vaga nem mudar uma vaga encerrada.
- **FR-009**: Aplicar MUST gravar só os itens marcados. Para cada mudança, a etapa, a data da etapa (do portal ou de
  hoje), o resultado quando encerrada e uma linha na anotação com o portal, a data e o status.
- **FR-010**: O casamento com o banco MUST usar os ids que o dashboard já conhece (`gupy-N` para a Gupy, `jk` para o
  Indeed, `li-N` para o LinkedIn), com cargo + empresa como reserva.
- **FR-011**: Vagas novas MUST entrar com cargo, empresa, link e a etapa proposta. A descrição vem do leitor público do
  portal quando der (Gupy pelo MCP público; Indeed pelo leitor de link que já existe).
- **FR-012**: As traduções de status MUST seguir a US3. Status desconhecido MUST virar só informação.
- **FR-013**: O LinkedIn MUST ficar implementado e testado, mas desativado: fora do painel e da leitura.
- **FR-014**: As rotas de contas conectadas MUST funcionar só no computador onde a ferramenta roda.
- **FR-015**: README, AGENTS.md e as skills consultar-gupy e buscar-vagas MUST explicar as contas conectadas: o que é
  lido, onde fica a sessão, como desconectar, e que nada é gravado sem confirmação.

### Key Entities

- **Conta conectada**: um portal ativo (nome, ícone, URL de login e de candidaturas) e se a sessão está aberta no
  perfil da ferramenta.
- **Candidatura lida**: o portal, o id da vaga no formato do dashboard, cargo, empresa, status como o portal mostra,
  data, link e avisos (ex.: vaga fechada).
- **Proposta**: os itens por portal (mudar etapa, levar ao quadro, adicionar, sem mudança), cada um com a etapa e o
  resultado sugeridos e a marcação da pessoa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com a Gupy e o Indeed conectados, a pessoa põe o quadro em dia com dois cliques ("Atualizar agora" e
  "Aplicar marcadas"), sem mover vaga por vaga.
- **SC-002**: Com as páginas fictícias dos dois portais, 100% dos status conhecidos viram a etapa da US3, e 100% dos
  desconhecidos viram só informação.
- **SC-003**: Nenhuma vaga muda sem estar marcada; nenhuma etapa é rebaixada; nenhuma vaga encerrada muda.
- **SC-004**: Nenhum botão de portal é clicado; o código de leitura só lê a página.
- **SC-005**: Depois de "Desconectar", o perfil do navegador da ferramenta não existe mais no disco.
- **SC-006**: Com um portal bloqueado ou deslogado, o outro portal é lido normalmente, e o aviso diz qual parou e
  por quê.
- **SC-007**: O LinkedIn não aparece no painel, e os testes do leitor dele passam.

## Assumptions

- Windows 10/11 com o Edge, que vem instalado; o Chrome serve de alternativa. Sem Playwright, Node ou dependência
  nova: a conversa com a janela usa o protocolo de depuração do navegador com a biblioteca padrão.
- A forma exata de ler cada página (pelo que a tela mostra ou pela chamada que a própria página faz) é decidida na
  pesquisa, com a pessoa logada na janela da ferramenta e o OK dela. Os dados reais não entram em testes nem na
  `master`; os testes usam páginas fictícias com a mesma estrutura.
- As traduções de status partem dos prints da pessoa (2026-10-17) e são completadas na pesquisa com os status
  reais.
- A sessão dura o que o portal decidir; quando expira, a pessoa loga de novo na janela.
- A emenda da constituição 3.0.0 já foi aprovada (commit dc8bc34 na branch).
- Verificação só no Windows.
