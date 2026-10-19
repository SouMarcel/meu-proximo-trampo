# Feature Specification: Completar descrições pendentes

**Feature Branch**: `019-completar-descricoes` (worktree saída da `master`; testada na branch pessoal antes da
`master`)

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Existem vagas sem informação na listagem, por quê? Se for o motivo de bloqueio, adicione
um botão para continuar de onde parou a última pesquisa de vagas."

## Contexto

As vagas sem informação são vagas do LinkedIn com **descrição pendente** (spec 015). A busca trouxe cargo, empresa e
link, mas o LinkedIn limitou os pedidos ("excesso de pedidos") antes de a ferramenta ler o texto. Elas ficam no
Relatório sem nota, e hoje só são completadas na **próxima busca completa**.

O que faltou foi só o texto dessas vagas; elas já estão no Relatório. Retomar as consultas da busca interrompida não
traria esse texto, e a spec 015 decidiu que uma busca interrompida recomeça do zero. Por isso o "continuar de onde
parou" vira **completar as descrições pendentes**, sem buscar vagas novas.

## Clarifications

### Session 2026-10-18

- Q: Retomar as consultas da busca ou completar as descrições? → A: Completar as descrições (decisão da pessoa).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Completar as descrições sem buscar de novo (Priority: P1)

O Relatório mostra "N vaga(s) sem descrição…" com o botão **Completar descrições**. A pessoa clica; a ferramenta lê
só essas descrições, com o mesmo limite (20 por vez) e a mesma pausa da busca, mostra o andamento e, no fim, manda as
vagas completadas para a nota de aderência.

**Independent Test**: com 2 vagas pendentes de uma fonte falsa, rodar o completar e conferir que só as 2 descrições
são pedidas (nenhuma consulta de busca), que a marca sai e que as vagas vão para a análise.

**Acceptance Scenarios**:

1. **Given** vagas com descrição pendente, **When** a pessoa abre o Relatório, **Then** vê o aviso com o número e o
   botão.
2. **Given** o clique, **When** a leitura roda, **Then** nenhuma vaga nova é buscada, e só as pendentes são lidas,
   até 20.
3. **Given** a leitura terminou, **Then** as vagas completadas saem de "descrição pendente" e vão para a nota; as que
   sobraram continuam pendentes.
4. **Given** o portal em espera depois de um bloqueio, **Then** o botão não aparece e o aviso mostra "disponível a
   partir das HH:MM".
5. **Given** um bloqueio no meio, **Then** a leitura para sem nova tentativa, a espera é gravada e as restantes
   continuam pendentes.
6. **Given** uma busca rodando, **When** a pessoa clica, **Then** a ferramenta recusa ("as pendentes são lidas pela
   busca").

### User Story 2 - Pelo terminal e pelo chat (Priority: P2)

`vagas.py completar` faz o mesmo. Durante a espera, sai com código 5, sem pedido.

## Requirements *(mandatory)*

- **FR-001**: Completar MUST usar a mesma fila e os mesmos limites da busca (spec 015): as pendentes do Relatório,
  das mais recentes para as mais antigas, no máximo 20 por portal, com a pausa do portal (inclusive
  `LINKEDIN_PAUSA`).
- **FR-002**: Completar MUST NOT buscar vagas novas.
- **FR-003**: Durante a espera de 6 horas, MUST NOT haver pedido ao portal.
- **FR-004**: As vagas completadas MUST ir para a análise automática, como as da busca.
- **FR-005**: A página MUST mostrar o aviso, o botão, o andamento e o resultado; o botão MUST funcionar só no
  computador onde a ferramenta roda.
- **FR-006**: Completar MUST NOT rodar junto com uma busca.
- **FR-007**: README, AGENTS.md e a skill buscar-vagas MUST citar o botão e o comando.

## Success Criteria *(mandatory)*

- **SC-001**: Com descrições pendentes e o portal liberado, um clique completa até 20 sem nenhuma consulta de busca.
- **SC-002**: Na espera, zero pedidos ao portal.
- **SC-003**: Toda vaga completada vai para a nota de aderência.

## Assumptions

- Só o LinkedIn limita descrições hoje; o código vale para qualquer portal que declare `MAX_DESCRICOES` e
  `descrever`.
- Verificação só no Windows.
