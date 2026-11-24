---
description: "Tarefas da spec 054: limpeza de vagas antigas"
---

# Tasks: Limpeza de vagas antigas

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: cada tarefa de código traz os próprios testes em `tests/test_limpeza.py`
(`python -m unittest discover -s tests`), com vagas fictícias. O banco e o config ficam numa pasta temporária (patch
de `banco.ARQUIVO`, `banco.BACKUPS` e `filtros.CONFIG`, como em `tests/test_integridade.py:245`).

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T0NN.md`.

- As de back e documentação rodam na worktree `../mpt-054`.
- As de front rodam na worktree do front, `../mpt-front-027b`, branch `frontend-react`, e são validadas com
  typecheck e build.
- O resto fica comigo, porque é a regra da feature.

## Format: `[ID] [P?] [D tamanho?] [Story] Description`

---

## Phase 1: Base (eu) — bloqueia as outras

- [X] T001 Em `filtros.py` e `config.exemplo.json`, a chave `limpeza` do D1:
  - `LIMPEZA_PADRAO`, `_limpeza_cfg` em `efetivos()`, `validar_limpeza(e)` e `salvar_limpeza(entrada)`;
  - `validar()` só aplica a chave quando o painel a manda.

  Validação: `dias` inteiro de 1 a 365; `nota_abaixo_de` null ou inteiro de 1 a 100; `resultados` só de
  `nao_aprovado`, `desisti`, `cancelada`, `sem_resposta` e `sem_resultado`.

  Testes:
  - os padrões sem a chave;
  - valores inválidos recusados;
  - `validar()` sem `limpeza` mantém o que está gravado;
  - `salvar_limpeza` sem `termos`.
- [X] T002 Em `dash/banco.py`, os itens D2, D3, D6 e D9:
  - `"sem_resposta"` em `RESULTADOS`;
  - `arquivada(v)`, `FICHA_CURTA`, `_ficha_curta(doc)`, `destaques(v)` e `grupo_limpeza(v, crit, hoje)`.

  Testes:
  - cada grupo, com 40 e 10 dias e prazo de 30;
  - grupo desligado;
  - `nota_abaixo_de`, inclusive a vaga sem nota;
  - resultados escolhidos e `sem_resultado`;
  - fallback de data e vaga sem data;
  - `atualizada_em` não conta;
  - exclusões: manual, entrevista, proposta, salva, contratado e vaga já arquivada;
  - vaga por link entra;
  - cada motivo de destaque;
  - a ficha curta só com as chaves de `FICHA_CURTA` mais `arquivada_em`.

## Phase 2: User Story 1 + 3 — prévia, arquivar e proteger o que tem trabalho (P1) 🎯 MVP

**Goal**: a pessoa vê o que seria limpo e arquiva. As destacadas só entram quando marcadas. A busca não traz as
arquivadas de volta.

**Independent Test**: num banco de teste com vagas em Fora há 40 e há 10 dias, uma delas com anotação:

- a prévia mostra só as de 40 dias, com a anotada destacada;
- arquivar sem a destacada deixa a anotada inteira;
- o `IndiceVistas` acha a arquivada.

- [X] T003 [US1] [US3] Em `dash/banco.py`:
  - `prever_limpeza(crit=None, hoje=None)` (D4);
  - `limpar(ids=None, crit=None, incluir_destacadas=False)` (D5): `backup_diario()` antes, uma transação com a
    recontagem, ficha curta ou "sem resposta", depois `wal_checkpoint(TRUNCATE)` e `VACUUM`. Devolve `arquivadas`,
    `encerradas`, `ignoradas`, `antes_kb`, `depois_kb` e `backup`.

  Testes:
  - a prévia não grava nada;
  - `ids=None` deixa as destacadas de fora;
  - `incluir_destacadas` as inclui;
  - ids vindos da página incluem a destacada;
  - id que saiu do grupo vai para `ignoradas`;
  - o backup é criado;
  - `depois_kb < antes_kb` com descrições grandes;
  - a dedupe por id, pelo jk do link e por cargo+empresa depois de arquivar.
- [X] T004 [US1] Em `dash/banco.py` e `dash/requisitos.py`, os itens D7 e D8:
  - `atualizar_usuario` desarquiva quando a etapa muda;
  - `_cmd_quadro` ignora as arquivadas;
  - `requisitos.selecionar` ignora as arquivadas;
  - `_cmd_vaga` mostra "(arquivada em …)".

  Testes:
  - desarquivar;
  - `selecionar` sem as arquivadas;
  - `precisa_analise` e `analise_perfil.lacunas` não pegam a ficha curta.
- [X] T005 [US1] As rotas do D10 em `dash/servidor.py`:
  - `GET` e `PUT /api/limpeza`;
  - `GET /api/limpeza/previa`;
  - `POST /api/limpeza/aplicar`: `ids` é uma lista de até 2000 itens, cada um validado por `banco.ID_VALIDO`, e o
    erro sai em 400.

  Testes das rotas no padrão de servidor de teste que já existe em `tests/`, se houver.

## Phase 3: User Story 2 — critérios próprios e "Sem resposta" (P1)

**Goal**: cada grupo segue o próprio critério. A aplicação parada vira Encerrada com "Sem resposta".

**Independent Test**: com Pendentes desligado e 15 dias em Fora, a prévia não traz pendentes e traz Fora a partir
de 15 dias. A aplicação parada sai como `encerrada`/`sem_resposta` e mantém a descrição.

- [X] T006 [US2] Testes do que a Phase 1 e a Phase 2 já implementaram, de ponta a ponta, em `tests/test_limpeza.py`:
  - os critérios gravados por `salvar_limpeza` mudam a prévia;
  - o grupo `sem_resposta` encerra sem arquivar e mantém `descricao`;
  - `atualizar_usuario` aceita `resultado: "sem_resposta"`.

## Phase 4: User Story 4 — terminal e chat (P2)

- [X] T007 [US4] O subcomando `limpar [--gravar] [--incluir-destacadas]` do D11 em `dash/banco.py`, mais o docstring
  do módulo:
  - a prévia por grupo: total, destacadas com motivo e até 10 exemplos;
  - "Nada foi gravado. Para gravar: python dash/banco.py limpar --gravar";
  - com `--gravar`, o resumo do D5.

  Testes: o subprocesso com `TRAMPO_BANCO`, como em `tests/test_busca.py:76`.
- [X] T008 [P] [D minor] [US4] Documentação:
  - `AGENTS.md`: o comando na lista "Principais comandos";
  - `.agents/skills/buscar-vagas/SKILL.md`: um trecho "Limpar vagas antigas" (mostrar a prévia; gravar só com o OK da
    pessoa), depois `python sincronizar_skills.py`;
  - `dash/API.md`: as rotas, `sem_resposta` na tabela de resultados, `arquivada_em` e a chave `limpeza` em §3.4;
  - `dash/README.md`;
  - `specs/lista-de-desejos.md`: "ver e restaurar vagas arquivadas".

## Phase 5: Página (frontend-react)

- [X] T009 [P] [D minor] [US1] [US2] Tipos, rótulos e serviço:
  - `src/types/api.ts`: `Resultado` ganha `"sem_resposta"`, `Vaga` ganha `arquivada_em?: string | null`, mais os
    tipos `CriteriosLimpeza` e `PreviaLimpeza` (formato do D4 e do D10);
  - `src/utils/rotulos.ts`: `sem_resposta: "Sem resposta"`;
  - `src/services/api/limpeza.ts`: `ler`, `gravar`, `previa` e `aplicar`.
- [X] T010 [D minor] [US1] Esconder as arquivadas:
  - `src/utils/formatters.ts`: `noQuadro` e `noRelatorio` passam a exigir `!vaga.arquivada_em`;
  - `src/App.tsx`: conferir todo filtro e contador de `vagas` que não passa por elas;
  - `FunnelAnalytics` continua recebendo todas.
- [X] T011 [D minor] [US1] [US2] [US3] A aba Limpeza:
  - componente novo `src/components/modals/LimpezaAba.tsx`, conforme o D12:
    - os critérios por grupo;
    - "Ver o que seria limpo", que grava os critérios e pede a prévia;
    - a lista por grupo com caixa de seleção, as destacadas em âmbar, desmarcadas e com o motivo;
    - "Arquivar N vagas" com confirmação;
    - o resumo do resultado e "Já arquivadas: N";
  - em `src/components/modals/SearchFiltersModal.tsx`: a `Aba` `"limpeza"` com o rótulo "Limpeza", fora do Salvar
    geral.

## Phase 6: Fechamento (eu)

- [ ] T012 Fechamento:
  - suíte inteira verde;
  - busca de dados pessoais no diff;
  - commit na `054-limpeza-vagas`;
  - merge na branch pessoal;
  - `PY dash/banco.py limpar` contra o banco real, só a prévia, mostrada à pessoa.
- [ ] T013 Front:
  - push da `frontend-react`, `gh workflow run front.yml` e merge de `origin/front/atualizacao` na branch pessoal;
  - reiniciar o dashboard;
  - teste da pessoa: aba Limpeza → prévia → arquivar → listas e contadores menores, funil igual, backup novo.

  Com o OK: master, push e PR do front.

---

## Dependencies

- T001 e T002 vêm antes de tudo.
- A cadeia do back é T003 → T004 → T005 → T006 → T007, porque todas mexem no `dash/banco.py`.
- T008 depende de T005 e T007, porque documenta as rotas e o comando.
- A Phase 5 pode correr em paralelo com o back, depois que o formato do D4 e do D10 estiver fixo no plano. A ordem é
  T009 → T010 → T011.
- T012 depende de T001 a T008; T013 depende de T012 e de T009 a T011.

## Parallel

- T008, a documentação, e T009 a T011, o front, vão a funcionários enquanto eu faço T003 a T007.

## Implementation Strategy

O MVP é a Phase 1, a Phase 2 e o comando T007: a limpeza já funciona pelo terminal com prévia, ficha curta, backup
e dedupe preservada. Depois entram a página (Phase 5) e a documentação (T008).
