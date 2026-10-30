# Feature Specification: Vagas sem análise sempre à vista, com a caixa "Analisadas"

**Feature Branch**: `038-vagas-analisadas` (worktree `../mpt-038-vagas-analisadas`, saída da `master`; o front na
`frontend-react`)

**Created**: 2026-10-29

**Status**: Aprovada em 2026-10-29

**Input**: Pedido do usuário em 29/10/2026. No Relatório de Vagas:
- as vagas sem classificação devem aparecer sempre;
- uma caixa de nome curto, de uma palavra, oculta as vagas ainda sem análise em todas as abas;
- com a caixa desmarcada, as vagas sem análise aparecem em todas as abas, independente do filtro.

**Decisões do usuário (29/10)**:
1. O nome da caixa é **Analisadas**: marcada, mostra só as vagas que já têm nota.
2. Com a caixa desmarcada, a vaga sem nota passa por **todos os filtros, menos a busca por texto**: Senioridade, Modo,
   Nota mínima e Publicada há até.
3. Com a caixa marcada, os **números das abas** e o **"Marcar todas como não seguidas"** consideram só as vagas
   visíveis.
4. A vaga com **nota provisória** (dada sem a descrição completa) conta como analisada.

## Contexto

O Relatório de Vagas tem três abas: Para decidir, Não seguidas e Fora dos critérios. Os filtros são busca por texto,
Senioridade, Modo, Nota mínima e Publicada há até, e ficam guardados no navegador.

A vaga "sem classificação" é a que ainda não tem nota de aderência: ela está esperando a IA, com a descrição pendente
ou com falha na análise. Hoje os filtros a escondem sem a pessoa perceber:
- **Nota mínima** esconde todas, porque elas não têm nota;
- **Senioridade** e **Modo** quase sempre também, porque esses dados vêm da análise. Sem ela, a vaga cai em "não
  informado".

Assim, uma vaga nova pode ficar fora da vista até a IA terminar, e a pessoa não sabe que ela existe.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vaga sem análise sempre à vista (Priority: P1)

Com a caixa **Analisadas** desmarcada, a vaga sem nota aparece nas três abas, mesmo com Senioridade, Modo, Nota mínima
ou Publicada há até ativos. Ela continua com o selo de hoje: aguardando a IA, descrição pendente ou falha. A busca por
texto vale para ela como para as outras.

**Why this priority**: é o centro do pedido: nenhuma vaga nova some sem a pessoa ver.

**Independent Test**: com Nota mínima 70 e uma vaga ainda sem nota em Para decidir, a vaga aparece. As vagas com nota
abaixo de 70 continuam fora.

**Acceptance Scenarios**:

1. **Given** Nota mínima 70 e uma vaga sem nota, **When** a pessoa abre Para decidir, **Then** a vaga sem nota aparece
   e as com nota abaixo de 70 não aparecem.
2. **Given** Senioridade "Sr" e Modo "Remoto" marcados, **When** há vaga sem nota em Fora dos critérios, **Then** ela
   aparece nessa aba.
3. **Given** "Publicada há até 7 dias" e uma vaga sem nota publicada há 30 dias, **When** a pessoa abre a aba, **Then**
   a vaga aparece.
4. **Given** a busca "SQL" e uma vaga sem nota sem "SQL", **When** a pessoa busca, **Then** a vaga não aparece.

---

### User Story 2 - Caixa "Analisadas" (Priority: P1)

Na barra de filtros fica a caixa **Analisadas**, com a dica "Oculta as vagas ainda sem análise". Ela vale assim:
- **Marcada**: as vagas sem nota somem das três abas. A vaga com nota provisória continua.
- **Números e "Marcar todas"**: os números das abas e o "Marcar todas como não seguidas" passam a contar só as vagas
  visíveis.
- **Linha "Mostrando X de Y"**: aparece como nos outros filtros, e "Limpar filtros" desmarca a caixa.
- **Navegador**: a escolha fica guardada, como os outros filtros.

**Why this priority**: é o controle que a pessoa pediu, para quando quiser ver só o que já tem nota.

**Independent Test**: com Analisadas marcada, uma vaga sem nota some de Para decidir, e o número da aba cai em um. O
"Marcar todas" não a marca.

**Acceptance Scenarios**:

1. **Given** Analisadas marcada, **When** a pessoa passa pelas três abas, **Then** nenhuma vaga sem nota aparece.
2. **Given** Analisadas marcada e uma vaga com nota provisória, **When** a pessoa abre a aba, **Then** a vaga aparece.
3. **Given** Analisadas marcada, **When** a pessoa usa "Marcar todas como não seguidas", **Then** só as vagas com nota
   da aba são marcadas.
4. **Given** Analisadas marcada, **When** a pessoa recarrega a página, **Then** a caixa continua marcada.
5. **Given** Analisadas marcada, **When** a pessoa clica em Limpar filtros, **Then** a caixa é desmarcada e as vagas
   sem nota voltam.

### Edge Cases

- **Vaga que ganha nota enquanto a página está aberta**: na próxima leitura das vagas, ela passa a seguir todos os
  filtros como as outras.
- **Falha na análise**: conta como sem nota. Aparece com a caixa desmarcada, com o selo de falha e o "Forçar verificar".
- **Vaga sem nota com nota abaixo de 50**: não existe. A seção recolhida "nota abaixo de 50" continua só com as vagas
  com nota.
- **Aba sem nada visível com a caixa marcada**: aparece a mensagem de hoje para filtros sem resultado, com "Limpar
  filtros".
- **Ordem**: a vaga sem nota vem depois das com nota em "Maior aderência", como hoje.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Com Analisadas desmarcada, a vaga sem nota MUST ignorar os filtros Senioridade, Modo, Nota mínima e
  Publicada há até, nas três abas. A busca por texto MUST valer para ela.
- **FR-002**: Com Analisadas marcada, a vaga sem nota MUST não aparecer em nenhuma das três abas. A vaga com nota
  provisória MUST aparecer.
- **FR-003**: "Sem nota" é a vaga sem nota de aderência: esperando a IA, com a descrição pendente ou com falha. É a
  mesma regra que o selo da vaga já usa.
- **FR-004**: Com Analisadas marcada, os números das abas e o "Marcar todas como não seguidas" MUST considerar só as
  vagas visíveis pela caixa. Os outros filtros não mudam os números, como hoje.
- **FR-005**: A caixa MUST ficar na barra de filtros, com a dica "Oculta as vagas ainda sem análise". Ela MUST ser
  guardada no navegador junto dos outros filtros, entrar na conta de "Mostrando X de Y" e ser desmarcada por "Limpar
  filtros".
- **FR-006**: O README MUST descrever a caixa e a regra das vagas sem nota.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com a caixa desmarcada, 100% das vagas sem nota de uma aba aparecem, com qualquer combinação de
  Senioridade, Modo, Nota mínima e Publicada há até.
- **SC-002**: Com a caixa marcada, nenhuma vaga sem nota aparece nas três abas, e o "Marcar todas" não marca nenhuma
  vaga escondida.
- **SC-003**: Marcar ou desmarcar a caixa é 1 clique, e a escolha continua depois de recarregar a página.
- **SC-004**: O tipo do front confere sem erro, e os testes do projeto continuam passando.

## Assumptions

- A mudança é só na página (`frontend-react`). O servidor já manda a nota e o estado da análise de cada vaga.
- O quadro de candidaturas não muda: as vagas seguidas já passaram pelo Relatório.
- A caixa vale para o Relatório de Vagas, nas três abas. A aba Internacional tem filtros próprios (moeda, visto), que
  não dependem da análise, e fica como está.
