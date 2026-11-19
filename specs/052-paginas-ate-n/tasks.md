---
description: "Tarefas da spec 052: páginas em duas opções (Completo ou Até N) e apagar currículo gerado"
---

# Tasks: Páginas em duas opções e apagar currículo gerado

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: as tarefas de backend trazem os próprios testes (`python -m unittest discover -s tests`). As do front são
validadas com `npm run typecheck` e `npm run build` na worktree do front.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.
São sequenciais dentro de cada lado (backend e front), porque mexem nos mesmos arquivos.

## Format: `[ID] [D tamanho?] [Story] Description`

---

## Phase 1: Backend

- [X] T001 [D minor] [US1] Opções de páginas de 1 a 5 (D1) em `curriculo.py` e orçamento de 3 a 5 (D2) em
  `curriculo_ia.py`. Testes em `tests/test_curriculo.py` e `tests/test_curriculo_ia.py`. → agy, GO na tentativa 1
- [X] T002 [D minor] [US3] `curriculo_ia.apagar(nome)` em duas fases (D3). Testes em `tests/test_curriculo_ia.py`. → copilot, GO na tentativa 1
- [X] T003 [D minor] [US3] `banco.desligar_curriculo`, `reprovacao.esquecer_curriculo` (D4) e a rota
  `DELETE /api/curriculo/<nome>` (D5). Testes em `tests/test_curriculo_ia.py` e `tests/test_reprovacao.py`. → agy, GO na tentativa 1

## Phase 2: Front (branch `frontend-react`)

- [X] T004 [D minor] [US1][US2] Área Páginas com Completo ou "Até [N]" e a caixa do limite obrigatório junto (D6), em
  `src/components/curriculo/Curriculos.tsx`. → copilot, GO na tentativa 1
- [X] T005 [D minor] [US3] Lixeira em cada currículo da lista (D7), em `src/components/curriculo/Curriculos.tsx` e
  `src/services/api/curriculo.ts`. → copilot, GO na tentativa 1

## Phase 3: Fechamento (eu)

- [X] T006 Documentação: `dash/API.md` (opções de páginas, rota de apagar), `.agents/skills/gerar-curriculo/tecnicas.md`
  e `SKILL.md` (1 a 5 páginas e orçamentos), depois `python sincronizar_skills.py`.
- [X] T007 Teste na branch pessoal: backend mesclado, `dist/` do front copiado para `dash/front/`, dashboard
  reiniciado; conferir o diálogo, gerar com "Até 3 páginas" e apagar um currículo de teste. Validado pelo usuário em
  19/11.
