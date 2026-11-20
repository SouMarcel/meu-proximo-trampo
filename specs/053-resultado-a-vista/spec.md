# Feature Specification: Currículo e carta com resultado à vista

**Feature Branch**: `053-resultado-a-vista` (worktree saída da `master`)

**Created**: 2026-11-19

**Status**: Draft

**Input**: Lições de uma auditoria externa de currículo (um site que dá nota ao currículo e o adapta a uma vaga). A
pessoa passou nele o currículo base gerado pela ferramenta e, depois, pediu a versão adaptada a uma vaga de Scrum
Master, com texto de candidatura. O site acertou alguns pontos e errou outros; esta spec traz para a ferramenta o
que ele acertou, sem copiar o que errou:

1. Resultado primeiro: dentro de cada experiência, os itens com resultado confirmado vêm antes dos itens de tarefa;
   os Destaques preferem itens com número.
2. Contato completo: a conferência avisa quando o currículo sai sem e-mail (e, no formato Brasil, sem telefone).
3. Itens só de tarefa: a conferência mostra "N de M itens descrevem tarefa", com os trechos.
4. Carta e respostas: diferencial que a pessoa não tem não é mencionado nem confessado; o que está "em preparação"
   pode ser dito assim, nunca como se ela já tivesse.
5. Requisitos: o que o perfil marca como "em preparação" ou "em andamento" não conta como "tem"; requisito que pede
   vários idiomas não sai "sustentado" quando falta um deles.

Fora do escopo: reescrever item com verbo mais forte, sugerir métricas para a pessoa preencher e a "caça de números"
(pergunta por item sem resultado que vira relato), que vai para a lista de desejos.

## Contexto

O que a auditoria mostrou no currículo da ferramenta:

- **Contato sem e-mail.** O cabeçalho saiu só com cidade e LinkedIn. A linha de contato já foi corrigida (passou a
  sair dos dados de contato salvos), mas a conferência só avisa quando o contato está **vazio**: um currículo sem
  e-mail passa sem aviso.
- **Resultados escondidos.** O perfil tinha os números (redução percentual, economia por ano, parcela dos
  atendimentos), mas eles ficaram no fim da experiência, depois de cinco itens de tarefa e já na página 2. Os três
  Destaques saíram sem nenhum número. Faltou ordem, não dado.
- **Itens de tarefa.** "8 de 27 itens descrevem tarefa, não resultado". A ferramenta não mede isso.

O que a auditoria errou, e que esta spec não adota:

- **Verbo inflado.** "Desenhei a arquitetura" para quem valida o código; "Reestruturei" para quem dividiu tarefas.
- **Competência copiada da vaga.** Pôs na lista de competências duas metodologias que a vaga pedia e que o perfil não
  tinha. A conferência da ferramenta bloquearia isso, desde que leia os requisitos da vaga. Essa leitura falhava em
  dois portais e já foi corrigida, fora desta spec.
- **Ressalva tirada.** "sem impactos" onde o perfil diz "sem grandes impactos".
- **Lacuna confessada.** O texto de candidatura dizia "não tenho a certificação X", e X era só um diferencial da
  vaga. O perfil ainda dizia que a certificação estava em preparação.

Na mesma análise, a classificação de requisitos da ferramenta mostrou dois erros próprios: uma certificação "em
preparação" no perfil contou como "tem", e "Inglês e Espanhol" saiu "sustentado" para um perfil sem espanhol.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - O que a pessoa conquistou aparece primeiro (Priority: P1)

A pessoa gera um currículo, base ou para uma vaga. Em cada experiência, os itens que trazem um resultado confirmado
(número, percentual, valor ou efeito descrito no perfil, como "o que permitiu encerrar os cards") vêm antes dos itens
que só descrevem tarefa. Se o currículo tem a seção Destaques, ela prefere os itens com número.

Nada é acrescentado nem reescrito para "criar" resultado: só a ordem muda, e só entre fatos que já estão no perfil e
nos relatos.

**Why this priority**: é o ganho mais direto. Quem lê o currículo olha o começo de cada experiência; hoje os números
ficam no fim, às vezes na página 2.

**Independent Test**: com um perfil fictício em que uma experiência lista três tarefas e depois dois itens com
número, gerar o currículo e ver os dois itens com número no topo daquela experiência. Gerar com Destaques e ver
itens com número nos Destaques.

**Acceptance Scenarios**:

1. **Given** uma experiência do perfil com itens de tarefa antes de itens com número, **When** a pessoa gera o
   currículo, **Then** os itens com número aparecem primeiro naquela experiência.
2. **Given** a seção Destaques ligada e um perfil com itens que têm número, **When** o currículo é gerado, **Then**
   os Destaques trazem pelo menos um item com número (se o perfil tiver ao menos um ligado ao alvo).
3. **Given** uma experiência sem nenhum item com resultado, **When** o currículo é gerado, **Then** a ordem fica a
   que melhor serve ao alvo, como hoje, e nada é inventado para preencher.
4. **Given** um currículo gerado depois desta spec, **When** a pessoa compara com o perfil, **Then** todo número e
   todo resultado do currículo estão no perfil ou nos relatos, do jeito que estão lá.

---

### User Story 2 - A conferência aponta contato incompleto e itens só de tarefa (Priority: P1)

Depois de gerar o currículo, a conferência sem IA (a que já aparece junto do currículo gerado) passa a avisar:

- **contato sem e-mail**: "o contato não tem e-mail: recrutadores usam o e-mail para responder";
- **no formato Brasil, contato sem telefone**: aviso equivalente;
- **itens só de tarefa**: "N de M itens das experiências descrevem tarefa, sem resultado", com os trechos, para a
  pessoa decidir se tem um resultado a contar (que vira relato) ou se deixa como está.

Todos os avisos novos são do nível "conferir": não bloqueiam o currículo.

**Why this priority**: o contato sem e-mail foi o único problema "prioritário" da auditoria e passou sem aviso. A
contagem de itens de tarefa diz à pessoa onde vale buscar um resultado, sem que a ferramenta invente nada.

**Independent Test**: conferir um currículo de exemplo sem e-mail no contato e ver o aviso; conferir um currículo
com 10 itens de experiência, 4 deles sem resultado, e ver "4 de 10 itens…" com os 4 trechos.

**Acceptance Scenarios**:

1. **Given** um currículo cujo contato tem cidade e LinkedIn mas não tem e-mail, **When** ele é conferido, **Then**
   aparece o aviso de e-mail ausente, nível "conferir".
2. **Given** um currículo no formato Brasil sem telefone no contato, **When** ele é conferido, **Then** aparece o
   aviso de telefone ausente; no formato dos Estados Unidos ou da Europa, a falta de telefone não gera aviso.
3. **Given** um currículo com contato completo, **When** ele é conferido, **Then** nenhum aviso de contato aparece.
4. **Given** itens de experiência sem número e sem efeito descrito, ou que começam por expressão vaga ("atua",
   "responsável por", "auxiliou", "participou de"), **When** o currículo é conferido, **Then** a conferência conta
   esses itens sobre o total, mostra os trechos e não muda o veredito para "bloquear".
5. **Given** um currículo em que todos os itens trazem resultado, **When** ele é conferido, **Then** não aparece o
   aviso de itens só de tarefa.
6. **Given** a conferência pela linha de comando, **When** a pessoa confere um currículo, **Then** os mesmos avisos
   aparecem no texto e no resultado em JSON.

---

### User Story 3 - Carta e respostas não confessam o que a vaga não exige (Priority: P2)

Na carta de apresentação e nas respostas de formulário geradas para uma vaga:

- um **diferencial** da vaga (o que ela lista como desejável, não como requisito) que a pessoa não tem **não é
  mencionado**: nem afirmado, nem confessado ("não tenho X");
- o que o perfil marca como **"em preparação"** ou **"em andamento"** pode ser dito assim ("em preparação para a
  certificação X"), nunca como se a pessoa já tivesse;
- um **requisito** que a pessoa não tem continua com a regra de hoje: não é afirmado e, se fizer sentido, o texto
  mostra a experiência vizinha, sem fingir que é a mesma coisa.

**Why this priority**: confessar uma lacuna que a vaga não exige só tira pontos. A regra de hoje já evita afirmar o
que não é verdade; falta evitar o excesso no outro sentido.

**Independent Test**: gerar a carta para uma vaga fictícia que lista uma certificação como diferencial, com um
perfil em que essa certificação está "em preparação". A carta não diz "não tenho"; se citar a certificação, diz "em
preparação".

**Acceptance Scenarios**:

1. **Given** uma vaga com a certificação X como diferencial e um perfil sem X, **When** a carta é gerada, **Then** o
   texto não cita X.
2. **Given** a mesma vaga e um perfil com "X (em preparação)", **When** a carta é gerada, **Then** o texto, se citar
   X, diz que está em preparação.
3. **Given** a conferência da carta, **When** o texto traz uma confissão de lacuna ("não tenho", "não possuo",
   "ainda não tenho", "I don't have"), **Then** aparece um aviso de nível "conferir" com o trecho.

---

### User Story 4 - Requisitos classificados sem otimismo (Priority: P2)

A classificação dos requisitos da vaga contra o perfil (tem, sustentado, lacuna), que alimenta a nota, o currículo
para a vaga, a carta e a conferência, passa a tratar dois casos:

- o requisito só bate com um item do perfil marcado "em preparação", "em andamento", "cursando" ou equivalente →
  **não** sai "tem"; sai "sustentado", com a evidência dizendo que está em preparação;
- o requisito pede vários idiomas ("Inglês e Espanhol") e o perfil não tem um deles → **não** sai "sustentado"; sai
  "lacuna", com a evidência dizendo qual idioma falta.

**Why this priority**: a classificação é a base do que a IA pode afirmar. "Tem" para o que está em preparação abre
espaço para o currículo listar a certificação como obtida.

**Independent Test**: com um perfil fictício que lista "Certificação X (em preparação)" e só o inglês, classificar
os requisitos "Certificação X" e "Inglês e Espanhol" e ver "sustentado (em preparação)" e "lacuna (falta:
Espanhol)".

**Acceptance Scenarios**:

1. **Given** um perfil com "Certificação X (em preparação)", **When** a vaga pede a certificação X, **Then** o
   requisito sai "sustentado", com a evidência "em preparação".
2. **Given** um perfil com "Certificação X" sem marca de andamento, **When** a vaga pede X, **Then** o requisito sai
   "tem", como hoje.
3. **Given** um perfil só com inglês, **When** a vaga pede "Inglês e Espanhol", **Then** o requisito sai "lacuna", e
   a evidência diz que falta o espanhol.
4. **Given** um perfil com inglês e espanhol, **When** a vaga pede "Inglês e Espanhol", **Then** o requisito sai
   "tem".

---

### Edge Cases

- Item com número que não é resultado ("Atendimento de 15 a 20 solicitações por dia"): conta como item com
  resultado para a contagem (traz uma medida), e a ordem é decidida pelo que melhor serve ao alvo.
- Item com resultado sem número ("o que permitiu encerrar os cards"): é resultado. A conferência reconhece as marcas
  mais comuns de efeito ("o que permitiu", "reduzindo", "resultando em", "garantindo", "o que levou a"); o que ela
  não reconhecer aparece na contagem para a pessoa julgar, sem bloquear.
- Experiência antiga só com a linha de empresa, cargo e período (sem itens): não entra na contagem.
- Currículo em inglês: as expressões vagas e as marcas de efeito são reconhecidas também em inglês ("responsible
  for", "assisted", "resulting in", "which enabled").
- Contato com e-mail escrito de outro jeito (com espaços, maiúsculas): conta como e-mail se tiver o formato de
  e-mail.
- Requisito com idioma e nível ("Inglês avançado e Espanhol intermediário"): a regra olha os idiomas; o nível segue
  a regra de hoje.
- Vaga em que a ferramenta não separa diferenciais de requisitos: a regra da carta vale para o que a vaga chama de
  desejável, diferencial ou "nice to have"; sem essa marca, vale a regra dos requisitos.
- "Em andamento" em formação (curso ou pós em andamento): segue a mesma regra, "sustentado" com a evidência, nunca
  "tem" para quem pede o título concluído.

## Requirements *(mandatory)*

### Functional Requirements

**Resultado primeiro**

- **FR-001**: O pedido do currículo (base e para a vaga) MUST orientar que, dentro de cada experiência, os itens com
  resultado confirmado venham antes dos itens só de tarefa, sem mudar o texto dos fatos.
- **FR-002**: Com a seção Destaques, o pedido MUST orientar a preferência por itens com número, desde que ligados ao
  alvo.
- **FR-003**: A regra MUST valer também no caminho pelo chat (a skill de currículo), pelas mesmas instruções de
  técnicas que o pedido da página usa.

**Conferência do currículo**

- **FR-004**: A conferência sem IA MUST avisar, no nível "conferir", quando o contato do currículo não tem e-mail.
- **FR-005**: No formato Brasil, a conferência MUST avisar, no nível "conferir", quando o contato não tem telefone.
- **FR-006**: A conferência MUST contar os itens das experiências que descrevem só tarefa (sem número, sem marca de
  efeito reconhecida, ou começando por expressão vaga) e mostrar "N de M itens…" com os trechos, no nível
  "conferir". Sem nenhum item assim, o aviso não aparece.
- **FR-007**: Os avisos novos MUST aparecer onde a conferência já aparece (junto do currículo gerado na página e na
  conferência pela linha de comando, em texto e em JSON), sem mudar a página.

**Carta e respostas**

- **FR-008**: O pedido da carta e das respostas MUST orientar a não mencionar diferencial que a pessoa não tem e a
  nunca escrever confissão de lacuna.
- **FR-009**: O pedido MUST orientar que o que o perfil marca como em preparação ou em andamento só seja citado
  assim.
- **FR-010**: A conferência da carta e das respostas MUST avisar, no nível "conferir", quando o texto traz confissão
  de lacuna, com o trecho.

**Classificação de requisitos**

- **FR-011**: Um requisito que só bate com item do perfil marcado em preparação, em andamento, cursando ou
  equivalente (também em inglês: "in progress", "preparing") MUST sair "sustentado", com a evidência dizendo isso.
- **FR-012**: Um requisito que cita dois ou mais idiomas MUST sair "lacuna" quando o perfil não tem algum deles, com
  a evidência dizendo qual falta; com todos, segue a regra de hoje.

**Limites**

- **FR-013**: Nenhuma mudança desta spec MUST acrescentar fato, número ou resultado ao currículo, à carta ou às
  respostas; a ferramenta só ordena, avisa e classifica.
- **FR-014**: A "caça de números" (pergunta por item sem resultado que vira relato) MUST entrar na lista de desejos,
  não nesta spec.

### Key Entities

- **Item de experiência**: uma linha de uma experiência do currículo. Tem ou não tem resultado (número ou marca de
  efeito); pode começar por expressão vaga.
- **Aviso da conferência**: nível (conferir), mensagem e trecho; os novos são contato sem e-mail, contato sem
  telefone (Brasil), itens só de tarefa e confissão de lacuna.
- **Requisito classificado**: texto do requisito da vaga, situação (tem, sustentado, lacuna) e evidência; ganha a
  marca "em preparação" e o idioma que falta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Num currículo gerado de um perfil em que uma experiência tem itens com número, 100% dessas
  experiências mostram um item com número entre os dois primeiros.
- **SC-002**: 100% dos currículos sem e-mail no contato recebem o aviso; nenhum currículo com contato completo
  recebe aviso de contato.
- **SC-003**: Num conjunto de teste com itens de tarefa e de resultado já marcados à mão, a contagem de itens só de
  tarefa acerta pelo menos 90% dos itens.
- **SC-004**: Nas cartas geradas para vagas com diferenciais que o perfil não tem, nenhuma traz confissão de lacuna,
  e a conferência acusa 100% das confissões dos textos de teste.
- **SC-005**: Requisitos que batem só com item "em preparação" nunca saem "tem"; requisitos de vários idiomas com um
  faltando nunca saem "sustentado".
- **SC-006**: Nenhum currículo, carta ou resposta gerado depois desta spec traz número ou resultado que não esteja no
  perfil ou nos relatos (a conferência de fatos continua passando).

## Assumptions

- A ordem dos itens é pedida à IA, pelas instruções de técnicas que ela já recebe; a ferramenta não reordena o texto
  sozinha depois da resposta. A contagem de itens de tarefa mostra à pessoa o que ficou.
- O telefone só é cobrado no formato Brasil, porque o contato do formato dos Estados Unidos e da Europa já é
  definido pelas regras de formato (a ferramenta não pede telefone onde ele não é costume).
- Os avisos novos não bloqueiam: o veredito "bloquear" continua reservado para fato inventado, lacuna listada como
  competência, cópia do modelo e dado pessoal no formato dos Estados Unidos.
- As listas de expressões vagas, marcas de efeito, confissões de lacuna e marcas de andamento são curtas, em
  português e inglês, e podem crescer depois sem mudar o comportamento.
- Exemplos e testes usam textos fictícios; nada do perfil real da pessoa entra na spec nem nos testes (constituição,
  princípio II).
- A correção da leitura de requisitos dos portais com texto achatado já existe (branch própria) e é pré-requisito da
  regra de competência copiada da vaga, mas não faz parte desta spec.
