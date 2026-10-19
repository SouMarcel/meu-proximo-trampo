# Feature Specification: Forçar verificar a nota de uma vaga

**Feature Branch**: `021-forcar-verificar` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Fizemos uma melhoria para que as vagas ainda sem nota pudessem ser analisadas
independente do período de 6h do LinkedIn. Podemos colocar um botão na vaga sem a nota ainda: embaixo de Seguir /
Não seguir, adicione o botão 'Forçar verificar' para que a nota seja verificada após alguns minutos."

## Contexto

Hoje a nota de aderência sai sozinha só para as vagas marcadas como "aguardando análise". Uma vaga do Relatório pode
ficar sem nota por vários motivos, e nenhum deles tem um jeito de pedir a nota daquela vaga:
- a busca rodou sem IA, sem perfil ou com "Buscar sem nota" (a vaga fica "sem nota");
- a vaga foi adicionada à mão sem descrição;
- a vaga do LinkedIn ficou com **descrição pendente** (limite de leituras ou espera de 6 horas);
- a IA falhou ou não devolveu a vaga, e ela não é tentada de novo até o servidor reiniciar.

A spec 019 resolveu as descrições pendentes em lote (botão "Completar descrições"). Esta spec dá à pessoa um botão
por vaga.

## Clarifications

### Session 2026-10-19

- Q: Em quais vagas o botão aparece? → A: Em todas as vagas sem nota do Relatório (triagem e Fora dos critérios);
  vaga com nota não ganha o botão.
- Q: Na vaga com descrição pendente? → A: Fora da espera do portal, lê a descrição daquela vaga (um pedido) e pede a
  nota; na espera, dá a nota com o que tem (título, empresa, local) e marca "nota sem a descrição"; quando a
  descrição chegar, a nota é refeita.
- Q: Sem IA configurada? → A: O botão avisa "Para dar nota, ligue uma IA" e leva ao botão IA do topo; nada é gravado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pedir a nota de uma vaga sem nota (Priority: P1)

No cartão de uma vaga sem nota, embaixo de "Seguir com a vaga" / "Não seguir", a pessoa clica em **Forçar
verificar**. O cartão passa a mostrar "verificando…" e, em alguns minutos, a nota aparece com o resumo, o que bate e
o que falta, como nas outras vagas.

**Why this priority**: é o pedido central; hoje a vaga sem nota só ganha nota numa busca nova ou pelo chat.

**Independent Test**: com uma vaga "sem nota" que tem descrição e uma IA falsa, clicar no botão e ver a vaga ganhar
a nota, sem mexer nas outras vagas sem nota.

**Acceptance Scenarios**:

1. **Given** uma vaga sem nota com descrição, **When** a pessoa clica em Forçar verificar, **Then** o cartão mostra
   "verificando…", o botão fica desligado e, quando a IA termina, a nota aparece sem recarregar a página.
2. **Given** várias vagas sem nota, **When** a pessoa força uma, **Then** só essa vai para a IA (as outras continuam
   como estavam).
3. **Given** a IA falhar ou não devolver a vaga, **When** a análise termina, **Then** o cartão volta a mostrar o botão
   e o aviso do erro, e a pessoa pode tentar de novo.
4. **Given** uma vaga que já tem nota, **When** a pessoa vê o cartão, **Then** o botão não aparece.
5. **Given** uma vaga sem nota em Fora dos critérios, **When** a pessoa força a verificação, **Then** ela ganha a nota
   e continua em Fora dos critérios.
6. **Given** uma vaga ainda na triagem cuja análise mostra que ela fura os filtros (ex.: o texto diz presencial),
   **When** a nota chega, **Then** ela vai para Fora dos critérios com o motivo, como acontece com a nota automática.

---

### User Story 2 - Vaga com descrição pendente (Priority: P2)

Numa vaga do LinkedIn com descrição pendente, o Forçar verificar primeiro tenta ler a descrição daquela vaga (um
pedido só). Se o portal estiver na espera depois de um bloqueio, não há pedido: a nota sai com título, empresa e
local, marcada "nota sem a descrição"; quando a descrição for lida depois (Completar descrições ou a próxima busca),
a nota é refeita com o texto completo.

**Why this priority**: são a maior parte das vagas sem nota; a regra de não consultar o portal na espera continua.

**Independent Test**: com uma vaga pendente e o portal fora da espera, conferir um pedido de descrição e a nota; com
o portal em espera, conferir nenhum pedido, a nota com a marca e, depois de completar a descrição, a vaga de volta
para a análise.

**Acceptance Scenarios**:

1. **Given** uma vaga com descrição pendente e o portal fora da espera, **When** a pessoa força, **Then** a ferramenta
   faz um pedido só, grava a descrição, tira a marca de pendente e pede a nota.
2. **Given** o portal em espera, **When** a pessoa força, **Then** nenhum pedido vai ao portal e a nota sai com o que a
   vaga tem, com a marca "nota sem a descrição" no cartão e no detalhe.
3. **Given** a leitura da descrição falhar ou o portal bloquear nesse pedido, **When** a ferramenta recebe o erro,
   **Then** segue para a nota sem a descrição (com a marca) e, no bloqueio, o portal entra na espera como numa busca.
4. **Given** uma vaga com "nota sem a descrição", **When** a descrição completa chega, **Then** a vaga volta a aguardar
   a nota e recebe a nota nova.

---

### User Story 3 - Sem IA, aviso claro (Priority: P3)

Sem IA configurada, o Forçar verificar não grava nada e mostra "Para dar nota, ligue uma IA", com o atalho para o
botão IA do topo.

**Why this priority**: evita o clique que não faz nada.

**Independent Test**: com a IA desligada, clicar e ver o aviso; a vaga continua igual.

**Acceptance Scenarios**:

1. **Given** nenhuma IA ligada, **When** a pessoa clica, **Then** aparece o aviso com o atalho e a vaga não muda.

---

### Edge Cases

- **Dois cliques seguidos ou duas abas**: a vaga entra na fila uma vez só.
- **Busca em andamento**: o pedido entra na mesma fila da análise; a vaga recebe a nota quando a fila chegar nela.
- **Vaga sem descrição e de portal sem leitura de descrição** (adicionada à mão, outra plataforma): nota com o que tem,
  com a marca "nota sem a descrição".
- **Vaga removida enquanto verificava**: a análise ignora a vaga e não dá erro.
- **Página aberta noutro computador da rede**: o botão responde "só neste computador", como o "Tentar a nota de
  novo" (a nota gasta a IA da pessoa).
- **A IA demora mais que o normal**: o cartão continua em "verificando…" até a análise terminar ou falhar; a página
  não trava.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Toda vaga do Relatório sem nota (triagem pendente ou Fora dos critérios) MUST mostrar o botão Forçar
  verificar embaixo dos botões de decisão; vaga com nota MUST NOT mostrar.
- **FR-002**: O clique MUST mandar só aquela vaga para a análise com IA, na mesma fila da análise automática, e MUST
  marcar a vaga como "verificando" até a análise terminar.
- **FR-003**: Enquanto a vaga verifica, o cartão MUST mostrar "verificando…" com o botão desligado e MUST atualizar
  sozinho quando a nota chegar ou a análise falhar.
- **FR-004**: Uma falha da IA ou uma vaga não devolvida MUST voltar o cartão ao botão, com o aviso do erro; a pessoa
  MUST poder tentar de novo sem reiniciar nada.
- **FR-005**: Para vaga com descrição pendente de um portal que lê descrições, a ferramenta MUST tentar ler a descrição
  daquela vaga com um pedido só, fora da espera do portal; na espera, MUST NOT fazer pedido.
- **FR-006**: Sem descrição (na espera, na falha da leitura ou em vaga que não tem de onde ler), a nota MUST sair com
  título, empresa, local e o que mais a vaga tiver, e a vaga MUST ficar marcada "nota sem a descrição", visível no
  cartão e no detalhe.
- **FR-007**: Quando a descrição de uma vaga com "nota sem a descrição" for lida depois, a vaga MUST voltar a aguardar
  a nota e receber a nota nova; a marca MUST sair.
- **FR-008**: Um bloqueio do portal durante a leitura MUST seguir a regra de sempre (o portal entra na espera, sem
  nova tentativa) e MUST NOT impedir a nota sem a descrição.
- **FR-009**: Sem IA ligada, o botão MUST mostrar o aviso com o atalho para a configuração da IA e MUST NOT gravar
  nada.
- **FR-010**: O pedido MUST seguir as regras de escrita da página e só ser aceito deste computador, como o "Tentar
  a nota de novo"; MUST NOT duplicar a vaga na fila.
- **FR-011**: A nota de uma vaga forçada MUST seguir as regras da nota automática: MUST NOT mudar uma decisão da
  pessoa (Seguir, Não seguir) nem tirar a vaga de Fora dos critérios; uma vaga ainda na triagem que fura os filtros
  pela análise vai para Fora dos critérios com o motivo.
- **FR-012**: O README do dashboard e a skill buscar-vagas MUST explicar o botão e a marca "nota sem a descrição".

### Key Entities

- **Vaga verificando**: vaga cuja nota foi pedida pela pessoa e ainda não voltou da IA.
- **Nota sem a descrição**: nota dada só com título, empresa, local e o que a vaga tiver, refeita quando o texto
  chega.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com uma IA ligada, 100% das vagas sem nota forçadas pela pessoa saem de "sem nota": ganham a nota ou
  mostram o erro.
- **SC-002**: Forçar uma vaga manda exatamente 1 vaga para a IA, e no máximo 1 pedido ao portal (a descrição), nunca
  na espera.
- **SC-003**: A pessoa vê a nota no cartão sem recarregar a página, em até 1 minuto depois de a IA terminar.
- **SC-004**: Nenhuma decisão da pessoa (Seguir, Não seguir) muda por causa do Forçar verificar.
- **SC-005**: Sem IA, nenhum clique grava nada.

## Assumptions

- A análise usa a IA e o perfil que a pessoa já configurou (sem escolha de provedor no botão).
- "Alguns minutos" é o tempo da própria IA (cerca de 1 minuto por vaga hoje; até 10 minutos no pior caso).
- Portais que leem descrição: os que têm a leitura de descrição hoje (LinkedIn, Nerdin, startup.jobs); os outros vão
  direto para a nota com o que têm.
- O estado "verificando" vale enquanto o servidor estiver aberto; se o servidor fechar no meio, a vaga volta a
  "aguardando análise" e a fila automática a retoma ao abrir.
- A nota sem a descrição usa as mesmas regras da nota normal; a marca é só para a pessoa saber que é provisória.
- Verificação só no Windows, como nas specs anteriores.
