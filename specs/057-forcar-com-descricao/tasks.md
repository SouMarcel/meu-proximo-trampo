---
description: "Tarefas da spec 057: Forçar verificar só com a descrição no computador"
---

# Tasks: Forçar verificar só com a descrição no computador

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: `tests/test_forcar.py` e `tests/test_forcar_descricao.py` (`python -m unittest discover -s tests`). No front:
typecheck e build.

## Phase 1: Back (eu)

- [X] T001 [US1] [US2] [US3] Itens 1 a 4 do plano em `dash/analise.py` e `vagas.py`:
  - descrição obrigatória;
  - aguardando e retomar;
  - `LINKEDIN_FORCAR_PAUSA`;
  - nova tentativa da IA.
- [X] T002 [US3] Item 5: leitura tolerante em `dash/banco.py`, `validar_analise`.
- [X] T003 [US4] Item 6: `banco.colar_descricao` e `PUT /api/vagas/<id>/descricao` em `dash/servidor.py`, mais
  `aguardando` em `/api/versao`.
- [X] T004 [US4] Item 7: dados do portal do JobGether, em `fontes/jobgether.py`, `dash/analise.py` (`montar_pedido`)
  e no caminho da vaga repetida.
- [X] T005 Testes de T001 a T004.
- [X] T006 [P] Documentação: `.env.exemplo`, `dash/API.md` e `AGENTS.md`.

## Phase 2: Front (funcionário)

- [X] T007 [D minor] [US1] [US4] Aguardando, Colar a descrição, nota pelos dados do portal e funções e experiência
  na aba Análise. Arquivos: `src/types/api.ts`, `src/services/api/vagas.ts`, `src/utils/formatters.ts`,
  `src/components/TriageReport.tsx` e `src/components/modals/JobDetailModal.tsx`.

## Phase 3: Fechamento (eu)

- [ ] T008 Fechamento:
  - suíte verde;
  - busca de dados pessoais;
  - commits;
  - front publicado;
  - merge na branch pessoal;
  - dashboard reiniciado;
  - teste da pessoa.

  Com o OK: 056 e 057 na master.
