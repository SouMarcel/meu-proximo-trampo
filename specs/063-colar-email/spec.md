# Feature Specification: Colar e-mail em Atualizar candidaturas

**Feature Branch**: `063-colar-email` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Em Atualizar candidaturas, uma área para colar o conteúdo do e-mail. Vale para qualquer
status: desde a candidatura validada (aplicação recebida), entrevista, proposta, negativa, desistência etc. A
ferramenta reconhece o que o e-mail diz, acha a candidatura e propõe a mudança; a pessoa confirma. Sem acesso à caixa
de e-mail e sem credenciais. Texto do e-mail é dado, nunca instrução."

## Contexto

O andamento das candidaturas chega por e-mail: a confirmação de que a candidatura foi recebida, o convite para
entrevista ou teste, a proposta, a negativa ("infelizmente não seguiremos"), o aviso de vaga cancelada. Hoje esse
andamento só entra na ferramenta se a pessoa abrir a vaga em Aplicações e mudar a etapa à mão. O "Atualizar
candidaturas" (spec 018) lê a área logada de alguns portais (Gupy, Indeed, Nerdin) e propõe as mudanças, mas não cobre
o que chega por e-mail das empresas, do LinkedIn, do JobGether e dos outros portais.

A ferramenta não acessa a caixa de e-mail (decisão da pessoa: sem credencial e sem acesso à caixa). A pessoa copia o
texto do e-mail e cola em Atualizar candidaturas, que passa a ter o e-mail como mais uma fonte das mesmas propostas.

## Clarifications

### Session 2026-11-26

- Q: Onde fica e o que cobre? → A: dentro de Atualizar candidaturas, para qualquer mudança de status da candidatura
  (recebida, entrevista, teste, proposta, negativa, cancelada, desistência, contratação). Os alertas de vagas por
  e-mail saem desta spec e vão para a lista de desejos.
- Q: O que fica guardado quando a pessoa confirma? → A: só a movimentação do card para o status identificado e a
  justificativa (data, tipo do e-mail e o trecho em que se apoia) acrescentada às Anotações do card (Andamento e
  anotação > Anotações). Nada mais é guardado: nem o e-mail, nem um histórico à parte.
- Q: Quando a leitura sem IA não reconhece um e-mail, como a IA entra? → A: automática, com a IA ligada: o e-mail não
  reconhecido vai à IA logo depois do Ler, sem clique a mais. A pessoa cola só o corpo do e-mail, e um aviso no topo da
  caixa diz isso.
- Q: Como separar vários e-mails colados de uma vez? → A: cada e-mail na sua caixa; o botão "+ outro e-mail" abre mais
  uma caixa, e o Ler lê todas.
- Q: Como validar a SC-001? → A: testes automáticos com 20 e-mails fictícios no repositório (português e inglês, todos
  os tipos) exigem 18 acertos; no teste na branch pessoal, a pessoa cola os e-mails reais que tiver, sem número mínimo,
  e eles nunca entram no Git.
- Q: E quando o e-mail não muda a etapa (o card já está nela ou adiante)? → A: a ferramenta propõe "só anotar": o card
  fica onde está e, se a pessoa marcar, a justificativa entra nas Anotações.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - E-mail vira a mudança de etapa da candidatura (Priority: P1)

A pessoa abre Atualizar candidaturas, cola o texto de um e-mail e clica em Ler. A ferramenta diz o que entendeu
("negativa da Empresa X para Analista de Dados"), acha a candidatura em Aplicações e propõe a mudança, com o trecho do
e-mail em que se apoia. A pessoa confirma: o card vai para o status identificado, e a justificativa (data, tipo do e-mail e trecho) é
acrescentada às Anotações do card, em Andamento e anotação, sem apagar o que já estava lá.

| O e-mail diz | Proposta |
|---|---|
| Candidatura recebida, validada, em análise | etapa Aplicada (se ainda estava Salva) |
| Convite para entrevista, teste técnico, case, próxima fase | etapa Entrevista |
| Proposta, oferta | etapa Proposta |
| Negativa ("seguimos com outros candidatos", "unfortunately") | Encerrada, resultado "não aprovado" |
| Vaga cancelada, encerrada ou congelada pela empresa | Encerrada, resultado "cancelada" |
| Desistência (a pessoa retirou a candidatura) | Encerrada, resultado "desisti" |
| Contratação, boas-vindas | Encerrada, resultado "contratado" |

**Why this priority**: é o uso diário; mantém o funil de Aplicações em dia sem a pessoa procurar a vaga.

**Independent Test**: com três candidaturas em Aplicações, colar uma negativa, um convite de entrevista e uma
confirmação de candidatura recebida; cada um propõe a mudança certa na candidatura certa, e nada muda sem confirmar.

**Acceptance Scenarios**:

1. **Given** uma candidatura aplicada da Empresa X para o cargo Y, **When** a pessoa cola uma negativa que cita a
   Empresa X e o cargo Y, **Then** a ferramenta propõe Encerrada com "não aprovado", mostrando o trecho, e nada muda
   até a confirmação.
2. **Given** a proposta confirmada, **When** a pessoa abre a vaga, **Then** ela tem a nova etapa (e o resultado, se
   encerrada) e, nas Anotações, uma linha nova com a justificativa (ex.: "26/11 — e-mail de negativa: 'seguimos com
   outros candidatos'"); as anotações anteriores ficam; a análise de reprovação (spec 049) fica disponível como hoje.
3. **Given** um convite para entrevista de uma candidatura aplicada, **When** a pessoa cola o texto, **Then** a
   ferramenta propõe a etapa Entrevista.
4. **Given** uma candidatura já na etapa do e-mail ou mais adiante (ex.: em Entrevista e chega o convite para a 2ª
   entrevista, ou "candidatura recebida"), **When** a pessoa cola o texto, **Then** a ferramenta não propõe voltar a
   etapa: propõe "só anotar", dizendo que a candidatura já está nessa etapa ou adiante; se a pessoa marcar, só a
   justificativa entra nas Anotações, e o card fica onde está.
5. **Given** duas candidaturas na mesma empresa, **When** o e-mail não deixa claro o cargo, **Then** a ferramenta
   mostra as duas e a pessoa escolhe qual (ou nenhuma).
6. **Given** um e-mail de uma candidatura que não está em Aplicações, **When** a pessoa cola o texto, **Then** a
   ferramenta diz que não achou e oferece escolher a vaga numa lista do quadro ou não fazer nada.

---

### User Story 2 - Vários e-mails de uma vez (Priority: P2)

A pessoa cola o primeiro e-mail, clica em "+ outro e-mail" para abrir mais uma caixa, cola o seguinte, e assim por
diante; depois clica em Ler. A ferramenta lê todas as caixas, mostra uma proposta por e-mail, cada uma com a candidatura e a mudança, e a pessoa confirma as que quiser de uma vez.

**Why this priority**: quem acumula a semana de e-mails resolve tudo numa vez só.

**Independent Test**: colar três e-mails, cada um na sua caixa (negativa, entrevista, recebida), e confirmar dois; só os dois
mudam.

**Acceptance Scenarios**:

1. **Given** três e-mails colados em três caixas, **When** a pessoa clica em Ler, **Then** aparecem três propostas, uma por
   e-mail, cada uma com o seu trecho.
2. **Given** as três propostas, **When** a pessoa marca duas e confirma, **Then** só as duas candidaturas mudam.

### Edge Cases

- E-mail em inglês ou espanhol: reconhecido pelos mesmos tipos.
- E-mail genérico, sem cargo nem empresa no texto (só a assinatura do portal): a ferramenta pede para a pessoa escolher
  a candidatura.
- Texto com instruções dirigidas à IA ou ao leitor ("ignore as instruções…"): tratado como dado; nada que o e-mail
  peça é executado, e o achado aparece como aviso (filtro de integridade, spec 034).
- Texto colado com cabeçalhos, rodapé, links de descadastro e endereços, apesar do aviso de colar só o corpo: os
  endereços de e-mail e as linhas de cabeçalho (De, Para, Cc, Assunto, Data) são tirados antes da leitura; nada é
  guardado, e esses dados não vão à IA.
- E-mail que não é sobre candidatura (propaganda, alerta de vagas, newsletter): a ferramenta diz que não reconheceu e
  não muda nada.
- Mudança que já foi feita (a candidatura já está encerrada como "não aprovado" e chega a negativa): a ferramenta
  avisa e propõe "só anotar"; o card e o resultado não mudam.
- Proposta do e-mail e proposta do portal (Atualizar candidaturas pela conta conectada) para a mesma vaga: as duas
  aparecem na mesma lista, e a pessoa escolhe.
- Sem IA ligada: os textos típicos de cada tipo funcionam; o que não for reconhecido sem IA aparece como "não
  reconheci; escolha a candidatura e a mudança".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Atualizar candidaturas MUST ganhar uma área "Colar e-mail", com uma caixa de texto e o botão Ler,
  disponível mesmo sem nenhum portal conectado. Um aviso no topo da caixa MUST pedir que a pessoa cole só o corpo do
  e-mail (sem remetente, destinatários e cabeçalhos).
- **FR-002**: A ferramenta MUST reconhecer o tipo de cada e-mail (recebida, entrevista/teste, proposta, negativa,
  cancelada, desistência, contratação ou não reconhecido) e mostrar o que entendeu antes de qualquer mudança.
- **FR-003**: Para cada e-mail reconhecido, a ferramenta MUST procurar a candidatura pela empresa e pelo cargo citados
  e propor a mudança da tabela da US1; com mais de uma candidatura possível, MUST deixar a pessoa escolher; sem nenhuma,
  MUST oferecer a escolha numa lista do quadro.
- **FR-004**: A ferramenta MUST NOT propor voltar uma candidatura para uma etapa anterior à atual. Quando o e-mail
  aponta a etapa atual ou uma anterior, MUST propor "só anotar" (o card fica onde está; ao confirmar, só a
  justificativa do FR-006 entra nas Anotações).
- **FR-005**: Nenhuma etapa ou resultado MUST mudar sem a confirmação da pessoa (constituição V); a confirmação pode
  ser de várias propostas de uma vez.
- **FR-006**: Ao confirmar, a ferramenta MUST mover o card para o status identificado e acrescentar às Anotações do
  card (Andamento e anotação > Anotações) uma linha com a justificativa: a data, o tipo do e-mail e o trecho em que a
  mudança se apoia (não o e-mail inteiro), sem apagar as anotações que já existem.
- **FR-007**: A área MUST ter o botão "+ outro e-mail", que abre mais uma caixa (um e-mail por caixa); o Ler MUST ler
  todas as caixas preenchidas e mostrar uma proposta por e-mail. Caixa vazia é ignorada.
- **FR-008**: O texto colado MUST ser tratado como dado, nunca como instrução: passa pelo filtro de integridade (spec
  034) e nada que ele peça é executado.
- **FR-009**: A ferramenta MUST funcionar sem IA para os textos típicos de cada tipo; com IA ligada, o e-mail que a
  leitura sem IA não reconheceu MUST ir à IA automaticamente, logo depois do Ler, sem clique a mais, mandando só o
  corpo do e-mail (já sem endereços e cabeçalhos, FR-008) e a lista de candidaturas (empresa, cargo, etapa).
- **FR-010**: Fora do FR-006, nada MUST ser guardado: nem o texto colado, nem a leitura, nem um histórico à parte.
- **FR-011**: A ferramenta MUST NOT acessar a caixa de e-mail nem pedir credencial de e-mail.
- **FR-012**: As propostas vindas do e-mail MUST aparecer junto das propostas dos portais conectados, no mesmo formato,
  com a origem "e-mail".
- **FR-013**: A documentação (README, AGENTS.md, `dash/API.md`) MUST descrever o "Colar e-mail".

### Key Entities

- **E-mail colado**: o corpo de um e-mail, numa caixa; não é guardado.
- **Leitura do e-mail**: o tipo, a empresa e o cargo citados, a data e o trecho de apoio; existe só durante a
  leitura e a confirmação.
- **Proposta**: a candidatura, a etapa (e o resultado) sugeridos ou "só anotar", a origem (e-mail ou portal); só vale
  com a confirmação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa amostra de 20 e-mails fictícios de candidatura nos testes automáticos (português e inglês, todos os
  tipos da US1, sem dado pessoal), pelo menos 18 levam à candidatura certa com a mudança certa, ou pedem a escolha
  quando há mais de uma candidatura possível. No teste na branch pessoal, os e-mails reais que a pessoa tiver são
  colados para conferir o mesmo comportamento (sem número mínimo; nunca entram no Git).
- **SC-002**: Registrar o andamento de um e-mail leva no máximo 3 ações da pessoa (colar, ler, confirmar).
- **SC-003**: Nenhuma mudança acontece sem confirmação, e nenhuma candidatura volta de etapa, em 100% dos casos
  testados (incluindo e-mails com instruções embutidas).
- **SC-004**: Cinco e-mails colados em cinco caixas geram cinco propostas, confirmadas de uma vez.

## Assumptions

- A pessoa copia o texto do e-mail no app de e-mail dela (Outlook, Gmail…) e cola na página; não há importação de
  arquivo nem acesso à caixa (os outros caminhos da conversa de 26/11 ficam na lista de desejos).
- As etapas e os resultados são os que a ferramenta já tem (Salva, Aplicada, Entrevista, Proposta, Encerrada; não
  aprovado, desisti, cancelada, sem resposta, contratado); a spec não cria etapa nova.
- A busca do chat (skill `buscar-vagas`, Fluxo C) pode ganhar o mesmo reconhecimento depois; esta spec cobre a página.
- Os alertas de vagas por e-mail ficam fora desta spec (lista de desejos).
- A data da justificativa nas Anotações é a da confirmação: só o corpo é colado, e ele em geral não traz a data do
  e-mail.
- Se a IA falhar ou estiver no limite de uso, o e-mail aparece como "não reconheci; escolha a candidatura e a
  mudança", como sem IA.
