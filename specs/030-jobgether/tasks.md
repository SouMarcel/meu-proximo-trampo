---
description: "Tarefas da feature 030: JobGether na busca (Windows)"
---

# Tasks: JobGether na busca de vagas

**Input**: spec.md, plan.md, research.md (R1–R7, D1–D8), data-model.md, contracts/jobgether.md, quickstart.md.
Mecanismos comuns da spec 026 em `fontes/_comum.py`.

**Testes**: incluídos. O roteiro `docs/novo-portal.md` (seção 5) pede testes sem rede para todo portal novo. Todos ficam
em `tests/test_jobgether.py` e trocam `jobgether._baixar`; nenhum pedido sai para a rede.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 [P] Amostras fictícias em `tests/dados/jobgether/`, no formato da research R3, com empresas e títulos
  trocados:
  - `lista.json`: página 1, `hasMore: true`, com
    - duas vagas cujo título bate com "project manager" (uma com `salaryRange` "65000-70000 USD" e outra sem);
    - uma que não bate ("NetSuite Consultant");
    - uma "Part time";
    - uma com `remote` híbrido;
    - uma republicada, com `id` da API diferente do id da URL;
  - `lista-2.json`: página 2, `hasMore: false`, com uma vaga dentro da janela e uma mais antiga que ela;
  - `erro-local.json`: o 400 `application/problem+json` com `code: "invalid_parameter"` e `field: "locations"`.

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 Esqueleto de `fontes/jobgether.py` pelo contrato (contracts §1), no molde de `fontes/infojobs.py`:
  - constantes `NOME = "jobgether"`, `PLATAFORMA = "JobGether"`, `AREAS = ("nacional", "internacional")`,
    `POR_PAIS = True`, `GLOBAL = True`, `TERMOS`, `URL = "https://jobgether.com/api/v1/jobs"`, `MAX_PAGINAS = 3`,
    `POR_PAGINA = 25`, `PAUSA = (2.0, 2.0)`, `VAR_PAUSA = "JOBGETHER_PAUSA"`, `PAUSA_MIN = 2.0`,
    `ESPERA = timedelta(hours=24)` e `ARQ_ESPERA = .cache/jobgether-espera.json`;
  - `_estado` (`bloqueado`, `ultimo`, `pausa`, `listas`, `avisos`) e `_esquecer` registrado em `_comum.AO_ESQUECER`;
  - `pausa()`, `aviso_pausa(consultas)` (até `consultas × MAX_PAGINAS` pedidos), `_pausar()`, `espera()`, `parada()`
    e `_bloquear(motivo)`;
  - `_baixar(corpo)`, que faz um POST JSON com `urllib` (D1): agente `_comum.AGENTE`, sem cookies, sem nova tentativa;
    403 e 429 vão para `_bloquear`; o resto, como na tabela D2;
  - `id_do_link(url)`: `jobgether-<24 hex>` para `https://(www.)jobgether.com/offer/<24 hex>-…`, e `None` para outro
    link.
- [X] T003 Registro:
  - `fontes/__init__.py` (import e `FONTES`);
  - `filtros.FONTES_NAC["jobgether"] = "JobGether"`, **fora** de `FONTES_PADRAO`;
  - `filtros.FONTES_GLOBAIS = ("linkedin", "jobgether")`, usado na condição da consulta global de
    `filtros.consultas` no lugar de `"linkedin" in f.get("fontes", [])`;
  - `dash/banco.PLATAFORMAS` ganha "JobGether";
  - `fontes/link.plataforma()` reconhece `("jobgether.", "JobGether")`.

**Checkpoint**: a suíte atual passa (`PY -m unittest discover -s tests`) com o módulo registrado e sem buscar nada.

## Phase 3: User Story 1 - Remotas abertas ao Brasil na busca nacional (P1) 🎯 MVP

**Goal**: com o JobGether ligado, a busca nacional traz as remotas que aceitam quem mora no país da pessoa.

**Independent Test**: respostas simuladas. Vagas com título, empresa, local aceito, data, link e salário quando houver.

- [X] T004 [US1] `normalizar(item)` em `fontes/jobgether.py`, pela tabela do data-model:
  - id pela URL, ou pelo `id` da API sem a URL;
  - `local` "Remoto (<location curto>)" e `restricao_local` com o texto curto, até 200 caracteres;
  - `remoto: true`, e `modelo_trabalho` "hibrido" se `remote` falar em hybrid, senão "remoto";
  - `publicada_em` pelo `_comum.data_iso(postedAt)`;
  - `salario` pelo `_comum.salario` sem período, e `moeda` (3 letras do fim de `salaryRange`);
  - `tipo` em português; `tipo_emprego` só para part time, internships, fixed term e freelance ("Full time" fica sem
    código);
  - `url_candidatura: None` e `descricao: ""`;
  - item sem `title` ou sem id vira `None`.
- [X] T005 [US1] `buscar(consulta, horas, por_termo)` em `fontes/jobgether.py`:
  - consulta da cidade (`grupo == "local"`) ou de mudança (`grupo` começa com `"mudanca:"`) devolve `([], [])` sem
    pedido;
  - em espera, nenhum pedido e o aviso uma vez por busca;
  - depois de um bloqueio nesta busca, nenhum pedido a mais;
  - o cargo sem aspas; o local do país pela tabela de slugs (D3); `includeHybrid: true` na consulta do país quando
    `"hibrido"` está em `consulta["modelos"]`;
  - páginas por D4: `sort: "date"`, `limit: 25`, a seguinte só com `hasMore` e com a mais antiga ainda na janela, até
    `MAX_PAGINAS`;
  - a mesma consulta (cargo, local, híbrido) é lida uma vez por busca (`_estado["listas"]`);
  - o resultado passa por `_comum.filtrar` (título, janela e remoto) e é cortado em `por_termo`.
- [X] T006 [P] [US1] Testes em `tests/test_jobgether.py`:
  - campos da vaga (salário "US$ 65.000–70.000" e moeda USD, sem salário, part time com `meio_periodo`, híbrido);
  - "NetSuite Consultant" fica de fora;
  - a janela corta a página 2, e `hasMore: false` não pede página 3;
  - corpo do POST com `locations: ["brazil"]` e `includeHybrid` na consulta do país;
  - consulta da cidade sem pedido;
  - a mesma consulta lida uma vez;
  - a vaga republicada fica com o id da URL.

**Checkpoint**: US1 testável sozinha.

## Phase 4: User Story 2 - Internacional, por país e no mundo todo (P1)

**Goal**: o JobGether roda em cada país da busca internacional e na consulta global (`anywhere`).

**Independent Test**: plano de consultas com a internacional ligada; corpo dos pedidos simulados.

- [X] T007 [US2] Em `fontes/jobgether.py`:
  - tabela `SLUGS = {"usa": "united-states", "uk": "united-kingdom"}`; os outros nomes de `filtros.PAISES` com hífen
    no lugar do espaço;
  - consulta global (`consulta.get("global")`) com `locations: ["anywhere"]`;
  - 400 com `field == "locations"` vira o aviso "o JobGether não reconhece o local <slug>", uma vez por busca para cada
    slug; as outras consultas seguem.
- [X] T008 [P] [US2] Testes em `tests/test_jobgether.py`:
  - Portugal → `portugal`, Estados Unidos → `united-states`, global → `anywhere`;
  - 400 de local (`erro-local.json`): aviso uma vez e a consulta seguinte roda;
  - consulta de mudança sem pedido;
  - `filtros.consultas` cria a consulta global com o JobGether nas fontes e a internacional ligada, sem outras fontes
    do exterior;
  - `vagas.atende` aceita as consultas nacionais e internacionais.

## Phase 5: User Story 3 - Desligado por padrão, com os termos à vista (P1)

**Goal**: o JobGether aparece no painel, desligado, com o resumo dos termos.

**Independent Test**: configuração nova sem pedido ao JobGether; lista do painel com o `termos`.

- [X] T009 [US3] Texto de `TERMOS` em `fontes/jobgether.py`, conforme a FR-011 e contracts §1: API oficial para
  assistentes; os termos do JobGether proíbem acesso automatizado; decisão registrada na spec 030; vagas sem descrição;
  espera de 24 h no bloqueio; a candidatura é no site da empresa. Conferir que `config.exemplo.json` e `FONTES_PADRAO`
  não mudam.
- [X] T010 [P] [US3] Testes em `tests/test_jobgether.py`:
  - `vagas.fontes_da_busca` com a configuração padrão não traz `jobgether`;
  - portal desligado: zero chamadas a `jobgether._baixar` numa busca simulada;
  - `filtros.fontes_nac()` lista `jobgether` com o `termos` do módulo.

## Phase 6: User Story 4 - Pausa, bloqueio e espera (P1)

**Goal**: pausa de 2 s ajustável e parada no primeiro bloqueio, com 24 h de espera.

**Independent Test**: bloqueio simulado com zero novas tentativas e zero pedidos durante a espera.

- [X] T011 [US4] Em `fontes/jobgether.py`:
  - 403 e 429 → `_bloquear` (grava a espera, `FonteErro` com o fim dela), sem nova tentativa e sem pedidos a mais na
    busca;
  - 500, 504, outro 4xx e erro de rede → erro só da consulta;
  - corpo fora do formato → "não consegui ler as vagas do JobGether (a API pode ter mudado)".

  No `.env.exemplo`, a linha `# JOBGETHER_PAUSA=2   # padrão 2 s; mínimo 2 s (API oficial, Crawl-delay do site)`.
- [X] T012 [P] [US4] Testes em `tests/test_jobgether.py`:
  - pausa: o padrão de 2 s, `JOBGETHER_PAUSA=5`, `1` vira 2 com o aviso, `abc` é ignorado (`segredos.ler` trocado);
  - 403 e 429: espera gravada num arquivo temporário (`ARQ_ESPERA` trocado), um pedido só, e as consultas seguintes sem
    pedido;
  - durante a espera, zero pedidos, o aviso uma vez e `vagas.fontes_em_espera` lista o JobGether;
  - 504: erro da consulta, e a seguinte roda.

## Phase 7: User Story 5 - Sem descrição e Adicionar Vaga (P2)

**Goal**: o link do JobGether é reconhecido no Adicionar Vaga com o mesmo id da busca, sem pedido à página.

**Independent Test**: `link.ler` sem rede e `banco.criar_manual` num banco temporário.

- [X] T013 [US5] `fontes/link.ler`: plataforma "JobGether" levanta
  `LinkErro("o JobGether não deixa a ferramenta ler a página da vaga; complete cargo, empresa e descrição", {"plataforma": "JobGether", "url": url})`
  **antes** de qualquer pedido.
- [X] T014 [US5] `dash/banco.criar_manual`:
  - com `url` de vaga do JobGether, o id é `jobgether.id_do_link(url)`;
  - se esse id já existe, devolve a vaga que existe com `nova = False`, e também no caso de outra aba gravar no meio,
    como no post;
  - os outros links continuam com `m-…`.
- [X] T015 [P] [US5] `candidatura/dominios.BLOQUEADOS["jobgether.com"] = "os termos do JobGether proíbem acesso automatizado"`.
- [X] T016 [P] [US5] Testes em `tests/test_jobgether.py`:
  - `link.ler` com link do JobGether levanta `LinkErro` com o `parcial`, e `link._baixar` trocado prova que não houve
    pedido;
  - `criar_manual` grava com `jobgether-<id>`, e a segunda vez devolve a existente;
  - `dominios.situacao("https://jobgether.com/offer/…")` sai bloqueado.

## Phase 8: Polish & Cross-Cutting

- [X] T017 Emenda da constituição em `.specify/memory/constitution.md`:
  - a seção "Termos contrários" no princípio VI, com o texto do plan.md;
  - o relatório de impacto no topo: 4.0.0 → 4.1.0 MINOR, motivo spec 030, arquivos atualizados;
  - `**Version**: 4.1.0 | … | **Last Amended**: 2026-10-25`.
- [X] T018 [P] Documentação:
  - `README.md`: portal na lista, resumo dos termos, `JOBGETHER_PAUSA` e a dica de cargo em inglês;
  - `dash/README.md`;
  - `dash/API.md`: "JobGether" em `plataforma` e `jobgether` em `fontes`; o 422 do link do JobGether; o id da vaga
    manual com link do JobGether;
  - `AGENTS.md`: lista de portais no topo e "Respeite os portais" (JobGether pela API para assistentes, desligado por
    padrão);
  - `docs/novo-portal.md`: na linha dos termos da tabela da seção 1, citar a seção "Termos contrários" da constituição.
- [X] T019 [P] `.agents/skills/buscar-vagas/SKILL.md` com o nome do portal; depois `python sincronizar_skills.py` e
  `python sincronizar_skills.py --conferir`.
- [X] T020 Front, na `frontend-react` (worktree própria saída de `origin/frontend-react`, branch
  `front-030-jobgether`):
  - "JobGether" em `src/types/api.ts`;
  - a cor da etiqueta e o domínio `jobgether.com` em `src/utils/formatters.ts`;
  - o texto do `src/components/modals/AddJobModal.tsx`;
  - `npm run build` sem erro, commit local e **sem push** antes do OK da pessoa.
- [X] T021 Verificação:
  - `PY -m unittest discover -s tests` inteiro;
  - quickstart §2: busca real pequena, só com o OK da pessoa;
  - `graphify update .`.
- [ ] T022 Procurar dados pessoais nos arquivos alterados; commit na `030-jobgether`. Depois, pelo fluxo do
  `CLAUDE.local.md`: merge na `marcel`, reiniciar o dashboard e esperar o teste da pessoa antes da `master`.

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002, T003)** → histórias.
- **US1 (T004–T006)** é o MVP. US2 (T007–T008) e US4 (T011–T012) mexem em `buscar`/`_baixar` e vêm depois de T005.
- **US3 (T009–T010)** só depende de T003.
- **US5 (T013–T016)** só depende de T002 (`id_do_link`) e T003 (`plataforma`).
- **Polish**: T017–T019 podem andar em paralelo com qualquer história. T020 só depende do nome do portal. T021 e
  T022 vêm por último.

## Parallel Opportunities

- T001 enquanto se escreve T002.
- T006, T008, T010, T012 e T016 são blocos do mesmo arquivo de testes. Escreva cada bloco logo depois da sua tarefa:
  o `[P]` vale em relação ao código, não entre os blocos.
- T015, T017, T018, T019 e T020: arquivos diferentes, sem dependência entre si.

## Implementation Strategy

1. **MVP**: T001–T006. A busca nacional traz as vagas do JobGether nos testes.
2. **Incremental**: US2 → US4 → US3 → US5, com os testes de cada uma passando antes da próxima.
3. Emenda, documentação e front no fim.
4. Verificação e teste da pessoa na `marcel` antes da `master` (T021–T022).

## Verificação (25/10/2026)

- Suíte inteira: 454 testes na `030-jobgether` e 459 na `marcel`, todos passando.
- Busca real pequena na `marcel` (`vagas.py buscar --fontes jobgether`, 4 cargos, Brasil, remoto):
  - 4 consultas em 9 s;
  - 3 candidatas com local aceito ("Remoto (South America, Latin America, Brazil)"), data e "(sem descrição)";
  - nenhum erro.
- Painel: o JobGether aparece na lista de portais, desligado.
