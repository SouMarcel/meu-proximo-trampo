---
description: "Tarefas da spec 056: Forçar verificar em fila, uma vaga por vez"
---

# Tasks: Forçar verificar em fila, uma vaga por vez

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: `tests/test_forcar.py` (`python -m unittest discover -s tests`). No front: typecheck e build.

## Phase 1: Back (eu)

- [X] T001 [US1] [US3] D1, D2 e D3 em `dash/analise.py` e `vagas.py` (`pausa_leitura`), com os testes em
  `tests/test_forcar.py`.
- [X] T002 [US2] D4 em `dash/servidor.py`, mais o teste da rota.
- [X] T003 [P] D6: `.env.exemplo`, `dash/API.md` e `AGENTS.md`.

## Phase 2: Front (funcionário)

- [X] T004 [D minor] [US2] D5 em `src/types/api.ts`, `src/utils/formatters.ts`, `src/components/TriageReport.tsx`,
  `src/components/modals/JobDetailModal.tsx` e `src/App.tsx`.

## Ajuste pedido no teste (eu)

- [X] T006 [US2] O botão da vaga com nota provisória (spec 021) passa a dizer "Reverificar", com a dica "Pede de novo a nota
  desta vaga à IA, agora tentando ler a descrição", em `src/components/TriageReport.tsx`. Só o texto: a vaga com nota normal
  continua sem o botão.

## Phase 3: Fechamento (eu)

- [ ] T005 Fechamento:
  - suíte verde;
  - busca de dados pessoais;
  - commits;
  - push da `frontend-react` e a Action do front;
  - merge na branch pessoal;
  - dashboard reiniciado;
  - teste da pessoa.

  Com o OK: master e PR do front.
