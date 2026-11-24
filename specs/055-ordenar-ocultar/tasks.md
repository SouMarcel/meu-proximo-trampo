---
description: "Tarefas da spec 055: ordenar as listas e ocultar empresas excluídas"
---

# Tasks: Ordenar as listas e ocultar empresas excluídas

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: `tests/test_ordenar_ocultar.py` (`python -m unittest discover -s tests`). No front: typecheck e build.

**Delegação**: T003 vai a um funcionário pelo `delegar.py`, na worktree do front (`../mpt-front-027b`).

## Phase 1: Back (eu)

- [X] T001 [US3] D1 e D2:
  - `filtros.empresa_excluida` e `criterios` usando essa função;
  - `banco.com_kit(..., excluir=None)` com a marca `empresa_excluida`;
  - em `/api/vagas`, a lista lida uma vez;
  - testes em `tests/test_ordenar_ocultar.py`.
- [X] T002 [P] D7: `dash/API.md` e `specs/lista-de-desejos.md`.

## Phase 2: Front (funcionário)

- [X] T003 [D minor] [US1] [US2] [US3] D3 a D6, em `src/utils/ordenacao.ts`, `src/services/storage.ts`,
  `src/types/api.ts`, `src/components/TriageReport.tsx`, `src/components/KanbanBoard.tsx` e `src/App.tsx`.

## Phase 3: Fechamento (eu)

- [ ] T004 Fechamento:
  - suíte verde;
  - busca de dados pessoais;
  - commits;
  - push da `frontend-react` e a Action do front;
  - merge na branch pessoal;
  - dashboard reiniciado;
  - teste da pessoa.

  Com o OK: master e PR do front.
