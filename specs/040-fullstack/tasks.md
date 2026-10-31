---
description: "Tarefas da feature 040: FullStack na busca (Windows)"
---

# Tasks: FullStack (talent.fullstack.com) na busca de vagas

**Input**: spec.md, plan.md, research.md (R1–R5, D1–D7), contracts/fullstack.md, quickstart.md. Mecanismos comuns da
spec 026 em `fontes/_comum.py`; molde `fontes/jobgether.py`.

**Testes**: incluídos (roteiro `docs/novo-portal.md`, seção 5), em `tests/test_fullstack.py`, com `fullstack._baixar`
trocado e a espera numa pasta temporária; nenhum pedido sai para a rede.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 [P] Amostras fictícias em `tests/dados/fullstack/`, no formato da research R3, com títulos, cidades, ids e
  e-mails trocados:
  - `lista-1.json`: `hasNextPage: true`; a mesma vaga (`jobId`) em duas cidades; títulos que batem e que não batem
    com "engineer"; um `CONTRACT`, um `Hybrid`; `ownerEmail` fictício;
  - `lista-2.json`: `hasNextPage: false`; uma vaga dentro da janela e uma mais antiga;
  - `detalhe.json`: `createdAt` em milissegundos, `sections` em HTML e `skillsNames`.

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 Esqueleto de `fontes/fullstack.py` pelo contrato: constantes, `_estado` com `_esquecer` em
  `_comum.AO_ESQUECER`, `pausa()`, `aviso_pausa()`, `_pausar()`, `espera()`, `parada()`, `_bloquear()` (24 h),
  `_baixar(caminho, params)` (GET JSON, sem cookies, sem nova tentativa; 401, 403, 429 e 503 bloqueiam; D7),
  `id_do_link()` (`None`, D6) e o regex `VAGA`.
- [X] T003 `ler_lista(dados)` em `fontes/fullstack.py`: publicações → vagas no formato comum, agrupadas por `jobId`
  (D5), sem `ownerEmail` nem ids internos; `createdAt` em texto ou milissegundos.

## Phase 3: User Story 1 - Vagas da FullStack na busca de sempre (P1)

**Independent Test**: com as amostras, `buscar` devolve vagas com título, "FullStack", "Remoto", data e link, sem
repetir a vaga por cidade.

- [X] T004 [US1] `_lista(pais, horas)` em `fontes/fullstack.py`: uma leitura por busca, ordem por data (D3), até
  `MAX_PAGINAS` ou a janela.
- [X] T005 [US1] `buscar()` em `fontes/fullstack.py`: país fora de `PAISES` e consulta da cidade sem pedido; filtro do
  título, da janela e dos `modelos`; `por_termo`; aviso `ILEGIVEL` se a resposta não tiver `data`/`meta`.
- [X] T006 [US1] `descrever()` em `fontes/fullstack.py`: o detalhe pela `url`, seções em texto e "Habilidades: …";
  parada: o que a vaga já tinha. `MAX_DESCRICOES = 30`.
- [X] T007 [US1] Testes em `tests/test_fullstack.py`: leitura e agrupamento, campos (local, restrição, modelo, tipo,
  `tipo_emprego`, idioma), nenhum e-mail, filtro do título, janela, paginação, uma leitura para vários cargos,
  cidade e outro país sem pedido, `descrever`.

## Phase 4: User Story 2 - Desligada por padrão, com os termos à vista (P1)

- [X] T008 [US2] Registro: `fontes/__init__.py`, `filtros.FONTES_NAC` (fora de `FONTES_PADRAO`), `dash/banco.PLATAFORMAS`.
- [X] T009 [US2] Testes: configuração nova sem `"fullstack"`; desligada, nenhum pedido; `TERMOS` diz que os termos
  proíbem acesso automatizado.

## Phase 5: User Story 3 - Pausa, bloqueio e espera (P1)

- [X] T010 [US3] `.env.exemplo`: `# FULLSTACK_PAUSA=3   # padrão 3 a 7 s (sorteado); mínimo 3 s para este portal`.
- [X] T011 [US3] Testes: pausa padrão, do `.env`, mínimo e inválida; 401, 403, 429 e 503 param no primeiro, sem nova
  tentativa, gravam a espera; na espera, nenhum pedido (busca, descrição e link) e o aviso sai uma vez;
  `vagas.fontes_em_espera` a encontra.

## Phase 6: User Story 4 - Descrição e Adicionar Vaga (P2)

- [X] T012 [US4] `fullstack.ler(url)`; `integridade.PORTAIS` (`"FullStack": ("talent.fullstack.com",)`),
  `fontes/link.PLATAFORMAS_LINK` e `link.ler()` para links da FullStack.
- [X] T013 [US4] Testes: `link.ler` com o detalhe fictício (id `fullstack-<jobId>`), link com `/apply`, espera →
  `LinkErro` com a plataforma e sem pedido.

## Phase 7: Polish

- [X] T014 [P] README e AGENTS.md (portal com termos contrários, desligado), `dash/README.md`, `dash/API.md`,
  `.agents/skills/buscar-vagas/SKILL.md` + `python sincronizar_skills.py`.
- [X] T015 [P] `frontend-react`: "FullStack" junto com a EY (tarefa T016 da spec 039).
- [X] T016 Verificação: suíte inteira, `graphify update .` e o quickstart (busca real pequena com a FullStack ligada
  só na worktree, ordem por data, Adicionar Vaga, espera simulada).

## Dependencies

- T001 → T007, T009, T011, T013. T002 → T003 → T004 → T005, T006. T008 depende de T002.
- US1 é o MVP; US2, US3 e US4 dependem só da fase 2 e de T004/T005.
- Pode ser feita depois da spec 039 na mesma worktree; os arquivos comuns (`fontes/__init__.py`, `filtros.py`,
  `link.py`, `integridade.py`, `banco.py`, docs) mudam em sequência, não em paralelo.
