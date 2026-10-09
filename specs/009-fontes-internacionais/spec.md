# Feature Specification: Fontes internacionais e elegibilidade

**Feature Branch**: `009-fontes-internacionais` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 8 do roteiro: fontes internacionais e elegibilidade. Fontes novas,
públicas e sem login, só na busca internacional: Remotive, Himalayas, RemoteOK, Jobicy, We Work
Remotely, Get on Board e as páginas de vagas de empresas no Greenhouse, Lever e Ashby (lista de
empresas da pessoa, identificador descoberto pelo link). Cada fonte traz restrição de local, moeda,
salário, link e sistema de candidatura quando houver; descrição maior. A pessoa escolhe as fontes no
painel internacional (desligadas até escolher). Elegibilidade sem IA pelo campo de restrição e por
frases comuns do anúncio, comparadas com as regiões aceitas e as caixas da pessoa: exige autorização
onde ela não tem e não patrocina → Fora dos critérios com o motivo; presencial/híbrido no exterior só
com aceito morar fora; sponsor ou relocation = sinal positivo; ambíguo passa. Frases numa lista
padrão ampliável. Adicionar Vaga reconhece esses links. README com os termos de cada fonte. Consultas
espaçadas. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mais vagas do exterior, de fontes feitas para remoto (Priority: P1)

Com a busca internacional ligada, a pessoa marca no painel internacional as fontes que quer usar:
Remotive, Himalayas, RemoteOK, Jobicy, We Work Remotely e Get on Board. A próxima busca consulta
também essas fontes, com os cargos em inglês, e as vagas aparecem na aba Internacional com a
etiqueta do país ou da região, a fonte, a moeda e o salário quando o portal informa.

**Why this priority**: o Indeed sozinho traz pouco do exterior; essas fontes são feitas para vagas
remotas e informam melhor região, salário e moeda.

**Independent Test**: ligar duas fontes, buscar e ver vagas delas na aba Internacional, cada uma com a
fonte, a região e o link para a vaga original.

**Acceptance Scenarios**:

1. **Given** a busca internacional ligada e nenhuma fonte nova marcada, **When** a busca roda,
   **Then** nada muda em relação a hoje.
2. **Given** fontes marcadas, **When** a busca roda, **Then** cada fonte é consultada só na parte
   internacional, com os cargos em inglês, e as vagas aparecem na aba Internacional.
3. **Given** uma vaga dessas fontes, **When** a pessoa abre o detalhe, **Then** vê a fonte, a
   restrição de região, a moeda e o salário (quando informados), o link da vaga original e o de
   candidatura.
4. **Given** uma fonte fora do ar ou que recusa a consulta, **When** a busca roda, **Then** as outras
   seguem e o resumo da busca aponta o erro daquela fonte.

---

### User Story 2 - Elegibilidade antes da nota (Priority: P1)

Antes de qualquer IA, a ferramenta lê a restrição de região informada pelo portal e frases comuns do
anúncio ("US only", "must be authorized to work in the US", "we do not sponsor visas", "open to
candidates in LATAM", "relocation package") e compara com o que a pessoa marcou: regiões aceitas,
países onde tem autorização de trabalho, se precisa de patrocínio de visto e se aceita morar fora.
Vaga que exige autorização num país onde a pessoa não tem e não oferece patrocínio vai para **Fora
dos critérios** com o motivo; vaga presencial ou híbrida no exterior só passa com "aceito morar fora"
(e no país escolhido, quando houver lista); vaga que oferece sponsor ou relocation ganha um **sinal
positivo** visível; o que for ambíguo passa.

**Why this priority**: boa parte das vagas "remotas" do exterior só aceita quem mora ou tem
autorização num país; sem esse corte, a pessoa perde tempo com vagas impossíveis.

**Independent Test**: com a pessoa sem autorização nos EUA e precisando de sponsor, ver uma vaga "US
only, no visa sponsorship" em Fora dos critérios com o motivo, uma "open to LATAM" passar, e uma
"visa sponsorship available" passar com o sinal positivo.

**Acceptance Scenarios**:

1. **Given** uma vaga que exige autorização nos EUA e não patrocina, e a pessoa sem autorização lá,
   **When** a vaga chega, **Then** vai para Fora dos critérios com "Exige autorização de trabalho nos
   Estados Unidos e não patrocina visto".
2. **Given** a mesma vaga e a pessoa com autorização nos EUA, **When** a vaga chega, **Then** passa.
3. **Given** uma vaga aberta à América Latina e a pessoa com essa região aceita, **When** a vaga
   chega, **Then** passa.
4. **Given** uma vaga presencial em Lisboa e a pessoa sem "aceito morar fora", **When** a vaga chega,
   **Then** vai para Fora dos critérios com o motivo; com "aceito morar fora" em Portugal, passa.
5. **Given** uma vaga que oferece patrocínio ou relocation, **When** ela aparece, **Then** mostra o
   sinal positivo na listagem e no detalhe.
6. **Given** um anúncio sem nenhuma frase reconhecida, **When** a vaga chega, **Then** passa.

---

### User Story 3 - Empresas que a pessoa acompanha (Greenhouse, Lever, Ashby) (Priority: P2)

No painel internacional, a pessoa cola o link da página de vagas das empresas que acompanha (por
exemplo a página de carreiras no Greenhouse, Lever ou Ashby). A ferramenta reconhece o sistema e o
identificador da empresa pelo link e, nas buscas, traz as vagas abertas dessas empresas que batem com
os cargos em inglês, com o link de candidatura direto.

**Why this priority**: as empresas que a pessoa quer de verdade nem sempre anunciam nos portais; a
página de vagas delas é a fonte mais confiável.

**Independent Test**: colar o link de carreiras de uma empresa no Greenhouse, ver a empresa
reconhecida no painel e, na busca, as vagas dela que batem com os cargos.

**Acceptance Scenarios**:

1. **Given** o link de carreiras de uma empresa no Greenhouse, Lever ou Ashby, **When** a pessoa cola,
   **Then** a empresa aparece na lista com o sistema reconhecido; link que não é desses sistemas é
   recusado com a explicação.
2. **Given** empresas na lista, **When** a busca internacional roda, **Then** as vagas abertas delas
   que batem com algum cargo em inglês entram na aba Internacional, com o link de candidatura.

---

### User Story 4 - Adicionar Vaga e frases da pessoa (Priority: P3)

O Adicionar Vaga reconhece links de vagas do Greenhouse, Lever, Ashby e das fontes novas e lê os
dados direto da fonte (título, empresa, local, restrição, descrição, salário). No painel, a pessoa
pode acrescentar frases próprias de restrição ("must reside in Canada") e de sinal positivo ("visa
support"), além das padrão.

**Why this priority**: completa o caminho manual e deixa a regra ajustável sem mexer no código.

**Independent Test**: colar o link de uma vaga do Lever e ver os dados preenchidos e a elegibilidade
aplicada; acrescentar uma frase própria e ver uma vaga com ela ser cortada.

**Acceptance Scenarios**:

1. **Given** o link de uma vaga do Greenhouse, Lever ou Ashby, **When** adicionada, **Then** os dados
   vêm da fonte e a elegibilidade é aplicada.
2. **Given** uma frase própria de restrição, **When** uma vaga a contém, **Then** ela vai para Fora dos
   critérios citando a frase.

---

### Edge Cases

- Fonte que devolve vagas antigas ou de outros cargos: os cortes de sempre (janela de publicação,
  cargo, empresa excluída, idioma) valem também para elas.
- A mesma vaga em duas fontes (por exemplo Remotive e a página da empresa): fica uma só, com as duas
  etiquetas de plataforma, como hoje entre portais.
- Restrição em formato livre ("USA, Canada", "Americas only", "EMEA"): reconhecida pelo país ou pela
  região; o que não for reconhecido não corta.
- Anúncio que diz ao mesmo tempo "US only" e "we sponsor visas": não corta (o patrocínio vence), e
  ganha o sinal positivo.
- Vaga que exige autorização num país onde a pessoa marcou autorização: passa.
- Empresa removida da página do sistema (link quebrado): a busca avisa e segue.
- Limites de consulta: uma consulta por fonte por cargo, espaçadas, e o número de consultas aparece
  no painel e na confirmação da busca.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta MUST oferecer as fontes Remotive, Himalayas, RemoteOK, Jobicy, We Work
  Remotely e Get on Board, todas públicas e sem login, só na busca internacional.
- **FR-002**: As fontes novas MUST vir desligadas; a pessoa MUST escolher quais usar no painel Filtros
  da busca internacional.
- **FR-003**: Cada vaga de fonte nova MUST trazer, quando o portal informa: restrição de região ou
  país, moeda, salário, link da vaga original, link de candidatura e sistema de candidatura; a
  descrição MUST ser guardada inteira até um limite maior que o de hoje.
- **FR-004**: A pessoa MUST poder informar empresas pelo link da página de vagas no Greenhouse, Lever
  ou Ashby; a ferramenta MUST reconhecer o sistema e o identificador e recusar link de outro sistema
  com a explicação.
- **FR-005**: As vagas das empresas acompanhadas MUST ser filtradas pelos cargos em inglês antes de
  entrar no relatório.
- **FR-006**: A elegibilidade MUST ser avaliada sem IA, pelo campo de restrição do portal e por frases
  do anúncio, contra as regiões aceitas, os países com autorização, a necessidade de sponsor e "aceito
  morar fora".
- **FR-007**: Vaga que exige autorização ou residência num país onde a pessoa não tem autorização, sem
  oferecer patrocínio quando a pessoa precisa, MUST ir para Fora dos critérios com o motivo.
- **FR-008**: Vaga presencial ou híbrida no exterior MUST passar só com "aceito morar fora" (e no país
  escolhido, quando houver lista).
- **FR-009**: Vaga restrita a uma região fora das regiões aceitas MUST ir para Fora dos critérios com
  o motivo, quando a pessoa marcou regiões.
- **FR-010**: Oferta de patrocínio ou relocation MUST aparecer como sinal positivo na listagem e no
  detalhe.
- **FR-011**: O que for ambíguo (sem campo nem frase reconhecida) MUST passar.
- **FR-012**: As frases de restrição e de sinal positivo MUST vir de uma lista padrão que a pessoa pode
  ampliar no painel.
- **FR-013**: O Adicionar Vaga MUST reconhecer links de vagas do Greenhouse, Lever, Ashby e das fontes
  novas e ler os dados direto da fonte.
- **FR-014**: As consultas às fontes novas MUST ser espaçadas e respeitar os limites de cada uma; o
  número de consultas MUST aparecer no painel e na confirmação da busca.
- **FR-015**: O README MUST citar os termos de uso de cada fonte (citar a fonte, linkar a vaga
  original) e a página da vaga MUST mostrar a fonte e o link original.
- **FR-016**: Textos MUST estar em português do Brasil.

### Key Entities *(include if feature involves data)*

- **Fonte internacional**: nome, se está ligada, limites de consulta e termos de uso.
- **Empresa acompanhada**: nome, sistema (Greenhouse, Lever, Ashby), identificador e link da página.
- **Restrição da vaga**: países ou regiões exigidos, exige autorização, oferece patrocínio, oferece
  relocation, presencial/híbrido e a frase que deu origem a cada um.
- **Frases de elegibilidade**: listas padrão e da pessoa, de restrição e de sinal positivo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com as fontes desligadas, a busca é igual à de antes desta fase.
- **SC-002**: Num conjunto de teste de anúncios com restrições conhecidas, 100% das vagas impossíveis
  para a pessoa (sem autorização e sem patrocínio, região não aceita, presencial sem aceitar mudar)
  vão para Fora dos critérios com o motivo certo, e nenhuma vaga ambígua é cortada.
- **SC-003**: 100% das vagas com oferta de sponsor ou relocation mostram o sinal positivo.
- **SC-004**: Uma fonte fora do ar não impede as outras de trazer vagas.
- **SC-005**: A pessoa acrescenta uma empresa pelo link e vê as vagas dela na próxima busca, sem
  editar arquivo.

## Assumptions

- As fontes e o formato de cada uma foram conferidos em 06/10/2026 (todas responderam sem chave);
  mudanças de formato de um portal afetam só aquela fonte, com aviso.
- Torre e outras fontes ficam fora desta fase.
- Regiões reconhecidas: Brasil, América Latina (LATAM), Américas, Estados Unidos/Canadá (North America),
  Europa/EMEA, mundo todo.
- A elegibilidade sem IA não substitui a análise com IA, que continua apontando o que ela não pega.
- O limite maior de descrição é de 12.000 caracteres.
- Verificação só no Windows; os testes usam respostas gravadas de cada fonte (sem consultar os
  portais), mais uma consulta real pequena a cada fonte com o OK da pessoa.
