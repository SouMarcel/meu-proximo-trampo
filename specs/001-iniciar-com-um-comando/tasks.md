---

description: "Tarefas da feature 001: iniciar a ferramenta com um comando (Windows)"
---

# Tasks: Iniciar a ferramenta com um comando

**Input**: Design documents from `/specs/001-iniciar-com-um-comando/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/comando-iniciar.md,
quickstart.md

**Tests**: incluídos para as funções puras do `iniciar.py`, porque a constituição exige `unittest`
em função pura nova ("Fluxo de desenvolvimento"). O resto é validado pelo quickstart.

**Organization**: tarefas agrupadas por história (US1, US2, US3) para entregar e testar cada uma.

**Plataforma**: só Windows 10/11 (macOS e Linux em `specs/lista-de-desejos.md`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1, US2, US3)

## Path Conventions

Projeto único na raiz: `iniciar.py`, `iniciar.bat`, `tests/`, `dash/`, `README.md`. Trabalho na
`master` por worktree (constituição).

---

## Phase 1: Setup

**Purpose**: esqueleto dos arquivos novos

- [ ] T001 Criar `iniciar.py` na raiz com docstring de uso (`python iniciar.py [--sim] [--sem-navegador] [--rede] [--porta N]`), constantes `RAIZ = Path(__file__).resolve().parent`, `VENV = RAIZ / ".venv"`, `CARIMBO = VENV / ".requisitos-instalados"`, `REQUISITOS = RAIZ / "requirements.txt"`, `PORTA_PADRAO = 8765`, `VERSAO_MINIMA = (3, 10)`, `main()` vazia com `sys.exit(main())`, e `sys.stdout/stderr.reconfigure(encoding="utf-8")` como em `vagas.py`. Sintaxe aceita desde o Python 3.6: sem `match`, sem `:=`, sem anotações `X | Y` (research.md §6)
- [ ] T002 [P] Criar `tests/test_iniciar.py` com `unittest`, importando `iniciar` a partir da raiz (`sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`) e uma classe de teste vazia por grupo de função (requisitos, versões, ambiente, opções)

---

## Phase 2: Foundational (pré-requisitos das histórias)

**Purpose**: funções puras do `iniciar.py` que US1 e US2 usam

**⚠️ CRITICAL**: nenhuma história começa antes desta fase

- [ ] T003 Implementar `ler_requisitos(caminho)` em `iniciar.py`: devolve lista de `(nome, versao_minima_ou_None, linha)` para linhas `nome` e `nome>=x.y[.z]` do `requirements.txt`; ignora vazias e comentários; qualquer outro especificador (`==`, `~=`, `<`, extras, marcadores) volta com `versao_minima="?"` para ser tratado como "faltando" (research.md §2)
- [ ] T004 Implementar `versao_ok(instalada, minima)` em `iniciar.py`: compara só as partes numéricas iniciais como tuplas (`"1.2.0"` ≥ `"1.2"`); `minima` `None` → `True`; `"?"` → `False`
- [ ] T005 Implementar `python_do_venv(venv)` em `iniciar.py`: `venv / "Scripts" / "python.exe"` no Windows, senão `venv / "bin" / "python"` (custa uma linha; só o Windows é verificado)
- [ ] T006 Implementar `hash_requisitos(caminho)` (SHA-256 do conteúdo), `ler_carimbo(caminho)` e `gravar_carimbo(caminho, hash)` em `iniciar.py`; o carimbo é JSON `{"requisitos_sha256": "<hash>", "python": "3.x.y"}` (data-model.md) e só é gravado depois de instalação ou verificação bem-sucedida
- [ ] T007 Implementar `estado_ambiente(raiz)` em `iniciar.py` devolvendo `"ausente"` (sem `.venv/`), `"invalido"` (executável ausente ou `home` do `.venv/pyvenv.cfg` apontando para pasta inexistente), `"sem_carimbo"`, `"desatualizado"` (carimbo diferente do hash atual) ou `"pronto"` (carimbo bate) — sem rodar processo e sem rede (data-model.md, research.md §3)
- [ ] T008 Implementar `ler_opcoes(argv)` em `iniciar.py` com `argparse` e ajuda em português: `--sim`, `--sem-navegador`, `--rede`, `--porta N` (inteiro); devolve as opções e a lista de argumentos a repassar ao servidor (`--sem-navegador`, `--rede`, `--porta N`) (contracts/comando-iniciar.md)
- [ ] T009 [P] Escrever em `tests/test_iniciar.py` os testes de T003–T008: requisitos com `>=`, nome solto, comentário e especificador não suportado; `versao_ok` com tamanhos diferentes; `estado_ambiente` com `.venv` falso em `tempfile.TemporaryDirectory` (sem pasta, executável ausente, `home` inexistente, sem carimbo, carimbo velho, carimbo certo); `ler_opcoes` com e sem `--porta`

**Checkpoint**: `python -m unittest discover -s tests` passa

---

## Phase 3: User Story 1 - Primeira vez: clonar e abrir com um comando (Priority: P1) 🎯 MVP

**Goal**: num clone limpo, um comando confere a versão, explica e pede confirmação, cria o
`.venv`, instala, sobe a ferramenta e abre a página; a página avisa o próximo passo se não há
configuração.

**Independent Test**: quickstart.md cenários 1, 2, 10 e 11 num clone limpo em pasta temporária.

- [ ] T010 [US1] Implementar `checar_versao()` em `iniciar.py`, chamada no início de `main()`: abaixo de `VERSAO_MINIMA` imprime "Precisa do Python 3.10 ou mais novo (você tem X.Y). Baixe em https://www.python.org/downloads/" e devolve 2 (FR-002)
- [ ] T011 [US1] Implementar `perguntar(texto, sim)` em `iniciar.py`: com `sim` devolve `True` sem perguntar; senão mostra `texto [S/n]`, Enter vazio ou S/s = sim, N/n = não; `EOFError` (sem terminal) = não (FR-003, FR-011)
- [ ] T012 [US1] Implementar `criar_ambiente(venv, recriar)` em `iniciar.py` com `venv.EnvBuilder(with_pip=True, clear=recriar)`; em falha, mensagem em português com a causa provável e "rode o comando de novo" e código 1 (FR-005)
- [ ] T013 [US1] Implementar `instalar(python_venv)` em `iniciar.py`: `subprocess.run([python_venv, "-m", "pip", "install", "-r", str(REQUISITOS), "--disable-pip-version-check", "--no-cache-dir"], cwd=RAIZ)` com a saída visível (andamento); sucesso → `gravar_carimbo`; falha → "Não deu para instalar. Confira a internet e rode o comando de novo." e código 1 (FR-004, FR-005, research.md §1)
- [ ] T014 [US1] Implementar `iniciar_servidor(python_venv, repassar)` em `iniciar.py`: se `sys.prefix` já é o `.venv`, insere `RAIZ/"dash"` no `sys.path`, ajusta `sys.argv` e chama `servidor.main()`; senão `subprocess.run([python_venv, str(RAIZ/"dash"/"servidor.py"), *repassar], cwd=RAIZ)`; `KeyboardInterrupt` no pai só espera o filho terminar; devolve o código do servidor (FR-006, FR-012, research.md §4)
- [ ] T015 [US1] Montar o fluxo de primeira vez em `main()` de `iniciar.py`: `checar_versao` → `ler_opcoes` → `estado_ambiente`; para `ausente`/`invalido` explica o que fará ("Vou preparar a ferramenta nesta pasta (.venv): criar o ambiente e instalar as dependências."; para `invalido`, "O ambiente atual não funciona neste computador e será recriado.") → `perguntar` → recusa: explica os passos manuais (`py -m venv .venv`, `.venv\Scripts\python -m pip install -r requirements.txt`) e devolve 3 → `criar_ambiente` → `instalar` → `iniciar_servidor`. Não lê nem escreve `config.json`, `perfil.md` ou `dash/dados/` (FR-009, contracts/comando-iniciar.md)
- [ ] T016 [P] [US1] Em `dash/dashboard.html`, no `carregar()` (~linha 1216) consultar uma vez `API.get("/api/config")` e guardar `existe` no estado `S`; em `renderRelatorio()` (~linha 737), com `existe === false`, mostrar no topo do Relatório de Vagas o aviso "Antes da primeira busca, escolha os cargos e o local em Filtros da busca." com um botão `data-abrir-filtros` (o mesmo atributo do botão atual, linha ~755); com `existe === true`, nada muda (contracts/comando-iniciar.md, "Página")
- [ ] T017 [US1] Validar US1 pelo quickstart.md cenários 1, 2, 10 e 11 num clone limpo em pasta temporária, comparando a lista de arquivos fora de `.venv/` antes e depois (SC-001, SC-005)

**Checkpoint**: clone limpo → um comando → página aberta com o aviso; recusa não instala nada

---

## Phase 4: User Story 2 - Uso do dia a dia (Priority: P1)

**Goal**: com o ambiente pronto, abre em segundos sem perguntas nem rede; ferramenta já aberta só
mostra a página; dependência nova é instalada com confirmação; ambiente antigo é reaproveitado.

**Independent Test**: quickstart.md cenários 3, 4, 5, 6, 7, 8 e 12.

- [ ] T018 [US2] Implementar `ja_rodando(porta)` em `iniciar.py` com `urllib.request` (timeout 2 s): `GET http://127.0.0.1:<porta>/api/versao` com 200 e campo `versao`; em `main()`, logo depois de `checar_versao`, se rodando: imprime o endereço, abre com `webbrowser.open` (salvo `--sem-navegador`) e devolve 0 sem olhar o ambiente (FR-007, SC-003, research.md §5)
- [ ] T019 [US2] Implementar `verificar_instalado(python_venv, requisitos)` em `iniciar.py`: roda uma vez o Python do `.venv` com `-c` e um verificador por `importlib.metadata.version(nome)` que imprime JSON `{nome: versao_ou_null}`; compara com `versao_ok`; tudo ok → `gravar_carimbo` e segue sem instalar (ambiente do jeito antigo); senão devolve a lista do que falta (research.md §2)
- [ ] T020 [US2] Completar `main()` em `iniciar.py` para os estados `sem_carimbo` e `desatualizado`: `sem_carimbo` → `verificar_instalado`; faltando algo (ou `desatualizado`) → "A ferramenta precisa de: <lista>." → `perguntar` → `instalar` → `iniciar_servidor`; `pronto` → `iniciar_servidor` direto, sem pergunta e sem rede (FR-008, SC-002)
- [ ] T021 [US2] Validar US2 pelo quickstart.md cenários 3, 4, 5, 6, 7, 8 e 12 (desligar a internet no cenário 3; conferir no Gerenciador de Tarefas que nenhum `servidor.py` sobra no cenário 7)

**Checkpoint**: dia a dia em até 10 s; segunda execução com a ferramenta aberta só mostra a página

---

## Phase 5: User Story 3 - Atalho de duplo clique (Priority: P3)

**Goal**: dois cliques em `iniciar.bat` fazem o mesmo que o comando, com a janela visível em erro.

**Independent Test**: quickstart.md cenário 9.

- [ ] T022 [P] [US3] Criar `iniciar.bat` na raiz: `@echo off`, `chcp 65001 >nul`, `cd /d "%~dp0"`; escolher o Python testando `py -3 --version` e depois `python --version` (o segundo pode ser o atalho da Microsoft Store, por isso testa a execução e não só a existência); sem Python → mensagem com https://www.python.org/downloads/, `pause`, `exit /b 2`; rodar `<python> iniciar.py %*` na mesma janela; se `errorlevel` diferente de 0 → `pause`; `exit /b` com o código (FR-013, research.md §7)
- [ ] T023 [US3] Validar US3 pelo quickstart.md cenário 9 (dois cliques com o ambiente pronto, e com um erro forçado, ex. porta ocupada, para ver a janela parar no `pause`)

**Checkpoint**: atalho equivalente ao comando

---

## Phase 6: Polish & Cross-Cutting

- [ ] T024 [P] Reescrever a seção "Instalação" do `README.md`: pré-requisitos (Python 3.10+ e Git), `git clone` + `cd` + `python iniciar.py` (ou `py iniciar.py`, ou dois cliques em `iniciar.bat`), o que o comando faz e pergunta, como parar (Ctrl+C ou fechar a janela) e as opções; mover os passos manuais (venv, pip, cópia do config) para "Instalação manual (alternativa)" e manter citadas a tarefa do VS Code, o Live Server e o `dash/abrir-dashboard.bat`; dizer que o foco é Windows (macOS e Linux pelos passos manuais) (FR-014)
- [ ] T025 Rodar `python -m unittest discover -s tests` e o quickstart.md completo no Windows; marcar no `quickstart.md` o resultado de cada cenário
- [ ] T026 Busca de dados pessoais no diff, mostrar o resultado ao usuário e, com o OK dele, commit na `master`, push e merge na branch pessoal (constituição, "Fluxo de desenvolvimento")

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003–T009)** → histórias.
- **US1 (T010–T017)** depende da Foundational. É o MVP.
- **US2 (T018–T021)** depende da US1 (reusa `perguntar`, `instalar` e `iniciar_servidor`);
  `ja_rodando` (T018) pode ser feito junto da US1.
- **US3 (T022–T023)** depende só de o `iniciar.py` existir e rodar (fim da US1).
- **Polish (T024–T026)** depois das histórias; T026 por último.

## Parallel Opportunities

- T002 em paralelo com T001 (arquivos diferentes).
- T009 (testes) em paralelo com o fim das funções da Foundational, arquivo à parte.
- T016 (`dashboard.html`) em paralelo com T010–T015 (`iniciar.py`).
- T022 (`iniciar.bat`) e T024 (`README.md`) em paralelo entre si, depois da US1.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → validar (T017) → já resolve a primeira instalação.
2. **US2** em seguida (também P1): uso diário rápido e ambiente antigo reaproveitado.
3. **US3** e README.
4. Validação completa (T025) e commit com OK (T026).
