---
description: "Tarefas da spec 059: Nerdin no Atualizar candidaturas"
---

# Tasks: Nerdin no "Atualizar candidaturas"

**Input**: [spec.md](spec.md), [plan.md](plan.md). **Tests**: `tests/test_contas_nerdin.py`. Front: sem mudança.

## Phase 1: Regras e documentação (eu)

- [X] T001 Emenda da constituição (VI, Conta conectada: liberados Gupy, Indeed e Nerdin, sob "Termos contrários") e
  documentação: `AGENTS.md`, `README.md`, `dash/API.md` (3.11), skill buscar-vagas (+ `sincronizar_skills.py`),
  `.env.exemplo` (`NERDIN_CANDIDATURAS`).

## Phase 2: Leitor (funcionário)

- [X] T002 [D minor] [US1] [US2] [US3] `contas/nerdin.py` (D1–D6) e `tests/test_contas_nerdin.py`. → copilot, GO na
  tentativa 1; ajuste meu em `_paginas` (só parâmetro de página numérico; nunca abre link que age, como o de cancelar).

## Phase 3: Ligação (eu)

- [X] T003 [US2] Registrar `nerdin` em `contas/__init__.py`; `_descricao` da Nerdin em `dash/sincronia.py` (D7); teste
  da proposta com lidas da Nerdin.

## Phase 4: Fechamento (eu)

- [X] T004 Fechamento (página real conferida em 2026-11-24; ajuste do link `vaga/NNNNN.php`):
  - suíte verde;
  - busca de dados pessoais;
  - commit na branch da feature;
  - merge na branch pessoal;
  - dashboard reiniciado;
  - teste da pessoa (Conectar → login → Pronto → Atualizar agora).
