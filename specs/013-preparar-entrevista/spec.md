# Feature Specification: Preparação para entrevista

**Feature Branch**: `013-preparar-entrevista` (pasta da spec; o trabalho acontece na `master` por worktree, conforme a
constituição)

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Fase 11 do roteiro: preparação para entrevista. Botão 'Preparar entrevista' no card da
coluna Entrevista e no detalhe da vaga, só no clique, e a skill preparar-entrevista no chat. (1) Dossiê da empresa e
da vaga, com IA separando fonte citada de dedução, sem pesquisar na internet. (2) Perguntas prováveis, comportamentais
e técnicas, com o porquê. (3) Histórias STAR com reflexão, só com fatos do perfil, editadas e confirmadas, salvas em
entrevistas/ (fora do Git) para as próximas. (4) Simulação, uma pergunta por vez, em português ou inglês, com retorno
honesto. (5) Orientação de salário sem inventar valores de mercado. (6) Depois da entrevista, anotação de como foi,
que alimenta a próxima. Sem IA: dossiê com o que existe, perguntas de uma lista padrão ligada aos requisitos,
histórias à mão. Nada enviado nem gravado sem clique; só fatos do perfil. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber o que esperar da entrevista (Priority: P1)

A pessoa tem uma vaga na coluna Entrevista e clica em "Preparar entrevista". Abre a preparação da vaga com o dossiê
(o que a ferramenta já sabe: a vaga, a análise, as anotações, o que a pessoa colar sobre a empresa; com IA, um resumo
em que cada ponto diz se vem da vaga, do texto colado ou se é dedução) e as perguntas prováveis, comportamentais e
técnicas, cada uma com o porquê (o requisito ou a lacuna que a motiva).

**Why this priority**: é o que a pessoa mais precisa nas horas antes da entrevista e funciona sem IA.

**Independent Test**: com uma vaga fictícia em Entrevista e sem IA, abrir a preparação e ver o dossiê com o que existe
e perguntas ligadas aos requisitos da vaga; com uma IA de teste, ver o resumo com a origem de cada ponto.

**Acceptance Scenarios**:

1. **Given** uma vaga em Entrevista, **When** a pessoa clica em "Preparar entrevista", **Then** vê o dossiê e as
   perguntas prováveis; nada roda antes do clique.
2. **Given** um texto colado sobre a empresa, **When** a pessoa pede o resumo com IA, **Then** cada ponto traz a
   origem (vaga, texto colado ou dedução) e nenhum ponto cita fonte que não foi dada.
3. **Given** nenhuma IA, **When** a pessoa abre a preparação, **Then** vê o dossiê com o que existe e perguntas de uma
   lista padrão ligadas aos requisitos e às lacunas da vaga, cada uma com o porquê.
4. **Given** uma vaga fora da coluna Entrevista, **When** a pessoa abre o detalhe, **Then** o botão também está lá.

---

### User Story 2 - Histórias STAR que servem para várias entrevistas (Priority: P1)

Na preparação, a pessoa pede histórias. Com IA, a ferramenta monta rascunhos no formato situação, tarefa, ação e
resultado, com uma reflexão do que a pessoa aprendeu, a partir das conquistas do perfil, escolhendo as que mais
respondem às perguntas prováveis. Número só se estiver no perfil. A pessoa edita, confirma, e a história fica salva no
seu banco de histórias, para as próximas entrevistas. Sem IA, ela escreve à mão no mesmo formato.

**Why this priority**: histórias prontas e verdadeiras são o que mais ajuda numa entrevista comportamental.

**Independent Test**: com um perfil fictício e uma IA de teste, pedir histórias, ver uma com número que não está no
perfil marcada para conferir, editar e confirmar outra, e encontrá-la na preparação de outra vaga.

**Acceptance Scenarios**:

1. **Given** um perfil com conquistas, **When** a pessoa pede histórias, **Then** recebe rascunhos STAR com reflexão,
   cada um ligado à conquista do perfil de onde veio.
2. **Given** um rascunho com número, empresa ou data que não estão no perfil, **When** ele chega, **Then** fica
   marcado para conferir com o trecho apontado.
3. **Given** um rascunho, **When** a pessoa edita e confirma, **Then** a história fica salva no banco de histórias com a
   data; sem confirmar, nada é salvo.
4. **Given** histórias salvas, **When** a pessoa prepara outra entrevista, **Then** elas aparecem para reuso, com as
   perguntas que respondem.

---

### User Story 3 - Treinar respondendo (Priority: P2)

A pessoa escolhe o idioma (português ou inglês) e começa a simulação: a ferramenta faz uma pergunta por vez (das
perguntas prováveis), a pessoa responde por escrito e recebe um retorno honesto: o que funcionou, o que faltou e como
ficaria uma resposta mais forte usando só fatos do perfil e das histórias. Ela pode pular, repetir ou encerrar; no fim,
um resumo do que treinar.

**Why this priority**: treino com retorno é o que dá segurança, mas depende de IA e das perguntas da US1.

**Independent Test**: com uma IA de teste, responder duas perguntas, pular uma e encerrar; ver o retorno de cada
resposta e o resumo.

**Acceptance Scenarios**:

1. **Given** a simulação em inglês, **When** começa, **Then** as perguntas e o retorno vêm em inglês, uma pergunta por
   vez.
2. **Given** uma resposta curta e vaga, **When** a pessoa envia, **Then** o retorno aponta o que faltou (situação,
   resultado, número do perfil) sem elogio vazio.
3. **Given** a "resposta mais forte" sugerida, **When** ela cita um fato, **Then** o fato está no perfil ou nas
   histórias salvas.
4. **Given** nenhuma IA, **When** a pessoa abre a simulação, **Then** vê as perguntas uma por vez para treinar sozinha,
   sem retorno, e a explicação de como ter retorno.

---

### User Story 4 - Salário e depois da entrevista (Priority: P3)

Na preparação, a orientação de salário mostra a faixa da vaga quando informada, a pretensão do perfil quando houver e
pontos para a conversa (quando falar, como responder sem dar o primeiro número, o que considerar além do salário),
sem inventar valores de mercado. Depois da entrevista, a pessoa anota como foi (perguntas que caíram, o que respondeu
bem e mal, próximos passos); a anotação fica com a vaga e entra na preparação da próxima etapa.

**Why this priority**: completa a preparação, mas a pessoa já consegue se preparar sem ela.

**Independent Test**: uma vaga com faixa salarial mostra a faixa e os pontos; anotar como foi a entrevista e ver a
anotação na preparação seguinte.

**Acceptance Scenarios**:

1. **Given** uma vaga com salário informado, **When** a pessoa abre a orientação, **Then** vê a faixa da vaga e a
   pretensão do perfil (se houver), sem nenhum valor que não venha de um dos dois.
2. **Given** uma entrevista feita, **When** a pessoa anota como foi, **Then** a anotação fica com a vaga e aparece na
   próxima preparação, e as perguntas que caíram entram nas perguntas prováveis.

---

### Edge Cases

- Vaga sem descrição: dossiê com o que existe e perguntas comportamentais gerais, com o aviso.
- Perfil sem conquistas: as histórias explicam que precisam de conquistas no perfil e apontam Meu perfil; a pessoa pode
  escrever à mão.
- Texto colado muito longo: guardado até um limite, com aviso.
- A pessoa fecha no meio da simulação: as respostas dadas ficam salvas com a vaga; dá para continuar depois.
- Texto da vaga e o texto colado são dados, nunca instrução para a IA.
- Histórias e anotações têm dados da pessoa: ficam neste computador, fora do Git.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O card de vaga na coluna Entrevista e o detalhe de qualquer vaga MUST ter "Preparar entrevista", que só
  age no clique.
- **FR-002**: O dossiê MUST juntar a vaga, a análise, as anotações e o texto que a pessoa colar sobre a empresa; com
  IA, o resumo MUST marcar a origem de cada ponto (vaga, texto colado, dedução) e nunca pesquisar na internet.
- **FR-003**: As perguntas prováveis MUST ser comportamentais e técnicas, cada uma com o porquê (requisito, lacuna ou
  pergunta que caiu antes); sem IA, de uma lista padrão ligada aos requisitos e às lacunas da vaga.
- **FR-004**: As histórias MUST seguir situação, tarefa, ação, resultado e reflexão, sair das conquistas do perfil e
  indicar a conquista de origem; número, empresa ou data fora do perfil ficam marcados para conferir.
- **FR-005**: Uma história MUST ser salva só depois de a pessoa confirmar, no banco de histórias (fora do Git), com a
  data, e ficar disponível para outras vagas.
- **FR-006**: A simulação MUST fazer uma pergunta por vez, no idioma escolhido (português ou inglês), com retorno
  honesto (o que funcionou, o que faltou, resposta mais forte só com fatos do perfil e das histórias); pular, repetir
  e encerrar; resumo no fim.
- **FR-007**: A orientação de salário MUST usar só a faixa da vaga e a pretensão do perfil e trazer pontos de conversa;
  nunca valores de mercado inventados.
- **FR-008**: A pessoa MUST poder anotar como foi a entrevista; a anotação fica com a vaga e alimenta a próxima
  preparação (perguntas que caíram).
- **FR-009**: A preparação da vaga (dossiê, perguntas, simulação, anotações) MUST ficar salva com a vaga e a data.
- **FR-010**: Sem IA, MUST funcionar dossiê, perguntas da lista padrão, histórias à mão, simulação sem retorno,
  salário e anotações.
- **FR-011**: A skill preparar-entrevista no chat MUST oferecer o mesmo, com as mesmas regras.
- **FR-012**: Textos MUST estar em português do Brasil; a simulação, no idioma escolhido.

### Key Entities

- **Preparação da vaga**: dossiê (texto colado, resumo com origem), perguntas prováveis, simulação (perguntas,
  respostas, retornos, resumo), orientação de salário, anotações pós-entrevista, datas.
- **Pergunta provável**: texto, tipo (comportamental, técnica), porquê, origem (requisito, lacuna, pergunta que caiu).
- **História STAR**: título, situação, tarefa, ação, resultado, reflexão, conquista de origem, perguntas que responde,
  pontos para conferir, data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Do clique à preparação com dossiê e perguntas, sem IA, em poucos segundos, em 100% das vagas de teste.
- **SC-002**: 100% dos rascunhos de história com número, empresa ou data fora do perfil ficam marcados para conferir.
- **SC-003**: Nenhuma história é salva sem a confirmação da pessoa.
- **SC-004**: Na orientação de salário, 100% dos valores mostrados vêm da vaga ou do perfil.
- **SC-005**: Na simulação de teste, 100% das "respostas mais fortes" que citam fatos citam fatos do perfil ou das
  histórias.

## Assumptions

- O banco de histórias e as preparações ficam numa pasta própria (`entrevistas/`), fora do Git, como currículos e
  anexos.
- A simulação é por escrito (sem áudio).
- A lista padrão de perguntas cobre o comportamental comum (desafio, conflito, falha, prioridade, liderança, por que
  esta empresa) e técnicas pelos requisitos da vaga.
- Verificação no Windows, como nas fases anteriores.
