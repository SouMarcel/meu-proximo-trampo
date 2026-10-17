---

description: "Tarefas da feature 017: Pausa do LinkedIn ajustável (Windows)"
---

# Tasks: Pausa do LinkedIn ajustável

**Input**: [spec.md](spec.md), [plan.md](plan.md)

**Tests**: `unittest` sem rede, com `segredos.ler` substituído.

## Phase 1: User Story 1 - Espaçar mais os pedidos ao LinkedIn (P1) 🎯 MVP

- [X] T001 [US1] Em `fontes/linkedin.py`:
  - `VAR_PAUSA = "LINKEDIN_PAUSA"`, `PAUSA_MIN, PAUSA_MAX, PAUSA_FAIXA = 3.0, 60.0, 4.0`;
  - `pausa()` → `{"faixa", "definida", "ajuste"}`;
  - `_pausar()` sorteia na faixa da busca (`_estado["pausa"]`, zerado em `_esquecer`).
- [X] T002 [US1] Em `fontes/linkedin.py`, `aviso_pausa(consultas)`: a pausa em uso e a estimativa em minutos
  ((consultas × 3 + 20) × pausa média), só com a variável definida.
- [X] T003 [US1] Em `vagas.py`, `aviso_pausa(f, fontes)`:
  - só com o LinkedIn na busca, cargos configurados e fora da espera;
  - impresso no começo do `buscar`, junto do aviso de cargos.
- [X] T004 [US1] Em `dash/buscador.py`, `plano()` devolve `aviso_pausa`, e `dash/dashboard.html` mostra o aviso no
  diálogo de busca.

## Phase 2: User Story 2 - Valor fora do permitido (P2)

- [X] T005 [US2] Em `pausa()`:
  - abaixo de 3 vale 3; acima de 60 vale 60;
  - texto que não é número (inclusive `nan`) vale o padrão;
  - vírgula e ponto valem como separador decimal;
  - o aviso diz o motivo do ajuste.

## Phase 3: Polish

- [X] T006 [P] Testes em `tests/test_linkedin.py` (`TestPausa`): sem a variável, valores válidos e inválidos, aviso,
  faixa usada entre os pedidos e lida de novo só na busca seguinte, aviso na busca com e sem LinkedIn e na espera.
- [X] T007 [P] README (seção LinkedIn) e skill buscar-vagas, com `python sincronizar_skills.py`.
- [X] T008 `python -m unittest discover -s tests`: 273 testes passando.
- [X] T009 Teste da pessoa na branch pessoal: `LINKEDIN_PAUSA` no `.env`, diálogo de busca com o aviso e uma busca
  real.
- [X] T010 Com o OK: busca de dados pessoais no diff, merge na `master`, push e merge na branch pessoal.
