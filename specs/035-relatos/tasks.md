---
description: "Tarefas da feature 035: Relatos — a candidatura assistida aprende com a pessoa (Windows)"
---

# Tasks: Relatos

**Input**: spec.md, plan.md. **Testes**: `tests/test_relatos.py` (sem rede e sem navegador).

## Phase 1: Base

- [X] T001 `relatos.py`: guardar, listar, editar, apagar, bloco, com_relatos, levar_ao_perfil e a linha de comando.
- [X] T002 Constituição IV (5.2.0) com relatório de impacto.

## Phase 2: US3 — fatos e classificação (P2, base para as outras)

- [X] T003 `candidatura_ia.SENSIVEIS`: remuneração atual × pretensão salarial.
- [X] T004 `formulario.PESSOAL` → cadastro em campo de texto longo.
- [X] T005 `memoria`: NAO_LEMBRAR e `fato()` com o fallback em `valor_para`.

## Phase 3: US1 — relato vira resposta (P1) 🎯

- [X] T006 `candidatura_ia.adaptar_relatos`.
- [X] T007 `auto.responder`: relatos adaptados, fontes e gravação; `servidor` passa `guardar_relatos`.

## Phase 4: US2 — relato vira conhecimento (P1)

- [X] T008 `com_relatos` em curriculo_ia, entrevista, analise_perfil, dash/analise e conferir.
- [X] T009 Rotas `/api/perfil/relatos`.

## Phase 5: Testes, front e documentação

- [X] T010 `tests/test_relatos.py` (SC-001 a SC-004).
- [X] T011 Front (branch `front-035-relatos` sobre `front-034-vaga-segura`): painel, Seus relatos, tipos; `tsc` e
  build; build de teste na branch pessoal, sem commit.
- [X] T012 API.md, README, AGENTS.md, skills (+ `sincronizar_skills.py`).
- [ ] T013 Suíte inteira; dados pessoais; commit; merge na branch pessoal; dashboard reiniciado; teste do usuário.
