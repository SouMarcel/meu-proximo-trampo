# Feature Specification: Aba Internacional com o layout do Relatório de Vagas

**Feature Branch**: `044-internacional-relatorio` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-02

**Status**: Concluída em 2026-11-03 (validada pela pessoa na branch pessoal)

**Input**: User description: "outra melhoria que preciso agora é a aba de vagas internacional deveria ter o mesmo
layout das vagas nacionais, com filtro e ordenamento + os que já existem pois da forma que está fica difícil
identificar a vaga com melhor compatibilidade" (02/11/2026). Decisões da mesma data em Clarifications.

## Contexto

- A aba **Relatório de Vagas** (vagas do Brasil) tem:
  - as abas internas Para decidir, Não seguidas e Fora dos critérios, cada uma com o seu número;
  - a busca no texto e **Ordenar**: Maior aderência (o padrão), Mais recentes, Por plataforma e Modo de trabalho;
  - os filtros Senioridade, Modo, Nota mínima, Publicada há até e Analisadas (spec 038). Eles ficam guardados no
    navegador entre uma abertura e outra;
  - "Mostrando X de Y vagas" com Limpar filtros;
  - em Para decidir, Baixa aderência (nota abaixo de 50) recolhida e Marcar todas como não seguidas, com dois cliques;
  - um cartão por linha:
    - a caixa da nota (ou a situação: aguardando, descrição pendente, sem nota, provisória);
    - plataforma, modo, senioridade, data e termo da busca;
    - título com o selo de integridade (spec 034) e Abrir a vaga;
    - empresa, local e salário;
    - em Fora dos critérios, o motivo;
    - a análise da IA, com encaixe e lacunas;
    - os botões da aba interna (Não seguir, Seguir com a vaga, Forçar verificar, Voltar para triagem).
- A aba **Internacional** (vagas de fora) tem outro desenho:
  - um banner grande ("Conquiste oportunidades remotas internacionais (USD / EUR)") com três números: vagas, remotas
    e com visto ou relocation;
  - uma barra com:
    - a busca no texto;
    - o filtro de moeda (Todas, Dólar, Euro);
    - o filtro Patrocínio de visto / Relocation;
    - a caixa Mostrar não seguidas;
    - os botões Filtros da busca internacional e Prontidão internacional;
  - uma grade de cartões em três colunas, **na ordem em que as vagas chegaram, sem opção de ordenar**. Cada cartão
    traz:
    - plataforma, país (ou "Global") e a nota;
    - título, empresa, salário, local e contratação;
    - os sinais de visto;
    - a data e os botões Não seguir (ou Voltar para Para decidir), Seguir vaga e Aplicar.
- Por isso, na aba Internacional:
  - as vagas **Fora dos critérios** aparecem misturadas com as que esperam decisão, sem o motivo;
  - não há filtro de senioridade, modo, nota ou data, nem Analisadas;
  - não aparecem a caixa da nota, a análise da IA, as lacunas e o Forçar verificar.

  Num uso real, a maior parte das vagas de fora estava em Fora dos critérios, e achar a de melhor aderência exigia
  olhar cartão por cartão.

## Clarifications

### Session 2026-11-02

- Q: O banner grande do topo fica como? → A: Vira uma linha compacta com os números (vagas, remotas, com visto), para a
  lista começar mais perto do topo, como na aba nacional.
- Q: Os filtros e a ordem da Internacional se misturam com os da nacional? → A: Não. Cada aba guarda os seus.
- Pedido durante o teste (02/11): no menu, "Relatório de Vagas (Triagem)" vira **Vagas Nacionais**, "Internacional"
  vira **Vagas Internacionais** e "Quadro de Candidaturas" vira **Aplicações**. A ordem passa a ser Vagas Nacionais,
  Vagas Internacionais, Aplicações, Preparador de Entrevistas e Métricas & Funil (FR-015).
- Q: Os textos que ainda dizem "Relatório" e "quadro" mudam também? → A: Sim. "Relatório" passa a ser o nome novo, e
  "Remover do quadro" vira "Remover de Aplicações" (FR-016).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Achar a vaga de fora com melhor aderência (Priority: P1)

A pessoa abre a aba Internacional e cai em Para decidir. As vagas de fora vêm da maior nota para a menor, com a caixa
da nota, a análise da IA e as lacunas, como no Relatório de Vagas. As que estão fora dos critérios ficam na aba delas,
com o motivo. Ela filtra, ordena e decide, como já faz com as vagas do Brasil.

**Why this priority**: é o pedido. Sem a ordem e as abas internas, a melhor vaga continua escondida no meio da grade.

**Independent Test**: com vagas de fora em Para decidir (com e sem nota) e em Fora dos critérios, abrir a aba e conferir:

- a primeira vaga de Para decidir é a de maior nota;
- as fora dos critérios estão só na aba delas, com o motivo;
- cada filtro e cada opção de Ordenar muda a lista como no Relatório de Vagas.

**Acceptance Scenarios**:

1. **Given** vagas de fora em Para decidir, Não seguidas e Fora dos critérios, **When** a pessoa abre a aba
   Internacional, **Then** vê as três abas internas com o número de cada uma, e Para decidir está ativa.
2. **Given** Para decidir com notas diferentes, **When** a ordem é Maior aderência, **Then** a vaga de maior nota vem
   primeiro, e as de nota abaixo de 50 ficam recolhidas em Baixa aderência.
3. **Given** a aba aberta, **When** a pessoa escolhe Mais recentes, Por plataforma ou Modo de trabalho, **Then** a lista
   segue essa ordem, com os mesmos desempates do Relatório de Vagas.
4. **Given** a aba aberta, **When** a pessoa usa Senioridade, Modo, Nota mínima, Publicada há até ou Analisadas,
   **Then** a lista muda com as regras do Relatório de Vagas, inclusive a da spec 038: a vaga ainda sem nota aparece
   sempre, a não ser com Analisadas marcada.
5. **Given** um filtro ligado, **Then** aparece "Mostrando X de Y vagas" com Limpar filtros.
6. **Given** uma vaga em Fora dos critérios, **Then** o cartão mostra o motivo e o botão Seguir com a vaga.
7. **Given** uma vaga sem nota que pode ser verificada, **When** a pessoa clica em Forçar verificar, **Then** acontece o
   mesmo que no Relatório de Vagas, com as mesmas mensagens (ligue uma IA, não deu para verificar).
8. **Given** Para decidir com vagas, **When** a pessoa usa Marcar todas como não seguidas e confirma, **Then** só as
   vagas de fora à vista em Para decidir são marcadas. As do Brasil não mudam.

---

### User Story 2 - Manter o que é só da Internacional (Priority: P2)

O que a aba Internacional já tem de próprio continua lá:

- os filtros de moeda e de visto ou relocation;
- no cartão, o país, a contratação e os sinais de visto;
- os botões Filtros da busca internacional e Prontidão internacional.

O banner grande vira uma linha compacta com os números.

**Why this priority**: completa o pedido ("+ os que já existem"). Sem isso, a aba fica igual à nacional, mas perde o
que importa para vaga de fora.

**Independent Test**: abrir a aba e conferir item a item que:

- cada filtro, informação e botão da aba de hoje está na aba nova;
- a linha compacta mostra os três números, que mudam com os filtros.

**Acceptance Scenarios**:

1. **Given** a aba aberta, **Then** no topo há uma linha compacta com:
   - quantas vagas a lista mostra;
   - quantas são remotas;
   - quantas têm sinal de visto ou relocation.

   Ela fica no lugar do banner grande.
2. **Given** a barra de filtros, **Then** ela tem o filtro de moeda (Todas, Dólar, Euro) e o filtro Patrocínio de
   visto / Relocation, com as regras de hoje, junto dos filtros do Relatório de Vagas.
3. **Given** um cartão de vaga de fora, **Then** ele mostra também:
   - o país da vaga (ou "Global");
   - a contratação (ou "não informada");
   - os sinais de visto ou relocation, quando houver.
4. **Given** a barra de filtros, **Then** os botões Filtros da busca internacional e Prontidão internacional estão lá e
   abrem o mesmo que hoje.
5. **Given** a aba nova, **Then** a caixa Mostrar não seguidas não existe mais: as não seguidas ficam na aba interna
   Não seguidas, com Voltar para triagem.

---

### User Story 3 - Filtros de cada aba à parte (Priority: P3)

A ordem e os filtros escolhidos na aba Internacional ficam guardados para a próxima vez, separados dos da aba Relatório
de Vagas. Filtrar as vagas de fora não muda o que a pessoa escolheu para as do Brasil, e o contrário também vale.

**Why this priority**: conforto. As abas funcionam sem isso, mas filtros misturados confundiriam (um filtro de Euro,
por exemplo, não faz sentido nas vagas do Brasil).

**Independent Test**:

1. Na Internacional, escolher Mais recentes, Nota mínima 60 e Dólar.
2. No Relatório de Vagas, conferir que nada mudou.
3. Recarregar a página e conferir que a Internacional voltou com as escolhas do passo 1.

**Acceptance Scenarios**:

1. **Given** filtros diferentes nas duas abas, **When** a pessoa troca de aba, **Then** cada uma mostra os seus.
2. **Given** filtros escolhidos na Internacional, **When** a pessoa recarrega a página, **Then** a ordem e os filtros
   continuam os mesmos.
3. **Given** a primeira abertura da aba nova, **Then** ela começa com Maior aderência e sem filtros, sem herdar os do
   Relatório de Vagas.

---

### Edge Cases

- **Busca internacional desligada**: o aviso de hoje continua no topo da aba, com o botão Filtros da busca
  internacional. Sem vagas de fora, a aba mostra a mensagem de lista vazia.
- **Nenhuma vaga passa nos filtros**: aparece "Nenhuma vaga passa nos filtros", com Limpar filtros.
- **Moeda ou visto ligados numa vaga sem nota**: os dois filtros não dependem da análise e valem para todas as vagas,
  com ou sem nota. A conta "Mostrando X de Y" inclui as que eles esconderam.
- **Vaga sem salário** com Dólar ou Euro escolhido: fica de fora, como hoje.
- **Servidor fora do ar** (página só para leitura): os filtros funcionam, os botões que gravam ficam desligados, e o
  aviso de só leitura aparece junto de Marcar todas, como no Relatório de Vagas.
- **Tela estreita** (celular): os cartões e os filtros se empilham como no Relatório de Vagas, sem a página rolar de
  lado.
- **Navegador sem guardar preferências** (modo privativo, armazenamento bloqueado): a aba funciona com o padrão (Maior
  aderência, sem filtros), sem erro.
- **Contador da aba na navegação**: continua mostrando quantas vagas de fora estão em Para decidir.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A aba Internacional MUST ter as abas internas Para decidir, Não seguidas e Fora dos critérios. Cada uma
  mostra quantas vagas de fora tem, com a mesma regra do Relatório de Vagas (com Analisadas marcada, só as que têm
  nota). A aba abre sempre em Para decidir.
- **FR-002**: A aba MUST ter a busca no texto e Ordenar com Maior aderência (o padrão), Mais recentes, Por plataforma e
  Modo de trabalho. A busca procura no título, na empresa, na descrição e nos termos, como no Relatório de Vagas, e
  também no local e no país, como a busca de hoje da Internacional. Cada opção ordena e desempata como no Relatório de
  Vagas.
- **FR-003**: A aba MUST ter os filtros Senioridade, Modo, Nota mínima, Publicada há até e Analisadas, com as regras do
  Relatório de Vagas. A vaga ainda sem nota aparece sempre, a não ser com Analisadas marcada (spec 038).
- **FR-004**: A aba MUST manter o filtro de moeda (Todas, Dólar, Euro) e o filtro Patrocínio de visto / Relocation:
  - os dois seguem as regras de hoje e valem para todas as vagas, com ou sem nota;
  - "Mostrando X de Y vagas" e Limpar filtros contam e limpam também esses dois.
- **FR-005**: Com Maior aderência, Para decidir MUST mostrar primeiro as vagas de nota 50 ou mais e recolher as de nota
  abaixo de 50 em Baixa aderência, com o próprio Marcar todas, como no Relatório de Vagas.
- **FR-006**: Marcar todas como não seguidas MUST pedir o segundo clique e marcar só as vagas de fora de Para decidir
  (as que Analisadas deixa à vista). As do Brasil não mudam.
- **FR-007**: O cartão da vaga de fora MUST ter tudo o que o cartão do Relatório de Vagas tem:
  - a caixa da nota ou a situação;
  - plataforma, modo, senioridade, data e termo;
  - título com o selo de integridade e Abrir a vaga;
  - empresa, local e salário;
  - o motivo em Fora dos critérios;
  - a análise da IA, com encaixe e lacunas;
  - os botões de cada aba interna, inclusive Forçar verificar.

  Além disso, MUST mostrar o país da vaga (ou "Global"), a contratação (ou "não informada") e os sinais de visto ou
  relocation.
- **FR-008**: No topo da aba, no lugar do banner grande, MUST haver uma linha compacta com três números, contados sobre
  a lista à vista (aba interna e filtros):
  - quantas vagas a lista mostra;
  - quantas são remotas;
  - quantas têm sinal de visto ou relocation.
- **FR-009**: Os botões Filtros da busca internacional e Prontidão internacional MUST continuar na barra de filtros,
  abrindo o mesmo que hoje.
- **FR-010**: A ordem e os filtros da aba (Ordenar, Senioridade, Modo, Nota mínima, Publicada há até, Analisadas,
  moeda e visto) MUST ficar guardados no navegador, separados dos do Relatório de Vagas. A busca no texto e a aba
  interna não são guardadas, como no Relatório de Vagas.
- **FR-011**: Na primeira abertura, ou sem preferências guardadas, a aba MUST começar com Maior aderência e sem filtros.
- **FR-012**: A caixa Mostrar não seguidas MUST sair: as não seguidas ficam na aba interna Não seguidas.
- **FR-013**: Os botões MUST gravar o mesmo que hoje (Seguir com a vaga, Não seguir, Voltar para triagem, Marcar todas,
  Forçar verificar). Ficam iguais:
  - o servidor, a busca e a nota;
  - o que vai para Fora dos critérios;
  - o aviso de busca internacional desligada e o contador da aba na navegação.
- **FR-014**: Os textos que descrevem a aba Internacional (README e README do dashboard) MUST citar as abas internas, a
  ordem e os filtros novos.
- **FR-015**: O menu de abas MUST mostrar, nesta ordem: Vagas Nacionais (o antigo Relatório de Vagas), Vagas
  Internacionais, Aplicações (o antigo Quadro de Candidaturas), Preparador de Entrevistas e Métricas & Funil. Os
  contadores de cada aba e a aba que abre primeiro (Vagas Nacionais) não mudam.
- **FR-016**: Os textos que a pessoa lê MUST usar os nomes novos:
  - onde dizia Relatório (ou Relatório de Vagas), Vagas Nacionais, ou Vagas Nacionais e Vagas Internacionais quando
    vale para as duas;
  - onde dizia quadro (a aba), Aplicações: "Remover de Aplicações", "Aplicações: Salva" no Adicionar vaga etc.;
  - na página, nas mensagens do terminal, no README, no README do dashboard, no contrato da API, no `AGENTS.md` e nas
    skills.

  Não mudam:
  - os nomes no código, os valores gravados (`etapa: "relatorio"`, `tipo: "quadro"`) e o comando `banco.py quadro`;
  - "quadro" no sentido de outra coisa (o quadro de vagas da empresa no Greenhouse, o quadro do WebSocket, o Quadro
    Europeu dos idiomas, o modo de exibição em Quadro Kanban);
  - as specs antigas, que são o registro de cada época.

### Key Entities

- **Preferências da aba Internacional**: a ordem e os filtros escolhidos na aba (Ordenar, níveis, modos, nota mínima,
  dias, Analisadas, moeda e visto). Ficam no navegador da pessoa, separadas das do Relatório de Vagas. Não vão para o
  arquivo de filtros nem para o servidor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ao abrir a aba Internacional, a vaga de fora de maior nota em Para decidir é a primeira da lista, sem
  rolar nem mexer em filtro.
- **SC-002**: Nenhuma vaga Fora dos critérios aparece em Para decidir: todas ficam na aba delas, com o motivo.
- **SC-003**: Nenhum recurso some, conferido item a item:
  - todo filtro, informação e botão da aba Internacional de hoje está na aba nova (a caixa Mostrar não seguidas vira a
    aba Não seguidas);
  - todo filtro, ordem e botão do Relatório de Vagas existe na aba Internacional.
- **SC-004**: Filtros escolhidos numa aba não mudam a outra. Depois de recarregar a página, cada aba volta com os seus.
- **SC-005**: Numa tela de celular (360 px de largura), a aba funciona sem a página rolar de lado.

## Assumptions

- O cartão é o do Relatório de Vagas, uma vaga por linha, no lugar da grade de três colunas.
- O botão Aplicar do cartão de hoje dá lugar ao Abrir a vaga do cartão nacional, que abre o anúncio. A candidatura
  segue pelo Quadro, como nas vagas do Brasil.
- O filtro de visto mantém a regra de hoje: a vaga tem um sinal que fala de visto ou de relocation.
- O filtro de moeda mantém a regra de hoje: o salário da vaga está em dólar ou em euro.
- O texto do banner grande (que cita fontes e "sem necessidade de visto") sai junto com ele.
- Fora do escopo:
  - mudanças na nota, na análise da IA, na busca internacional e no que vai para Fora dos critérios;
  - filtros novos de vaga de fora (fuso, inglês, autorização de trabalho). Podem vir numa spec própria;
  - mudanças no Relatório de Vagas, a não ser o que for preciso para as duas abas usarem o mesmo desenho.
