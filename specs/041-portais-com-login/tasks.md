---
description: "Tarefas da feature 041: portais com login na busca, com o MyGreenhouse Jobs como primeiro portal (Windows)"
---

# Tasks: Portais com login na busca (primeiro: MyGreenhouse Jobs)

**Input**: spec.md, plan.md (com a emenda 5.3.0 aprovada em 2026-11-01), research.md (R1–R4, D1–D11), data-model.md,
contracts/sessao.md, contracts/mygreenhouse.md, contracts/api.md, quickstart.md. Moldes: `fontes/fullstack.py` (pausa,
espera, `parada`), `contas/` e `dash/sincronia.py` (aba logada e espera de login), `fontes/ats.py` (id e `ler`).

**Testes**: incluídos (roteiro `docs/novo-portal.md`, seção 5, e quickstart.md §1). Nenhum teste faz pedido à rede ou
abre o navegador:
- a `Aba` é falsa e devolve as amostras de `tests/dados/mygreenhouse/`;
- `navegador`, `contas.conectados`, `ats.ler`, o relógio e o `sleep` são trocados;
- o estado e a espera ficam numa pasta temporária.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Emenda da constituição em `.specify/memory/constitution.md` (5.2.0 → 5.3.0, MINOR), com o texto aprovado no
  plan.md, seção "Emenda proposta":
  1. no 1º parágrafo do princípio VI, depois de "…sem nova tentativa nem forma de contornar.", a frase "A exceção é a
     busca com login (abaixo).";
  2. a seção nova **"Busca com login"** depois de "Conta conectada", com os seis itens (portal por portal; login da
     pessoa, na janela da ferramenta; só no clique da página; só leitura, só a busca; pouco e parando; termos
     contrários, com o exemplo do MyGreenhouse Jobs, spec 041, decisão de 2026-11-01);
  3. o relatório de impacto no topo, data 2026-11-01, com a lista de arquivos de documentação atualizados (T028 a T030).
- [X] T002 [P] Amostras fictícias em `tests/dados/mygreenhouse/`, no formato da research R2. Empresas, títulos, ids,
  `urlToken` e locais trocados, sem `currentUserEmail` nem dado de conta real:
  - `data-page.json`: o `{component: "jobs", version}` que a leitura do `data-page` devolve (a aba falsa responde
    com ele);
  - `pagina-1.json`: `props.jobPosts` com 12 vagas e `moreResultsAvailable: true`:
    - títulos que batem e que não batem com "scrum master";
    - uma remota só para os EUA, uma aberta ao Brasil, uma "LATAM" e uma `hybrid`;
    - `viewed`, `appliedAt` e `saved` preenchidos, para provar que são descartados;
    - `payRanges`, `summary` e `description` nulos;
  - `pagina-2.json`: `moreResultsAvailable: false`, com uma vaga dentro da janela e uma de `firstPublished` antigo;
  - `sem-jobposts.json`: resposta Inertia sem `props.jobPosts` (o caso "o portal mudou").

## Phase 2: Foundational (bloqueia as histórias)

- [X] T003 Área comum em `fontes/_sessao.py`, pelo contrato `contracts/sessao.md`:
  - `PortalComLoginErro(motivo, tipo)`, com `tipo` em `"login"`, `"captcha"`, `"bloqueio"`, `"mudou"` ou `"janela"`;
  - `na_pagina(esperar_login)` (contextmanager), `dentro_da_pagina()` e `aviso_fora(modulo)`:
    - o texto do aviso é `"<ROTULO>: só pelo botão Buscar da página (portal com login)"`;
    - abrir aninhado ou em outra thread com o contexto já ligado é erro de uso;
  - `conectados()` e `marcar(nome, conectado)` em `.cache/portais-login.json`, formato
    `{"conectados": {"<nome>": {"desde": "AAAA-MM-DD"}}}`. Arquivo ausente ou inválido dá `[]`;
  - `aba(modulo)`: uma aba em segundo plano por portal e por busca, com `navegador.abrir_para_leitura(URL_BUSCA)`,
    reaproveitada nos pedidos seguintes. `fechar_abas()` roda no fim do `with`;
  - `no_portal(modulo, aba)`: o host de `aba.url()` está em `modulo.DOMINIOS`. Toda chamada a `aba.avaliar` passa por
    ele antes;
  - `pedir_json(modulo, aba, url, cabecalhos) -> (status, dados | None)`: `fetch` GET com `credentials: "include"`, de
    dentro da aba e só com `no_portal`. Resposta que não é JSON dá `dados = None`;
  - `captcha_na_aba(modulo, aba)`, só com `no_portal`: iframe visível de reCAPTCHA, hCaptcha ou Cloudflare, ou texto
    de verificação. Reaproveita a ideia de `candidatura/formulario.captcha_visivel`, sem importar a candidatura;
  - `esperar(modulo, aba, segundos=180, passo=3, cancelado=None, relogio=time.monotonic, dormir=time.sleep) -> bool`:
    lê só `aba.url()` e `modulo.logado(url)` e para com `cancelado()`;
  - `garantir_login(modulo, aba)`: se `logado(aba.url())` for falso, chama o `esperar_login` do contexto. Com `True`,
    recarrega `URL_BUSCA`; com `False`, levanta `PortalComLoginErro(tipo="login")`;
  - `algum_conectado()`: `conectados()` ou `contas.conectados()`;
  - `desconectar(modulo)`: `marcar(nome, False)`. Se `algum_conectado()` ainda for verdadeiro, apaga `ORIGENS` e
    `ORIGENS_SSO` com `Storage.clearDataForOrigin`, como em `dash/servidor.py` (contas). Se não, chama
    `navegador.desconectar()`.

  O único JavaScript que roda na aba é a leitura (`fetch` GET e consulta ao DOM). Nada de clique, digitação, `submit`
  ou leitura de campo de senha.
- [X] T004 Registro e listas comuns:
  - `fontes/__init__.py`: o registro de `mygreenhouse` em `FONTES`, e na docstring os atributos de portal com login
    (`COM_LOGIN`, `ROTULO`, `URL_LOGIN`, `URL_BUSCA`, `DOMINIOS`, `ORIGENS`, `ORIGENS_SSO`, `AVISO_RISCO`,
    `AVISO_LOGIN`, `logado(url)`; data-model.md);
  - `filtros.py`:
    - `FONTES_LOGIN = {"mygreenhouse": "MyGreenhouse Jobs"}`, fora de `FONTES_PADRAO`;
    - na leitura do painel (`fontes`), aceitar os nomes de `FONTES_LOGIN` depois dos de `FONTES_NAC`. "Marque pelo
      menos um portal" continua contando só os portais de busca pública, porque um portal com login não roda no
      terminal;
    - `fontes_login()` para o painel: `[{nome, rotulo, termos, aviso_risco, aviso_login}]`, em `opcoes()` como
      `"fontes_login"`;
  - `dash/banco.py`: `"MyGreenhouse"` em `PLATAFORMAS`;
  - `integridade.py`: `"MyGreenhouse": ("my.greenhouse.io",)` em `PORTAIS`.
- [X] T005 Testes da área comum em `tests/test_sessao.py`, com `Aba` e `navegador` falsos:
  - fora do contexto, `dentro_da_pagina()` é falso; o contexto aninhado é erro;
  - `conectados` e `marcar`, inclusive com o arquivo ausente ou inválido;
  - `no_portal`: só os hosts de `DOMINIOS`. `pedir_json` fora do portal não chama `avaliar`;
  - `esperar` com relógio e `sleep` trocados: logou no meio, o tempo acabou e cancelado;
  - `garantir_login`: logado não chama o callback; `False` levanta `tipo="login"`;
  - `desconectar`: com outro portal ou conta conectada, só apaga as origens; sem nenhum, chama
    `navegador.desconectar()`;
  - nenhum script mandado a `avaliar` contém `click`, `.value =`, `submit` ou `password`.

**Checkpoint**: a área comum existe e é testada sem nenhum portal.

---

## Phase 3: User Story 1 - Conectar um portal com login (Priority: P1) 🎯 MVP

**Goal**: a pessoa liga o MyGreenhouse com o aviso de risco, conecta pela janela, vê a situação e desconecta.

**Independent Test**: com o navegador falso, `GET /api/portais-login` mostra a situação certa em cada caso. Conectar abre
`URL_LOGIN` na frente. Pronto com sessão marca "conectado"; sem sessão, devolve `conectado: false`. Desconectar volta
para "desconectado" e só apaga o perfil inteiro sem outra conexão.

- [X] T006 [US1] Constantes e `logado(url)` de `fontes/mygreenhouse.py`, pelo `contracts/mygreenhouse.md`:
  - `NOME`, `PLATAFORMA`, `ROTULO`, `AREAS`, `POR_PAIS`, `GLOBAL`, `COM_LOGIN = True` e `TERMOS`;
  - `URL_LOGIN`, `URL_BUSCA`, `DOMINIOS`, `ORIGENS` e `ORIGENS_SSO`;
  - `AVISO_RISCO` e `AVISO_LOGIN`;
  - `logado(url)`: host `my.greenhouse.io` e caminho fora de `/users/sign_in`.

  O resto do módulo entra na US2.
- [X] T007 [US1] Rotas em `dash/servidor.py`, pelo `contracts/api.md`:
  - `GET /api/portais-login` devolve `{navegador, portais: [{nome, rotulo, termos, aviso_risco, aviso_login, ligado,
    conectado, situacao, espera}]}`. A `situacao` segue a ordem `desligado` → `em_espera` → `desconectado` →
    `conectado` (data-model.md);
  - `POST /api/portais-login/{portal}/conectar`: abre `URL_LOGIN` com `navegador.abrir(...).frente()`;
  - `POST /api/portais-login/{portal}/pronto`: confere `logado(aba.url())` numa aba em segundo plano, só pelo endereço.
    Com o login, chama `_sessao.marcar(portal, True)` e minimiza. Devolve `{conectado}`;
  - `POST /api/portais-login/{portal}/desconectar` chama `_sessao.desconectar(modulo)`.

  Regras das rotas:
  - só pedidos locais, como `/api/contas`: outro aparelho recebe 403 `SO_LOCAL_PERFIL`;
  - portal fora de `filtros.FONTES_LOGIN` recebe 404 "portal desconhecido";
  - erro de navegador recebe 409 com a mensagem;
  - `/api/portais-login` entra nas listas de prefixos onde `/api/contas` aparece hoje (perto das linhas 789 e 834).
- [X] T008 [US1] O Desconectar das contas em `dash/servidor.py` (`/api/contas/{portal}/desconectar`) troca
  `if not contas.conectados()` por `if not _sessao.algum_conectado()`. Assim, desconectar a Gupy não apaga a sessão
  do MyGreenhouse.
- [X] T009 [US1] Testes das rotas em `tests/test_sessao.py`, com o servidor de teste já usado em `tests/test_contas.py`
  e o navegador falso:
  - situação desligado, em espera, desconectado e conectado;
  - Conectar, Pronto com e sem login, Desconectar;
  - 404 com portal desconhecido e 403 com pedido de fora;
  - o Desconectar das contas mantém o perfil quando há um portal com login conectado.
- [X] T010 [P] [US1] Front na `frontend-react` (worktree `../mpt-front-027b`):
  - `src/types/api.ts`: `PortalLogin` e `fontes_login` nas opções do painel;
  - `src/services/api/`: `portaisLogin()`, `conectarPortal`, `prontoPortal` e `desconectarPortal`;
  - `src/components/modals/SearchFiltersModal.tsx`: seção "Portais com login", separada dos portais de busca pública,
    com:
    - nome, termos e `aviso_login`;
    - o liga/desliga, que pede a confirmação de `aviso_risco` antes de pôr o portal em `fontes`;
    - Conectar, Pronto e Desconectar;
    - a situação, com o fim da espera quando houver.

**Checkpoint**: a área funciona sozinha. O portal pode ser ligado e conectado, mesmo sem a busca.

---

## Phase 4: User Story 2 - Vagas do MyGreenhouse no Buscar da página (Priority: P1)

**Goal**: com o portal ligado e conectado, o Buscar da página traz as vagas remotas abertas ao Brasil para o relatório,
com a etiqueta "MyGreenhouse".

**Independent Test**: com a `Aba` falsa e as amostras, `buscar` dentro de `na_pagina` devolve as vagas filtradas, no
formato comum, sem os campos da conta. O id é o mesmo de `fontes/ats.py`. O desligado faz zero pedidos.

- [X] T011 [US2] Leitura em `fontes/mygreenhouse.py`:
  - `PAISES`, `POR_PAGINA = 12`, `MAX_PAGINAS = 3`, `MAX_DESCRICOES = 30`, `JANELA_5_DIAS = 120` e `PROPS`.
    `PROPS` vale `"browsing,page,moreResultsAvailable,jobPosts"`, nunca com `trackingData` nem `recentSearches`;
  - `endereco(cargo, consulta, horas, pagina)` monta o endereço com:
    - `query` sem aspas e `work_type[]=remote`;
    - na consulta nacional, os parâmetros do país em `PAISES`;
    - `date_posted=past_five_days` se `horas <= 120`;
    - `page` a partir de 2;
  - `ler_resposta(dados) -> (vagas, mais)`, pelo mapeamento de data-model.md:
    - id `_comum.ident("greenhouse", f"{urlToken}-{id}")`, `plataforma` "MyGreenhouse", `ats` "greenhouse" e
      `url = publicUrl`;
    - `local` e `restricao_local` com `locations` juntos por "; ";
    - `workType` vira `remoto` e `modelo_trabalho`;
    - `publicada_em = firstPublished[:10]`;
    - descarta `viewed`, `appliedAt`, `saved`, `departmentId`, `logoUrl`, `summary`, `description` e `payRanges`;
    - sem `props.jobPosts`, levanta `PortalComLoginErro(tipo="mudou")`;
  - a versão do Inertia vem do `data-page` da primeira carga da aba, uma vez por busca;
  - o pedido vai com os cabeçalhos `X-Inertia: true`, `X-Inertia-Version`, `X-Inertia-Partial-Component: jobs` e
    `X-Inertia-Partial-Data: PROPS`, por `_sessao.pedir_json`.
- [X] T012 [US2] `buscar(consulta, horas, por_termo)` em `fontes/mygreenhouse.py`:
  - fora de `na_pagina`, devolve `([], [aviso_fora])` uma vez por busca, sem tocar no navegador;
  - na área nacional, só o grupo remoto com país em `PAISES` faz pedido. Cidade, estado e país desconhecido devolvem
    `([], [])`;
  - na internacional, só a consulta global, sem local;
  - lê até `MAX_PAGINAS` páginas, ou até `mais = False`, com `_pausar()` entre os pedidos;
  - filtra pelo cargo (`_comum`), pela janela (`publicada_em`) e, no grupo remoto nacional, por
    `filtros.aberta_ao_pais`;
  - respeita `por_termo`.
- [X] T013 [US2] `descrever(vaga)` em `fontes/mygreenhouse.py`: `ats.ler(vaga["url"])["descricao"]`, pela API pública e
  sem a sessão. Em erro, devolve o que a vaga já tinha. Lê no máximo `MAX_DESCRICOES` por busca.
- [X] T014 [US2] Pausa e espera em `fontes/mygreenhouse.py`, como em `fontes/fullstack.py`:
  - `PAUSA = (3.0, 7.0)`, `VAR_PAUSA = "MYGREENHOUSE_PAUSA"`, `PAUSA_MIN = 3.0` e `PAUSA_FAIXA = 4.0`;
  - `ESPERA` de 24 h em `ARQ_ESPERA = .cache/mygreenhouse-espera.json`;
  - `pausa()`, `aviso_pausa(consultas)`, `espera()`, `parada()` e `_bloquear()`. `aviso_pausa` conta
    `MAX_PAGINAS × cargos + 1`.
- [X] T015 [US2] `dash/buscador.py`:
  - `_rodar` passa a chamar `vagas.executar` dentro de `_sessao.na_pagina(esperar_login=self._esperar_login)`.
    `vagas.executar` não muda de assinatura;
  - nesta história, `_esperar_login` só devolve `False` (o portal é pulado com aviso). A espera de verdade entra na
    US3;
  - `plano()` conta os pedidos do portal com login quando ele está ligado e conectado. Ligado e desconectado, avisa
    "conecte em Portais com login".
- [X] T016 [US2] Testes em `tests/test_mygreenhouse.py`, com a `Aba` falsa:
  - `endereco`: aspas, remoto, país, `date_posted` até 120 h e não acima, `page`;
  - `ler_resposta`:
    - campos e descartados (nenhum `viewed`, `appliedAt` ou `saved` na vaga);
    - id igual a `ats.ident` e `workType`;
    - `locations` e `restricao_local`;
  - `buscar` nas duas páginas, com parada em `mais = False` e no limite de `MAX_PAGINAS`;
  - os filtros de título, de janela e de `aberta_ao_pais`, com a vaga só dos EUA fora e a aberta ao Brasil dentro;
  - cidade e outro país sem pedido; internacional sem local; `por_termo`;
  - `descrever` com `ats.ler` trocado, inclusive em erro.
- [X] T017 [US2] Casos novos em `tests/test_busca.py`:
  - a busca da página roda dentro de `na_pagina`;
  - com `"mygreenhouse"` fora de `fontes` (o padrão), zero pedidos e a mesma busca de antes;
  - a mesma vaga vinda de `ats` e de `mygreenhouse` aparece uma vez (junção pelo id);
  - o filtro de integridade age numa vaga do MyGreenhouse com texto escondido;
  - o `plano` conta o portal ligado e conectado, e avisa quando está desconectado.

**Checkpoint**: US1 e US2 juntas formam o MVP: ligar, conectar e buscar pela página.

---

## Phase 5: User Story 3 - Login caído (Priority: P2)

**Goal**: com a sessão expirada, a janela vem para a frente, a página mostra "aguardando login" e a busca espera até
3 minutos, sem travar os outros portais.

**Independent Test**: com o relógio e o `sleep` trocados:
- `BUSCA.estado()` mostra `situacao: "aguardando_login"` e `login: {portal, rotulo, ate}`;
- logou: a busca segue;
- o tempo acabou: o portal é pulado com aviso em `erros`;
- cancelar interrompe a espera.

- [X] T018 [US3] `_esperar_login(modulo, aba)` de verdade em `dash/buscador.py`:
  1. `_set(situacao="aguardando_login", login={"portal", "rotulo", "ate"})` e `aba.frente()`;
  2. `_sessao.esperar(modulo, aba, cancelado=self._cancelar.is_set)`;
  3. no fim, minimiza a janela e volta para `situacao="consultando"` com `login=None`.

  `"aguardando_login"` entra na regra de `_set` que impede o "cancelando" de voltar atrás (linha 83).
- [X] T019 [US3] Em `fontes/mygreenhouse.py`, a resposta 401 ou o endereço de `/users/sign_in` chama
  `_sessao.garantir_login`. Com `tipo="login"`, o aviso diz que o portal foi pulado por falta de login, e ele fica fora
  do resto da busca.
- [X] T020 [US3] Testes:
  - `tests/test_busca.py`: o estado durante a espera; logou e seguiu; o tempo acabou com o aviso e as vagas dos outros
    portais gravadas; o cancelamento durante a espera;
  - `tests/test_mygreenhouse.py`: 401 e redirecionamento chamam o callback; sem login, nenhum pedido depois.
- [X] T021 [P] [US3] Front na `frontend-react`:
  - `src/types/api.ts`: `"aguardando_login"` na situação da busca e o campo `login`;
  - no progresso da busca, o texto `"Aguardando login no <rotulo>: entre na janela da ferramenta (faltam N s)"`.

**Checkpoint**: login caído sem travar a busca.

---

## Phase 6: User Story 4 - Bloqueio, captcha, portal mudado e busca fora da página (Priority: P2)

**Goal**: a ferramenta para no primeiro sinal de problema, sem nova tentativa, e nunca usa a sessão fora do clique da
página.

**Independent Test**:
- 403, 429 e 503 gravam 24 h de espera, e depois disso nenhum pedido sai;
- captcha traz a janela e para sem espera;
- resposta sem `jobPosts` dá "o portal mudou";
- `vagas.py buscar --fontes mygreenhouse` não abre a janela.

- [X] T022 [US4] Paradas em `fontes/mygreenhouse.py` (contrato, tabela "Parada no primeiro problema"):
  - `BLOQUEIOS` (403, 429, 503) ou página de desafio: `_bloquear()` com `_comum.gravar_espera`, `parada()` e aviso
    com o fim da espera;
  - na espera: aviso uma vez e nenhum pedido (busca e descrição);
  - 409: recarrega a aba uma vez por busca. Se repetir, "o portal mudou; a leitura precisa de ajuste";
  - captcha (`_sessao.captcha_na_aba`): aviso "resolva na janela e busque de novo" e `aba.frente()`, sem espera;
  - "mudou" e "janela" (navegador ausente ou janela fechada): aviso, e o portal fica fora do resto da busca. As outras
    fontes seguem.
- [X] T023 [US4] `vagas.py`: `fontes_em_espera(nomes_fontes, pagina=False)` ignora as fontes com `COM_LOGIN` quando
  `pagina` é falso. `dash/buscador.py` passa `pagina=True` no `plano` e no `iniciar`, para perguntar antes de seguir
  sem o MyGreenhouse em espera. No terminal, a busca não pergunta por um portal que não vai rodar.
- [X] T024 [P] [US4] `.env.exemplo`: a linha
  `# MYGREENHOUSE_PAUSA=3   # padrão 3 a 7 s (sorteado); mínimo 3 s para este portal`, perto da `FULLSTACK_PAUSA`.
- [X] T025 [US4] Testes em `tests/test_mygreenhouse.py`:
  - 403, 429 e 503 param no primeiro pedido, sem nova tentativa, e gravam a espera. Depois, zero pedidos e o aviso sai
    uma vez;
  - desafio; captcha com `frente()` e sem espera;
  - resposta sem `jobPosts`; 409 com uma recarga e depois "mudou"; erro de navegador ("janela");
  - pausa padrão, do `.env`, abaixo do mínimo e inválida;
  - fora da página, com `vagas.executar` chamado direto: o aviso `aviso_fora` e o `navegador` nunca chamado;
  - `vagas.fontes_em_espera` com e sem `pagina`.

**Checkpoint**: todas as paradas cobertas, e o terminal e o chat sem a sessão.

---

## Phase 7: User Story 5 - Acompanhar a empresa da vaga (Priority: P3)

**Goal**: a vaga do MyGreenhouse de empresa com página pública oferece "Acompanhar empresa", como as vagas do Greenhouse
adicionadas pelo link.

**Independent Test**: `ats.vaga_do_link(publicUrl)` reconhece o link da amostra, e a vaga tem `ats: "greenhouse"`.

- [X] T026 [US5] Conferir que o "Acompanhar empresa" do detalhe da vaga usa o campo `ats` ou o link da vaga
  (`ats.vaga_do_link`, `filtros.acompanhar`). Se o front decidir pela `plataforma`, incluir "MyGreenhouse" na regra da
  `frontend-react`. Caso de teste em `tests/test_mygreenhouse.py`: o `publicUrl` da amostra
  (`job-boards.greenhouse.io/<empresa>/jobs/<id>`) é reconhecido por `ats.vaga_do_link`, com o mesmo `urlToken`.
- [X] T027 [P] [US5] Front na `frontend-react`: em `src/utils/formatters.ts`, a etiqueta "MyGreenhouse" e o domínio
  `my.greenhouse.io` no mapa de plataformas.

**Checkpoint**: todas as histórias funcionando.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T028 [P] Documentação:
  - `README.md`: a área "Portais com login", o MyGreenhouse desligado por padrão, os termos contrários, o login na
    janela e "só pelo Buscar da página";
  - `dash/README.md`;
  - `dash/API.md`: as rotas `/api/portais-login`, o `aguardando_login` e o `login` no estado da busca, o `plano` e o
    Desconectar das contas;
  - `AGENTS.md`, em "Respeite os portais": a busca com login, só pelo botão da página, que o assistente nunca usa.
- [X] T029 [P] Roteiro e lista:
  - `docs/novo-portal.md`: seção nova "Portal com login" (atributos, `_sessao`, testes com a `Aba` falsa, spec própria
    com análise de risco);
  - `specs/lista-de-desejos.md`: o item do Greenhouse como portal passa a "feito na spec 041".
- [X] T030 [P] Skill: `.agents/skills/buscar-vagas/SKILL.md` (portais com login: o assistente não usa a sessão; na busca
  pelo chat, o portal fica de fora com aviso), depois `python sincronizar_skills.py` e
  `python sincronizar_skills.py --conferir`.
- [ ] T031 Front na `frontend-react`: `npm run build` sem erro de tipo. Commit local, e o push só com o OK da pessoa
  depois do teste.
- [ ] T032 Verificação e entrega:
  1. a suíte inteira (`python -m unittest discover -s tests`);
  2. a busca por dados pessoais nos arquivos alterados;
  3. o commit na branch `041-portais-com-login`;
  4. o merge na branch pessoal, com o dashboard reiniciado (`dash\servidor.py --sem-navegador`);
  5. o quickstart.md §2 com a pessoa (ligar, conectar, Buscar, login caído, terminal, Desconectar);
  6. `graphify update .`.

  Master, push e PR do front só com o OK dela depois do teste.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: T001 vem primeiro (a emenda é a primeira tarefa). T002 pode correr junto.
- **Foundational**: T003 → T004 → T005. Bloqueia todas as histórias.
- **US1** (T006–T010) depende da fase 2. T010 (front) pode correr em paralelo com T007–T009.
- **US2** (T011–T017) depende da fase 2 e de T006 (constantes do módulo). T011 → T012 → T013. T014 entra antes de
  T012 (a pausa). T015 depende de T012. T016 e T017 vêm no fim da história.
- **US3** (T018–T021) depende de T015 (o callback) e de T012.
- **US4** (T022–T025) depende de T012 e T014. T023 depende de T015.
- **US5** (T026–T027) depende de T011 (o formato da vaga).
- **Polish** depende das histórias escolhidas.

### Arquivos compartilhados (mudam em sequência)

- `fontes/mygreenhouse.py`: T006, T011, T012, T013, T014, T019 e T022;
- `dash/buscador.py`: T015, T018 e T023;
- `dash/servidor.py`: T007 e T008;
- `tests/test_mygreenhouse.py`: T016, T020, T025 e T026;
- `tests/test_busca.py`: T017 e T020;
- `tests/test_sessao.py`: T005 e T009;
- a `frontend-react`: T010, T021, T027 e T031, em sequência na mesma worktree.

### Parallel Opportunities

- T001 e T002;
- o front (T010, T021, T027) em paralelo com o Python da mesma história;
- T024, T028, T029 e T030 (arquivos diferentes).

## Parallel Example: User Story 1

```text
Task: "Rotas /api/portais-login em dash/servidor.py" (T007)
Task: "Seção Portais com login em SearchFiltersModal.tsx na frontend-react" (T010)
```

## Implementation Strategy

### MVP (US1 + US2)

1. T001 (emenda) e T002 (amostras).
2. Fase 2: a área comum e o registro.
3. US1: ligar, conectar e desconectar.
4. US2: as vagas no Buscar da página.
5. Parar e validar com a suíte e com o quickstart §1.

### Incremental

1. US3: o login caído.
2. US4: as paradas e o terminal.
3. US5: o Acompanhar empresa.
4. Polish e a entrega na branch pessoal para o teste da pessoa (T032).
