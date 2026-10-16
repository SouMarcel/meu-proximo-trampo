---

description: "Tarefas da feature 015: LinkedIn com menos pedidos (Windows)"
---

# Tasks: LinkedIn com menos pedidos

**Input**: Design documents from `/specs/015-linkedin-menos-pedidos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/fontes.md, contracts/busca.md,
quickstart.md

**Tests**: `unittest` sem rede (constituição): o `abridor` falso de `tests/test_linkedin.py` e o banco temporário de
`tests/test_busca.py`. O resto é verificado pelo quickstart.

**Organization**: por história, numa ordem que entrega primeiro o que **não depende do OR** (research R1 pendente):
1. US3, espera e motivo: com ela, o próximo teste do OR já mostra o código da recusa;
2. US1 (limite de descrições) e US2 (pendentes);
3. US4, aviso de cargos;
4. por último, a consulta combinada da US1, atrás de um portão de verificação.

**Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Rodar `python -m unittest discover -s tests` na worktree e anotar o total de testes que passam (linha de
  base). Com o LinkedIn e o Indeed desligados, guardar a saída de `vagas.py buscar --fontes gupy` com uma fonte falsa
  (`tests/fonte_falsa.py`) para comparar no fim (SC-006).

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 Documentar no docstring de `fontes/__init__.py` os atributos opcionais `AGRUPAR`, `MAX_DESCRICOES`,
  `espera()` e `parada()`, com o texto de `contracts/fontes.md`
- [X] T003 Em `fontes/linkedin.py`, criar as constantes:
  - `AGRUPAR = False`, ligado só na T028;
  - `MAX_PAGINAS_AGRUPADA = 3`;
  - `MAX_DESCRICOES = 20`;
  - `ESPERA = timedelta(hours=6)`;
  - `ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "linkedin-espera.json"`.

**Checkpoint**: contrato documentado; nada muda no comportamento.

---

## Phase 3: User Story 3 - Espera depois de um bloqueio, com o motivo (Priority: P2, feita primeiro)

**Goal**: o aviso diz o motivo e o horário. Por 6 horas, nenhum pedido vai ao LinkedIn, e toda busca pergunta antes
de seguir sem ele.

**Independent Test**: quickstart §1 (casos de espera e motivo), §3.3–3.5 e §4.

- [X] T004 [US3] Em `fontes/linkedin.py`, `_bloquear(motivo)`:
  - grava `{"desde": agora ISO, "motivo": motivo}` em `ARQ_ESPERA`, criando a pasta;
  - se a gravação falhar, segue sem a espera;
  - devolve `FonteErro(f"{BLOQUEIO} ({motivo}); em espera até HH:MM")`.
  
  Em `_baixar`, o motivo segue o research R10: 429 "excesso de pedidos"; 999 "recusa automática, costuma ser a rede:
  VPN, Wi-Fi corporativo ou internet compartilhada"; 3xx "pediu login"; 401/403 "acesso negado (código N)".
- [X] T005 [US3] Em `fontes/linkedin.py`:
  - `espera() -> dict | None`: lê `ARQ_ESPERA`. Arquivo ausente ou ilegível dá `None`. Senão,
    `ate = min(desde, agora) + ESPERA`, e devolve `{"ate": ISO até minutos, "motivo"}` se `agora < ate`.
  - `parada() -> bool`: `_estado["bloqueado"] or espera() is not None`.
  - `buscar`: em espera, devolve `([], [f"LinkedIn em espera até HH:MM ({motivo}); ficou de fora desta busca"])` na
    primeira consulta da busca e `([], [])` nas outras. O flag `_estado["avisou_espera"]` é zerado em `_esquecer`.
  - `descrever`: em espera, devolve a descrição que a vaga já tinha, sem pedido.
- [X] T006 [US3] Em `vagas.py`:
  - `fontes_em_espera(nomes) -> list[dict]`: `[{nome, portal, ate, motivo}]` das fontes com `espera()` ativa;
  - `executar` grava `resultado["espera"]`.
- [X] T007 [US3] Em `vagas.py`, `cmd_buscar`, antes da `TravaBusca`, seguindo `contracts/busca.md`:
  - todas as fontes em espera: imprime o aviso e devolve 5;
  - espera com `sys.stdin.isatty()`: pergunta `Seguir sem o LinkedIn? [s/N]`;
  - espera sem terminal interativo e sem `--confirmar-espera`: imprime o aviso e como confirmar, e devolve 5.
  
  Criar o argumento `--confirmar-espera` no parser de `buscar`.
- [X] T008 [US3] Em `dash/buscador.py`:
  - `plano()` devolve `espera` (de `vagas.fontes_em_espera`) e `so_espera`;
  - `iniciar(sem_nota, confirmar_recente, confirmar_espera=False)` recusa `so_espera` com
    `BuscaRecusada(mensagem)`, e espera sem confirmação com `BuscaRecusada(mensagem, precisa_confirmar=True)`. Os
    textos são os de `contracts/busca.md`.
- [X] T009 [US3] Em `dash/servidor.py`, `POST /api/busca` repassa `confirmar_espera` (bool) para `BUSCA.iniciar`
- [X] T010 [US3] Em `dash/dashboard.html`, `montarBusca`:
  - linha "LinkedIn em espera até HH:MM (motivo): fica de fora desta busca" para cada item de `p.espera`;
  - botão "Buscar sem o LinkedIn" quando há espera;
  - com `p.so_espera`, botão desligado e a mensagem.
  
  `buIniciar` envia `confirmar_espera: !!(BU.plano && BU.plano.espera && BU.plano.espera.length)`.
- [X] T011 [P] [US3] Testes em `tests/test_linkedin.py`, com `ARQ_ESPERA` num diretório temporário:
  - motivos de 429, 999, 302 e 403 no aviso;
  - arquivo gravado no bloqueio;
  - `espera()` válida, expirada (mais de 6 h), com `desde` no futuro e com arquivo corrompido;
  - `buscar`/`descrever` em espera sem nenhum pedido;
  - aviso só na primeira consulta.
  
  Ajustar `test_429_para_o_resto_da_busca` e `test_login_e_999_contam_como_bloqueio` para conferir o prefixo
  `li.BLOQUEIO`.
- [X] T012 [P] [US3] Testes em `tests/test_busca.py`:
  - `plano()` com `espera`/`so_espera`;
  - `iniciar` recusando sem confirmação, recusando `so_espera` e aceitando com `confirmar_espera`;
  - `cmd_buscar` devolvendo 5 sem terminal e seguindo com `--confirmar-espera`, sem pedido ao LinkedIn.
- [X] T013 [US3] Na skill `.agents/skills/buscar-vagas/SKILL.md`:
  - passo "Buscar": código 5 → mostrar o aviso, perguntar com opções e repetir com `--confirmar-espera` só se a
    pessoa confirmar;
  - seção "Se o portal bloquear": o limite é por rede (pessoas na mesma rede dividem a cota), a espera de 6 horas e
    o que cada motivo sugere.

**Checkpoint**: bloqueio com motivo, espera respeitada e confirmação nos três caminhos. A partir daqui, uma nova
tentativa do teste do OR mostra o código da recusa.

---

## Phase 4: User Story 1 (limite) + User Story 2 - Descrições com limite e pendentes (Priority: P1) 🎯 MVP

**Goal**: no máximo 20 descrições do LinkedIn por busca, pendentes primeiro. A vaga sem texto fica "descrição
pendente" e não recebe nota até o texto chegar.

**Independent Test**: quickstart §1 (limite, pendentes e IA) e §3.6.

- [X] T014 [US2] Em `dash/banco.py`:
  - `pendentes_de_descricao(plataforma) -> list[dict]`: vagas com `descricao_pendente`, a plataforma pedida,
    `triagem == "pendente"` e sem `etapa`, ordenadas por `publicada_em` e depois `encontrada_em`, da mais recente
    para a mais antiga (research R6);
  - `completar_descricao(vid, descricao, tipo_emprego=None)`: grava o texto e o tipo, remove `descricao_pendente`,
    roda `aplicar_criterios` e atualiza `atualizada_em`;
  - `precisa_analise(v)` devolve falso com `descricao_pendente`;
  - `_cmd_quadro`/`_cmd_pendentes` mostram "descrição pendente".
- [X] T015 [P] [US2] Em `dash/analise.py`, `precisa(v)` devolve falso quando `v.get("descricao_pendente")`
- [X] T016 [US1] Em `vagas.py`, `executar`, no bloco das descrições (hoje ~linha 312):
  - **Fila por fonte com `MAX_DESCRICOES`**: as pendentes do banco (`banco.pendentes_de_descricao(fonte.PLATAFORMA)`,
    sem repetir ids desta busca), depois as candidatas novas da mais recente para a mais antiga, depois as "fora";
    fontes sem o atributo seguem como hoje.
  - **Limite**: no máximo `MAX_DESCRICOES` chamadas, contando as que falham.
  - **Marca**: candidata ou pendente sem texto (fora do limite, ou com `fonte.parada()` verdadeiro) recebe
    `descricao_pendente = True`.
  - **Erro de vaga** (fonte não parada): a marca sai.
  - **Resultado**: `resultado["descricoes_completadas"] = [{id, descricao, tipo_emprego?, erro?}]` para as pendentes
    do banco tratadas.
- [X] T017 [US2] Em `vagas.py`, `gravar_resultado`:
  - `documento()` copia `descricao_pendente` quando verdadeiro;
  - aplicar `dados.get("descricoes_completadas", [])` com `banco.completar_descricao`;
  - devolver `completadas` (quantidade) no retorno.
- [X] T018 [US2] Em `dash/buscador.py`, `_rodar`:
  - `analise.FILA.pedir()` também quando `r["completadas"]`;
  - resumo com `pendentes` (candidatas novas com a marca) e `completadas`.
  
  Em `dash/dashboard.html`, o painel de fim de busca mostra "N com descrição pendente (lidas na próxima busca)"
  quando houver.
- [X] T019 [P] [US2] Em `dash/dashboard.html`, quando `v.descricao_pendente`:
  - chip "Descrição pendente" no lugar de "Aguardando análise" (cartão ~linha 948);
  - "descrição pendente" no lugar de "aguardando" na nota (~1044) e na tabela (~1000);
  - banner do detalhe (~1151): "Descrição pendente: o LinkedIn limitou os pedidos; ela é lida na próxima busca, e
    só então a vaga recebe nota."
- [X] T020 [P] [US2] Em `vagas.py`, `cmd_buscar` e `escrever_digest`:
  - a contagem de candidatas com descrição pendente;
  - no digest do chat, a vaga pendente aparece com "(descrição pendente: não avaliar)".
- [X] T021 [P] [US1] [US2] Testes em `tests/test_busca.py`, com uma fonte falsa com `MAX_DESCRICOES = 3`:
  - limite contando falhas;
  - ordem: pendentes do banco, depois novas recentes, depois "fora";
  - a marca nas que sobram e no bloqueio;
  - a marca sai com 404;
  - pendente descartada ou no quadro fica fora da fila;
  - `completar_descricao` aplica critérios;
  - `analise.precisa` e `banco.precisa_analise` pulam pendentes;
  - fonte sem o atributo continua igual.

**Checkpoint**: MVP. Uma busca com o LinkedIn faz no máximo 20 leituras de descrição, e nenhuma vaga sem texto recebe
nota.

---

## Phase 5: User Story 4 - Aviso quando há cargos demais (Priority: P3)

**Goal**: aviso, sem bloquear, quando há mais de 5 cargos e o LinkedIn ou o Indeed estão ligados.

**Independent Test**: quickstart §3.2 e a primeira linha de `vagas.py buscar`.

- [X] T022 [US4] Em `filtros.py`, `MAX_CARGOS_AVISO = 5` e `aviso_cargos(f, fontes) -> str | None` (research R11):
  - avisa quando `len(f["termos"]) > 5`, ou quando a busca internacional está ligada e os cargos do exterior passam
    de 5;
  - só se `linkedin` ou `indeed` estiverem entre as fontes;
  - texto: "Mais de 5 cargos com LinkedIn ou Indeed ligados aumentam o risco de bloqueio desses portais."
- [X] T023 [US4] Mostrar o aviso:
  - `vagas.cmd_buscar` imprime antes das consultas;
  - `executar` guarda em `resultado["aviso_cargos"]`;
  - `dash/buscador.py` `plano()` devolve `aviso_cargos`;
  - `dash/dashboard.html`: no painel de filtros, uma linha ao lado de `#fb-conta`, com a mesma regra em JS
    (`d.termos.length > 5` ou os cargos do exterior com `d.internacional.ativo`, e `linkedin`/`indeed` em
    `d.fontes`), sem desligar o "Salvar"; no diálogo de busca, a linha `p.aviso_cargos`.
- [X] T024 [P] [US4] Testes em `tests/test_busca.py` (ou `tests/test_internacional.py`, onde os filtros já são
  testados) para `aviso_cargos`:
  - 5 e 6 cargos;
  - sem LinkedIn/Indeed;
  - cargos do exterior;
  - salvar continua válido com 6 cargos (`filtros.validar`).

**Checkpoint**: aviso de cargos na página, no terminal e no chat (pela saída do terminal).

---

## Phase 6: User Story 1 (consulta combinada) - atrás do portão R1 (Priority: P1)

**Goal**: uma consulta por grupo no LinkedIn, com os cargos ligados por OR, até 3 páginas.

**Independent Test**: quickstart §1 (expressão, agrupamento, cargos pelo título) e §2.

- [X] T025 [US1] **PORTÃO R1**. Com o OK da pessoa, fora de qualquer espera, de preferência noutra rede ou com a
  US3 pronta (para ver o código), fazer **um único** pedido com 2 a 3 cargos fictícios ligados por OR (quickstart §2) e
  anotar o resultado em `specs/015-linkedin-menos-pedidos/research.md` (R1).
  - Se aceitar: seguir para a T026.
  - Se não aceitar: manter `AGRUPAR = False`, pular as T026 a T030, registrar o plano B no research e no README e ir
    para a Phase 7.
- [X] T026 [US1] Em `filtros.py`, `expressao_or(termos, maximo=200) -> list[str]` (research R2/R3):
  - cargo entre aspas fica como está;
  - cargo de uma palavra vai sem aspas;
  - cargo de várias palavras sem aspas vai entre parênteses;
  - aspas soltas são removidas;
  - os cargos são ligados por `" OR "` e divididos em partes de até `maximo` caracteres, na ordem da configuração.
  
  `termos_no_titulo(titulo, termos) -> list[str]` (research R5) compara sem acento e sem diferenciar maiúsculas; um
  cargo entre aspas precisa aparecer em sequência.
- [X] T027 [US1] Em `vagas.py`:
  - `agrupar(plano, fonte)`: para fontes com `AGRUPAR`, junta as consultas do mesmo `grupo` (e da mesma `area`/`pais`)
    numa por parte de `expressao_or`, com `termos`, `termo` e `agrupada: True`;
  - `executar` usa as consultas agrupadas para essas fontes;
  - os termos de cada vaga vêm de `filtros.termos_no_titulo(v["titulo"], c["termos"]) or [c["termo"]]`;
  - o evento de progresso mostra `cargo` como "N cargos";
  - `contar_consultas` conta pelo agrupamento (research R12).
- [X] T028 [US1] Em `fontes/linkedin.py`:
  - `AGRUPAR = True`;
  - `parametros` usa `consulta["termo"]` sem `strip('"')` quando `consulta.get("agrupada")` e com mais de um cargo,
    e mantém o comportamento atual com um cargo só;
  - `buscar` usa `MAX_PAGINAS_AGRUPADA` na consulta agrupada.
- [X] T029 [P] [US1] Em `dash/dashboard.html`, `contarLinkedin(d)` conta 1 consulta por grupo, e não grupos × cargos
  (research R12). O texto de `#fb-conta` continua igual.
- [X] T030 [P] [US1] Testes:
  - em `tests/test_linkedin.py`: `expressao_or` (aspas, parênteses, um cargo, aspas soltas, divisão por tamanho),
    `parametros` agrupado e com um cargo, e até 3 páginas parando com página incompleta;
  - em `tests/test_busca.py`: uma consulta por grupo para o LinkedIn e uma por cargo para as outras fontes,
    `termos_no_titulo`, e a contagem de consultas.

**Checkpoint**: com 7 cargos e 2 grupos, no máximo 26 pedidos ao LinkedIn por busca (SC-001).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T031 [P] Documentação:
  - no `README.md`, na seção de fontes e bloqueio: limite por rede, espera de 6 horas, descrições pendentes, aviso de
    cargos e, se a T025 passar, a consulta combinada;
  - no `AGENTS.md`, na linha "Respeite os portais": "depois de um bloqueio, o LinkedIn fica 6 horas de fora, e a
    busca pergunta antes de seguir sem ele".
- [X] T032 Rodar `python sincronizar_skills.py` e `python sincronizar_skills.py --conferir`
- [X] T033 Rodar `python -m unittest discover -s tests`: todos passam, com o total maior que a linha de base da T001.
  Comparar a saída guardada na T001 (SC-006).
- [X] T034 Verificação na página (Windows), pelo quickstart §3: servidor com `--sem-navegador`, Chrome sem janela
  ou Live Server, com espera simulada, aviso de cargos e chip de pendente.
- [ ] T035 Antes do commit:
  - procurar dados pessoais no diff (nomes, empresas, cargos do usuário, caminhos pessoais);
  - mostrar o resultado à pessoa;
  - com o OK dela: commit no branch, merge na `master`, push, merge na branch pessoal e `graphify update .`.

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002–T003)** → as histórias.
- **US3 (T004–T013)**: depende só da Foundational. Vem primeiro porque mostra o código da recusa no próximo teste
  do OR.
- **US1-limite + US2 (T014–T021)**: depende da Foundational. Usa `parada()` da T005, então vem depois da US3.
- **US4 (T022–T024)**: independente. Pode vir em paralelo com a Phase 4.
- **US1-combinada (T026–T030)**: depende do **portão T025**. A T027 depende da T026; a T028 depende da T027.
- **Polish (T031–T035)**: depois das histórias entregues. Sem o OR, depois da Phase 5.

### Parallel Opportunities

- US3: T011 e T012 (testes) em paralelo, depois da T004–T010; T013 (skill) em paralelo com o código.
- Phase 4: T015, T019 e T020 em paralelo depois da T014/T016; T021 no fim.
- US4 inteira em paralelo com a Phase 4 (arquivos diferentes, exceto `vagas.py`/`dashboard.html`: alternar com
  cuidado).
- US1-combinada: T029 e T030 em paralelo depois da T028.

### Parallel Example: Phase 4

```text
T015 dash/analise.py   precisa() pula pendentes
T019 dash/dashboard.html   chip e banner "Descrição pendente"
T020 vagas.py   saída do terminal e digest
```

---

## Implementation Strategy

1. **MVP = Phases 1–4.** Espera com motivo, limite de 20 descrições e pendentes. Isso já corta a maior parte dos
   pedidos (as descrições), sem depender do OR.
2. **Incremento: Phase 5** (aviso de cargos).
3. **Portão T025**, com o OK da pessoa. Se passar, Phase 6; se não, plano B documentado.
4. **Polish e entrega**, com o OK da pessoa em cada passo público (commit, push).
