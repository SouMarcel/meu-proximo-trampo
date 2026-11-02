---
description: "Tarefas da feature 043: abas no painel Filtros da busca (Windows)"
---

# Tasks: Abas no painel Filtros da busca

**Input**: spec.md, plan.md, research.md (D1–D11), data-model.md, contracts/api.md, contracts/painel.md,
quickstart.md. Molde das abas: `abaBotao` em `src/components/modals/JobDetailModal.tsx` (`frontend-react`).

**Testes**: incluídos, em `tests/test_abas_filtros.py`, sem rede (D2). O front é conferido com `tsc --noEmit`,
`vite build` e o roteiro do quickstart.

**Caminhos**:
- servidor: a worktree `wt-043`, na branch `043-abas-filtros`;
- front: uma worktree da `frontend-react`, ao lado da pasta do projeto, abreviada como `FR/`.

**Formato**: `[P]` = pode rodar em paralelo; `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Conferir a worktree do front `FR/`:
  - `git fetch origin`;
  - a `frontend-react` igual à `origin/frontend-react` e sem mudanças;
  - o `node_modules` presente, ou então `npx -y pnpm@10.34.3 install --frozen-lockfile`.

## Phase 2: Foundational

- [X] T002 [P] `FR/src/services/api/config.ts`:
  - `export interface PortalAMapear { nome: string; situacao: "em_estudo" | "nao_deu"; motivo: string }`;
  - `portais_a_mapear?: PortalAMapear[]` em `Opcoes`, opcional para servidor antigo (contracts/api.md).
- [X] T003 `FR/src/components/modals/SearchFiltersModal.tsx`, estrutura das abas (D4, D5):
  - `type Aba = "geral" | "portais" | "internacionais" | "empresas"` e `const [aba, setAba] = useState<Aba>("geral")`;
  - a lista das abas, na ordem: Geral, Portais, Portais internacionais, Empresas acompanhadas/excluídas;
  - no modo nacional, uma faixa fixa entre o cabeçalho e a área que rola, com o visual do `abaBotao` do
    `JobDetailModal` (borda de baixo índigo na ativa, `overflow-x-auto`, `whitespace-nowrap`);
  - `role="tablist"` com `aria-label="Grupos de filtros"`, e cada botão com `role="tab"`, `id`, `aria-selected`,
    `aria-controls` e `tabIndex` 0 na ativa e -1 nas outras;
  - ← e →, com volta ao começo e ao fim, e Home e End trocam de aba e levam o foco à aba nova;
  - a área com `role="tabpanel"` e `aria-labelledby`;
  - a função `irPara(a: Aba)`: `setAba(a)` e depois `onTrocarModo("nacional")`.

**Checkpoint**: as quatro abas aparecem e trocam; o conteúdo ainda é o de hoje.

## Phase 3: User Story 1 - Achar cada grupo de filtros pela aba (P1) 🎯 MVP

**Goal**: cada seção de hoje numa aba, num formulário só, com o rodapé e os avisos em qualquer aba.

**Independent Test**: quickstart, passos 1, 3, 4, 5 e 6.

- [X] T004 [US1] `FR/src/components/modals/SearchFiltersModal.tsx`, distribuir as seções sem mudar os textos (FR-003,
  FR-004, FR-006):
  - **Geral**: Cargos, Localidade, Modo de trabalho, Data de publicação, Tipo de emprego, Senioridade, Moedas aceitas
    (vagas fora do seu país) e Idiomas aceitos;
  - **Portais**: a seção "Portais", com o título "Portais da busca" e o mesmo texto, seguida do `<PortaisLogin>`, sem
    mudança;
  - **Empresas acompanhadas/excluídas**: "Empresas que você acompanha" (link, Adicionar, erro e aviso da IA, lista com
    Remover), seguida de "Empresas a excluir" (`Etiquetas`).

  A borda da última seção de cada aba some (`last:border-0` continua valendo dentro de cada aba).
- [X] T005 [US1] `FR/src/components/modals/SearchFiltersModal.tsx`, avisos e erro em qualquer aba (FR-008, FR-009,
  D7):
  - os avisos de filtros sugeridos e de primeira vez ficam no topo da área que rola, fora do `tabpanel`, em todas as
    abas;
  - o aviso de primeira vez continua só no modo nacional;
  - o `<p role="alert">` do erro sai da área que rola e vai para o rodapé, acima da conta de consultas.
- [X] T006 [US1] `FR/src/components/modals/SearchFiltersModal.tsx`, contadores (FR-014, D6), com `useMemo` sobre
  `d` e `op`:
  - **Portais**: os nomes de `d.fontes` que estão em `op.fontes_nac` ou `op.fontes_login`;
  - **Portais internacionais**: os de `d.internacional.fontes` que estão em `op.fontes_int`;
  - **Empresas**: `d.empresas.length + d.empresas_excluir.length`;
  - a pílula pequena depois do nome mostra também o zero;
  - para o leitor de tela, "N ligados" (Portais), "N ligadas" (Portais internacionais) ou "N empresas", com
    `sr-only` ou `aria-label`;
  - a Geral fica sem contador.

**Checkpoint**: US1 completa. Editar em três abas e salvar grava tudo; Cancelar descarta; reabrir volta à Geral.

## Phase 4: User Story 2 - Portais internacionais numa aba própria (P2)

**Goal**: as fontes do exterior na aba Portais internacionais, com o aviso da busca internacional desligada.

**Independent Test**: quickstart, passo 7.

- [X] T007 [US2] `FR/src/components/modals/SearchFiltersModal.tsx`, aba Portais internacionais (FR-005, D8):
  - a seção "Fontes do exterior" sai do bloco `internacional &&` e vai para a aba, com o mesmo título, texto e
    `Marcar`;
  - com `!d.internacional.ativo`, um aviso âmbar no topo da aba (o estilo do aviso de primeira vez, com
    `AlertTriangle`): "A busca internacional está desligada: estas fontes só rodam com ela ligada.";
  - nesse aviso, o botão-link "Ligar em Filtros da busca internacional" chama `onTrocarModo("internacional")`;
  - marcar continua possível.
- [X] T008 [US2] `FR/src/components/modals/SearchFiltersModal.tsx`, fim do painel internacional (FR-010, FR-011):
  - o `<p className={DICA}>` passa a dizer: "Cargos, portais e localidade ficam em **Filtros da busca**; as fontes do
    exterior, na aba **Portais internacionais**.";
  - o primeiro link chama `onTrocarModo("nacional")` e mantém a aba;
  - o segundo chama `irPara("internacionais")`;
  - conferir que o texto de "Buscar também vagas no exterior" ainda faz sentido sem a seção no mesmo painel.

**Checkpoint**: US2 completa. Ida e volta entre os dois modos mantém o editado e a aba.

## Phase 5: User Story 3 - Ver os próximos portais (P3)

**Goal**: o bloco Próximos a mapear na aba Portais, com a lista fixa do servidor.

**Independent Test**: quickstart, passo 2, e `PY -m unittest tests.test_abas_filtros`.

- [X] T009 [P] [US3] `tests/test_abas_filtros.py` (D2), escrito antes de T010 e falhando sem ele. Confere:
  - `filtros.opcoes()["portais_a_mapear"]` é uma lista;
  - cada item tem `nome` não vazio, e `situacao` é `"em_estudo"` ou `"nao_deu"`;
  - "`motivo` obrigatório quando `situacao` é `nao_deu`";
  - nenhum `nome` coincide, com `filtros.sem_acento` e minúsculas, com um rótulo de `FONTES_NAC`, `FONTES_LOGIN` ou
    `FONTES_INT` ("o portal que entra na busca sai da lista", FR-013);
  - `opcoes()` devolve uma cópia: mudar o resultado não altera a constante.
- [X] T010 [US3] `filtros.py` (D1, D3, data-model.md):
  - `PORTAIS_A_MAPEAR` logo depois de `FONTES_LOGIN`, com um comentário que remete a `docs/novo-portal.md`. Conteúdo,
    nesta ordem:
    - InHire: `em_estudo`, motivo `""`;
    - Catho: `em_estudo`, motivo `""`;
    - Glassdoor: `nao_deu`, motivo "Recusou acesso automatizado em 23/10/2026, e a API de parceiros não está aberta.";
  - `opcoes()` acrescenta `"portais_a_mapear": [dict(p) for p in PORTAIS_A_MAPEAR]`.
- [X] T011 [US3] `FR/src/components/modals/SearchFiltersModal.tsx`, a seção "Próximos a mapear", última da aba
  Portais (FR-012, contracts/painel.md):
  - a dica: "Portais que a ferramenta estuda para entrar na busca, e os que não deram, com o motivo.";
  - uma linha por portal: o nome em negrito, a situação ("Em estudo", em cinza, ou "Não deu", em âmbar) e, se
    `nao_deu`, o motivo;
  - só leitura, sem botão;
  - não aparece com `op.portais_a_mapear` ausente ou vazio.

**Checkpoint**: as três histórias completas.

## Phase 6: Polish

- [X] T012 [P] Documentação (FR-017, D10):
  - `dash/API.md` §3.4: `opcoes.portais_a_mapear` e as quatro abas do painel; as fontes do exterior na aba Portais
    internacionais;
  - `dash/README.md`: o item Filtros da busca com as quatro abas, e Empresas e Portais com login como estão hoje;
  - `.agents/skills/buscar-vagas/SKILL.md`, com os caminhos novos ("Filtros da busca → aba Portais", "aba Portais →
    Portais com login", "aba Empresas acompanhadas/excluídas", "aba Portais internacionais"), depois
    `python sincronizar_skills.py`;
  - `docs/novo-portal.md`:
    - na tabela "Arquivos que o portal novo toca", linha `filtros.py`: tirar o portal de `PORTAIS_A_MAPEAR`;
    - na seção 1: o portal barrado entra em `PORTAIS_A_MAPEAR` como `nao_deu`, com o motivo;
  - `specs/lista-de-desejos.md`: em "Mais portais do Brasil", a lista do painel (`filtros.PORTAIS_A_MAPEAR`) acompanha
    este item.
- [X] T013 Front: em `FR/`, `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./`,
  ambos sem erro. Depois o commit local na `frontend-react`, sem push.
- [X] T014 Verificação e entrega:
  1. `PY -m unittest discover -s tests` e `python sincronizar_skills.py --conferir`;
  2. a busca por dados pessoais no diff das duas branches;
  3. o commit na `043-abas-filtros`;
  4. na pasta principal (branch pessoal):
     - `git merge 043-abas-filtros`;
     - o `FR/dist/` copiado para `dash/front/`, sem commit;
     - o dashboard reiniciado com `--sem-navegador`;
  5. a conferência automática por CDP com o Edge sem janela: as abas trocam, os contadores aparecem, o bloco de
     próximos tem 3 itens e o painel internacional não tem Fontes do exterior; sem salvar;
  6. `graphify update .`.

  Master, push e PR do front só com o OK da pessoa depois do teste. Antes da entrega, `git checkout -- dash/front` e
  apagar os assets novos.

  A conferência por CDP achou uma barra de rolagem sob as abas no computador: a faixa passava 12 px da largura do
  painel. Foi corrigido com menos margem e espaço entre as abas, e a barra ficou fina. A mesma conferência também
  passou:
  - teclado (Home, End e as setas, com volta);
  - ida e volta entre os dois modos;
  - o aviso com a busca internacional desligada, só no formulário;
  - 360 px sem rolagem lateral;
  - reabrir na Geral.

## Dependencies

- T001 → T002 e T003 → todas as histórias.
- US1 (T004–T006) é o MVP.
- US2 (T007–T008) depende de T003 (`irPara`) e pode vir depois de US1.
- US3: T009 → T010 (servidor); T011 depende de T002 e T004 (a aba Portais montada).
- T004 a T008 e T011 mexem no mesmo arquivo (`SearchFiltersModal.tsx`) e vão em sequência.
- T012 depende só da spec. T013 depende das tarefas do front. T014 é a última.

## Parallel Example

```text
Ao mesmo tempo, em arquivos diferentes:
  T002  FR/src/services/api/config.ts
  T009  tests/test_abas_filtros.py   →  T010  filtros.py
  T012  documentação
Em sequência, no mesmo arquivo:
  T003 → T004 → T005 → T006 → T007 → T008 → T011  (SearchFiltersModal.tsx)
```

## Implementation Strategy

1. **MVP**: T001 a T006. O painel com abas, as seções no lugar, o formulário único, o erro no rodapé e os contadores.
2. **Incremento 1**: T007 e T008 (Portais internacionais).
3. **Incremento 2**: T009 a T011 (Próximos a mapear, com o servidor).
4. **Fechamento**: T012 a T014. Uma entrega só na branch pessoal, para a pessoa testar tudo de uma vez.
