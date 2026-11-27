# Feature Specification: Limpeza de vagas antigas

**Feature Branch**: `054-limpeza-vagas` (worktree saída da `master`)

**Created**: 2026-11-23

**Status**: Draft

**Input**: A pessoa quer limpar as vagas antigas e as que não foram adiante. Depois de algumas semanas de busca, o
banco acumula centenas de vagas que ninguém vai mais olhar: as que furaram os filtros, as que ficaram sem decisão,
as dispensadas, as candidaturas encerradas e as aplicações que nunca tiveram retorno. Elas pesam nas listas, nos
contadores e no tamanho do banco.

Decisões da pessoa:

- os quatro grupos entram, cada um com critério próprio;
- os critérios ficam numa aba nova "Limpeza", nos filtros da busca, junto de Geral, Portais, Portais
  internacionais e Empresas (spec 043);
- o padrão é 30 dias sem movimento;
- a limpeza **arquiva** a vaga, sem apagá-la de vez;
- só roda quando a pessoa pede, sempre com prévia antes de gravar.

## Contexto

- **Apagar não serve.** A busca reconhece uma vaga que já apareceu pelas vagas guardadas (pelos números da vaga nos
  portais e pelos links). Se a vaga for apagada, ela volta como nova na busca seguinte, e a pessoa tria de novo o que
  já tinha descartado.
- **O peso está no texto.** O que ocupa espaço numa vaga é a descrição completa e a análise (resumo, encaixe,
  lacunas, requisitos). O cargo, a empresa, as datas e a decisão da pessoa são poucos bytes.
- **"Sem retorno" é um desfecho.** Uma aplicação parada há semanas não é uma vaga para esquecer: é uma candidatura
  que terminou sem resposta. Hoje não há esse resultado, e ela fica em "Aplicada" para sempre.
- **A data certa.** A data de "última atualização" da vaga muda sozinha: quando a mesma vaga aparece em outro
  portal, quando a análise roda, quando os requisitos são lidos. Ela não diz quando a **pessoa** mexeu na vaga.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver o que pode ser limpo e arquivar (Priority: P1)

A pessoa abre os filtros da busca, vai à aba Limpeza e clica em "Ver o que seria limpo". A ferramenta mostra, por
grupo, as vagas que atendem aos critérios: cargo, empresa, portal e há quantos dias estão paradas. Todas vêm marcadas,
menos as destacadas (US3). A pessoa desmarca o que quiser manter, clica em "Arquivar N vagas" e confirma.

As vagas arquivadas somem das listas (Vagas Nacionais, Vagas Internacionais e Aplicações) e dos contadores. O banco
diminui. Uma busca nova não traz nenhuma delas de volta.

**Why this priority**: é o pedido. Sem a prévia não há limpeza segura; sem arquivar, a busca devolveria o que foi
limpo.

**Independent Test**: com um banco de teste com vagas fictícias em Fora dos critérios há 40 dias e há 10 dias, ver a
prévia com só as de 40 dias; arquivar; ver as listas sem elas e uma busca de teste que traz as mesmas vagas sem
criá-las de novo.

**Acceptance Scenarios**:

1. **Given** vagas em Fora dos critérios há 40 e há 10 dias e o prazo de 30 dias, **When** a pessoa pede a prévia,
   **Then** só as de 40 dias aparecem, e nada é gravado.
2. **Given** a prévia aberta, **When** a pessoa desmarca uma vaga e arquiva, **Then** só as marcadas são arquivadas.
3. **Given** vagas arquivadas, **When** a pessoa abre as listas, **Then** elas não aparecem nas listas nem nos
   contadores.
4. **Given** uma vaga arquivada, **When** a busca encontra a mesma vaga no mesmo portal ou em outro, **Then** ela não
   volta como vaga nova.
5. **Given** a pessoa clica em Arquivar, **When** a gravação começa, **Then** uma cópia do banco é guardada antes.
6. **Given** nenhuma vaga atende aos critérios, **When** a pessoa pede a prévia, **Then** a ferramenta diz que não há
   nada para limpar.

---

### User Story 2 - Critérios próprios para cada grupo (Priority: P1)

Na aba Limpeza, cada grupo tem um interruptor (entra ou não na limpeza) e o prazo em dias sem movimento, com 30 como
padrão. Alguns grupos têm um critério a mais:

| Grupo | Quais vagas | Conta "sem movimento" desde | O que a limpeza faz | Critério a mais |
|---|---|---|---|---|
| Fora dos critérios | as que furaram os filtros da busca | o dia em que caíram em Fora (ou em que foram encontradas) | arquiva | — |
| Pendentes sem decisão | as da busca em que a pessoa nunca decidiu seguir ou não seguir | o dia em que foram encontradas | arquiva | "só com nota abaixo de N" (opcional; vazio = todas) |
| Visitadas e encerradas | as dispensadas e as candidaturas encerradas | o dia em que foram dispensadas ou encerradas | arquiva | quais resultados entram (padrão: todos menos "contratado") |
| Aplicadas sem retorno | as em "Aplicada" | o dia em que passaram para "Aplicada" | **não arquiva**: passa para Encerrada com o resultado "Sem resposta" | — |

A pessoa grava os critérios como grava os outros filtros. A prévia usa os critérios gravados.

**Why this priority**: a pessoa pediu critérios próprios por grupo. Uma vaga em Fora perde o valor em dias; uma
aplicação merece mais paciência.

**Independent Test**: com um banco de teste, desligar o grupo Pendentes e pôr 15 dias em Fora; ver a prévia sem
pendentes e com as vagas de Fora com mais de 15 dias.

**Acceptance Scenarios**:

1. **Given** um grupo desligado, **When** a pessoa pede a prévia, **Then** nenhuma vaga daquele grupo aparece.
2. **Given** prazos diferentes por grupo, **When** a pessoa pede a prévia, **Then** cada grupo usa o próprio prazo.
3. **Given** "só com nota abaixo de 60" no grupo Pendentes, **When** a pessoa pede a prévia, **Then** as pendentes com
   nota 60 ou mais e as ainda sem nota ficam de fora.
4. **Given** o grupo Visitadas e encerradas sem o resultado "não aprovado", **When** a pessoa pede a prévia, **Then**
   as encerradas como não aprovado ficam de fora.
5. **Given** uma aplicação parada há mais que o prazo, **When** a pessoa limpa, **Then** a vaga vai para Encerrada com
   o resultado "Sem resposta", continua em Aplicações e mantém a descrição.
6. **Given** uma configuração sem a parte da Limpeza (instalação antiga), **When** a pessoa abre a aba, **Then** ela
   vê os padrões: os quatro grupos ligados, 30 dias, sem nota mínima, todos os resultados menos "contratado".

---

### User Story 3 - O que tem trabalho da pessoa não some sem ela ver (Priority: P1)

Uma vaga que tem currículo ou carta gerada, ou uma anotação da pessoa, aparece **destacada** na prévia, com o motivo
("tem currículo", "tem anotação"), e vem **desmarcada**. Só é arquivada se a pessoa marcar.

Nunca entram na limpeza:

- vaga em Entrevista ou Proposta;
- vaga encerrada como "contratado";
- vaga adicionada à mão pela pessoa.

**Why this priority**: princípio V, a pessoa decide. Arquivar tira a descrição, e o trabalho em cima de uma vaga não
pode sumir num clique em lote.

**Independent Test**: com uma vaga fictícia em Fora há 40 dias com anotação, ver a vaga destacada e desmarcada na
prévia; arquivar sem marcá-la e ver que ela continua inteira.

**Acceptance Scenarios**:

1. **Given** uma vaga dentro dos critérios com anotação, **When** a pessoa pede a prévia, **Then** a vaga aparece
   destacada, com o motivo, e desmarcada.
2. **Given** a pessoa arquiva sem marcar as destacadas, **When** a gravação termina, **Then** as destacadas continuam
   como estavam.
3. **Given** a pessoa marca uma destacada e arquiva, **When** a gravação termina, **Then** a anotação e os nomes dos
   currículos e das cartas ficam na ficha da vaga arquivada, e os arquivos em `curriculos/` não são apagados.
   *(Mudou na spec 061: arquivar apaga os documentos da vaga, e a ficha guarda só quantos existiam e quando foram
   apagados.)*
4. **Given** uma vaga em Entrevista, Proposta ou contratado parada há meses, **When** a pessoa pede a prévia, **Then**
   ela não aparece.

---

### User Story 4 - Limpar pelo terminal ou pelo chat (Priority: P2)

O mesmo pelo terminal: um comando mostra a prévia por grupo, com os números e as destacadas, sem gravar nada. Com a
opção de gravar, aplica a limpeza nas vagas não destacadas. Com uma opção a mais, aplica também nas destacadas. O
assistente de chat usa o comando para mostrar a prévia e só grava com o OK da pessoa.

**Why this priority**: a ferramenta funciona sem a página (princípio III). Os comandos de revisão do banco que já
existem (filtro de integridade, regiões) seguem esse padrão.

**Independent Test**: rodar o comando num banco de teste e ver a prévia sem nenhuma mudança no banco; rodar com a
opção de gravar e ver só as não destacadas arquivadas.

**Acceptance Scenarios**:

1. **Given** o comando sem opção, **When** ele roda, **Then** mostra a prévia e diz como gravar, sem mudar nada.
2. **Given** a opção de gravar, **When** ele roda, **Then** guarda a cópia do banco, aplica a limpeza nas não
   destacadas e diz quantas vagas foram arquivadas, quantas foram encerradas sem resposta e o tamanho do banco antes e
   depois.

---

### Edge Cases

- **Vaga arquivada que volta na busca:** continua arquivada. Se apareceu num portal novo, ganha a etiqueta desse
  portal, como já acontece com uma vaga repetida.
- **Vaga arquivada que muda na leitura das contas conectadas** (a Gupy diz que ela foi para entrevista): a vaga é
  desarquivada e volta às listas na etapa nova, só com a ficha curta, sem a descrição.
- **Vaga sem a data do grupo** (vaga antiga, de antes de a data existir): usa a data em que foi encontrada; sem
  nenhuma data, não entra na limpeza.
- **A pessoa pede a prévia, muda uma vaga em outra aba e depois arquiva:** a gravação refaz a conta e só aplica nas
  vagas que ainda atendem aos critérios.
- **Aplicada sem retorno com lembrete de follow-up pendente:** entra normalmente. O lembrete deixa de valer quando a
  vaga é encerrada.
- **Relatos ligados a uma vaga arquivada** (spec 035): ficam onde estão; arquivar não mexe nos relatos.
- **Desfazer:** só pela cópia do banco guardada antes da gravação. Não há "desarquivar" com a descrição de volta.
- **Duas vagas iguais em portais diferentes**, uma arquivada e outra não: cada uma segue o próprio critério.

## Requirements *(mandatory)*

### Functional Requirements

**Critérios**

- **FR-001**: A configuração da busca MUST ter a parte Limpeza, com quatro grupos: Fora dos critérios, Pendentes sem
  decisão, Visitadas e encerradas e Aplicadas sem retorno. Cada grupo tem um interruptor e o prazo em dias (de 1 a
  365, padrão 30).
- **FR-002**: O grupo Pendentes MUST aceitar uma nota máxima opcional. Quando preenchida, só entram as pendentes com
  nota abaixo dela; as sem nota ficam de fora.
- **FR-003**: O grupo Visitadas e encerradas MUST aceitar a escolha dos resultados que entram, entre "não aprovado",
  "desisti", "cancelada", "sem resposta" e "sem resultado". O padrão é todos. "Contratado" nunca entra.
- **FR-004**: A configuração sem a parte Limpeza MUST continuar funcionando, com os padrões do FR-001 a FR-003.
- **FR-005**: O "sem movimento" de cada grupo MUST contar a partir da data em que a pessoa (ou a busca) mudou a
  situação da vaga, como na tabela da US2. Se faltar essa data, conta a data em que a vaga foi encontrada. Nunca conta
  a data de última atualização.

**Prévia e gravação**

- **FR-006**: A prévia MUST mostrar, por grupo, cada vaga com cargo, empresa, portal e dias sem movimento, e o total
  por grupo. Não grava nada.
- **FR-007**: Ficam destacadas, desmarcadas e com o motivo as vagas com currículo gerado, carta ou respostas geradas,
  ou anotação.
- **FR-008**: Nunca entram na limpeza: vaga em Entrevista ou Proposta, vaga encerrada como contratado e vaga
  adicionada à mão.
- **FR-009**: A gravação MUST refazer a conta dos critérios e só aplicar nas vagas pedidas que ainda atendem a eles.
- **FR-010**: Antes de gravar, a ferramenta MUST guardar uma cópia do banco. Depois de gravar, MUST reduzir o arquivo
  do banco ao espaço que ele de fato usa.
- **FR-011**: A gravação MUST dizer quantas vagas foram arquivadas, quantas foram encerradas sem resposta e o tamanho
  do banco antes e depois.

**Arquivar**

- **FR-012**: Arquivar MUST deixar na vaga só uma ficha curta:
  - o que a busca e a leitura das contas usam para reconhecer a vaga (os números da vaga nos portais, os links, o
    cargo e a empresa);
  - o portal e os outros portais;
  - a área (nacional ou internacional);
  - as datas;
  - a decisão (triagem, etapa e resultado);
  - a nota e a faixa salarial;
  - a anotação e os nomes dos currículos e documentos;
  - a data do arquivamento.

  Todo o resto (descrição, resumo, encaixe, lacunas, alertas, requisitos e situação da análise) sai.
- **FR-013**: A vaga arquivada MUST continuar sendo reconhecida pela busca, que não a cria de novo.
- **FR-014**: A vaga arquivada MUST ficar fora das listas, dos contadores, da fila de análise, das análises do perfil
  (lacunas) e do resumo do que as vagas pedem. O funil das Métricas continua contando as arquivadas.
- **FR-015**: Se a leitura das contas conectadas mudar a etapa de uma vaga arquivada, a vaga MUST ser desarquivada.

**Sem resposta**

- **FR-016**: O resultado "Sem resposta" MUST existir junto de "não aprovado", "desisti", "cancelada" e "contratado",
  e a pessoa pode escolhê-lo à mão no detalhe da vaga.
- **FR-017**: A limpeza do grupo Aplicadas sem retorno MUST passar a vaga para Encerrada com o resultado "Sem
  resposta", sem arquivar e sem tirar a descrição.

**Onde roda**

- **FR-018** (desde a spec 064, a aba fica no diálogo Buscar vagas): Na página, a aba Limpeza dos filtros da busca MUST ter os critérios, o botão de prévia, a seleção por
  vaga, o botão de arquivar com confirmação e o número de vagas já arquivadas.
- **FR-019**: No terminal, um comando MUST mostrar a prévia e, com a opção de gravar, aplicar a limpeza nas não
  destacadas. Com uma opção a mais, aplica também nas destacadas.
- **FR-020**: A limpeza MUST rodar só quando a pessoa pede. A busca nunca limpa sozinha.

### Key Entities

- **Critério de limpeza**: grupo, ligado ou não, prazo em dias e o critério a mais do grupo (nota máxima; resultados
  que entram).
- **Vaga arquivada**: a ficha curta do FR-012, com a data do arquivamento. Continua reconhecível pela busca e pela
  leitura das contas.
- **Prévia**: os grupos, cada um com as vagas (cargo, empresa, portal, dias sem movimento, destaque e motivo) e o
  total.
- **Resultado "Sem resposta"**: desfecho de uma candidatura que terminou sem retorno da empresa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Num banco de teste com vagas em todos os grupos, a prévia lista 100% das vagas que atendem aos
  critérios e nenhuma que não atenda.
- **SC-002**: Nenhuma vaga com currículo, carta ou anotação é arquivada sem a pessoa marcá-la.
- **SC-003**: Depois de arquivar, uma busca que encontra as mesmas vagas cria zero vagas novas.
- **SC-004**: Num banco de teste em que metade das vagas é arquivada, o arquivo do banco fica pelo menos 40% menor.
- **SC-005**: O funil das Métricas mostra os mesmos números antes e depois da limpeza, contando como Encerradas as
  aplicações que receberam "Sem resposta".
- **SC-006**: Da aba Limpeza até as vagas arquivadas, a pessoa precisa de no máximo três cliques: prévia, arquivar e
  confirmar.

## Assumptions

- Arquivar é guardar a ficha curta no próprio banco, não mover para outro arquivo. Assim a busca e a leitura das
  contas continuam reconhecendo a vaga sem mudança no caminho delas.
- A nota e a faixa salarial ficam na ficha, porque são poucos bytes e mantêm a média de aderência das Métricas e os
  exemplos de faixa salarial.
- "Sem resultado" (a vaga encerrada sem resultado escolhido) é uma opção do grupo Visitadas e encerradas, para a
  pessoa poder deixá-la de fora.
- A cópia do banco é a mesma cópia diária que a ferramenta já guarda, feita na hora se ainda não houver a do dia.
  Para desfazer, a pessoa troca o banco pela cópia, com a página fechada.
- A aba Limpeza é parte da página React (branch `frontend-react`) e chega pelo PR do front, como nas specs
  anteriores.
- Exemplos e testes usam vagas fictícias; nenhum número, empresa ou vaga real da pessoa entra na spec nem nos
  testes (princípio II).
- Fora do escopo:
  - limpeza automática depois da busca;
  - apagar vagas de vez;
  - restaurar a descrição de uma vaga arquivada;
  - uma lista para ver as arquivadas (o número delas aparece na aba).
