---
description: "Tarefas da feature 031: Empresas acompanhadas na busca nacional (Windows)"
---

# Tasks: Empresas acompanhadas na busca nacional

**Input**: spec.md, plan.md, research.md (R1–R4, D1–D8), data-model.md, contracts/empresas.md, quickstart.md.

**Testes**: incluídos (fluxo da constituição: funções novas ganham `unittest`). Os testes novos ficam em
`tests/test_empresas_acompanhadas.py`, sem rede, com as amostras de `tests/dados/{greenhouse,lever,ashby}.json` e
`urlopen` trocado. Os testes de `tests/test_fontes_int.py` que esperam a lista em `internacional.empresas` são
atualizados.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [ ] T001 Base de testes em `tests/test_empresas_acompanhadas.py`:
  - `_comum.esquecer()`, `urlopen` falso (fila de respostas JSON ou código HTTP), `filtros.CONFIG` e `banco.ARQUIVO`
    num diretório temporário;
  - um ajudante que monta a lista de uma empresa a partir das amostras, trocando o `location` de cada vaga ("Remote,
    Brazil", "Remote, United States", "Remote", "Anywhere", "São Paulo, Brazil", "Latin America").

## Phase 2: Foundational (bloqueia as histórias)

- [ ] T002 `fontes/_comum.py`:
  - `FonteErro(motivo, repetido=False, codigo=None)`, guardando o `codigo`;
  - `baixar(url, params=None, aceitar=..., nova_tentativa=True)`: com `False`, o 429 vira
    `FonteErro(..., codigo=429)` sem esperar; todo `HTTPError` leva o `codigo`;
  - `baixar_json(url, params=None, nova_tentativa=True)` repassa o parâmetro;
  - as outras fontes não mudam (padrão `True`).
- [ ] T003 `filtros.py`, a lista no nível de cima (data-model, `config.json`):
  - `efetivos` devolve `"empresas"` a partir de `cfg["empresas"]` ou, sem a chave, de `cfg["internacional"]["empresas"]`,
    e `internacional` deixa de ter `empresas`;
  - `validar` usa `_empresas(e["empresas"])` quando a chave vem e `_empresas(inter.get("empresas"))` quando não vem,
    devolve `"empresas"` em cima e conta a lista de cima na regra "escolha pelo menos um país, uma fonte do exterior ou
    uma empresa para a busca internacional";
  - `consultas` usa `f["empresas"]` na consulta global e na condição dela;
  - o resumo da busca conta as empresas fora do bloco da internacional ("N empresas acompanhadas");
  - `salvar` não muda: o `cfg.update(novos)` já tira `internacional.empresas`.
- [ ] T004 Atualizar `tests/test_fontes_int.py` (linhas que leem `inter["empresas"]` ou montam
  `internacional.empresas`) para a lista de cima, mantendo o mesmo comportamento esperado.

**Checkpoint**: `PY -m unittest discover -s tests` passa sem mudança de comportamento visível.

## Phase 3: User Story 1 - Vagas das empresas na busca nacional (P1) 🎯 MVP

**Goal**: a busca nacional traz as vagas das empresas no país da pessoa, mesmo com a internacional desligada.

**Independent Test**: listas simuladas: "Remote, Brazil" entra como nacional e "Remote, United States" não entra.

- [ ] T005 [US1] `filtros.aberta_ao_pais(texto, pais) -> bool`: verdadeiro se algum lugar de `_lugares(texto)` satisfaz
  `_inclui(lugar, pais)`; "Remote" sozinho dá falso. A elegibilidade continua usando `_lugares` e `_inclui`, sem mudança.
- [ ] T006 [US1] `filtros.consultas`: as consultas nacionais (`remoto`, `pais`, `local`) levam `"empresas": f["empresas"]`.
- [ ] T007 [US1] `fontes/ats.py`:
  - `AREAS = ("nacional", "internacional")`, `POR_PAIS = True`, `GLOBAL = True`;
  - `buscar` atende `grupo` em (`remoto`, `pais`, `local`) e a global; `internacional:<p>` e `mudanca:<p>` devolvem
    `([], [])` sem pedido;
  - lista por empresa via `_comum.lembrar(f"ats:{sistema}:{id}", …)`, a mesma chave de hoje, para as duas áreas
    usarem um download só;
  - filtro por título e janela como hoje;
  - na `remoto`, vaga remota com `aberta_ao_pais(restricao_local ou local, pais_nome)`;
  - na `pais`, isso mais as não remotas com `filtros.pais_do_local(local) == pais_nome`;
  - na `local`, não remota cujo local (sem acento) cita a cidade da consulta ou o nome do estado (`_comum.UFS`), sem
    citar outro país;
  - na global, como hoje.
- [ ] T008 [US1] `vagas.fontes_da_busca`: `ats` entra sempre que `f["empresas"]` não está vazia, com ou sem a
  internacional.
- [ ] T009 [P] [US1] Testes:
  - "Remote, Brazil", "Latin America" e "Anywhere" entram na consulta `remoto`;
  - "Remote, United States" e "Remote" ficam de fora;
  - "São Paulo, Brazil" presencial entra na `local` e não na `remoto`;
  - com a internacional desligada, `fontes_da_busca` inclui `ats` e `filtros.consultas` leva as empresas nas
    consultas nacionais;
  - com as duas áreas, uma lista baixada por empresa (um pedido);
  - `internacional:Portugal` sem pedido;
  - `filtros.area_da_vaga` dá nacional para a vaga achada pela `remoto` (SC-001).

**Checkpoint**: US1 testável sozinha.

## Phase 4: User Story 2 - A lista no painel principal (P1)

**Goal**: a lista fica em `empresas`, no nível de cima, e um config antigo continua valendo.

**Independent Test**: config antigo lido e regravado pelo `filtros.salvar`.

- [ ] T010 [US2] Conferir e completar os casos de compatibilidade em `filtros.py` (T003):
  - pedido com `empresas` em cima e `internacional.empresas` diferente: vale a de cima;
  - pedido só com `internacional.empresas` (front antigo): vira `empresas`;
  - `salvar` não deixa `internacional.empresas` no arquivo.
- [ ] T011 [P] [US2] Testes:
  - config antigo → `efetivos(...)["empresas"]` com as mesmas empresas (SC-003);
  - `salvar` com pedido do front antigo grava em cima e tira de `internacional`;
  - pedido do front novo vale;
  - máximo de 50, e mesma empresa (maiúsculas) contada uma vez.

## Phase 5: User Story 3 - Parar no primeiro bloqueio (P1)

**Goal**: 403 ou 429 de um sistema param esse sistema até o fim da busca; 404 vira aviso da empresa.

**Independent Test**: três empresas no Greenhouse e uma no Lever; 429 na primeira.

- [ ] T012 [US3] `fontes/ats.py`:
  - `_estado = {"bloqueados": set()}`, zerado num `_esquecer` registrado em `_comum.AO_ESQUECER`;
  - `_lista` baixa com `nova_tentativa=False`;
  - no `buscar`, empresa de sistema bloqueado não faz pedido;
  - `FonteErro` com `codigo` 403 ou 429 põe o sistema em `bloqueados`, com o aviso "o <Sistema> limitou as consultas
    (código N); as outras empresas dele ficam para a próxima busca", uma vez por busca;
  - `codigo` 404: "a página de vagas de <empresa> no <Sistema> não existe mais (a empresa pode ter mudado de sistema ou
    de nome); remova ou troque o link";
  - outros erros: como hoje ("<empresa> (<Sistema>): <motivo>");
  - `ler(url)` baixa com `nova_tentativa=False`.
- [ ] T013 [P] [US3] Testes:
  - 429 na primeira empresa do Greenhouse: zero pedidos às outras duas, a do Lever pedida, aviso uma vez e um só
    pedido ao Greenhouse, sem nova tentativa (SC-002);
  - 403 igual;
  - 404 com o aviso;
  - 500 numa empresa não para as outras do mesmo sistema;
  - `_comum.baixar(..., nova_tentativa=False)` não dorme no 429 e a padrão continua tentando de novo.

## Phase 6: User Story 4 - Acompanhar pelo Adicionar Vaga (P2)

**Goal**: o link de vaga do Greenhouse, do Lever ou do Ashby informa a empresa e se ela já é acompanhada; acompanhar
grava na lista.

**Independent Test**: `filtros.acompanhar` num config temporário; resposta do `POST /api/vagas/link` com a empresa.

- [ ] T014 [US4] `filtros.acompanhar(url) -> (empresa, nova, empresas)`:
  - reconhece pelo `ats.reconhecer` (`ValueError` com a mensagem do link inválido);
  - lê `ler_config()` e parte de `efetivos(cfg)["empresas"]`;
  - deduplica por sistema e id, sem diferença de maiúsculas;
  - recusa a 51ª com "a lista de empresas está cheia (50); remova uma no painel Filtros da busca";
  - grava `cfg["empresas"]`, tira `cfg["internacional"]["empresas"]` e escreve o arquivo como o `salvar` (tmp +
    `os.replace`), sem revalidar os outros filtros.
- [ ] T015 [US4] `dash/servidor.py`:
  - `GET /api/empresas` → `{empresas, maximo: filtros.MAX_EMPRESAS}`;
  - `POST /api/empresas` com `{url}` (até 1.000) → 201 `{empresa, nova: true, empresas}`, 200 com `nova: false`, 400 no
    `ValueError`;
  - no `POST /api/vagas/link`, quando `ats.vaga_do_link(url)` reconhece o link, a resposta ganha
    `empresa: {sistema, id, nome, url, acompanhada}`.

  O `POST /api/empresas` entra na mesma checagem de origem dos outros pedidos de escrita.
- [ ] T016 [P] [US4] Testes:
  - `acompanhar` nova, repetida (outra caixa), lista cheia e link inválido;
  - config antigo migra no primeiro acompanhar;
  - servidor: `POST /api/empresas` e `GET /api/empresas` pelo handler, como nos testes atuais do servidor;
  - `POST /api/vagas/link` com link do Lever (`ats.ler` simulado) traz `empresa.acompanhada` falso e depois verdadeiro.

## Phase 7: User Story 5 - Acompanhar pelo detalhe da vaga (P2)

**Goal**: o detalhe oferece "Acompanhar empresa" quando o link da vaga ou o de candidatura é de vaga desses sistemas.

**Independent Test**: no front, a empresa sai de `empresaDoLink(url_candidatura || url)` e o estado vem de
`GET /api/empresas`.

- [ ] T017 [US5] Front, na `frontend-react` (worktree própria saída de `origin/frontend-react`, branch
  `front-031-empresas`):
  - `src/services/api/config.ts`: `empresas` no nível de cima do tipo dos filtros, fora de `internacional`, e
    `contarConsultas` com as empresas;
  - clientes de `GET` e `POST /api/empresas`;
  - `src/components/modals/SearchFiltersModal.tsx`: a seção "Empresas que você acompanha" sai do painel internacional
    e vai para o principal, com o texto sem "cargos em inglês";
  - `src/components/modals/AddJobModal.tsx`: com `empresa` na resposta, "Acompanhar <nome>" ou "Já acompanhada";
  - `src/components/kit/Kit.tsx`: "Acompanhar empresa" / "Acompanhando", junto do "Candidatar no …";
  - `npm run build` sem erro e commit local. **Push só depois do back-end na master** (research D7).

## Phase 8: Polish & Cross-Cutting

- [ ] T018 [P] `specs/lista-de-desejos.md`: Greenhouse como portal barrado (o MyGreenhouse Jobs exige login), com a
  ideia da conta conectada e o motivo de não seguir (research D8).
- [ ] T019 [P] Documentação:
  - `README.md`: as empresas acompanhadas também na busca nacional, a seção no painel principal, "Acompanhar" e a
    parada no bloqueio;
  - `dash/README.md`;
  - `dash/API.md`: `filtros.empresas` em cima; `GET`/`POST /api/empresas`; `empresa` na resposta do link.
- [ ] T020 [P] `.agents/skills/buscar-vagas/SKILL.md`: empresas acompanhadas nas duas áreas e "Acompanhar"; depois
  `python sincronizar_skills.py` e `--conferir`.
- [ ] T021 Verificação: `PY -m unittest discover -s tests` inteiro; busca real pequena na branch de teste com
  `--fontes ats`, com o OK da pessoa (quickstart §2).
- [ ] T022 Procurar dados pessoais nos arquivos alterados; commit; merge na branch pessoal de teste; reiniciar o
  dashboard; teste da pessoa; com o OK, master e push. Só depois, o push do front e o PR.

## Dependencies & Execution Order

- **T001** → **Foundational (T002–T004)** → histórias.
- **US1 (T005–T009)** é o MVP. US2 (T010–T011) completa o T003.
- **US3 (T012–T013)** depende de T002 e mexe no `ats.py` depois de T007.
- **US4 (T014–T016)** depende de T003.
- **US5 (T017)** depende da API de T015.
- **Polish**: T018–T020 podem andar em paralelo. T021 e T022 vêm por último. O push do front fica depois da master.

## Parallel Opportunities

- T018, T019 e T020: arquivos diferentes.
- Os blocos de teste (T009, T011, T013, T016) são do mesmo arquivo: cada um vem logo depois da sua tarefa.
- T017 (front) pode começar junto com T014, com o contrato pronto.

## Implementation Strategy

1. **MVP**: T001–T009. A busca nacional traz as vagas das empresas nos testes.
2. **Incremental**: US2 → US3 → US4 → US5.
3. Documentação e lista de desejos.
4. Teste da pessoa e master; depois o front (D7).
