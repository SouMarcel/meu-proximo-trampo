---
description: "Tarefas da spec 058: a mesma vaga em vários portais"
---

# Tasks: A mesma vaga em vários portais

**Input**: [spec.md](spec.md), [plan.md](plan.md). **Tests**: `tests/test_repetidas.py`. Front: typecheck e build.

## Phase 1: Back (eu)

- [X] T001 [US1] D1 e D2 em `dash/banco.py`, `dash/sincronia.py` e `vagas.py`.
- [X] T002 [US3] D3 a D5: `juntar`, `_principal`, `grupos_repetidos`, `juntar_repetidas`, o comando e as rotas.
- [X] T003 [US2] D6: `completar_pelo_link` e `PUT /api/vagas/<id>/link-original`.
- [X] T004 Testes de T001 a T003.
- [X] T005 [P] D8: documentação.

## Phase 2: Front (funcionários, pelo rodízio)

- [X] T006 [D minor] [US2] [US4] Etiquetas de todos os portais e o "Link do anúncio original" no detalhe.
- [ ] T007 [D minor] [US3] A seção "Vagas repetidas" na aba Limpeza.

## Phase 3: Fechamento (eu)

- [ ] T008 Fechamento:
  - suíte verde;
  - busca de dados pessoais;
  - commits;
  - front publicado;
  - merge na branch pessoal;
  - dashboard reiniciado;
  - teste da pessoa.
