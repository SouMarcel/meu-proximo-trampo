# Feature Specification: Widgets reorganizáveis no painel Métricas & Funil

**Feature Branch**: `046-widgets-metricas` (worktree saída da `master` com a 045; testada na branch pessoal antes da
`master`)

**Created**: 2026-11-03

**Status**: Concluída em 2026-11-03 (validada pela pessoa na branch pessoal)

**Input**: User description: "é possivel transofrmar os itens dash em widgets onde podemos reorganizar da forma que
achar melhor? trocar de lugar, lagura e altura, e os itens de cada widgeth se ajustar internamente?" (03/11/2026).
Decisões da mesma data em Clarifications.

## Contexto

- **O painel Métricas & Funil, com a spec 045, tem 16 blocos numa ordem fixa:**
  1. quatro números: Total rastreadas, Conversão para entrevista, Média de aderência e Ofertas & propostas;
  2. o funil, de Descobertas a Contratado;
  3. a barra de O que as vagas pedem: o título, o seletor (Vagas e Área), a linha de contagem e a leitura dos
     requisitos;
  4. nove blocos:
     - Habilidades mais pedidas;
     - Suas habilidades;
     - Certificações e cursos;
     - Tempo de experiência;
     - Formação;
     - Idiomas;
     - Senioridade;
     - Modelo de trabalho;
     - Tipo de contratação;
  5. a Distribuição por plataforma.
- **A largura de cada bloco é fixa** e segue a tela: uma coluna no celular, duas ou três no computador. A altura acompanha o
  conteúdo. Quem quer ver primeiro, por exemplo, Suas habilidades ou o Tempo de experiência precisa rolar a página.

## Clarifications

### Session 2026-11-03

- Q: Onde os widgets reorganizáveis existem? → A: Só no painel Métricas & Funil. As listas de vagas, Aplicações e o
  Preparador de Entrevistas ficam como estão.
- Q: Como a pessoa mexe nos widgets? → A: Arrastando para trocar de lugar e puxando o canto para mudar a largura e a
  altura, num modo de edição.
- Q: Onde o layout fica guardado? → A: Neste navegador, como os filtros e a ordem das listas.
- Q: E a spec 045? → A: Vai antes para a `master`, com os ajustes do teste; a 046 começa sobre ela.

### Decisões do plano (2026-11-03)

- **Altura:** a altura de cada widget acompanha o conteúdo, como hoje, até a pessoa mudá-la pelo canto. Daí em diante,
  fica fixa, e o widget mostra no modo de edição o botão **Altura do conteúdo**, que desfaz isso (FR-002, FR-006).
- **Tela estreita:** abaixo de 768 px de largura do painel (FR-014).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Montar o painel do seu jeito (Priority: P1)

A pessoa clica em **Organizar painel**. Cada bloco vira um widget com uma alça de arrastar e um canto de
redimensionar. Ela arrasta Suas habilidades para o topo, ao lado de Habilidades mais pedidas, alarga o Tempo de
experiência e encolhe a Distribuição por plataforma. Os outros widgets abrem espaço sozinhos, sem sobrepor. Ela clica
em **Concluir**, e o painel fica assim, inclusive depois de recarregar a página.

**Why this priority**: é o pedido: pôr à vista o que importa para a pessoa, no tamanho que ela quer.

**Independent Test**: em Organizar painel, trocar dois widgets de lugar e mudar a largura e a altura de um terceiro.
Concluir e recarregar a página: o layout continua o mesmo.

**Acceptance Scenarios**:

1. **Given** o painel no layout padrão, **When** a pessoa clica em Organizar painel, **Then** cada widget mostra a alça
   e o canto de redimensionar, e o painel avisa que está em edição, com Concluir e Restaurar o padrão.
2. **Given** o modo de edição, **When** a pessoa arrasta um widget para outro lugar, **Then** ele se encaixa na grade e
   os outros se movem para abrir espaço, sem se sobrepor.
3. **Given** o modo de edição, **When** a pessoa puxa o canto de um widget, **Then** a largura e a altura mudam em
   passos da grade, entre o mínimo e o máximo daquele widget.
4. **Given** o layout mudado, **When** a pessoa clica em Concluir e recarrega a página, **Then** o painel abre no layout
   dela.
5. **Given** um layout montado, **When** a pessoa clica em Restaurar o padrão e confirma, **Then** o painel volta ao
   layout de fábrica.
6. **Given** o modo de edição, **When** a pessoa clica num item dentro de um widget, por exemplo uma habilidade,
   **Then** nada é arrastado por engano: só a alça arrasta.

---

### User Story 2 - O conteúdo se ajusta ao tamanho do widget (Priority: P1)

Num widget estreito, o conteúdo fica compacto: números menores, uma coluna, rótulos que quebram a linha. Num widget
largo, ele se espalha: listas em duas colunas, barras mais longas, o funil numa linha só. Quando o conteúdo passa da
altura que a pessoa escolheu, ele rola dentro do widget, sem cortar e sem empurrar os outros.

**Why this priority**: sem isso, mudar o tamanho só cortaria ou esticaria o conteúdo, e o widget ficaria ruim de ler.

**Independent Test**: encolher Habilidades mais pedidas até o mínimo e alargá-la até o máximo. Nos dois casos, tudo
fica legível. Baixar a altura de Suas habilidades: a lista rola dentro do widget.

**Acceptance Scenarios**:

1. **Given** o funil num widget estreito, **When** a pessoa olha, **Then** as seis etapas aparecem em duas ou três
   colunas, sem rolagem para o lado.
2. **Given** o funil no widget da largura toda, **When** a pessoa olha, **Then** as seis etapas ficam numa linha.
3. **Given** uma lista longa num widget baixo, **When** a pessoa rola dentro dele, **Then** a lista inteira aparece, e o
   resto do painel não se mexe.
4. **Given** a lista das vagas de um item aberta dentro de um widget, **When** ela passa da altura, **Then** rola dentro
   do widget.

---

### User Story 3 - No celular, uma coluna na ordem escolhida (Priority: P2)

Em telas estreitas, como o celular, os widgets ficam numa coluna só, na ordem em que a pessoa os deixou (de cima para
baixo, da esquerda para a direita), cada um na altura do seu conteúdo. Organizar painel não aparece nessas telas,
porque arrastar ali é difícil.

**Why this priority**: o layout é feito para o computador, mas o painel continua útil no celular.

**Independent Test**: montar um layout no computador e estreitar a janela até cerca de 360 px. Os widgets aparecem numa
coluna, na ordem do layout, sem rolagem para o lado.

**Acceptance Scenarios**:

1. **Given** um layout com Suas habilidades no topo, **When** a tela fica estreita, **Then** Suas habilidades é o
   primeiro widget da coluna.
2. **Given** a tela estreita, **When** a pessoa procura Organizar painel, **Then** o botão não aparece, e o layout dela
   fica guardado para quando voltar à tela larga.

---

### Edge Cases

- **Layout guardado de uma versão antiga da ferramenta:**
  - um widget novo que a ferramenta ganhar entra no fim, no tamanho padrão;
  - um widget que deixou de existir sai do layout;
  - o resto fica como a pessoa deixou.
- **Layout guardado ilegível** (apagado, corrompido, navegador sem armazenamento): o painel abre no padrão, sem erro.
- **Widget no tamanho mínimo:** o mínimo de cada widget garante que o título e o conteúdo principal caibam (por exemplo,
  o número inteiro num widget de número).
- **Seletor de O que as vagas pedem:** a barra com o seletor e a leitura também é um widget. O seletor vale para os
  nove blocos onde quer que eles estejam, e a leitura continua mostrando o andamento.
- **Leitura dos requisitos rodando durante a edição:** a leitura não para, e os números se atualizam nos widgets.
- **Sem requisitos lidos:** os widgets que dependem deles aparecem com o aviso de hoje, no tamanho que a pessoa deu.
- **Organizar e sair sem Concluir** (trocar de aba): o que já foi mexido fica guardado, como em Concluir.
- **Tema claro e escuro:** a alça, o canto de redimensionar e o contorno de edição aparecem nos dois.

## Requirements *(mandatory)*

### Functional Requirements

**Widgets e grade**

- **FR-001**: O painel Métricas & Funil MUST mostrar os 16 blocos como widgets numa grade:
  - os 4 números, um widget cada;
  - o funil;
  - a barra de O que as vagas pedem;
  - os 9 blocos dela;
  - a Distribuição por plataforma.
- **FR-002**: O layout padrão MUST reproduzir o painel de hoje (spec 045), na mesma ordem e com larguras parecidas, para
  quem nunca organizou não perceber diferença além do botão Organizar painel. A altura de cada widget acompanha o
  conteúdo, como hoje, até a pessoa mudá-la (FR-006).
- **FR-003**: Cada widget MUST ter um tamanho mínimo e um máximo, na largura e na altura, que mantêm o conteúdo legível.

**Modo de edição**

- **FR-004**: O botão **Organizar painel**, no topo do painel, MUST ligar o modo de edição. Nele:
  - cada widget mostra uma alça de arrastar no título e um canto de redimensionar;
  - o painel mostra "Organizando o painel: arraste pelo título e puxe o canto para mudar o tamanho", com **Concluir** e
    **Restaurar o padrão**.
- **FR-005**: Arrastar um widget pela alça MUST trocá-lo de lugar, encaixado na grade. Os outros widgets abrem espaço,
  sem sobreposição e sem buracos no alto do painel: o que fica embaixo sobe.
- **FR-006**: Puxar o canto MUST mudar a largura e a altura em passos da grade, entre o mínimo e o máximo do widget.
  - A altura mudada pela pessoa fica fixa; mudar só a largura não fixa a altura.
  - No modo de edição, o widget de altura fixa mostra **Altura do conteúdo**, que volta a altura a acompanhar o
    conteúdo.
- **FR-007**: No modo de edição, só a alça arrasta. Botões, listas e itens dentro do widget continuam funcionando com o
  clique.
- **FR-008**: Fora do modo de edição, os widgets MUST NOT se mover: não há alça nem canto, e o painel funciona como
  hoje.
- **FR-009**: **Restaurar o padrão** MUST pedir confirmação e voltar ao layout padrão.

**Conteúdo**

- **FR-010**: O conteúdo de cada widget MUST se ajustar à largura do próprio widget, e não à da janela:
  - **números:** o valor diminui num widget estreito;
  - **funil:** as etapas se arranjam em 2, 3 ou 6 colunas;
  - **listas:** ficam em uma coluna, ou em duas num widget largo;
  - **rótulos:** os longos quebram a linha.
- **FR-011**: Quando o conteúdo passa da altura fixa do widget (ou do máximo dele), ele MUST rolar dentro do widget, sem
  cortar e sem mexer nos outros. Vale também para a lista das vagas de um item aberta dentro dele. Com a altura que
  acompanha o conteúdo, o widget cresce (Ver todas, lista das vagas) e os de baixo descem, como hoje.

**Guardar**

- **FR-012**: O layout MUST ficar guardado neste navegador a cada mudança, e o painel MUST abrir no layout guardado.
- **FR-013**: O layout guardado MUST tolerar mudanças da ferramenta: o widget novo entra no fim, no tamanho padrão; o que
  deixou de existir sai; o ilegível dá lugar ao padrão.

**Telas estreitas**

- **FR-014**: Em telas estreitas (painel com menos de 768 px, como no celular), os widgets MUST ficar numa coluna, na ordem do layout (de cima para baixo, da
  esquerda para a direita), cada um na altura do seu conteúdo. Organizar painel não aparece, e o layout guardado não
  muda.

**Geral**

- **FR-015**: O modo de edição MUST funcionar no tema claro e no escuro, e a página MUST continuar sem rolagem para o lado
  a 360 px.
- **FR-016**: README e README do dashboard MUST descrever Organizar painel, Restaurar o padrão e que o layout fica neste
  navegador.

### Key Entities

- **Widget:** um bloco do painel. Tem um nome fixo (ex.: "suas-habilidades"), um título, um tamanho padrão e um tamanho
  mínimo e máximo.
- **Layout:** a posição e o tamanho de cada widget na grade. Guardado neste navegador.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A pessoa troca dois widgets de lugar e muda o tamanho de um terceiro em menos de 1 minuto, e o layout
  continua o mesmo depois de recarregar a página.
- **SC-002**: Em 100% dos widgets, no tamanho mínimo e no máximo, o conteúdo fica legível, sem texto cortado e sem
  rolagem para o lado; o que passa da altura rola dentro do widget.
- **SC-003**: Nenhum clique dentro de um widget arrasta o widget por engano, no modo de edição ou fora dele.
- **SC-004**: Restaurar o padrão devolve o layout de fábrica em um clique e uma confirmação.
- **SC-005**: A 360 px, o painel mostra todos os widgets numa coluna, na ordem do layout, sem rolagem para o lado.
- **SC-006**: Quem nunca organizou o painel vê o mesmo painel de antes, mais o botão Organizar painel.

## Assumptions

- A grade tem 12 colunas no computador e passos de 4 px de altura. Os tamanhos padrão, mínimos e máximos de cada
  widget estão no plano (data-model §1).
- O layout é guardado por navegador. Outro navegador ou outro computador abre no padrão, por decisão da pessoa.
- **Fica de fora** (pode virar uma spec depois):
  - esconder e mostrar widgets;
  - vários layouts com nome;
  - organizar pelo teclado;
  - widgets nas outras abas.
- A biblioteca de arrastar e redimensionar (react-grid-layout, MIT) entra só na página (`frontend-react`), no build
  da Action. A pessoa continua sem precisar de Node, e o servidor e os dados não mudam. O motivo e as alternativas estão
  no research D1 (constituição III).
- A 046 vai para a `master` depois da 045.
