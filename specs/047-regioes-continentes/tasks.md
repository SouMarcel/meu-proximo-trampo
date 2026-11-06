# Tasks: Regiões e continentes nos filtros da busca internacional

**Input**: documentos em `specs/047-regioes-continentes/` (spec, plan, research, data-model, contracts, quickstart)

**Tests**: sim. O plano pede `tests/test_regioes.py` e ajustes nos testes de hoje, todos sem rede.

**Formato**: `[ID] [P?] [Story] Descrição`. `[P]` marca tarefa em arquivo diferente, sem depender de outra aberta.

## Phase 1: Setup

- [ ] T001 Conferir a worktree `../mpt-047` (branch `047-regioes-continentes`) e a `../mpt-front-027b` (`frontend-react` igual à `origin/frontend-react`); rodar `python -m unittest discover -s tests` na worktree para ter a linha de base

---

## Phase 2: Foundational (catálogo e sobreposição; bloqueia tudo)

- [ ] T002 Em `filtros.py`, criar o catálogo `REGIOES_PAISES` (nome em português → países de `PAISES`) com as 10 regiões marcáveis e as 3 só de texto (Oriente Médio, EMEA, Ásia-Pacífico), conforme research D1. Manter `PAISES_DA_REGIAO = REGIOES_PAISES`. Criar `REGIOES_MARCAVEIS` (lista ordenada das 10) e `REGIAO_EN` (nome em inglês de cada marcável: North America, Central America, South America, Latin America, Americas, European Union, Europe, Asia, Oceania, Africa).
- [ ] T003 Em `filtros.py`, trocar `REGIOES` pelos códigos novos: `pais`, `america_norte`, `america_central`, `america_sul`, `latam`, `americas`, `ue`, `europa`, `asia`, `oceania`, `africa`. Rótulos: "Seu país" e o nome da região. Criar `REGIAO_DO_CODIGO` (código → nome do catálogo) e `CODIGOS_ANTIGOS = {"brasil": "pais", "mundo": None}`.
- [ ] T004 Em `filtros.py`, atualizar `LUGARES` conforme research D4:
  - "eu", "european union" e "uniao europeia" → União Europeia;
  - "south america" e "america do sul" → América do Sul;
  - "central america" e "america central" → América Central;
  - "america do norte" → América do Norte;
  - "oceania" e "anz" → Oceania;
  - "asia" → Ásia;
  - "apac" e "asia pacific" → Ásia-Pacífico;
  - "africa" → África;
  - "emea" → EMEA;
  - "middle east", "oriente medio" e "mena" → Oriente Médio.
- [ ] T005 Em `filtros.py`, criar as funções:
  - `lugar_pt(nome)`: país por `pais_pt` ou região marcável pelo nome em português (com ou sem acento) ou em inglês;
  - `paises_de(lugar)`: conjunto de países; `None` para "mundo todo";
  - `sobrepoe(a, b)`.

  Reescrever `_inclui(lugar, pais)` como `sobrepoe(lugar, pais)`.
- [ ] T006 [P] Criar `tests/test_regioes.py` com os testes do catálogo:
  - cada país de `PAISES` está em exatamente um continente: América do Norte + América Central + América do Sul,
    Europa, Ásia, Oceania e África;
  - a UE tem 27 países e está dentro da Europa;
  - a América Latina está dentro das Américas;
  - leitura do texto: "Remote - Oceania", "APAC", "EMEA", "EU only", "South America", "Asia", "Africa";
    "South Africa" continua África do Sul; "Malaysia" não é Ásia pelo nome da região;
  - `lugar_pt` aceita "União Europeia", "uniao europeia" e "European Union", e recusa "Atlântida";
  - `sobrepoe`: Europa × UE, Alemanha × UE, América Latina × Américas, mundo todo × qualquer, Ásia × Europa falso.

**Checkpoint**: catálogo, leitura e sobreposição testados.

---

## Phase 3: User Story 1 - Aceitar vagas por continente (P1) 🎯 MVP

**Goal**: Regiões aceitas com continentes e regra por sobreposição; mundo todo sempre passa.

**Independent Test**: marcar regiões no painel e conferir, nos anúncios de exemplo, quais vão para Fora e com que motivo.

- [ ] T007 [US1] Em `filtros.py`, `efetivos()`: `regioes` com os códigos novos. `brasil` vira `pais`, `mundo` e códigos desconhecidos saem, e os repetidos também.
- [ ] T008 [US1] Em `filtros.py`, `validar()`: aceitar `brasil` (vira `pais`) e `mundo` (sai) sem erro. Qualquer outro código fora de `REGIOES` dá "região inválido", como hoje.
- [ ] T009 [US1] Em `filtros.py`, `elegibilidade()`, corte 3, regra nova (research D3):
  - vale só com regiões marcadas e com lugar declarado pela vaga (`do_campo or das_frases`), sem "mundo todo";
  - corta quando nenhum lugar da vaga sobrepõe alguma região marcada; `pais` conta como o país da pessoa;
  - motivo: "Vaga aberta a: <lugares com ' ou '>; você aceita <rótulos com ' e '>", em que `pais` mostra o nome do país
    da pessoa;
  - remover `_regiao()`.
- [ ] T010 [US1] Em `filtros.py`, `criterios_extra()`: rótulos novos das regiões aceitas, com `pais` pelo nome do país da pessoa.
- [ ] T011 [US1] Em `filtros.py`, `opcoes()`: devolver `regioes` (códigos novos), `regioes_lugar` (`REGIOES_MARCAVEIS`) e `fontes_regiao` (portais com `POR_REGIAO`, lidos de `fontes.FONTES`).
- [ ] T012 [P] [US1] Ajustar `tests/test_elegibilidade.py`:
  - o caso "só LATAM, vaga do mundo todo" passa a não cortar;
  - "mundo" + "latam" continua sem corte;
  - casos novos: América Latina com `americas`; Ásia cortada com `americas` + `europa`; "EU only" com `europa`;
    "Remote" sem lugar não corta; sem região marcada não corta; `pais` com vaga "Brazil".
- [ ] T013 [P] [US1] Ajustar `tests/test_internacional.py` (validação: `regioes` com `brasil` e `mundo` aceitas; `lua` dá erro) e acrescentar em `tests/test_regioes.py` os testes de `efetivos`/`validar`/`opcoes` das regiões.
- [ ] T014 [US1] Front `../mpt-front-027b/src/services/api/config.ts`: em `Opcoes`, campos opcionais `regioes_lugar?: string[]` e `fontes_regiao?: string[]`.
- [ ] T015 [US1] Front `../mpt-front-027b/src/components/modals/SearchFiltersModal.tsx`, Regiões aceitas:
  - as pílulas usam `{...op.regioes, pais: "Seu país (<país>)"}`;
  - a dica vira "Passa a vaga aberta a uma região com país em comum com as marcadas; a aberta ao mundo todo sempre
    passa. Nenhuma marcada = sem restrição.";
  - ao carregar, os códigos antigos `brasil`/`mundo` viram `pais` ou saem, para a pílula aparecer marcada.

**Checkpoint**: o filtro de regiões funciona sozinho (MVP).

---

## Phase 4: User Story 2 - Autorização de trabalho por região (P1)

**Goal**: "União Europeia" na autorização serve para vagas restritas a um país-membro.

**Independent Test**: autorização "União Europeia" e os anúncios "Germany only", "authorized to work in the EU" e "UK right to work".

- [ ] T016 [US2] Em `filtros.py`:
  - `efetivos()` e `validar()` usam `lugar_pt` em `autorizacao_trabalho`;
  - o erro passa a ser "autorização de trabalho: país ou região desconhecido: X".
- [ ] T017 [US2] Em `filtros.py`, `elegibilidade()`, cortes 1 e 2: `serve` usa `sobrepoe(lugar, p)` para cada `p` em `[casa, *autorizacao_trabalho]` (já vem do T005 pelo `_inclui`). Conferir que "UK right to work" com a UE continua cortado.
- [ ] T018 [P] [US2] Em `tests/test_regioes.py`, testes da autorização por região: "must be based in Germany", "authorized to work in the EU", "right to work in the UK" sem patrocínio e Portugal + "EU only".
- [ ] T019 [US2] Front `SearchFiltersModal.tsx`:
  - o rótulo da autorização vira "Tenho visto ou autorização de trabalho em (países ou regiões, separados por
    vírgula)";
  - o placeholder vira "nenhum (ex.: Portugal, União Europeia)".

**Checkpoint**: US1 e US2 funcionam juntas.

---

## Phase 5: User Story 3 - Buscar numa região inteira (P2)

**Goal**: região em países de interesse ou em países para morar vira consulta no LinkedIn; o Indeed fica nos países.

**Independent Test**: marcar uma região, abrir a confirmação da busca e conferir portais e número de consultas.

- [ ] T020 [US3] Em `filtros.py`:
  - `efetivos()` e `validar()` usam `lugar_pt` em `paises` e `paises_mudanca`;
  - o país da pessoa sai dessas listas, mas a região que o contém fica;
  - o erro passa a ser "<campo>: país ou região desconhecido: X".
- [ ] T021 [US3] Em `filtros.py`, `consultas()`: o lugar que é região faz `internacional:<Região>` e `mudanca:<Região>` com `pais: None`, `pais_nome: <Região>` e `regiao: REGIAO_EN[<Região>]`. País continua como hoje.
- [ ] T022 [US3] Em `vagas.py`, `atende()`: consulta com `regiao` só roda na fonte com `POR_REGIAO = True`, respeitando `AREAS`.
- [ ] T023 [US3] Documentar `POR_REGIAO` no contrato em `fontes/__init__.py`, e em `fontes/linkedin.py`:
  - `POR_REGIAO = True`;
  - `parametros()` usa `location = consulta["regiao"]` quando houver.
- [ ] T024 [US3] Em `filtros.py`, `area_da_vaga()`: quando o lugar do grupo é região (research D7):
  - o país do local vale (`pais_do_local(local)`);
  - local no país da pessoa → nacional;
  - outro país → internacional com esse país;
  - sem país no local → internacional com o nome da região.
- [ ] T025 [US3] Em `filtros.py`, `elegibilidade()`, corte 4: o país da vaga precisa sobrepor algum lugar de `paises_mudanca`.
- [ ] T026 [P] [US3] Em `tests/test_regioes.py`:
  - consultas com região: grupos, `regiao` e `pais` None;
  - `atende`: LinkedIn sim; Indeed, JobGether e as fontes do exterior não;
  - `vagas.contar_consultas` com UE e 2 cargos: LinkedIn +1 agrupada, Indeed +0;
  - `linkedin.parametros` com `location` "European Union";
  - área: vaga do grupo da região com local "Berlin" → Alemanha, com local do país da pessoa → nacional, sem local →
    a região;
  - corte de mudança com Europa e vaga híbrida em Lisboa.
- [ ] T027 [US3] Front `config.ts`:
  - `contarConsultas(d, porGrupo = false, regioes: string[] = [])` não conta os lugares que são região quando
    `porGrupo` é falso;
  - `contarLinkedin(d, regioes)` conta tudo;
  - os dois tratam também `paises_mudanca`.
- [ ] T028 [US3] Front `SearchFiltersModal.tsx`, Países de interesse:
  - uma linha "Regiões" com `op.regioes_lugar` em pílulas acima da grade, alternando em `it.paises`;
  - a contagem recebe `op.regioes_lugar`;
  - aviso quando há região em `paises` ou em `paises_mudanca` e nenhum de `op.fontes_regiao` está em `d.fontes`:
    "Nenhum portal ligado procura por região; o Indeed só procura nos países marcados um a um.";
  - a caixa de países para morar ganha o placeholder "Para quais países ou regiões (separados por vírgula); vazio = os
    de interesse".

**Checkpoint**: a busca por região funciona.

---

## Phase 6: User Story 4 - Regiões no perfil (P3)

**Goal**: o perfil e a proposta de filtros aceitam regiões.

**Independent Test**: responder "Europa, Estados Unidos" e conferir a linha do perfil e a proposta.

- [ ] T029 [US4] Em `primeiros_passos.py`:
  - a pergunta `exterior_paises` vira "De quais países ou regiões você aceita vagas? Um por linha (ex.: Estados
    Unidos, União Europeia).";
  - a linha do perfil vira "Países e regiões de interesse";
  - a proposta usa `filtros.lugar_pt` e avisa, num aviso só, os nomes não reconhecidos.
- [ ] T030 [P] [US4] Em `tests/test_primeiros_passos.py`: a linha nova (ajustar se algum teste cita "Países de interesse"), a proposta com "Europa, Estados Unidos" e o aviso com um nome desconhecido.

---

## Phase 7: User Story 5 - Rever vagas cortadas pela regra antiga (P3)

**Goal**: mostrar e, com OK, devolver ao relatório as vagas cortadas só pela região.

**Independent Test**: vaga em Fora por "Vaga aberta a: América Latina" com Américas marcada; revisão sem e com `--gravar`.

- [ ] T031 [US5] Em `dash/banco.py`:
  - `rever_regioes(gravar=False)`:
    - para cada vaga em `triagem == "fora"` com motivo que começa por "Vaga aberta a:", refaz os motivos de região
      com `filtros.elegibilidade` e o config de agora;
    - mantém os outros motivos;
    - sem motivo, a vaga volta: `triagem = "pendente"`, sem `motivo_fora` nem `triada_em`, com `atualizada_em`;
  - comando `regioes [--gravar]` no `main()`, com a saída do contrato;
  - a linha no docstring do módulo.
- [ ] T032 [P] [US5] Em `tests/test_regioes.py`, a revisão com banco temporário (`TRAMPO_BANCO`) e config temporário (`TRAMPO_CONFIG`):
  - sem gravar não muda nada;
  - com gravar, a vaga só de região volta;
  - a vaga com região e moeda perde só o motivo de região.

---

## Phase 8: Polish & Cross-Cutting

- [ ] T033 [P] `dash/API.md`: `opcoes.regioes` (códigos novos), `regioes_lugar`, `fontes_regiao`; os campos de lugar aceitam regiões; o erro novo.
- [ ] T034 [P] `README.md` (tabela do config: `regioes` e campos de lugar) e `AGENTS.md`: comando `PY dash/banco.py regioes`, que mostra e só grava com `--gravar` e o OK da pessoa.
- [ ] T035 [P] `docs/novo-portal.md`: o atributo `POR_REGIAO`.
- [ ] T036 Rodar `python -m unittest discover -s tests` na worktree; tudo passa.
- [ ] T037 Front: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./` em `../mpt-front-027b`; commit local na `frontend-react` (sem push).
- [ ] T038 Procurar dados pessoais no diff da worktree e fazer o commit local na `047-regioes-continentes`.
- [ ] T039 Na pasta principal (branch pessoal):
  - `git merge 047-regioes-continentes`;
  - rodar os testes;
  - copiar o `dist/` do front para `dash/front/` sem commit;
  - aplicar no `config.json` as regiões e a autorização combinadas;
  - aplicar no `perfil.md` as linhas combinadas;
  - reiniciar o dashboard com `--sem-navegador`;
  - rodar `dash/banco.py regioes` sem gravar, para mostrar à pessoa.

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002–T006)**, que bloqueia todas as histórias.
- **US1 (T007–T015)** e **US2 (T016–T019)**:
  - as duas dependem só da fase 2;
  - no `filtros.py`, as tarefas vão uma depois da outra, porque é o mesmo arquivo.
- **US3 (T020–T028)** depende da fase 2. O front de US3 (T027–T028) vem depois do T014.
- **US4 (T029–T030)** depende do T005 (`lugar_pt`).
- **US5 (T031–T032)** depende do T009 (regra nova do corte 3).
- **Polish** vem por último. T039 depende de T036–T038.

## Parallel Opportunities

- Os testes `[P]` (T006, T012, T013, T018, T026, T030, T032) estão em arquivos de teste diferentes do código.
- O front (T014, T015, T019, T027, T028) fica noutra worktree e pode andar junto com o back depois do T011.
- Os documentos T033–T035 podem andar juntos.

## Implementation Strategy

- **MVP**: fases 1 a 3 (US1). Regiões aceitas com continentes resolvem o pedido principal: Europa e Oceania marcadas,
  América Latina e mundo todo passando.
- **Depois**: US2 (autorização na UE), US3 (busca por região), US4 (perfil), US5 (revisão), cada uma testável sozinha.
- **Entrega**: tudo junto no merge na branch pessoal, para o teste da pessoa.
