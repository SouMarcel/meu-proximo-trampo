---
description: "Tarefas da spec 061: documento apagado na página some da pasta"
---

# Tasks: Documento apagado na página some da pasta

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: as tarefas de backend trazem os próprios testes (`python -m unittest discover -s tests`). As do front são
validadas com `npm run typecheck` e `npm run build` na worktree do front.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.
Sequenciais dentro de cada lado (backend e front).

## Format: `[ID] [D tamanho?] [Story] Description`

---

## Phase 1: Backend

- [X] T001 [D minor] [US1][US2][US4] `apagar_lote`, `apagar` para os três tipos, `documentos_da_vaga` e
  `documentos_orfaos` (D1-D3) em `curriculo_ia.py`. Testes em `tests/test_curriculo_ia.py`.
- [X] T002 [D minor] [US3][US4] Limpeza apaga os documentos e registra na ficha (D6), `desligar_documento` (D4) e o
  comando `documentos-orfaos` (D7) em `dash/banco.py`. Testes em `tests/test_limpeza.py`.
- [X] T003 [D minor] [US1][US2] Rotas: `DELETE /api/curriculo/<nome>` para carta e respostas (D4) e
  `DELETE /api/vagas/<id>` apagando os documentos (D5) em `dash/servidor.py`. Testes em `tests/test_curriculo_ia.py`
  (classe de rotas nova).

## Phase 2: Front (`frontend-react`)

- [X] T004 [D minor] [US1] Lixeira em cada carta e cada conjunto de respostas do kit (D8), em
  `src/components/kit/Kit.tsx` (e o tipo de retorno em `src/services/api/curriculo.ts`, se preciso).
- [X] T005 [D minor] [US2][US3] Confirmação de remover vaga com a contagem de documentos e aviso de 409 (D9) em
  `src/components/JobCard.tsx` e `src/components/modals/JobDetailModal.tsx`; aviso e resumo da Limpeza em
  `src/components/modals/LimpezaAba.tsx`.

## Phase 3: Documentação e entrega

- [X] T006 Documentação: `dash/API.md` (DELETE de curriculo e de vagas, limpeza), `README.md`, `AGENTS.md` (comando
  `documentos-orfaos`), nota na `specs/054-limpeza-vagas/spec.md`.
- [X] T007 Merge na `marcel`, build do front, reiniciar o dashboard; prévia de `documentos-orfaos` na pasta real (sem
  gravar) para o usuário conferir.
