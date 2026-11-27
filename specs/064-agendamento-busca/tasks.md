---
description: "Tarefas da spec 064: Busca agendada e retomada depois da espera"
---

# Tasks: Busca agendada e retomada depois da espera

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md).

**Tests**: pedidos pela spec (testes independentes com relógio falso e portal falso que bloqueia na 3ª consulta).
Suíte: `.venv\Scripts\python.exe -m unittest discover -s tests`. Front: `npx -y pnpm@10.34.3 exec tsc --noEmit` e
`npx -y pnpm@10.34.3 exec vite build --base ./` na `frontend-react` (worktree `../mpt-front-027b`).

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.

## Format: `[ID] [P?] [D tamanho?] [Story] Description`

## Phase 1: Base (bloqueia as histórias)

- [X] T001 [P] [D minor] → copilot, GO na tentativa 1. Espera no `.env` (FR-012, research R8): em `fontes/_comum.py`, `espera_do_env(var, padrao=360,
  minimo=60, maximo=2880) -> {"duracao": timedelta, "definida": bool, "ajuste": str}` no molde de `pausa_do_env`
  (aceita vírgula; "60 a 2880" minutos; fora da faixa vira o limite com aviso; inválido usa o padrão com aviso). Em
  `fontes/linkedin.py`, `infojobs.py`, `vagascom.py`, `jobgether.py`, `fullstack.py` e `mygreenhouse.py`: `VAR_ESPERA =
  "<PORTAL>_ESPERA"` e `duracao_espera()` lida a cada uso, no lugar da constante `ESPERA` em `espera()` e `_bloquear()`.
  Padrão 360 para todos. Novo `tests/test_espera_env.py`; ajustar os testes dos portais que usam `ESPERA`.
- [X] T002 [P] [D minor] → agy, GO na tentativa 1. Em `vagas.py` (research R3, R5, R7; data-model "Resultado do executar" e "Histórico de buscas"):
  (a) `executar(..., so_consultas: dict[str, list[dict]] | None = None)`: com o parâmetro, só os portais da chave
  rodam, e só essas consultas (lista vazia: nenhuma consulta, vai direto às descrições pendentes do portal);
  (b) `resultado["faltaram"] = {nome: [consultas]}`: para portal com `parada()`, a consulta em que ele parou e as
  seguintes dele, mais `resultado["rodaram"]` e `resultado["bloqueados"]`; (c) `TravaBusca.__exit__` acrescenta `{origem, inicio, fim, situacao}` a
  `.cache/buscas-historico.json` (últimas 20) e `ler_historico()`. Testes em `tests/test_agendamento.py` com um portal
  falso que bloqueia na 3ª consulta.
- [X] T003 [P] [US1] `filtros.py` (data-model "Agendamento"): `agendamento_padrao()` (`ligado` false, `horario`
  "08:00", `continuar` false), `_agendamento_cfg` tolerante, `validar_agendamento` ("HH:MM", 00:00 a 23:59; erro
  "horário inválido: use HH:MM"), `salvar_agendamento` (grava só a chave, como `salvar_limpeza`) e `efetivos()` com
  `agendamento`. Testes em `tests/test_agendamento.py`. (feita por mim: pequena)

## Phase 2: US1 Busca diária no horário escolhido (P1)

**Teste independente**: relógio falso no horário → a busca agendada começa uma vez; 07:30 manual concluída → pulada.

- [X] T004 [D minor] [US1] → agy, GO na tentativa 1. Novo `agendamento.py` (raiz), regras puras com `agora` injetável (research R2, R3; data-model
  "Execução do relógio"): `decidir_agendada(cfg_agendamento, agora, estado, historico_buscas) -> ("rodar" | "pulada" |
  "perdida" | "esperar" | None, motivo)` (janela H a H + 15 min; data de hoje já em `estado["dia"]` → None; manual
  `pagina`/`terminal`/`chat` concluída ou rodando com início entre H − 4 h e H → "pulada" com "busca manual às HH:MM");
  `proxima_agendada(cfg, agora, estado)`; leitura e gravação atômica de `.cache/agendamento.json` (`dia`, `historico`
  com os 30 últimos eventos). Testes em `tests/test_agendamento.py` (US1-1, US1-2, US1-3, US1-5, mudança de horário no
  mesmo dia).
- [X] T005 [D minor] [US1] → copilot, GO na tentativa 1. `dash/buscador.py`: `Busca.iniciar(..., origem="pagina", retomada=None)`; com origem
  `agendada` ou `retomada`: sem confirmação de recente nem de espera, sem intervalo mínimo, portal em espera fica de fora
  com aviso nos erros, roda fora de `_sessao.na_pagina` (portais com login de fora, com aviso), `TravaBusca(origem)` e
  `gravar_resultado(origem=...)`. Novo `dash/agendador.py`: classe `Agendador` com thread daemon, `tick(agora)` a cada
  30 s (`threading.Event.wait`), que usa `agendamento.decidir_agendada` e só inicia com nada rodando (`BUSCA`,
  `vagas.ocupada()`, `COMPLETAR`, `vagas._LEITURA`; senão fica "devida" e tenta no próximo tick), e grava o evento.
  `dash/servidor.py`: `AGENDADOR.iniciar()` no `main()`. Testes do `tick` com relógio e busca falsos.

## Phase 3: US2 Continuar de onde parou (P1)

**Teste independente**: portal falso bloqueia na 3ª consulta; 6 h depois (relógio falso) a retomada roda só as que
faltaram e as descrições pendentes; sem novo bloqueio, a retomada some.

- [X] T006 [D minor] [US2] → agy, GO na tentativa 1 (corrigi perdida com portal em espera e data quebrada). Em `agendamento.py` (research R6; data-model "Retomada" e transições): `.cache/retomadas.json`
  (ler, gravar atômico, `cancelar(nome)`, `apagar_todas()`); `depois_da_busca(resultado, origem, agora, continuar)`
  (agendada apaga todas antes; portal que rodou e bloqueou cria ou atualiza com `proxima = agora + 6 h`, `tentativas +
  1` se origem `retomada`, `criada_em` mantido; portal que rodou sem bloquear: apaga se não houver pendente dele, senão
  fica com `faltaram` vazio e + 6 h); `retomadas_devidas(agora, cfg_agendamento, em_espera)` com perdida (mais de 15
  min no passado, avança de 6 em 6 h até o futuro), pulada (portal em espera, + 6 h), teto de 24 h sem agendamento
  ligado. Testes (US2-3, US2-4, US2-6, perdida, pulada, 24 h, caixa desmarcada).
- [X] T007 [D minor] [US2] → copilot, GO na tentativa 1. Integração: `dash/buscador.py` chama `agendamento.depois_da_busca` no fim de toda busca
  (também na falha por bloqueio provável, com `faltaram` = todas as consultas do portal); origem `retomada` roda
  `executar(so_consultas={nome: faltaram})` e pede a análise (FR-008); `dash/agendador.py` roda as retomadas devidas e
  registra perdida e pulada; `vagas.py cmd_buscar` chama `depois_da_busca(origem="terminal")` e avisa "LinkedIn
  bloqueou; com o dashboard ligado, a retomada roda às HH:MM". O resumo da busca ganha `bloqueados` e `retomada_as`.
  Teste de ponta a ponta com o portal falso (US2-1, US2-2).

## Phase 4: US3 Ver o que está agendado e o que aconteceu (P2)

- [X] T008 [D minor] [US3] → agy, GO na tentativa 1. `dash/servidor.py`: `GET /api/agendamento`, `PUT /api/agendamento` (local; desmarcar
  `continuar` apaga as retomadas), `DELETE /api/agendamento/retomadas/<nome>` (local; 404 sem retomada), no formato de
  contracts/api.md (`hoje`, `proxima`, `retomadas` com `consultas` e `descricoes` contadas pelo banco, `historico` até
  10, `aviso_login`); `GET /api/busca` com `origem` e `retomada`. `vagas.py agendamento` com `--ligar HH:MM`,
  `--desligar`, `--continuar sim|nao`, `--cancelar-retomada <nome>` (horário inválido: código 2). Teste de rota com
  servidor de verdade em porta livre.
- [X] T009 [D minor] [US1] [US3] → copilot, GO na tentativa 1 (ajustei os textos de devida e bloqueou). Front (`frontend-react`): `src/services/api/agendamento.ts` (tipos e chamadas),
  `src/components/modals/AgendamentoAba.tsx` (novo, aba "Agendamento" no `SearchFiltersModal.tsx`, no molde da
  `LimpezaAba.tsx`: ligar, horário, "Continuar de onde parou", texto "roda só com o dashboard ligado; portais com login
  ficam de fora"), `src/components/AgendamentoStatus.tsx` (novo: próxima busca, hoje, retomadas com Cancelar, último
  evento) junto do Buscar vagas, e `AndamentoBusca.tsx` com "Busca agendada" / "Retomada do LinkedIn" pela `origem`.

## Phase 5: Fechamento

- [ ] T010 Documentação: `dash/API.md` (3.3b e origem no estado da busca), `README.md` (agendamento, retomada, esperas
  no `.env`, fim das "24 horas"), `AGENTS.md`, `.env.exemplo` (as seis `<PORTAL>_ESPERA`), docstring do `vagas.py`
  (FR-011).
- [ ] T011 Validação: suíte inteira, typecheck e build do front, merge na branch pessoal, front copiado para
  `dash/front/` sem commit, dashboard reiniciado; quickstart passos 2 a 5 pela pessoa.

## Dependências

T001, T002 e T003 em paralelo (arquivos diferentes). T004 depois de T003. T005 depois de T002 e T004. T006 depois de
T004 (mesmo arquivo). T007 depois de T005 e T006. T008 depois de T007. T009 depende só do contrato (pode rodar junto de
T005 a T008). T010 depois de T008. T011 no fim.

**MVP**: Phase 1 + US1 (T001 a T005) já dão a busca diária; US2 traz a retomada; US3 e o front, a visão na página.
