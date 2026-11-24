# Feature Specification: Ordenar as listas e ocultar empresas excluídas

**Feature Branch**: `055-ordenar-ocultar` (worktree saída da `master`)

**Created**: 2026-11-23

**Status**: Draft

**Input**: A pessoa quer ordenar as vagas nas telas que as mostram (por nota, data do anúncio etc.) e ter uma caixa
"Ocultar vagas de empresas excluídas".

Decisões da pessoa:

- as Aplicações ganham ordenação no quadro e na lista;
- as três telas (Vagas Nacionais, Vagas Internacionais e Aplicações) ganham opções novas de ordem;
- a caixa de ocultar vale em todas as listas.

## Contexto

- **O que já existe.** Vagas Nacionais e Vagas Internacionais já ordenam por maior aderência, mais recentes (pela
  data do anúncio), plataforma e modo de trabalho. A escolha fica lembrada por área. Aplicações não tem ordenação: os
  cartões saem na ordem em que estão no banco.
- **Empresas excluídas.** A lista de exclusão fica nos Filtros da busca, aba Empresas. Uma vaga nova de uma dessas
  empresas vai para Fora dos critérios, quando chega pela busca ou pela análise. Mas a vaga que já estava gravada
  quando a empresa entrou na lista continua onde estava: em Para decidir, em Seguidas ou em Aplicações. E as que foram
  para Fora continuam aparecendo lá, misturadas com as outras.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ordenar as Aplicações (Priority: P1)

Em Aplicações, um seletor "Ordenar" muda a ordem dos cartões dentro de cada coluna do quadro e a ordem das linhas na
visão em lista. As opções são:

- na etapa há menos tempo (padrão);
- na etapa há mais tempo;
- maior aderência;
- menor aderência;
- anúncio mais recente;
- encontrada mais recente;
- empresa (A–Z);
- plataforma.

A escolha fica lembrada neste navegador.

**Why this priority**: as Aplicações são onde a pessoa acompanha as candidaturas, e hoje não dá para ver primeiro a
que está parada há mais tempo ou a de nota mais alta.

**Independent Test**: com três candidaturas fictícias em Aplicação Enviada, com datas de etapa diferentes:

- "na etapa há mais tempo" põe a mais antiga no topo da coluna;
- recarregar a página mantém a escolha.

**Acceptance Scenarios**:

1. **Given** cartões numa coluna, **When** a pessoa escolhe uma ordem, **Then** os cartões de cada coluna seguem essa
   ordem, no quadro e na lista.
2. **Given** a ordem por aderência, **When** há vagas sem nota, **Then** elas ficam no fim.
3. **Given** a ordem por data, **When** há vagas sem a data, **Then** elas ficam no fim.
4. **Given** a pessoa escolheu uma ordem, **When** recarrega a página, **Then** a ordem continua a mesma.
5. **Given** a pessoa arrasta um cartão para outra coluna, **When** a coluna é ordenada, **Then** o cartão vai para a
   posição que a ordem manda. O arrastar continua mudando só a etapa.

---

### User Story 2 - Mais opções de ordem nas Vagas (Priority: P2)

Vagas Nacionais e Vagas Internacionais ganham três opções, além das que já existem:

- menor aderência;
- encontrada mais recente (o dia em que a busca trouxe a vaga);
- empresa (A–Z).

**Why this priority**: completa o pedido ("nota, data do anúncio etc.") nas telas que já ordenam.

**Independent Test**: com vagas fictícias de empresas e datas diferentes, "Empresa (A–Z)" põe a de nome com "A" no
topo, e "Encontrada mais recente" põe primeiro a encontrada por último.

**Acceptance Scenarios**:

1. **Given** as vagas de uma sub-aba, **When** a pessoa escolhe "Menor aderência", **Then** a de menor nota vem
   primeiro e as sem nota ficam no fim.
2. **Given** "Empresa (A–Z)", **When** os nomes têm acento ou maiúsculas, **Then** a ordem é a do português ("Álvaro"
   junto de "Alvo").
3. **Given** a escolha numa área, **When** a pessoa recarrega a página, **Then** a escolha continua, como já acontece
   com as opções de hoje.

---

### User Story 3 - Ocultar as vagas de empresas excluídas (Priority: P1)

Em Vagas Nacionais, Vagas Internacionais e Aplicações, uma caixa "Ocultar vagas de empresas excluídas" esconde as
vagas cuja empresa está **hoje** na lista de exclusão dos Filtros da busca. Isso vale em todas as sub-abas, inclusive
Fora dos critérios.

- A caixa vem marcada e fica lembrada neste navegador.
- Quando ela esconde alguma vaga da tela, aparece "N vaga(s) de empresas excluídas ocultas".
- A empresa conta como excluída pela mesma regra da busca: o nome da lista aparece no nome da empresa da vaga, sem
  diferenciar acento e maiúsculas.

**Why this priority**: a pessoa excluiu a empresa para não ver as vagas dela, e elas continuam aparecendo.

**Independent Test**: com "Empresa Beta" na lista de exclusão e uma vaga fictícia dela em Para decidir:

- a caixa marcada esconde a vaga e mostra "1 vaga de empresas excluídas oculta";
- desmarcada, a vaga volta.

**Acceptance Scenarios**:

1. **Given** uma vaga de empresa excluída em qualquer sub-aba ou coluna, **When** a caixa está marcada, **Then** a
   vaga não aparece.
2. **Given** a caixa desmarcada, **When** a pessoa olha as listas, **Then** a vaga aparece como hoje.
3. **Given** a pessoa tira a empresa da lista de exclusão e grava os filtros, **When** as vagas são relidas, **Then** a
   vaga volta a aparecer, mesmo com a caixa marcada.
4. **Given** a caixa marcada numa tela, **When** a pessoa vai a outra tela, **Then** a caixa está marcada lá também
   (a escolha é uma só).
5. **Given** a lista de exclusão vazia, **When** a pessoa olha as listas, **Then** a caixa não esconde nada e o aviso
   não aparece.

---

### Edge Cases

- **Nome curto na lista de exclusão** (ex.: "Ita"): a regra é a mesma da busca, por trecho, então também esconde
  "Itaú". É o comportamento que a busca já tem com essa lista, e a pessoa vê o número de ocultas.
- **Vaga sem empresa** ("Empresa confidencial"): só é escondida se a lista tiver esse texto.
- **Contadores do menu** (as quantidades nas abas): continuam contando todas as vagas, porque a caixa é um filtro de
  visão, como a busca por texto.
- **Métricas & Funil**: não mudam com a caixa.
- **Detalhe da vaga aberto** quando a caixa esconde a vaga: o detalhe continua aberto. A vaga só some da lista.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aplicações MUST ter o seletor "Ordenar", com as oito opções da US1. Ele vale para o quadro (dentro de
  cada coluna) e para a lista.
- **FR-002**: Vagas Nacionais e Vagas Internacionais MUST ganhar "Menor aderência", "Encontrada mais recente" e
  "Empresa (A–Z)", mantendo as opções e o padrão de hoje.
- **FR-003**: Em toda ordem, a vaga sem o dado usado (nota ou data) MUST ir para o fim. O empate MUST ser resolvido
  pela maior nota e depois pelo anúncio mais recente, como as Vagas já fazem.
- **FR-004**: A escolha de ordem MUST ficar lembrada neste navegador: em Aplicações, uma só; nas Vagas, por área, como
  hoje.
- **FR-005**: Cada vaga que a página recebe MUST dizer se a empresa dela está hoje na lista de exclusão, pela mesma
  regra que a busca usa.
- **FR-006**: Vagas Nacionais, Vagas Internacionais e Aplicações MUST ter a caixa "Ocultar vagas de empresas
  excluídas", marcada por padrão, com uma escolha só para as três telas, lembrada neste navegador.
- **FR-007**: Com a caixa marcada e alguma vaga escondida na tela atual, a tela MUST mostrar quantas foram ocultadas.
- **FR-008**: A caixa MUST NOT mudar dados: nenhuma vaga muda de triagem, etapa ou lista por causa dela.

### Key Entities

- **Ordem**: a opção escolhida. É uma por tela, e nas Vagas uma por área.
- **Marca de empresa excluída**: um atributo calculado da vaga (sim ou não), conforme a lista de exclusão atual.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em Aplicações, a pessoa põe no topo da coluna a candidatura parada há mais tempo com uma escolha só.
- **SC-002**: 100% das vagas de empresas da lista de exclusão somem das três telas com a caixa marcada, e 100% voltam
  com ela desmarcada.
- **SC-003**: A escolha de ordem e a da caixa sobrevivem a recarregar a página.
- **SC-004**: Nenhuma vaga muda de lugar no banco por causa da ordem ou da caixa.

## Assumptions

- "Lembrada neste navegador" usa o mesmo mecanismo das preferências de hoje das Vagas; trocar de navegador volta ao
  padrão.
- A marca de empresa excluída é calculada pelo servidor a cada leitura (como o checklist), e não gravada. Assim,
  mudar a lista de exclusão vale na leitura seguinte, sem rever o banco.
- Reclassificar para Fora dos critérios as vagas antigas de empresas excluídas fica fora do escopo. Pode ir para a
  lista de desejos.
- Os testes usam empresas fictícias (princípio II).
