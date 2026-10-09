# Feature Specification: Buscar vagas pela página

**Feature Branch**: `005-buscar-pela-pagina` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 4 do roteiro: buscar vagas pela página. Hoje a busca só roda
pelo terminal ou pela skill de chat. Na aba Relatório de Vagas, um botão Buscar vagas roda a busca
com os filtros gravados em segundo plano, uma por vez, mostrando o progresso (consulta atual,
vagas achadas, portais) e permitindo cancelar; ao terminar, grava no relatório e mostra o resumo
(encontradas, novas, fora dos critérios, repetidas). Com IA configurada, as vagas novas recebem a
nota pela IA escolhida, em lotes, com o mesmo pedido da análise automática; sem IA, gravam sem nota
e a página diz isso. Sem filtros ou sem perfil, a página orienta antes de buscar. Respeito aos
portais: intervalo mínimo entre buscas e aviso se a última foi há pouco. A busca pelo terminal e
pela skill continua igual e não roda junto com a da página. Escrita só do próprio computador. Foco
em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar vagas com um clique (Priority: P1)

Na aba Relatório de Vagas, a pessoa clica em **Buscar vagas**. Antes de começar, a página mostra o
que vai acontecer: quantas consultas, em quais portais, com quais cargos, a janela de publicação e,
se houver IA, que as vagas novas vão receber nota pela IA escolhida (e se ela cobra por uso). A
pessoa confirma; a busca roda em segundo plano e a página mostra o andamento: o portal e o cargo da
consulta atual, quantas consultas faltam e quantas vagas apareceram até agora. Ao terminar, as
vagas novas aparecem no relatório, e um resumo diz quantas foram encontradas, quantas são novas
para decidir, quantas ficaram fora dos critérios e quantas já estavam no dashboard.

**Why this priority**: hoje a busca exige terminal ou chat; quem usa só a página não consegue
buscar vagas, que é a função principal da ferramenta.

**Independent Test**: com filtros gravados e sem IA, clicar em Buscar vagas, confirmar, acompanhar o
andamento e, no fim, ver as vagas novas no relatório e o resumo, sem abrir terminal nem chat.

**Acceptance Scenarios**:

1. **Given** filtros da busca gravados, **When** a pessoa clica em Buscar vagas, **Then** a página
   mostra o plano (consultas, portais, cargos, janela, IA) e pede confirmação; nada sai antes dela.
2. **Given** a busca confirmada, **When** ela roda, **Then** o andamento é atualizado a cada
   consulta concluída e o resto da página (abas, quadro, filtros) continua usável.
3. **Given** a busca termina, **When** as vagas são gravadas, **Then** as novas aparecem no
   relatório e o resumo mostra encontradas, novas, fora dos critérios, já vistas, cortadas pelo
   título e fora da janela, junto com os avisos dos portais (erro, provável bloqueio).
4. **Given** uma busca em andamento, **When** a pessoa fecha e reabre a página, **Then** ela vê o
   andamento (ou o resultado, se já terminou).

---

### User Story 2 - Nota das vagas novas pela IA escolhida (Priority: P1)

Com IA configurada no painel IA, as vagas novas dentro dos critérios recebem a nota de aderência ao
perfil pela IA escolhida, em lotes, com o mesmo pedido da análise automática que já existe. A
página mostra "IA analisando n de N" e, no fim, as notas no relatório. Sem IA, as vagas são gravadas
sem nota e a página diz isso e como obtê-la (escolher uma IA ou pedir a análise no chat). Se a IA
falhar, as vagas continuam gravadas, sem nota, com o motivo visível e a opção de tentar de novo.

**Why this priority**: a nota é o que torna o relatório útil para decidir; sem ela a busca pela
página entrega só uma lista.

**Independent Test**: com uma IA falsa local, buscar e ver as vagas novas com nota; trocar para
"sem IA", buscar de novo e ver as vagas sem nota, sem nenhum pedido ao provedor.

**Acceptance Scenarios**:

1. **Given** IA configurada, **When** a busca grava vagas novas dentro dos critérios, **Then** elas
   recebem nota em lotes e a página mostra o andamento da análise.
2. **Given** a ferramenta sem IA, **When** a busca grava, **Then** as vagas ficam sem nota, nada é
   enviado a provedores e a página explica como ter a nota.
3. **Given** a IA falha no meio da análise, **When** a busca termina, **Then** as vagas continuam no
   relatório, as que ficaram sem nota mostram o motivo e há como tentar de novo.
4. **Given** vagas fora dos critérios, **When** a busca grava, **Then** elas vão para a aba Fora dos
   critérios sem passar pela IA, como hoje.

---

### User Story 3 - Orientação antes da primeira busca (Priority: P2)

Sem cargos nos filtros, o botão leva ao painel Filtros da busca em vez de buscar. Sem perfil, a
página avisa que as notas dependem dele e oferece dois caminhos: montar o perfil (Meu perfil) ou
buscar assim mesmo, com as vagas gravadas sem nota.

**Why this priority**: evita buscas vazias ou notas sem base; é o caminho natural de quem acabou de
instalar a ferramenta.

**Independent Test**: num ambiente sem filtros, clicar em Buscar vagas e cair no painel Filtros; com
filtros e sem perfil, ver o aviso com as duas opções.

**Acceptance Scenarios**:

1. **Given** nenhum cargo nos filtros, **When** a pessoa clica em Buscar vagas, **Then** abre o
   painel Filtros da busca com a explicação e nenhuma consulta é feita.
2. **Given** filtros sem perfil, **When** a pessoa clica em Buscar vagas, **Then** a página oferece
   Meu perfil ou buscar sem nota.

---

### User Story 4 - Cancelar e respeitar os portais (Priority: P2)

A pessoa pode cancelar uma busca em andamento: ela para depois da consulta atual e nada dessa busca
é gravado. Para não sobrecarregar os portais (e não ser bloqueada por eles), a página não inicia uma
busca antes de um intervalo mínimo desde a última concluída, de qualquer origem, e mostra a partir
de que horário pode buscar de novo; se a última foi há pouco (mas depois do mínimo), avisa que os
portais devem ter pouca novidade e pede confirmação.

**Why this priority**: protege a pessoa de bloqueios dos portais e de buscas por engano.

**Independent Test**: iniciar e cancelar uma busca (nada gravado); concluir uma busca e ver o botão
indisponível com o horário da próxima; depois do mínimo, ver o aviso de busca recente.

**Acceptance Scenarios**:

1. **Given** uma busca em andamento, **When** a pessoa cancela, **Then** nenhuma consulta nova é
   iniciada, nada da busca é gravado e a página informa o cancelamento.
2. **Given** a última busca concluída dentro do intervalo mínimo, **When** a pessoa olha o botão,
   **Then** ele está indisponível e diz a partir de que horário pode buscar.
3. **Given** a última busca concluída há pouco, mas depois do mínimo, **When** a pessoa clica,
   **Then** a página avisa e pede confirmação.
4. **Given** um portal que devolve erro ou parece bloquear, **When** a busca termina, **Then** o
   resumo diz qual portal falhou e sugere esperar, e as vagas dos outros portais são gravadas.

---

### User Story 5 - Uma busca por vez, com o terminal e o chat (Priority: P2)

A busca pelo terminal e pela skill de chat continua igual. Elas não rodam junto com a da página:
enquanto uma busca roda pela página, o comando do terminal recusa com uma mensagem clara; enquanto
uma busca roda pelo terminal ou pelo chat, a página mostra que há uma busca em andamento fora dela e
não inicia outra. A busca da página não mexe nas vagas de uma busca do chat que ainda esperam
avaliação.

**Why this priority**: duas buscas ao mesmo tempo dobram as consultas aos portais e podem gravar a
mesma vaga duas vezes.

**Independent Test**: com uma busca rodando pela página, rodar a busca no terminal e ver a recusa; o
inverso também; com candidatas do chat esperando avaliação, buscar pela página e gravar as do chat
depois, sem perda.

**Acceptance Scenarios**:

1. **Given** uma busca rodando pela página, **When** a busca é pedida no terminal ou no chat,
   **Then** ela é recusada com uma mensagem que diz que há uma busca pela página.
2. **Given** uma busca rodando pelo terminal ou pelo chat, **When** a pessoa abre o relatório,
   **Then** a página mostra que há uma busca em andamento fora dela e não deixa iniciar outra.
3. **Given** candidatas de uma busca do chat esperando avaliação, **When** a página faz uma busca,
   **Then** essas candidatas continuam disponíveis para o chat avaliar e gravar.

---

### Edge Cases

- A página é fechada durante a busca: a busca continua; ao reabrir, aparece o andamento ou o
  resultado.
- O servidor da ferramenta é fechado durante a busca: a busca é interrompida, nada dela é gravado e,
  ao reabrir, a página diz que a última busca foi interrompida.
- Todos os portais falham e nenhuma vaga aparece: nada é gravado, o resumo diz que provavelmente
  houve bloqueio e sugere esperar; essa busca conta para o intervalo mínimo.
- Nenhuma vaga nova: o resumo diz isso; as já vistas que apareceram em outro portal ganham a
  etiqueta do portal, como hoje.
- Os filtros mudam durante a busca: vale o que estava gravado quando ela começou.
- Muitas consultas (cargos × portais × modelos × países): a confirmação mostra o número e a
  estimativa de duração para a pessoa decidir.
- A IA é desligada ou fica sem chave durante a análise: as vagas que faltavam ficam sem nota, com o
  motivo.
- Falta uma dependência da busca (biblioteca dos portais): a página diz como resolver (rodar
  `python iniciar.py`) em vez de um erro genérico.
- Acesso por outro aparelho da rede: vê o andamento e o resultado; iniciar e cancelar ficam
  indisponíveis, com a explicação.
- Uma busca do terminal termina enquanto a página está aberta: o relatório se atualiza e o intervalo
  mínimo passa a contar dela.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O Relatório de Vagas MUST ter o botão **Buscar vagas**, que roda a busca com os
  filtros e portais gravados, com as mesmas consultas, cortes e regras de vagas repetidas da busca
  pelo terminal.
- **FR-002**: Antes de começar, a página MUST mostrar o plano (número de consultas, portais, cargos,
  janela de publicação, estimativa de duração e, com IA, qual IA dará a nota e se cobra por uso) e
  pedir confirmação.
- **FR-003**: A busca MUST rodar em segundo plano, sem travar a página, com no máximo uma busca por
  vez no computador, contando página, terminal e chat.
- **FR-004**: Durante a busca, a página MUST mostrar o andamento (portal e cargo da consulta atual,
  consultas feitas e total, vagas encontradas até agora; depois, gravação e análise), e o andamento
  MUST reaparecer quando a página é reaberta.
- **FR-005**: Ao terminar, a busca MUST gravar as vagas no relatório pelas mesmas regras do terminal
  e a página MUST mostrar o resumo: encontradas, novas para decidir, fora dos critérios, já vistas,
  cortadas pelo título, fora da janela e erros dos portais.
- **FR-006**: Com IA disponível e perfil gravado, as vagas novas dentro dos critérios MUST receber
  nota pela IA escolhida, em lotes, com o mesmo pedido da análise automática, com o andamento "n de
  N" na página; se a IA falhar, as vagas MUST continuar gravadas sem nota, com o motivo visível e a
  opção de tentar de novo.
- **FR-007**: Sem IA, ou quando a pessoa escolhe buscar sem nota, as vagas MUST ser gravadas sem
  nota, nada MUST ser enviado a provedores de IA, e a página MUST dizer como obter a nota.
- **FR-008**: Sem cargos nos filtros, a página MUST NOT buscar e MUST levar ao painel Filtros da
  busca.
- **FR-009**: Sem perfil, a página MUST avisar e oferecer Meu perfil ou buscar sem nota.
- **FR-010**: A pessoa MUST poder cancelar: nenhuma consulta nova começa depois do pedido, nada da
  busca cancelada é gravado e a página informa o cancelamento.
- **FR-011**: A página MUST NOT iniciar uma busca antes de 30 minutos da última busca concluída
  (pela página, pelo terminal ou pelo chat), mostrando a partir de que horário pode buscar; se a
  última foi há menos de 6 horas, MUST avisar e pedir confirmação.
- **FR-012**: A busca pela página MUST manter entre as consultas a mesma pausa da busca pelo
  terminal.
- **FR-013**: Os comandos do terminal e da skill MUST continuar os mesmos, com o mesmo resultado, e
  MUST recusar com mensagem clara enquanto houver uma busca pela página; a página MUST NOT iniciar
  uma busca enquanto houver uma pelo terminal ou pelo chat.
- **FR-014**: A busca pela página MUST NOT apagar nem alterar as candidatas de uma busca do terminal
  ou do chat que ainda esperam avaliação.
- **FR-015**: Iniciar e cancelar a busca MUST ser aceitos só no computador onde a ferramenta roda;
  de outro aparelho, só ver o andamento e o resultado.
- **FR-016**: O registro de cada busca MUST guardar a origem (página, terminal ou chat) e a situação
  (concluída, cancelada, interrompida ou falha), e o relatório MUST continuar mostrando a última
  busca como hoje.
- **FR-017**: Textos MUST estar em português do Brasil.

### Key Entities *(include if feature involves data)*

- **Busca em andamento**: a execução atual: origem, início, situação (preparando, consultando,
  gravando, analisando, concluída, cancelada, interrompida, falha), consulta atual (portal e cargo),
  consultas feitas e total, vagas encontradas até agora, erros dos portais e, no fim, o resumo.
- **Registro de busca** (já existe): resumo de cada busca gravada no relatório; passa a guardar a
  origem e a situação.
- **Vaga** (já existe): gravada como hoje; com IA, recebe a nota pela análise automática; sem IA,
  fica sem nota.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com filtros gravados, a pessoa busca e vê as vagas novas no relatório sem usar
  terminal nem chat, em 100% das buscas concluídas.
- **SC-002**: O andamento aparece na página em até 5 segundos depois de cada consulta concluída.
- **SC-003**: Depois do pedido de cancelamento, nenhuma consulta nova é iniciada, a busca para em no
  máximo o tempo de uma consulta e nenhuma vaga dela fica gravada.
- **SC-004**: 0 buscas simultâneas (página, terminal e chat) e 0 buscas iniciadas pela página antes
  do intervalo mínimo.
- **SC-005**: Com os mesmos filtros e as mesmas respostas dos portais, as vagas gravadas e o resumo
  da busca pela página são iguais aos da busca pelo terminal.
- **SC-006**: Sem IA, 0 pedidos a provedores; com IA, 100% das vagas novas dentro dos critérios
  terminam com nota ou com o motivo da falha visível.
- **SC-007**: Durante toda a busca, a pessoa consegue usar as outras partes da página (abas, quadro,
  filtros, detalhe da vaga).

## Assumptions

- Intervalo mínimo de 30 minutos e aviso abaixo de 6 horas, para respeitar os portais; o README já
  recomenda algumas buscas por semana. Os valores ficam no código e podem mudar depois.
- Cancelar descarta a busca inteira (não grava parte dela), porque o resumo e a detecção de vagas
  repetidas dependem do conjunto completo. Busca cancelada não conta para o intervalo mínimo; busca
  concluída, ou que falhou em todos os portais, conta.
- A nota usa a análise automática que já existe (mesmo pedido e mesmos lotes); a página não traz um
  pedido novo à IA.
- Sem perfil, "buscar assim mesmo" grava sem nota: a nota sem perfil não tem base.
- A página busca só com o que está gravado (filtros e portais); as opções pontuais do terminal
  (substituir cargos, janela, portais) não aparecem na página: muda-se pelo painel Filtros.
- A estimativa de duração parte do número de consultas e da pausa entre elas; é aproximada.
- Fica fora desta fase: buscas agendadas, notificações, a área internacional e o filtro de idioma
  (Fase 7) e fontes novas (Fase 8).
- Depende do painel IA (spec 002), dos primeiros passos (spec 004, para o perfil) e do painel
  Filtros da busca. Verificação só no Windows.
