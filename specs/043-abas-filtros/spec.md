# Feature Specification: Abas no painel Filtros da busca

**Feature Branch**: `043-abas-filtros` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-02

**Status**: Concluída em 2026-11-02 (validada pela pessoa na branch pessoal)

**Input**: User description: "vamos fazer uma outra melhoria da interface, em filtros de busca, vamos criar abas, 1
primeira "Geral" com tudo exceto o que deve ir para outras abas. 2 aba "Portais" - nela vamos colocar os portais
mapeados e quais os próximos que devemos mapear. 3 aba Empresas acompanhadas/excluídas - deve ter os itens de mesmo
nome do filtro atual." (02/11/2026). Decisões da mesma data em Clarifications.

## Contexto

- Hoje o painel **Filtros da busca** é uma coluna única com 12 seções, nesta ordem:
  1. Cargos
  2. Portais
  3. Portais com login (spec 041)
  4. Localidade
  5. Modo de trabalho
  6. Data de publicação
  7. Tipo de emprego
  8. Senioridade
  9. Moedas aceitas
  10. Idiomas aceitos
  11. Empresas a excluir
  12. Empresas que você acompanha (specs 031 e 042)

  O painel é longo, e para chegar às empresas é preciso rolar até o fim.
- O painel **Filtros da busca internacional** é o outro modo do mesmo painel, aberto pelo link em Modo de trabalho. Ele
  tem as seções da busca no exterior, entre elas **Fontes do exterior** (Remotive, Himalayas, RemoteOK, Jobicy, We Work
  Remotely, Get on Board).
- Portais que ainda não entraram: a lista de desejos registra InHire e Catho como próximos portais do Brasil, e o
  Glassdoor como recusado (o site recusou acesso automatizado em 23/10/2026, e a API de parceiros não está aberta).

## Clarifications

### Session 2026-11-02

- Q: O que o bloco "Próximos a mapear" mostra? → A: Uma lista fixa da ferramenta, só para leitura, atualizada a cada
  portal novo ou descartado. Ela traz os portais em estudo e os que não deram, com o motivo, e serve a qualquer pessoa.
- Q: As fontes do exterior vão para a aba Portais? → A: Não. Elas ganham uma aba própria, "Portais internacionais".
- Q: Onde fica essa aba? → A: É a quarta aba do painel Filtros da busca:
  Geral | Portais | Portais internacionais | Empresas acompanhadas/excluídas.
  As fontes do exterior saem do painel da busca internacional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Achar cada grupo de filtros pela aba (Priority: P1)

A pessoa abre Filtros da busca e cai na aba Geral, com o que define a busca: cargos, onde, como e o que aceita. Portais e
empresas ficam cada um na sua aba, a um clique. Ela pode mexer em várias abas e salvar tudo de uma vez.

**Why this priority**: é o pedido. Sem as abas, nada do resto faz sentido.

**Independent Test**: abrir o painel, conferir que cada uma das 12 seções de hoje está em alguma aba, editar algo em
três abas, salvar e conferir no arquivo de filtros que as três mudanças foram gravadas.

**Acceptance Scenarios**:

1. **Given** o painel fechado, **When** a pessoa abre Filtros da busca, **Then** a aba Geral está ativa, com Cargos,
   Localidade, Modo de trabalho, Data de publicação, Tipo de emprego, Senioridade, Moedas aceitas e Idiomas aceitos,
   na ordem de hoje.
2. **Given** o painel aberto, **When** a pessoa clica em Portais, **Then** vê os portais da busca e os Portais com
   login, com o funcionamento de hoje:
   - termos de uso e o que cada portal precisa;
   - ligar um portal com login pede a confirmação com o aviso de risco;
   - conectar abre a janela de login, e a situação (conectado, desconectado, em espera) aparece ao lado.
3. **Given** o painel aberto, **When** a pessoa clica em Empresas acompanhadas/excluídas, **Then** vê "Empresas que
   você acompanha" e "Empresas a excluir", com os mesmos nomes, textos e funcionamento de hoje:
   - colar o link e Adicionar;
   - o reconhecimento da página e o aviso de ligar a IA;
   - a lista com Remover;
   - as etiquetas das empresas a excluir.
4. **Given** a pessoa mudou um cargo em Geral, ligou um portal em Portais e removeu uma empresa na aba de empresas,
   **When** clica em Salvar filtros, **Then** as três mudanças são gravadas juntas, numa gravação só.
5. **Given** a pessoa editou algo numa aba, **When** troca de aba e volta, **Then** o que editou continua lá.
6. **Given** qualquer aba ativa, **Then** o rodapé mostra a conta de consultas, atualizada a cada mudança, e os botões
   Cancelar e Salvar filtros.

---

### User Story 2 - Portais internacionais numa aba própria (Priority: P2)

As fontes do exterior saem do painel da busca internacional e vão para a aba Portais internacionais, ao lado dos
portais do Brasil. Assim, todos os portais ficam no mesmo painel. A aba avisa quando a busca internacional está
desligada, porque só com ela ligada essas fontes rodam.

**Why this priority**: completa a separação dos portais. Sem ela, as fontes do exterior continuam escondidas no outro
painel.

**Independent Test**: com a busca internacional desligada, abrir a aba, ver o aviso, marcar uma fonte, seguir o link,
ligar a busca internacional, salvar e conferir que a fonte e a busca internacional foram gravadas.

**Acceptance Scenarios**:

1. **Given** a busca internacional ligada, **When** a pessoa abre a aba Portais internacionais, **Then** vê as fontes
   do exterior com os termos de uso, e marcar e desmarcar funciona como hoje.
2. **Given** a busca internacional desligada, **When** a pessoa abre a aba, **Then** vê o aviso de que estas fontes só
   rodam com a busca internacional ligada e um link que abre Filtros da busca internacional. Marcar uma fonte continua
   possível e vale quando ela ligar a busca internacional.
3. **Given** o painel Filtros da busca internacional aberto, **Then** ele não tem mais a seção Fontes do exterior, e
   o texto do fim diz que as fontes do exterior estão na aba Portais internacionais, com um link que abre o painel
   Filtros da busca nessa aba.
4. **Given** a pessoa editou algo em Filtros da busca e seguiu o link para o painel internacional, **When** volta para
   Filtros da busca, **Then** o que editou continua lá, ainda sem gravar, e a aba é a mesma de onde saiu.

---

### User Story 3 - Ver os próximos portais (Priority: P3)

No fim da aba Portais, o bloco "Próximos a mapear" mostra os portais que a ferramenta estuda para entrar na busca e os
que foram descartados, com o motivo. A pessoa sabe o que vem por aí e por que um portal conhecido não está na lista.

**Why this priority**: é informação, não muda a busca. As abas funcionam sem ela.

**Independent Test**: abrir a aba Portais e conferir os três itens da entrega. Depois, com a ferramenta sem a lista,
conferir que o bloco não aparece.

**Acceptance Scenarios**:

1. **Given** a aba Portais aberta, **Then** o bloco "Próximos a mapear" lista cada portal com o nome e a situação: "em
   estudo" ou "não deu". Os que não deram mostram também o motivo.
2. **Given** a entrega desta spec, **Then** a lista traz InHire e Catho em estudo e o Glassdoor como "não deu", com o
   motivo de ter recusado acesso automatizado em 23/10/2026.
3. **Given** o bloco à vista, **Then** não há nada para marcar nem botão: é só leitura.
4. **Given** a ferramenta sem a lista (vazia, ou a página nova com um servidor antigo), **Then** o bloco não aparece, e
   o resto da aba funciona.

---

### Edge Cases

- **Erro ao salvar** (regra que falhou, ex.: nenhum portal marcado) com outra aba aberta: a mensagem aparece em
  qualquer aba e diz o que corrigir.
- **Filtros sugeridos** (primeiros passos, cargos-alvo): o aviso "Estes são os filtros sugeridos…" aparece no topo,
  em todas as abas, e nada é gravado sem Salvar filtros.
- **Primeira vez** (ainda sem arquivo de filtros): o aviso de primeira vez aparece em todas as abas.
- **Cancelar ou fechar** com mudanças: nada é gravado, como hoje. Ao reabrir, o painel volta à aba Geral.
- **Sem portais com login** na ferramenta: a seção não aparece, como hoje.
- **Servidor fora do ar** (página só para leitura): as abas funcionam para ver. O Salvar fica desligado, e o aviso de
  hoje aparece no rodapé.
- **Tela estreita** (celular): as quatro abas cabem ou rolam na horizontal, sem a página rolar de lado.
- **Nenhum portal ligado**: o contador da aba Portais mostra 0, e o servidor recusa a gravação com a mensagem de hoje.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O painel Filtros da busca MUST ter quatro abas, nesta ordem: Geral, Portais, Portais internacionais e
  Empresas acompanhadas/excluídas.
- **FR-002**: O painel MUST abrir sempre na aba Geral.
- **FR-003**: A aba Geral MUST ter Cargos, Localidade, Modo de trabalho, Data de publicação, Tipo de emprego,
  Senioridade, Moedas aceitas e Idiomas aceitos, com os textos e o funcionamento de hoje.
- **FR-004**: A aba Portais MUST ter, nesta ordem:
  - os portais da busca, com o texto de hoje (inclusive o de que o LinkedIn também busca vagas de fora);
  - Portais com login, com o funcionamento de hoje;
  - o bloco Próximos a mapear.
- **FR-005**: A aba Portais internacionais MUST ter as fontes do exterior, com o texto e o funcionamento de hoje.
  Quando a busca internacional está desligada, MUST mostrar o aviso de que elas só rodam com a busca internacional
  ligada e um link que abre o painel Filtros da busca internacional.
- **FR-006**: A aba Empresas acompanhadas/excluídas MUST ter "Empresas que você acompanha" e "Empresas a excluir", com
  os mesmos nomes, textos e funcionamento de hoje.
- **FR-007**: As abas MUST formar um formulário só:
  - trocar de aba não perde nada do que foi editado;
  - Salvar filtros grava as quatro abas numa gravação só;
  - Cancelar descarta as mudanças de todas.
- **FR-008**: O rodapé (conta de consultas, aviso de risco de bloqueio, Cancelar e Salvar filtros) MUST ficar à vista
  em todas as abas.
- **FR-009**: Os avisos do topo (filtros sugeridos, primeira vez) e a mensagem de erro ao salvar MUST aparecer em
  qualquer aba.
- **FR-010**: O painel Filtros da busca internacional MUST deixar de ter a seção Fontes do exterior. O texto do fim
  MUST dizer onde ficam cargos, portais e localidade (Filtros da busca) e as fontes do exterior (aba Portais
  internacionais), com links que abrem Filtros da busca na aba certa.
- **FR-011**: Ir de Filtros da busca para o painel internacional e voltar, sem fechar, MUST manter o que foi editado e
  voltar à aba de onde a pessoa saiu, a não ser que o link leve a uma aba específica.
- **FR-012**: O bloco Próximos a mapear MUST mostrar a lista fixa que vem com a ferramenta, só para leitura. Cada
  item mostra o nome do portal e a situação ("em estudo" ou "não deu"). Os que não deram mostram também o motivo. Sem
  lista, o bloco não aparece.
- **FR-013**: A lista de próximos MUST ser mantida junto com a ferramenta, sem nada de uma pessoa específica, e MUST
  ser atualizada no roteiro de portal novo:
  - o portal que entra na busca sai da lista;
  - o portal descartado entra como "não deu", com o motivo.

  Conteúdo na entrega: InHire e Catho (em estudo) e Glassdoor (não deu: recusou acesso automatizado em 23/10/2026).
- **FR-014**: As abas Portais, Portais internacionais e Empresas acompanhadas/excluídas MUST mostrar um contador, que
  muda junto com o formulário, antes de salvar:
  - Portais: quantos portais estão ligados, os da busca e os com login;
  - Portais internacionais: quantas fontes do exterior estão ligadas;
  - Empresas acompanhadas/excluídas: quantas empresas estão nas duas listas.
- **FR-015**: As abas MUST funcionar pelo teclado e indicar a aba ativa, na tela e para o leitor de tela. Em tela
  estreita, MUST rolar na horizontal sem a página rolar de lado.
- **FR-016**: A gravação e a busca MUST continuar iguais: os mesmos filtros, as mesmas regras de validação e as mesmas
  consultas. Só muda a organização do painel, além do bloco novo, que é só leitura.
- **FR-017**: Os textos que indicam caminhos no painel (skills da ferramenta, README do dashboard, contrato da API)
  MUST citar a aba onde cada seção ficou.

### Key Entities

- **Portal a mapear**: um portal que ainda não está na busca. Tem nome, situação ("em estudo" ou "não deu") e, quando
  não deu, o motivo com a data. Faz parte da ferramenta, não dos filtros da pessoa, e não é gravado no arquivo de
  filtros.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ao abrir o painel, as quatro abas estão à vista sem rolar, e cada grupo de filtros fica a um clique.
- **SC-002**: Uma edição em três abas seguida de Salvar grava as três mudanças numa gravação só. Trocar de aba não perde
  nada.
- **SC-003**: Nenhum campo some. Cada seção de hoje dos dois painéis está numa aba ou no painel internacional,
  conferido item a item.
- **SC-004**: Numa tela de celular (360 px de largura), as quatro abas são alcançáveis sem a página rolar de lado.
- **SC-005**: Na entrega, o bloco Próximos a mapear mostra três portais: InHire, Catho e Glassdoor.

## Assumptions

- Dentro da aba Portais, a seção "Portais" passa a se chamar "Portais da busca", para não repetir o nome da aba.
- Na aba de empresas, "Empresas que você acompanha" vem antes de "Empresas a excluir", na ordem do nome da aba.
- A aba ativa não é lembrada entre aberturas: o painel sempre abre na Geral.
- O painel Filtros da busca internacional continua sem abas e com as outras seções como estão.
- A lista de próximos vem do servidor, junto com as opções do painel. A página nova com um servidor antigo não mostra
  o bloco.
- Fora do escopo:
  - sugerir um portal pelo painel e anotações pessoais de portais (decisão de 02/11/2026: lista fixa);
  - mudanças na busca;
  - portais candidatos do exterior. A lista de hoje só tem portais do Brasil; se aparecer um do exterior, ele entra
    na mesma lista e no mesmo bloco.
