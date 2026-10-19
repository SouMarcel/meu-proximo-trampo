---

description: "Tarefas da feature 020: Nerdin na busca de vagas (Windows)"
---

# Tasks: Nerdin na busca de vagas

**Input**: Design documents from `/specs/020-nerdin/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/nerdin.md, quickstart.md

**Tests**: `unittest` com HTML fictício e sem rede (constituição: funções puras novas ganham testes); o resto pelo
quickstart.

**Organization**: por história (US1–US5). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US5)

---

## Phase 1: Setup

- [X] T001 Rodar `python -m unittest discover -s tests` na worktree e anotar quantos testes passam antes da mudança
- [X] T002 [P] Criar `tests/dados/nerdin/lista.html` (página 1: 20 cards fictícios no formato da research R3, com
  empresas e vagas inventadas; incluir selo "Nova", ícone de urgente, Home Office, Híbrido, Presencial, card sem
  local, "Salário a combinar", uma faixa salarial, CLT, PJ, Freelancer, títulos que batem e que não batem com o cargo
  de teste, datas em ordem decrescente), `tests/dados/nerdin/lista-2.html` (página 2 com menos de 20 cards, alguns
  mais antigos que a janela) e `tests/dados/nerdin/vaga.html` (página de vaga com o JSON-LD `JobPosting`)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 `fontes/nerdin.py`: atributos do contrato (`NOME`, `PLATAFORMA`, `AREAS`, `TERMOS`, `MAX_DESCRICOES`,
  `MAX_PAGINAS`, `POR_PAGINA`, `PAUSA`), `_estado` zerado por `_comum.AO_ESQUECER`, `_baixar(url)` próprio (urllib,
  `_comum.AGENTE`, sem cookies, pausa de 3 s desde o último pedido, tempo limite 20 s, limite de 3 MB, 403/429/503 →
  bloqueio com `FonteErro`, sem nova tentativa) e `parada()`
- [X] T004 `fontes/nerdin.py`: `ler_lista(pagina)` com `html.parser` (classe `_Cards`, no molde de
  `fontes/linkedin.py`) e a normalização da data-model (id `nerdin-<n>`, título sem selo, local "Cidade, UF" ou
  "Remoto", `modelo_trabalho`, `remoto`, `tipo_emprego`, `tipo`, `salario`, `publicada_em`, `url` absoluta)
- [X] T005 Registrar `nerdin` em `fontes/__init__.py` (`import` e `FONTES`)

**Checkpoint**: a fonte lê uma página salva; nenhuma busca a usa ainda

---

## Phase 3: User Story 1 - Vagas da Nerdin na busca de sempre (Priority: P1) 🎯 MVP

**Goal**: a Nerdin traz vagas filtradas pelo cargo e pela janela para o relatório, sem repetir.

**Independent Test**: quickstart.md cenários 1 e 2.

- [X] T006 [US1] `fontes/nerdin.py`: `_lista_do_termo(termo, horas)` (páginas `vagas.php?busca=<cargo sem aspas>`
  e `&pagina=N`, até `MAX_PAGINAS`, parando com menos de `POR_PAGINA` cards, página vazia ou a última vaga fora da
  janela; guarda `(vagas, erro)` em `_estado["listas"]`; aviso de página ilegível)
- [X] T007 [US1] `fontes/nerdin.py`: `buscar(consulta, horas, por_termo)` (sem pedido fora do Brasil ou bloqueada;
  filtro por `_comum.bate_cargo`, janela, grupo remoto/país/cidade e modelos, cidade ou UF com a tabela das 27 UFs;
  sem repetir id; até `max(1, por_termo)`; o mesmo erro uma vez por cargo)
- [X] T008 [US1] `dash/banco.py`: `"Nerdin"` em `PLATAFORMAS`
- [X] T009 [P] [US1] `dash/dashboard.html`: `"Nerdin"` no array `PLATAFORMAS`, par `["nerdin.", "Nerdin"]` em
  `plataformaDoLink`, `.plat[data-p="Nerdin"] i { background: #f0a43a; }`
- [X] T010 [P] [US1] `tests/test_nerdin.py` com `nerdin._baixar` e a pausa substituídos: cards de `lista.html`
  (título sem selo, empresa, local, modelo, tipo, salário "a combinar" → None, faixa mantida, data, url, id); filtro
  de título; janela para a paginação; duas páginas sem repetir; lista lida uma vez para remoto e cidade do mesmo
  cargo; cidade/UF (sigla e nome do estado); consulta fora do Brasil sem pedido; página sem cards → aviso de ilegível

**Checkpoint**: `vagas.py buscar --fontes nerdin` traz vagas para o relatório

---

## Phase 4: User Story 2 - Ligada por padrão, desligável no painel (Priority: P1)

**Goal**: config nova já busca na Nerdin; a pessoa desliga no painel.

**Independent Test**: quickstart.md cenário 3 e cenário 4, passo 3.

- [X] T011 [US2] `filtros.py`: `FONTES_NAC` com `"nerdin": "Nerdin"` depois da Gupy; `FONTES_PADRAO = ["indeed",
  "gupy", "nerdin"]`
- [X] T012 [US2] `vagas.py`: `fontes_da_busca` usa `filtros.FONTES_PADRAO` quando o config não tem `fontes`
- [X] T013 [P] [US2] `config.exemplo.json`: `"fontes": ["indeed", "gupy", "nerdin"]`
- [X] T014 [US2] Testes: ajustar `tests/test_linkedin.py` (ordem de `fontes_nac` e `efetivos({})["fontes"]`); em
  `tests/test_nerdin.py`, config sem `fontes` → Nerdin na busca; config com `fontes` sem a Nerdin → nenhum pedido

**Checkpoint**: padrão com Nerdin; lista escolhida pela pessoa intacta

---

## Phase 5: User Story 3 - Descrição completa para a nota (Priority: P2)

**Goal**: as candidatas recebem a descrição da página da vaga.

**Independent Test**: quickstart.md cenário 4, passo 4.

- [X] T015 [US3] `fontes/nerdin.py`: `descrever(vaga)` (sem pedido se bloqueada; senão `link.extrair_jobposting`
  da página da vaga, até 12 000 caracteres)
- [X] T016 [P] [US3] Testes em `tests/test_nerdin.py`: `descrever` com `vaga.html`; bloqueada → texto que a vaga
  já tinha, sem pedido; `vagas.ler_descricoes` com a Nerdin respeita `MAX_DESCRICOES`

---

## Phase 6: User Story 5 - Respeito ao portal e bloqueio (Priority: P2)

**Goal**: pausa entre pedidos; no primeiro bloqueio, a Nerdin sai do resto da busca sem nova tentativa.

**Independent Test**: teste de bloqueio simulado (SC-005).

- [X] T017 [US5] Testes em `tests/test_nerdin.py` com `urllib.request.build_opener`/`urlopen` substituído: 429 na
  página 2 → vagas da página 1 entregues, aviso, nenhum pedido a mais na busca nem em `descrever`; `_comum.esquecer()`
  libera de novo; pausa mínima entre dois pedidos; nenhum cabeçalho `Cookie`

---

## Phase 7: User Story 4 - Adicionar uma vaga da Nerdin pelo link (Priority: P3)

**Goal**: link da Nerdin no Adicionar Vaga com portal, dados e o mesmo id da busca.

**Independent Test**: quickstart.md cenário 4, passo 5.

- [X] T018 [US4] `fontes/nerdin.py`: `id_do_link(url)`
- [X] T019 [US4] `fontes/link.py`: `("nerdin.", "Nerdin")` em `plataforma()`; ramo Nerdin em `ler()` (import de
  `nerdin` dentro da função; id de `id_do_link`; página por `extrair_jobposting`)
- [X] T020 [P] [US4] Testes: `id_do_link` (com e sem `www`, com parâmetros, link de outro site → None); `link.ler`
  com `link._baixar` substituído devolve `plataforma "Nerdin"` e id `nerdin-<n>`

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T021 [P] `README.md`: Nerdin na lista de portais, no diagrama, na tabela da chave `fontes` (novo padrão), nos
  termos/avisos e no checklist; `dash/README.md`: prefixo `nerdin-` e valor `Nerdin` de `plataforma`
- [X] T022 [P] `AGENTS.md` (linha de abertura com os portais) e `.agents/skills/buscar-vagas/SKILL.md` (descrição,
  portais, exemplo de `--fontes`, parágrafo do portal); depois `python sincronizar_skills.py` e `--conferir`
- [X] T023 Rodar `python -m unittest discover -s tests` (tudo passa) e a busca real pequena do quickstart cenário 2,
  com o OK da pessoa
- [X] T026 [US1] Teste na branch pessoal: a busca de "scrum master" com janela de 7 dias deu zero (a última vaga
  da Nerdin era de 13 dias antes). Decisão da pessoa: a janela segue o painel (máximo 30 dias) e o painel ganha
  "Últimos 15 dias" (`filtros.JANELAS`, 360 h); README da chave `janela_horas`; teste em `tests/test_nerdin.py`
- [ ] T024 Procurar dados pessoais nos arquivos alterados; commit na branch `020-nerdin`; merge na branch pessoal; com o OK
  da pessoa, acrescentar `nerdin` em `fontes` no `config.json` pessoal; reiniciar o dashboard (`--sem-navegador`) e
  passar o quickstart cenário 4 com a pessoa
- [ ] T025 Com o OK da pessoa: merge na `master`, `git push origin master`, `git merge master` na branch pessoal, apagar a
  worktree e a branch; `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T005) → US1 (T006–T010) → US2 (T011–T014).
- US3 (T015–T016), US5 (T017) e US4 (T018–T020) dependem só da Foundational e de T006–T007; podem seguir em
  qualquer ordem depois do US1.
- Polish (T021–T025) no fim; T024 e T025 só com o OK da pessoa.

### Parallel Opportunities

- T002 enquanto T001 roda.
- T009 e T010 junto com T008.
- T013 junto com T011–T012.
- T021 e T022 juntos.

## Implementation Strategy

1. MVP: Setup + Foundational + US1 → `--fontes nerdin` funciona e é testado sem rede.
2. US2 → a Nerdin passa a vir ligada por padrão.
3. US3 + US5 → descrição e bloqueio.
4. US4 → Adicionar Vaga.
5. Documentação, verificação real, teste na branch pessoal e entrega.
