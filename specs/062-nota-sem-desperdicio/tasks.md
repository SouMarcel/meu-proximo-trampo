---
description: "Tarefas da spec 062: nota sem desperdício de IA"
---

# Tasks: Nota sem desperdício de IA

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md).

**Tests**: pedidos pelo plano (funções puras com `unittest`, fila com IA falsa e `dormir` falso). Suíte:
`.venv\Scripts\python.exe -m unittest discover -s tests`.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`; as
outras ficam comigo (fila com threads e pausas, texto das regras e a calibração com os dados da pessoa).

## Format: `[ID] [P?] [D tamanho?] [Story] Description`

## Phase 1: Fundação (bloqueia US1, US2 e US3)

- [X] T001 [P] [D minor] D4 em `ia.py`: → copilot, GO na tentativa 1 (agy falhou ao iniciar)
  - `IAErro.__init__(self, mensagem, limite=False, espera=None)`, com `limite: bool = False` e
    `espera: float | None = None` como atributos (quem faz `IAErro("texto")` não muda);
  - função pura `_espera_pedida(cabecalhos, corpo) -> float | None`: `Retry-After` em segundos (número; data HTTP →
    None), senão `"retryDelay": "<n>s"` no corpo (Gemini), senão None;
  - `_postar`: no `HTTPError` 429, `IAErro(motivo_http(...), limite=True, espera=_espera_pedida(e.headers, corpo))`;
  - `_responder_uma`: o `IAErro` remascarado mantém `limite` e `espera`;
  - `responder`: cada item de `falhas` ganha `limite` e `espera`; o erro final (uma ou várias falhas) tem
    `limite=True` se alguma falha foi por limite, e `espera` a maior entre as pedidas (None se nenhuma);
  - testes em `tests/test_ia_reserva.py`: `Retry-After: 30` → 30; corpo com `"retryDelay": "36s"` → 36; nenhum →
    None; principal 429 + reserva com chave recusada → `limite=True`; duas falhas sem 429 → `limite=False`.
- [X] T002 [P] D7 e a primeira parte da D5 em `dash/analise.py`:
  - `_pausa_env(nome, padrao, minimo, maximo)` com a regra de `pausa_ia()` de hoje (vírgula aceita; fora da faixa, o
    limite mais próximo; inválido, NaN ou ausente, o padrão); `pausa_ia()` passa a usá-la ("FORCAR_PAUSA", 5, 0, 60);
  - `pausa_lote()` = `_pausa_env("ANALISE_PAUSA", 20, 5, 120)`;
  - `analisar_lote(lote, sem_descricao=frozenset()) -> (ok, problemas)`: o corpo do laço de `analisar` (um pedido,
    `lista_json`, marca da IA, provisória, `banco.aplicar_analises`); `analisar` passa a chamá-la por lote, sem mudar
    o comportamento;
  - testes em `tests/test_forcar.py`: `pausa_lote()` com 0 → 5, 200 → 120, "abc" → 20, "7,5" → 7.5, ausente → 20;
    os testes de `pausa_ia()` seguem passando.

**Checkpoint**: suíte verde; nada muda para a pessoa.

## Phase 2: User Story 1 + User Story 4 — regras enxutas e começo idêntico (P1/P3) 🎯 MVP

**Goal**: o pedido usa `regras-da-nota.md`, sem a seção Contato, com a parte fixa idêntica até `## Vagas`.

**Independent Test**: `PY calibrar_nota.py --medir` ≤ 20.000 caracteres; calibração com "SC-002: PASSA".

- [X] T003 [US1] Escrever `.agents/skills/buscar-vagas/regras-da-nota.md` pelo
  [contrato](contracts/regras-da-nota.md):
  - fonte: a linha "Formato de cada objeto" e o caso `sem_dados` de `montar_pedido` (vão para `## Resposta`), o trecho
    de "Campos" do passo 3 do Fluxo A (`` `modelo_trabalho`: `` até `4. **Gravar.**`) e `## Como dar a nota` do
    `SKILL.md`;
  - tirar o que é do chat: linha `busca:`, "comente no chat", "o dashboard mostra/filtra", comandos;
  - juntar o que se repete (a lista de campos do formato e a explicação de cada campo);
  - o que é de um portal só vai para `## Portais` → `### <PLATAFORMA>`, com o nome exatamente igual ao `PLATAFORMA` de
    `fontes/*.py` (`Gupy`, `Startup Jobs`, `Nerdin`, `InfoJobs`, `Vagas.com`, `JobGether`, `EY`, `FullStack`;
    `Indeed` se houver regra só dele);
  - "Parte fixa (tudo menos `## Portais`): no máximo 5,5 mil caracteres";
  - sem nomes, números ou regras de uma pessoa (constituição II).
- [X] T004 [US1] [US4] D2 em `dash/analise.py`:
  - `REGRAS = SKILL.parent / "regras-da-nota.md"`; `_regras() -> (fixa, portais: dict[str, str])`, lendo as seções
    por título `## ` e `### `;
  - `_sem_contato(texto)`: tira do título `## Contato` até o próximo `## ` (ou o fim); sem o título, devolve igual;
  - ordem do pedido: abertura fixa → parte fixa das regras → `## Perfil do usuário` (`_sem_contato(com_relatos(...))`)
    → `## Filtros da busca do usuário` → `## Vagas` + aviso → frase de nota sem descrição (se o grupo tiver) →
    `### <plataforma>` das plataformas do grupo, na ordem do arquivo → blocos das vagas;
  - nada de data, contagem ou id antes de `## Vagas`;
  - sem o arquivo: resumo mínimo embutido (formato do JSON e os pesos 40/30/15/15) e um aviso no log, uma vez;
  - remover `_secao` se não tiver mais uso, e o recorte da skill.
- [X] T005 [US1] [US4] Testes em `tests/test_nota_regras.py` (novo; perfil e vagas fictícios):
  - o pedido traz o texto do arquivo de regras e não traz `## Contato`, o e-mail nem o telefone do perfil;
  - perfil sem `## Contato` vai inteiro;
  - dois pedidos (vagas de portais diferentes, uma delas com `sem_descricao`) têm o texto até `## Vagas` idêntico;
  - `### Gupy` aparece só no pedido com vaga da Gupy;
  - o arquivo tem `## Resposta`, `## Campos`, `## Como dar a nota` e `## Portais`, e a parte fixa tem no máximo 5.500
    caracteres;
  - arquivo ausente (caminho trocado no teste) → pedido com o resumo mínimo;
  - ajustar `tests/test_requisitos.py:547` (procurava `**Os requisitos**`) e conferir `tests/test_integridade.py:337`
    e `tests/test_relatos.py:123`.
- [X] T006 [P] [US1] D3 em `.agents/skills/buscar-vagas/SKILL.md`:
  - passo 3 do Fluxo A: fica só o que é do chat (exceções, vaga que mira a IA, outra área) e "os campos e a nota seguem
    `regras-da-nota.md`, nesta pasta: leia o arquivo inteiro antes de avaliar";
  - `## Como dar a nota`: um parágrafo que aponta para o arquivo;
  - conferir as outras menções a "Como dar a nota" nas skills (`grep -rn "Como dar a nota" .agents`);
  - `python sincronizar_skills.py` e `python sincronizar_skills.py --conferir`.
- [ ] T007 [P] [D minor] [US1] D8: `calibrar_nota.py` na raiz, pelo [contrato](contracts/calibrar_nota.md):
  - `--medir [ID]`: partes e total, `.cache/pedido-<ID>.txt`, "SC-001: PASSA/NÃO PASSA" (≤ 20.000);
  - calibração: amostra (`--amostra 30`, `--semente`, `--ids`), pedidos de 3 com `analise.montar_pedido` e
    `ia.responder`, `ANALISE_PAUSA` (`analise.pausa_lote()`) entre pedidos, 429 com a espera de `IAErro.espera`
    (60 s sem ela, teto 300) e fim depois de 3 recusas; **nunca grava no banco**;
  - relatório no terminal e em `.cache/calibracao-AAAAMMDD-HHMM.json` (formato no `data-model.md`); códigos de saída
    0/1/2;
  - funções puras com testes em `tests/test_calibrar_nota.py`: `escolher_amostra` (faixas, áreas, preferência pelo
    modelo, sem provisórias nem sem descrição) e `resumir` (% dentro de 10, trocas de fora/dentro, passa).
- [ ] T008 [US1] Calibrar com os dados da pessoa:
  - commit na branch, merge na branch pessoal (pasta principal);
  - `PY calibrar_nota.py --medir` (sem IA);
  - **com o OK da pessoa** (gasta a cota da IA), `PY calibrar_nota.py`;
  - sem PASSA: ajustar `regras-da-nota.md` (T003) e repetir com `--ids` do relatório; com PASSA, seguir.

**Checkpoint**: US1 e US4 prontas e calibradas; o resto da spec pode seguir.

## Phase 3: User Story 3 — análise automática que não trava no limite (P1)

**Goal**: depois da busca, lotes com pausa; no 429, espera, lote menor e nova tentativa, sem perder vagas.

**Independent Test**: IA falsa com 429 no 1º lote → todas as vagas com nota na mesma rodada, sem reiniciar.

- [X] T009 [US3] D5 em `dash/analise.py` (`Fila`), depende de T001 e T002:
  - `_rodar` deixa de marcar todas as pendentes antes e chama `self._analisar_pendentes(pendentes, tentadas)`;
  - `_analisar_pendentes`: tamanhos `(10, 5, 3, 1)`, começando em 10; `lotes(faltam, tamanho)`;
    `_pausar_lote()` (`pausa_lote()` desde o último pedido da fila, não antes do primeiro) e `analisar_lote`;
  - lote respondido → os ids em `tentadas`, recusas = 0, log como hoje;
  - `IAErro` com `limite`: recusas += 1; com 3 → `ultimo_erro` e fim, sem marcar as que faltam; senão
    `self._dormir(min(e.espera or 60, 300))`, próximo tamanho e lotes refeitos com as que faltam; log
    "[análise automática] limite de uso: lote de N em S s";
  - outro `IAErro` ou exceção: como hoje (`ultimo_erro`, as pendentes da rodada em `tentadas`);
  - entre dois lotes, com forçadas na fila → sai, e o laço de fora trata as forçadas primeiro;
  - `ultimo_erro = None` só depois de uma rodada sem erro.
- [X] T010 [US3] Testes em `tests/test_forcar.py`, classe nova `TestAnaliseLimite` (IA falsa que conta os pedidos e
  os ids; `dormir` falso que registra):
  - 25 vagas → 3 pedidos (10, 10, 5), `dormir` com 20 entre eles e nunca antes do primeiro;
  - 429 no 1º pedido (sem `espera`) → `dormir(60)`, depois lotes de 5, e as 25 com nota na mesma rodada;
  - 429 com `espera=30` → `dormir(30)`; com `espera=4000` → `dormir(300)`;
  - 3 × 429 seguidos → `erro()` com o motivo, nenhuma vaga em `tentadas`; um `pedir()` depois → elas vão de novo;
  - chave recusada → um pedido só, `erro()` preenchido, sem repetir na mesma rodada;
  - forçar uma vaga durante a rodada → o pedido dela sai antes do lote seguinte.

**Checkpoint**: US3 pronta.

## Phase 4: User Story 2 — Forçar verificar em grupos de até 3 (P2)

**Goal**: a fila lê as descrições e junta até 3 vagas por pedido à IA.

**Independent Test**: forçar 6 vagas com descrição → 2 pedidos; 5 → 3 + 2.

- [X] T011 [US2] D6 em `dash/analise.py` (`Fila`), depende de T002:
  - `_preparar(vid) -> (vaga, sem_descricao) | None`: a primeira metade de `_verificar_uma` (removida ou com nota → None;
    descrição que falta → `_descricao`);
  - `self._grupo: list[str]` e `self._lendo: str | None` no lugar de `self._atual`; `verificando()` = grupo + lendo +
    fila, sem repetir; `agora()` = `_lendo` ou `_grupo[0]`; `forcar` não duplica vaga do grupo;
  - laço das forçadas: tira, prepara e junta até 3 prontas ou a fila esvaziar; então `_notar_grupo(grupo)`;
  - `_notar_grupo`: `lotes(grupo, 3)` (a vaga que mira a IA vai sozinha); por lote, `_pausar_ia()` e `analisar_lote`,
    com uma nova tentativa no `IAErro`; falha → `_falhar` em cada vaga do lote com o motivo; vaga não devolvida pela IA
    ou com problema → falha só dela (mesmos textos de hoje);
  - `_verificar_uma` some ou passa a ser `_notar_grupo([preparada])`.
- [X] T012 [US2] Testes em `tests/test_forcar.py`, classe nova `TestForcarGrupos`, e ajuste dos testes de
  `tests/test_forcar.py` e `tests/test_forcar_descricao.py` que contam um pedido por vaga ou leem `_atual`:
  - 6 vagas com descrição → 2 pedidos de 3; 5 → 3 + 2; 1 → 1 pedido, sem `dormir` extra;
  - vagas sem descrição: as leituras seguem uma por vez, com a pausa do portal, e o pedido sai depois da 3ª leitura;
  - a vaga que mira a IA vai num pedido só dela;
  - IA falha duas vezes no 1º grupo → as 3 vagas em `falhas`; o 2º grupo ganha nota;
  - `verificando()` e `agora()` durante a leitura e durante o pedido.

**Checkpoint**: US2 pronta.

## Phase 5: Fechamento

- [ ] T013 [P] D9:
  - `.env.exemplo`: `# ANALISE_PAUSA=20   # análise automática: segundos entre dois lotes à IA (5 a 120; padrão 20)`;
  - `AGENTS.md`: `ANALISE_PAUSA` junto das pausas e `PY calibrar_nota.py` (desenvolvimento) na seção de
    desenvolvimento;
  - `README.md`: a pausa nova, onde cita as pausas;
  - `docs/`: procurar menções ao recorte da skill pela análise (`grep -rn "Como dar a nota\|SKILL.md" docs`).
- [ ] T014 Suíte inteira verde, `python sincronizar_skills.py --conferir` e `graphify update .`.
- [ ] T015 Fechamento:
  - busca de dados pessoais no diff;
  - commits na branch;
  - merge na branch pessoal e dashboard reiniciado;
  - teste da pessoa: quickstart 5 (Forçar 6 vagas) e 6 (busca com muitas vagas);
  - com o OK: merge na `master`, push, `git merge master` na branch pessoal, apagar a worktree e a branch.

## Dependencies & Execution Order

- T001 e T002 em paralelo (arquivos diferentes) → bloqueiam o resto.
- Phase 2: T003 → T004 → T005; T006 e T007 em paralelo com T004/T005; T008 depois de T003 a T007.
- Phase 3 (T009 → T010) depende só da Phase 1; pode correr junto da calibração (T008), mas entra na branch depois do
  PASSA.
- Phase 4 (T011 → T012) depois da Phase 3 (as duas mexem em `Fila._rodar`).
- Phase 5 no fim.

### Parallel Example

```text
Funcionário: T001 (ia.py)        | Eu: T002 (analise.py, pausas e analisar_lote)
Funcionário: T007 (calibrar_nota) | Eu: T003 → T004 → T005, T006
```

## Implementation Strategy

1. **MVP = Phase 1 + Phase 2**: o pedido menor, sem Contato e com começo idêntico, calibrado. Já reduz cerca de 25%
   do custo de cada nota e o dado pessoal no pedido.
2. **Phase 3**: acaba com o "vagas sem nota depois da busca".
3. **Phase 4**: divide o custo do Forçar verificar.
4. Cada fase é testada na branch pessoal antes da seguinte; a `master` recebe tudo junto, com o OK da pessoa.
