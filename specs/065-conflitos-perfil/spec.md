# Feature Specification: Conflitos do Meu perfil mais claros e seguros

**Feature Branch**: `065-conflitos-perfil` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Conflitos do Meu perfil mais claros e seguros. (1) Na aba Conflitos, depois que a pessoa
escolhe e clica em Continuar, os conflitos já resolvidos ficam recolhidos num resumo "N resolvidos (mudar)" em vez de
continuarem todos abertos; só os sem escolha ficam à vista. (2) O valor de cada opção de conflito vem limpo: hoje a IA
põe comentário junto do valor (ex.: "04/2018 (no perfil atual, uma entrada única …)"), e esse comentário entraria
literalmente no perfil.md; o comentário passa a ser uma nota separada, mostrada na tela mas fora do valor gravado. (3)
Na Revisão, aviso quando o rascunho do assistente é mais antigo que o perfil.md gravado (o perfil mudou depois, por
exemplo por relatos incorporados ou edição), dizendo que gravar substitui o perfil e o que se perderia, com a opção de
refazer o rascunho a partir do perfil atual. Ferramenta pública (master): nada específico de uma pessoa."

## Contexto

O assistente do Meu perfil (spec de primeiros passos) monta um rascunho do perfil a partir dos materiais da pessoa e do
perfil atual. Quando duas fontes discordam num valor (uma data, um cargo, o nome de um curso), o rascunho guarda um
conflito, e a pessoa escolhe a opção certa na aba Conflitos. As escolhas ficam guardadas e só entram no perfil quando a
pessoa clica em Gravar, na Revisão.

Três problemas apareceram no uso:

1. **Os conflitos resolvidos continuam todos abertos.** Depois de escolher e clicar em Continuar, a pessoa volta à aba
   e vê a mesma lista inteira, com as opções marcadas. Parece que nada foi feito, e é difícil achar o que ainda falta.
2. **A IA põe comentário dentro do valor.** Uma opção chega como "04/2018 (no perfil atual, uma entrada única
   'Analista de …')" ou "12/2016 (conclusão do curso em 15/12/2016)". O valor escolhido substitui o marcador no texto do
   perfil como está, e o comentário entraria no cargo, na data ou na formação gravada.
3. **Gravar um rascunho antigo apaga o que mudou depois.** O rascunho é uma foto do momento em que foi montado. Se o
   perfil mudou depois (relatos incorporados, revisão do perfil, edição à mão ou pelo assistente no chat), gravar o
   rascunho substitui o perfil inteiro e tira essas mudanças. A versão anterior fica guardada, mas a pessoa não é
   avisada de forma clara antes de gravar, e a lista "o que muda" pode passar despercebida.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Não perder o que entrou no perfil depois do rascunho (Priority: P1)

A pessoa montou um rascunho dias atrás, depois incorporou relatos e editou o perfil. Ela volta ao assistente, chega à
Revisão e, antes de gravar, vê um aviso: o perfil mudou depois que este rascunho foi montado, gravar substitui o perfil,
e estes itens sairiam (a lista). Ela escolhe entre refazer o rascunho a partir do perfil atual, gravar mesmo assim ou
sair sem gravar.

**Why this priority**: é a única das três que pode tirar do perfil fatos que a pessoa já confirmou. As outras duas
incomodam ou sujam o texto; esta apaga trabalho.

**Independent Test**: montar um rascunho, depois mudar o perfil gravado (acrescentar um item numa experiência), abrir a
Revisão e conferir que o aviso aparece com o item novo na lista do que sairia, e que Gravar só acontece depois de a
pessoa escolher "gravar mesmo assim".

**Acceptance Scenarios**:

1. **Given** um rascunho montado antes da última mudança do perfil, **When** a pessoa abre a Revisão, **Then** vê o
   aviso com a data do rascunho, a data da última mudança do perfil e a lista dos itens do perfil atual que não estão
   no texto que seria gravado.
2. **Given** o aviso na tela, **When** a pessoa clica em Gravar, **Then** a ferramenta pede confirmação explícita
   ("gravar mesmo assim") antes de substituir o perfil.
3. **Given** o aviso na tela, **When** a pessoa escolhe refazer o rascunho, **Then** um rascunho novo é montado com os
   mesmos materiais e o perfil atual como fonte, e as escolhas de conflitos que continuam valendo (mesmo campo e mesmo
   valor entre as opções) já vêm marcadas.
4. **Given** um rascunho montado depois da última mudança do perfil, ou nenhum perfil gravado ainda, **When** a pessoa
   abre a Revisão, **Then** nenhum aviso aparece e o Gravar funciona como hoje.

---

### User Story 2 - Valor do conflito sem comentário (Priority: P2)

Ao escolher uma opção num conflito, a pessoa vê o valor limpo ("04/2018") e, ao lado, em letra menor, a observação da
IA ("no perfil atual, uma entrada única…"). O que vai para o perfil é só o valor.

**Why this priority**: evita texto estranho no perfil e, a partir dele, no currículo. Não apaga nada, mas o erro só é
notado depois de gravado.

**Independent Test**: montar um rascunho com fontes que discordam numa data em que a IA explica a diferença; conferir
que a opção mostra valor e observação separados e que, depois de escolher e gravar, a data no perfil não tem a
observação.

**Acceptance Scenarios**:

1. **Given** uma opção de conflito com observação, **When** a aba Conflitos a mostra, **Then** o valor aparece como
   texto principal e a observação separada, com aparência de nota.
2. **Given** a pessoa escolheu essa opção, **When** o perfil é montado na Revisão, **Then** o campo recebe só o valor.
3. **Given** um conflito na data de início ou de fim de uma experiência, **When** o valor escolhido traz texto além
   da data, **Then** o Diagnóstico aponta o campo para a pessoa conferir, como já faz com datas sem mês.

---

### User Story 3 - Conflitos resolvidos saem da aba (Priority: P3)

A pessoa resolve os conflitos e clica em Continuar. Quando volta à aba Conflitos, vê só os que ainda estão sem
escolha. Os resolvidos não aparecem mais: a escolha está guardada e vai para o perfil; para corrigir, a pessoa edita o
texto na Revisão.

**Why this priority**: melhora a clareza. Nada se perde sem ela, porque as escolhas já ficam guardadas.

**Independent Test**: com conflitos todos escolhidos, clicar em Continuar, voltar à aba e conferir que nenhum conflito
aparece, só a frase de que todos estão resolvidos.

**Acceptance Scenarios**:

1. **Given** conflitos com escolha feita antes de a pessoa entrar na aba, **When** a aba abre, **Then** eles não
   aparecem, e os sem escolha aparecem abertos.
2. **Given** a pessoa está escolhendo na aba, **When** marca uma opção, **Then** o conflito continua à vista até ela
   sair da aba (para corrigir um clique errado sem procurar).
3. **Given** todos os conflitos resolvidos, **When** a aba abre, **Then** aparece a frase de que todos estão
   resolvidos e o botão Continuar.

---

### Edge Cases

- Rascunho de antes desta mudança, sem a data em que foi montado: a Revisão compara o texto que seria gravado com o
  perfil atual e avisa sempre que algum item do perfil atual sairia, sem citar datas.
- Rascunho com valores já sujos (montado antes desta mudança): não são limpos sozinhos; o Diagnóstico aponta as datas
  que não são datas (US2, cenário 3) e o aviso da Revisão oferece refazer o rascunho.
- Refazer o rascunho sem IA ligada: o aviso diz que é preciso ligar uma IA para refazer, e as outras duas opções
  continuam disponíveis.
- A IA não separa a observação (manda tudo no valor): o valor fica como veio e o Diagnóstico aponta o campo de data
  que não é data; nada é cortado por adivinhação.
- O perfil muda enquanto a Revisão está aberta (por exemplo, um relato incorporado em outra aba): o Gravar recusa e
  pede para ver de novo o que muda. Hoje isso não é conferido; passa a ser (FR-012).
- Os relatos que divergem do perfil (spec 060), que também aparecem na aba Conflitos, seguem o próprio fluxo de hoje;
  o recolhimento desta spec vale para os conflitos entre fontes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O rascunho MUST guardar quando foi montado.
- **FR-002**: Na Revisão, a ferramenta MUST avisar quando o perfil gravado mudou depois que o rascunho foi montado,
  mostrando as duas datas e a lista dos itens do perfil atual que não estariam no texto gravado.
- **FR-003**: Sem data do rascunho, a ferramenta MUST avisar sempre que gravar tiraria algum item do perfil atual.
- **FR-004**: Com o aviso na tela, gravar MUST pedir uma confirmação explícita a mais; sem ela, o perfil não muda.
- **FR-005**: O aviso MUST oferecer refazer o rascunho com os mesmos materiais e o perfil atual como fonte, usando a
  IA escolhida pela pessoa, e manter marcadas as escolhas de conflito que ainda valem (mesmo campo e mesmo valor).
- **FR-006**: Cada opção de conflito MUST ter valor e observação separados; o pedido à IA MUST dizer que o valor é só
  o dado (uma data, um nome, um cargo) e que a explicação vai na observação.
- **FR-007**: Só o valor MUST entrar no perfil quando a opção é escolhida; a observação aparece só na tela.
- **FR-008**: O Diagnóstico MUST apontar data de início ou de fim de uma experiência cujo valor escolhido num conflito
  não é só uma data (traz texto a mais).
- **FR-009**: Na aba Conflitos, os conflitos com escolha feita antes de a pessoa abrir a aba MUST NOT aparecer (decisão
  da pessoa em 27/11: não há motivo para manter o histórico dos resolvidos; corrigir, no texto da Revisão); os sem
  escolha MUST aparecer abertos.
- **FR-010**: Um conflito escolhido durante a visita à aba MUST continuar aberto até a pessoa sair dela.
- **FR-011**: Nada desta spec MUST gravar o perfil sem o clique da pessoa em Gravar (constituição IV e V); a versão
  anterior do perfil continua guardada a cada gravação, como hoje.
- **FR-012**: Gravar pela Revisão MUST recusar quando o perfil gravado mudou depois que a Revisão mostrou o que muda,
  pedindo para ver de novo.

### Key Entities

- **Rascunho do perfil**: o perfil proposto pelo assistente, com a fonte de cada item, os conflitos e, a partir desta
  spec, a data em que foi montado.
- **Conflito**: um campo em que as fontes discordam, com as opções (cada uma com valor, observação e fonte) e a escolha
  da pessoa.
- **Perfil gravado**: o perfil de carreira da pessoa, com a data da última mudança por qualquer caminho (assistente,
  relatos, revisão, edição).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos casos de teste em que o perfil mudou depois do rascunho, a pessoa vê o aviso e a lista do que
  sairia antes de qualquer gravação, e nenhuma gravação acontece sem a confirmação a mais.
- **SC-002**: Nenhum campo do perfil gravado a partir de um rascunho novo traz a observação da IA junto com o valor nos
  casos de teste com opções comentadas.
- **SC-003**: Ao voltar à aba Conflitos com tudo resolvido, a pessoa vê numa só tela que não falta nada, sem precisar
  rolar a lista de conflitos.
- **SC-004**: A aba Conflitos nunca mostra um conflito resolvido em visita anterior.

## Assumptions

- O aviso da Revisão compara o perfil atual com o texto que seria gravado item a item (linhas de lista e títulos),
  como a lista "o que muda" que a Revisão já tem; não é preciso entender o significado de cada item.
- "Data da última mudança do perfil" vale para qualquer caminho que grave o perfil, inclusive a edição à mão fora da
  ferramenta.
- Refazer o rascunho é um pedido novo à IA, com o custo e a espera de hoje; a ferramenta não tenta juntar o rascunho
  antigo com o perfil atual sem IA.
- Rascunhos antigos não são corrigidos automaticamente; o caminho para eles é o aviso e o Diagnóstico.
- A página é o front React (`frontend-react`, montado pela Action); a parte de tela desta spec vai para essa branch, e
  a parte de servidor e do pedido à IA vai para a `master`.
