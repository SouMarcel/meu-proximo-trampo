---
description: "Tarefas da feature 038: vagas sem análise sempre à vista, com a caixa Analisadas (Windows)"
---

# Tasks: Vagas sem análise e a caixa "Analisadas"

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [quickstart.md](quickstart.md).

**Testes**: só a página muda. A verificação é `tsc --noEmit`, `vite build`, a suíte Python (sem mudança) e o teste do
usuário pelo quickstart.

**Caminhos**: front na worktree `../mpt-front-027b`, branch `front-038-vagas-analisadas`; a spec e o README na
`038-vagas-analisadas`.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Na `../mpt-front-027b`:
  1. `git status` limpo;
  2. `git pull` da `frontend-react` (8f7cdb7 ou depois);
  3. criar a branch `front-038-vagas-analisadas`;
  4. `tsc --noEmit` deve passar.

## Phase 2: Foundational

- [X] T002 Em `src/services/storage.ts`, `ScreenPreferences` ganha `analisadas?: boolean`, com comentário (spec 038).

## Phase 3: User Story 1 - Vaga sem análise sempre à vista (Priority: P1) 🎯 MVP

**Independent Test**: com Nota mínima 70, a vaga sem nota continua em Para decidir.

- [X] T003 [US1] Em `src/components/TriageReport.tsx`, no filtro de `lista`, depois da busca por texto, a linha
  `if (!temNota(v)) return true`. A vaga sem nota passa por Senioridade, Modo, Nota mínima e Publicada há até
  (research.md R2), com o comentário da regra.

## Phase 4: User Story 2 - Caixa "Analisadas" (Priority: P1)

**Independent Test**: com a caixa marcada, a vaga sem nota some das três abas, e o número da aba cai.

- [X] T004 [US2] Em `TriageReport.tsx`:
  - `const [soAnalisadas, setSoAnalisadas] = useState(prefs.analisadas === true)`;
  - salvar `analisadas: soAnalisadas` no `useEffect` das preferências;
  - `visivel(v) = !soAnalisadas || temNota(v)`.
- [X] T005 [US2] Em `TriageReport.tsx`, nas contas e na lista:
  - `counts` só conta as vagas visíveis;
  - `daTriagem` filtra por `visivel`;
  - os `ids` do `BotaoMarcarTodas` são os da aba pendente com `visivel`;
  - `filtrando` inclui `soAnalisadas`;
  - `limparFiltros` faz `setSoAnalisadas(false)`.
- [X] T006 [US2] Em `TriageReport.tsx`, a caixa na linha dos filtros secundários, depois de "Publicada há até":
  `<label title="Oculta as vagas ainda sem análise">` com `<input type="checkbox">` e "Analisadas", no estilo dos
  outros rótulos.
- [X] T007 [US2] Em `TriageReport.tsx`, na linha "Mostrando X de Y", acrescentar "(N sem análise ocultas)" quando a
  caixa esconde vagas da aba. O N é o total da aba menos as visíveis.

## Phase 5: Polish e entrega

- [X] T008 [P] `README.md`: a frase dos filtros do Relatório ganha a caixa **Analisadas** e a regra das vagas sem
  nota.
- [X] T009 Rodar `tsc --noEmit` e `vite build`, depois commit na `front-038-vagas-analisadas`. Rodar a suíte Python
  e fazer o commit da spec e do README na `038-vagas-analisadas`, procurando dados pessoais antes.
- [X] T010 Na branch pessoal:
  - `git merge 038-vagas-analisadas`;
  - copiar o `dist/` para `dash/front/`, sem commit;
  - pedir o teste do usuário pelo quickstart.
- [X] T011 Com o OK do usuário:
  1. `git checkout -- dash/front` e apagar os assets novos;
  2. merge `--no-ff` na `master` e push;
  3. merge do front na `frontend-react` e push;
  4. Action e merge do PR com squash;
  5. `git merge origin/master` na branch pessoal;
  6. apagar a worktree e as branches;
  7. `graphify update .`.

## Dependencies & Execution Order

T001 → T002 → T003 → T004 → T005 → T006 → T007, em sequência, porque é o mesmo arquivo. T008 é independente. T009 →
T010 → T011.

## Implementation Strategy

US1 (T003) já resolve as vagas que somem. US2 traz a caixa. A entrega só acontece com o OK do usuário.
