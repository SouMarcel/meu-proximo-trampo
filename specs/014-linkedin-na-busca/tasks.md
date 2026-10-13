---

description: "Tarefas da feature 014: LinkedIn na busca de vagas (Windows)"
---

# Tasks: LinkedIn na busca de vagas

**Input**: Design documents from `/specs/014-linkedin-na-busca/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/linkedin.md, quickstart.md

**Tests**: `unittest` com HTML fictício e sem rede (constituição); o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Conferir que as referências do `vagas.py` (`ref13-*.txt` no scratchpad) e os 199 testes ainda batem
- [X] T002 Emenda 2.0.0 da constituição em `.specify/memory/constitution.md`: princípio VI reescrito (research §7),
  relatório de impacto no topo, versão e data; `AGENTS.md` com a linha "Respeite os portais" reescrita

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Contrato: atributo opcional `GLOBAL` documentado em `fontes/__init__.py`; `vagas.atende` aceita a consulta
  global para `POR_PAIS=False` ou `GLOBAL=True`
- [X] T004 Em `filtros.py`: `FONTES_NAC` (indeed, gupy, linkedin, startupjobs); `efetivos` devolve `fontes` (padrão
  `["indeed","gupy"]`); `validar` aceita `fontes` (pelo menos um, só os conhecidos); `opcoes()["fontes_nac"]`
  `[{nome, rotulo, termos, precisa}]`; `consultas` cria o grupo global também com o LinkedIn nos portais e a busca
  internacional ligada
- [X] T005 [P] Testes do contrato e da config em `tests/test_linkedin.py`: `atende` com `GLOBAL`, `fontes` validado,
  grupo global só com o LinkedIn

**Checkpoint**: contrato e configuração prontos; com o LinkedIn fora, nada muda

---

## Phase 3: User Story 1 - Vagas do LinkedIn na busca de sempre (Priority: P1) 🎯 MVP

**Goal**: o LinkedIn traz vagas para o relatório, sem repetir.

**Independent Test**: quickstart.md cenários 2, 3, 7 e 8.

- [X] T006 [US1] `fontes/linkedin.py`: atributos (contrato), `_baixar` próprio (sem cookies, sem seguir
  redirecionamento, sem nova tentativa, pausa de 3 a 7 s desde o último pedido), `ler_lista(html)` com `html.parser`
  (`base-search-card`, `data-entity-urn`, título, empresa, local, `time[datetime]`), `buscar(consulta, horas,
  por_termo)` com uma página de 10 vagas por consulta, `descrever(vaga)` reaproveitando `link._ler_linkedin`; registrar em
  `fontes/__init__.py`
- [X] T007 [US1] `vagas.documento()` copia `tipo_emprego` da fonte, quando houver
- [X] T008 [P] [US1] `tests/dados/linkedin/lista.html` e `vaga.html` fictícios; testes: três cards (sem empresa, sem
  data), id `li-<n>` igual ao do link, mesma vaga em dois grupos uma vez, `descrever` só das candidatas, LinkedIn
  desligado sem nenhum pedido
- [X] T009 [US1] Validar US1 pelo quickstart.md cenários 2, 3, 7 e 8 (referências iguais com o LinkedIn desligado)

---

## Phase 4: User Story 2 - Todos os tipos de vaga (Priority: P1)

**Goal**: local, modelo, tipos de emprego e janela certos em cada grupo; critérios de sempre.

**Independent Test**: quickstart.md cenários 1 e 4.

- [X] T010 [US2] Em `fontes/linkedin.py`: `parametros(consulta, horas, tipos)` (research §2 e data-model: `location`
  país em inglês / cidade / "Worldwide", `distance` em milhas, `f_WT` por grupo, `f_JT` pelos `tipos_emprego`, `f_TPR`),
  `modelo_trabalho` quando o `f_WT` tem um valor só, `tipo_emprego(texto)` (research §5) aplicado na descrição
- [X] T011 [P] [US2] Testes: parâmetros dos seis grupos (SC-001), tipos e janela, modelo da vaga, tipo de emprego
  PT/EN, vaga presencial fora da mudança e estágio sem estágio marcado em Fora dos critérios
- [X] T012 [US2] Validar US2 pelo quickstart.md cenários 1 e 4

---

## Phase 5: User Story 3 - Portais na página (Priority: P2)

**Goal**: ligar e desligar os portais no painel, com o contador.

**Independent Test**: quickstart.md cenário 9.

- [X] T013 [US3] Em `dash/dashboard.html`, "Filtros da busca": seção Portais (caixas com rótulo e termos de cada
  portal; startup.jobs avisa da chave), grava `fontes`, exige pelo menos um; `contarConsultas` mostra à parte as
  consultas do LinkedIn (todos os grupos, mais o global com a busca internacional ligada) com o aviso acima de 20
- [X] T014 [US3] Validar US3 pelo quickstart.md cenário 9 (servidor no roteiro, Chrome sem janela, captura)

---

## Phase 6: User Story 4 - Respeito ao portal e bloqueio (Priority: P2)

**Goal**: parar no primeiro bloqueio, avisar uma vez, seguir com as outras fontes.

**Independent Test**: quickstart.md cenários 5 e 6.

- [X] T015 [US4] Em `fontes/linkedin.py`: estado `_bloqueado` (429, 999, 4xx/5xx, redirecionamento para login) que
  faz `buscar` e `descrever` levantarem `FonteErro` sem pedido (o primeiro com a mensagem, os seguintes com
  `repetido=True`); zerado em `_comum.esquecer()`; "não consegui ler as vagas do LinkedIn" quando a resposta não tem
  cards reconhecíveis
- [X] T016 [P] [US4] Testes: 429 na 2ª consulta sem pedido depois (SC-004), aviso uma vez, outras fontes no
  resultado, redirecionamento para login, nenhum cabeçalho de cookie, reset na busca seguinte
- [X] T017 [US4] Validar US4 pelo quickstart.md cenários 5 e 6

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T018 [P] `README.md` (fonte LinkedIn: o que é, consulta não oficial, bloqueio temporário, termos; seção Portais;
  roteiro) e skill `.agents/skills/buscar-vagas/SKILL.md` (LinkedIn como fonte, `--fontes`, o aviso de bloqueio);
  `python sincronizar_skills.py`
- [X] T019 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T020 Busca real pequena (quickstart cenário 10), só com o OK do usuário, sem gravar no banco dele
- [X] T021 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch
  pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T005) → histórias.
- **US1 (T006–T009)** primeiro; **US2 (T010–T012)** usa o módulo da US1; **US4 (T015–T017)** usa o `_baixar` da US1;
  **US3 (T013–T014)** depende só da Foundational.
- Polish por último; T020 e T021 só com o OK do usuário.

## Parallel Opportunities

- Os testes [P] de cada história junto da implementação.
- T013 (página) em paralelo com T010 e T015 (arquivos diferentes).
- T018 a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → vagas do LinkedIn no relatório.
2. US2 (tipos de vaga), US4 (bloqueio) e US3 (painel).
3. Validação completa, busca real com OK e commit com OK.
