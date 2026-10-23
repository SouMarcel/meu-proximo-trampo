---
description: "Tarefas da feature 026: InfoJobs na busca e pausa por portal (Windows)"
---

# Tasks: InfoJobs na busca de vagas e pausa por portal

**Input**: spec.md, plan.md, research.md. **Tests**: `unittest` sem rede. **Plataforma**: Windows 10/11.

## Phase 1: Setup

- [X] T001 Rodar `python -m unittest discover -s tests` na worktree e anotar a contagem (359 OK antes; 389 OK depois)
- [X] T002 [P] `tests/dados/infojobs/lista.html` (cards fictícios no formato da research R2: data em `js_date`,
  empresa confidencial, empresa com link, "Cidade - UF" com a distância oculta, salário, Presencial, Home office,
  Híbrido, títulos que batem e que não batem) e `tests/dados/infojobs/vaga.html` (JSON-LD `JobPosting`)

## Phase 2: Foundational — mecanismos comuns (US4)

- [X] T003 `fontes/_comum.py`: `pausa_do_env`, `aviso_pausa`, `pausar`, `gravar_espera`, `ler_espera`,
  `baixar_pagina`, `UFS`, `na_regiao`
- [X] T004 `fontes/linkedin.py`: `pausa`, `aviso_pausa`, `_pausar`, `_bloquear` e `espera` pelos helpers, sem mudar
  o comportamento (os testes do LinkedIn passam sem alteração)
- [X] T005 `fontes/nerdin.py`: `VAR_PAUSA = "NERDIN_PAUSA"`, `_pausar` pelo helper (padrão e mínimo de 3 s),
  `aviso_pausa()`, `UFS` do `_comum`
- [X] T006 `vagas.py`: `aviso_pausa` junta os avisos de todas as fontes da busca que têm `aviso_pausa` e não estão em
  espera
- [X] T007 [P] `tests/test_pausa_portal.py`: padrão, valor, mínimo, máximo, inválido, vírgula decimal; aviso por
  portal; `vagas.aviso_pausa` com dois portais; `NERDIN_PAUSA`

## Phase 3: US1/US2/US3/US5 — InfoJobs na busca (P1)

- [X] T008 `fontes/infojobs.py`: contrato (`NOME`, `PLATAFORMA`, `AREAS`, `TERMOS`, `MAX_DESCRICOES`, `PAUSA`,
  `VAR_PAUSA`, `ESPERA`, `ARQ_ESPERA`), leitura dos cards, lista por cargo e da cidade, `Antiguedad` pela janela,
  `buscar`, `descrever`, `espera`, `parada`, `aviso_pausa`, `id_do_link`
- [X] T009 Registro: `fontes/__init__.py`, `filtros.FONTES_NAC` e `FONTES_PADRAO`, `dash/banco.PLATAFORMAS`,
  `config.exemplo.json`
- [X] T010 `fontes/link.py`: `plataforma("infojobs.")` e `ler()` com o id `infojobs-<n>`, sem pedido durante a
  espera (US6)
- [X] T011 [P] `tests/test_infojobs.py`:
  - cards, filtros, uma leitura por cargo, cidade, janela, fora do Brasil, ilegível;
  - `descrever`, `id_do_link`, Adicionar Vaga;
  - bloqueio → espera de 24 h, nenhum pedido na espera, `vagas.fontes_em_espera`;
  - ligado por padrão; desligado sem pedido

## Phase 4: Documentação e front

- [X] T012 `.env.exemplo` (novo) com as linhas comentadas de `LINKEDIN_PAUSA`, `NERDIN_PAUSA`, `INFOJOBS_PAUSA` e
  as chaves que já existem (sem valores)
- [X] T013 README, `dash/README.md`, `dash/API.md`, AGENTS.md, `docs/novo-portal.md`, skill buscar-vagas +
  `python sincronizar_skills.py`
- [X] T014 `frontend-react` (worktree própria, branch `front-026-portais`, com o Vagas.com): `InfoJobs` em `src/types/api.ts`, cor e domínio em
  `src/utils/formatters.ts`, texto do `AddJobModal.tsx`; commit local (push só com o OK da pessoa)

## Phase 5: Verificação

- [X] T015 `python -m unittest discover -s tests` inteiro
- [X] T016 Busca real pequena: `vagas.py buscar --fontes infojobs` com um cargo; conferir 10 vagas (SC-002) e o
  link de uma vaga no `fontes.link.ler`
- [X] T017 Procurar dados pessoais nos arquivos alterados; commit local na `026-infojobs`
