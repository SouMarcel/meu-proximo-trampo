# Feature Specification: Informações básicas no Meu perfil e idiomas com nível

**Feature Branch**: `036-informacoes-basicas` (worktree `../mpt-036-informacoes-basicas`, saída da `master`; o front na
`frontend-react`)

**Created**: 2026-10-29

**Status**: Aprovada em 2026-10-29

**Input**: Pedido do usuário em 29/10/2026:
- O diálogo "Atualizar candidaturas" deve ter só o necessário para acessar os portais e atualizar o quadro com o
  andamento das candidaturas. O resto vai para o **Meu perfil**, numa aba própria de **informações básicas**.
- Na pergunta de idiomas, cada idioma fica numa linha de uma lista, com o idioma e o nível lado a lado e um **+** para
  adicionar outro. O idioma é escolhido numa lista com, nesta ordem, inglês, português (BR), francês, alemão e
  espanhol. O nível segue a tabela do CEFR (A1 a C2), com o que a pessoa consegue fazer em cada nível.

**Decisões do usuário (29/10)**:
1. O **login guardado** de cada portal fica em "Atualizar candidaturas", porque é informação de acesso aos portais.
2. **Onde a ferramenta preenche** (sites liberados e bloqueados da candidatura assistida) vai para as Informações
   básicas, como seção própria.
3. A lista de idiomas ganha a opção **Outro**, com um campo para escrever o nome. A de níveis ganha **Nativo**.
4. A pergunta separada "Qual o seu nível de inglês?" sai: o nível vem da lista de idiomas.
5. Decidido na implementação, em 29/10: sem resposta à pergunta, a lista já vem com os
   idiomas tirados do currículo ou do LinkedIn. Na resposta, cada idioma da lista substitui a linha do currículo do
   mesmo idioma, para o inglês não aparecer duas vezes. Detalhes da linha antiga, como uma nota de prova, saem dela; a
   pessoa pode pô-los em Certificações.

## Contexto

Hoje o diálogo "Atualizar candidaturas" junta duas coisas diferentes:
- **A leitura do andamento nos portais**: conectar, pronto e desconectar da Gupy e do Indeed, a leitura, a proposta de
  mudanças e o Aplicar.
- **A configuração inteira da candidatura assistida**: dados de contato, login guardado, respostas que a pessoa já deu
  e sites onde a ferramenta preenche.

Os dados de contato e as respostas são informações da pessoa, usadas na carta, nos formulários e na candidatura. Quem
procura onde editar o próprio telefone não pensa em "Atualizar candidaturas". A carta (spec 035) chega a mandar a
pessoa para lá quando falta o nome no cabeçalho.

No passo Perguntas do Meu perfil, os idiomas são um texto livre, "um por linha". Cada pessoa escreve o nível de um
jeito ("avançado", "Professional Working", "fluente", "B2"), e a análise de prontidão para vagas de fora precisa
adivinhar o nível. Logo depois vem "Qual o seu nível de inglês?" com outra escala (básico a fluente). O inglês fica
repetido no perfil e às vezes com níveis diferentes, como "Inglês — Professional Working" numa linha e
"Inglês (nível declarado): avancado" na outra.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Informações básicas no Meu perfil (Priority: P1)

A pessoa abre **Meu perfil** e encontra a aba **Informações básicas**, ao lado de "Currículo base" e "Análises". Na
aba ficam três seções:
1. **Seus dados de contato**, com "Propor a partir do currículo", Salvar e Apagar.
2. **Respostas que você já deu**, com Apagar em cada uma.
3. **Onde a ferramenta preenche**: sites conhecidos, sites liberados com Revogar e sites onde ela nunca preenche.

Tudo funciona como hoje no diálogo, só que no lugar novo. A aba aparece também em "Primeiros passos", antes de o
perfil existir, porque os dados de contato não dependem dele.

**Why this priority**: é o centro do pedido. Os dados da pessoa ficam onde ela procura por eles.

**Independent Test**:
- Abrir Meu perfil, ir a Informações básicas, mudar o telefone e salvar. O telefone novo aparece no cabeçalho da
  próxima carta e é usado na candidatura assistida.
- Apagar uma resposta guardada: ela some da lista e deixa de ser reaproveitada.

**Acceptance Scenarios**:

1. **Given** o perfil gravado, **When** a pessoa abre Meu perfil, **Then** vê a aba Informações básicas ao lado de
   Currículo base e Análises.
2. **Given** nenhum perfil gravado (Primeiros passos), **When** a pessoa abre o diálogo, **Then** a aba Informações
   básicas também aparece e salva os dados de contato.
3. **Given** a aba aberta, **When** a pessoa clica em "Propor a partir do currículo", **Then** os campos vazios são
   preenchidos com a proposta, e nada é gravado até ela clicar em Salvar (como na spec 033).
4. **Given** um site liberado, **When** a pessoa clica em Revogar na aba, **Then** a ferramenta deixa de preencher
   nele.
5. **Given** a página aberta em outro aparelho, **When** a pessoa abre a aba, **Then** vê o aviso de que esses dados
   só podem ser vistos e mudados no computador onde a ferramenta roda.

---

### User Story 2 - "Atualizar candidaturas" só com o acesso aos portais (Priority: P1)

O diálogo "Atualizar candidaturas" passa a ter:
- os portais, com Conectar, Pronto e Desconectar;
- o **login guardado** de cada portal, com Guardar, Trocar e Apagar;
- a leitura, a proposta de mudanças, o Aplicar e o "Importar como histórico".

Os dados de contato, as respostas e os sites saem dele. Uma linha curta avisa onde eles estão agora: "Seus dados de
contato, respostas guardadas e sites da candidatura assistida ficam em Meu perfil → Informações básicas."

**Why this priority**: é a outra metade do pedido. Sem ela, os dados ficariam em dois lugares.

**Independent Test**: abrir "Atualizar candidaturas" e ver só portais, login guardado e a leitura. Conectar, ler e
aplicar funcionam como antes.

**Acceptance Scenarios**:

1. **Given** o diálogo aberto, **When** a pessoa olha as seções, **Then** vê Portais, Login guardado e a leitura, e
   não vê dados de contato, respostas nem sites.
2. **Given** o diálogo aberto, **When** a pessoa guarda ou apaga o login de um portal, **Then** funciona como hoje (a
   senha vai para o `.env` e nunca volta para a página).
3. **Given** o diálogo aberto, **When** a pessoa procura os dados de contato, **Then** a linha de aviso indica Meu
   perfil → Informações básicas.

---

### User Story 3 - Idiomas com nível, numa lista (Priority: P1)

No passo **Perguntas** do Meu perfil, a pergunta "Quais idiomas você fala e em que nível?" mostra uma lista de linhas.
Cada linha tem:
- um **idioma**, escolhido numa lista com Inglês, Português (BR), Francês, Alemão, Espanhol e Outro, nessa ordem.
  "Outro" abre um campo para escrever o nome do idioma;
- um **nível**: A1 Iniciante, A2 Básico, B1 Intermediário, B2 Intermediário superior, C1 Avançado, C2 Proficiência
  plena e Nativo. Abaixo do nível escolhido aparece o que a pessoa consegue fazer nele (tabela abaixo);
- um **×** para remover a linha.

O botão **+** adiciona uma linha. Cada idioma é gravado como um item do perfil no formato
"Inglês — B2 (Intermediário superior)" ou "Português (BR) — Nativo".

| Nível | Nome | O que a pessoa consegue fazer |
|---|---|---|
| A1 | Iniciante | Frases básicas do cotidiano, apresentações simples |
| A2 | Básico | Textos curtos e informações previsíveis |
| B1 | Intermediário | Textos claros sobre assuntos familiares |
| B2 | Intermediário superior | Textos complexos, inclusive técnicos da própria área |
| C1 | Avançado | Textos longos e implícitos, uso flexível do idioma |
| C2 | Proficiência plena | Compreende com facilidade praticamente tudo |
| Nativo | Nativo | Língua materna |

A coluna "Na prova de proficiência" da tabela do pedido fica de fora: ela trata de editais de pós-graduação, não de
vagas.

**Why this priority**: o nível padronizado deixa o perfil, o currículo e a análise de prontidão para vagas de fora
consistentes, sem adivinhar o nível escrito à mão.

**Independent Test**: responder Inglês B2 e Português (BR) Nativo e concluir as perguntas. O perfil traz as duas
linhas no formato acima, e a análise de prontidão mostra o inglês como pronto.

**Acceptance Scenarios**:

1. **Given** a pergunta de idiomas sem resposta, **When** ela aparece, **Then** mostra uma linha vazia (idioma e
   nível) e o botão +.
2. **Given** uma linha preenchida, **When** a pessoa clica em +, **Then** aparece outra linha vazia abaixo.
3. **Given** duas linhas, **When** a pessoa clica no × de uma, **Then** ela sai da lista.
4. **Given** "Outro" no idioma, **When** a pessoa escreve "Italiano" e escolhe A2, **Then** o item gravado é
   "Italiano — A2 (Básico)".
5. **Given** um nível escolhido, **When** a pessoa olha a linha, **Then** vê o que esse nível significa.
6. **Given** uma linha com idioma e sem nível, **When** a pessoa clica em Próxima, **Then** a ferramenta avisa que
   falta o nível daquele idioma e não avança.
7. **Given** a mesma língua em duas linhas, **When** a pessoa clica em Próxima, **Then** a ferramenta avisa da
   repetição e não avança.
8. **Given** linhas todas vazias, **When** a pessoa clica em Próxima ou Pular, **Then** a pergunta fica sem resposta,
   como hoje.

---

### User Story 4 - Respostas antigas e a pergunta de inglês (Priority: P2)

Quem já respondeu idiomas em texto livre não perde nada, e a ferramenta não escolhe nível por ela:
- Ao reabrir a pergunta, cada linha antiga vira uma linha da lista. O nível só vem escolhido quando a linha antiga
  traz a sigla do CEFR (A1 a C2) ou "nativo"/"native".
- Palavras como "fluente", "avançado" ou "Professional Working" não têm equivalência exata no CEFR. Nesses casos a
  linha vem com o idioma escolhido, o nível em branco e o texto antigo ao lado ("você tinha escrito: …"), para a
  pessoa escolher o nível.
- Quando nem o idioma é reconhecido, a linha vem como "Outro", com o texto antigo no campo.
- Pular continua como hoje: deixa a pergunta sem resposta.

A pergunta "Qual o seu nível de inglês?" deixa de ser feita. Quem já a respondeu continua com essa linha no perfil até
responder de novo a pergunta de idiomas com o inglês na lista. A partir daí, a resposta antiga não entra mais no
perfil.

**Why this priority**: evita que a mudança apague ou duplique o que a pessoa já disse.

**Independent Test**:
- Com as respostas antigas "Inglês — Professional Working", "Português — nativo" e "Espanhol — B1", reabrir a
  pergunta. Aparecem Inglês com o nível em branco e o texto antigo ao lado, Português (BR) Nativo e Espanhol B1.
- Com a pergunta respondida de novo e o inglês na lista, o perfil não traz mais "Inglês (nível declarado)".

**Acceptance Scenarios**:

1. **Given** respostas antigas em texto livre, **When** a pessoa reabre a pergunta, **Then** vê uma linha para cada
   resposta antiga. O nível vem escolhido só com sigla do CEFR ou "nativo". Nas outras, aparece o texto antigo ao lado
   do nível em branco, e a ferramenta pede o nível antes de avançar.
2. **Given** o passo Perguntas, **When** a pessoa passa por ele, **Then** não aparece mais a pergunta "Qual o seu nível
   de inglês?".
3. **Given** a resposta antiga de nível de inglês e o inglês na nova lista, **When** o perfil é montado, **Then** o
   inglês aparece uma vez só, com o nível da lista.

---

### User Story 5 - Os avisos apontam o lugar novo (Priority: P3)

Os textos que mandam a pessoa para "Atualizar candidaturas → … dados de contato" ou "… sites" passam a apontar
"Meu perfil → Informações básicas":
- o aviso da carta sem dados de contato;
- o aviso de "revogar depois" ao liberar um site na candidatura assistida;
- o README;
- a documentação da API e as skills.

Também é corrigido o texto de "Respostas que você já deu", que ainda diz que salário nunca fica guardado. Desde a spec
035 a remuneração atual fica guardada; só a pretensão salarial e a relocação não ficam.

**Why this priority**: sem isso, a pessoa é mandada para um lugar onde o item não está mais.

**Independent Test**: gerar uma carta sem dados de contato. O aviso indica Meu perfil → Informações básicas.

**Acceptance Scenarios**:

1. **Given** nenhum dado de contato salvo, **When** a carta é gerada, **Then** o aviso indica Meu perfil →
   Informações básicas.
2. **Given** o pedido de liberar um site na candidatura assistida, **When** a pessoa lê o aviso, **Then** ele diz que
   dá para revogar em Meu perfil → Informações básicas.

### Edge Cases

- **Outro aparelho**: as Informações básicas são só deste computador, como hoje. Em outro aparelho, a aba mostra o
  aviso e não mostra os dados.
- **Outro sem nome**: com "Outro" escolhido e o campo vazio, a ferramenta pede o nome do idioma antes de avançar.
- **Português (BR) e "Outro: português"**: os dois contam como o mesmo idioma no aviso de repetição.
- **Resposta antiga sem idioma reconhecível** (ex.: "Libras — intermediário"): vira "Outro" com o texto antigo, sem
  descartar nada.
- **Idiomas tirados do currículo ou do LinkedIn** (decisão 5): sem resposta à pergunta, eles aparecem como linhas da
  lista, com a mesma conversão das respostas antigas. Respondida a pergunta, a linha do material com um idioma que
  está na lista sai do perfil. Os idiomas que não estão na lista continuam como estão.
- **Pergunta de idiomas pulada**: o diagnóstico continua apontando "Idiomas vazios" quando não há idioma em lugar
  nenhum, como hoje.
- **Candidatura assistida desligada**: as Informações básicas aparecem e funcionam mesmo assim. Os dados de contato
  servem também à carta.

## Requirements *(mandatory)*

### Functional Requirements

**Informações básicas e o diálogo de candidaturas**

- **FR-001**: O Meu perfil MUST ter a aba "Informações básicas", visível com ou sem perfil gravado, com as seções Seus
  dados de contato, Respostas que você já deu e Onde a ferramenta preenche, com as mesmas ações de hoje.
- **FR-002**: O diálogo "Atualizar candidaturas" MUST mostrar só os portais (Conectar, Pronto, Desconectar), o login
  guardado de cada portal e a leitura com a proposta, o Aplicar e o "Importar como histórico".
- **FR-003**: O diálogo "Atualizar candidaturas" MUST ter uma linha que indique Meu perfil → Informações básicas para
  os dados de contato, as respostas guardadas e os sites.
- **FR-004**: Nenhuma regra de gravação muda:
  - os dados de contato continuam só neste computador e nunca vão para a IA;
  - a proposta a partir do currículo não grava sozinha;
  - a senha nunca volta para a página;
  - os domínios bloqueados não podem ser liberados.
- **FR-005**: Em outro aparelho, a aba MUST mostrar que esses dados só podem ser vistos e mudados no computador onde a
  ferramenta roda.

**Idiomas**

- **FR-006**: A pergunta de idiomas MUST ser uma lista de linhas, cada uma com idioma, nível e ×, e um botão + que
  adiciona uma linha.
- **FR-007**: As opções de idioma MUST ser, nesta ordem: Inglês, Português (BR), Francês, Alemão, Espanhol e Outro.
  "Outro" MUST abrir um campo de texto para o nome.
- **FR-008**: As opções de nível MUST ser A1 Iniciante, A2 Básico, B1 Intermediário, B2 Intermediário superior, C1
  Avançado, C2 Proficiência plena e Nativo. A linha MUST mostrar o que a pessoa consegue fazer no nível escolhido.
- **FR-009**: Cada linha MUST ser gravada como `Idioma — Sigla (Nome do nível)`, ex.: "Inglês — B2 (Intermediário
  superior)", ou `Idioma — Nativo`.
- **FR-010**: A ferramenta MUST impedir o avanço, com um aviso que nomeia a linha, quando:
  - uma linha tem idioma sem nível;
  - "Outro" está sem nome;
  - o mesmo idioma aparece duas vezes.
  Linhas totalmente vazias são ignoradas.
- **FR-011**: Ao reabrir a pergunta, cada resposta antiga em texto livre MUST virar uma linha da lista, sem perder o
  texto. O nível MUST vir escolhido só quando a resposta traz a sigla do CEFR ou "nativo"/"native". Nos outros
  casos, o nível fica em branco com o texto antigo à vista (User Story 4).
- **FR-012**: A pergunta "Qual o seu nível de inglês?" MUST sair do passo Perguntas.
- **FR-013**: Quando a lista de idiomas tem o inglês, a resposta antiga de nível de inglês MUST deixar de entrar no
  perfil. Sem inglês na lista, a resposta antiga continua como está.
- **FR-013a** (decisão 5): Sem resposta à pergunta, as linhas MUST vir dos idiomas tirados dos materiais. Na montagem
  do perfil, a linha do material com um idioma que está na resposta MUST sair.
- **FR-014**: A análise de prontidão para vagas de fora MUST reconhecer o nível gravado no formato novo. Pelo
  reconhecimento de hoje: B1 é intermediário, B2 é avançado, C1 e C2 são fluente e Nativo é nativo.

**Textos**

- **FR-015**: Os avisos e os documentos que apontam os dados de contato ou os sites em "Atualizar candidaturas" MUST
  apontar Meu perfil → Informações básicas. São eles:
  - o aviso da carta;
  - o aviso de liberar um site;
  - o README;
  - a documentação da API;
  - as skills, se citarem.
- **FR-016**: O texto de "Respostas que você já deu" MUST dizer que a pretensão salarial e a relocação nunca ficam
  guardadas, sem dizer que o salário nunca fica.

### Key Entities

- **Idioma declarado**: idioma (da lista ou escrito em "Outro") e nível (CEFR ou Nativo). É gravado como um item de
  texto na resposta de idiomas do perfil.
- **Informações básicas**: os dados que já existem hoje, sem mudar onde são guardados:
  - dados de contato (`dash/dados/contato.json`);
  - respostas guardadas (`dash/dados/respostas_formulario.json`);
  - sites liberados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir do botão Meu perfil, a pessoa chega aos próprios dados de contato em até 2 cliques.
- **SC-002**: O diálogo "Atualizar candidaturas" tem no máximo três blocos (portais, login guardado e leitura), contra
  os seis de hoje.
- **SC-003**: Com idiomas respondidos pela lista, 100% das linhas de idioma do perfil têm um nível que a análise de
  prontidão reconhece.
- **SC-004**: O inglês aparece uma vez só no perfil de quem responde a lista com o inglês.
- **SC-005**: Nenhuma resposta antiga de idioma se perde ao reabrir a pergunta: cada linha antiga aparece como linha
  da lista ou como texto em "Outro".
- **SC-006**: Os testes automáticos do projeto continuam passando, e o tipo do front confere sem erro.

## Assumptions

- O mapeamento dos níveis para a análise de prontidão segue o reconhecimento que já existe, que usa a escala do
  LinkedIn. Ele não é mudado nesta spec.
- A aba Informações básicas reaproveita os mesmos dados e as mesmas rotas de hoje. Nada muda no formato dos arquivos
  guardados.
- "Contato no perfil", na revisão do perfil (e-mail, telefone e LinkedIn do `perfil.md`), continua onde está. Juntar os
  dois contatos fica fora desta spec.
- O login guardado continua servindo só à candidatura assistida. Usá-lo também no Conectar de "Atualizar
  candidaturas" fica fora desta spec.
- O front é mudado na branch `frontend-react` e chega à `master` pelo PR da Action, como nas specs 033 a 035.
