# Research: Widgets reorganizáveis no painel Métricas & Funil

## D1. A biblioteca da grade

- **Decision:** `react-grid-layout` 2.3.0 (MIT, publicada em 05/10/2026), com a API v2 (`GridLayout`,
  `useContainerWidth`, `verticalCompactor`).
  - Ela traz alça (`dragConfig.handle`), seletor que não arrasta (`dragConfig.cancel`), canto de redimensionar
    (`resizeConfig.handles`), mínimo e máximo por widget (`minW`, `maxW`, `minH`, `maxH`) e compactação vertical, em
    que o que fica embaixo sobe.
  - Funciona com React 19: o código usa `nodeRef`, sem `findDOMNode`.
  - O estilo próprio (`react-grid-layout/css/styles.css`) já inclui o canto de redimensionar. Não é preciso importar o
    CSS da `react-resizable`, que no pnpm não fica acessível ao nosso código.
- **Rationale:**
  - é a biblioteca de grade de painel mais usada (Grafana, Metabase, Kibana) e cobre o que a spec pede sem código
    próprio de colisão;
  - entra só no build da página, feito pela Action, e não muda a instalação da ferramenta.
- **Alternatives considered:**
  - **grade escrita à mão** (eventos de ponteiro, colisão e compactação): cerca de 300 linhas, com os erros todos por
    nossa conta;
  - **arrastar do HTML5 sobre a grade do CSS:** não redimensiona e não funciona bem no toque;
  - **dnd-kit:** ordena listas, mas não tem grade com largura e altura;
  - **a versão 1 da react-grid-layout:** usa `findDOMNode`, que o React 19 não tem mais.

## D2. Grade: colunas, passos e espaço entre widgets

- **Decision:** 12 colunas; linhas de 4 px; espaço de 16 px entre colunas e nenhum entre linhas
  (`margin: [16, 0]`, `containerPadding: [0, 0]`).
  - O espaço de 16 px entre um widget e o de baixo fica dentro do item da grade (`pb-4`).
  - A sombra do lugar novo e o canto de redimensionar descontam esses 16 px no CSS.
- **Rationale:**
  - a linha de 4 px deixa a altura automática encaixar no conteúdo, com no máximo 3 px de sobra;
  - com o espaço entre linhas da biblioteca (passo de 26 px ou mais), sobraria até 25 px em cada widget;
  - redimensionar em passos de 4 px parece contínuo e continua "em passos da grade".
- **Alternatives considered:** linha de 10 px com espaço de 16 px (sobra visível); grade de 24 colunas (mais fina do
  que o necessário para 16 widgets).

## D3. Altura que acompanha o conteúdo até a pessoa mudar

- **Decision:** cada item do layout tem `fixa` (sim ou não).
  - **Altura automática (`fixa: false`):** é o padrão. A moldura mede o conteúdo com `ResizeObserver` e ajusta `h` na
    grade.
    - A medida é a altura do título mais a altura natural do conteúdo (o elemento de dentro, que não estica), mais 16
      px do espaço.
    - O valor fica entre o mínimo e o máximo do widget.
  - **Altura fixa:** puxar o canto e mudar a altura deixa o widget com `fixa: true`; o conteúdo que passar rola dentro.
    Mudar só a largura não fixa a altura: uma mudança de menos de 3 linhas (12 px) na altura é o tremor da mão ao puxar
    o canto para o lado.
  - **Volta:** no modo de edição, o widget de altura fixa mostra **Altura do conteúdo**, que volta para `fixa: false`.
  - **Estado:** o layout da pessoa (posição, largura, altura fixa) fica à parte das alturas medidas; a tela é sempre
    calculada dos dois. A compactação é a nossa (`layout.compactar`), estável: na ordem da posição, cada widget sobe até
    encostar no de cima da sua coluna, e ninguém passa à frente de ninguém. A da biblioteca depende do caminho: no
    teste, o resumo carregando (blocos pequenos) e depois cheio fez um widget atravessar o funil ao recarregar.
  - **Animação:** só no modo de edição, e só da posição (os outros abrindo espaço). Fora dele, a altura acompanha o
    conteúdo na hora, como numa página comum, e o painel não "cresce" ao abrir.
- **Rationale:**
  - quem nunca organizou vê o painel de hoje, em que a altura segue o conteúdo (FR-002, SC-006);
  - Ver todas e a lista das vagas de um item fazem o widget crescer como hoje, e os de baixo descem;
  - a pessoa que quer um widget baixo com rolagem consegue isso puxando o canto (FR-011).
- **Alternatives considered:**
  - **altura fixa padrão para todos:** os widgets ficariam cortados ou vazios, e o painel de hoje mudaria;
  - **trocar por um layout livre só depois do primeiro Organizar:** daria um salto visual ao entrar no modo de edição.

## D4. Modo de edição

- **Decision:**
  - **Botão:** **Organizar painel** fica no topo do painel. Com ele, `dragConfig.enabled` e `resizeConfig.enabled`
    ligam.
  - **Alça:** `dragConfig.handle = ".alca-widget"`, o título do widget, que ganha o ícone de pegar (`GripVertical`) e o
    cursor de mover.
  - **O que não arrasta:** `dragConfig.cancel = "button, a, input, select, textarea, label"`. Um botão no título, como
    Altura do conteúdo, não arrasta.
  - **O que vale:** `resizeConfig.handles = ["se"]`. O arrasto só começa depois de 3 px de movimento (padrão da v2),
    então um clique não move nada.
  - **Aviso:** uma faixa no topo diz "Organizando o painel: arraste pelo título e puxe o canto para mudar o tamanho",
    com **Concluir** e **Restaurar o padrão**.
  - **Restaurar:** confirma com `window.confirm`, como o Meu perfil já faz, apaga a chave e volta ao padrão.
  - **Gravação:** acontece a cada `onDragStop`, `onResizeStop` e Altura do conteúdo. Sair sem Concluir, trocando de aba,
    não perde nada (edge case da spec).
  - **Contorno:** cada widget ganha um contorno tracejado em índigo, nos dois temas.
- **Rationale:** segue a spec (FR-004 a FR-009). O limite de 3 px e o seletor `cancel` cobrem o SC-003.
- **Alternatives considered:** arrastar pelo widget inteiro (atrapalha os cliques nas listas); modal de edição à parte
  (a pessoa não veria o resultado no lugar).

## D5. Conteúdo que se ajusta ao widget

- **Decision:** o corpo de cada widget é um contêiner (`@container`), e o conteúdo usa as variantes de contêiner do
  Tailwind v4:
  - **números:** `text-2xl @[10rem]:text-3xl` (a partir de 160 px; o widget padrão tem uns 250 px por dentro numa
    janela de 1280 px, e o número grande tem de continuar como antes);
  - **funil:** `grid-cols-2 @md:grid-cols-3 @4xl:grid-cols-6` (3 colunas a partir de 448 px, 6 a partir de 896 px);
  - **listas** de habilidades, certificações e Suas habilidades: uma coluna; duas a partir de 768 px
    (`@3xl:grid-cols-2`);
  - **rótulos:** continuam com `break-words` e `flex-wrap`, como na 045.
- **Rationale:** o ajuste depende da largura do widget, não da janela (FR-010). As classes por tamanho de tela
  (`sm:`, `lg:`) saem do conteúdo dos widgets.
- **Alternatives considered:** medir a largura em JavaScript e escolher as classes (mais código, e as consultas de
  contêiner já existem no Tailwind v4).

## D6. Telas estreitas

- **Decision:** com o painel abaixo de 768 px de largura (medida por `useContainerWidth`):
  - a grade não é montada;
  - os widgets ficam numa coluna (`flex flex-col gap-4`), ordenados pela posição no layout (linha `y`, depois coluna
    `x`), na altura do conteúdo;
  - sem layout guardado pela pessoa, a coluna segue a ordem padrão (a de antes): a compactação sobe cada widget na sua
    coluna e trocaria, no celular, a ordem dos blocos menores;
  - Organizar painel não aparece, e o modo de edição desliga;
  - o layout guardado não muda.
- **Rationale:** a 768 px, um widget de 3 colunas teria cerca de 180 px. Abaixo disso, a grade deixa de ajudar
  (US3, FR-014).
- **Alternatives considered:** layouts por faixa de largura (`ResponsiveGridLayout`) — a pessoa teria de organizar cada
  faixa, o que a spec não pede.

## D7. Guardar e ler o layout

- **Decision:**
  - **Chave:** `mpt_pref_metricas_layout`, no `ScreenPreferencesService`, com `try/catch` como as outras.
  - **Formato:** `{"versao": 1, "itens": [{"i", "x", "y", "w", "h", "fixa"}]}` (data-model §2).
  - **Leitura tolerante** (`lerLayout`, função pura em `painel/layout.ts`):
    1. o texto ilegível, a versão desconhecida ou a lista vazia dão o padrão;
    2. o item de widget que não existe mais sai;
    3. números inválidos são corrigidos: `w` entre o mínimo e o máximo e `x + w` até 12; `h` entre o mínimo e o máximo;
       `x` e `y` não negativos;
    4. o widget que falta entra no fim (`y` abaixo de tudo), no tamanho padrão, com altura automática;
    5. a compactação vertical estável (D3) tira buracos e sobreposições.
- **Rationale:** FR-012 e FR-013. O formato com versão deixa mudar depois sem quebrar o que está guardado.
- **Alternatives considered:** guardar no servidor (a pessoa escolheu este navegador); guardar só a ordem (perderia
  largura e altura).

## D8. A seção O que as vagas pedem em dez widgets

- **Decision:** `RequisitosVagas.tsx` passa a exportar:
  - `useRequisitos({ vagas, versao })`: seleção, resumo, erro, leitura (ler, parar, andamento), item aberto, Ver todas
    e a aba de habilidades. É o mesmo estado e as mesmas chamadas de hoje;
  - `widgetsRequisitos(r, acoes)`: o conteúdo da barra (título, seletor, contagem, leitura, avisos) e dos nove blocos,
    cada um com id, título, ícone e corpo.
  - Os nove blocos aparecem sempre: sem requisitos lidos, mostram "Ainda não há requisitos lidos nestas vagas", e
    enquanto o resumo carrega, "Montando o resumo…". Hoje alguns somem; com widgets, o layout da pessoa não pode
    pular.
- **Rationale:** os widgets ficam soltos na grade, mas o seletor vale para os nove (edge case da spec). Com o estado num
  hook só, um pedido ao servidor serve a todos.
- **Alternatives considered:**
  - um contexto React (mais cerimônia para um só consumidor);
  - cada bloco pedir o próprio resumo (dez pedidos iguais).

## D9. Ids e tamanhos

- **Decision:** os ids, o layout padrão e os limites estão no data-model §1.
  - O padrão repete o painel da 045: os quatro números lado a lado (3 colunas cada), o funil e a barra na largura toda,
    Habilidades mais pedidas com 8 colunas ao lado de Suas habilidades com 4, os outros blocos com 4 e a Distribuição
    por plataforma na largura toda.
  - Os mínimos garantem o título e o conteúdo principal; os máximos evitam um widget de número maior que a tela.
- **Rationale:** FR-002 e FR-003.

## D10. Conferência

- **Decision:** um script CDP, como o `scratchpad/cdp-045`, com o Edge sem janela e só leituras e cliques de tela.
  1. layout padrão: a ordem e as larguras, e nenhum widget sobreposto;
  2. Organizar painel: aparecem a faixa, as alças e os cantos;
  3. arrastar Suas habilidades pelo título até o topo: `Input.dispatchMouseEvent`;
  4. puxar o canto de Tempo de experiência: largura e altura mudam;
  5. clicar numa habilidade no modo de edição: a lista das vagas abre e nada se move;
  6. recarregar: o layout continua;
  7. Restaurar o padrão, aceitando a confirmação com `Page.handleJavaScriptDialog`;
  8. layout corrompido, widget desconhecido e widget faltando no `localStorage`;
  9. a 360 px: uma coluna, na ordem, sem rolagem para o lado e sem Organizar painel;
  10. capturas de tela no tema claro e no escuro.
- **Rationale:** a `frontend-react` não tem executor de testes; a conferência no navegador cobre a função pura de
  leitura (item 8) e o comportamento. Nunca clica em "Ler os requisitos" nem em "Parar".
