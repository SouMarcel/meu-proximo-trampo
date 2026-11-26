# Feature Specification: Perfil como base, relato só na vaga dele, e relatos incorporados com conflitos

**Feature Branch**: `060-relatos-por-vaga` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Só o perfil.md vai para a IA como base; os relatos entram depois de incorporados. Na
vaga em que o relato foi criado, vale perfil + relato da vaga. Relatos para incorporar ficam em Seus relatos (com
ícone de aviso); os que derem problema vão para Conflitos (com ícone de aviso) e os demais entram no perfil. A aba
Currículo base vira 'Extração perfil - currículo', sem os campos de currículo PT/EN."

## Contexto

Hoje todo pedido à IA leva o perfil.md mais todos os relatos ainda não levados ao perfil (os relatos são o que a
pessoa contou com as próprias palavras na candidatura assistida e na análise de reprovação, spec 035). Isso pesa em
todo pedido (a nota de cada vaga leva os relatos de todas as outras) e mistura fatos de uma candidatura nas outras.
Os relatos entram no perfil por uma revisão item a item (spec 050), e a aba Seus relatos mostra os pendentes e os já
levados misturados.

A aba "Currículo base" passa a ideia errada de que os currículos das vagas saem dela; eles saem do perfil.md. Os
campos "Em português"/"Em inglês" marcam arquivos que a pessoa enviou, e a candidatura assistida lê dados desse
arquivo, não do perfil.

A emenda 5.6.0 da constituição (princípio IV) registra a regra nova dos relatos.

## Clarifications

### Session 2026-11-26

- Q: O que vai para a IA? → A: Nos pedidos gerais (nota das vagas, análises do perfil, currículos sem vaga,
  conferência sem vaga), só o perfil.md. Nos pedidos de uma vaga (currículo da vaga, carta, respostas, candidatura
  assistida, entrevista, análise de reprovação), o perfil.md mais os relatos daquela vaga que ainda não entraram no
  perfil.
- Q: Como os relatos entram no perfil? → A: A pessoa clica em Incorporar. A IA analisa: o que encaixa sem contradizer
  o perfil entra direto (ela vê o que entrou e pode desfazer; a versão anterior do perfil fica guardada); o que
  contradiz o perfil ou não tem lugar claro (ex.: em qual cargo aconteceu) vai para a aba Conflitos e segue a
  resolução de lá. Sem IA, o relato espera; o texto cru não vai mais para o perfil.
- Q: O que a aba Seus relatos mostra? → A: É uma caixa de entrada: os relatos ainda fora do perfil, cada um com
  Incorporar e Excluir, e um ícone de aviso na aba quando há algum. Os incorporados ficam numa subseção no fim, fechada
  por padrão.
- Q: A aba Conflitos mostra o quê? → A: Além das divergências entre os materiais (hoje), as divergências entre
  relatos e perfil, com um ícone de aviso na aba quando há alguma.
- Q: E o currículo base? → A: A aba vira "Extração perfil - currículo": gera currículos sem uma vaga, a partir do
  perfil. Saem os campos de currículo em português e em inglês. Cada vaga mostra o currículo geral mais recente do
  idioma dela (sem contar o Completo, que é de consulta). Quando o perfil muda depois dele, a aba recomenda gerar de
  novo o Completo e o de até 2 páginas.
- Q: Um perfil por idioma? → A: Não. Um perfil só; o currículo em inglês sai traduzido do perfil na hora de gerar.
- Q: A candidatura assistida lê de onde? → A: Do perfil.md.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cada pedido leva só o que é dele (Priority: P1)

A nota das vagas, as análises do perfil e os currículos gerais usam só o perfil.md. O currículo, a carta, as
respostas, a entrevista e a análise de reprovação de uma vaga usam o perfil.md mais os relatos dessa vaga que ainda
não entraram no perfil.

**Why this priority**: é a regra central; reduz o tamanho de todo pedido à IA e evita que um fato contado numa
candidatura apareça em outra.

**Independent Test**: com um relato pendente da vaga A, gerar a carta da vaga A (o relato vai no pedido) e a da vaga
B (não vai); pedir a nota de uma vaga qualquer (não vai).

**Acceptance Scenarios**:

1. **Given** relatos pendentes das vagas A e B, **When** a ferramenta pede a nota de qualquer vaga, **Then** o pedido
   leva só o perfil.md.
2. **Given** um relato pendente da vaga A, **When** a pessoa gera a carta, as respostas, o currículo ou a preparação
   de entrevista da vaga A, **Then** o pedido leva o perfil.md e esse relato; os relatos da vaga B não vão.
3. **Given** um relato já incorporado, **When** qualquer pedido é feito, **Then** o fato vai pelo perfil.md (que já
   o contém) e o relato não vai repetido.
4. **Given** a vaga A foi juntada a outra (vagas repetidas, spec 058), **When** a pessoa gera a carta da vaga que
   ficou, **Then** os relatos da vaga A também valem.

---

### User Story 2 - Incorporar relatos, com conflitos (Priority: P1)

Em Meu perfil → Seus relatos, a pessoa marca um ou mais relatos e clica em Incorporar. A IA propõe onde cada fato
entra no perfil (como hoje na revisão da spec 050). O que não contradiz o perfil entra direto: a página mostra
"Entrou no perfil: …" com Desfazer. O que contradiz o perfil ou não tem lugar claro vai para a aba Conflitos, onde a
pessoa escolhe (manter o perfil, usar o relato ou escrever a correção) e grava. Cada relato sai da caixa de entrada
quando todos os fatos dele foram resolvidos.

**Why this priority**: é como os relatos chegam à base única; sem isso, eles ficariam presos à vaga para sempre.

**Independent Test**: com dois relatos, um que encaixa sem conflito e outro que contradiz uma data do perfil,
incorporar os dois: o primeiro entra no perfil e sai da caixa; o segundo aparece em Conflitos com as duas versões.

**Acceptance Scenarios**:

1. **Given** um relato que encaixa sem contradição, **When** a pessoa clica em Incorporar, **Then** o item entra no
   perfil.md, a versão anterior fica guardada, a página mostra o que entrou e o relato vai para a subseção dos
   incorporados.
2. **Given** um relato que contradiz o perfil, **When** a pessoa incorpora, **Then** a divergência aparece em
   Conflitos (ícone de aviso na aba) e o relato continua na caixa de entrada até ela decidir.
3. **Given** a pessoa decide o conflito em Conflitos e grava, **When** a gravação termina, **Then** o perfil muda
   como ela escolheu, o aviso some e o relato vai para os incorporados.
4. **Given** a pessoa clica em Desfazer logo depois de incorporar, **When** a ação termina, **Then** o perfil volta à
   versão anterior e os relatos voltam para a caixa de entrada.
5. **Given** a IA está desligada, **When** a pessoa clica em Incorporar, **Then** nada muda no perfil e a página diz
   que é preciso ligar uma IA; o relato continua na caixa.
6. **Given** o perfil mudou por outro caminho entre a análise e a gravação, **When** a pessoa grava um conflito,
   **Then** a ferramenta recusa e pede para incorporar de novo (como hoje na revisão).

---

### User Story 3 - Seus relatos como caixa de entrada (Priority: P2)

A aba Seus relatos mostra no topo os relatos fora do perfil (com editar, Excluir e Incorporar) e, no fim, uma
subseção "Relatos incorporados (N)", fechada por padrão, só de leitura, com Apagar. A aba ganha um ícone de aviso
quando há relato fora do perfil; a aba Conflitos ganha o ícone quando há divergência de relato esperando decisão.

**Why this priority**: deixa claro o que falta fazer; depende da US2 para esvaziar a caixa.

**Independent Test**: com 7 relatos pendentes e 5 incorporados, a aba mostra 7 no topo, a subseção fechada com 5 e o
ícone de aviso na aba.

**Acceptance Scenarios**:

1. **Given** relatos pendentes, **When** a pessoa abre Meu perfil, **Then** a aba Seus relatos tem o ícone de aviso.
2. **Given** nenhum relato pendente, **When** a pessoa abre Meu perfil, **Then** a aba não tem o ícone e o topo diz
   que não há relatos fora do perfil.
3. **Given** a subseção dos incorporados, **When** a pessoa abre a aba, **Then** ela vem fechada; ao abrir, mostra a
   pergunta, o relato, a vaga e a data, sem Incorporar.
4. **Given** a pessoa apaga um relato incorporado, **When** a ação termina, **Then** ele some da lista e o perfil.md
   não muda.

---

### User Story 4 - Extração perfil - currículo (Priority: P2)

A aba "Currículo base" vira "Extração perfil - currículo". Ela gera currículos sem uma vaga, a partir do perfil
(português ou inglês, Completo ou até N páginas). Saem os campos "Em português" e "Em inglês". Cada vaga mostra, no
item Currículo, o currículo geral mais recente do idioma dela (sem contar o Completo; se só houver o Completo, ele
vale). Quando o perfil foi gravado depois do currículo geral mais recente, a aba mostra o aviso de gerar de novo o
Completo e o de até 2 páginas. A candidatura assistida lê os dados do perfil.md.

**Why this priority**: alinha a página com a regra (o perfil é a base); não muda o que vai para a IA.

**Independent Test**: gerar um currículo geral em português; abrir uma vaga nacional e ver esse currículo no item
Currículo; incorporar um relato e ver o aviso na aba.

**Acceptance Scenarios**:

1. **Given** dois currículos gerais em português (um de 2 páginas, depois um Completo), **When** a pessoa abre uma
   vaga nacional, **Then** o item Currículo mostra o de 2 páginas.
2. **Given** um currículo geral em inglês, **When** a pessoa abre uma vaga internacional, **Then** o item Currículo
   mostra o em inglês.
3. **Given** o perfil foi gravado depois do currículo geral mais recente, **When** a pessoa abre a aba, **Then** ela vê
   o aviso de gerar de novo, com atalho para gerar.
4. **Given** a candidatura assistida propõe respostas, **When** ela busca dados da pessoa, **Then** usa o perfil.md e
   não um arquivo de currículo.
5. **Given** a análise de reprovação de uma vaga sem currículo próprio, **When** ela precisa do currículo enviado,
   **Then** usa o currículo geral mais recente do idioma da vaga.

### Edge Cases

- Relato sem vaga (registro antigo): vale como pendente na caixa de entrada; não vai a nenhum pedido até ser
  incorporado.
- Relato da vaga que foi removida do quadro: continua na caixa de entrada (é fato da pessoa).
- Incorporar com o perfil vazio: a página pede para montar o perfil antes.
- A IA responde sem itens para um relato (opinião, pedido): o relato vai para os incorporados com a marca "sem fato
  para o perfil" e não muda o perfil.
- Pessoa sem currículo geral em nenhum idioma: o item Currículo da vaga oferece gerar um.
- Configuração antiga com o currículo marcado (`curriculo_base` no config): continua sendo lida só se não houver
  nenhum currículo geral gerado, para não deixar a vaga sem currículo na transição.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Os pedidos gerais à IA (nota das vagas, análises do perfil, requisitos x perfil, currículos sem vaga e
  conferência sem vaga) MUST levar só o perfil.md, sem relatos pendentes.
- **FR-002**: Os pedidos de uma vaga (currículo, carta, verificação de carta, respostas, candidatura assistida,
  entrevista e análise de reprovação) MUST levar o perfil.md mais os relatos pendentes daquela vaga (pelo id dela e
  pelos ids das vagas juntadas a ela).
- **FR-003**: O pedido do currículo Completo MUST falar em "todos os fatos do perfil" (sem "e dos relatos").
- **FR-004**: Incorporar MUST pedir à IA onde cada fato entra (revisão da spec 050) e gravar direto no perfil.md os
  itens sem divergência, guardando a versão anterior, marcando como incorporados os relatos cujos fatos foram todos
  aplicados e mostrando à pessoa o que entrou.
- **FR-005**: As divergências MUST ficar numa proposta aberta, mostrada na aba Conflitos, com as escolhas de hoje
  (perfil, relato ou correção); gravar aplica a escolha e marca os relatos resolvidos.
- **FR-006**: Desfazer MUST voltar o perfil.md à versão anterior à incorporação e devolver os relatos à caixa de
  entrada, se o perfil não tiver mudado desde então.
- **FR-007**: Sem IA, Incorporar MUST não mudar o perfil e dizer que é preciso uma IA; o caminho que colava o relato
  cru na seção "Relatos" do perfil deixa de existir na página.
- **FR-008**: A aba Seus relatos MUST mostrar os pendentes no topo e os incorporados numa subseção fechada por padrão;
  a aba MUST ter um ícone de aviso quando há pendentes, e a aba Conflitos quando há divergência de relato aberta.
- **FR-009**: A aba "Currículo base" MUST se chamar "Extração perfil - currículo" e não ter os campos de currículo em
  português e em inglês.
- **FR-010**: O item Currículo da vaga, a análise de reprovação (reserva) e a análise internacional ("tem currículo em
  inglês?") MUST usar o currículo geral mais recente do idioma, sem contar o Completo quando houver outro.
- **FR-011**: A aba MUST avisar quando o perfil foi gravado depois do currículo geral mais recente, recomendando gerar
  de novo o Completo e o de até 2 páginas.
- **FR-012**: A candidatura assistida MUST ler os dados da pessoa do perfil.md, não de um arquivo de currículo.
- **FR-013**: A documentação (README, AGENTS.md, contrato da API, skills que citam relatos) MUST seguir a regra nova.

### Key Entities

- **Relato**: o que a pessoa contou, com pergunta, texto, vaga (id, cargo, empresa), data e situação (pendente ou
  incorporado).
- **Proposta de incorporação**: os itens que a IA propôs, separados em aplicados e divergências abertas; guarda a
  versão do perfil de quando foi feita.
- **Currículo geral**: currículo gerado sem vaga, com idioma, páginas (ou Completo) e data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pedido da nota de uma vaga fica do tamanho do perfil mais as regras, sem os relatos (no perfil do
  usuário, hoje cerca de 21 mil caracteres de parte fixa; depois, sem os cerca de 4 mil dos relatos pendentes).
- **SC-002**: Nenhum relato de uma vaga aparece no pedido de outra vaga (verificado nos pedidos montados em teste).
- **SC-003**: Um relato sem conflito chega ao perfil em 1 clique (Incorporar), com o que entrou à vista.
- **SC-004**: 100% das divergências entre relato e perfil aparecem em Conflitos antes de mudar o perfil.
- **SC-005**: Toda vaga com currículo geral do seu idioma mostra o arquivo no item Currículo sem a pessoa marcar nada.

## Assumptions

- A revisão da spec 050 (pedido à IA, conferência sem IA, aplicar itens, versão anterior guardada) é reaproveitada;
  muda o fluxo da página (aplica direto o que não tem divergência).
- "Relatos da vaga" são os relatos cujo `vaga.id` é a vaga ou uma das vagas juntadas a ela.
- O idioma da vaga segue a área: nacional → português; internacional → inglês.
- Os arquivos que a pessoa enviou em Materiais continuam servindo para montar o perfil; só deixam de ser "o currículo
  da vaga".
