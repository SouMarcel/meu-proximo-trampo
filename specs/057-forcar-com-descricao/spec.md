# Feature Specification: Forçar verificar só com a descrição no computador

**Feature Branch**: `057-forcar-com-descricao` (a partir da `056-forcar-sequencial`)

**Created**: 2026-11-24

**Status**: Draft

**Input**: No teste da spec 056, várias vagas forçadas falharam ("a IA não conseguiu dar nota sem a descrição",
"esperava texto", "a resposta da IA não trouxe o JSON", "nenhuma IA respondeu", "senioridade deve ser uma lista").
Todas estavam sem a descrição no computador. A pessoa pediu:

- o Forçar verificar garante que a descrição esteja no computador antes de pedir a nota;
- uma coisa de cada vez: se uma busca estiver rodando, a vaga espera na fila;
- no LinkedIn, mais tempo entre uma verificação e a próxima;
- conferir de novo se o JobGether entrega a descrição;
- nova tentativa da IA, leitura tolerante da resposta e um campo para colar a descrição.

## Contexto

- **LinkedIn:** o portal respondeu "excesso de pedidos" (HTTP 429) a um Forçar verificar. A regra da ferramenta
  (constituição VI) deixa o LinkedIn 6 h sem pedidos depois disso. Durante essa espera, o Forçar verificar mandava a
  vaga à IA sem a descrição.
- **JobGether:** a API oficial para assistentes só tem a busca, sem a descrição e sem consulta de uma vaga só. Isso
  foi conferido em 24/11 no `llms.txt`, na referência da API, em `/developers` e no OpenAPI. A página da vaga não é
  lida (spec 030), e a pessoa manteve essa decisão. Os outros campos da API (funções, experiência, contrato) ajudam a
  dar a nota.
- **IA:** provedores fora do ar e respostas fora do formato derrubavam a nota. Um campo secundário fora do padrão
  recusava a análise inteira.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A nota só sai com a descrição (Priority: P1)

Quando a pessoa força uma vaga sem descrição, a fila lê a descrição antes de pedir a nota:

- **leu:** segue para a IA;
- **uma busca está rodando:** a vaga fica "Aguardando a busca terminar" e volta sozinha para a fila no fim da busca;
- **o portal está em espera depois de um bloqueio:** a vaga fica "Aguardando o LinkedIn (até 04:07)" e volta
  sozinha quando a espera acaba;
- **o portal não entrega a descrição** (JobGether): veja a US4;
- **a leitura falhou** ou o anúncio saiu do portal: a vaga mostra o motivo e não gasta a IA.

**Independent Test**: com uma fonte falsa em espera, forçar uma vaga sem descrição e ver "aguardando", com zero
pedidos à IA. Ao fim da espera, ver a vaga voltar à fila e ganhar nota.

**Acceptance Scenarios**:

1. **Given** uma busca rodando, **When** a pessoa força uma vaga sem descrição, **Then** ela fica aguardando a busca,
   sem pedido ao portal nem à IA, e é verificada quando a busca termina.
2. **Given** o LinkedIn em espera até 04:07, **When** a pessoa força uma vaga do LinkedIn sem descrição, **Then** ela
   mostra "Aguardando o LinkedIn (até 04:07)" e é verificada depois disso, sem novo clique.
3. **Given** a leitura deu erro, **When** a fila trata a vaga, **Then** a vaga mostra "não deu para ler a descrição no
   {portal}", sem pedido à IA.
4. **Given** uma vaga aguardando, **When** a pessoa clica de novo, **Then** ela volta para o fim da fila.

### User Story 2 - Mais tempo entre as leituras do LinkedIn (Priority: P1)

Entre duas leituras de descrição do LinkedIn pelo Forçar verificar, a fila espera `LINKEDIN_FORCAR_PAUSA` segundos:
de 30 a 600, com padrão de 60. Os outros portais seguem a pausa da spec 056.

**Acceptance Scenarios**:

1. **Given** duas vagas do LinkedIn sem descrição, **When** a fila roda, **Then** a segunda leitura começa 60 s
   depois da primeira.
2. **Given** `LINKEDIN_FORCAR_PAUSA=10`, **When** a fila roda, **Then** vale 30 s. Com 900, vale 600. Com um valor
   inválido, vale 60.

### User Story 3 - A IA não perde a nota por pouco (Priority: P1)

- Se a IA responde sem o JSON, ou se nenhum provedor responde (erro 503, resposta vazia), a fila tenta mais uma vez,
  depois da pausa da IA, antes de marcar a falha.
- Na resposta, um campo secundário fora do padrão é descartado ou convertido, sem perder a nota:
  - uma senioridade ou um tipo de emprego desconhecido é descartado;
  - um resumo em lista vira texto.

**Acceptance Scenarios**:

1. **Given** a IA falha na primeira tentativa e responde na segunda, **When** a fila trata a vaga, **Then** a vaga
   ganha a nota.
2. **Given** a IA devolve senioridade `["senior", "especialista"]`, **When** a análise é gravada, **Then** fica
   `["senior"]`, com a nota.
3. **Given** a IA não devolve a aderência, **When** a análise é lida, **Then** continua sendo erro.

### User Story 4 - JobGether: nota pelos dados do portal e colar a descrição (Priority: P1)

- A busca passa a guardar as funções, a experiência pedida e o contrato que a API do JobGether entrega. Esses dados
  vão no pedido à IA de toda vaga que os tem.
- Forçar uma vaga do JobGether sem descrição dá uma nota **provisória pelos dados do portal**, marcada como tal.
- Uma vaga sem esses dados (gravada antes, ainda não revista por uma busca) mostra "O JobGether não entrega a
  descrição à ferramenta: abra o anúncio e cole o texto em Colar a descrição".
- No detalhe de qualquer vaga sem descrição, a seção **Colar a descrição** grava o texto e põe a vaga na fila de nota.
- A vaga do JobGether já gravada ganha os dados do portal na próxima busca que a trouxer.

**Acceptance Scenarios**:

1. **Given** uma vaga do JobGether com funções e experiência, sem descrição, **When** a pessoa força, **Then** a IA
   recebe os dados do portal, e a nota sai provisória.
2. **Given** a pessoa cola a descrição numa vaga sem nota, **When** grava, **Then** a vaga vai para a fila e ganha a
   nota completa.
3. **Given** um texto colado com menos de 50 caracteres, **When** a pessoa grava, **Then** aparece o erro, e nada
   muda.

### Edge Cases

- **O servidor é reiniciado com vagas aguardando:** a fila se perde, como na 056, e o botão volta.
- **O texto colado traz instruções para a IA:** o filtro de integridade (spec 034) vale como para qualquer descrição.
- **A vaga ganha nota enquanto aguarda** (análise automática): ela sai da espera sem novo pedido.

## Requirements *(mandatory)*

- **FR-001**: O Forçar verificar MUST NOT pedir nota sem a descrição, exceto pelos dados do portal (FR-009).
- **FR-002**: Com uma busca rodando, ou com o portal em espera, a vaga MUST ficar aguardando e voltar sozinha para a
  fila.
- **FR-003**: `LINKEDIN_FORCAR_PAUSA` (30 a 600 s, padrão 60) MUST valer entre duas leituras do LinkedIn pela fila.
- **FR-004**: Uma falha da IA (sem JSON, provedor fora) MUST ter uma nova tentativa antes de virar falha.
- **FR-005**: A leitura da análise MUST tolerar campos secundários fora do padrão, descartando ou convertendo, e
  MUST manter estritas a aderência e a situação.
- **FR-006**: A página MUST mostrar a vaga aguardando, com o motivo e o horário.
- **FR-007**: O detalhe da vaga sem descrição MUST ter a seção "Colar a descrição" (50 a 30.000 caracteres), que
  grava o texto e põe a vaga na fila.
- **FR-008**: A busca MUST guardar as funções, a experiência e o contrato do JobGether, e completar esses dados nas
  vagas já gravadas que voltarem numa busca.
- **FR-009**: A vaga sem descrição com dados do portal MUST poder ter uma nota provisória pelos dados do portal.
  Sem esses dados, a vaga MUST mostrar como colar a descrição.

## Success Criteria *(mandatory)*

- **SC-001**: Nenhum pedido do Forçar verificar à IA sai sem descrição e sem dados do portal.
- **SC-002**: As vagas que aguardam voltam sozinhas e ganham nota, sem novo clique.
- **SC-003**: A falha momentânea de um provedor de IA não deixa uma vaga sem nota quando a nova tentativa funciona.

## Assumptions

- As 6 h de espera do LinkedIn depois de um 429 continuam, sem mudar a constituição.
- O JobGether continua só pela API (spec 030). Pedir à empresa uma API com a descrição é decisão e iniciativa da
  pessoa.
- Os testes usam vagas fictícias e uma IA falsa (princípio II).
