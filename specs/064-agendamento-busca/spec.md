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
que a ferramenta continue sozinha depois da espera, num ritmo (a cada 6 horas) que não insista com o portal.

## Clarifications

### Session 2026-11-27

- Q: Se a pessoa já buscou à mão pouco antes do horário, a busca agendada roda mesmo assim? → A: Não; a busca agendada
  do dia é pulada se houve uma busca manual nas 4 horas antes do horário, com aviso na página.
- Q: Se o dashboard só liga depois do horário, no mesmo dia, a busca agendada daquele dia roda? → A: Não; perdeu o
  horário, o dia fica sem busca agendada, e a próxima é a do dia seguinte.
- Q: Com espera de 24 h, InfoJobs, Vagas.com, JobGether e FullStack nunca seriam retomados no mesmo dia; o que fazer?
  → A: (revista na pergunta seguinte sobre o `.env`) A espera de cada portal passa a ser ajustável, com padrão de 6
  horas para todos, e esses portais entram na retomada como os outros.
- Q: Como contar o limite de 2 retomadas quando a espera passa da meia-noite? → A: Não há mais limite de 2: a retomada
  roda a cada 6 horas enquanto aquele portal não terminar com sucesso (todas as páginas e descrições lidas, sem
  bloqueio) e para quando terminar ou quando chegar a próxima busca agendada, que assume o lugar dela.
- Q: Se o dashboard estava desligado na hora da retomada, ela roda ao ligar? → A: Não, igual à busca agendada: a
  tentativa perdida não roda; a próxima é 6 horas depois da hora perdida (ou a próxima busca agendada).
- Q: Onde fica a espera de cada portal depois de um bloqueio? → A: No `.env`, uma variável por portal
  (`<PORTAL>_ESPERA`, em minutos, de 60 a 2880), com padrão de 360 minutos (6 h) para todos os portais que têm espera
  (LinkedIn, InfoJobs, Vagas.com, JobGether, FullStack e MyGreenhouse). A retomada segue a cada 6 horas fixas; se a
  espera do portal ainda não acabou nessa hora, a tentativa é pulada e a próxima fica para 6 horas depois.

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
2. **Given** o computador desligado às 08:00, **When** o dashboard liga às 10:00 do mesmo dia, **Then** a busca
   agendada daquele dia não roda; a página mostra a próxima (amanhã às 08:00).
3. **Given** a pessoa já buscou à mão às 07:30, **When** chega 08:00, **Then** a busca agendada do dia não roda e a
   página mostra "Busca agendada pulada: busca manual às 07:30"; se a busca manual foi às 03:00 (mais de 4 horas
   antes), a agendada roda.
4. **Given** uma busca rodando (à mão) às 08:00, **When** chega o horário, **Then** a agendada espera essa terminar e
   não roda duas ao mesmo tempo.
5. **Given** o agendamento desligado, **When** chega o horário, **Then** nada acontece.

---

### User Story 2 - Continuar de onde parou depois da espera (Priority: P1)

Com "Continuar de onde parou" marcado, quando um portal bloqueia no meio da busca (agendada ou manual), a ferramenta
guarda o que faltou daquele portal (as páginas de resultado não lidas e as descrições pendentes). Quando a espera
acaba, ela retoma só isso, com as pausas de sempre, e as vagas que ganharem descrição recebem a nota da análise
automática. Se o portal bloquear de novo na retomada, ela tenta de novo 6 horas depois, e assim por diante, até o
portal terminar com sucesso ou até a próxima busca agendada, que assume o lugar dela.

**Why this priority**: é o que tira da pessoa o trabalho de voltar depois de 6 horas; sem isso, a busca agendada perde
metade do valor nos dias de bloqueio.

**Independent Test**: com um portal falso que bloqueia na 3ª leitura, a busca para nele; depois da espera (relógio
falso), a retomada lê o que faltou, e as vagas ganham descrição e nota.

**Acceptance Scenarios**:

1. **Given** o LinkedIn bloqueou com 18 descrições pendentes e "Continuar de onde parou" marcado, **When** a espera de
   6 horas acaba, **Then** a ferramenta lê essas descrições (com a pausa do LinkedIn) e a análise dá as notas.
2. **Given** o bloqueio veio antes de ler todas as páginas de resultado do LinkedIn, **When** a espera acaba, **Then**
   a retomada lê as páginas que faltaram, além das descrições.
3. **Given** um novo bloqueio na retomada, **When** ele acontece, **Then** a ferramenta marca a próxima retomada para
   6 horas depois e a página mostra "LinkedIn bloqueou de novo; nova tentativa às HH:MM".
4. **Given** a retomada leu todas as páginas e descrições que faltavam sem bloqueio, **When** ela termina, **Then** não
   há nova retomada daquele portal até o próximo bloqueio.
5. **Given** a caixa desmarcada, **When** um portal bloqueia, **Then** o comportamento é o de hoje (espera e nada de
   retomada sozinha).
6. **Given** a busca agendada do dia seguinte chegando enquanto ainda há retomada pendente, **When** chega o horário,
   **Then** a busca do dia substitui a retomada (ela já inclui o portal, se a espera tiver acabado) e as retomadas
   seguintes passam a ser as dessa busca.

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

- Dashboard desligado no horário (o dia todo ou só naquela hora): a busca daquele dia não roda; no dia seguinte, a do
  novo dia.
- Dashboard desligado na hora da retomada: aquela tentativa não roda (mesma tolerância de 15 minutos da busca agendada);
  a próxima fica para 6 horas depois da hora perdida, se a próxima busca agendada ainda não tiver rodado.
- Busca manual com retomada pendente: se a busca manual incluir o portal (espera já acabada), ela assume o lugar da
  retomada, como a busca agendada.
- Portais com login (MyGreenhouse, spec 041): ficam de fora da busca agendada e da retomada, como na busca pelo
  terminal (rodam só no botão Buscar), com aviso.
- Espera de cada portal ajustável no `.env` (FR-012): se a pessoa puser uma espera maior que 6 horas, a retomada que
  cair antes do fim da espera é pulada e a próxima fica para 6 horas depois; valor fora da faixa (60 a 2880 minutos)
  vira o limite mais próximo, como nas pausas.
- Busca sem IA ligada: a busca agendada grava as vagas sem nota, como a manual.
- A pessoa muda o horário depois que a busca do dia já rodou: a nova hora vale a partir do dia seguinte.
- Fuso e horário de verão: o horário é o do computador.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Os filtros da busca MUST ganhar a aba "Agendamento" com: ligar/desligar, horário (hora e minuto, uma vez
  por dia) e a caixa "Continuar de onde parou", desligados por padrão.
- **FR-002**: Com o agendamento ligado e o dashboard ligado, a ferramenta MUST rodar uma busca por dia no horário, com
  os filtros salvos, como a busca da página (análise automática incluída), e no máximo uma busca agendada por dia.
- **FR-002a**: A busca agendada do dia MUST ser pulada se houve uma busca manual (página, chat ou terminal) nas 4 horas
  antes do horário; a página e o resultado da última execução MUST mostrar que ela foi pulada e por quê.
- **FR-003**: A busca agendada MUST rodar só se o dashboard estiver ligado no horário (tolerância de 15 minutos, para o
  computador que sai do modo de espera); se o dashboard ligar depois disso, a busca agendada daquele dia MUST NOT rodar,
  e a próxima é a do dia seguinte.
- **FR-004**: A busca agendada MUST NOT rodar ao mesmo tempo que outra busca; ela espera a que estiver rodando.
- **FR-005**: A busca agendada MUST deixar de fora os portais com login, com aviso, e MUST respeitar as esperas em
  andamento: o portal em espera fica de fora daquela busca sem perguntar (a escolha da pessoa já está no agendamento).
- **FR-006**: Com "Continuar de onde parou" marcado, quando um portal bloqueia durante uma busca (agendada ou manual),
  a ferramenta MUST guardar o que faltou daquele portal (páginas de resultado e descrições pendentes) e retomá-lo
  quando a espera acabar, com as pausas e as regras do portal (constituição VI).
- **FR-007**: Se o portal bloquear de novo na retomada, a ferramenta MUST marcar outra retomada para 6 horas depois, e
  repetir enquanto o portal não terminar com sucesso (se a espera do portal, ajustável no FR-012, ainda não tiver
  acabado na hora da tentativa, ela é pulada e a próxima fica para 6 horas depois) (todas as páginas e descrições que faltavam lidas, sem bloqueio).
  As retomadas MUST parar quando o portal terminar com sucesso ou quando a próxima busca agendada rodar (ela assume o
  lugar delas); nunca mais de uma retomada do mesmo portal ao mesmo tempo. Uma retomada perdida porque o dashboard
  estava desligado MUST NOT rodar ao ligar (tolerância de 15 minutos, como no FR-003); a próxima tentativa é 6 horas
  depois da hora perdida.
- **FR-008**: As vagas que ganharem descrição na retomada MUST entrar na análise automática (spec 062).
- **FR-009**: A página MUST mostrar a próxima busca agendada, a retomada esperando (portal e hora, com cancelar) e o
  resultado da última busca agendada e das retomadas.
- **FR-010**: O agendamento MUST ficar no `config.json` (sem dados pessoais além do horário) e valer também para quem
  usa a ferramenta pelo terminal, que pode ver e mudar o agendamento por comando.
- **FR-011**: A documentação (README, AGENTS.md, `dash/API.md` e `.env.exemplo`) MUST descrever o agendamento, a
  retomada a cada 6 horas até terminar com sucesso e as variáveis `<PORTAL>_ESPERA`.
- **FR-012**: A espera depois de um bloqueio MUST ser ajustável no `.env`, uma variável por portal que tem espera:
  `LINKEDIN_ESPERA`, `INFOJOBS_ESPERA`, `VAGASCOM_ESPERA`, `JOBGETHER_ESPERA`, `FULLSTACK_ESPERA` e
  `MYGREENHOUSE_ESPERA`, em minutos, de 60 a 2880, com padrão de 360 (6 horas) para todos (antes: 6 h no LinkedIn e
  24 h nos outros). Valor fora da faixa vira o limite mais próximo; valor inválido ou ausente usa o padrão. A busca
  manual, a agendada e a retomada respeitam a mesma espera.

### Key Entities

- **Agendamento**: ligado, horário, "continuar de onde parou"; parte da configuração da busca.
- **Retomada**: portal, busca de origem, hora da próxima tentativa, o que faltou (páginas e descrições), tentativas
  feitas.
- **Execução agendada**: data, horário real, origem (agendada, ao ligar, retomada), resultado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o dashboard ligado, a busca agendada roda em até 2 minutos depois do horário em 100% dos dias
  testados.
- **SC-002**: Depois de um bloqueio com "Continuar de onde parou", pelo menos 90% das descrições pendentes daquele
  portal são lidas e ganham nota no mesmo dia, sem a pessoa clicar (quando o portal não bloqueia de novo).
- **SC-003**: Nunca duas buscas (ou retomadas) ao mesmo tempo, nunca uma retomada antes de 6 horas da anterior do
  mesmo portal, e nenhuma retomada depois que o portal terminou com sucesso ou que a próxima busca agendada rodou.
- **SC-004**: A pessoa sabe, pela página, quando é a próxima busca e o que aconteceu na última, sem abrir o terminal.

## Assumptions

- A busca agendada só roda com o servidor do dashboard ligado (a ferramenta é local); não há serviço do sistema
  operacional (Agendador de Tarefas do Windows) nesta spec.
- A busca manual usa os mesmos filtros salvos que a agendada; por isso, uma busca manual nas 4 horas antes do horário
  substitui a agendada do dia (clarify de 27/11).
- "Continuar de onde parou" vale para qualquer portal que entra em espera, mas o caso que motivou a spec é o LinkedIn
  (espera de 6 horas).
- A retomada não pergunta antes de seguir (o `--confirmar-espera` da busca pelo terminal): marcar a caixa é a
  confirmação da pessoa.
- Depende do Forçar/análise da spec 062 para dar a nota às vagas retomadas; a 062 vai à `master` antes desta.
- A página é o React da branch `frontend-react` (a aba nova e os avisos); o back e o contrato em `dash/API.md` vêm
  primeiro.
