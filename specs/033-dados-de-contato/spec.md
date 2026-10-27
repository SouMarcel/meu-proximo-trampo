# Feature Specification: Dados de contato na candidatura assistida, sem IA

**Feature Branch**: `033-dados-de-contato` (worktree `../meu-proximo-trampo-033`, saída da `master`)

**Created**: 2026-10-28

**Status**: Aprovada em 2026-10-28

**Input**: User description: "vamos seguir com sua proposta" (27–28/10/2026). A proposta: um cadastro único de "Seus
dados de contato", tirado do currículo e confirmado pela pessoa, que a candidatura assistida usa sem IA em qualquer
formulário, reconhecendo o campo pelo sentido. A pessoa aceitou as recomendações:
- os dados vêm do currículo, e a pessoa confirma;
- a edição fica no painel da candidatura assistida;
- endereço e CEP são opcionais.

## Contexto

Na candidatura assistida, nome, e-mail, telefone, cidade e LinkedIn nunca vão à IA. Eles só são preenchidos com o que a
pessoa já respondeu antes, e só quando a pergunta tem o mesmo texto (research R1). Cada site escreve de um jeito ("First
Name", "Nome", "Full name", "Celular"), e a pessoa digita de novo a cada formulário novo. Com a IA fora do ar, sobra mais
ainda para digitar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar e confirmar os dados de contato (Priority: P1)

No painel da candidatura assistida, a pessoa vê "Seus dados de contato". A ferramenta propõe os valores a partir do
currículo base, das respostas já guardadas e da cidade dos filtros. A pessoa confere, corrige e salva. Nada é gravado
antes disso.

**Independent Test**: currículo de exemplo e memória simulados; a proposta traz nome, e-mail, telefone e LinkedIn; nada
é gravado até salvar.

**Acceptance Scenarios**:

1. **Given** um currículo base com nome, e-mail, telefone e LinkedIn, **When** a pessoa pede a proposta, **Then** os
   campos vêm preenchidos para conferir, e nada fica gravado.
2. **Given** a proposta conferida, **When** a pessoa salva, **Then** os dados ficam guardados no computador dela,
   fora do Git.
3. **Given** dados já salvos, **When** a pessoa abre o painel, **Then** vê os valores e pode editar, apagar ou pedir
   uma nova proposta.

### User Story 2 - Preencher os campos de contato em qualquer formulário (Priority: P1)

Em "Preencher esta página", os campos de contato são reconhecidos pelo sentido e preenchidos com os dados salvos, sem
IA. Isso vale para o atributo `autocomplete`, o tipo do campo e os sinônimos em português e inglês.

**Independent Test**: página simulada com "Full name", "E-mail", "Celular", "LinkedIn profile" e campos com
`autocomplete`; todos preenchidos com a fonte "seus dados de contato" e sem chamar a IA.

**Acceptance Scenarios**:

1. **Given** dados de contato salvos, **When** a página pergunta "Full name", "Nome", "E-mail", "Celular" e "LinkedIn
   profile", **Then** a ferramenta preenche cada um com o dado certo e marca a fonte "seus dados de contato".
2. **Given** a IA fora do ar, **When** a pessoa usa Preencher esta página, **Then** os campos de contato são
   preenchidos mesmo assim.
3. **Given** um campo que já tem valor na página, **When** a ferramenta preenche, **Then** ela não troca o valor.
4. **Given** um campo de contato sem dado salvo (ex.: CEP não cadastrado), **When** a ferramenta lê a página, **Then**
   ele vira pergunta, como hoje.

### Edge Cases

- **Nome e sobrenome separados, ou nome completo**: o nome completo junta os dois. Um campo "Name" sozinho recebe o
  nome completo.
- **Telefone**: vai como está salvo. Campos separados de DDI ou DDD e listas de código de país ficam com a pessoa.
- **País em lista**: escolhe a opção que bate com o país salvo (em português ou inglês); sem opção que bata, fica com a
  pessoa.
- **Campo de link genérico** ("Website", "Portfolio"): recebe o portfólio. Sem portfólio, fica com a pessoa. O LinkedIn
  só vai a campo que fala de LinkedIn.
- **Documentos** (CPF, RG, data de nascimento): nunca entram nos dados de contato e nunca são propostos.
- **Mais de um e-mail ou telefone no currículo**: a proposta mostra o primeiro, e a pessoa escolhe ou corrige.
- **Sem currículo base**: a proposta usa só a memória e os filtros, e a pessoa completa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Os dados de contato MUST ter:
  - nome, sobrenome, e-mail, telefone;
  - cidade, estado, país;
  - LinkedIn e portfólio (site, GitHub);
  - endereço e CEP, opcionais.

  O nome completo é a junção de nome e sobrenome. Eles ficam guardados fora do Git, em `dash/dados/`.
- **FR-002**: A proposta MUST vir do currículo base (e-mail, telefone e LinkedIn pela leitura que já existe nos
  primeiros passos; o nome pela primeira linha), das respostas guardadas (ex.: "First Name") e da cidade, do estado e
  do país dos filtros da busca. Nada é gravado sem a pessoa salvar.
- **FR-003**: A candidatura assistida MUST reconhecer o campo de contato pelo atributo `autocomplete`, pelo tipo do
  campo e por sinônimos em português e inglês (research R4).
- **FR-004**: Em "Preencher esta página", os campos de contato reconhecidos MUST ser preenchidos com os dados salvos
  antes da memória e da IA, sem pisar em valor já preenchido. A fonte aparece como "seus dados de contato".
- **FR-005**: Os dados de contato MUST nunca ir para a IA, e o preenchimento deles MUST funcionar com a IA desligada ou
  fora do ar.
- **FR-006**: CPF, RG e data de nascimento MUST nunca ser propostos nem guardados.
- **FR-007**: O painel da candidatura assistida (na página, onde ficam os logins e os sites liberados) MUST mostrar
  "Seus dados de contato", com "Propor a partir do currículo", a edição de cada campo, Salvar e Apagar.
- **FR-008**: Documentação: `dash/API.md` (rotas), README (candidatura assistida) e spec 027 (referência).

### Key Entities

- **Dados de contato**: `{nome, sobrenome, email, telefone, cidade, estado, pais, linkedin, portfolio, endereco, cep}`,
  com textos curtos, em `dash/dados/contato.json`, gravados só quando a pessoa salva.

## Success Criteria *(mandatory)*

- **SC-001**: Num formulário com "Full name", "E-mail", "Celular" e "LinkedIn profile", os quatro campos são
  preenchidos com os dados salvos, sem chamada à IA.
- **SC-002**: Com a IA fora do ar, os campos de contato reconhecidos são preenchidos.
- **SC-003**: Nenhum dado de contato é gravado antes de a pessoa salvar, e nenhum vai para a IA.
- **SC-004**: Na configuração do usuário, a proposta traz nome, e-mail, telefone e LinkedIn do currículo base dele.

## Assumptions

- **Os dados de contato vêm antes da memória**: são o dado que a pessoa confirmou para isso, e a memória continua
  valendo para o resto.
- **Nome pela primeira linha do currículo**: é a convenção comum. Se não parecer um nome (muito longo, com números),
  a proposta fica sem nome e a pessoa digita.
- **Painel**: na página, a seção fica no painel "Contas conectadas", onde já estão os logins e os sites da candidatura
  assistida (front na `frontend-react`).
- **Constituição**: sem emenda. Os dados são da pessoa e confirmados por ela (IV), ficam no computador dela (I) e
  nunca vão à IA.
- **Verificação**: só no Windows.
