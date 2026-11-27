# Feature Specification: Nota sem desperdício de IA

**Feature Branch**: `062-nota-sem-desperdicio` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Regras enxutas para a IA (um arquivo só com o que a nota precisa, que a skill passa a
apontar), juntar o Forçar verificar em grupos pequenos (2 ou 3 vagas por pedido), ordem do pedido que favorece cache,
e a análise automática que não trava depois de um limite de uso (429)."

## Contexto

O pedido de nota de uma vaga tem hoje cerca de 25 mil caracteres (medição de 26/11/2026, com os dados do usuário,
depois da spec 060):

| Parte | Caracteres | % |
|---|---:|---:|
| Regras copiadas da skill `buscar-vagas` (explicação de cada campo + "Como dar a nota") | 9.956 | 40% |
| Perfil | 6.716 | 27% |
| Descrição da vaga | 6.358 | 25% |
| Formato da resposta e instruções fixas | 1.815 | 7% |
| Filtros | 152 | 1% |

As regras são o mesmo texto em todo pedido. No Forçar verificar, que manda uma vaga por pedido (spec 056), elas pesam
mais que a própria vaga. Nos planos gratuitos (a maioria das notas sai do OpenRouter gratuito e do Gemini), o limite que
estoura é o de tokens por minuto: pedidos grandes geram erro 429 e vagas sem nota.

Além disso, a análise automática depois da busca:
- manda os lotes um atrás do outro, sem pausa, e estoura o limite por minuto;
- marca como "já tentadas" **todas** as vagas pendentes antes de chamar a IA; quando um lote falha, nem as dos lotes
  seguintes voltam a ser tentadas até o servidor reiniciar. Sobra para a pessoa o Forçar verificar, vaga a vaga, que é
  o modo mais caro.

A ideia de fundo vem do api-anything: aprender uma vez e reaproveitar até mudar, em vez de reenviar o mesmo texto
longo a cada vez.

## Clarifications

### Session 2026-11-26

- Q: As seções do perfil que não pesam na nota (Contato: e-mail, telefone, links) devem continuar indo no pedido? → A:
  Não; saem do pedido de nota (FR-009). Hoje vão em todo pedido, gastam caracteres e mandam dado pessoal ao provedor.
- Q: Quais metas valem para o tamanho do pedido e para a calibração? → A: pedido de 1 vaga com no máximo 20 mil
  caracteres (medido em 25,7 mil em 26/11); nota mudando no máximo 10 pontos em 90% da amostra (SC-001 e SC-002
  confirmadas).
- Q: A calibração é passo do desenvolvimento ou recurso da ferramenta? → A: comando de desenvolvimento, que mostra a
  comparação sem gravar e roda de novo quando as regras mudarem; sem botão na página (FR-003).
- Q: No Forçar verificar, a vaga pronta espera a leitura das próximas para ir em grupo? → A: sim, a fila lê primeiro e
  manda quando junta 3; se não houver mais vagas para juntar, manda o que tem (FR-004).
- Q: No 429 da análise automática, quanto esperar, quando desistir e o que acontece com as vagas? → A: pausa de 20 s
  entre lotes (`ANALISE_PAUSA`, 5 a 120 s); no 429, espera o pedido pelo provedor ou 60 s e diminui o lote; desiste
  depois de 3 recusas seguidas, e as vagas voltam na próxima busca ou análise (FR-005, FR-006).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Regras enxutas, numa fonte só (Priority: P1)

As regras que a IA precisa para dar a nota (o formato de cada campo, os critérios da nota) passam a ficar num arquivo
próprio, escrito para a IA, sem as explicações voltadas ao assistente do chat. A análise automática, o Forçar
verificar e a skill `buscar-vagas` usam esse mesmo arquivo (a skill aponta para ele, em vez de repetir o texto).

**Why this priority**: é a maior parte fixa do pedido (40%); reduzi-la diminui todo pedido de nota.

**Independent Test**: medir o pedido de nota de uma vaga antes e depois; dar nota a uma amostra de vagas já
analisadas e comparar com as notas antigas.

**Acceptance Scenarios**:

1. **Given** o arquivo de regras enxutas, **When** a ferramenta monta o pedido de nota, **Then** usa esse arquivo e o
   pedido fica menor que hoje (meta na SC-001).
2. **Given** uma amostra de cerca de 30 vagas já analisadas, **When** a nota é refeita com as regras enxutas, **Then**
   as notas e os campos ficam equivalentes aos de antes (critério na SC-002); diferença grande bloqueia a troca.
3. **Given** o assistente do chat analisando vagas pela skill, **When** ele lê a skill, **Then** a skill o leva ao mesmo
   arquivo de regras, sem uma segunda versão para manter.
4. **Given** um perfil com a seção Contato (e-mail, telefone, links), **When** a ferramenta monta o pedido de nota,
   **Then** essa seção não vai no pedido; o resto do perfil vai inteiro.

---

### User Story 2 - Forçar verificar em grupos pequenos (Priority: P2)

Quando a pessoa clica em Forçar verificar em várias vagas, a leitura das descrições continua uma por vez (com a pausa
de cada portal), mas o pedido à IA junta até 3 vagas que já têm descrição, com a pausa `FORCAR_PAUSA` entre pedidos.
A fila lê as descrições em sequência até juntar 3 vagas prontas e só então faz o pedido; se não houver mais vagas para
juntar, manda as que tem (1 ou 2), sem esperar.

**Why this priority**: divide o custo das regras sem voltar ao lote de 10 da spec 056, que estourava o limite.

**Independent Test**: forçar 5 vagas com descrição e ver 2 pedidos à IA (3 + 2) em vez de 5.

**Acceptance Scenarios**:

1. **Given** 5 vagas forçadas com descrição, **When** a fila roda, **Then** a IA recebe no máximo 3 vagas por pedido.
2. **Given** um pedido em grupo que falha, **When** a falha acontece, **Then** só as vagas daquele grupo ficam para
   tentar de novo, com o motivo; as outras seguem.
3. **Given** a vaga que parece mirar a IA (spec 034), **When** ela entra no grupo, **Then** vai num pedido só dela, como
   hoje.

---

### User Story 3 - Análise automática que não trava no limite (Priority: P1)

Depois da busca, a análise automática faz pausa entre os lotes e, quando o provedor recusa por limite de uso (429),
diminui o tamanho do lote e tenta de novo depois de um tempo, sem perder as vagas: só contam como tentadas as vagas de
lotes realmente enviados.

**Why this priority**: é a causa de a pessoa precisar do Forçar verificar logo depois da busca.

**Independent Test**: com uma IA falsa que devolve 429 no primeiro lote, as vagas desse lote e dos seguintes ganham
nota depois, sem reiniciar o servidor.

**Acceptance Scenarios**:

1. **Given** 25 vagas novas, **When** a análise automática roda, **Then** há pausa entre os lotes.
2. **Given** um 429 no primeiro lote, **When** a análise segue, **Then** o lote seguinte é menor e as vagas do lote que
   falhou voltam depois da espera (o tempo pedido pelo provedor ou 60 s), sem reiniciar o servidor.
3. **Given** um erro que não é de limite (chave recusada, sem crédito), **When** ele acontece, **Then** o comportamento
   é o de hoje (reserva da spec 032 e o erro à vista), sem repetir sem fim.

---

### User Story 4 - Ordem do pedido que favorece cache (Priority: P3)

O pedido mantém a parte fixa (regras e perfil) no começo, sempre igual entre pedidos, e a vaga no fim, para os
provedores que reaproveitam um começo de pedido idêntico.

**Why this priority**: ganho que depende do provedor e não é garantido nos gratuitos; custo de implementação baixo.

**Independent Test**: dois pedidos seguidos para vagas diferentes têm o mesmo começo, byte a byte, até o início das
vagas.

**Acceptance Scenarios**:

1. **Given** dois pedidos de nota seguidos, **When** a ferramenta os monta, **Then** o texto até o início das vagas é
   idêntico (nada variável, como data ou contagem, antes das vagas).

### Edge Cases

- Regras enxutas trocadas e uma vaga com nota muito diferente da antiga: a troca não entra até a calibração passar.
- Perfil vazio ou sem IA: o comportamento de hoje.
- Perfil sem a seção Contato, ou com o contato espalhado em outra seção: o pedido leva o perfil como está, sem tentar
  achar e-mail ou telefone no meio do texto.
- Forçar verificar de uma vaga só: vai sozinha, sem esperar grupo.
- 429 repetido: depois de 3 recusas seguidas a análise para e mostra o erro, sem laço infinito; as vagas voltam na
  próxima busca ou análise.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As regras da nota MUST ficar num arquivo próprio, escrito para a IA, usado pela análise automática e pelo
  Forçar verificar.
- **FR-002**: A skill `buscar-vagas` MUST apontar para esse arquivo nas regras da nota, sem repetir o texto.
- **FR-003**: Um comando de desenvolvimento MUST refazer a nota de uma amostra de vagas já analisadas com as regras
  novas e mostrar a comparação com a nota gravada, sem gravar nada; a troca só vai à `master` se o critério da SC-002
  for atendido, e o comando roda de novo sempre que as regras mudarem. Não há botão na página.
- **FR-004**: O Forçar verificar MUST juntar até 3 vagas com descrição por pedido à IA, mantendo a leitura das
  descrições uma por vez (com a pausa de cada portal) e a pausa `FORCAR_PAUSA` entre pedidos. A fila lê primeiro e
  manda depois: o pedido sai quando há 3 vagas prontas ou quando não há mais vagas na fila para juntar (aí vai com 1
  ou 2).
- **FR-005**: A análise automática MUST fazer pausa entre lotes: `ANALISE_PAUSA` no `.env`, padrão 20 s, de 5 a
  120 s.
- **FR-006**: Quando a IA principal e as reservas recusam por limite de uso (429), a análise automática MUST esperar o
  tempo que o provedor pedir (ou 60 s, se ele não disser), diminuir o lote (10 → 5 → 3 → 1) e tentar de novo. Depois
  de 3 recusas seguidas, ela para e mostra o erro; as vagas sem nota voltam sozinhas na próxima busca ou na próxima
  análise, sem reiniciar o servidor. Só contam como tentadas as vagas de lotes que a IA respondeu.
- **FR-007**: O pedido de nota MUST manter idêntico, entre pedidos, todo o texto antes do início das vagas.
- **FR-008**: A documentação (README, AGENTS.md, `.env.exemplo`, `dash/API.md` se mudar) MUST seguir as mudanças.
- **FR-009**: O pedido de nota MUST deixar de fora a seção Contato do perfil (e-mail, telefone, links), que não pesa na
  nota; as outras seções vão inteiras.

### Key Entities

- **Regras da nota**: o texto que diz à IA como preencher cada campo e como dar a nota; uma fonte só.
- **Grupo do Forçar verificar**: até 3 vagas com descrição num pedido.
- **Lote da análise automática**: as vagas de um pedido, com tamanho que diminui num 429.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pedido de nota de uma vaga cai de cerca de 25 mil para no máximo 20 mil caracteres com os dados do
  usuário (regras com pelo menos 50% a menos).
- **SC-002**: Na amostra de calibração, a nota muda no máximo 10 pontos em pelo menos 90% das vagas, e nenhuma vaga
  troca de "fora dos critérios" para dentro (ou o contrário) sem motivo na própria vaga.
- **SC-003**: Forçar 6 vagas com descrição gera no máximo 2 pedidos à IA.
- **SC-004**: Depois de uma busca com 429 no primeiro lote, 100% das vagas com descrição ganham nota sem a pessoa forçar
  e sem reiniciar o servidor.

## Assumptions

- O formato da resposta (o JSON de cada vaga) não muda; só o texto das regras.
- A calibração usa a IA configurada no `.env` de quem roda o comando (no desenvolvimento, a branch pessoal) e custa
  chamadas; quem usa a ferramenta recebe as regras já calibradas.
- O cache do provedor é um ganho possível, não garantido; nada depende dele.
- Ficam fora: o perfil compacto (resumo do perfil por IA) e a receita da página própria de empresa, que seguem na lista
  de desejos.
