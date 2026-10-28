---
description: "Tarefas da feature 034: Vaga segura — filtro de integridade do texto e origem do link (Windows)"
---

# Tasks: Vaga segura — filtro de integridade do texto e origem do link

**Input**: spec.md, plan.md, research.md (R1–R9), data-model.md, contracts/integridade.md, quickstart.md.

**Testes**: incluídos (fluxo da constituição). Ficam em `tests/test_integridade.py`, sem rede: HTML e textos
fabricados, banco temporário (`banco.ARQUIVO`) e `ia` trocado por uma IA falsa que registra os pedidos.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Base de testes em `tests/test_integridade.py`: textos com cada truque, montados com `chr()` para os
  caracteres invisíveis, que ficam explícitos no código.

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 `integridade.py`:
  - `limpar` com a tabela de R4 (bandeiras e ZWJ de emoji preservados);
  - `verificar` com instruções PT/EN (R5), alfabetos (R6), adulteração e marcas de oculto, no formato do data-model;
  - `sinal_oculto`;
  - crédito ao ai-job-search (MIT) no cabeçalho.
- [X] T003 `integridade.py`: `PORTAIS`, `ATS`, `casa`, `portal_do_host` e `origem_do_link` (R8).

**Checkpoint**: testes de T002/T003 passando; nenhum outro arquivo mudou.

## Phase 3: User Story 1 - O texto escondido não chega à IA (P1) 🎯 MVP

- [X] T004 [US1] `fontes/link.py`, `_Texto`:
  - pula os elementos ocultos (R2) e script/style/noscript/template;
  - o trecho oculto com sinal vira marca (R3);
  - os `href` dentro do oculto entram no sinal.
- [X] T005 [US1] `vagas.executar`: `verificar` nas candidatas e nas fora dos critérios depois de `ler_descricoes`,
  gravando `descricao` limpa e `integridade`. `gravar_resultado.documento` leva `integridade`.
- [X] T006 [US1] `dash/banco.py`: helper `_aplicar_integridade(doc)` em `inserir_vagas`, `completar_descricao`,
  `criar_manual` e `criar_de_link`.
- [X] T007 [US1] `dash/analise.montar_pedido` usa `integridade.limpar`; `post_ia.pedido` também.
- [X] T008 [US1] Testes:
  - HTML com `display:none`, `hidden`, `font-size:0`, script;
  - texto colado com tag characters;
  - vaga antiga suja limpa no pedido;
  - vaga comum idêntica (SC-006);
  - 100 vagas em menos de 1 s (SC-005).

## Phase 4: User Story 2 - A pessoa vê o que foi achado (P1)

- [X] T009 [US2] `vagas.py`: ⚠ no `candidatas.md` e contagem no resumo do `buscar` (FR-016).
- [X] T010 [US2] `dash/banco.py`:
  - `pendentes` com `"integridade": "atencao"` e aviso no stderr;
  - `vaga` com as citações;
  - comando `integridade [--gravar]` (FR-017).
- [X] T011 [US2] Testes: linha PT e EN citada e mantida, mistura cirílica, só navegação oculta sem ⚠, vaga de IA
  legítima sem ⚠, comando `integridade` sem e com `--gravar`.

## Phase 5: User Story 3 - Vaga suspeita não contamina as outras (P2)

- [X] T012 [US3] `dash/analise.analisar`: lotes com a vaga ⚠ sozinha (R7); regra nova no pedido (FR-010).
- [X] T013 [US3] Testes: 12 vagas com uma ⚠ dão dois pedidos sem mistura; a regra está no pedido; o resultado do
  filtro não aparece no pedido.

## Phase 6: User Story 4 - Origem do link (P2)

- [X] T014 [US4] `fontes/link.plataforma` usa `integridade.portal_do_host` (FR-014). `banco.criar_de_link` e
  `criar_manual` gravam `origem_link` a partir da URL.
- [X] T015 [US4] Testes: domínios parecidos (prefixo, sufixo, `usuario@`) → `nao_verificada`; subdomínios legítimos
  e Indeed por país reconhecidos; `plataforma("evil-greenhouse.io") == "Outra"`.

## Phase 7: Front e documentação

- [X] T016 Front, na `frontend-react` (worktree `../mpt-front-034`, branch `front-034-vaga-segura` saída de
  `origin/frontend-react`):
  - `types/api.ts` com `integridade` e `origem_link`;
  - ⚠ no `JobCard`;
  - bloco "Texto da vaga" no `JobDetailModal`, com as citações, as contagens e o lembrete "confira a nota";
  - origem do link no detalhe e na confirmação do `AddJobModal`;
  - `tsc --noEmit` e `vite build --base ./` sem erro; commit local, sem push;
  - build de teste copiado no `dash/front` da branch pessoal, sem commit.
- [X] T017 [P] Documentação:
  - `dash/API.md`: campos da vaga;
  - README: seção sobre o texto das vagas;
  - skill `buscar-vagas`: ⚠ e uma vaga por vez; depois `python sincronizar_skills.py`;
  - AGENTS.md: comando `banco.py integridade`.

## Phase 8: Verificação e entrega

- [ ] T018 Verificação:
  - `PY -m unittest discover -s tests` inteiro;
  - `banco.py integridade` no banco real da branch pessoal (SC-002, sem `--gravar`);
  - `graphify update .`.
- [ ] T019 Procurar dados pessoais nos arquivos alterados; commit; merge na branch pessoal; reiniciar o dashboard;
  teste da pessoa. Com o OK: master, push e o front.

## Dependencies & Execution Order

- **T001** → **T002/T003** → histórias.
- **US1 (T004–T008)** é o MVP. **US2** usa o achado de T002 e a gravação de T005/T006. **US3** só depende de T002.
  **US4** só depende de T003.
- **T016** depende dos campos de T006/T014. T017 em paralelo. T018 e T019 por último.

## Implementation Strategy

1. MVP: T001–T008.
2. US2, US3 e US4, que tocam funções diferentes.
3. Front e documentação; verificação no banco real; commit e merge na branch pessoal para o teste.
