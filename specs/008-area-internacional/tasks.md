---

description: "Tarefas da feature 008: área de vagas internacionais (Windows)"
---

# Tasks: Área de vagas internacionais

**Input**: Design documents from `/specs/008-area-internacional/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/config-e-api.md, quickstart.md

**Tests**: `unittest` para configuração, consultas, área, idioma e salário (constituição), com a fonte
falsa; saída de referência do `vagas.py` (spec 005); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Conferir que a saída de referência do `vagas.py buscar --gravar` com a fonte falsa (scratchpad, spec 005) ainda bate com o código atual, para servir de prova de SC-002 no fim

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 Em `filtros.py`: constantes `IDIOMAS` (`pt` português, `en` inglês, `es` espanhol, `fr` francês, `de` alemão, `it` italiano), `REGIOES` (`brasil`, `latam`, `americas`, `mundo`), `CONTRATACOES` (`contractor`, `eor`, `pj`, `clt`); `efetivos()` com `idiomas_aceitos` e o `internacional` completo (data-model.md, padrões neutros; formato antigo lido); `validar()` dos campos novos (listas, `salario_min_anual_usd` ≥ 0, `fuso_horas` 0–12, países por `pais_pt`; `ativo` exige países e cargos e **não** exige `modelos.remoto`); `opcoes()` com `idiomas`, `regioes`, `contratacao`
- [X] T003 Em `filtros.py`: `pais_do_local(texto) -> str | None` (país em português pelos nomes em PT e EN de `PAISES`, siglas e cidades comuns — US/USA/United States, UK/London —, e regiões "mundo todo" para Worldwide/Anywhere/Global, "Europa" para Europe/EMEA, "América Latina" para LATAM) e `area_da_vaga(v, f) -> (area, pais)` (grupo `internacional:`/`mudanca:` → internacional com o país; local reconhecido fora do país da pessoa → internacional; senão nacional)
- [X] T004 [P] `tests/test_internacional.py`: validação e padrões, formato antigo, `pais_do_local`, `area_da_vaga` (grupo, local, vaga antiga sem `area`)

**Checkpoint**: configuração e área prontas

---

## Phase 3: User Story 1 - Habilitar a busca internacional e ver as vagas separadas (Priority: P1) 🎯 MVP

**Goal**: consultas internacionais independentes do remoto nacional; vaga marcada com área e país; aba e etiqueta na página.

**Independent Test**: quickstart.md cenários 1, 3 e 9.

- [X] T005 [US1] Em `filtros.py`, `consultas()`: cada consulta com `area`; a internacional roda com `inter.ativo` mesmo sem `modelos.remoto` (remoto em cada país); `resumo()` atualizado; em `vagas.py`, `gravar_resultado` grava `area` e `pais_vaga` (por `area_da_vaga`) em cada vaga
- [X] T006 [US1] Em `dash/banco.py`: `listar_vagas`/`obter` completam `area` e `pais_vaga` das vagas antigas (deduzidos, sem gravar); `criar_manual` e `criar_de_link` gravam `area` e `pais_vaga` (do formulário ou do palpite)
- [X] T007 [US1] Em `dash/dashboard.html`: aba **Internacional** (`tab-internacional`, contador próprio), Relatório de Vagas só `nacional` e o mesmo relatório para `internacional` (filtro por `S.aba`); helper `areaDe(v)`; etiqueta `intTag(v)` ("Internacional · país · moeda", cor própria) em `relItemHTML`, `cardHTML`, `renderLista` e `renderDetalhe`; filtro de área no Quadro (todas, nacional, internacional), lembrado no navegador; aba Internacional vazia e desligada explica e abre o painel internacional
- [X] T008 [P] [US1] Testes em `tests/test_internacional.py`: consultas com área, internacional sem remoto nacional, área gravada pela busca com a fonte falsa
- [X] T009 [US1] Validar US1 pelo quickstart.md cenários 1, 3 e 9

---

## Phase 4: User Story 2 - Filtros da busca internacional (Priority: P1)

**Goal**: painel próprio; morar fora; moeda e salário; caixas na análise.

**Independent Test**: quickstart.md cenários 2, 4 e 7.

- [X] T010 [US2] Em `filtros.py`: com `aceita_mudar`, consultas `mudanca:<país>` sem filtro de remoto em `paises_mudanca` (ou nos países de interesse); `salario_anual_usd(v)` (texto de salário do portal: números, "k", período ano/mês/hora; só USD) e corte em `criterios()` para vaga internacional abaixo de `salario_min_anual_usd`; `criterios_extra()` com regiões, contratação, fuso e as caixas quando a internacional está ligada
- [X] T011 [US2] Em `dash/dashboard.html`: painel **Filtros da busca internacional** (`dlg-filtros-int`): ligar, países (lista com busca, como hoje), cargos em inglês, regiões, moedas, salário mínimo anual (USD), fuso, contratação e as caixas (aceito morar fora com países, passaporte, autorização com países, precisa de sponsor), contagem de consultas; grava pelo `PUT /api/config`; o trecho "também vagas remotas no exterior" sai do painel nacional
- [X] T012 [US2] Na skill `buscar-vagas` (`.agents/skills/buscar-vagas/SKILL.md`): em vagas internacionais, alertar sobre autorização de trabalho, sponsor, fuso e forma de contratação conforme os critérios do usuário; rodar `python sincronizar_skills.py`
- [X] T013 [P] [US2] Testes: validação do painel (ligada sem países/cargos), consultas de mudança, `salario_anual_usd` (anual, mensal, por hora, "k", outra moeda → None) e corte
- [X] T014 [US2] Validar US2 pelo quickstart.md cenários 2, 4 e 7

---

## Phase 5: User Story 3 - Idiomas aceitos (Priority: P2)

**Goal**: filtro geral de idioma, sem IA, confirmado pela análise.

**Independent Test**: quickstart.md cenários 6 e 8.

- [X] T015 [US3] Em `filtros.py`: `idioma_texto(texto) -> str | None` (palavras comuns de PT, EN, ES, FR, DE, IT; mínimo de 25 reconhecidas e folga de 1,5× sobre o segundo) e `idioma_da_vaga(v)` (campo do portal `idioma`/`lang`, depois detecção); corte em `criterios()` com "Vaga em <idioma>; você aceita <lista>"; `vagas.executar` grava `idioma` nas candidatas antes do corte; `criterios_extra()` com os idiomas aceitos
- [X] T016 [US3] Em `dash/banco.py`, `validar_analise` aceita `idioma` (código de `filtros.IDIOMAS`), que vale mais que a detecção; skill `buscar-vagas`: campo `idioma` no JSON da análise; em `dash/dashboard.html`, "Idiomas aceitos" no painel nacional (pílulas, vazio = todos)
- [X] T017 [P] [US3] Testes: idioma de textos em PT, EN, ES, FR; texto curto e misturado → None; corte e mensagem; análise com `idioma`
- [X] T018 [US3] Validar US3 pelo quickstart.md cenários 6 e 8

---

## Phase 6: User Story 4 - Área no Adicionar Vaga e portais por área (Priority: P3)

**Goal**: campo Área com palpite; fonte só nas consultas da sua área.

**Independent Test**: quickstart.md cenários 5 e 10.

- [X] T019 [US4] Fontes declaram `AREAS` (`fontes/indeed.py`: nacional e internacional; `fontes/gupy.py`: nacional; `fontes/startupjobs.py`: nacional e internacional) e o contrato em `fontes/__init__.py`; `vagas.executar` pula a fonte nas consultas de área que ela não atende (total de consultas e progresso coerentes)
- [X] T020 [US4] Em `dash/dashboard.html`, Adicionar Vaga: campo **Área** (nacional/internacional) e país, com palpite pelo local lido do link (`pais_do_local` no servidor, devolvido em `parcial`/vaga) e no formulário à mão; etiqueta no aviso de vaga repetida
- [X] T021 [P] [US4] Testes: fonte só nacional não chamada nas consultas internacionais (fonte falsa com `AREAS`); palpite de área no link
- [X] T022 [US4] Validar US4 pelo quickstart.md cenários 5 e 10

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T023 [P] `README.md` (área internacional, painel, idiomas, etiqueta, configuração) e `dash/README.md` (campos novos da vaga); `config.exemplo.json` com os campos novos nos padrões neutros
- [X] T024 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T025 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal, configurar `idiomas_aceitos` PT e EN no `config.json` da branch pessoal (pedido do usuário), reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T004) → histórias.
- **US1 (T005–T009)** primeiro; **US2 (T010–T014)**, **US3 (T015–T018)** e **US4 (T019–T022)**
  mexem em `filtros.py` e `dashboard.html` e seguem em sequência.
- Polish por último; T025 só com o OK do usuário.

## Parallel Opportunities

- Testes (T004, T008, T013, T017, T021) em `tests/test_internacional.py`, junto com cada função.
- T012 (skill) e T023 (README) em arquivos próprios.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → busca internacional separada, com filtros próprios.
2. US3 (idiomas) e US4 (Adicionar Vaga e portais por área).
3. Validação completa e commit com OK.
