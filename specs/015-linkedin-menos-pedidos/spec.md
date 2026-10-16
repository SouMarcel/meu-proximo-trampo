# Feature Specification: LinkedIn com menos pedidos

**Feature Branch**: `015-linkedin-menos-pedidos` (o trabalho acontece numa worktree saída da `master`, conforme a
constituição)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "LinkedIn com menos pedidos: (1) uma consulta por grupo no LinkedIn juntando os cargos
numa expressão OR mantendo as aspas de cada termo, até 3 páginas; (2) máximo de 20 descrições do LinkedIn por busca,
primeiro as vagas que ficaram sem descrição (pendentes), depois as novas das mais recentes; as que passarem ficam com
descrição pendente e a IA espera a descrição antes de dar nota; (3) espera de 6 horas depois de um bloqueio, gravada
em .cache, sem nenhum pedido no período, com aviso do horário; aviso de bloqueio traz o motivo (429, 999 rede/VPN,
pedido de login); (4) aviso (sem bloquear) quando há mais de 5 cargos com LinkedIn ou Indeed ligados, no formulário e
no começo da busca. Depois de um bloqueio a busca seguinte começa do zero e completa as descrições pendentes, sem
retomar a busca interrompida. Limite é por IP: pessoas na mesma rede dividem a cota."

## Contexto

A busca pública do LinkedIn limita os pedidos por endereço de internet (IP), não por pessoa nem por instalação.
Quem está na mesma rede (casa, escritório, Wi-Fi compartilhado) divide a mesma cota. Hoje uma busca faz uma consulta
para cada cargo em cada grupo e, depois, abre uma página para cada vaga nova, só para ler a descrição. Com 7 cargos e
2 grupos, são 14 consultas e até ~140 leituras de descrição. O bloqueio chega rápido, às vezes já na primeira busca
do dia. Quando ele vem no meio da busca, as vagas já trazidas entram no relatório sem descrição, a IA dá nota a uma
vaga "(sem descrição)" e ninguém volta a buscar o texto dela.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Uma busca no LinkedIn faz poucos pedidos (Priority: P1)

A pessoa tem vários cargos configurados e o LinkedIn ligado. Ao buscar, o LinkedIn recebe uma consulta só por grupo
(remoto no país, cidade, cada país de fora…), com todos os cargos juntos, em vez de uma consulta para cada cargo. As
leituras de descrição do LinkedIn param em 20 por busca. Uma busca inteira fica em torno de duas dezenas de pedidos ao
LinkedIn, e não mais centenas.

**Why this priority**: é a causa do bloqueio; sem isso as outras partes só remediam.

**Independent Test**: com 7 cargos, 2 grupos e respostas do LinkedIn simuladas trazendo 60 vagas novas, rodar a busca
e contar os pedidos ao LinkedIn: no máximo 3 páginas por grupo e 20 descrições.

**Acceptance Scenarios**:

1. **Given** 7 cargos e o LinkedIn ligado com 2 grupos, **When** a pessoa busca, **Then** o LinkedIn recebe uma
   consulta por grupo com todos os cargos (até 3 páginas cada), e não 14 consultas.
2. **Given** cargos escritos entre aspas (expressão exata) e sem aspas, **When** a consulta combinada é montada,
   **Then** cada cargo mantém a forma como a pessoa escreveu, e os cargos são ligados por "OR".
3. **Given** a mesma busca, **When** as consultas terminam, **Then** as outras fontes (Indeed, Gupy, startup.jobs)
   continuam com uma consulta por cargo, como hoje.
4. **Given** uma vaga encontrada pela consulta combinada, **When** ela vai para o relatório, **Then** ela mostra os
   cargos da configuração que aparecem no título dela (ou, se nenhum aparecer, a consulta combinada inteira).
5. **Given** 60 vagas novas do LinkedIn, **When** chega a hora das descrições, **Then** só 20 são lidas, e as outras 40
   entram no relatório com título, empresa e local, marcadas como "descrição pendente".

---

### User Story 2 - Vaga sem descrição não fica esquecida (Priority: P1)

Uma vaga do LinkedIn entrou no relatório sem descrição, porque passou do limite de 20 ou porque o LinkedIn bloqueou
antes. Ela aparece como "descrição pendente" e não recebe nota da IA enquanto o texto não chega. Na busca seguinte,
antes das vagas novas, a ferramenta lê primeiro as descrições pendentes, dentro do mesmo limite de 20, e só então a
IA analisa essas vagas.

**Why this priority**: sem isso, cada bloqueio deixa vagas com nota ruim e sem como corrigir.

**Independent Test**: com 25 vagas pendentes no banco e 10 vagas novas, rodar uma busca simulada e conferir que as 20
primeiras lidas são pendentes (as mais recentes primeiro). Conferir também que as 5 pendentes restantes e as 10 novas
continuam pendentes e que nenhuma pendente foi para a IA.

**Acceptance Scenarios**:

1. **Given** vagas do LinkedIn com descrição pendente no relatório, **When** a pessoa busca de novo, **Then** as
   pendentes são lidas antes das novas, mesmo que a busca não as encontre de novo.
2. **Given** uma vaga com descrição pendente, **When** a análise com IA roda, **Then** essa vaga não recebe nota, e o
   relatório mostra "descrição pendente".
3. **Given** a descrição de uma vaga pendente lida com sucesso, **When** a busca termina, **Then** a vaga deixa de
   estar pendente e segue para a análise como as outras.
4. **Given** uma vaga pendente que o LinkedIn não tem mais (vaga encerrada ou removida), **When** a ferramenta tenta
   ler a descrição, **Then** a vaga deixa de estar pendente, é analisada com o que tem, e o pedido conta no limite de 20.
5. **Given** um bloqueio no meio das descrições, **When** ele acontece, **Then** as vagas não lidas continuam
   pendentes para a próxima busca, sem nova tentativa nesta.

---

### User Story 3 - Espera depois de um bloqueio, com o motivo (Priority: P2)

O LinkedIn bloqueou. O aviso diz o motivo provável: excesso de pedidos; recusa automática, que costuma ser a rede
(VPN, Wi-Fi corporativo, IP compartilhado); ou pedido de login. Diz também até que horas o LinkedIn fica em espera.
Se a pessoa tentar buscar de novo nas 6 horas seguintes, a ferramenta avisa antes de começar: o LinkedIn fica de
fora até HH:MM e a busca segue só com os outros portais. A pessoa decide se continua ou não.

**Why this priority**: insistir durante o bloqueio prolonga o bloqueio; a espera protege a pessoa de buscar de novo
sem perceber.

**Independent Test**: simular um bloqueio e pedir outra busca 1 hora depois. Conferir que a ferramenta pergunta se
continua sem o LinkedIn. Se a resposta for não, conferir que nenhuma busca começa. Se for sim, conferir zero pedidos
ao LinkedIn e o aviso com o horário. Rodar de novo 7 horas depois e conferir que o LinkedIn volta a ser consultado.

**Acceptance Scenarios**:

1. **Given** o LinkedIn respondendo "muitos pedidos", **When** o bloqueio acontece, **Then** o aviso diz "o LinkedIn
   limitou as consultas" com o motivo "excesso de pedidos" e o horário até quando fica em espera.
2. **Given** o LinkedIn recusando com o código de recusa automática, **When** o bloqueio acontece, **Then** o aviso
   sugere que a causa costuma ser a rede (VPN, Wi-Fi corporativo, internet compartilhada).
3. **Given** o LinkedIn redirecionando para login, **When** o bloqueio acontece, **Then** o aviso diz que ele pediu
   login.
4. **Given** um bloqueio há menos de 6 horas, **When** a pessoa pede uma busca (página, terminal ou chat), **Then**
   antes de começar a ferramenta avisa que o LinkedIn fica de fora até HH:MM e pergunta se segue só com os outros
   portais.
5. **Given** o aviso do cenário 4, **When** a pessoa confirma, **Then** a busca roda sem nenhum pedido ao LinkedIn, com
   os outros portais, e o resumo repete o aviso; **When** a pessoa não confirma, **Then** nenhuma busca começa.
6. **Given** o LinkedIn em espera e nenhum outro portal ligado, **When** a pessoa pede uma busca, **Then** a
   ferramenta avisa até que horas o LinkedIn fica em espera e não começa a busca, porque não haveria o que buscar.
7. **Given** um bloqueio há mais de 6 horas, **When** a pessoa busca, **Then** o LinkedIn volta a ser consultado
   normalmente, sem pergunta.
8. **Given** o LinkedIn em espera, **When** a pessoa abre o painel de busca, **Then** ela vê que o LinkedIn está em
   espera e até que horas, antes de clicar em buscar.

---

### User Story 4 - Aviso quando há cargos demais (Priority: P3)

A pessoa coloca mais de 5 cargos com o LinkedIn ou o Indeed ligados. O painel de filtros avisa, sem impedir de
salvar, que muitos cargos aumentam o risco de bloqueio nesses portais. A busca repete o aviso no começo.

**Why this priority**: orienta a pessoa, mas a consulta combinada (US1) já reduz o efeito no LinkedIn.

**Independent Test**: no painel, colocar 6 cargos com o LinkedIn ligado e ver o aviso. Salvar e conferir que salvou.
Tirar um cargo e ver o aviso sumir. Desligar LinkedIn e Indeed com 6 cargos e ver que não há aviso.

**Acceptance Scenarios**:

1. **Given** 6 cargos e o LinkedIn ou o Indeed ligados, **When** a pessoa edita os filtros, **Then** o painel mostra o
   aviso, e salvar continua permitido.
2. **Given** 5 cargos ou menos, ou nenhum dos dois portais ligados, **When** a pessoa edita os filtros, **Then** não
   há aviso de cargos.
3. **Given** mais de 5 cargos com um desses portais ligado, **When** a busca começa (página, terminal ou chat),
   **Then** o resumo da busca mostra o aviso.

---

### Edge Cases

- **Um só cargo**: a consulta combinada é o próprio cargo, sem "OR".
- **Cargo com aspas no meio ou só de um lado**: entra como a pessoa escreveu; a consulta combinada não fica com aspas
  soltas.
- **Consulta combinada longa demais** (muitos cargos): passa de um tamanho razoável e é dividida em mais de uma
  consulta. Mesmo assim, são menos consultas que uma por cargo.
- **O LinkedIn ignora o "OR"** e traz poucas vagas ou vagas fora dos cargos: os critérios de sempre (título incluído
  ou excluído, senioridade) filtram, como hoje. A verificação na fase de pesquisa decide o plano B (ver Assumptions).
- **Vaga pendente que já foi descartada ou movida para o quadro**: não entra na fila de descrições pendentes.
- **Arquivo da espera corrompido ou apagado**: a ferramenta segue sem espera, como se não houvesse bloqueio.
- **Relógio do computador mudou** (horário da espera no futuro distante): a espera vale no máximo 6 horas a partir da
  hora gravada; se a hora gravada estiver no futuro, ela é tratada como agora.
- **Adicionar Vaga por link do LinkedIn durante a espera**: não é afetado. É um pedido só, feito pela pessoa, e segue
  como hoje.
- **Configuração antiga** sem o campo novo: vagas antigas sem descrição não viram pendentes automaticamente. Só as
  vagas do LinkedIn salvas sem descrição a partir desta funcionalidade entram na fila.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Com o LinkedIn ligado, cada grupo de consulta MUST gerar uma única consulta ao LinkedIn com todos os
  cargos do grupo ligados por "OR". Cada cargo mantém a forma em que a pessoa o escreveu, com ou sem aspas.
- **FR-002**: A consulta combinada MUST ler até 3 páginas de resultados. Se a expressão passar de um tamanho máximo,
  ela MUST ser dividida no menor número de consultas que caiba nele.
- **FR-003**: As outras fontes MUST continuar com uma consulta por cargo, sem mudança.
- **FR-004**: Cada vaga encontrada pela consulta combinada MUST registrar os cargos da configuração que aparecem no
  título dela; se nenhum aparecer, MUST registrar a consulta combinada.
- **FR-005**: Uma busca MUST ler no máximo 20 descrições do LinkedIn, contando as tentativas que falharam.
- **FR-006**: A ordem das descrições MUST ser: primeiro as vagas do LinkedIn já no relatório com descrição pendente,
  das mais recentes para as mais antigas; depois as vagas novas, também das mais recentes para as mais antigas.
- **FR-007**: Vagas do LinkedIn que ficarem sem descrição (limite atingido, bloqueio ou espera) MUST ser gravadas com a
  marca "descrição pendente".
- **FR-008**: A análise com IA MUST pular as vagas com descrição pendente. O relatório MUST mostrar "descrição
  pendente" no lugar da nota.
- **FR-009**: Quando a descrição de uma vaga pendente é lida, ou quando a vaga não existe mais no LinkedIn, a marca
  MUST sair e a vaga MUST seguir para a análise como as outras.
- **FR-010**: Vagas pendentes que a pessoa já descartou ou levou para o quadro MUST ficar fora da fila de descrições.
- **FR-011**: Ao receber um sinal de bloqueio, a ferramenta MUST gravar a hora do bloqueio em arquivo local fora do Git.
  Nas 6 horas seguintes, nenhuma busca (página, terminal ou chat) MUST fazer pedido ao LinkedIn.
- **FR-011a**: Durante a espera, antes de começar uma busca, a ferramenta MUST avisar que o LinkedIn fica de fora até
  HH:MM e MUST pedir a confirmação da pessoa para seguir só com os outros portais. Sem confirmação, nenhuma busca
  começa. Se o LinkedIn for o único portal ligado, a ferramenta MUST avisar e não começar a busca. Isso vale na página
  (como a confirmação de busca recente que já existe), no chat (a skill pergunta) e no terminal (pergunta quando há
  alguém digitando; sem isso, só segue com uma opção explícita).
- **FR-012**: O aviso de bloqueio MUST trazer o motivo. Para excesso de pedidos: "excesso de pedidos". Para recusa
  automática: que costuma ser a rede (VPN, Wi-Fi corporativo, internet compartilhada). Para redirecionamento: "pediu
  login". Para acesso negado: o código recebido. O aviso MUST trazer também o horário até quando o LinkedIn fica em
  espera.
- **FR-013**: O painel de busca MUST mostrar, antes de buscar, quando o LinkedIn está em espera e até que horas.
- **FR-014**: Com mais de 5 cargos e o LinkedIn ou o Indeed ligados, o painel de filtros MUST mostrar um aviso de risco
  de bloqueio sem impedir de salvar, e o resumo da busca MUST repetir o aviso no começo.
- **FR-015**: Depois de um bloqueio, a busca seguinte MUST começar do zero, sem retomar a busca interrompida; o que
  ficou para trás é recuperado pelas descrições pendentes (FR-006).
- **FR-016**: Continuam valendo: sem login, sem conta ou cookies da pessoa, pausa entre pedidos e nenhuma nova
  tentativa depois do primeiro bloqueio na mesma busca (constituição, princípio VI).
- **FR-017**: README, AGENTS.md e a skill buscar-vagas MUST explicar que o limite é por rede (pessoas na mesma rede
  dividem a cota), a espera de 6 horas, as descrições pendentes e o aviso de cargos.
- **FR-018**: Com o LinkedIn desligado, a busca MUST dar o mesmo resultado de antes, exceto o aviso de cargos, que
  também vale para o Indeed.

### Key Entities

- **Consulta combinada do LinkedIn**: os cargos de um grupo ligados por "OR", com o local, os modelos de trabalho, os
  tipos de emprego e a janela de tempo do grupo.
- **Descrição pendente**: marca numa vaga do LinkedIn salva sem descrição, com a data da vaga para a ordem da fila.
- **Espera do LinkedIn**: a hora do último bloqueio e o motivo, num arquivo local fora do Git; vale por 6 horas.
- **Aviso de cargos**: aparece quando há mais de 5 cargos e o LinkedIn ou o Indeed estão ligados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com 7 cargos e 2 grupos, uma busca faz no máximo 26 pedidos ao LinkedIn (até 3 páginas por grupo e 20
  descrições), contra até ~154 antes.
- **SC-002**: Nenhuma vaga do LinkedIn salva sem descrição recebe nota da IA, e todas aparecem como "descrição
  pendente" até o texto chegar.
- **SC-003**: Com pendentes no banco e o LinkedIn disponível, 100% das descrições lidas numa busca são pendentes até a
  fila delas acabar.
- **SC-004**: Dentro das 6 horas depois de um bloqueio simulado, 100% dos pedidos de busca perguntam antes de
  começar; a busca confirmada faz zero pedidos ao LinkedIn e mostra o horário; a não confirmada não começa.
- **SC-005**: Os três tipos de bloqueio simulados (excesso de pedidos, recusa automática, pedido de login) geram três
  avisos diferentes, cada um com o motivo.
- **SC-006**: Com o LinkedIn e o Indeed desligados, a saída da busca é idêntica à de antes desta funcionalidade.

## Assumptions

- A busca pública do LinkedIn aceita "OR" entre termos com aspas. Na fase de pesquisa, isso é conferido com **um único
  pedido**, feito fora de um período de espera. Se não aceitar, o plano B mantém uma consulta por cargo no LinkedIn.
  Nesse caso, valem só os limites de descrições, a espera e os avisos.
- 3 páginas de 10 vagas por consulta combinada bastam para não perder volume em relação a hoje (uma página por cargo),
  porque a mesma vaga costuma aparecer em mais de um cargo.
- O tamanho máximo da expressão é decidido no plano, a partir do que a busca pública aceita sem erro.
- 20 descrições por busca e 6 horas de espera são decisões da pessoa. Ficam como constantes no código, não como
  opção da página.
- O aviso de cargos usa o contador de consultas que já existe no painel de filtros e convive com o aviso de "muitas
  consultas" (mais de 20).
- O intervalo mínimo de 30 minutos entre buscas da página continua como está.
- Adicionar Vaga por link do LinkedIn não muda nesta spec.
- Verificação só no Windows, como nas specs anteriores.
