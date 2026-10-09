---

description: "Tarefas da feature 009: fontes internacionais e elegibilidade (Windows)"
---

# Tasks: Fontes internacionais e elegibilidade

**Input**: Design documents from `/specs/009-fontes-internacionais/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/fontes-e-config.md, quickstart.md

**Tests**: `unittest` com respostas gravadas de cada fonte e um conjunto de anúncios de elegibilidade
(constituição); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Gravar em `tests/dados/` uma resposta real de cada fonte (Remotive, Himalayas, RemoteOK, Jobicy, We Work Remotely, Get on Board e uma empresa pública em cada um de Greenhouse, Lever e Ashby): **uma consulta por fonte** (aprovada com o plano), recortada a poucas vagas, sem dados pessoais; anotar o formato real de cada uma em `research.md` se diferir do previsto
- [X] T002 Conferir que as referências do `vagas.py` (scratchpad, specs 005 e 008) ainda batem, para provar SC-001 no fim

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Criar `fontes/_comum.py`: `baixar_json(url, params)` e `baixar_texto(url)` (urllib, `User-Agent` da ferramenta, tempo limite, erro legível), `bate_cargo(titulo, termo)` (frase exata entre aspas ou todas as palavras significativas), `texto(html)` (reaproveita `link.texto_de_html`, até 12.000 caracteres), `data_iso(valor)` e uma memória por busca (`lembrar(chave, fn)`) para não consultar a mesma lista duas vezes na mesma busca
- [X] T004 Em `filtros.py`: `internacional.fontes`, `empresas`, `frases_restricao`, `frases_positivas` em `efetivos()` (padrões vazios) e `validar()` (fontes do catálogo `FONTES_INT`; empresas por `ats.reconhecer(url)` com erro explicado; limites 50/30/120); `opcoes()` com `fontes_int` (nome, rótulo, termos); `consultas()` com o grupo `internacional:global` por cargo em inglês (`global: True`) quando a busca internacional está ligada; `area_da_vaga` para o grupo global (país pela restrição ou "mundo todo")
- [X] T005 Em `vagas.py`: as fontes da busca = `fontes` + `internacional.fontes` (quando ligada); `atende(fonte, consulta)` considera `POR_PAIS` (globais só nas fontes `POR_PAIS = False`, por país só nas outras); `gravar_resultado` grava `restricao_local`, `ats`, `moeda` da fonte e `sinais`; em `fontes/__init__.py`, o contrato (`POR_PAIS`, `TERMOS`) e o registro das fontes novas
- [X] T006 [P] `tests/test_fontes_int.py` (base): `_comum.bate_cargo`, consultas globais, fontes por `POR_PAIS` com fontes falsas

**Checkpoint**: estrutura pronta; referências do `vagas.py` iguais

---

## Phase 3: User Story 1 - Mais vagas do exterior (Priority: P1) 🎯 MVP

**Goal**: as seis fontes novas, desligadas por padrão, escolhidas no painel.

**Independent Test**: quickstart.md cenários 1, 2, 3 e 9.

- [X] T007 [P] [US1] `fontes/remotive.py` (lista recente uma vez por busca, filtrada pelo cargo; `candidate_required_location` → `restricao_local`; salário em texto; `url`; descrição HTML → texto)
- [X] T008 [P] [US1] `fontes/himalayas.py` (página recente; `locationRestrictions` → `restricao_local`; `minSalary`/`maxSalary`/`currency`; `applicationLink`)
- [X] T009 [P] [US1] `fontes/remoteok.py` (pula o item 0, o aviso legal; `location`; `salary_min`/`salary_max` em USD; `apply_url`; `url` para a vaga original)
- [X] T010 [P] [US1] `fontes/jobicy.py` (por cargo; `jobGeo`; `annualSalaryMin/Max` e `salaryCurrency`; `url`)
- [X] T011 [P] [US1] `fontes/weworkremotely.py` (RSS com `xml.etree`; título "Empresa: Cargo"; `region`; `type`; `link`)
- [X] T012 [P] [US1] `fontes/getonboard.py` (por cargo; `remote`/`remote_modality`; `countries`; `min_salary`/`max_salary`; `lang` → idioma)
- [X] T013 [US1] Em `dash/dashboard.html`, painel internacional: seção **Fontes** (caixas com o rótulo e os termos de cada uma, vindas de `opcoes.fontes_int`), contagem de consultas somando as globais; detalhe da vaga com a restrição do portal e o link de candidatura
- [X] T014 [P] [US1] Testes em `tests/test_fontes_int.py`: cada fonte com a resposta gravada (vagas normalizadas, filtro pelo cargo, restrição, moeda, salário, links, id prefixado); fonte com erro de rede não derruba as outras
- [X] T015 [US1] Validar US1 pelo quickstart.md cenários 1, 2, 3 e 9

---

## Phase 4: User Story 2 - Elegibilidade antes da nota (Priority: P1)

**Goal**: cortes e sinais sem IA, com o motivo.

**Independent Test**: quickstart.md cenários 5, 6 e 7.

- [X] T016 [US2] Em `filtros.py`, `elegibilidade(v, f) -> {motivos, sinais}` (research.md §4): países e regiões exigidos (campo do portal + frases), não patrocina / patrocina / relocation, regras 1 a 6, frases próprias; `criterios()` acrescenta os motivos para vaga internacional; `sinais(v, f)` para gravar
- [X] T017 [US2] Em `vagas.py`, `dash/banco.py` (`criar_de_link`, `criar_manual`, `aplicar_criterios` após análise) e `dash/analise.py` (sinais no pedido): sinais gravados e recalculados com a vaga
- [X] T018 [US2] Em `dash/dashboard.html`: sinais como etiqueta verde na listagem, no card e no detalhe; painel internacional com as **Frases** (duas caixas, uma frase por linha)
- [X] T019 [P] [US2] `tests/test_elegibilidade.py`: conjunto de anúncios (US only sem sponsor; com autorização; LATAM aceita; Europa only; presencial em Lisboa com e sem morar fora; sponsor disponível; relocation; ambíguo; "US only" + "we sponsor"; frase própria) com o resultado esperado (SC-002, SC-003)
- [X] T020 [US2] Validar US2 pelo quickstart.md cenários 5, 6 e 7

---

## Phase 5: User Story 3 - Empresas acompanhadas (Priority: P2)

**Goal**: vagas de empresas no Greenhouse, Lever e Ashby pelo link de carreiras.

**Independent Test**: quickstart.md cenário 4.

- [X] T021 [US3] `fontes/ats.py`: `reconhecer(url)` (Greenhouse `boards.greenhouse.io/<e>` e `job-boards.greenhouse.io/<e>`, Lever `jobs.lever.co/<e>`, Ashby `jobs.ashbyhq.com/<e>`; outro → `ValueError` explicado) e `buscar` (uma consulta por empresa por busca, filtrada pelos cargos; `ats` e `url_candidatura`; local e modelo de trabalho)
- [X] T022 [US3] Em `dash/dashboard.html`, painel internacional: **Empresas que você acompanha** (colar o link, lista com sistema e remover; a validação do servidor normaliza e explica)
- [X] T023 [P] [US3] Testes: `reconhecer` (três sistemas e um link de outro sistema), `buscar` com as respostas gravadas
- [X] T024 [US3] Validar US3 pelo quickstart.md cenário 4

---

## Phase 6: User Story 4 - Adicionar Vaga e frases da pessoa (Priority: P3)

**Goal**: links do Greenhouse, Lever e Ashby lidos pela API; plataformas novas reconhecidas.

**Independent Test**: quickstart.md cenário 8.

- [X] T025 [US4] Em `fontes/link.py`: vaga do Greenhouse, Lever e Ashby pela API pública da vaga (dados, `ats`, `url_candidatura`, `restricao_local`); `plataforma(host)` reconhece as fontes novas; em `dash/banco.py`, `PLATAFORMAS` com as novas (e na página)
- [X] T026 [P] [US4] Testes: leitura de uma vaga de cada ATS com a resposta gravada (rede substituída)
- [X] T027 [US4] Validar US4 pelo quickstart.md cenário 8

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T028 [P] `README.md` (fontes internacionais, como ligar, empresas, frases, elegibilidade e os termos de uso de cada fonte) e `dash/README.md` (campos novos da vaga); `config.exemplo.json` com os campos novos vazios
- [X] T029 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T030 Com o OK do usuário, a busca internacional real pequena do cenário 10 (duas fontes, um cargo)
- [X] T031 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T006) → histórias.
- **US1 (T007–T015)**: as seis fontes são independentes entre si ([P]); T013 depois de T004.
- **US2 (T016–T020)** depende da Foundational; **US3 (T021–T024)** depende de T003–T005;
  **US4 (T025–T027)** depende de T021.
- Polish por último; T030 e T031 só com o OK do usuário.

## Parallel Opportunities

- As seis fontes (T007–T012) e os testes de cada uma em paralelo.
- T019 (elegibilidade) em paralelo com as fontes.
- T028 (README) a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → fontes novas com a elegibilidade cortando o impossível.
2. US3 (empresas) e US4 (Adicionar Vaga).
3. Validação completa, busca real pequena e commit com OK.
