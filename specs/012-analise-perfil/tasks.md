---

description: "Tarefas da feature 012: análise de perfil contínua (Windows)"
---

# Tasks: Análise de perfil contínua

**Input**: Design documents from `/specs/012-analise-perfil/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/analises.md, quickstart.md

**Tests**: `unittest` com perfil e vagas fictícios e IA falsa (constituição); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Conferir que as referências do `vagas.py` e os 173 testes ainda batem
- [X] T002 [P] Vagas fictícias analisadas para os testes, montadas em `tests/test_analise_perfil.py` (8 vagas com
  lacunas conhecidas, variações de "Power BI", aderências diferentes, seguidas e não seguidas; requisitos no anúncio)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Criar `analise_perfil.py`: `carregar()`, `salvar(tipo, resultado)` (atômico em
  `dash/dados/analises-perfil.json`, com a data), `marcar(chave, valor)` (só `linkedin_en`), `perfil_texto()` e
  `vagas_do_banco()`
- [X] T004 [P] `tests/test_analise_perfil.py` (base): salvar, carregar e marcar

**Checkpoint**: módulo e gravação prontos

---

## Phase 3: User Story 1 - Lacunas das vagas (Priority: P1) 🎯 MVP

**Goal**: ranking de lacunas sem IA, com níveis, visões e mínimo de 5 vagas; plano de estudo a pedido.

**Independent Test**: quickstart.md cenários 1, 2, 3 e 7.

- [X] T005 [US1] Em `analise_perfil.py`, `lacunas(vagas, perfil, visao)`: fontes (lacunas da análise e requisitos
  `lacuna` de `conferir.conferir_requisitos`), termos significativos sem as palavras genéricas PT/EN, grupos por termo
  distintivo (rótulo = termo mais frequente; exemplo e até 5 variações), peso da vaga (aderência/100, 0,5 sem nota;
  ×1,5 seguida; ×0,5 fora dos critérios ou "não seguir"), níveis (crítica ≥ 0,5, alta 0,25–0,5, média 0,1–0,25;
  abaixo fora), até 3 vagas de exemplo, visões "seguidas" e "todas", mínimo de 5 vagas analisadas (`faltam`)
- [X] T006 [US1] Em `analise_perfil.py`, `plano_estudo(perfil, itens)`: pedido à IA para até 5 lacunas do topo, JSON
  `[{lacuna, passos (até 3), semanas}]`, sem afirmar experiência; erro legível sem IA
- [X] T007 [US1] Em `dash/servidor.py`: `GET /api/analises-perfil`, `POST /api/analises-perfil/lacunas` e
  `POST /api/analises-perfil/plano` (só deste computador; IA fora da trava)
- [X] T008 [US1] Em `dash/dashboard.html`, Meu perfil: passo "Análises" com a seção "Lacunas das vagas" (visões, botão
  Analisar, ranking com nível, número de vagas, exemplos com link para abrir a vaga, aviso de quantas faltam, data da
  última análise, botão "Plano de estudo" e o plano)
- [X] T009 [P] [US1] Testes: variações juntas e a mais frequente nas vagas de maior aderência no topo (SC-001), níveis,
  visões, mínimo de 5 (SC-002), plano com IA falsa
- [X] T010 [US1] Validar US1 pelo quickstart.md cenários 1, 2, 3 e 7

---

## Phase 4: User Story 2 - Carreiras e cargos-alvo (Priority: P1)

**Goal**: 5 a 10 cargos com tipo, evidência, lacuna e termos; levar para os filtros com confirmação.

**Independent Test**: quickstart.md cenários 4 e 5.

- [X] T011 [US2] Em `analise_perfil.py`: `cargos_alvo(perfil)` (pedido à IA, JSON `[{titulo, titulo_en, tipo, evidencia,
  lacuna}]`, tipo em lateral|degrau|vizinho, título repetido ou fora do formato descartado, evidência conferida no
  perfil por termos, senão `conferir: true`, aviso se sobrarem menos de 5) e `filtros_com_cargos(cargos, confirmar)`
  (pela `curriculo_base.montar_filtros`, cargos atuais mais os escolhidos sem repetir; grava só com `confirmar`)
- [X] T012 [US2] Em `dash/servidor.py`: `POST /api/analises-perfil/cargos` e `POST /api/analises-perfil/cargos/filtros`
- [X] T013 [US2] Em `dash/dashboard.html`: seção "Carreiras e cargos-alvo" (botão, lista com tipo, evidência, lacuna,
  termos PT/EN e "conferir", caixas para marcar, "Levar para os filtros" com o que muda e "Confirmar")
- [X] T014 [P] [US2] Testes: cargos com IA falsa, evidência inventada marcada (SC-003), formato ruim descartado,
  filtros sem gravar antes de confirmar e com o resto igual (SC-004)
- [X] T015 [US2] Validar US2 pelo quickstart.md cenários 4 e 5

---

## Phase 5: User Story 3 - Prontidão internacional (Priority: P2)

**Goal**: o que está pronto e o que falta para vagas de fora.

**Independent Test**: quickstart.md cenário 6.

- [X] T016 [US3] Em `analise_perfil.py`, `prontidao(perfil, cfg)`: inglês (linha de idiomas do perfil, PT/EN, nível
  intermediário ou mais), fuso, contratação, passaporte e autorização (filtros internacionais), currículo em inglês
  (seu currículo em inglês ou currículo gerado us/eu), LinkedIn em inglês (marcação); `situacao`, `origem`, `detalhe`,
  `acao`
- [X] T017 [US3] Em `dash/servidor.py`, `PUT /api/analises-perfil/marcas`; em `dash/dashboard.html`, seção "Prontidão
  internacional" com cada item, a origem e o botão do caminho (painel internacional, currículo, Meu perfil, marcar)
- [X] T018 [P] [US3] Testes: situação certa em cada item com perfil e filtros de teste (SC-005); marcar LinkedIn
- [X] T019 [US3] Validar US3 pelo quickstart.md cenário 6

---

## Phase 6: User Story 4 - Pelo chat (Priority: P3)

**Goal**: as três análises pela skill de perfil.

**Independent Test**: quickstart.md cenário 9.

- [X] T020 [US4] Em `analise_perfil.py`, linha de comando: `lacunas [--seguidas]`, `prontidao`, `cargos`, `plano`
- [X] T021 [US4] Em `.agents/skills/analisar-perfil/SKILL.md`: seção "Análises do perfil" (quando oferecer, os
  comandos, mudança nos filtros só com o OK); `python sincronizar_skills.py`
- [X] T022 [P] [US4] Testes da linha de comando
- [X] T023 [US4] Validar US4 pelo quickstart.md cenário 9

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T024 [P] `README.md` (análises do perfil), `AGENTS.md` (comandos) e `dash/README.md` (o arquivo de análises)
- [X] T025 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [ ] T026 Com o OK do usuário, rodar as lacunas das vagas e a prontidão com os dados dele (sem IA) e mostrar
- [X] T027 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch
  pessoal, reiniciar o servidor e `graphify update .`; marcar a T024 da spec 011

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T004) → histórias.
- **US1 (T005–T010)**, **US2 (T011–T015)** e **US3 (T016–T019)** dependem só da Foundational; o plano de estudo
  (T006) usa o resultado das lacunas.
- **US4 (T020–T023)** depende das três.
- Polish por último; T026 e T027 só com o OK do usuário.

## Parallel Opportunities

- US1, US2 e US3 em paralelo depois da Foundational (mesmos arquivos `analise_perfil.py`, `servidor.py` e
  `dashboard.html`: em sequência na prática, com os testes [P] junto).
- T024 a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → o ranking de lacunas, sem IA.
2. US2 (cargos-alvo) e US3 (prontidão), depois US4 (chat).
3. Validação completa, análise com os dados do usuário (com OK) e commit com OK.
