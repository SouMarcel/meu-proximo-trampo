---
description: "Tarefas da feature 032: IA com reserva e aviso de indisponibilidade (Windows)"
---

# Tasks: IA com reserva e aviso de indisponibilidade

**Input**: spec.md, plan.md, research.md (R1–R4, D1–D7), data-model.md, contracts/ia.md, quickstart.md.

**Testes**: incluídos (fluxo da constituição). Ficam em `tests/test_ia_reserva.py`, sem rede: `ia._postar` e
`segredos.ler` trocados, e `.cache/ia-estado.json` num diretório temporário. Os testes de `tests/test_ia.py` servem de
não regressão.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Base de testes em `tests/test_ia_reserva.py`:
  - provedor simulado por URL (resposta OpenAI-like `{"choices": [{"message": {"content": "..."}}]}` ou erro HTTP
    com código);
  - `segredos.ler` com chaves fictícias por variável;
  - `ia.ARQ_ESTADO` num diretório temporário;
  - `filtros.CONFIG` temporário com a escolha de cada teste.

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 `ia.py`, validação e leitura:
  - `validar_escolha` aceita `reservas` (lista, **até 3**). Cada item passa pela mesma validação da principal e
    não pode ser "nenhum" ("Sem IA não pode ser reserva"). Não aceita repetida: mesmo provedor, modelo efetivo e
    `url_base` da principal ou de outra ("reserva repetida"). Mais de 3 → "no máximo 3 reservas";
  - `salvar_escolha` grava `reservas` (lista vazia = sem a chave) e mantém a lista gravada quando o pedido não traz
    `reservas`;
  - `escolha_efetiva` continua devolvendo só a principal;
  - `sequencia(cfg=None)`: `[]` com "nenhum"; senão a principal e as reservas, na ordem.

**Checkpoint**: `tests/test_ia.py` passa sem mudança.

## Phase 3: User Story 1 - Reserva quando a principal cai (P1) 🎯 MVP

**Goal**: com a principal falhando por motivo do provedor, a próxima da sequência responde.

**Independent Test**: principal com 503 e reserva respondendo; principal funcionando, sem chamar a reserva.

- [X] T003 [US1] `ia.py`:
  - a chamada de uma IA sai do `responder` atual para `_responder_uma(escolha, pedido, sistema, tempo, chave)`, sem
    mudar o comportamento;
  - `responder(...)` com `escolha` explícita chama `_responder_uma`;
  - sem `escolha`, percorre `sequencia()`: cada `IAErro` vira `{provedor, nome, modelo, motivo mascarado}`, e a
    próxima é tentada. A primeira que responder vence;
  - sem sequência: "a IA está desligada (Sem IA)", como hoje;
  - todas falhando: com uma IA só, o mesmo `IAErro` de hoje; com mais de uma,
    `IAErro("nenhuma IA respondeu: {nome}: {motivo}; …")`;
  - o resultado vai para um `threading.local`: `ultima()` devolve `{provedor, modelo, nome, falhas}`; `aviso_reserva()`
    devolve `"{nome principal} fora: {motivo}. Respondeu o {nome} ({modelo})."` quando a resposta veio de uma reserva,
    senão `None`; `marca()` devolve `{provedor, modelo}` de quem respondeu (+ `reserva: True` e `aviso`) ou a escolha
    efetiva sem chamada na thread.
- [X] T004 [US1] Chamadores com `ia.marca()`:
  - `candidatura_ia._marca_ia`, `analise_perfil._marca_ia` e a marca em `curriculo_ia` (`escolha = ia.escolha_efetiva()`
    no meta) passam a usar `ia.marca()`;
  - `candidatura_ia.propor_respostas` devolve `"aviso": ia.aviso_reserva()` quando a resposta veio de uma reserva.
- [X] T005 [P] [US1] Testes:
  - principal 503 e reserva ok: texto da reserva, `ultima()` com a falha, `aviso_reserva()` com o motivo,
    `marca()` da reserva (SC-001);
  - principal ok: uma chamada só e `aviso_reserva()` `None` (SC-002);
  - reserva sem chave pulada ("falta a chave") e a próxima tentada;
  - `responder(escolha=…)` sem reserva;
  - Sem IA;
  - marca separada por thread (duas threads, cada uma com o seu resultado);
  - `propor_respostas` com o aviso da reserva.

**Checkpoint**: US1 testável sozinha.

## Phase 4: User Story 2 - Aviso com o motivo (P1)

**Goal**: a pessoa vê qual IA falhou e por quê, na função e no botão IA.

**Independent Test**: todas falhando; situação gravada; alerta da principal no estado e no `/api/versao`.

- [X] T006 [US2] `ia.py`:
  - `ARQ_ESTADO = .cache/ia-estado.json`;
  - `_registrar(escolha, ok, motivo)` grava `{"provedor|modelo": {ok, em, motivo}}` a cada tentativa, inclusive no
    `testar`, sem chave e sem texto do pedido. `OSError` é ignorado;
  - `situacao()` lê o arquivo;
  - `estado_para_pagina` traz `sequencia: [{provedor, nome, modelo, gratuito, chave_ok, principal, situacao}]` e
    `alerta: {nome, modelo, motivo, em}`, este quando a situação da principal é falha.
- [X] T007 [US2] `dash/servidor.py`: `/api/versao` traz `ia_alerta` (o mesmo `alerta`). Conferir que o erro da análise
  automática (`analise.FILA.erro()`) já traz a mensagem com todas as IAs.
- [X] T008 [P] [US2] Testes:
  - todas falhando: a mensagem lista cada uma, com a chave mascarada (SC-003);
  - uma IA só: a mensagem de hoje;
  - situação gravada no sucesso e na falha, sem chave;
  - alerta presente com a principal em falha e ausente depois de um sucesso dela;
  - `/api/versao` com `ia_alerta`, pelo servidor real em porta livre, como nos testes atuais.

## Phase 5: User Story 3 - Configurar e testar a sequência (P1)

**Goal**: o painel IA monta a sequência, avisa da reserva sem chave e testa cada IA.

**Independent Test**: `PUT /api/ia` com reservas; estado com a sequência; `testar` grava a situação.

- [X] T009 [US3] `dash/servidor.py`: `PUT /api/ia` repassa `reservas` ao `salvar_escolha` (400 com a regra); `POST
  /api/ia/testar` continua com uma IA e passa a gravar a situação (via `ia.testar`).
- [X] T010 [P] [US3] Testes:
  - `PUT /api/ia` com 1 reserva → `GET /api/ia` traz a sequência com `chave_ok`;
  - 4 reservas e reserva repetida dão 400;
  - nenhuma chave no `config.json`;
  - PUT sem `reservas` mantém a lista.
- [X] T011 [US3] Front, na `frontend-react`:
  - **worktree pública** saída de `origin/frontend-react`, branch `front-032-ia-reserva`:
    - `src/services/api/ia.ts`: tipos `reservas`, `sequencia`, `alerta`;
    - `AISettingsModal.tsx`: lista de reservas (adicionar até 3, remover, subir e descer, provedor, modelo e chave como
      na principal), aviso "a reserva recebe os mesmos pedidos", situação de cada IA e "Testar a sequência", uma linha
      por IA;
    - botão IA com alerta (`ia_alerta` do `/api/versao`, em `Ferramenta.tsx` e no cabeçalho);
    - aviso da reserva onde o documento mostra a IA (`ia.aviso`);
  - `npm run build` sem erro e commit local, **sem push** antes do OK;
  - **build de teste da branch pessoal**: juntar a branch com a `frontend-react` local da 027b (`../mpt-front-027b`),
    compilar e copiar no `dash/front` da branch pessoal, sem commit (como o build da 027b).

## Phase 6: Polish & Cross-Cutting

- [X] T012 [P] `dash/API.md` §3.5 (reservas, sequência, alerta, `ia_alerta`) e a seção da IA no README (reserva e aviso).
- [ ] T013 Verificação:
  - `PY -m unittest discover -s tests` inteiro;
  - na branch pessoal de teste: configurar Gemini (`gemini-3.8-flash`) como principal e OpenRouter (`openrouter/free`)
    como reserva (SC-004), reiniciar o dashboard, testar a sequência e ver o aviso;
  - `graphify update .`.
- [ ] T014 Procurar dados pessoais nos arquivos alterados; commit; merge na branch pessoal (com a 027b), teste da pessoa;
  com o OK, master, push e o PR do front.

## Dependencies & Execution Order

- **T001** → **T002** → histórias.
- **US1 (T003–T005)** é o MVP. US2 (T006–T008) usa o `responder` de T003. US3 (T009–T011) usa T002 e T006.
- **T011** (front) só depende dos contratos e pode começar junto com T006.
- **T012** em paralelo. T013 e T014 por último.

## Parallel Opportunities

- T011 (front) e T012 (documentação), com os contratos prontos.
- Os blocos de teste (T005, T008, T010) são do mesmo arquivo: cada um vem logo depois da sua tarefa.

## Implementation Strategy

1. **MVP**: T001–T005. A reserva responde nos testes.
2. US2 (aviso e situação) → US3 (servidor e painel).
3. Documentação, configuração do usuário e teste na branch pessoal.
