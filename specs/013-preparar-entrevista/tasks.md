---

description: "Tarefas da feature 013: preparação para entrevista (Windows)"
---

# Tasks: Preparação para entrevista

**Input**: Design documents from `/specs/013-preparar-entrevista/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/entrevista.md, quickstart.md

**Tests**: `unittest` com perfil e vagas fictícios e IA falsa (constituição); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Conferir que as referências do `vagas.py` e os 183 testes ainda batem
- [X] T002 `.gitignore` com `entrevistas/` e AGENTS.md com `entrevistas/` na lista de dados pessoais e a skill nova na tabela

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Criar `entrevista.py`: pasta `entrevistas/` (atributo para os testes), `carregar_preparacao(vid)` e
  `_gravar_preparacao(vid, prep)` (atômico, `vaga-<id>.json` com o id saneado), `listar_historias()`,
  `salvar_historia(h)` (campos e limites do data-model; com `id`, atualiza; até 60), `remover_historia(id)`,
  `perfil_texto()`
- [X] T004 [P] `tests/test_entrevista.py` (base): preparação vazia, gravar e ler, histórias (salvar, atualizar, remover,
  limites)

**Checkpoint**: módulo e gravação prontos

---

## Phase 3: User Story 1 - Saber o que esperar (Priority: P1) 🎯 MVP

**Goal**: dossiê e perguntas prováveis, sem IA; resumo e perguntas a mais com IA.

**Independent Test**: quickstart.md cenários 1, 2 e 3.

- [X] T005 [US1] Em `entrevista.py`: `dossie(vaga, prep)` (vaga, análise, kit, anotações, texto colado),
  `perguntas(vaga, perfil, prep)` (lista padrão comportamental PT/EN, técnicas pelos requisitos até 6, lacunas da
  análise até 3, perguntas que caíram nas rodadas, as da IA salvas; sem repetir; `{texto, texto_en, tipo, porque,
  origem}`), `guardar_texto_empresa(vid, texto)` (até 20.000)
- [X] T006 [US1] Em `entrevista.py`: `resumo_ia(vaga, texto)` (`[{ponto, origem, trecho}]`; origem vaga/texto só com o
  trecho achado no texto certo, senão dedução) e `perguntas_ia(vaga, perfil)` (até 10 `{texto, tipo, porque}`)
- [X] T007 [US1] Em `dash/servidor.py`: `GET /api/entrevista/<vaga>`, `PUT …/empresa`, `POST …/resumo`, `POST …/perguntas`
- [X] T008 [US1] Em `dash/dashboard.html`: botão "Preparar entrevista" no card da coluna Entrevista e no detalhe; diálogo
  com as seções Dossiê (com o texto colado e o resumo) e Perguntas (tipo, porquê, origem)
- [X] T009 [P] [US1] Testes: dossiê e perguntas sem IA (SC-001), origem do resumo com trecho inventado virando dedução,
  perguntas da IA somadas sem repetir
- [X] T010 [US1] Validar US1 pelo quickstart.md cenários 1, 2 e 3

---

## Phase 4: User Story 2 - Histórias STAR (Priority: P1)

**Goal**: rascunhos conferidos, salvos só com confirmação, reaproveitados em outras vagas.

**Independent Test**: quickstart.md cenários 4 e 5.

- [X] T011 [US2] Em `entrevista.py`, `historias_ia(perfil, perguntas)`: até 5 rascunhos STAR com reflexão, conquista e
  perguntas; conferência de número e data (`conferir._fatos_do_texto`) e de nomes próprios fora do perfil → `conferir`
- [X] T012 [US2] Em `dash/servidor.py`: `POST …/<vaga>/historias` (rascunhos), `POST /api/entrevista/historias`
  (grava), `DELETE /api/entrevista/historias/<id>`
- [X] T013 [US2] Em `dash/dashboard.html`, seção Histórias: as salvas (com as perguntas que respondem, editar, remover),
  "Sugerir histórias" (rascunhos com os pontos para conferir, editar, confirmar) e "Escrever uma" à mão
- [X] T014 [P] [US2] Testes: rascunho com número fora do perfil marcado (SC-002), salvar só com confirmação (SC-003),
  história aparecendo na preparação de outra vaga
- [X] T015 [US2] Validar US2 pelo quickstart.md cenários 4 e 5

---

## Phase 5: User Story 3 - Simulação (Priority: P2)

**Goal**: uma pergunta por vez, retorno honesto com fatos conferidos.

**Independent Test**: quickstart.md cenário 6.

- [X] T016 [US3] Em `entrevista.py`: `retorno_ia(pergunta, resposta, perfil, historias, idioma)` (`{funcionou, faltou,
  mais_forte}`, sem nota nem elogio vazio; "mais forte" conferida contra perfil e histórias → `conferir`),
  `registrar_resposta(vid, …)` (com ou sem retorno) e o resumo sem IA (os "faltou" juntos)
- [X] T017 [US3] Em `dash/servidor.py`, `POST …/<vaga>/simulacao`; em `dash/dashboard.html`, seção Simular (idioma, uma
  pergunta por vez, responder, pular, repetir, encerrar, retorno, resumo; sem IA, só as perguntas)
- [X] T018 [P] [US3] Testes: retorno com IA falsa, "mais forte" com fato inventado marcada (SC-005), sem IA grava só a
  resposta, resumo
- [X] T019 [US3] Validar US3 pelo quickstart.md cenário 6

---

## Phase 6: User Story 4 - Salário e depois da entrevista (Priority: P3)

**Goal**: salário só com valores da vaga e do perfil; anotações que alimentam a próxima.

**Independent Test**: quickstart.md cenários 7 e 8.

- [X] T020 [US4] Em `entrevista.py`: `salario(vaga, perfil)` (faixa e moeda da vaga, pretensão do perfil, pontos fixos)
  e `registrar_rodada(vid, …)`; em `dash/servidor.py`, `POST …/<vaga>/rodada`
- [X] T021 [US4] Em `dash/dashboard.html`: seções Salário e Depois (anotar como foi; rodadas anteriores)
- [X] T022 [P] [US4] Testes: salário sem valor de fora (SC-004), rodada alimentando as perguntas
- [X] T023 [US4] Validar US4 pelo quickstart.md cenários 7 e 8

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T024 [P] Skill `.agents/skills/preparar-entrevista/SKILL.md` (quando usar, as regras, os comandos, histórias com
  confirmação, simulação pelo chat uma pergunta por vez) e `entrevista.py` com linha de comando (`preparar <vaga>`,
  `historias`); `python sincronizar_skills.py`
- [X] T025 [P] `README.md` (preparação para entrevista) e `dash/README.md` (pasta `entrevistas/`)
- [X] T026 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T027 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch
  pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T004) → histórias.
- **US1 (T005–T010)** primeiro (as perguntas alimentam US2 e US3).
- **US2 (T011–T015)** e **US4 (T020–T023)** dependem só da Foundational e da US1; **US3 (T016–T019)** usa as perguntas
  (US1) e as histórias (US2).
- Polish por último; T027 só com o OK do usuário.

## Parallel Opportunities

- Os testes [P] de cada história junto da implementação.
- T024 e T025 a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → dossiê e perguntas prováveis, sem IA.
2. US2 (histórias), US3 (simulação) e US4 (salário e depois).
3. Validação completa e commit com OK.
