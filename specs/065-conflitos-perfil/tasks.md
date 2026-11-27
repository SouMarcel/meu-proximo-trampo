---
description: "Tarefas da spec 065: Conflitos do Meu perfil mais claros e seguros"
---

# Tasks: Conflitos do Meu perfil mais claros e seguros

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md).

**Tests**: no estilo do projeto, cada mudança de servidor vem com teste em `tests/test_primeiros_passos.py` (perfil e
progresso em pasta temporária, sem IA de verdade). Suíte: `.venv\Scripts\python.exe -m unittest discover -s tests`.
Front: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./` na `frontend-react`
(worktree `../mpt-front-027b`).

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`. O
servidor fica comigo: são mudanças pequenas no mesmo arquivo e com teste, e o brief custaria mais que fazer.

## Format: `[ID] [P?] [D tamanho?] [Story] Description`

## Phase 1: Base (bloqueia as histórias)

- [X] T001 Rascunho com data e nota em `primeiros_passos.py` (data-model "Rascunho" e "Opção"; research R1, R6):
  `FORMATO` com `"opcoes": [{"valor", "nota", "fonte"}]`; regra nova em `pedido_rascunho`: "Em cada opção de conflito,
  \"valor\" é só o dado (a data, o nome, o cargo), sem explicação; a explicação, se houver, vai em \"nota\"."
  `normalizar_rascunho` guarda `nota` ("string (≤200)", documentos mascarados, `""` quando não vem) e `gerado_em`
  ("ISO 8601 (segundos)"); `rascunho_sem_ia` também grava `gerado_em`. `_escolher` continua usando só `valor`. Testes:
  nota separada não entra em `montar_perfil`; nota ausente vira `""`; `gerado_em` presente nos dois caminhos.

## Phase 2: US1 Não perder o que entrou no perfil depois do rascunho (P1) 🎯 MVP

**Teste independente**: rascunho com `gerado_em` antigo + perfil com um item a mais → `previa` traz `aviso` com o item
em `sairiam`; `PUT /api/perfil` com `perfil_versao` velho → 409.

- [X] T002 [US1] Aviso na prévia em `primeiros_passos.py` (research R2, R3, R4; contrato `POST /api/perfil/previa`):
  `versao_perfil(texto) -> str | None` (SHA-256, 16 primeiros hex; `None` sem perfil); `itens_que_sairiam(atual,
  novo) -> list[str]` (linhas do atual que começam com `- ` ou `#` e cuja `_chave` não aparece entre as `_chave` das
  linhas do novo; ordem do perfil; "≤60"); `previa` devolve `perfil_versao` e `aviso` = `{rascunho_em, perfil_em,
  sairiam, pode_refazer}` quando há perfil, `origem == "ia"` e (rascunho mais antigo que o `perfil.md` ou sem
  `gerado_em` com `sairiam` não vazio); senão `aviso: null`. `pode_refazer` = `ia.disponivel()` (falha conta como
  false). Com `markdown` editado, `sairiam` é refeito sobre ele. Testes dos quatro casos (antigo, novo, sem data com e
  sem perda) e de linha que só mudou de lugar não contar.
- [X] T003 [US1] Herdar escolhas ao refazer (research R5): `herdar_escolhas(novo: dict, antigo: dict | None) -> dict`
  em `primeiros_passos.py` (mesmo `campo` por `_chave` e valor escolhido igual, por `_chave`, ao `valor` de uma opção
  nova; o resto fica `None`); `dash/servidor.py`, `POST /api/perfil/rascunho`, aplica com o rascunho anterior lido na
  mesma trava antes de salvar. Testes: casa, não casa por valor diferente, conflito sem par.
- [X] T004 [US1] Gravar confere a versão (FR-012; contrato `PUT /api/perfil`): em `dash/servidor.py`, com
  `perfil_versao` no corpo diferente de `pp.versao_perfil(texto atual)`, responde 409 "O perfil mudou depois que você
  abriu a Revisão. Veja de novo o que muda antes de gravar."; sem o campo, como hoje. Teste no estilo dos testes de
  servidor existentes (ou da função auxiliar, se o servidor não tiver teste de rota para o perfil).
- [X] T005 [D minor] → copilot, GO na tentativa 1 (com a T007, mesmo brief). [US1] Front da Revisão (`frontend-react`: `src/services/api/perfil.ts`,
  `src/components/perfil/MeuPerfil.tsx`; research R9): tipos `Previa.perfil_versao` e `Previa.aviso`; `gravar(md,
  perfilVersao?)`; na tela "revisao", com `prev.aviso`, caixa âmbar acima do texto: "Este rascunho é de <data> e o seu
  perfil mudou em <data>. Gravar substitui o perfil inteiro." (sem `rascunho_em`: "Gravar substitui o perfil
  inteiro."), a lista `sairiam` ("Sairiam do perfil (N):"; vazia: "Nenhum item do perfil atual sairia.") e os botões
  "Refazer o rascunho" (`perfilApi.rascunho(false)`; depois vai a "conflitos" se houver conflito sem escolha, senão
  remonta a prévia; desabilitado com `title` "Ligue uma IA para refazer o rascunho" quando `!pode_refazer`) e "Manter o
  perfil atual" (`ir("concluido")`). Com aviso, o botão de confirmar vira "Gravar mesmo assim (substitui o perfil)".
  Gravar manda `prev.perfil_versao`; no 409, mostra a mensagem e volta ao "Ver o que muda" (`setConfirmar(false)` e
  nova prévia).

**Checkpoint**: US1 sozinha já evita a perda (servidor + tela).

## Phase 3: US2 Valor do conflito sem comentário (P2)

**Teste independente**: opção com nota → valor limpo no perfil; data de experiência escolhida com texto a mais →
achado no Diagnóstico.

- [X] T006 [US2] Diagnóstico da data com texto a mais em `primeiros_passos.py` (research R7; FR-008): em
  `diagnosticar`, para `inicio` e `fim` de cada experiência com marcador `{{conflito:N}}` já escolhido, resolve com
  `_escolher`; se o valor não for "só data" (`mm/aaaa`, `aaaa`, `aaaa-mm`, mês por extenso ou abreviado com ano, ou
  `_atual`), acha `fraco` "A data escolhida em <cargo> traz texto a mais: <valor>." com pergunta "Qual é só a data?" e
  `ir: "texto"` (emenda: os resolvidos não voltam à aba Conflitos). Testes: "04/2018" passa; "04/2018 (comentário)" acusa; "mar/2021" passa.
- [X] T007 [D minor] → entregue junto da T005. [US2] [US3] Front da aba Conflitos (`frontend-react`: `src/services/api/perfil.ts`,
  `src/components/perfil/MeuPerfil.tsx`; research R8; depois da T005, mesmo arquivo): tipo `opcoes[].nota?`; a nota sob
  o valor, `text-xs` em cinza; ao entrar na tela "conflitos", guardar os índices com `escolha != null` (estado que só
  muda quando a tela muda); esses vão num `<details>` fechado com `<summary>` "N resolvidos (mudar)", os demais abertos
  como hoje; tudo resolvido: "Todos os conflitos estão resolvidos." acima do resumo; escolher durante a visita não
  move o conflito. A seção de relatos que divergem (spec 060) fica como está.

## Phase 4: US3 Conflitos resolvidos recolhidos (P3)

A tela é a T007 (mesmo arquivo da nota; uma entrega só). **Teste independente**: tudo escolhido → Continuar → voltar
à aba → só o resumo; abrir, mudar, sair e voltar → a escolha nova ficou.

**Emenda (27/11, pedido no teste)**: os resolvidos não aparecem mais (sem o resumo "N resolvidos (mudar)"); feita
por mim no front (patch).

## Phase 5: Polish

- [X] T008 [P] `dash/API.md`: `rascunho.gerado_em`, `opcoes[].nota`, `previa` com `perfil_versao` e `aviso`, `PUT
  /api/perfil` com `perfil_versao` e o 409, herança de escolhas no `POST /api/perfil/rascunho` (contracts/api.md).
- [ ] T009 Suíte inteira, `graphify update .`, procurar dados pessoais nos arquivos alterados; commit na branch.
- [ ] T010 Teste na branch pessoal (merge na `marcel`, front pelo build local da `frontend-react`), quickstart US1 a US3;
  com o OK: `master`, push, PR do front pela Action, `git merge master` na `marcel`, apagar worktree e branch.

## Dependencies & Execution Order

- T001 → T002, T003, T006 (mesmo arquivo; em sequência).
- T002 → T004 (usa `versao_perfil`) → T005.
- T005 → T007 (mesmo arquivo no front).
- T008 em paralelo com qualquer tarefa depois da T004.
- Paralelo real: o front (T005, depois T007, delegados) enquanto eu faço T006 e T008 no servidor.

## Implementation Strategy

MVP = Phase 1 + US1 (T001 a T005): é o que impede perder fatos do perfil. US2 e US3 entram na mesma entrega, porque
são pequenas e o front sai num único PR.
