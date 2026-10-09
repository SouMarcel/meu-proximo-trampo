# Feature Specification: Área de vagas internacionais

**Feature Branch**: `008-area-internacional` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 7 do roteiro: área de vagas internacionais. Busca internacional
opcional, habilitada no painel de filtros (desligada por padrão). Toda vaga encontrada por ela é
marcada como internacional e mostra a etiqueta 'Internacional · país' (e a moeda) na listagem, no
card e na lista do quadro, no detalhe e no aviso de vaga repetida. Aba Internacional com relatório
e filtros próprios; o Relatório de Vagas mostra só o Brasil; o Quadro é comum, com filtro por área.
Filtros: países, regiões aceitas, cargos em inglês, moedas e salário mínimo anual, fuso, contratação
aceita e as caixas aceito morar fora, passaporte, visto ou autorização de trabalho e sponsor. Filtro
de idioma da vaga para qualquer vaga (vazio = todos): campo do portal, senão detecção sem IA, e a IA
confirma; fora da lista vai para Fora dos critérios com o motivo. Com aceito morar fora, inclui
presenciais e híbridas nos países escolhidos. Cada portal só roda nas buscas da sua área. Adicionar
Vaga com campo Área e palpite pelo link. O remoto nacional deixa de ser pré-requisito. Fontes novas e
elegibilidade ficam para a Fase 8. Nada muda para quem não habilitar. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Habilitar a busca internacional e ver as vagas separadas (Priority: P1)

A pessoa abre a aba **Internacional**, liga a busca internacional e escolhe os países de interesse
e os cargos em inglês. As buscas seguintes trazem também vagas do exterior, que aparecem no
relatório próprio da aba Internacional (o Relatório de Vagas continua só com as do Brasil). Cada vaga
de lá mostra a etiqueta **Internacional · país** (e a moeda, quando o anúncio diz) em todo lugar
onde a vaga aparece. Ao seguir com uma vaga internacional, ela vai para o mesmo Quadro, com a
etiqueta, e o Quadro ganha um filtro por área (todas, Brasil, internacional).

**Why this priority**: hoje a busca no exterior está misturada com a nacional, sem marca, e depende
de marcar "remoto" no Brasil; quem quer só vagas daqui se confunde e quem quer de fora não acha.

**Independent Test**: ligar a busca internacional com um país e um cargo, buscar e ver as vagas de
fora só na aba Internacional, com a etiqueta no relatório, no card, na lista do quadro e no
detalhe.

**Acceptance Scenarios**:

1. **Given** a busca internacional desligada (padrão), **When** a pessoa busca, **Then** nada muda
   em relação a hoje e a aba Internacional explica como ligar.
2. **Given** a busca internacional ligada com países e cargos em inglês, **When** a busca roda,
   **Then** as vagas de fora vão para o relatório da aba Internacional, marcadas como internacionais.
3. **Given** uma vaga internacional, **When** ela aparece na listagem, no card, na lista do quadro,
   no detalhe ou no aviso de vaga repetida, **Then** a etiqueta "Internacional · país" (e a moeda,
   quando houver) aparece.
4. **Given** vagas do Brasil e de fora no Quadro, **When** a pessoa filtra por área, **Then** só as
   da área escolhida aparecem.
5. **Given** o remoto nacional desmarcado (só híbrido na cidade), **When** a busca internacional
   está ligada, **Then** ela roda mesmo assim.

---

### User Story 2 - Filtros da busca internacional (Priority: P1)

O painel **Filtros da busca internacional** reúne o que importa para vagas de fora, como no LinkedIn:
países de interesse, regiões aceitas (Brasil, América Latina, Américas, mundo todo), cargos em
inglês, moedas aceitas e salário mínimo anual, fuso ou horas de sobreposição aceitas, formas de
contratação aceitas (contractor, EOR, PJ) e as caixas **aceito morar fora** (com os países),
**tenho passaporte válido**, **tenho visto ou autorização de trabalho** (com os países) e **preciso
de patrocínio de visto (sponsor)**. As caixas valem só para vagas internacionais e alimentam a
análise da vaga. Com **aceito morar fora**, a busca inclui vagas presenciais e híbridas nos países
escolhidos.

**Why this priority**: sem esses filtros, a busca de fora traz vagas que a pessoa não pode ou não
quer aceitar.

**Independent Test**: preencher o painel, gravar e ver os valores no arquivo de configuração; com
"aceito morar fora" e um país, ver a busca incluir vagas presenciais naquele país.

**Acceptance Scenarios**:

1. **Given** o painel, **When** a pessoa preenche e grava, **Then** os filtros ficam guardados e
   aparecem iguais ao reabrir.
2. **Given** moeda fora das aceitas ou salário anual abaixo do mínimo informado na vaga, **When** a
   vaga é avaliada, **Then** ela vai para Fora dos critérios com o motivo.
3. **Given** "aceito morar fora" marcado com Portugal, **When** a busca internacional roda, **Then**
   ela inclui vagas presenciais e híbridas em Portugal.
4. **Given** as caixas de passaporte, autorização e sponsor, **When** a IA analisa uma vaga
   internacional, **Then** ela considera essas informações nos alertas (a regra completa de
   elegibilidade fica para a Fase 8).

---

### User Story 3 - Idiomas aceitos, para qualquer vaga (Priority: P2)

No painel de filtros, a pessoa escolhe os **idiomas aceitos** da vaga (por exemplo, português e
inglês). Vazio = todos. Vale para vagas do Brasil e de fora: o idioma vem do portal quando ele
informa; senão, da leitura do título e da descrição, sem IA; com IA, a análise confirma. Vaga em
idioma fora da lista vai para **Fora dos critérios** com o motivo ("vaga em espanhol; você aceita
português e inglês").

**Why this priority**: muita vaga aparece em espanhol, alemão ou francês; quem não fala o idioma
perde tempo triando.

**Independent Test**: com português e inglês aceitos, buscar e ver uma vaga em espanhol em Fora dos
critérios com o motivo; com a lista vazia, ver a mesma vaga no relatório.

**Acceptance Scenarios**:

1. **Given** idiomas aceitos PT e EN, **When** uma vaga em espanhol chega, **Then** ela vai para Fora
   dos critérios com o motivo do idioma.
2. **Given** a lista de idiomas vazia, **When** vagas em qualquer idioma chegam, **Then** nenhuma é
   cortada pelo idioma.
3. **Given** uma vaga curta demais para saber o idioma, **When** ela chega, **Then** ela passa (na
   dúvida, não corta).

---

### User Story 4 - Área no Adicionar Vaga e portais por área (Priority: P3)

No **Adicionar Vaga**, um campo **Área** (Brasil ou internacional) vem preenchido com um palpite
pelo link e pelo local, e a pessoa pode trocar. Na busca, cada portal só roda nas buscas da área que
ele atende (um portal só do Brasil não é consultado para vagas de fora), o que economiza consultas.

**Why this priority**: completa a separação por área nas outras entradas de vaga e respeita os
portais.

**Independent Test**: adicionar uma vaga de um site dos Estados Unidos e ver a área sugerida como
internacional; buscar com a internacional ligada e ver que o portal só do Brasil não foi consultado
para os países de fora.

**Acceptance Scenarios**:

1. **Given** o link de uma vaga com local nos Estados Unidos, **When** a pessoa adiciona, **Then** a
   área sugerida é internacional, com o país.
2. **Given** um portal que só atende o Brasil, **When** a busca internacional roda, **Then** ele não
   é consultado para os países de fora.

---

### Edge Cases

- Vagas antigas, gravadas antes desta fase: contam como Brasil, a não ser as que vieram de uma
  consulta internacional (que passam a internacionais, com o país da consulta).
- Vaga internacional que é remota para o mundo todo: etiqueta "Internacional · mundo todo".
- Vaga com local no Brasil encontrada pela consulta internacional (empresa de fora contratando no
  Brasil): fica na área Brasil, com a moeda informada se houver.
- Moeda não informada no anúncio: não corta pela moeda nem pelo salário.
- Salário informado por mês ou por hora: convertido em anual para comparar; se não der, não corta.
- Idioma ambíguo (texto curto ou misturado): não corta.
- Busca internacional ligada sem países ou sem cargos: o painel não grava e explica o que falta.
- Muitas consultas (países × cargos × portais): o painel e a confirmação da busca mostram o número.
- Pessoa desliga a busca internacional: as vagas de fora já gravadas continuam na aba Internacional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A busca internacional MUST ser opcional e vir desligada; a pessoa liga no painel
  Filtros da busca internacional.
- **FR-002**: Toda vaga encontrada pela busca internacional (ou com local fora do Brasil) MUST ser
  marcada com a área internacional e o país (ou região).
- **FR-003**: A etiqueta "Internacional · país" (e a moeda, quando houver) MUST aparecer na listagem
  do relatório, no card e na lista do quadro, no detalhe e no aviso de vaga repetida.
- **FR-004**: A página MUST ter a aba Internacional com relatório próprio; o Relatório de Vagas MUST
  mostrar só as vagas do Brasil; o Quadro MUST ser comum, com filtro por área.
- **FR-005**: O painel Filtros da busca internacional MUST permitir: ligar a busca, países de
  interesse, regiões aceitas, cargos em inglês, moedas aceitas, salário mínimo anual, fuso ou horas
  de sobreposição, contratação aceita e as caixas aceito morar fora (com países), passaporte válido,
  visto ou autorização de trabalho (com países) e precisa de sponsor.
- **FR-006**: A busca internacional MUST NOT depender do remoto nacional.
- **FR-007**: Com "aceito morar fora", a busca internacional MUST incluir vagas presenciais e
  híbridas nos países escolhidos.
- **FR-008**: Vaga internacional com moeda fora das aceitas ou salário anual abaixo do mínimo MUST ir
  para Fora dos critérios com o motivo; sem moeda ou salário informados, não corta.
- **FR-009**: O filtro de idiomas aceitos MUST valer para qualquer vaga (vazio = todos), com o idioma
  do portal quando houver, senão por detecção sem IA, e confirmado pela análise com IA; fora da
  lista → Fora dos critérios com o motivo; na dúvida, não corta.
- **FR-010**: As caixas de passaporte, autorização e sponsor e as formas de contratação MUST ir para
  a análise da vaga internacional com IA.
- **FR-011**: Cada portal MUST rodar só nas buscas da área que atende.
- **FR-012**: O Adicionar Vaga MUST ter o campo Área, com palpite pelo link e pelo local, que a pessoa
  pode trocar.
- **FR-013**: Para quem não ligar a busca internacional e não preencher idiomas, a busca, o relatório
  e o quadro MUST continuar como hoje.
- **FR-014**: Textos MUST estar em português do Brasil.

### Key Entities *(include if feature involves data)*

- **Área da vaga**: Brasil ou internacional, com país ou região e moeda quando houver.
- **Filtros internacionais**: ligado, países, regiões, cargos em inglês, moedas, salário mínimo
  anual, fuso, contratação aceita, aceito morar fora (países), passaporte, autorização (países),
  precisa de sponsor.
- **Idiomas aceitos**: lista de idiomas (vazia = todos), filtro geral.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das vagas encontradas pela busca internacional aparecem só na aba Internacional,
  com a etiqueta em todos os lugares onde a vaga aparece.
- **SC-002**: Com a busca internacional desligada e sem idiomas, o resultado de uma busca é igual ao
  de antes desta fase.
- **SC-003**: Com PT e EN aceitos, 100% das vagas claramente em outro idioma de um conjunto de teste
  vão para Fora dos critérios com o motivo, e nenhuma vaga em PT ou EN é cortada.
- **SC-004**: Nenhum portal que só atende o Brasil é consultado para os países de fora.
- **SC-005**: A pessoa liga a busca internacional e grava os filtros em até 2 minutos.

## Assumptions

- Os portais de hoje: Indeed atende Brasil e exterior (por país); Gupy só Brasil; startup.jobs só
  exterior. As fontes internacionais novas (Remotive, Himalayas, Greenhouse…) ficam para a Fase 8.
- A elegibilidade completa (vaga que exige autorização num país × caixas da pessoa) fica para a Fase
  8; nesta fase, as caixas vão para a análise com IA e aparecem nos alertas.
- Idiomas detectados sem IA: português, inglês, espanhol, francês, alemão e italiano; os outros
  ficam como "não identificado" (não corta).
- Câmbio não é feito: o salário mínimo anual é um valor em dólar (USD); vagas que pagam em outra
  moeda não são cortadas pelo salário (só pela moeda, se ela não for aceita).
- Regiões aceitas: Brasil, América Latina, Américas, mundo todo; servem para a análise e para
  vagas "remoto para região X" (a regra completa é da Fase 8).
- O padrão de idiomas aceitos é vazio (todos); cada pessoa escolhe os seus no painel.
- Verificação só no Windows.
