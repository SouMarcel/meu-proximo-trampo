# Feature Specification: Forçar verificar em fila, uma vaga por vez

**Feature Branch**: `056-forcar-sequencial` (worktree saída da `master`)

**Created**: 2026-11-24

**Status**: Draft

**Input**: "Forçar verificar sequencial, assim não gasta muitos acessos de uma única vez."

Decisões da pessoa:

- as duas etapas passam a ir uma vaga por vez: a leitura da descrição no portal e o pedido à IA;
- a pausa entre dois pedidos à IA é ajustável no `.env`, com padrão de 5 s.

## Contexto

O botão Forçar verificar (spec 021) pede a nota de uma vaga na hora. Hoje, quando a pessoa clica em várias vagas
seguidas, a ferramenta junta todas numa rodada só e:

- lê nos portais, uma atrás da outra e **sem pausa**, as descrições que faltam. A leitura do Forçar verificar não
  segue a pausa de cada portal que a busca respeita (`<PORTAL>_PAUSA`);
- manda as vagas **juntas** para a IA, até 10 por pedido. É um pedido grande, que esbarra no limite por minuto dos
  planos gratuitos. Quando ele falha, falham todas as vagas da rodada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Uma vaga por vez, na ordem dos cliques (Priority: P1)

A pessoa clica em Forçar verificar em cinco vagas. Elas entram numa fila, na ordem dos cliques. A ferramenta trata
uma por vez:

1. lê a descrição no portal, se faltar;
2. pede a nota à IA, só daquela vaga;
3. grava;
4. passa para a próxima.

Entre duas leituras no mesmo portal, ela respeita a pausa do portal. Entre dois pedidos à IA, a pausa da IA.

**Why this priority**: é o pedido. Espaçar os acessos protege a conta da pessoa nos portais (menos risco de bloqueio)
e a cota da IA gratuita. Uma vaga com problema também deixa de derrubar as outras.

**Independent Test**: com uma IA falsa que registra a hora de cada pedido, forçar três vagas e ver três pedidos, um
por vaga, na ordem dos cliques e espaçados pela pausa.

**Acceptance Scenarios**:

1. **Given** três vagas forçadas em sequência, **When** a fila roda, **Then** a IA recebe três pedidos, cada um com
   uma vaga só, na ordem em que foram forçadas.
2. **Given** duas vagas do mesmo portal sem descrição, **When** a fila roda, **Then** a segunda leitura começa só
   depois da pausa daquele portal (`<PORTAL>_PAUSA`, ou o padrão do portal).
3. **Given** duas vagas de portais diferentes sem descrição, **When** a fila roda, **Then** a pausa de leitura de um
   portal não atrasa a leitura do outro. A pausa da IA continua valendo entre os pedidos.
4. **Given** a IA falha numa vaga, **When** a fila segue, **Then** só aquela vaga fica com o motivo da falha, e as
   próximas são verificadas normalmente.
5. **Given** a pessoa força uma vaga que já está na fila, **When** clica de novo, **Then** a vaga não é duplicada e
   mantém a posição.
6. **Given** vagas forçadas e vagas esperando a análise automática, **When** a fila roda, **Then** as forçadas vão
   antes, uma por vez. A análise automática continua como hoje, em lotes.

---

### User Story 2 - Ver quem está na fila (Priority: P1)

No cartão e no detalhe da vaga:

- a vaga que está sendo verificada agora mostra "Verificando…", como hoje;
- as que esperam a vez mostram "Na fila (posição N)".

Quando a vaga ganha a nota ou falha, a marca some, como hoje.

**Why this priority**: com a fila, a verificação de várias vagas demora mais, e a pessoa precisa ver que a vaga está
esperando a vez e não travada.

**Independent Test**: forçar três vagas e ver, enquanto a primeira é verificada, as outras duas com "Na fila
(posição 1)" e "Na fila (posição 2)".

**Acceptance Scenarios**:

1. **Given** três vagas forçadas, **When** a primeira está sendo verificada, **Then** ela mostra "Verificando…" e as
   outras mostram a posição na fila.
2. **Given** a primeira terminou, **When** a página se atualiza, **Then** as posições andam.

---

### User Story 3 - Ajustar a pausa da IA (Priority: P2)

A pausa entre dois pedidos do Forçar verificar à IA fica no `.env`: `FORCAR_PAUSA`, de 0 a 60 s, com padrão de 5 s.
Fora da faixa, vale o limite mais próximo. Valor inválido é ignorado e vale o padrão. O `.env.exemplo` mostra a
variável, como as pausas dos portais.

**Why this priority**: o limite de cada plano de IA é diferente. Quem usa uma IA paga pode zerar a pausa.

**Acceptance Scenarios**:

1. **Given** `FORCAR_PAUSA=0`, **When** a fila roda, **Then** a próxima vaga começa assim que a anterior termina.
2. **Given** `FORCAR_PAUSA=90`, **When** a fila roda, **Then** a pausa é de 60 s.
3. **Given** `FORCAR_PAUSA=abc` ou sem a variável, **When** a fila roda, **Then** a pausa é de 5 s.

---

### Edge Cases

- **Portal em espera depois de um bloqueio**: a leitura não acontece, como hoje. A vaga vai à IA sem a descrição, com
  a marca de nota provisória (spec 021).
- **Uma busca começa no meio da fila**: a leitura da descrição dá lugar à busca, como hoje. A fila segue sem a
  descrição daquela vaga, com nota provisória.
- **A vaga ganhou nota enquanto esperava a vez** (pela análise automática): ela sai da fila sem pedido à IA.
- **A vaga foi removida enquanto esperava**: sai da fila.
- **Portal sem pausa própria** (lido por API, como a Gupy): vale uma pausa mínima de 3 s entre leituras do mesmo
  portal.
- **O servidor é reiniciado com vagas na fila**: a fila se perde, como hoje. A vaga volta a mostrar o botão.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As vagas forçadas MUST formar uma fila, na ordem em que foram pedidas, sem repetição.
- **FR-002**: A fila MUST tratar uma vaga por vez: leitura da descrição que falta, pedido à IA só com ela e gravação,
  antes de começar a próxima.
- **FR-003**: Entre duas leituras no mesmo portal, a fila MUST esperar a pausa daquele portal: a de `<PORTAL>_PAUSA`,
  ou o padrão do portal, com no mínimo 3 s.
- **FR-004**: Entre dois pedidos da fila à IA, MUST haver a pausa `FORCAR_PAUSA` (0 a 60 s, padrão 5 s).
- **FR-005**: A falha de uma vaga (leitura ou IA) MUST afetar só ela, com o motivo, como hoje.
- **FR-006**: A página MUST receber, além das vagas em verificação, qual delas está sendo verificada agora. O cartão e
  o detalhe mostram "Verificando…" para essa e "Na fila (posição N)" para as outras.
- **FR-007**: As vagas forçadas MUST ir antes da análise automática, que continua em lotes.
- **FR-008**: `FORCAR_PAUSA` MUST constar no `.env.exemplo` e na documentação, junto das pausas dos portais.

### Key Entities

- **Fila de verificação**: lista ordenada de vagas forçadas, com a vaga atual.
- **Pausa da IA (`FORCAR_PAUSA`)**: segundos entre dois pedidos da fila à IA.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Forçar N vagas gera exatamente N pedidos à IA, cada um com uma vaga.
- **SC-002**: Nenhuma leitura no mesmo portal acontece antes da pausa daquele portal.
- **SC-003**: Uma falha da IA numa vaga não deixa nenhuma outra vaga da fila sem nota.
- **SC-004**: Em toda vaga forçada, a pessoa vê "Verificando…" ou a posição na fila até ela terminar.

## Assumptions

- A fila vive na memória do servidor, como hoje. Ela não é gravada.
- A pausa da IA vale só para o Forçar verificar. A análise automática depois da busca continua em lotes, com um pedido
  por lote.
- A pausa dos portais usa a mesma configuração da busca (`<PORTAL>_PAUSA` e o padrão de cada portal), sem variável
  nova por portal.
- Os testes usam vagas fictícias e uma IA falsa (princípio II).
