# Feature Specification: Regiões e continentes nos filtros da busca internacional

**Feature Branch**: `047-regioes-continentes` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "notei que meu perfil diz apenas brasil / americas mas eu tbm quero europa e oceania porem
nao tem como marcar o continente apenas os paises, assim faça a melhoria para adicionar os continentes ao filtro e ao
meu perfil" (06/11/2026). Decisões da mesma data em Clarifications.

## Contexto

- **Regiões aceitas**, no painel **Filtros da busca internacional**, tem quatro opções: Brasil, América Latina,
  Américas e Mundo todo. Não há Europa, Oceania, Ásia nem África.
- **Os campos de país só aceitam países, um a um:**
  - Países de interesse (onde a busca procura);
  - Países para morar (quem aceita mudar);
  - Autorização de trabalho (onde a pessoa já pode trabalhar).
- **Hoje cada região só passa se estiver marcada com o nome exato.** Com Brasil e Américas marcados:
  - vaga aberta à América Latina vai para Fora dos critérios, embora a América Latina faça parte das Américas;
  - vaga aberta ao mundo todo também vai, embora inclua a pessoa.

  No banco de uma pessoa que testou a ferramenta, 4 vagas da América Latina foram para Fora dos critérios por isso.
- **A ferramenta não reconhece no texto da vaga** "Oceania", "APAC", "Asia" nem "Africa". Uma vaga aberta só à
  Oceania passa sem análise.
- **"EU" e "European Union" são lidos como Europa**, embora a União Europeia seja só parte dela. Vaga "só Alemanha"
  vai para Fora mesmo para quem tem autorização de trabalho na União Europeia, porque o campo de autorização só aceita
  países.

## Clarifications

### Session 2026-11-06

- **Q: Que regiões a pessoa marca?**
  - Por continente e por sub-região: América do Norte, América Central, América do Sul, América Latina, Américas,
    União Europeia, Europa, Ásia, Oceania e África.
  - "Seu país" continua como opção.
- **Q: Com Américas marcada, vaga aberta à América Latina passa? E vaga aberta ao mundo todo?**
  - Passam. Basta a região da vaga ter país em comum com alguma região marcada.
  - Vaga aberta ao mundo todo sempre passa, e a opção "Mundo todo" sai.
- **Q: Onde as regiões entram?**
  - Em Regiões aceitas e nos três campos de país: países de interesse, países para morar e autorização de trabalho.
  - Na busca, o portal que procura por região (LinkedIn) faz uma consulta pela região.
  - O portal que exige um país (Indeed) só procura nos países marcados um a um.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aceitar vagas por continente (Priority: P1)

A pessoa abre **Regiões aceitas** e marca Américas, Europa e Oceania, além do seu país. Na busca seguinte:

- vagas abertas à América Latina, à União Europeia, a "Europe" ou à Oceania não vão mais para Fora dos critérios por
  região;
- vagas abertas ao mundo todo passam;
- uma vaga aberta só à Ásia vai para Fora com o motivo "Vaga aberta a: Ásia; você aceita Brasil, Américas, Europa e
  Oceania".

**Why this priority**: é o pedido da pessoa. Hoje ela não consegue dizer que aceita vagas da Europa e da Oceania, e a
regra corta vagas que a incluem (América Latina, mundo todo).

**Independent Test**: marcar regiões no painel, gravar e conferir, numa lista de anúncios de exemplo, quais vão para
Fora e com que motivo.

**Acceptance Scenarios**:

1. **Given** Regiões aceitas com Brasil e Américas, **When** chega uma vaga aberta à América Latina, **Then** ela não
   vai para Fora por região.
2. **Given** qualquer região marcada, **When** chega uma vaga aberta ao mundo todo ("Anywhere", "Worldwide"),
   **Then** ela não vai para Fora por região.
3. **Given** Regiões aceitas com Américas e Europa, **When** chega uma vaga aberta só à Ásia, **Then** ela vai para
   Fora com o motivo que cita a região da vaga e as regiões marcadas.
4. **Given** Europa marcada, **When** chega uma vaga "EU only" e a pessoa pode trabalhar na União Europeia, **Then** a
   vaga passa (a União Europeia faz parte da Europa).
5. **Given** nenhuma região marcada, **When** a busca roda, **Then** nada é cortado por região, como hoje.
6. **Given** uma vaga que não diz a que lugares está aberta ("Remote"), **When** ela é avaliada, **Then** não vai para
   Fora por região.

---

### User Story 2 - Autorização de trabalho por região (Priority: P1)

A pessoa tem autorização de trabalho em toda a União Europeia e marca **União Europeia** no campo de autorização. Vagas
que exigem morar ou ter autorização na Alemanha, na Espanha ou em "EU" passam a servir para ela. Vaga que exige o Reino
Unido continua indo para Fora, porque o Reino Unido não está na União Europeia.

**Why this priority**: sem isso, quem pode trabalhar num bloco de países precisa digitar cada país, e as vagas
restritas a um deles vão para Fora sem motivo real.

**Independent Test**: gravar a autorização "União Europeia" e conferir anúncios "Germany only", "authorized to work in
the EU" e "UK right to work".

**Acceptance Scenarios**:

1. **Given** autorização na União Europeia, **When** chega uma vaga "must be based in Germany", **Then** ela não vai
   para Fora por exigir lugar.
2. **Given** autorização na União Europeia, **When** chega uma vaga "right to work in the UK" sem patrocínio de visto,
   **Then** ela vai para Fora com o motivo de hoje.
3. **Given** autorização só em Portugal, **When** chega uma vaga "EU only", **Then** ela passa (Portugal está na União
   Europeia), como hoje.

---

### User Story 3 - Buscar numa região inteira (Priority: P2)

Em **Países de interesse**, a pessoa marca **União Europeia** em vez de 27 países. Cada cargo vira uma consulta à
região no portal que procura por região (LinkedIn), em vez de uma por país. O painel avisa que o Indeed só procura nos
países marcados um a um, e a estimativa de consultas mostra o número certo. As vagas achadas assim mostram a região na
etiqueta ("Internacional · União Europeia").

Em **Países para morar**, a região também vale. Vaga presencial ou híbrida num país da região não vai para Fora por
"você aceita morar em…".

**Why this priority**: amplia a busca no exterior sem multiplicar as consultas, mas a busca global (LinkedIn
"Worldwide", JobGether, sites de remoto) já traz vagas de qualquer região. O filtro (P1) é o que a pessoa precisa
primeiro.

**Independent Test**: marcar uma região em Países de interesse, abrir a confirmação da busca e conferir os portais e o
número de consultas. Depois, buscar com um cargo e ver a etiqueta da região.

**Acceptance Scenarios**:

1. **Given** União Europeia em Países de interesse e 2 cargos, **When** a pessoa abre a confirmação da busca,
   **Then** a estimativa conta 2 consultas a mais no LinkedIn e nenhuma no Indeed para essa região.
2. **Given** uma região marcada e o LinkedIn desligado, **When** a pessoa grava os filtros, **Then** o painel avisa que
   nenhum portal ligado procura por região.
3. **Given** uma vaga achada pela consulta da região, **When** ela aparece no relatório, **Then** a etiqueta mostra a
   região.
4. **Given** "aceito morar fora" com Europa em Países para morar, **When** chega uma vaga híbrida em Lisboa, **Then**
   ela não vai para Fora por país de mudança.

---

### User Story 4 - Regiões no perfil (Priority: P3)

Na montagem do perfil (**Meu perfil** na página ou a skill analisar-perfil), a pergunta "De quais países você aceita
vagas?" aceita também regiões ("Europa, Oceania"). O perfil mostra a linha **Países e regiões de interesse**, e a
proposta de filtros leva as regiões para Países de interesse.

**Why this priority**: mantém o perfil e os filtros falando a mesma língua. A pessoa já consegue marcar as regiões pelo
painel (P1).

**Independent Test**: responder a pergunta com "Europa, Estados Unidos" e conferir a linha do perfil e a proposta de
filtros.

**Acceptance Scenarios**:

1. **Given** a resposta "Europa, Estados Unidos", **When** o perfil é gerado, **Then** a linha diz "Países e regiões de
   interesse: Europa, Estados Unidos".
2. **Given** a mesma resposta, **When** a ferramenta propõe os filtros, **Then** Países de interesse traz Europa e
   Estados Unidos.
3. **Given** um nome que não é país nem região do catálogo, **When** a ferramenta propõe os filtros, **Then** ele fica
   de fora, com um aviso.

---

### User Story 5 - Rever vagas cortadas pela regra antiga (Priority: P3)

A pessoa pede para rever as vagas que foram para Fora dos critérios só pela região. A ferramenta mostra quais voltariam
para o relatório pela regra nova, sem gravar. Com o OK da pessoa, elas voltam.

**Why this priority**: corrige o passado (vagas da América Latina e do mundo todo cortadas). Afeta poucas vagas, e a
busca seguinte já usa a regra nova.

**Independent Test**: com vagas em Fora pelo motivo "Vaga aberta a: …", rodar a revisão sem gravar, conferir a lista,
gravar e ver as vagas de volta no relatório.

**Acceptance Scenarios**:

1. **Given** uma vaga em Fora só por "Vaga aberta a: América Latina", com Américas marcada, **When** a revisão roda sem
   gravar, **Then** ela aparece na lista das que voltariam, e nada muda no banco.
2. **Given** a mesma vaga, **When** a revisão roda com o OK da pessoa, **Then** a vaga volta para o relatório e perde o
   motivo de região.
3. **Given** uma vaga em Fora por região e por outro motivo (ex.: moeda), **When** a revisão roda, **Then** ela perde só
   o motivo de região e continua em Fora.

### Edge Cases

- **Config antigo com "Mundo todo" marcado:** a marca é ignorada. Se era a única, a pessoa fica sem região marcada, o
  que quer dizer sem restrição. Antes, só passavam as vagas abertas ao mundo todo; agora passam todas, o que inclui
  essas.
- **Config antigo com "Brasil", "América Latina" ou "Américas":** continua valendo, com o mesmo significado.
- **Região do próprio país da pessoa em Países de interesse** (ex.: América do Sul para quem mora no Brasil): aceita.
  A consulta por região pode trazer vagas do próprio país; elas ficam na área nacional pela regra de área de hoje.
- **Vaga que cita país e região juntos** ("Remote — Germany or EU"): vale a sobreposição de qualquer um dos lugares
  citados.
- **"EMEA" e "APAC"/"Asia Pacific":** são reconhecidas no texto, mas não aparecem como opção para marcar.
  - EMEA = Europa, Oriente Médio e África.
  - APAC = Ásia e Oceania.
- **"South America"** passa a ser América do Sul, não mais América Latina. Para quem mora no Brasil, nada muda na
  prática.
- **Turquia** conta como Ásia, porque o catálogo tem cada país num só continente.
- **Nome de região desconhecido digitado na autorização de trabalho** (texto livre): recusado ao gravar, com a mensagem
  de hoje para país desconhecido, que passa a citar também as regiões.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta MUST ter um catálogo único de regiões com os países de cada uma, tirados da lista de países
  da ferramenta. Cada região MUST valer igual em todo lugar onde aparece. Regiões e países de cada uma:
  - **América do Norte**: Estados Unidos, Canadá, México.
  - **América Central**: Costa Rica, Panamá.
  - **América do Sul**: Argentina, Brasil, Chile, Colômbia, Equador, Peru, Uruguai, Venezuela.
  - **América Latina**: América do Sul, América Central e México.
  - **Américas**: América do Norte e América Latina.
  - **União Europeia**: os 27 países-membros.
  - **Europa**: União Europeia, Reino Unido, Suíça, Noruega e Ucrânia.
  - **Ásia**: os países da Ásia e do Oriente Médio da lista, inclusive a Turquia.
  - **Oceania**: Austrália, Nova Zelândia.
  - **África**: África do Sul, Egito, Marrocos, Nigéria.
- **FR-002**: Regiões aceitas MUST mostrar "Seu país" com o nome do país da pessoa, mais as regiões do catálogo.
  - "Mundo todo" MUST sair das opções.
  - Um config com "mundo" MUST continuar válido, com essa marca ignorada.
- **FR-003**: Uma vaga do exterior MUST ir para Fora dos critérios por região só quando três coisas valem juntas:
  - a pessoa marcou ao menos uma região;
  - a vaga diz a que países ou regiões está aberta, sem incluir o mundo todo;
  - nenhum desses lugares tem país em comum com as regiões marcadas.

  O motivo MUST citar o lugar da vaga e as regiões marcadas.
- **FR-004**: A leitura do local e do texto da vaga MUST reconhecer:
  - "Oceania", "Asia", "Africa", "Central America", "South America" e "North America";
  - "European Union" e "EU", como União Europeia, separada de Europa;
  - "Europe", "EMEA", "APAC" e "Asia Pacific";
  - os nomes que já reconhece hoje.
- **FR-005**: O campo de autorização de trabalho MUST aceitar regiões do catálogo. A elegibilidade MUST considerar que a
  pessoa pode trabalhar em todos os países da região. Uma vaga que exige um lugar MUST servir quando esse lugar tem país
  em comum com os lugares onde a pessoa pode trabalhar, além do próprio país dela.
- **FR-006**: Países de interesse MUST aceitar regiões do catálogo.
  - **Região:** vira uma consulta por cargo em cada portal ligado que procura por região.
  - **Portal que exige país:** MUST rodar só nos países marcados um a um.
  - **Painel:** MUST avisar quando há região marcada e nenhum portal ligado procura por região.
  - **Estimativa de consultas:** MUST contar a região só nos portais que a usam.
- **FR-007**: Países para morar MUST aceitar regiões do catálogo.
  - O corte "presencial ou híbrido fora dos países onde aceita morar" MUST considerar os países da região.
  - A consulta de mudança segue a regra do FR-006.
- **FR-008**: Uma vaga achada só pela consulta de uma região MUST mostrar essa região como lugar da vaga na etiqueta.
  A regra vale quando o local não diz o país.
- **FR-009**: A pergunta do perfil sobre países de interesse MUST aceitar países e regiões.
  - O perfil MUST mostrar a linha "Países e regiões de interesse".
  - A proposta de filtros MUST levar os países e as regiões reconhecidos para Países de interesse.
  - Os nomes não reconhecidos MUST ficar de fora, com aviso.
- **FR-010**: A ferramenta MUST oferecer uma revisão das vagas em Fora dos critérios que têm motivo de região. A revisão
  roda pelo terminal e pelo chat.
  - Sem gravar, MUST mostrar quais perderiam esse motivo pela regra nova e quais voltariam ao relatório.
  - Só com a confirmação da pessoa, MUST gravar: tira o motivo de região e devolve ao relatório a vaga que não tem outro
    motivo.
- **FR-011**: A análise da vaga pela IA MUST receber as regiões aceitas e a autorização de trabalho com os nomes novos
  das regiões.
- **FR-012**: Nada MUST mudar para quem não marca regiões nem usa região nos campos de país, exceto a leitura do texto
  da vaga:
  - vagas abertas à União Europeia, Oceania, Ásia ou África passam a mostrar a região na etiqueta;
  - a elegibilidade dessas vagas segue as regras de hoje.

### Key Entities

- **Região**: nome, conjunto de países e nome em inglês (para a busca por região e para a leitura do texto). Pode ser
  marcável ou só reconhecida no texto (EMEA, APAC).
- **Lugar exigido pela vaga**: países ou regiões que a vaga cita no campo de restrição do portal ou nas frases do
  anúncio. "Mundo todo" quer dizer sem restrição.
- **Filtros da busca internacional**:
  - regiões aceitas, com "Seu país" e as regiões;
  - países de interesse, países para morar e autorização de trabalho, cada um com países e regiões.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A pessoa marca Europa e Oceania em Regiões aceitas com 2 cliques, sem marcar país por país.
- **SC-002**: Com Américas marcada, 0 vagas abertas à América Latina ou ao mundo todo vão para Fora por região.
- **SC-003**: Com autorização na União Europeia, um anúncio que exige qualquer um dos 27 países-membros não vai para
  Fora por exigir lugar.
- **SC-004**: Marcar União Europeia em Países de interesse acrescenta 1 consulta por cargo no LinkedIn, não 27.
- **SC-005**: A revisão das vagas antigas mostra a lista antes de gravar e só grava com a confirmação, em 100% das
  execuções.
- **SC-006**: Os testes de elegibilidade e de área que existem hoje continuam passando. A exceção é "South America" e
  "EU", ajustados para os nomes novos.

## Assumptions

- O catálogo usa só os países que a ferramenta já conhece. Um país fora da lista (ex.: Guatemala) não é reconhecido.
  A região que o contém ("Central America") é reconhecida pelo nome.
- A autorização numa região é declarada pela pessoa. A ferramenta não deduz cidadania nem direito de trabalho:
  constituição IV, "pergunte, não preencha".
- Os nomes em inglês das regiões na busca por região precisam ser aceitos pelo portal. Região que o portal não
  reconhecer fica fora da consulta, com aviso, conforme a pesquisa do plano.
- A página muda pelo processo de sempre da página da ferramenta, como nas specs 043 a 046.
- Foco no Windows, como no resto da ferramenta.
