---
description: "Tarefas da feature 046: widgets reorganizáveis no painel Métricas & Funil (Windows)"
---

# Tasks: Widgets reorganizáveis no painel Métricas & Funil

**Input**: spec.md, plan.md, research.md (D1–D10), data-model.md, contracts/painel-widgets.md, quickstart.md.

**Testes**: a spec não pede testes automáticos novos, e a `frontend-react` não tem executor de testes. A conferência é
`tsc --noEmit`, `vite build`, a conferência por CDP do research D10 (que cobre a leitura tolerante do layout) e o
roteiro do quickstart. A suíte Python roda inteira só para garantir que nada mudou.

**Caminhos**:
- documentos: a worktree da branch `046-widgets-metricas`;
- front: a worktree da `frontend-react` ao lado da pasta do projeto, abreviada como `FR/`.

**Formato**: `[P]` = pode rodar em paralelo; `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Conferir a worktree do front `FR/`:
  - `git fetch origin`;
  - a `frontend-react` igual à `origin/frontend-react` (com a 045) e sem mudanças;
  - o `node_modules` presente, ou então `npx -y pnpm@10.34.3 install --frozen-lockfile`.
- [X] T002 `FR/package.json` e `FR/pnpm-lock.yaml`: `npx -y pnpm@10.34.3 add react-grid-layout@2.3.0` (research D1).
  - Conferir no pacote instalado: a licença MIT, os tipos próprios (sem `@types`), as exportações `default`,
    `useContainerWidth` e `verticalCompactor`, os nomes das props (`gridConfig`, `dragConfig`, `resizeConfig`,
    `compactor`, `onDragStop`, `onResizeStop`, `onLayoutChange`) e as classes do `css/styles.css`
    (`react-grid-placeholder`, `react-resizable-handle-se`, `react-draggable-dragging`, `resizing`).
  - Ajustar as tarefas abaixo se algum nome for diferente.

## Phase 2: Foundational (a grade com o painel de hoje)

- [X] T003 [P] `FR/src/services/storage.ts` (data-model §2, research D7):
  - `PREF_KEYS.METRICAS_LAYOUT = "mpt_pref_metricas_layout"`, com o comentário da spec 046;
  - `getLayoutMetricas(): string | null`, `saveLayoutMetricas(texto: string)` e `apagarLayoutMetricas()` no
    `ScreenPreferencesService`, cada um com `try/catch` como os vizinhos.
- [X] T004 [P] `FR/src/components/painel/layout.ts` (novo), funções puras (data-model §1 e §2, research D2, D7 e D9):
  - **Constantes:** `COLUNAS = 12`, `LINHA = 4` (px), `ESPACO = 16` (px, o `pb-4` do item).
  - **Tipos:**
    - `TipoWidget = "numero" | "secao" | "bloco"`;
    - `WidgetDef`: `id`, `titulo`, `tipo`, `icone` (ReactNode), `corIcone` (classes do quadrado do número),
      `subtitulo` (opcional) e `corpo` (ReactNode);
    - `ItemLayout`: `i`, `x`, `y`, `w`, `h`, `fixa`;
    - `Limites`: `minW`, `maxW`, `minH`, `maxH`, em colunas e linhas.
  - **`LIMITES`** por id, da tabela §1, com a altura convertida de px para linhas de 4 px:
    - números de 2 a 6 colunas, "112–320" px;
    - funil e barra (`requisitos`) de 4 a 12, funil "176–640" px, barra "136–640" px;
    - `habilidades`, `suas-habilidades` e `certificacoes` de 3 a 12, "136–2400" px;
    - `experiencia`, `formacao` e `idiomas` "136–1600" px;
    - `senioridade`, `modelo` e `contratacao` "136–1200" px;
    - `plataformas` "136–800" px.
  - **`LAYOUT_PADRAO`** na ordem da §1 (`fixa: false`):
    - os números em `y` 0, `h` 34, `x` 0, 3, 6 e 9, `w` 3;
    - o funil em `y` 34, `h` 54, `w` 12;
    - a barra em `y` 88, `h` 47, `w` 12;
    - `habilidades` (`x` 0, `w` 8) e `suas-habilidades` (`x` 8, `w` 4) em `y` 135, `h` 150;
    - `certificacoes`, `experiencia` e `formacao` em `y` 285; `idiomas`, `senioridade` e `modelo` em `y` 360;
      `contratacao` em `y` 435; todos com `h` 75, `w` 4, `x` 0, 4 e 8;
    - `plataformas` em `y` 510, `h` 55, `w` 12.
  - **`alturaEmLinhas(id, px)`:** `Math.ceil(px / LINHA)`, entre o `minH` e o `maxH` do widget.
  - **`compactar(itens)`:** compactação vertical estável, própria (research D3): na ordem (`y`, `x`), cada widget sobe
    até encostar no de cima da sua coluna; mantém o `fixa`.
  - **`lerLayout(texto)`** (D7), sem lançar erro:
    1. JSON ilegível, `versao` diferente de 1 ou `itens` vazio ou que não é lista → cópia do padrão;
    2. item de id desconhecido sai, e o id repetido vale só na primeira vez;
    3. números inválidos corrigidos: inteiros; `w` entre `minW` e `maxW`; `x` de 0 a `COLUNAS - w`; `y` 0 ou mais;
       `h` entre `minH` e `maxH`; `fixa` só `true` quando é `true`;
    4. o widget que falta entra no fim (`y` abaixo de tudo), com o `x`, o `w` e o `h` do padrão e `fixa: false`;
    5. o resultado passa por `compactar`.
  - **`paraTexto(itens)`:** `{"versao":1,"itens":[{"i","x","y","w","h","fixa"}]}`.
  - **`ordemDaColuna(itens)`:** os ids ordenados por `y` e depois por `x` (research D6).
- [X] T005 [P] `FR/src/components/painel/Widget.tsx` (novo), a moldura (contracts/painel-widgets.md, Widget):
  - **Props:** `def` (`WidgetDef`), `modo` (`"grade"` ou `"coluna"`), `editando`, `fixa`, `onMedida(px)` e
    `onAlturaConteudo()`.
  - **Estrutura no modo grade:**
    - um invólucro `data-widget={id}` com `h-full pb-4` (o espaço de 16 px até o widget de baixo);
    - a moldura com as classes de hoje (`bg-white dark:bg-slate-900 rounded-2xl border border-slate-200
      dark:border-slate-800 shadow-2xs`), `h-full flex flex-col min-w-0`, o padding por tipo (número `p-5`, seção
      `p-5 sm:p-6`, bloco `p-5`) e o espaço entre título e corpo de hoje (`space-y-2`, `space-y-4`, `space-y-3`);
    - o título;
    - o corpo `@container flex-1 min-h-0 overflow-y-auto rolagem-fina`, com um elemento de dentro que não estica e
      leva o `def.corpo`.
  - **Título por tipo:**
    - número: o rótulo `text-xs font-semibold text-slate-500` e o ícone num quadrado `p-2 rounded-xl` com `corIcone`;
    - seção: `h3` (`font-bold text-base`) e o subtítulo `text-xs text-slate-500`;
    - bloco: `h4` (`font-bold text-sm flex items-center gap-2`) com o ícone.
  - **Modo coluna:** o mesmo, sem `h-full`, sem `pb-4`, sem `flex-1` e sem rolagem; o widget tem a altura do conteúdo.
  - **Medida (D3):** só no modo grade, um `ResizeObserver` no título e no elemento de dentro do corpo.
    - Fórmula: `moldura.offsetHeight - corpo.clientHeight + dentro.offsetHeight + ESPACO`.
    - Chama `onMedida` só quando o valor muda; desliga no `unmount`.
- [X] T006 `FR/src/components/painel/PainelWidgets.tsx` (novo), a grade sem edição (research D2, D3 e D6):
  - **Props:** `widgets: WidgetDef[]`.
  - **Estado:**
    - `itens` = `lerLayout(ScreenPreferencesService.getLayoutMetricas())`;
    - as medidas de cada widget num `useRef` (id → px);
    - o layout da pessoa (`base`) à parte das alturas medidas; a tela é `comAlturas(base, alturas)` (research D3).
  - **Largura:** `useContainerWidth()` num invólucro que existe nos dois modos.
  - **Grade:** com o painel de 768 px ou mais, `<ReactGridLayout>` com:
    - `width`;
    - `gridConfig` `{ cols: 12, rowHeight: 4, margin: [16, 0], containerPadding: [0, 0] }`;
    - `compactor={verticalCompactor}`;
    - `layout` = os `itens` com os `LIMITES` de cada id;
    - um filho por widget, com `key` = id, e o `<Widget modo="grade">` dentro.
  - **Altura automática:**
    - `onMedida` grava a medida;
    - se o item não é `fixa`, o `h` vira `alturaEmLinhas(id, px)`;
    - as mudanças do mesmo quadro vão juntas (`requestAnimationFrame`) e passam por `compactar`;
    - a medida não grava no `localStorage`.
  - **Sem animação ao abrir:** a grade só anima no modo de edição (T011).
  - **Sincronia:** a grade recebe o layout calculado; a posição da biblioteca só entra no fim de arrastar ou
    redimensionar, sem `onLayoutChange`, para não entrar em laço.
- [X] T007 `FR/src/components/RequisitosVagas.tsx` (research D8):
  - **`useRequisitos({ vagas, versao })`:** o estado e as chamadas de hoje (`selecao`, `dados`, `erro`, `pedindo`,
    `aberto`, `abaHab`, `todas`, `carregar`, a releitura a cada 3 s com a leitura rodando, `mudarSelecao`, `ler`,
    `parar`, `alternar`), sem mudar o comportamento.
  - **`widgetsRequisitos(r, { onSelectVaga, onAbrirIA, onAbrirPerfil })`:** devolve dez `WidgetDef`, na ordem do
    data-model §1:
    - `requisitos` (seção): título "O que as vagas pedem"; o subtítulo de hoje, com "das vagas escolhidas abaixo"
      trocado por "das vagas escolhidas neste seletor", porque os blocos podem mudar de lugar; o corpo com o seletor,
      a contagem, a leitura com andamento e Parar, os avisos e o erro;
    - os nove blocos (`habilidades`, `suas-habilidades`, `certificacoes`, `experiencia`, `formacao`, `idiomas`,
      `senioridade`, `modelo`, `contratacao`), cada um com o título e o ícone de hoje e o corpo sem a moldura e sem o
      título.
  - **Blocos sempre presentes:**
    - sem o resumo e sem erro: "Montando o resumo…" com o `Loader2`;
    - sem o resumo e com erro: "O resumo não carregou; veja o aviso em O que as vagas pedem.";
    - sem requisitos lidos, em Habilidades mais pedidas, Certificações e cursos, Tempo de experiência e Formação:
      "Ainda não há requisitos lidos nestas vagas.";
    - Suas habilidades, Idiomas, Senioridade, Modelo de trabalho e Tipo de contratação: o conteúdo de hoje.
  - **Fora:** o `export default`, o `CARTAO`, o `Titulo` e a `section` com o grid.
  - **Ficam:** `linha`, `listaPedida`, `suasLinhas`, `listaDeVagas`, `Rodape`, `MARCA`, `VISIVEIS` e `VISIVEIS_SUAS`,
    usados pelos corpos.
- [X] T008 `FR/src/components/FunnelAnalytics.tsx`:
  - chama `useRequisitos({ vagas, versao })`;
  - monta os 16 `WidgetDef` na ordem do data-model §1:
    - os quatro números com os textos, ícones e cores de hoje ("Total Rastreadas", "Conversão para Entrevista",
      "Média de Aderência (IA)", "Ofertas & Propostas"); o corpo é o valor e a linha de baixo;
    - o funil (seção "Funil de Conversão de Candidaturas", com o subtítulo de hoje);
    - os dez de `widgetsRequisitos`;
    - `plataformas` (bloco "Distribuição por Plataforma", `PieChart`);
  - entrega tudo ao `<PainelWidgets>` no lugar do `space-y-6` de hoje.

**Checkpoint**: com o `localStorage` vazio, o painel tem a ordem, as larguras e as alturas de hoje (SC-006), sem
"crescer" ao abrir; a leitura e o seletor funcionam.

## Phase 3: User Story 1 - Montar o painel do seu jeito (Priority: P1) 🎯 MVP

**Goal**: Organizar painel, arrastar pela alça, mudar o tamanho pelo canto, Altura do conteúdo, Concluir e Restaurar
o padrão, com o layout guardado.

**Independent Test**: quickstart, passos 1 a 5, 7, 8 e 11.

- [X] T009 [US1] `FR/src/components/painel/PainelWidgets.tsx`, o modo de edição (research D4, contracts, Topo do
  painel):
  - **Fora da edição:** o botão **Organizar painel** (`LayoutDashboard`) à direita, discreto (contorno, `text-xs`).
  - **Na edição:** a faixa índigo claro (escuro no tema escuro) com:
    - "Organizando o painel: arraste pelo título e puxe o canto para mudar o tamanho";
    - **Restaurar o padrão** (contorno);
    - **Concluir** (cheio, índigo).
  - **Grade na edição:**
    - `dragConfig` `{ enabled: editando, handle: ".alca-widget", cancel: "button, a, input, select, textarea,
      label" }`;
    - `resizeConfig` `{ enabled: editando, handles: ["se"] }`.
  - **`onDragStop`:** copia o layout e grava (`saveLayoutMetricas(paraTexto(itens))`).
  - **`onResizeStop(layout, antes, depois)`:**
    - se a altura mudou 3 linhas (12 px) ou mais, o item fica `fixa: true`;
    - mudar só a largura mantém o `fixa`; o widget automático é medido de novo na largura nova;
    - grava.
  - **Altura do conteúdo:** `fixa: false`, o `h` da última medida, `compactar` e grava.
  - **Restaurar o padrão:**
    - `window.confirm("Voltar o painel ao layout padrão? A posição e o tamanho que você escolheu serão perdidos.")`;
    - com OK, `apagarLayoutMetricas()` e o padrão com as medidas atuais;
    - a edição continua.
  - **Concluir:** desliga a edição; o que mudou já está gravado.
- [X] T010 [US1] `FR/src/components/painel/Widget.tsx`, a moldura na edição (contracts, Widget):
  - o título ganha `alca-widget`, `cursor-move`, `select-none`, o `GripVertical` à esquerda e
    `title="Arraste para mudar de lugar"`;
  - a moldura ganha o contorno tracejado índigo (`outline-2 outline-dashed outline-indigo-400
    dark:outline-indigo-500`);
  - com `fixa`, o título mostra o botão **Altura do conteúdo** (`ArrowUpDown`, `text-[11px]`), que chama
    `onAlturaConteudo`.
- [X] T011 [P] [US1] `FR/src/index.css`, o estilo da grade (research D2 e D4; contracts, Ao arrastar):
  - `import "react-grid-layout/css/styles.css"` em `PainelWidgets.tsx`, e não aqui, para o Vite resolver o pacote;
  - **Sombra do lugar novo:** `.react-grid-item.react-grid-placeholder` sem o vermelho da biblioteca (fundo
    transparente, opacidade 1), com um `::before` em `inset: 0 0 16px 0`, borda tracejada índigo, fundo índigo bem
    claro e cantos de 16 px; no tema escuro, índigo escuro.
  - **Canto de redimensionar:** `.react-grid-item > .react-resizable-handle-se` a 16 px do pé do item (`bottom: 16px`),
    com a marca do canto em `slate-400` no claro e `slate-500` no escuro.
  - **Ao arrastar e ao redimensionar:** `react-draggable-dragging` e `resizing` com sombra mais forte e acima dos
    outros.
  - **Animação:** nenhuma fora do modo de edição; nele, só a da posição (`transform`), fora do item que se mexe.

**Checkpoint**: arrastar, redimensionar, Altura do conteúdo, recarregar e Restaurar funcionam; um clique numa
habilidade, na edição, abre a lista sem mover nada.

## Phase 4: User Story 2 - O conteúdo se ajusta ao tamanho do widget (Priority: P1)

**Goal**: o conteúdo segue a largura do widget, e o que passa da altura fixa rola dentro dele.

**Independent Test**: quickstart, passos 4 e 6.

- [X] T012 [US2] `FR/src/components/FunnelAnalytics.tsx`, consultas de contêiner (research D5):
  - nos números, `text-2xl @[10rem]:text-3xl` no lugar de `text-2xl sm:text-3xl`;
  - no funil, `grid-cols-2 @md:grid-cols-3 @4xl:grid-cols-6` no lugar de `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6`;
  - nas plataformas, os nomes longos quebram a linha (`break-words`, `min-w-0`, a contagem em `whitespace-nowrap`).
- [X] T013 [US2] `FR/src/components/RequisitosVagas.tsx`, listas em duas colunas no widget largo (contracts, Conteúdo
  por largura):
  - em `listaPedida` (Habilidades mais pedidas, Certificações e cursos), o `ul` vira
    `grid grid-cols-1 @3xl:grid-cols-2 gap-x-6 gap-y-2 items-start`;
  - em `suasLinhas`, o `ul` vira `grid grid-cols-1 @3xl:grid-cols-2 gap-x-3 gap-y-1.5 items-start`;
  - os demais blocos continuam numa coluna, com `break-words` e `flex-wrap` como na 045.
- [X] T014 [US2] Rolagem dentro do widget (FR-011):
  - com `fixa`, o corpo rola, inclusive com a lista das vagas de um item aberta;
  - com a altura automática, o widget cresce com Ver todas e com a lista das vagas, até o `maxH`, e daí rola;
  - conferir em `Widget.tsx` que a rolagem do corpo não cria rolagem para o lado (`overflow-x-hidden`).

**Checkpoint**: no mínimo e no máximo de cada widget, o conteúdo fica legível e sem rolagem para o lado (SC-002).

## Phase 5: User Story 3 - No celular, uma coluna na ordem escolhida (Priority: P2)

**Goal**: abaixo de 768 px de largura do painel, uma coluna na ordem do layout, sem Organizar painel.

**Independent Test**: quickstart, passo 10.

- [X] T015 [US3] `FR/src/components/painel/PainelWidgets.tsx`, a coluna única (research D6, data-model §3):
  - com `width < 768`, sem a grade: `flex flex-col gap-4` com `ordemDaColuna(itens, daPessoa)` e
    `<Widget modo="coluna">` (sem layout guardado, a ordem padrão);
  - nem o botão nem a faixa aparecem, e a edição desliga (`useEffect` no `width`);
  - os `itens` e o `localStorage` não mudam;
  - antes da primeira medida da largura (`mounted` falso), nada é desenhado, para não piscar entre os modos.

**Checkpoint**: a 360 px, os 16 widgets numa coluna, na ordem do layout, sem rolagem para o lado (SC-005).

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T016 [P] `README.md` (FR-016): no item Métricas & Funil, Organizar painel (arrastar pelo título, mudar o tamanho
  pelo canto, Altura do conteúdo), Restaurar o padrão, o layout guardado neste navegador e a coluna única no celular.
- [X] T017 [P] `dash/README.md` (FR-016): o mesmo, com os arquivos (`src/components/painel/`), a biblioteca
  `react-grid-layout` só no build da página e a chave `mpt_pref_metricas_layout`.
- [X] T018 `FR/`: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./`, sem erro;
  o `pnpm-lock.yaml` mudou e vai no commit (a Action usa `--frozen-lockfile`).
- [X] T019 `python -m unittest discover -s tests` na worktree da feature, com tudo passando.
- [X] T020 Conferência por CDP (research D10, quickstart), com o build de teste no dashboard, num perfil temporário do
  Edge sem janela:
  1. o layout padrão: a ordem, as larguras, nenhum widget sobreposto e as alturas parecidas com as de hoje;
  2. Organizar painel: a faixa, as alças e os cantos;
  3. arrastar Suas habilidades pelo título até o topo (`Input.dispatchMouseEvent`);
  4. puxar o canto de Tempo de experiência: a largura e a altura mudam, e aparece Altura do conteúdo;
  5. clicar numa habilidade na edição: a lista abre, e nada se move;
  6. recarregar: o layout continua;
  7. Restaurar o padrão, aceitando a confirmação (`Page.handleJavaScriptDialog`);
  8. no `localStorage`: texto corrompido, id desconhecido, widget faltando e números fora dos limites;
  9. a 360 px: uma coluna, na ordem, sem rolagem para o lado e sem Organizar painel;
  10. capturas de tela no tema claro e no escuro, na edição e fora dela.

  Nunca clica em Ler os requisitos, Parar ou nos botões que gravam no servidor.
- [ ] T021 Entrega para o teste (plan, Entrega 1 e 2):
  - busca de dados pessoais no diff;
  - commit local na `046-widgets-metricas` (documentos) e na `frontend-react` (página);
  - merge na branch pessoal;
  - o build em `dash/front/` sem commit;
  - o dashboard reiniciado.

## Dependencies & Execution Order

- T001 → T002.
- **Foundational:**
  - T003, T004 e T005 juntos depois de T002;
  - T006 depois de T003, T004 e T005;
  - T007 a qualquer momento depois de T004;
  - T008 depois de T006 e T007.
- **US1:** T009 → T010; T011 junto com T009.
- **US2:** T012 e T013 depois de T008, em qualquer ordem; T014 depois de T010.
- **US3:** T015 depois de T009 (mesmo arquivo).
- **Polish:** T016 e T017 a qualquer momento; T018 a T021 no fim, nesta ordem.

## Parallel Example

```text
T003 (storage.ts) junto com T004 (layout.ts) e T005 (Widget.tsx)
T016 (README) junto com T017 (dash/README)
```

## Implementation Strategy

- **MVP:** Phases 1 a 3. O painel vira grade com o layout de hoje e já dá para organizar e guardar.
- **Depois:** US2 (conteúdo pela largura do widget) e US3 (coluna única).
- **Entrega:** uma só, para o teste na branch pessoal (T021). Master, push e PR esperam o OK da pessoa.
