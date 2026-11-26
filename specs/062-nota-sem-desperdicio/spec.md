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

---

### User Story 2 - Forçar verificar em grupos pequenos (Priority: P2)

Quando a pessoa clica em Forçar verificar em várias vagas, a leitura das descrições continua uma por vez (com a pausa
de cada portal), mas o pedido à IA junta até 3 vagas que já têm descrição, com a pausa `FORCAR_PAUSA` entre pedidos.
Uma vaga sozinha vai sozinha, sem esperar as outras além de um tempo curto.

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
   falhou voltam depois de um intervalo, sem reiniciar o servidor.
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
- Forçar verificar de uma vaga só: vai sozinha, sem esperar grupo.
- 429 repetido por muito tempo: a análise para de tentar depois de um limite e mostra o erro, sem laço infinito.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As regras da nota MUST ficar num arquivo próprio, escrito para a IA, usado pela análise automática e pelo
  Forçar verificar.
- **FR-002**: A skill `buscar-vagas` MUST apontar para esse arquivo nas regras da nota, sem repetir o texto.
- **FR-003**: Antes de trocar as regras, a ferramenta MUST refazer a nota de uma amostra de vagas já analisadas e
  mostrar a comparação; a troca só entra se o critério da SC-002 for atendido.
- **FR-004**: O Forçar verificar MUST juntar até 3 vagas com descrição por pedido à IA, mantendo a leitura das
  descrições uma por vez e a pausa `FORCAR_PAUSA` entre pedidos.
- **FR-005**: A análise automática MUST fazer pausa entre lotes (configurável no `.env`, com padrão e faixa como as
  outras pausas).
- **FR-006**: Num 429, a análise automática MUST diminuir o lote (10 → 5 → 3 → 1) e tentar de novo depois de um
  intervalo; só contam como tentadas as vagas de lotes enviados.
- **FR-007**: O pedido de nota MUST manter idêntico, entre pedidos, todo o texto antes do início das vagas.
- **FR-008**: A documentação (README, AGENTS.md, `.env.exemplo`, `dash/API.md` se mudar) MUST seguir as mudanças.

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
- A calibração usa a IA configurada pela pessoa e só roda com o clique ou o comando dela (custa chamadas).
- O cache do provedor é um ganho possível, não garantido; nada depende dele.
- Ficam fora: o perfil compacto (resumo do perfil por IA) e a receita da página própria de empresa, que seguem na lista
  de desejos.
