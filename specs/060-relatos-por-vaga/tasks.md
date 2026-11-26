---
description: "Tarefas da spec 060: perfil como base, relato só na vaga dele, relatos incorporados com conflitos"
---

# Tasks: Perfil como base e relatos por vaga

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: as tarefas de backend trazem os próprios testes (`python -m unittest discover -s tests`). As do front são
validadas com `npm run typecheck` e `npm run build` na worktree do front.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T0XX.md`.

## Format: `[ID] [D tamanho?] [Story] Description`

---

## Phase 0: Preparação

- [ ] T000 Merge da `061-apagar-documentos` nesta branch; emenda 5.6.0 da constituição (feita junto da spec).

## Phase 1: Backend

- [ ] T001 [D minor] [US1] `relatos.com_relatos(perfil, vaga)`, `pendentes`, `desmarcar_no_perfil`, `lista --vaga`
  (D1) em `relatos.py`. Testes em `tests/test_relatos.py`.
- [ ] T002 [D minor] [US1] Pedidos gerais só com o perfil (D2): `dash/analise.py`, `analise_perfil.py`, `conferir.py`,
  `curriculo_ia.py` (COMPLETO e `perfil_texto(vaga=None)`). Testes nos arquivos de teste de cada um.
- [ ] T003 [D minor] [US1] Pedidos da vaga (D3), parte 1: `curriculo_ia.gerar` e `candidatura_ia.py`. Testes em
  `tests/test_curriculo_ia.py` e `tests/test_candidatura_ia.py` (ou o teste que já cobre o kit).
- [ ] T004 [D minor] [US1] Pedidos da vaga (D3), parte 2: `entrevista.py` e `reprovacao.py`. Testes nos arquivos de
  teste deles.
- [ ] T005 [D minor] [US2] `revisao_perfil.incorporar`, `desfazer`, `ultima_incorporacao` (D4). Testes em
  `tests/test_revisao_perfil.py`.
- [ ] T006 [D minor] [US2] Geração e rotas (D5) em `dash/gerador.py` e `dash/servidor.py`. Testes em
  `tests/test_revisao_perfil.py`.
- [ ] T007 [D minor] [US4] Currículo geral (D6) em `curriculo_ia.py`, `dash/banco.py` e `dash/servidor.py`. Testes em
  `tests/test_curriculo_ia.py`.
- [ ] T008 [D minor] [US4] Usos do currículo geral e do perfil (D6, D7) em `reprovacao.py`, `analise_perfil.py` e
  `candidatura/contato.py`. Testes nos arquivos de teste deles.

## Phase 2: Front (`frontend-react`)

- [ ] T009 [D minor] [US2][US3] Seus relatos como caixa de entrada, Incorporar e Desfazer (D8) em `Relatos.tsx` e
  `src/services/api/perfil.ts`.
- [ ] T010 [D minor] [US2][US3][US4] Ícones de aviso, Conflitos com os relatos, "Extração perfil - currículo" (D9) em
  `MeuPerfil.tsx`, `Curriculos.tsx` e `src/services/api/curriculo.ts`.

## Phase 3: Documentação e entrega

- [ ] T011 Documentação: `dash/API.md`, `README.md`, `AGENTS.md`, skills `analisar-perfil`, `gerar-curriculo`,
  `preparar-entrevista` + `python sincronizar_skills.py`.
- [ ] T012 Merge na `marcel`, build do front, reiniciar o dashboard; medir o pedido da nota antes/depois.
