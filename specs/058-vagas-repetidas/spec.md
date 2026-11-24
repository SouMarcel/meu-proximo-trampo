# Feature Specification: A mesma vaga em vários portais

**Feature Branch**: `058-vagas-repetidas` (a partir da `057-forcar-com-descricao`)

**Created**: 2026-11-24

**Status**: Draft

**Input**: A pessoa notou que uma vaga do JobGether leva à candidatura na Gupy. No banco, a mesma vaga apareceu três
vezes:

- pela busca na Gupy, com a empresa "Alfaweb", com descrição e nota, em Aplicações;
- pelo Atualizar candidaturas, com a empresa "Seja Alfaweb", sem descrição, em Aplicações;
- pelo JobGether, com a empresa "Alfaweb Corp", sem descrição e com nota provisória, em Para decidir.

A ferramenta reconhece a mesma vaga em outro portal pelo número da vaga, pelo link ou por cargo + empresa
**idênticos**. A empresa veio escrita de três jeitos, e o link da Gupy só aparece na página do JobGether, que a
ferramenta não lê.

Decisões da pessoa:

- juntar por empresa parecida;
- colar o link do anúncio original;
- revisar as repetidas já gravadas;
- mostrar as etiquetas de todos os portais em que a vaga foi anunciada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Empresa escrita de outro jeito é a mesma empresa (Priority: P1)

A mesma vaga é reconhecida quando o cargo é igual e um nome de empresa contém o outro, depois de tirar o que só muda a
escrita:

- maiúsculas e acentos;
- pontuação;
- sufixos societários: Ltda, S.A., SA, ME, EIRELI, Inc, LLC, Ltd, Corp, Corporation, Co., Group, Grupo, Holding;
- palavras de página de carreira: "Seja", "Carreiras", "Trabalhe na/no".

Assim, "Alfaweb", "Alfaweb Corp" e "Seja Alfaweb" são a mesma empresa.

O nome **contido**, e não igual, só junta vagas de **portais diferentes**, ou quando uma delas veio do Atualizar
candidaturas. Na prévia com o banco real, três vagas de Scrum Master da "Omega Data North America", da "Omega Data, Inc." e
da "Omega Data Europe & Latam", todas do LinkedIn, são vagas diferentes, de regiões diferentes. No mesmo portal, continua
a regra de hoje, com o nome-base igual.

A regra vale nas três entradas:

- a busca: a vaga nova vira etiqueta da que já existe;
- o Adicionar Vaga;
- o Atualizar candidaturas: a candidatura casa com a vaga já no dashboard.

O prazo de 60 dias da regra de hoje continua.

**Acceptance Scenarios**:

1. **Given** "SCRUM MASTER PL | Alfaweb" no dashboard, **When** a busca traz "Scrum Master PL | Alfaweb Corp" de
   outro portal, **Then** não entra vaga nova, e a vaga que existe ganha a etiqueta do portal e o número da vaga nova.
2. **Given** a candidatura "Scrum Master PL | Seja Alfaweb" lida na Gupy, **When** a pessoa atualiza as candidaturas,
   **Then** ela casa com a vaga "Alfaweb" que já existe.
3. **Given** "Analista | Ita" e "Analista | Itaú", **When** a busca roda, **Then** elas **não** são juntadas: o nome
   contido precisa ter pelo menos 5 letras.
4. **Given** cargos diferentes ("Scrum Master PL" e "Scrum Master SR") na mesma empresa, **When** a busca roda,
   **Then** as vagas continuam separadas.

### User Story 2 - Colar o link do anúncio original (Priority: P1)

No detalhe da vaga, o campo "Link do anúncio original" recebe o link para onde o portal leva a candidatura. Exemplo:
o link da Gupy que o JobGether mostra. A ferramenta lê esse link como o Adicionar Vaga lê, com os mesmos portais e
limites, e:

- **a vaga daquele link já está no dashboard:** a vaga atual é **juntada** a ela. A existente ganha a etiqueta do
  portal e o número desta, e esta sai das listas;
- **não está:** a vaga atual ganha a descrição lida, o link de candidatura e a etiqueta do portal do link, e entra
  na fila de verificação.

**Acceptance Scenarios**:

1. **Given** a vaga do JobGether sem descrição e o link da Gupy de uma vaga que já está em Aplicações, **When** a
   pessoa cola o link, **Then** a vaga do JobGether é juntada à da Gupy, que passa a mostrar as etiquetas Gupy e
   JobGether.
2. **Given** um link da Gupy de uma vaga que não está no dashboard, **When** a pessoa cola, **Then** a vaga ganha a
   descrição da Gupy e entra na fila de nota.
3. **Given** um link que a ferramenta não consegue ler, **When** a pessoa cola, **Then** aparece o motivo, e nada muda.

### User Story 3 - Revisar as repetidas que já estão gravadas (Priority: P2)

Uma prévia lista os grupos de vagas repetidas já no banco, pela regra da US1 (mais o número da vaga e o link). Para
cada grupo, ela indica a vaga que fica, a **principal**, pela ordem abaixo:

1. a que está em Aplicações;
2. a que tem descrição;
3. a que tem nota definitiva;
4. a mais antiga.

Com o OK da pessoa, as outras vagas do grupo são **juntadas** à principal.

Ao juntar, a principal ganha:

- as etiquetas e os números de vaga das outras;
- a descrição, se não tinha;
- a etapa mais adiantada, com a data e o resultado;
- as anotações, somadas;
- os currículos e os documentos das outras.

As outras saem das listas, guardadas como ficha curta com `juntada_a` (como o arquivamento da spec 054), para a busca
continuar reconhecendo os números delas.

Onde fica a revisão:

- na aba Limpeza dos filtros, a seção "Vagas repetidas", com a prévia e "Juntar N grupos";
- no terminal, `PY dash/banco.py repetidas [--gravar]`.

**Acceptance Scenarios**:

1. **Given** as três vagas da Alfaweb, **When** a pessoa abre a prévia, **Then** elas aparecem num grupo, com a da
   busca da Gupy (descrição e nota, em Aplicações) como principal.
2. **Given** o OK, **When** junta, **Then** a principal mostra as etiquetas Gupy e JobGether, e as outras somem das
   listas.
3. **Given** a prévia, **When** a pessoa não confirma, **Then** nada muda.

### User Story 4 - As etiquetas de todos os portais (Priority: P1)

O cartão (Vagas Nacionais, Vagas Internacionais e Aplicações) e o detalhe mostram, além do portal da vaga, uma
etiqueta para cada outro portal em que ela foi anunciada.

**Acceptance Scenarios**:

1. **Given** uma vaga da Gupy também vista no JobGether, **When** a pessoa vê o cartão, **Then** aparecem as
   etiquetas "Gupy" e "JobGether".

### Edge Cases

- **Duas vagas do mesmo portal, com números diferentes e o mesmo cargo e empresa** (repostagem): seguem a regra de
  hoje, juntadas dentro dos 60 dias.
- **Empresa genérica** ("Empresa confidencial", "Empresa não informada"): nunca entra na regra (como hoje).
- **Juntar duas vagas em Aplicações com etapas diferentes:** fica a etapa mais adiantada. A prévia mostra isso antes.
- **Desfazer:** a junção na revisão é precedida da cópia do banco (spec 054).

## Requirements *(mandatory)*

- **FR-001**: O reconhecimento da mesma vaga MUST aceitar cargo igual e empresa contida, pelo nome-base (sem caixa,
  acento, pontuação, sufixo societário e palavras de página de carreira), com pelo menos 5 letras no nome contido.
  Isso vale na busca, no Adicionar Vaga e no Atualizar candidaturas.
- **FR-002**: O detalhe da vaga MUST aceitar o link do anúncio original: juntar à vaga que já existe ou completar a
  vaga atual com a descrição, o link de candidatura e a etiqueta.
- **FR-003**: A revisão MUST mostrar os grupos e a principal antes de gravar, e juntar só com o OK, depois da cópia do
  banco.
- **FR-004**: Juntar MUST manter na principal tudo o que a pessoa fez nas outras: etapa mais adiantada, anotações,
  currículos e documentos.
- **FR-005**: A vaga juntada MUST continuar sendo reconhecida pela busca e sair das listas.
- **FR-006**: O cartão e o detalhe MUST mostrar as etiquetas de todos os portais da vaga.

## Success Criteria *(mandatory)*

- **SC-001**: As três vagas da Alfaweb viram uma só, com as etiquetas Gupy e JobGether.
- **SC-002**: Uma busca depois da junção não recria nenhuma das vagas juntadas.
- **SC-003**: Nenhum par de empresas com nome-base de menos de 5 letras é juntado.

## Assumptions

- A regra da empresa contida vale só com o cargo igual, depois da normalização de hoje. Não há junção por cargo
  parecido.
- A leitura do link original usa o mesmo leitor do Adicionar Vaga (`link.ler`), com os mesmos portais, pausas e
  bloqueios. Os termos de cada portal seguem as decisões já registradas.
- Os testes usam empresas fictícias (princípio II).
