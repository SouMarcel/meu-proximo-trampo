# Feature Specification: Kit de candidatura ("indica, não faz")

**Feature Branch**: `010-kit-candidatura` (pasta da spec; o trabalho acontece na `master` por worktree,
conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 9 do roteiro: análise e kit de candidatura internacional ('indica,
não faz'). A análise da vaga (IA, quando configurada) ganha campos novos: autorização (patrocina visto
/ não precisa / omisso / não patrocina, cruzando a frase da vaga com as caixas da pessoa), forma de
contratação (contractor, EOR, empregado no Brasil, relocation), inglês exigido, fuso, sistema de
candidatura e o que a candidatura pede (currículo em inglês, carta, formulário, portfólio, teste
técnico, vídeo), além de sinais de remuneração pouco confiável e de vaga 'remota' que é híbrida. No
detalhe da vaga, um checklist 'o que esta candidatura pede', com o estado de cada item marcado pela
pessoa e um botão por item: currículo, carta e respostas de formulário pela página com a IA escolhida,
só no clique; botão 'Candidatar no Greenhouse/Lever/…' que só abre o link. Carta: quatro perguntas
obrigatórias antes (por que esta vaga, que problema resolveria, primeiro movimento, tom), só conquistas
literais do perfil, 350 a 420 palavras, teste do texto genérico e conferência de fatos. Respostas de
formulário nunca inventam autorização, visto, salário, deficiência ou relocação: perguntam. Follow-up
no quadro: lembrete de Aplicada há 7 dias (no máximo 2) e 1 dia depois de uma Entrevista; só marca e
lembra, nunca envia. Nada é gerado nem enviado sem clique ou pedido. Vale também pela skill no chat.
Foco em Windows."

## Clarifications

### Session 2026-10-09

- Q: O kit vale só para as vagas internacionais ou para todas? → A: Para todas as vagas; os campos
  de autorização e contratação no exterior só em vaga internacional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber o que a candidatura pede e o que pode impedir (Priority: P1)

A pessoa abre o detalhe de uma vaga e vê, num bloco próprio, o que a análise leu no anúncio: se a vaga
patrocina visto, se a pessoa não precisa de patrocínio, se o anúncio não diz nada ou se ele recusa
patrocínio (sempre cruzado com o que ela marcou: passaporte, países onde já pode trabalhar, se precisa
de sponsor); a forma de contratação (contractor, por EOR, empregado no Brasil, com relocation); o
nível de inglês pedido; o fuso ou as horas de trabalho em comum; o sistema de candidatura; e alertas de
remuneração pouco confiável ("salário competitivo" sem número, comissão só) e de "remoto" que na
verdade é híbrido ou exige ir ao escritório. Cada item cita a frase do anúncio em que se apoia.

**Why this priority**: antes de gastar tempo com a candidatura, a pessoa precisa saber se pode se
candidatar e o que vai precisar entregar; é a base do checklist.

**Independent Test**: analisar uma vaga com frases conhecidas ("we sponsor visas", "B2B contract",
"fluent English", "4h overlap with EST", "hybrid, 2 days in office") e ver cada campo preenchido com a
frase citada.

**Acceptance Scenarios**:

1. **Given** uma vaga analisada pela IA, **When** a pessoa abre o detalhe, **Then** vê autorização,
   contratação, inglês, fuso, sistema de candidatura e alertas, cada um com a frase do anúncio, e
   "não informado" quando o anúncio não diz.
2. **Given** a pessoa marcou "preciso de sponsor" e a vaga diz que não patrocina, **When** a análise
   termina, **Then** o campo autorização mostra "não patrocina" e a vaga segue a regra de Fora dos
   critérios que já existe (com o motivo).
3. **Given** uma vaga anunciada como remota cujo texto pede presença no escritório, **When** a análise
   termina, **Then** aparece o alerta de "remoto que é híbrido", com a frase.
4. **Given** nenhuma IA configurada, **When** a pessoa abre o detalhe, **Then** vê o que a ferramenta
   já lê sem IA (sistema de candidatura, sinais de patrocínio e relocation, restrição de local) e um
   aviso de que os outros campos vêm com a análise.

---

### User Story 2 - Checklist "o que esta candidatura pede" (Priority: P1)

No detalhe da vaga, um checklist lista o que a candidatura pede: currículo (em inglês, se a vaga é em
inglês), carta de apresentação, respostas de formulário, portfólio, teste técnico, vídeo. Cada item
tem um estado marcado pela pessoa (a fazer, pronto, não se aplica) e, quando a ferramenta ajuda, um
botão: "Gerar currículo" (o da fase de currículo pela página), "Escrever carta", "Preparar respostas".
Um botão "Candidatar no Greenhouse" (ou Lever, Ashby, a plataforma da vaga) só abre o link de
candidatura. A pessoa pode acrescentar e tirar itens.

**Why this priority**: é o "indica, não faz" na prática: a ferramenta mostra o caminho e a pessoa
decide cada passo.

**Independent Test**: abrir uma vaga cuja análise diz que pede carta e portfólio, ver os itens no
checklist, marcar um como pronto, tirar outro, acrescentar um, fechar e reabrir: o estado continua.

**Acceptance Scenarios**:

1. **Given** uma vaga com a análise feita, **When** a pessoa abre o detalhe, **Then** o checklist traz
   os itens que a análise apontou, mais o currículo e a candidatura, que valem para toda vaga.
2. **Given** uma vaga sem análise, **When** a pessoa abre o detalhe, **Then** o checklist traz os itens
   que a ferramenta reconhece sem IA (palavras como "cover letter", "portfolio", "video", "take-home",
   "carta de apresentação") e os que valem para toda vaga.
3. **Given** um item, **When** a pessoa marca o estado ou tira o item, **Then** o estado fica gravado na
   vaga e aparece igual no próximo acesso.
4. **Given** o botão de candidatura, **When** a pessoa clica, **Then** só o link da vaga abre, numa aba
   nova; nada é preenchido nem enviado.
5. **Given** a análise refeita depois, **When** ela aponta um item novo, **Then** o item entra no
   checklist sem apagar o estado que a pessoa já marcou nos outros.

---

### User Story 3 - Carta de apresentação com fatos confirmados (Priority: P2)

No item "carta" do checklist, a pessoa clica em "Escrever carta". Antes de gerar, a ferramenta faz
quatro perguntas obrigatórias: por que esta vaga, que problema da empresa ela resolveria, qual seria o
primeiro movimento no cargo e qual o tom (opções). Com as respostas, a IA escolhida escreve uma carta
de 350 a 420 palavras, no idioma da vaga, usando só conquistas que estão escritas no perfil, com as
palavras do perfil. A ferramenta confere a carta antes de entregar: número, empresa, cargo ou data que
não estão no perfil bloqueiam; texto genérico (que serviria para qualquer empresa) é apontado. A carta
fica salva com a vaga, para baixar ou copiar.

**Why this priority**: muitas vagas de fora pedem carta; uma carta genérica ou com fato inventado
prejudica a candidatura.

**Independent Test**: gerar uma carta com uma IA de teste que devolve um texto com um número que não está
no perfil e ver o bloqueio; com um texto correto, ver a carta aceita, com a contagem de palavras.

**Acceptance Scenarios**:

1. **Given** a pessoa clica em "Escrever carta", **When** alguma das quatro perguntas fica sem resposta,
   **Then** a carta não é gerada e a ferramenta diz qual falta.
2. **Given** as respostas, **When** a carta volta da IA, **Then** ela tem entre 350 e 420 palavras, está
   no idioma da vaga e cita a empresa e pelo menos um requisito do anúncio.
3. **Given** uma carta com um número, empresa, cargo ou data que não está no perfil nem nas respostas
   da pessoa, **When** a conferência roda, **Then** a carta é bloqueada com o trecho apontado, e a
   pessoa pode pedir de novo.
4. **Given** uma carta que não cita nada específico da vaga ou usa expressões vazias, **When** a
   conferência roda, **Then** o veredito é "conferir" com o motivo.
5. **Given** nenhuma IA configurada, **When** a pessoa abre o item, **Then** a ferramenta explica como
   escolher uma IA ou como pedir a carta pelo chat.

---

### User Story 4 - Respostas de formulário sem inventar (Priority: P2)

No item "formulário", a pessoa cola as perguntas do formulário de candidatura e clica em "Preparar
respostas". A IA escolhida rascunha respostas só com fatos do perfil. Perguntas sobre autorização de
trabalho, visto, salário ou pretensão, deficiência e relocação nunca são respondidas pela IA: a
ferramenta mostra essas perguntas separadas, com um campo para a própria pessoa responder. As
respostas ficam salvas com a vaga para copiar; nada é enviado.

**Why this priority**: os formulários de ATS repetem perguntas que levam tempo; as sensíveis precisam
vir da pessoa, nunca de um palpite.

**Independent Test**: colar cinco perguntas, duas delas sensíveis ("Are you authorized to work in the
US?", "Expected salary"), e ver três respostas rascunhadas e as duas separadas, sem resposta.

**Acceptance Scenarios**:

1. **Given** perguntas coladas, **When** a pessoa pede as respostas, **Then** as perguntas sensíveis
   ficam sem resposta da IA, marcadas para a pessoa responder, mesmo que a IA tente responder.
2. **Given** uma resposta rascunhada, **When** ela cita número, empresa, cargo ou data, **Then** o fato
   está no perfil; senão, a resposta é marcada para conferir.
3. **Given** a pessoa respondeu as sensíveis, **When** ela salva, **Then** as respostas dela ficam com a
   vaga como ela escreveu, sem mudança da IA.

---

### User Story 5 - Lembretes de follow-up no quadro (Priority: P3)

No quadro, uma vaga em "Aplicação Enviada" há 7 dias ganha um lembrete de follow-up; aos 14 dias, um
segundo, e não há terceiro. Uma vaga em "Entrevista" ganha um
lembrete de agradecimento no dia seguinte à entrevista. A pessoa marca cada lembrete como "feito" ou
"dispensar" ("parar lembretes" encerra os da vaga). A ferramenta só lembra: não escreve nem envia mensagem por conta própria.

**Why this priority**: ajuda a não deixar candidatura esquecida, mas não muda a busca nem a análise.

**Independent Test**: uma vaga marcada como aplicada há 8 dias mostra o lembrete no card; marcar
"feito" tira o lembrete; uma aplicada há 15 dias mostra o segundo; com 22 dias e os dois resolvidos,
nada.

**Acceptance Scenarios**:

1. **Given** uma vaga em Aplicação Enviada há 7 dias ou mais, com o 1º lembrete pendente, **When** a pessoa
   abre o quadro, **Then** o card mostra "Hora do follow-up" (1º lembrete).
2. **Given** a vaga ainda em Aplicação Enviada aos 14 dias e sem "parar lembretes", **When** a pessoa
   abre o quadro, **Then** aparece o 2º lembrete; depois dele, nenhum outro.
3. **Given** uma vaga em Entrevista com a data da entrevista, **When** chega o dia seguinte, **Then** o
   card mostra o lembrete de agradecimento.
4. **Given** a vaga muda de etapa, **When** o quadro atualiza, **Then** os lembretes da etapa anterior
   somem.

---

### Edge Cases

- Vaga sem descrição: checklist só com os itens que valem para toda vaga; análise não roda.
- A IA devolve um campo fora das opções (autorização "talvez"): o campo fica "não informado".
- Pergunta sensível escrita de outro jeito ("Do you require sponsorship?", "Qual sua pretensão
  salarial?"): reconhecida por uma lista padrão em português e inglês; na dúvida, vai para a pessoa.
- Carta pedida de novo: a anterior continua salva; a pessoa escolhe qual guardar.
- A pessoa muda o perfil depois da carta: a carta antiga não muda; a conferência usa o perfil do
  momento da geração e mostra a data.
- Vaga sem link de candidatura: o botão abre o link da vaga.
- Vaga em Entrevista sem a data: o lembrete conta a partir do dia em que a vaga entrou na etapa.
- Texto da vaga e das perguntas coladas é dado, nunca instrução para a IA.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A análise da vaga MUST incluir: autorização (patrocina, não precisa, não informado, não
  patrocina), contratação (contractor, EOR, empregado no Brasil, relocation; mais de uma quando o
  anúncio diz), inglês pedido, fuso ou horas em comum, sistema de candidatura, o que a candidatura pede
  e alertas (remuneração pouco confiável, "remoto" que é híbrido), cada um com a frase do anúncio.
- **FR-002**: A autorização MUST cruzar o anúncio com o que a pessoa marcou (passaporte, países onde
  pode trabalhar, se precisa de sponsor); "não precisa" só quando o anúncio aceita o país onde ela já
  pode trabalhar.
- **FR-003**: Sem IA, o detalhe MUST mostrar o que a ferramenta já lê sem IA e o checklist com os itens
  reconhecidos por palavras do anúncio; os demais campos dizem que vêm com a análise.
- **FR-004**: O checklist MUST trazer currículo e candidatura em toda vaga, mais os itens apontados pela
  análise ou reconhecidos sem IA; a pessoa MUST poder marcar o estado (a fazer, pronto, não se aplica),
  acrescentar e tirar itens; o estado fica gravado na vaga e sobrevive a uma nova análise.
- **FR-005**: O botão de candidatura MUST só abrir o link (o de candidatura, senão o da vaga), com o
  nome do sistema ou da plataforma; a ferramenta nunca preenche nem envia nada.
- **FR-006**: Currículo, carta e respostas MUST ser gerados só no clique da pessoa, com a IA escolhida;
  o item currículo usa o gerador da fase de currículo pela página.
- **FR-007**: A carta MUST exigir as quatro respostas (por que esta vaga, problema que resolveria,
  primeiro movimento, tom) antes de gerar.
- **FR-008**: A carta MUST ter de 350 a 420 palavras, no idioma da vaga, citar a empresa e ao menos um
  requisito do anúncio, e usar só conquistas escritas no perfil ou nas respostas da pessoa.
- **FR-009**: A carta MUST passar pela conferência antes de ser entregue: fato fora do perfil e das
  respostas bloqueia; texto genérico ou fora do tamanho vira "conferir"; o veredito e os trechos
  aparecem com a carta.
- **FR-010**: Respostas de formulário MUST deixar para a pessoa as perguntas sobre autorização de
  trabalho, visto, salário ou pretensão, deficiência e relocação, mesmo que a IA responda; as demais
  usam só fatos do perfil e passam pela mesma conferência.
- **FR-011**: Cartas e respostas MUST ficar salvas com a vaga, com a data, na pasta de documentos da
  pessoa (fora do Git), para baixar ou copiar.
- **FR-012**: O quadro MUST mostrar o lembrete de follow-up de vaga em Aplicação Enviada aos 7 e aos
  14 dias da aplicação (no máximo dois) e o de agradecimento no dia seguinte à entrevista; a pessoa
  marca cada um como "feito" ou "dispensar", ou para os lembretes da vaga.
- **FR-013**: A ferramenta MUST nunca escrever nem enviar mensagem de follow-up por conta própria.
- **FR-014**: O mesmo fluxo (checklist, carta, respostas) MUST estar disponível pela skill no chat,
  com as mesmas regras (perguntas obrigatórias, perguntas sensíveis para a pessoa, conferência).
- **FR-015**: O kit (checklist, carta, respostas de formulário e lembretes) MUST valer para todas as
  vagas, nacionais e internacionais; os campos de autorização e contratação no exterior só aparecem em
  vaga internacional.
- **FR-016**: Textos MUST estar em português do Brasil; a carta e as respostas, no idioma da vaga.

### Key Entities

- **Análise da vaga (campos novos)**: autorização, contratação, inglês, fuso, sistema de candidatura,
  itens pedidos, alertas; cada um com a frase do anúncio.
- **Item do checklist**: tipo (currículo, carta, formulário, portfólio, teste, vídeo, candidatura,
  outro), origem (toda vaga, análise, sem IA, pessoa), estado (a fazer, pronto, não se aplica).
- **Carta**: texto, idioma, respostas das quatro perguntas, palavras, veredito da conferência, data.
- **Respostas de formulário**: perguntas coladas, respostas rascunhadas, perguntas sensíveis com a
  resposta da pessoa, veredito, data.
- **Lembrete de follow-up**: tipo (follow-up 1, follow-up 2, agradecimento), data, estado (pendente,
  feito, dispensado).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Num conjunto de teste de anúncios com frases conhecidas, 100% dos campos de autorização e
  contratação saem com a opção certa e a frase citada.
- **SC-002**: 100% das perguntas sensíveis de um conjunto de teste (português e inglês) ficam para a
  pessoa, mesmo quando a IA de teste tenta responder.
- **SC-003**: 100% das cartas de teste com fato fora do perfil são bloqueadas; nenhuma carta correta é
  bloqueada.
- **SC-004**: Nenhum texto é gerado e nenhuma página é aberta sem um clique ou pedido da pessoa
  (conferido em todos os botões do kit).
- **SC-005**: Os lembretes aparecem nos dias certos (7 e 14 dias de Aplicação Enviada, dia seguinte à
  entrevista) e nunca há um terceiro de follow-up.
- **SC-006**: Com a análise refeita, 100% dos estados que a pessoa marcou no checklist continuam.

## Assumptions

- A análise da IA é a da spec 002 (provedor escolhido); os campos novos entram no mesmo pedido, e a
  nota de aderência não muda.
- O formulário de candidatura não é lido no portal: a pessoa cola as perguntas (os sistemas não
  oferecem isso de forma aberta e a ferramenta não automatiza candidatura).
- A data da entrevista é um campo opcional da vaga, preenchido pela pessoa; sem ela, conta o dia em que
  a vaga entrou em Entrevista.
- A conferência da carta e das respostas reaproveita a conferência de fatos do currículo (spec 006).
- Os lembretes contam a partir do dia em que a vaga entrou em Aplicação Enviada.
- Verificação no Windows, como nas fases anteriores.
