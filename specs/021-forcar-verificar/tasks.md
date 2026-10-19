---

description: "Tarefas da feature 021: Forçar verificar a nota de uma vaga (Windows)"
---

# Tasks: Forçar verificar a nota de uma vaga

**Input**: Design documents from `/specs/021-forcar-verificar/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/forcar-verificar.md, quickstart.md

**Tests**: `unittest` sem rede e sem IA de verdade (constituição); o resto pelo quickstart.

**Organization**: por história (US1–US3). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US3)

---

## Phase 1: Setup

- [X] T001 Rodar `python -m unittest discover -s tests` na worktree e anotar quantos testes passam antes da mudança

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 `dash/banco.py`: `validar_analise` aceita `nota_sem_descricao` (bool, só com `analise_status == "feita"`);
  `aplicar_analises` tira `nota_sem_descricao` do documento quando a análise não traz a marca
- [X] T003 `dash/analise.py`: `Fila` com `_forcadas` (conjunto), `falhas` (dict), `forcar(vid) -> bool` (False sem
  IA; apaga a falha anterior; não duplica) e `verificando() -> list[str]`

**Checkpoint**: estrutura pronta; a rodada ainda não trata as forçadas

---

## Phase 3: User Story 1 - Pedir a nota de uma vaga sem nota (Priority: P1) 🎯 MVP

**Goal**: o botão manda só aquela vaga para a IA e o cartão mostra "verificando…", a nota ou o erro.

**Independent Test**: quickstart.md cenário 1 e cenário 2, passos 2 e 6.

- [X] T004 [US1] `dash/analise.py`: `_rodar` processa primeiro as forçadas (`banco.obter`; vaga sumida ou com nota sem
  a marca → sai; uma chamada a `analisar`; ids sem nota → `falhas[id]` com o motivo: erro da IA, vaga não devolvida
  ou `sem_dados`), tira cada id de `_forcadas` no fim, e depois as automáticas sem as forçadas desta rodada
- [X] T005 [US1] `dash/servidor.py`: `POST /api/vagas/<id>/analisar` antes de `_id_da_rota` (só deste computador;
  202/409/404 do contrato); `GET /api/versao` com `verificando` e `falhas`
- [X] T006 [US1] `dash/dashboard.html`: `S.verificando`/`S.falhas` em `conferir()`; botão `[data-forcar]` "Forçar
  verificar" numa linha embaixo dos botões de decisão em `relItemHTML` (vaga sem nota ou com `nota_sem_descricao`,
  triagem `pendente` ou `fora`); "Verificando…" desligado com a dica do tempo; dica com o motivo da falha; clique com
  `API.send("POST", …)` e toast; estilo da linha nova
- [X] T007 [P] [US1] `tests/test_forcar.py`: `Fila.forcar` com `analisar` substituído (só a forçada vai para a IA, sem
  duplicar, vaga já tentada pela fila automática vai de novo, falha da IA e vaga não devolvida em `falhas`, nova
  tentativa limpa a falha, vaga com nota sai sem chamar a IA); rota com servidor de teste como em
  `tests/test_post.py` (202, 404, 409 com nota, 403 de outro computador) e `/api/versao` com os campos novos

**Checkpoint**: vaga "sem nota" com descrição ganha a nota pelo botão

---

## Phase 4: User Story 2 - Vaga com descrição pendente (Priority: P2)

**Goal**: lê a descrição (um pedido, fora da espera e da busca) ou dá a nota sem a descrição, com a marca.

**Independent Test**: quickstart.md cenário 2, passos 3 e 4.

- [X] T008 [US2] `vagas.py`: `descrever_uma(vid)` (research R3: sem fonte, busca rodando, espera, erro, bloqueio,
  vazia; grava com `banco.completar_descricao`)
- [X] T009 [US2] `dash/analise.py`: na rodada, vaga forçada com `descricao_pendente` ou sem descrição chama
  `vagas.descrever_uma` (import pelo `_raiz()`); sem texto → `sem_descricao`; `analisar(vagas, sem_descricao)` e
  `montar_pedido` com o bloco "sem a descrição" e a exceção na regra do `sem_dados`; análises com
  `nota_sem_descricao: true`
- [X] T010 [US2] `dash/banco.py`: `completar_descricao` com texto e `nota_sem_descricao` → tira a marca e grava
  `analise_status = "pendente"`
- [X] T011 [P] [US2] `dash/dashboard.html`: com `nota_sem_descricao`, rótulo "sem a descrição" no selo, chip "Nota sem
  a descrição" e banner no detalhe
- [X] T012 [P] [US2] Testes em `tests/test_forcar.py`: `descrever_uma` com fonte falsa (um pedido e a descrição
  gravada; na espera, nenhum pedido; com busca rodando, nenhum pedido; bloqueio → motivo e espera gravada pela
  fonte; plataforma sem `descrever` → sem pedido); `montar_pedido` com o bloco "sem a descrição"; nota gravada com a
  marca; `completar_descricao` tira a marca e volta para `pendente`; nota normal tira a marca

---

## Phase 5: User Story 3 - Sem IA, aviso claro (Priority: P3)

**Goal**: sem IA, o clique só avisa, com atalho para o botão IA.

**Independent Test**: quickstart.md cenário 2, passo 5.

- [X] T013 [US3] `dash/dashboard.html`: resposta 409 com `sem_ia` → toast "Para dar nota, ligue uma IA" com o atalho
  `abrirIA()`
- [X] T014 [P] [US3] Teste em `tests/test_forcar.py`: sem IA, a rota devolve 409 `sem_ia` e nada muda na vaga nem na
  fila

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T015 [P] `dash/README.md`: o botão Forçar verificar, a rota, os campos novos de `/api/versao` e
  `nota_sem_descricao`; `.agents/skills/buscar-vagas/SKILL.md`: a marca "nota sem a descrição" (não tratar como nota
  final) e o botão; `python sincronizar_skills.py` e `--conferir`
- [X] T016 Rodar `python -m unittest discover -s tests` (tudo passa)
- [ ] T017 Procurar dados pessoais nos arquivos alterados; commit na branch `021-forcar-verificar`; merge na branch
  pessoal; reiniciar o dashboard (`--sem-navegador`) e passar o quickstart cenário 2 com a pessoa
- [ ] T018 Com o OK da pessoa: merge na `master`, `git push origin master`, `git merge master` na branch pessoal,
  apagar a worktree e a branch; `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T003) → US1 (T004–T007) → US2 (T008–T012) → US3 (T013–T014) → Polish.
- T009 depende de T004 (a rodada das forçadas) e de T008.
- T017 e T018 só com o OK da pessoa.

### Parallel Opportunities

- T007 junto com T006; T011 e T012 junto com T009–T010; T014 junto com T013; T015 a qualquer momento depois da US2.

## Implementation Strategy

1. MVP: Foundational + US1 → o botão dá a nota a vagas sem nota que já têm descrição.
2. US2 → descrição pendente: lê se der, senão nota provisória com a marca.
3. US3 → aviso sem IA.
4. Documentação, teste na branch pessoal e entrega.
