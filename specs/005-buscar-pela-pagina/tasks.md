---

description: "Tarefas da feature 005: buscar vagas pela página (Windows)"
---

# Tasks: Buscar vagas pela página

**Input**: Design documents from `/specs/005-buscar-pela-pagina/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-busca.md, quickstart.md

**Tests**: `unittest` para a busca refatorada, a trava, o intervalo e o estado da busca
(constituição), com uma fonte falsa e o provedor de IA falso; o resto pelo quickstart.

**Organization**: por história (US1–US5). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US5)

---

## Phase 1: Setup

- [X] T001 Criar `tests/fonte_falsa.py`: fonte no contrato de `fontes/__init__.py` (`NOME = "falsa"`, `PLATAFORMA = "Falsa"`, `buscar(consulta, horas, por_termo)` devolvendo vagas fictícias estáveis por termo e grupo, com `id` prefixado `falsa-`, descrição, data de hoje; parâmetros de módulo para pausa por consulta, erro forçado e vagas repetidas entre termos; `descrever(vaga)` opcional contando chamadas), usada nos testes e na validação

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: a mesma busca para terminal e página, a trava entre processos e o registro da última busca.

- [X] T002 Em `vagas.py`, extrair de `cmd_buscar` a função `executar(cfg, f, nomes_fontes, por_termo, pausa=2.0, incluir_presencial=False, progresso=None, cancelado=None) -> dict` (research.md §1): o mesmo dicionário de hoje (`gerado_em`, `parametros`, `por_busca`, `brutas`, `fora_da_janela`, `excluidas_titulo`, `ja_vistas`, `outros_portais`, `erros`, `candidatas`, `fora`, mais `excluidas` para a impressão), sem imprimir; `progresso` recebe `{"etapa": "consulta", "portal", "cargo", "grupo", "feitas", "total", "encontradas"}` a cada consulta e `{"etapa": "descricoes", "lidas", "total"}` a cada descrição; `cancelado()` é olhado antes de cada consulta e de cada descrição e, se verdadeiro, levanta `Cancelada`; `ImportError` sobe para quem chama. `cmd_buscar` passa a chamar `executar` e imprimir exatamente o que imprime hoje
- [X] T003 Em `vagas.py`, `salvar_candidatas(resultado, pasta=CACHE)` (`candidatas.json` e `candidatas.md`) e `gravar_resultado(dados, avals=None, sem_avaliacao=False, status_sem_nota="sem_analise", origem="terminal") -> dict` (a lógica de `gravar` sem imprimir; devolve `{novas, existentes, fora_novas, faltando, problemas, notas, busca_id}`); `registrar_busca` ganha `origem` e `situacao: "concluida"`; `gravar(sem_avaliacao, arquivo, pasta=CACHE)` continua o comando de linha com as mesmas mensagens
- [X] T004 Em `vagas.py`, a trava (research.md §3): `class TravaBusca` (contexto) que trava `.cache/busca.trava` com `msvcrt.locking(LK_NBLCK)` no Windows e `fcntl.flock(LOCK_EX | LOCK_NB)` nos outros, levanta `BuscaOcupada` se outro processo segura; ao entrar grava `.cache/busca.json` `{origem, inicio, situacao: "rodando", pid}` (atômico) e ao sair `{…, situacao, fim}` (`concluida`, `falha`, `cancelada`); `ultima() -> dict | None` lê `busca.json` e devolve `situacao: "interrompida"` quando diz `rodando` e a trava está livre; `ocupada() -> dict | None` (quem busca agora). `cmd_buscar` roda dentro de `TravaBusca("terminal")`; se a trava for da página, sai com código 4 e "Há uma busca rodando pela página do dashboard (desde HH:MM). Espere ela terminar ou cancele por lá." (se for de outro terminal, mensagem equivalente)
- [X] T005 [P] Testes de T002–T004 em `tests/test_busca.py`, com `vagas.FONTES` trocado pela fonte falsa e `CACHE`/banco temporários: eventos de progresso na ordem e com totais certos; cancelar no meio levanta `Cancelada`, para antes da consulta seguinte e não grava nada; resultado e mensagens do `cmd_buscar` iguais ao comportamento anterior (contagens de repetidas, fora da janela, cortadas pelo título); `gravar_resultado` com `sem_analise` e com `pendente`; registro com `origem`; trava: um subprocesso segura e o outro recebe `BuscaOcupada`, e depois que o subprocesso morre a trava fica livre; `ultima()` mostra `interrompida`

**Checkpoint**: terminal igual a antes, com trava e registro; testes passando

---

## Phase 3: User Story 1 - Buscar vagas com um clique (Priority: P1) 🎯 MVP

**Goal**: botão Buscar vagas, confirmação com o plano, andamento e resumo, sem terminal.

**Independent Test**: quickstart.md cenários 3, 4, 11 e 14.

- [X] T006 [US1] Criar `dash/buscador.py`: classe `Busca` (molde de `analise.Fila`) com estado em memória protegido por trava (data-model.md), `plano()` (consultas por `filtros.consultas`, portais do `config.json`, cargos, janela, `estimativa_min` = consultas × 8 s, IA por `ia.escolha_efetiva`/`disponivel` com nome, modelo e cobrança, `filtros_ok`, `perfil_ok`), `estado()`, `iniciar(sem_nota=False, confirmar_recente=False)` e a linha de execução `_rodar`: `TravaBusca("pagina")` → `vagas.executar(progresso=…, cancelado=evento.is_set)` → `salvar_candidatas(pasta=.cache/pagina)` → `gravar_resultado(origem="pagina")` → `resumo` (`brutas, novas, fora_criterios, ja_vistas, excluidas_titulo, fora_da_janela, busca_id`) e `erros` (até 20); `ImportError` → `falha` com "Falta uma biblioteca da busca: rode python iniciar.py"; outros erros → `falha` com mensagem genérica (detalhe só no terminal do servidor)
- [X] T007 [US1] Em `dash/servidor.py`: `GET /api/busca/plano`, `GET /api/busca` (com `pode_alterar` = `_local()`), `POST /api/busca` (`202`; `409 {"erro", "estado"}` quando já há busca) e `GET /api/versao` com `busca: {situacao, origem}`; instância única `buscador.BUSCA`; escrita só do próprio computador (`403` com a mensagem do contrato)
- [X] T008 [US1] Em `dash/dashboard.html`: botão **Buscar vagas** em `rel-acoes`, ao lado de Filtros da busca; diálogo `dlg-busca` com o plano (consultas, portais, cargos, janela, "cerca de N minutos", IA e aviso de cobrança por uso) e Confirmar; painel de andamento no topo do relatório (portal e cargo da consulta atual, "consulta n de N", vagas encontradas, "lendo descrições n de N", "gravando…"); consulta a `/api/busca` a cada 2 s enquanto a situação não é final (e ao abrir a página, se `/api/versao` disser que há busca); no fim, recarrega as vagas e mostra o resumo (encontradas, novas para decidir, fora dos critérios, já vistas, cortadas pelo título, fora da janela, erros dos portais), com Fechar; pela rede, botão indisponível com a explicação
- [X] T009 [US1] Validar US1 pelo quickstart.md cenários 3, 4, 11 e 14 (servidor no roteiro, porta 8799, fonte falsa)

**Checkpoint**: busca pela página do começo ao fim, sem IA

---

## Phase 4: User Story 2 - Nota das vagas novas pela IA escolhida (Priority: P1)

**Goal**: com IA e perfil, as vagas novas recebem nota pela análise automática; sem IA, nada sai.

**Independent Test**: quickstart.md cenários 5 e 6.

- [X] T010 [US2] Em `dash/buscador.py`: `com_nota` = IA disponível e perfil gravado e não `sem_nota`; com nota, `gravar_resultado(status_sem_nota="pendente")` e `analise.FILA.pedir()`; sem nota, `sem_analise`; `estado()["analise"] = {rodando: FILA.rodando, faltam: vagas com analise.precisa, erro: FILA.erro()}`; em `dash/servidor.py`, `POST /api/busca/analisar` (só local) que chama `FILA.pedir()` e devolve `{analise}`
- [X] T011 [US2] Em `dash/dashboard.html`: depois da gravação, "IA analisando: faltam N" até zerar; sem nota, o resumo diz "gravadas sem nota" com o caminho (botão IA ou pedir a análise no chat); falha da IA: o motivo e o botão **Tentar a nota de novo** (`POST /api/busca/analisar`)
- [X] T012 [P] [US2] Testes em `tests/test_busca.py`: com IA (provedor falso) e perfil, vagas novas `pendente` e fora dos critérios `sem_analise`; sem IA, `sem_analise` e o provedor falso sem nenhum pedido; sem perfil, `sem_analise`
- [X] T013 [US2] Validar US2 pelo quickstart.md cenários 5 e 6

---

## Phase 5: User Story 3 - Orientação antes da primeira busca (Priority: P2)

**Goal**: sem cargos, leva aos Filtros; sem perfil, Meu perfil ou buscar sem nota.

**Independent Test**: quickstart.md cenários 1 e 2.

- [X] T014 [US3] `POST /api/busca` sem cargos → `400` ("Escolha os cargos em Filtros da busca antes de buscar."); em `dash/dashboard.html`, sem `filtros_ok` o botão abre o painel Filtros da busca; sem `perfil_ok`, o diálogo explica que a nota depende do perfil e oferece **Montar meu perfil** (abre Meu perfil) ou **Buscar sem nota** (`sem_nota: true`)
- [X] T015 [US3] Validar US3 pelo quickstart.md cenários 1 e 2

---

## Phase 6: User Story 4 - Cancelar e respeitar os portais (Priority: P2)

**Goal**: cancelar sem gravar nada; intervalo mínimo e aviso de busca recente.

**Independent Test**: quickstart.md cenários 7 e 8.

- [X] T016 [US4] Em `dash/buscador.py`: `cancelar()` (evento; situação `cancelando` → `cancelada`, nada gravado, `busca.json` com `cancelada`); intervalo (research.md §4): `INTERVALO_MINIMO = 30 min` e `AVISO_RECENTE = 6 h` a partir de `vagas.ultima()` só com `concluida` ou `falha` (sem `busca.json`, a data da última busca do banco); `plano()` com `ultima`, `proxima_em` e `recente`; `iniciar` → `409` antes do mínimo (com `proxima_em`) e com `recente` sem `confirmar_recente`; todos os portais com erro e nenhuma vaga → `falha` ("Os portais não responderam; provável bloqueio temporário. Espere antes de tentar de novo."), nada gravado, conta para o intervalo; em `dash/servidor.py`, `DELETE /api/busca` (só local)
- [X] T017 [US4] Em `dash/dashboard.html`: botão **Cancelar** no painel de andamento ("cancelando: termina a consulta atual…"); com `proxima_em`, o botão Buscar vagas fica indisponível com "Você pode buscar de novo a partir das HH:MM"; com `recente`, o diálogo avisa que os portais devem ter pouca novidade e o Confirmar manda `confirmar_recente`; resumo com os erros por portal e, se houve erro, a sugestão de esperar
- [X] T018 [P] [US4] Testes em `tests/test_busca.py`: intervalo (concluída há 10 min bloqueia; há 2 h avisa; há 7 h livre; cancelada e interrompida não contam; falha conta; sem `busca.json`, vale o banco) e cancelamento pela `Busca` (situação final `cancelada`, banco sem vaga nova)
- [X] T019 [US4] Validar US4 pelo quickstart.md cenários 7 e 8

---

## Phase 7: User Story 5 - Uma busca por vez, com o terminal e o chat (Priority: P2)

**Goal**: página e terminal nunca buscam juntos; as candidatas do chat ficam intactas.

**Independent Test**: quickstart.md cenários 9, 10, 12 e 13.

- [X] T020 [US5] Em `dash/buscador.py` e `dash/servidor.py`: `iniciar` com a trava de outro processo → `409` ("Há uma busca rodando no terminal ou no chat desde HH:MM."); `estado()` sem busca da página mostra `vagas.ocupada()` (origem `terminal`) e, ao subir o servidor, a `interrompida` do `vagas.ultima()`; a página mostra "busca em andamento no terminal" sem deixar iniciar e recarrega o relatório quando ela termina
- [X] T021 [P] [US5] Em `.agents/skills/buscar-vagas/SKILL.md`: a busca também pode ser feita pela página (botão Buscar vagas) e, se o comando sair com código 4, há uma busca pela página: dizer isso à pessoa e esperar, sem tentar de novo em seguida; rodar `python sincronizar_skills.py`
- [X] T022 [US5] Validar US5 pelo quickstart.md cenários 9, 10, 12 e 13

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T023 [P] `README.md` (Uso sem IA: buscar pela página; uma busca por vez; intervalo de 30 min e aviso de 6 h; com IA, a nota chega em seguida) e `dash/README.md` (rotas `/api/busca…` e `buscador.py`)
- [X] T024 Rodar `python -m unittest discover -s tests` e o quickstart.md inteiro; registrar os resultados no `quickstart.md`
- [X] T025 Com o OK do usuário, a busca real pequena do cenário 16 (um cargo, um portal) com config e banco temporários
- [X] T026 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T005) → histórias.
- **US1 (T006–T009)** é a base da página; **US2 (T010–T013)**, **US3 (T014–T015)**, **US4
  (T016–T019)** e **US5 (T020–T022)** dependem dela e mexem nos mesmos arquivos
  (`dash/buscador.py`, `dash/servidor.py`, `dash/dashboard.html`), então seguem em sequência.
- Polish por último; T025 e T026 só com o OK do usuário.

## Parallel Opportunities

- Testes (T005, T012, T018) em arquivo próprio, junto com as funções.
- T021 (skill) e T023 (README) a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → buscar pela página sem IA, com o mesmo resultado do
   terminal.
2. US2 (nota) e US3 (orientação).
3. US4 (cancelar e intervalo) e US5 (terminal e chat).
4. Validação completa, busca real opcional e commit com OK.
