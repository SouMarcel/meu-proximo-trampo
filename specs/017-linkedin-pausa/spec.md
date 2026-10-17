# Feature Specification: Pausa do LinkedIn ajustável

**Feature Branch**: `017-linkedin-pausa` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Colocar o tempo entre as pesquisas do LinkedIn numa variável do .env, algo como
LINKEDIN_TIMELAPSE=5, em segundos. Objetivo: evitar bloqueio."

## Contexto

A busca pública do LinkedIn limita pedidos por rede (IP). Hoje a ferramenta espera um tempo sorteado entre 3 e 7
segundos entre cada pedido ao LinkedIn: as páginas de resultados de cada grupo e as leituras de descrição (até 20 por
busca, spec 015). Esse valor é fixo no código. Quem é bloqueado com frequência (rede compartilhada, VPN, Wi-Fi do
escritório) não tem como espaçar mais os pedidos sem mexer no código.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Espaçar mais os pedidos ao LinkedIn (Priority: P1)

A pessoa foi bloqueada pelo LinkedIn mais de uma vez. Ela põe `LINKEDIN_PAUSA=10` no arquivo `.env`. Na busca
seguinte, a ferramenta avisa no começo que o LinkedIn vai esperar de 10 a 14 segundos entre os pedidos, e espera
mesmo isso. A busca demora mais, e o risco de bloqueio cai.

**Why this priority**: é o pedido inteiro.

**Independent Test**: com `LINKEDIN_PAUSA=10` e respostas do LinkedIn simuladas, rodar uma busca e conferir que
todas as esperas entre pedidos ao LinkedIn ficam entre 10 e 14 segundos, e que o aviso aparece no começo.

**Acceptance Scenarios**:

1. **Given** `LINKEDIN_PAUSA=10` no `.env`, **When** a pessoa busca (página, terminal ou chat), **Then** cada espera
   entre dois pedidos ao LinkedIn é sorteada entre 10 e 14 segundos.
2. **Given** a mesma configuração, **When** a busca começa, **Then** o resumo da busca mostra "LinkedIn: pausa de 10
   a 14 s entre os pedidos (LINKEDIN_PAUSA)".
3. **Given** nenhuma `LINKEDIN_PAUSA`, **When** a pessoa busca, **Then** tudo fica como hoje: de 3 a 7 segundos e sem
   aviso novo.
4. **Given** `LINKEDIN_PAUSA` definida como variável de ambiente do sistema, **When** a pessoa busca, **Then** vale o
   valor do ambiente, que vence o `.env` (como as chaves de API).

---

### User Story 2 - Valor fora do permitido (Priority: P2)

A pessoa escreve um valor que não serve: abaixo do mínimo, acima do máximo ou que não é número. A ferramenta não
quebra e não deixa a pausa abaixo do mínimo: usa o valor permitido mais próximo, ou o padrão, e avisa no começo da
busca.

**Why this priority**: evita que um erro de digitação tire a proteção (princípio VI) ou trave a busca por horas.

**Independent Test**: rodar com `LINKEDIN_PAUSA` igual a `1`, `0`, `-5`, `500`, `abc` e `7,5` e conferir a pausa
usada e o aviso de cada caso.

**Acceptance Scenarios**:

1. **Given** um valor abaixo de 3 (inclusive 0 ou negativo), **When** a busca começa, **Then** a pausa fica de 3 a 7 s e
   o aviso diz que o mínimo é 3 segundos.
2. **Given** um valor acima de 60, **When** a busca começa, **Then** a pausa fica de 60 a 64 s e o aviso diz que o
   máximo é 60 segundos.
3. **Given** um texto que não é número, **When** a busca começa, **Then** vale o padrão (3 a 7 s) e o aviso diz que o
   valor de `LINKEDIN_PAUSA` foi ignorado.
4. **Given** um número com vírgula (`7,5`) ou ponto (`7.5`), **When** a busca começa, **Then** ele é aceito como 7,5
   segundos.

---

### Edge Cases

- **LinkedIn desligado na busca**: a variável é ignorada e não há aviso.
- **LinkedIn em espera de 6 horas** (spec 015): não há pedidos, então a pausa não se aplica. Vale o aviso da espera.
- **Adicionar Vaga por link de vaga ou de post**: é um pedido só; a pausa não se aplica e nada muda.
- **Outras fontes** (Indeed, Gupy, startup.jobs): continuam com a pausa delas, sem mudança.
- **`.env` alterado com o dashboard aberto**: vale na próxima busca, sem reiniciar o servidor.
- **Pausa longa** (ex.: 60 s): uma busca com cerca de 26 pedidos ao LinkedIn leva perto de 30 minutos. O aviso do
  começo traz uma estimativa do tempo de pausa ("cerca de N min só de pausa no LinkedIn").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta MUST ler `LINKEDIN_PAUSA` (segundos) do ambiente ou do `.env`, nessa ordem, como as chaves
  de API, a cada busca.
- **FR-002**: Com um valor válido N, cada espera entre dois pedidos ao LinkedIn na busca MUST ser sorteada entre N e
  N + 4 segundos.
- **FR-003**: N MUST ficar entre 3 e 60. Abaixo de 3 vale 3; acima de 60 vale 60. Valor que não é número é ignorado
  (vale o padrão). Vírgula e ponto são aceitos como separador decimal.
- **FR-004**: Sem a variável, a pausa MUST continuar de 3 a 7 segundos, sem aviso novo.
- **FR-005**: Com a variável presente e o LinkedIn na busca, o começo da busca (página, terminal e chat) MUST mostrar
  a pausa em uso e uma estimativa do tempo total de pausa no LinkedIn. Com valor ajustado ou ignorado, o aviso MUST
  dizer o motivo.
- **FR-006**: A variável MUST valer só para a busca do LinkedIn. Adicionar Vaga (link de vaga ou de post) e as outras
  fontes não mudam.
- **FR-007**: README e a skill buscar-vagas MUST explicar a variável, o mínimo, o máximo e quando usar (bloqueios
  frequentes).

### Key Entities

- **Pausa do LinkedIn**: o mínimo N (segundos) e o intervalo sorteado de N a N + 4; vem de `LINKEDIN_PAUSA` ou do
  padrão 3.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com `LINKEDIN_PAUSA=10`, 100% das esperas entre pedidos ao LinkedIn numa busca simulada ficam entre 10 e
  14 segundos.
- **SC-002**: Sem a variável, a busca dá o mesmo resultado e as mesmas esperas de antes (3 a 7 s).
- **SC-003**: Nenhum valor de `LINKEDIN_PAUSA` faz a pausa ficar abaixo de 3 segundos ou acima de 64.
- **SC-004**: Os valores inválidos testados (`1`, `0`, `-5`, `500`, `abc`) geram cada um o aviso certo e a busca
  segue.

## Assumptions

- O nome `LINKEDIN_PAUSA` segue o padrão do projeto, em português. O pedido falava em "LINKEDIN_TIMELAPSE" como
  exemplo.
- O `.env` passa a guardar também uma configuração que não é chave. A constituição (princípio I) exige que as chaves
  fiquem só no `.env`, mas não proíbe outros valores lá; a escolha do `.env` é da pessoa. O `config.json` e o painel
  não mudam.
- O mínimo de 3 s é a pausa de hoje: a variável só serve para aumentar a proteção (princípio VI). O máximo de 60 s
  evita uma busca de horas por erro de digitação.
- A pausa continua sorteada (intervalo de 4 s), para não ter um ritmo fixo.
- Verificação só no Windows, como nas specs anteriores.
