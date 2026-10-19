---

description: "Tarefas da feature 018: Contas conectadas (Windows)"
---

# Tasks: Contas conectadas

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[quickstart.md](quickstart.md)

**Tests**: `unittest` sem rede e sem navegador real (a `Aba` é substituída por uma falsa), com JSON fictício.

## Phase 1: Setup e base

- [X] T001 Emenda da constituição 3.0.0 (Conta conectada), aprovada pela pessoa (commit `dc8bc34`).
- [X] T002 `navegador.py`: achar o navegador, abrir com perfil próprio (esperando sair do `about:blank`), WebSocket
  mínimo, `Aba.ir`/`avaliar`/`url`/`frente`, `fechar`, `desconectar`.
- [X] T003 Pesquisa com a pessoa logada (research.md): APIs da Gupy e do Indeed, categorias de etapa da Gupy,
  `statuses` do Indeed, sessão da Gupy que some ao fechar.
- [X] T004 [P] Dados de teste fictícios em `tests/dados/contas/`:
  - `gupy-lista.json` e `gupy-etapas.json`, com a mesma estrutura do research §3;
  - `indeed-applied.json`, com a estrutura do §4;
  - `linkedin-tracker.html`, com a estrutura do print.

## Phase 2: Contrato e portais (US3, US4)

- [X] T005 `contas/__init__.py`:
  - `PortalErro(motivo, login=False)` e `Lida` (dict com os campos do data-model);
  - `ORDEM` das etapas e `avancou(de, para)`;
  - `TODAS` = {gupy, indeed, linkedin} e `CONTAS` = só os `ATIVO`;
  - docstring do contrato: `NOME`, `PLATAFORMA`, `ATIVO`, `ICONE`, `URL_LOGIN`, `URL_CANDIDATURAS`,
    `conectado(aba)`, `ler(aba, esperar_login)` e `traduzir(item)`.
- [X] T006 [US3] `contas/gupy.py`:
  - lista pela API em `portal.gupy.io`;
  - detalhe das ativas na página da empresa, com o mapa em `.cache/contas/gupy.json`;
  - `traduzir` pela tabela do research §3;
  - login: 401 → `PortalErro(login=True)`;
  - nunca clicar em nada.
- [X] T007 [US3] `contas/indeed.py`:
  - `appStatusJobs?type=POST_APPLY` e `interviews` em `myjobs.indeed.com`;
  - `traduzir` pela tabela do research §4 (status mais forte; data do timestamp);
  - avisos de vaga fechada ou expirada;
  - login (redireciona para `secure.indeed.com`) → `PortalErro(login=True)`.
- [X] T008 [US4] `contas/linkedin.py`:
  - `ATIVO = False`;
  - leitura da tela do Rastreador de vagas (cargo, empresa, local, "há N sem/m" → data aproximada, filtro da
    página → etapa);
  - "Não aceita mais candidaturas" e Arquivadas só informam.

## Phase 3: Sincronia (US2)

- [X] T009 [US2] `dash/sincronia.py`, `proposta(lidas, vagas)`:
  - casamento por `banco.ids_da_vaga` (todos os ids do banco) e, na falta, por `banco.chave_vaga` no banco inteiro;
  - tipos `mudar`/`quadro`/`nova`/`info`;
  - não rebaixar a etapa, encerrada é final;
  - marcado padrão do data-model;
  - mesma vaga em dois portais fica com o item mais avançado.
- [X] T010 [US2] `dash/sincronia.py`, `aplicar(itens)`:
  - `mudar`: `banco.atualizar_usuario` (etapa, `etapa_em`, resultado) + `banco.anotar` + `conta_status`;
  - `quadro`: o mesmo + triagem `seguir`;
  - `nova`: descrição pelo leitor público quando der (Gupy `fontes/gupy.ler`, Indeed `fontes/link.ler`);
    `banco.criar_de_link` e depois atualizar a etapa e a triagem; se falhar, cria com cargo, empresa e link.
- [X] T011 [US2] `dash/sincronia.py`, `Leitura` (thread):
  - estados `parada`/`lendo`/`aguardando_login`/`pronta`/`erro`, com o portal atual;
  - abre a janela minimizada e lê cada conta conectada;
  - em `PortalErro(login=True)`, traz a janela para a frente e espera até 3 minutos a API responder;
  - um portal com erro não para os outros;
  - fecha a janela no fim e guarda a última proposta em `.cache/contas/ultima.json`.

## Phase 4: Servidor e página (US1, US2)

- [X] T012 [US1] `dash/servidor.py`, rotas só deste computador:
  - `GET /api/contas` (portais ativos, ícone, conectado, navegador achado, última leitura);
  - `POST /api/contas/<portal>/conectar` (abre a janela na página de candidaturas, que leva ao login);
  - `POST /api/contas/<portal>/pronto` (confere a sessão e marca o portal como conectado em
    `.cache/contas/estado.json`);
  - `POST /api/contas/<portal>/desconectar` (tira o portal da lista de conectados; o último portal fecha a janela e
    apaga o perfil).
- [X] T013 [US2] `dash/servidor.py`: `POST /api/candidaturas/ler`, `GET /api/candidaturas/estado` e
  `POST /api/candidaturas/aplicar`.
- [X] T014 [US1, US2] `dash/dashboard.html`:
  - botão "Atualizar candidaturas" na barra;
  - diálogo com os portais (ícone, estado, Conectar, Pronto, Desconectar);
  - "Atualizar agora" com o progresso e o aviso de login;
  - proposta agrupada por portal, com caixas de marcar e "Aplicar marcadas";
  - de outro aparelho, aviso de que só funciona neste computador.

## Phase 5: Testes, documentação e entrega

- [X] T015 [P] `tests/test_navegador.py`: quadros do WebSocket (curto, 126, 127 bytes, com e sem máscara) e `achar`
  com caminhos falsos.
- [X] T016 [P] `tests/test_contas.py`:
  - tradução da Gupy, do Indeed e do LinkedIn com os JSON e HTML fictícios;
  - `proposta` (casamento por id e por cargo + empresa, não rebaixar, encerrada final, marcado padrão, dois
    portais);
  - `aplicar` com banco temporário (anotação, `etapa_em`, triagem, vaga nova);
  - LinkedIn fora de `CONTAS`.
- [X] T017 [P] Documentação:
  - README (Contas conectadas);
  - AGENTS.md (Respeite os portais: conta conectada);
  - skills buscar-vagas (perguntas sobre o andamento) e consultar-gupy (o MCP não tem as candidaturas; a conta
    conectada tem);
  - lista de desejos (MCP oficial com login, LinkedIn, mais portais, site/demo no GitHub Pages);
  - `python sincronizar_skills.py`.
- [X] T018 Todos os testes passando; checagem de dados pessoais no diff, inclusive nos dados de teste.
- [X] T019 Commit na branch, merge na branch pessoal, reiniciar o dashboard e a pessoa testa pelo quickstart.
- [X] T020 Com o OK: merge na `master`, push, merge na branch pessoal, apagar a worktree e a branch e rodar
  `graphify update .`.
