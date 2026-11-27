# Feature Specification: Busca agendada e retomada depois da espera

**Feature Branch**: `064-agendamento-busca` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Quero ambas: auto busca 1x ao dia e, após o tempo de suspensão, a continuação caso não
tenha terminado. Criar uma aba em Buscar vagas com o agendamento, apenas 1x ao dia, a pessoa escolhe a hora, e a
checkbox com auto continuar de onde parou. Se bloquear de novo na retomada: no máximo 2 retomadas por dia."

## Contexto

Hoje a busca só roda quando a pessoa clica em Buscar (ou pede no chat/terminal). Quando um portal bloqueia (no
LinkedIn, o erro 429 de excesso de pedidos), a busca segue sem ele, e ele fica 6 horas em espera (constituição VI). O
que faltou (as páginas de resultado não lidas e as descrições das vagas que ficaram "descrição pendente") só volta se a
pessoa lembrar de buscar de novo ou clicar em "Completar descrições" depois da espera. Na busca de 26/11, 18 vagas do
LinkedIn ficaram sem descrição e, por isso, sem nota.

A pessoa quer: uma busca por dia, no horário que ela escolher, sem precisar clicar; e, quando um bloqueio interromper,
que a ferramenta continue sozinha depois da espera, com um limite para não insistir com o portal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Busca diária no horário escolhido (Priority: P1)

Nos filtros da busca, uma aba nova "Agendamento" tem: ligar a busca agendada, o horário (uma vez por dia) e a caixa
"Continuar de onde parou". A pessoa escolhe 08:00 e salva. No dia seguinte, às 08:00, com o dashboard ligado, a busca
roda com os filtros salvos, como se ela tivesse clicado em Buscar, e a análise automática dá as notas.

**Why this priority**: é o pedido principal: as vagas novas chegam todo dia sem depender de lembrar de buscar.

**Independent Test**: agendar para daqui a 2 minutos e ver a busca começar sozinha; a página mostra "Busca agendada"
como origem e o resultado.

**Acceptance Scenarios**:

1. **Given** o agendamento ligado para 08:00 e o dashboard ligado, **When** chega 08:00, **Then** a busca roda uma vez
   com os filtros salvos e aparece no relatório como "agendada".
2. **Given** o computador desligado às 08:00, **When** o dashboard liga às 10:00 do mesmo dia, **Then** a busca do dia
   roda ao ligar (uma vez), com aviso de que foi fora do horário.
3. **Given** a pessoa já buscou à mão às 07:30, **When** chega 08:00, **Then** a busca agendada roda mesmo assim (a
   ferramenta não sabe se os filtros mudaram) [ver Assumptions].
4. **Given** uma busca rodando (à mão) às 08:00, **When** chega o horário, **Then** a agendada espera essa terminar e
   não roda duas ao mesmo tempo.
5. **Given** o agendamento desligado, **When** chega o horário, **Then** nada acontece.

---

### User Story 2 - Continuar de onde parou depois da espera (Priority: P1)

Com "Continuar de onde parou" marcado, quando um portal bloqueia no meio da busca (agendada ou manual), a ferramenta
guarda o que faltou daquele portal (as páginas de resultado não lidas e as descrições pendentes). Quando a espera
acaba, ela retoma só isso, com as pausas de sempre, e as vagas que ganharem descrição recebem a nota da análise
automática. Se o portal bloquear de novo na retomada, ela espera outra vez e tenta mais uma; na terceira, para e mostra
o aviso até a pessoa pedir.

**Why this priority**: é o que tira da pessoa o trabalho de voltar depois de 6 horas; sem isso, a busca agendada perde
metade do valor nos dias de bloqueio.

**Independent Test**: com um portal falso que bloqueia na 3ª leitura, a busca para nele; depois da espera (relógio
falso), a retomada lê o que faltou, e as vagas ganham descrição e nota.

**Acceptance Scenarios**:

1. **Given** o LinkedIn bloqueou com 18 descrições pendentes e "Continuar de onde parou" marcado, **When** a espera de
   6 horas acaba, **Then** a ferramenta lê essas descrições (com a pausa do LinkedIn) e a análise dá as notas.
2. **Given** o bloqueio veio antes de ler todas as páginas de resultado do LinkedIn, **When** a espera acaba, **Then**
   a retomada lê as páginas que faltaram, além das descrições.
3. **Given** um novo bloqueio na retomada, **When** ele acontece, **Then** a ferramenta espera de novo e faz no máximo
   mais uma retomada naquele dia; na terceira vez, para e a página mostra "LinkedIn bloqueou de novo; retome quando
   quiser".
4. **Given** a caixa desmarcada, **When** um portal bloqueia, **Then** o comportamento é o de hoje (espera e nada de
   retomada sozinha).
5. **Given** a busca agendada do dia seguinte chegando enquanto ainda há retomada pendente, **When** chega o horário,
   **Then** a busca do dia substitui a retomada (ela já inclui o portal, se a espera tiver acabado).

---

### User Story 3 - Ver o que está agendado e o que aconteceu (Priority: P2)

A página mostra quando é a próxima busca agendada, se há retomada esperando ("LinkedIn retoma às 02:52") e o resultado
da última (horário, vagas novas, portais que bloquearam, retomadas feitas).

**Why this priority**: sem isso, a pessoa não sabe se a busca rodou nem por que um portal ficou de fora.

**Independent Test**: depois de uma busca agendada com bloqueio, a página mostra a retomada marcada para o fim da
espera e, depois dela, o resultado.

**Acceptance Scenarios**:

1. **Given** o agendamento ligado, **When** a pessoa abre a página, **Then** vê a próxima busca agendada.
2. **Given** uma retomada esperando, **When** a pessoa abre a página, **Then** vê o portal e a hora da retomada, e pode
   cancelar.

### Edge Cases

- Dashboard desligado no horário e o dia todo: a busca daquele dia não roda; no dia seguinte, a do novo dia.
- Dashboard desligado no fim da espera: a retomada roda quando o dashboard ligar, se ainda for o mesmo dia e dentro do
  limite de 2.
- Portais com login (MyGreenhouse, spec 041): ficam de fora da busca agendada e da retomada, como na busca pelo
  terminal (rodam só no botão Buscar), com aviso.
- Portal com espera de 24 horas (InfoJobs, Vagas.com, JobGether, FullStack): a retomada só acontece se a espera acabar
  no mesmo dia; senão, a busca agendada do dia seguinte cobre.
- Busca sem IA ligada: a busca agendada grava as vagas sem nota, como a manual.
- A pessoa muda o horário depois que a busca do dia já rodou: a nova hora vale a partir do dia seguinte.
- Fuso e horário de verão: o horário é o do computador.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Os filtros da busca MUST ganhar a aba "Agendamento" com: ligar/desligar, horário (hora e minuto, uma vez
  por dia) e a caixa "Continuar de onde parou", desligados por padrão.
- **FR-002**: Com o agendamento ligado e o dashboard ligado, a ferramenta MUST rodar uma busca por dia no horário, com
  os filtros salvos, como a busca da página (análise automática incluída), e no máximo uma busca agendada por dia.
- **FR-003**: Se o dashboard ligar depois do horário, no mesmo dia, sem a busca agendada daquele dia ter rodado, a
  ferramenta MUST rodá-la ao ligar, uma vez.
- **FR-004**: A busca agendada MUST NOT rodar ao mesmo tempo que outra busca; ela espera a que estiver rodando.
- **FR-005**: A busca agendada MUST deixar de fora os portais com login, com aviso, e MUST respeitar as esperas em
  andamento: o portal em espera fica de fora daquela busca sem perguntar (a escolha da pessoa já está no agendamento).
- **FR-006**: Com "Continuar de onde parou" marcado, quando um portal bloqueia durante uma busca (agendada ou manual),
  a ferramenta MUST guardar o que faltou daquele portal (páginas de resultado e descrições pendentes) e retomá-lo
  quando a espera acabar, com as pausas e as regras do portal (constituição VI).
- **FR-007**: A ferramenta MUST fazer no máximo 2 retomadas por portal por dia; depois, MUST parar e mostrar o aviso
  até a pessoa pedir.
- **FR-008**: As vagas que ganharem descrição na retomada MUST entrar na análise automática (spec 062).
- **FR-009**: A página MUST mostrar a próxima busca agendada, a retomada esperando (portal e hora, com cancelar) e o
  resultado da última busca agendada e das retomadas.
- **FR-010**: O agendamento MUST ficar no `config.json` (sem dados pessoais além do horário) e valer também para quem
  usa a ferramenta pelo terminal, que pode ver e mudar o agendamento por comando.
- **FR-011**: A documentação (README, AGENTS.md, `dash/API.md`, `.env.exemplo` se mudar) MUST descrever o
  agendamento, a retomada e o limite de 2.

### Key Entities

- **Agendamento**: ligado, horário, "continuar de onde parou"; parte da configuração da busca.
- **Retomada**: portal, hora em que a espera acaba, o que faltou (páginas e descrições), tentativas no dia.
- **Execução agendada**: data, horário real, origem (agendada, ao ligar, retomada), resultado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o dashboard ligado, a busca agendada roda em até 2 minutos depois do horário em 100% dos dias
  testados.
- **SC-002**: Depois de um bloqueio com "Continuar de onde parou", pelo menos 90% das descrições pendentes daquele
  portal são lidas e ganham nota no mesmo dia, sem a pessoa clicar (quando o portal não bloqueia de novo).
- **SC-003**: Nunca mais de 2 retomadas por portal por dia, e nunca duas buscas ao mesmo tempo.
- **SC-004**: A pessoa sabe, pela página, quando é a próxima busca e o que aconteceu na última, sem abrir o terminal.

## Assumptions

- A busca agendada só roda com o servidor do dashboard ligado (a ferramenta é local); não há serviço do sistema
  operacional (Agendador de Tarefas do Windows) nesta spec.
- A busca agendada roda mesmo que a pessoa tenha buscado à mão antes no mesmo dia; ela custa os mesmos pedidos de uma
  busca manual. Se isso incomodar, o clarify pode mudar para "pula se já houve busca nas últimas N horas".
- "Continuar de onde parou" vale para qualquer portal que entra em espera, mas o caso que motivou a spec é o LinkedIn
  (espera de 6 horas).
- A retomada não pergunta antes de seguir (o `--confirmar-espera` da busca pelo terminal): marcar a caixa é a
  confirmação da pessoa.
- Depende do Forçar/análise da spec 062 para dar a nota às vagas retomadas; a 062 vai à `master` antes desta.
- A página é o React da branch `frontend-react` (a aba nova e os avisos); o back e o contrato em `dash/API.md` vêm
  primeiro.
