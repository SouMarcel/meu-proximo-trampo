---
description: "Tarefas da feature 044: aba Internacional com o layout do Relatório de Vagas (Windows)"
---

# Tasks: Aba Internacional com o layout do Relatório de Vagas

**Input**: spec.md, plan.md, research.md (D1–D9), data-model.md, contracts/aba-internacional.md, quickstart.md.

**Testes**: sem teste novo em Python (o servidor não muda). O front é conferido com `tsc --noEmit`, `vite build`, a
conferência por CDP sem gravar e o roteiro do quickstart.

**Caminhos**:
- documentos: a worktree da branch `044-internacional-relatorio`;
- front: uma worktree da `frontend-react`, ao lado da pasta do projeto, abreviada como `FR/`.

**Formato**: `[P]` = pode rodar em paralelo; `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Conferir a worktree do front `FR/`:
  - `git fetch origin`;
  - a `frontend-react` igual à `origin/frontend-react` e sem mudanças;
  - o `node_modules` presente, ou então `npx -y pnpm@10.34.3 install --frozen-lockfile`.

## Phase 2: Foundational

- [X] T002 [P] `FR/src/services/storage.ts` (D2, data-model):
  - a chave `TRIAGE_FILTROS_INT: "mpt_pref_internacional_filtros"` em `PREF_KEYS`;
  - em `ScreenPreferences`: `moeda?: "todas" | "usd" | "eur"` e `visto?: boolean`;
  - `getTriagePreferences(area: "nacional" | "internacional" = "nacional")` e
    `saveTriagePreferences(prefs, area = "nacional")`, com a chave de cada área. A nacional continua em
    `mpt_pref_triage_filtros`.
- [X] T003 `FR/src/components/TriageReport.tsx`, a área (D1):
  - a prop `area?: "nacional" | "internacional"` (padrão `"nacional"`);
  - as props opcionais `onAbrirFiltrosInternacional?: () => void` e `onAbrirProntidao?: () => void`;
  - `const internacional = area === "internacional"`;
  - as preferências lidas e gravadas com `getTriagePreferences(area)` e `saveTriagePreferences(…, area)`.
- [X] T004 `FR/src/App.tsx` e `FR/src/components/InternationalHub.tsx` (D1):
  - na aba Internacional, `<TriageReport area="internacional" …>` com as mesmas props da nacional, sobre
    `vagasInternacional`;
  - mais `onAbrirFiltrosInternacional={() => setFiltrosModo("internacional")}` e
    `onAbrirProntidao={() => setPerfilAberto({ tela: "analises" })}`;
  - o aviso de busca internacional desligada e o `painelBusca` continuam acima, sem mudança;
  - sair o `import InternationalHub` e apagar `InternationalHub.tsx`.

**Checkpoint**: a aba Internacional mostra as vagas de fora no desenho do Relatório (abas internas, Ordenar, filtros,
Baixa aderência, cartão com a nota, Forçar verificar).

## Phase 3: User Story 1 - Achar a vaga de fora com melhor aderência (P1) 🎯 MVP

**Goal**: as vagas de fora nas abas internas, em ordem de aderência, com os filtros do Relatório.

**Independent Test**: quickstart, passos 1 a 6 (sem moeda e visto).

- [X] T005 [US1] `FR/src/components/TriageReport.tsx`, busca no texto (D4, FR-002):
  - com `internacional`, a busca também procura em `v.local` e em `paisDe(v)`;
  - o placeholder passa a ser "Filtrar por cargo, empresa, país ou habilidades...";
  - a nacional não muda.
- [X] T006 [US1] `FR/src/components/TriageReport.tsx`, lista vazia (D8): com `internacional` e Para decidir vazia,
  sem filtro, o texto "Nenhuma vaga de fora esperando decisão. Ligue mais fontes na aba Portais internacionais de
  Filtros da busca, ou peça uma busca." Os outros textos ficam como estão.
- [X] T007 [US1] Conferir (FR-006, US1 8) que o Marcar todas da Internacional só leva ids de vagas de fora:
  - o `ids` vem do `vagas` que o App passa (`vagasInternacional`);
  - o `handleMarcarTodasNaoSeguidas` só grava os ids recebidos.

**Checkpoint**: US1 completa. A primeira vaga de Para decidir é a de maior nota, e as fora dos critérios ficam na
aba delas.

## Phase 4: User Story 2 - Manter o que é só da Internacional (P2)

**Goal**: moeda, visto, linha compacta, botões e extras do cartão.

**Independent Test**: quickstart, passos 5 (moeda e visto), 6, 8 e 9.

- [X] T008 [US2] `FR/src/components/TriageReport.tsx`, filtros de moeda e visto (D3, D7, FR-004):
  - os estados `moeda` (`"todas" | "usd" | "eur"`) e `visto` (`boolean`), lidos das preferências;
  - no filtro, **antes** do `if (!temNota(v)) return true`, e só com `internacional`:
    - Dólar: o salário cita "usd" ou "$";
    - Euro: o salário cita "eur" ou "€";
    - Visto: algum sinal fala de "visto" ou "relocation";
  - `filtrando` passa a incluir `moeda !== "todas" || visto`, e `limparFiltros` volta a moeda para "todas" e desliga
    o visto;
  - na segunda linha da barra, depois de Modo, o grupo "Moeda:" (Todas, Dólar, Euro), um botão de cada vez, e o botão
    "Visto / relocation", os dois com `aria-pressed` e o estilo dos botões de Senioridade e Modo.
- [X] T009 [US2] `FR/src/components/TriageReport.tsx`, linha compacta (D5, FR-008): só com `internacional`, acima das
  abas internas, um cartão baixo com o ícone de globo, "Vagas de fora" e os três números sobre `lista`:
  - "N vagas";
  - "N remotas" (`modoFiltro(v) === "remoto"`);
  - "N com visto ou relocation" (a regra do visto de T008).
- [X] T010 [US2] `FR/src/components/TriageReport.tsx`, botões (D7, FR-009): só com `internacional`, ao lado de
  Ordenar, os botões "Filtros da busca internacional" (`onAbrirFiltrosInternacional`) e "Prontidão internacional"
  (`onAbrirProntidao`, com o `title` de hoje), no estilo de hoje.
- [X] T011 [US2] `FR/src/components/TriageReport.tsx`, extras do cartão (D6, FR-007): só com `internacional`, abaixo
  da linha de empresa, local e salário:
  - a etiqueta com o globo e `paisDe(vaga) || "Global"`;
  - "Contratação: …" com `CONTRATACAO` (ou "não informada");
  - os sinais com o escudo, como no cartão de hoje.

  Os ícones `Globe2` e `ShieldCheck` e o `CONTRATACAO` passam a ser importados.

**Checkpoint**: US2 completa. Tudo o que a aba de hoje tinha está na aba nova (SC-003).

## Phase 5: User Story 3 - Filtros de cada aba à parte (P3)

**Goal**: a ordem e os filtros da Internacional guardados à parte dos da nacional.

**Independent Test**: quickstart, passo 10.

- [X] T012 [US3] `FR/src/components/TriageReport.tsx`, preferências (FR-010, FR-011, data-model):
  - o `saveTriagePreferences` grava também `moeda` e `visto` quando a área é a internacional;
  - a leitura valida cada campo pelas regras do data-model, e o que não vale vira o padrão;
  - a aba interna e a busca no texto continuam sem ser guardadas.

**Checkpoint**: US3 completa. Recarregar a página mantém os filtros de cada aba, sem misturar.

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] `README.md`, "Vagas internacionais" (FR-014): a aba tem o desenho do Relatório de Vagas (abas internas,
  ordem, filtros), mais moeda, visto e os botões, e guarda os seus filtros.
- [X] T014 [P] `dash/README.md` (FR-014): uma linha para a aba Internacional, depois do Relatório de Vagas.
- [X] T015 `FR/`: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./`, sem erro.
- [X] T016 `python -m unittest discover -s tests` na worktree da feature: tudo passando.
- [X] T017 Conferência por CDP (D9, quickstart), com o build de teste no dashboard:
  - só leitura do DOM e cliques em abas internas, Ordenar e filtros;
  - nunca em Seguir, Não seguir, Voltar, Marcar todas ou Forçar verificar;
  - confere a ordem, a separação das abas internas, as preferências por área e a largura de 360 px.
- [X] T018 Entrega para o teste (plan, Entrega 1 e 2):
  - busca de dados pessoais no diff;
  - commit local na `044-internacional-relatorio` e na `frontend-react`;
  - merge na branch pessoal;
  - o build em `dash/front/` sem commit;
  - o dashboard reiniciado.
- [X] T019 `FR/src/components/NavigationTabs.tsx` (FR-015, pedido durante o teste):
  - os rótulos Vagas Nacionais, Vagas Internacionais e Aplicações;
  - a ordem Vagas Nacionais, Vagas Internacionais, Aplicações, Preparador de Entrevistas e Métricas & Funil;
  - o texto de Filtros da busca que cita a aba passa a dizer "Vagas Internacionais";
  - `tsc`, `vite build` e o build de teste de novo no dashboard da branch pessoal.

## Dependencies & Execution Order

- T001 → T002 e T003 → T004.
- US1 (T005–T007) depois de T004.
- US2 (T008–T011) e US3 (T012) mexem no mesmo arquivo de US1: em sequência, na ordem das tarefas.
- T013 e T014 podem rodar a qualquer momento.
- T015–T018 no fim, nesta ordem.

## Parallel Example

```text
T002 (storage.ts) junto com T013 e T014 (documentos)
```

## Implementation Strategy

- **MVP**: Phases 1 a 3. A aba Internacional já fica no desenho do Relatório, com a ordem por aderência.
- Depois US2 (o que é só da Internacional) e US3 (preferências à parte).
- A pessoa pediu para seguir direto até o teste na branch pessoal. Master, push e PR esperam o OK dela.
