---

description: "Tarefas da feature 011: começar pelo currículo que a pessoa já tem (Windows)"
---

# Tasks: Começar pelo currículo que a pessoa já tem

**Input**: Design documents from `/specs/011-curriculo-existente/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/curriculo-base.md, quickstart.md

**Tests**: `unittest` com currículos fictícios gerados no teste e IA falsa (constituição); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Conferir que as referências do `vagas.py` e os 164 testes ainda batem
- [X] T002 [P] Currículos fictícios para os testes, gerados no próprio teste em `tests/test_curriculo_base.py` (DOCX em
  português com objetivo, cargo mais recente com período, cidade "Curitiba, PR", CPF e data de nascimento; PDF em
  inglês com "Senior Data Analyst" e "Remote"), sem dados pessoais

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Em `primeiros_passos.py`: `adicionar_existente(estado, caminho)` (arquivo de `anexos/`, PDF ou DOCX, sem
  copiar, mesma leitura e máscara; recusa caminho fora de `anexos/`) e, em `estado_para_pagina`,
  `perfil_do_curriculo` (pela marca de origem no perfil)
- [X] T004 Criar `curriculo_base.py`: `candidatos()` (PDF/DOCX de `anexos/`, menos `perfis-anteriores/`, com nome,
  caminho, data e idioma), `marcados(cfg)`, `marcar(idioma, arquivo)` e `desmarcar(idioma)` (em `config.json →
  curriculo_base`, mantendo as outras chaves; caminho dentro de `anexos/`, `.pdf` ou `.docx`, arquivo existente),
  `ler(arquivo)`, `perfil_do_curriculo(texto, arquivo)` (cabeçalho e marca `<!-- origem: curriculo arquivo=… data=… -->`)
  e `origem_do_perfil(texto)`
- [X] T005 [P] `tests/test_curriculo_base.py` (base): candidatos, marcar/desmarcar e validação do caminho, máscara de
  CPF/RG/nascimento no perfil (SC-002), marca de origem

**Checkpoint**: módulo e leitura prontos; nada da busca muda

---

## Phase 3: User Story 1 - Do currículo direto para as vagas (Priority: P1) 🎯 MVP

**Goal**: proposta numa tela só e confirmação que grava perfil, filtros e currículo base e abre a busca.

**Independent Test**: quickstart.md cenários 1 a 5 e 9.

- [X] T006 [US1] Em `curriculo_base.py`: `dados_do_curriculo(texto, com_ia)` (sem IA: objetivo/cargo pretendido,
  senão o cargo mais recente pela primeira linha de experiência com período; cidade "Cidade, UF"; remoto/híbrido; com
  IA: pedido curto `{cargos_alvo, cargos_alvo_en, cidade, modelos}` só com o que o currículo diz, falha cai no sem IA),
  `proposta(arquivo | material)` (texto, idioma, perfil, dados, filtros por `primeiros_passos.propor_filtros`,
  existe_perfil, avisos; currículo sem texto → aviso com as opções) e `confirmar(dados)` (grava o perfil por
  `gravar_perfil` salvo `manter_perfil`, os filtros por `filtros.salvar` e o currículo base; nada antes)
- [X] T007 [US1] Em `dash/servidor.py`: `GET /api/perfil/curriculos`, `POST /api/perfil/do-curriculo` e
  `POST /api/perfil/do-curriculo/confirmar` (só deste computador, na trava do perfil; `400` com a explicação)
- [X] T008 [US1] Em `dash/dashboard.html`, Meu perfil: "Usar este currículo e ir para as vagas" em cada currículo dos
  materiais e na lista de `anexos/`; tela de confirmação (texto lido recolhido, perfil editável, cargos PT/EN, cidade,
  modelos, substituir ou manter o perfil, marcar como "Seu currículo em <idioma>"); confirmar grava e abre o painel de
  busca; fechar não grava
- [X] T009 [P] [US1] Testes em `tests/test_curriculo_base.py`: dados sem IA (PT e EN, SC-005), com IA falsa (e falha),
  proposta validada, confirmar grava tudo, sem confirmar nada (SC-003), manter o perfil, currículo sem texto
- [X] T010 [US1] Validar US1 pelo quickstart.md cenários 1 a 6 e 9

---

## Phase 4: User Story 2 - Currículo base nas vagas (Priority: P1)

**Goal**: o item Currículo mostra o currículo da pessoa no idioma da vaga.

**Independent Test**: quickstart.md cenário 7.

- [X] T011 [US2] Em `dash/kit.py`, `checklist(v, base)`: item Currículo com `base {idioma, nome, url}` e "Pronto" por
  padrão quando há currículo base no idioma da vaga (en para vaga em inglês, pt para o resto), ou `falta_base` e "A
  fazer"; arquivo sumido conta como falta; a situação da pessoa vale sempre. Em `dash/banco.py`, `com_kit` passa os
  currículos base
- [X] T012 [US2] Em `dash/servidor.py`: `PUT /api/curriculo-base` e `GET /arquivos/curriculo-base/<idioma>` (só o
  arquivo marcado, só deste computador)
- [X] T013 [US2] Em `dash/dashboard.html`: item Currículo com o nome e o link "Abrir" (ou o aviso de que falta no
  idioma da vaga); em Meu perfil, a seção "Seu currículo" (português e inglês: escolher entre os arquivos de `anexos/`,
  trocar, desmarcar)
- [X] T014 [P] [US2] Testes em `tests/test_curriculo_base.py`: item por idioma, arquivo sumido, escolha da pessoa vale
  (SC-004); rota do arquivo recusa outro caminho
- [X] T015 [US2] Validar US2 pelo quickstart.md cenário 7

---

## Phase 5: User Story 3 - Completar o perfil depois (Priority: P2)

**Goal**: Meu perfil diz de onde veio o perfil e oferece a anamnese.

**Independent Test**: quickstart.md cenário 8.

- [X] T016 [US3] Em `dash/dashboard.html`, Meu perfil: aviso "Seu perfil veio do currículo <arquivo> em <data>" com
  "Completar com a anamnese" (segue o fluxo de hoje com o currículo como material) e o diagnóstico
- [X] T017 [US3] Validar US3 pelo quickstart.md cenário 8

---

## Phase 6: User Story 4 - O mesmo caminho pelo chat (Priority: P3)

**Goal**: a skill de perfil oferece "já tenho currículo".

**Independent Test**: quickstart.md cenário 10.

- [X] T018 [US4] Em `curriculo_base.py`, linha de comando: `lista`, `proposta <arquivo>` (não grava), `usar <arquivo>
  [--manter-perfil]` e `marcar <arquivo> [--idioma en]`
- [X] T019 [US4] Em `.agents/skills/analisar-perfil/SKILL.md`: o caminho "já tenho currículo" (mostrar a proposta,
  pedir o OK, `usar`, oferecer a busca); `python sincronizar_skills.py`
- [X] T020 [P] [US4] Testes da linha de comando em `tests/test_curriculo_base.py`
- [X] T021 [US4] Validar US4 pelo quickstart.md cenário 10

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T022 [P] `README.md` (primeiros passos: começar pelo currículo; "Seu currículo" nas vagas), `AGENTS.md` (comandos
  do `curriculo_base.py`) e `config.exemplo.json` (sem `curriculo_base`, que é pessoal; só citado no README)
- [X] T023 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [ ] T024 Com o OK do usuário, marcar o currículo dele (de `anexos/`) como "Seu currículo" pela página, sem trocar o
  perfil
- [X] T025 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch
  pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T005) → histórias.
- **US1 (T006–T010)** e **US2 (T011–T015)** dependem da Foundational; US2 usa o `marcar` da Foundational e não
  depende da US1.
- **US3 (T016–T017)** depende da US1 (perfil com a origem).
- **US4 (T018–T021)** depende da US1.
- Polish por último; T024 e T025 só com o OK do usuário.

## Parallel Opportunities

- T002 com T001; os testes [P] de cada história junto da implementação.
- US2 em paralelo com US1 depois da Foundational.
- T022 a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → quem tem currículo vai direto para as vagas, e as vagas mostram o
   currículo que a pessoa já tem.
2. US3 (completar depois) e US4 (chat).
3. Validação completa, currículo do usuário marcado (com OK) e commit com OK.
