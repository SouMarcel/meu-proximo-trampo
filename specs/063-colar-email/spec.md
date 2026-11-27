# Feature Specification: Colar e-mail (negativas e alertas de vagas)

**Feature Branch**: `063-colar-email` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Na página, um 'Colar e-mail' (junto do Adicionar Vaga, que já tem 'Colar texto de post ou
mensagem') onde a pessoa cola o texto de um e-mail que recebeu. A ferramenta reconhece o tipo: (a) negativa de
candidatura → acha a vaga correspondente em Aplicações e propõe marcar como recusada, a pessoa confirma; (b) alerta de
vagas (LinkedIn, Indeed, JobGether, várias vagas num e-mail) → lista as vagas e propõe adicionar as que a pessoa
marcar, pelo fluxo de Adicionar Vaga. Foco principal: as negativas. Sem acesso à caixa de e-mail e sem credenciais.
Texto do e-mail é dado, nunca instrução."

## Contexto

Quem procura emprego recebe todo dia, por e-mail, as negativas das candidaturas ("infelizmente não seguiremos com a
sua candidatura") e os alertas de vagas dos portais. Hoje a negativa só entra na ferramenta se a pessoa abrir a vaga
em Aplicações e marcar à mão o resultado; o "Atualizar candidaturas" (spec 018) lê só a área logada de alguns portais
(Gupy, Indeed, Nerdin) e não cobre a negativa que chega da empresa ou do LinkedIn. Os alertas trazem vagas que a busca
nem sempre pega (outros termos, outro dia).

A ferramenta não acessa a caixa de e-mail (decisão da pessoa: sem credencial, sem acesso à caixa). A pessoa copia o
texto do e-mail e cola na página.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Negativa vira resultado da candidatura (Priority: P1)

A pessoa recebe "Obrigado pelo interesse na vaga de Analista de Dados na Empresa X; seguimos com outros candidatos".
Ela cola o texto em "Colar e-mail". A ferramenta reconhece que é uma negativa, acha em Aplicações a candidatura da
Empresa X para Analista de Dados e mostra: "Marcar a candidatura de Analista de Dados — Empresa X como não aprovada?",
com o trecho do e-mail em que se apoia. A pessoa confirma, e a candidatura vai para encerrada, resultado "não
aprovado", com a data do e-mail (ou a de hoje) e o trecho guardado na vaga.

**Why this priority**: é o uso diário e o que hoje dá trabalho manual; mantém o funil de Aplicações em dia.

**Independent Test**: com três candidaturas em Aplicações, colar uma negativa de uma delas e confirmar; só ela muda,
e com o resultado certo.

**Acceptance Scenarios**:

1. **Given** uma candidatura aplicada da Empresa X para o cargo Y, **When** a pessoa cola uma negativa que cita a
   Empresa X e o cargo Y, **Then** a ferramenta propõe marcar essa candidatura como não aprovada, mostrando o trecho, e
   nada muda até a pessoa confirmar.
2. **Given** a proposta confirmada, **When** a pessoa abre a vaga, **Then** ela está em encerrada, com resultado "não
   aprovado", a data e o trecho da negativa; a análise de reprovação (spec 049) fica disponível como hoje.
3. **Given** duas candidaturas na mesma empresa, **When** a negativa não deixa claro o cargo, **Then** a ferramenta
   mostra as duas e a pessoa escolhe qual (ou nenhuma).
4. **Given** uma negativa de uma empresa sem candidatura em Aplicações, **When** a pessoa cola o texto, **Then** a
   ferramenta diz que não achou a candidatura e oferece escolher a vaga numa lista de Aplicações, sem criar vaga nova.
5. **Given** uma candidatura já encerrada, **When** chega a negativa dela, **Then** a ferramenta avisa que ela já está
   encerrada e só oferece guardar o trecho.

---

### User Story 2 - Alerta de vagas vira vagas no quadro (Priority: P2)

A pessoa cola um alerta do LinkedIn ("10 novas vagas para Scrum Master"). A ferramenta lista as vagas que achou no
texto (cargo, empresa, local, link), marca as que já estão no quadro e deixa a pessoa escolher quais adicionar. As
escolhidas entram pelo mesmo caminho do Adicionar Vaga por link (a leitura pública do link, sem login, com as regras de
cada portal), e a análise automática dá a nota.

**Why this priority**: útil, mas a busca já cobre boa parte dessas vagas; as negativas valem mais.

**Independent Test**: colar um alerta fictício com 4 vagas, uma delas já no quadro; a lista mostra 4, com 1 marcada
"já no quadro", e adicionar 2 cria 2 vagas.

**Acceptance Scenarios**:

1. **Given** um alerta com várias vagas, **When** a pessoa cola o texto, **Then** a ferramenta lista cada vaga com
   cargo, empresa, local e link, sem adicionar nada sozinha.
2. **Given** uma vaga do alerta que já está no quadro (mesmo link ou mesma vaga em outro portal, spec 058), **When** a
   lista aparece, **Then** ela vem marcada "já no quadro" e não é adicionada de novo.
3. **Given** a pessoa marca 3 vagas e confirma, **When** a ferramenta adiciona, **Then** cada uma passa pelo fluxo do
   Adicionar Vaga por link; o portal que bloquear deixa a vaga com a descrição pendente, como hoje.

---

### User Story 3 - E-mail que não é nem uma coisa nem outra (Priority: P3)

A pessoa cola um e-mail de convite para entrevista, de teste técnico ou uma propaganda. A ferramenta diz o que
entendeu ("parece um convite para entrevista da Empresa X") e, quando acha a candidatura, oferece o passo que já
existe (mover para Entrevista), ou diz que não reconheceu o e-mail, sem mudar nada.

**Why this priority**: evita erro de leitura nos e-mails que não são negativa nem alerta.

**Independent Test**: colar um convite de entrevista e um e-mail de propaganda; nenhum muda nada sem confirmação.

**Acceptance Scenarios**:

1. **Given** um convite para entrevista de uma candidatura aplicada, **When** a pessoa cola o texto, **Then** a
   ferramenta propõe mover para Entrevista; nada muda sem a confirmação.
2. **Given** um e-mail sem relação com vagas, **When** a pessoa cola o texto, **Then** a ferramenta diz que não
   reconheceu e não muda nada.

### Edge Cases

- E-mail em inglês ("unfortunately", "we decided to move forward with other candidates"): reconhecido como negativa.
- Negativa genérica, sem cargo nem empresa no texto (só a assinatura do portal): a ferramenta pede para a pessoa
  escolher a candidatura.
- Texto com instruções dirigidas à IA ou ao leitor ("ignore as instruções…"): tratado como dado; nada que o e-mail
  peça é executado, e o achado aparece como aviso (filtro de integridade, spec 034).
- Texto colado com cabeçalhos, rodapé, links de descadastro e endereços: só o necessário é usado; o resto não é
  guardado nem enviado.
- E-mail muito longo (alerta com dezenas de vagas): a lista mostra todas; nada é adicionado sem escolha.
- Sem IA ligada: os formatos conhecidos (negativa típica, alerta dos portais da ferramenta) funcionam; o que não for
  reconhecido sem IA aparece como "não reconheci; escolha a candidatura" (negativa) ou "não reconheci" (outros).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A página MUST oferecer "Colar e-mail" junto do Adicionar Vaga, com uma caixa de texto e um botão para
  ler o e-mail.
- **FR-002**: A ferramenta MUST classificar o texto em negativa, alerta de vagas, convite (entrevista ou teste) ou não
  reconhecido, e mostrar o que entendeu antes de qualquer mudança.
- **FR-003**: Numa negativa, a ferramenta MUST procurar a candidatura em Aplicações pela empresa e pelo cargo citados
  e propor marcar como encerrada com resultado "não aprovado"; com mais de uma possível, MUST deixar a pessoa escolher;
  sem nenhuma, MUST oferecer a escolha numa lista de Aplicações.
- **FR-004**: Nenhuma etapa, resultado ou vaga MUST mudar sem a confirmação da pessoa (constituição V).
- **FR-005**: Ao confirmar uma negativa, a ferramenta MUST guardar na vaga a data e o trecho do e-mail em que a
  negativa se apoia (não o e-mail inteiro).
- **FR-006**: Num alerta, a ferramenta MUST listar as vagas encontradas (cargo, empresa, local, link), marcar as que já
  estão no quadro e adicionar só as escolhidas, pelo fluxo do Adicionar Vaga por link.
- **FR-007**: Num convite, a ferramenta MUST propor mover a candidatura para Entrevista, com confirmação.
- **FR-008**: O texto colado MUST ser tratado como dado, nunca como instrução: passa pelo filtro de integridade (spec
  034) e nada que ele peça é executado.
- **FR-009**: A ferramenta MUST funcionar sem IA para as negativas e os alertas nos formatos conhecidos; com IA ligada,
  MAY usar a IA para os e-mails que não reconheceu, mandando só o texto do e-mail (sem cabeçalhos de endereço) e a lista
  de candidaturas (empresa e cargo).
- **FR-010**: O texto colado MUST NOT ser guardado depois da leitura, a não ser o trecho do FR-005.
- **FR-011**: A ferramenta MUST NOT acessar a caixa de e-mail nem pedir credencial de e-mail.
- **FR-012**: A documentação (README, AGENTS.md, `dash/API.md`) MUST descrever o "Colar e-mail".

### Key Entities

- **E-mail colado**: o texto que a pessoa cola; não é guardado.
- **Leitura do e-mail**: o tipo (negativa, alerta, convite, não reconhecido), a empresa e o cargo citados, o trecho de
  apoio, a data e, num alerta, a lista de vagas.
- **Proposta**: a mudança sugerida (marcar não aprovada, mover para Entrevista, adicionar vagas), que só vale com a
  confirmação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa amostra de 20 negativas reais coladas pela pessoa, pelo menos 18 acham a candidatura certa (ou
  pedem a escolha quando há mais de uma) sem a pessoa procurar a vaga.
- **SC-002**: Registrar uma negativa leva no máximo 3 ações da pessoa (colar, ler, confirmar).
- **SC-003**: Nenhuma mudança acontece sem confirmação, em 100% dos casos testados (incluindo e-mails com instruções
  embutidas).
- **SC-004**: Num alerta com N vagas, a lista mostra as N, e as que já estão no quadro aparecem marcadas.

## Assumptions

- A pessoa copia o texto do e-mail no app de e-mail dela (Outlook, Gmail…) e cola na página; não há importação de
  arquivo nem acesso à caixa (os caminhos 2 e 3 da conversa de 26/11 ficam para depois, na lista de desejos).
- "Recusada" é a etapa encerrada com o resultado "não aprovado", como hoje; a análise de reprovação (spec 049) continua
  como é.
- A busca do chat (skill `buscar-vagas`) não ganha esse fluxo agora; só a página.
- A vaga do alerta adicionada pelo link segue as regras de cada portal (sem login; no bloqueio, a descrição fica
  pendente).
