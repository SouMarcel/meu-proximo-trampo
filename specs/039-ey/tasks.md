---
description: "Tarefas da feature 039: EY na busca (Windows)"
---

# Tasks: EY (careers.ey.com) na busca de vagas

**Input**: spec.md, plan.md, research.md (R1–R5, D1–D6), contracts/ey.md, quickstart.md. Mecanismos comuns da spec
026 em `fontes/_comum.py`.

**Testes**: incluídos (roteiro `docs/novo-portal.md`, seção 5), em `tests/test_ey.py`, com `ey._baixar` trocado e a
memória de datas numa pasta temporária; nenhum pedido sai para a rede.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 [P] Amostras fictícias em `tests/dados/ey/`, no formato da research R3, com títulos, cidades e textos
  trocados:
  - `lista-1.html`: 25 linhas `tr.data-row` e o link `startrow=25`; títulos que batem e que não batem com
    "desenvolvedor", um "Banco de Talentos", um "(Vaga Exclusiva PCD)", um com "Remoto", um com "+3 more";
  - `lista-2.html`: poucas linhas, sem página seguinte;
  - `vaga.html`: microdados com `datePosted`, `description` e três `PostalAddress`;
  - `vaga-sem-data.html`: sem `datePosted`.

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 Esqueleto de `fontes/ey.py` pelo contrato: constantes, `_estado` (`bloqueado`, `ultimo`, `pausa`, `listas`,
  `lidas`, `textos`) com `_esquecer` em `_comum.AO_ESQUECER`, `pausa()`, `aviso_pausa()`, `_pausar()`, `parada()`,
  `_bloquear()` (sem espera, D6), `_baixar(url)` por `_comum.baixar_pagina`, `id_do_link()`, `url_lista()` (país em
  inglês, D5).
- [X] T003 Leitura em `fontes/ey.py`: `ler_lista(pagina)` (`HTMLParser` das linhas) e `ler_pagina(pagina)` (microdados:
  data, locais, descrição; `tipo` com "Banco de talentos" e "Exclusiva para PCD"; `remoto` pelo título e local).
- [X] T004 Memória de datas em `fontes/ey.py` (D3): `_ler_datas()`, `_gravar_datas()` em `ARQ_DATAS`, descartando
  entradas com mais de `VALIDADE_DATAS`; arquivo ausente ou ilegível vale como vazio.

## Phase 3: User Story 1 - Vagas da EY na busca de sempre (P1)

**Independent Test**: com as amostras, `buscar` devolve vagas com título, "EY", local, data, descrição e link.

- [X] T005 [US1] `_lista(termo, pais, horas)` em `fontes/ey.py`: até 2 páginas, filtro do título, página de cada vaga
  que bate (ou a memória), até `MAX_VAGAS` por busca, parada na primeira mais antiga que a janela (D2); guardada por
  cargo para as outras consultas.
- [X] T006 [US1] `buscar()` e `_atende()` em `fontes/ey.py`: consultas remota, cidade e país (contrato, "Consultas"),
  `por_termo`, aviso `ILEGIVEL` quando a página tem linhas e nada é lido.
- [X] T007 [US1] `descrever()` em `fontes/ey.py`: o texto lido na busca, sem pedido; senão a página (conta em
  `MAX_VAGAS`); parada: o que a vaga já tinha.
- [X] T008 [US1] Testes em `tests/test_ey.py`: linhas da lista, microdados (data, locais, descrição, tipo, remoto),
  filtro do título, consultas remota, cidade e país com uma leitura, janela, paginação sem repetir vaga, limite de 20
  páginas de vaga, memória de datas (a segunda busca não abre a página), vaga sem data entra, `descrever` sem pedido.

## Phase 4: User Story 2 - Ligada por padrão (P1)

- [X] T009 [US2] Registro: `fontes/__init__.py` (import e `FONTES`), `filtros.FONTES_NAC` e `FONTES_PADRAO`,
  `config.exemplo.json` (`"ey"` em `fontes`), `dash/banco.PLATAFORMAS`.
- [X] T010 [US2] Testes em `tests/test_ey.py`: configuração nova traz `"ey"`; lista escolhida sem `"ey"` não faz pedido.

## Phase 5: User Story 3 - Pausa e bloqueio (P1)

- [X] T011 [US3] `.env.exemplo`: `# EY_PAUSA=3   # padrão 3 a 7 s (sorteado); mínimo 3 s para este portal`.
- [X] T012 [US3] Testes em `tests/test_ey.py`: pausa padrão, do `.env`, mínimo e inválida; 403, 429, 503 e login param
  no primeiro, sem nova tentativa, as vagas já lidas seguem, e nenhum pedido no resto da busca.

## Phase 6: User Story 4 - Adicionar Vaga pelo link (P2)

- [X] T013 [US4] `integridade.PORTAIS` (`"EY": ("careers.ey.com",)`), `fontes/link.PLATAFORMAS_LINK` e `link.ler()`:
  link da EY por `ey.ler_pagina(_baixar(url))`, com `id` e `url`.
- [X] T014 [US4] Testes: `id_do_link`, `link.plataforma("careers.ey.com")`, `link.ler` com a página fictícia (mesmo id
  da busca), link de outro host não vira EY.

## Phase 7: Polish

- [X] T015 [P] README, `dash/README.md`, `dash/API.md` (`plataforma` e `fontes`), AGENTS.md (lista de portais),
  `.agents/skills/buscar-vagas/SKILL.md` + `python sincronizar_skills.py`.
- [X] T016 [P] `frontend-react` (com a spec 040; branch local `front-039-portais`, commit 4e544f9): "EY" em `src/types/api.ts`, cor e domínio em
  `src/utils/formatters.ts`, texto do `AddJobModal.tsx`; commit local, push só com o OK da pessoa.
- [X] T017 Verificação: `python -m unittest discover -s tests`, `graphify update .` e o quickstart (busca real pequena,
  segunda busca sem reabrir páginas, ordem por data, Adicionar Vaga).

## Dependencies

- T001 → T008, T010, T012, T014. T002 → T003, T004 → T005 → T006, T007. T009 depende de T002.
- US1 é o MVP; US2, US3 e US4 dependem só da fase 2 e de T005/T006.
- T016 é na `frontend-react` e não bloqueia o resto.
