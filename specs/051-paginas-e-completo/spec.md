# Feature Specification: Limite de páginas que vale e currículo completo

**Feature Branch**: `051-paginas-e-completo` (worktree saída da `master`)

**Created**: 2026-11-17

**Status**: Aprovada em 2026-11-17

**Input**: Pedido do usuário depois de gerar currículos pela página. O limite de páginas escolhido (até 2) não é
respeitado: dos 6 currículos gerados até aqui, 4 saíram com 3 páginas, entre eles todos os currículos base (7
experiências e de 24 a 28 itens). Ele também quer um currículo novo, completo e livre, com todos os dados que a
ferramenta tem dele, "tipo o perfil do LinkedIn".

**Decisões do usuário (17/11)**:
1. "Até 2 páginas" continua sendo um **objetivo**, como hoje. Quando o currículo passa do limite, a página avisa que o
   perfil tem coisa demais para ele.
2. Uma opção nova torna o limite **obrigatório**. Se o currículo passar, a IA encurta, mantendo as 3 experiências mais
   recentes e tirando ou resumindo as antigas. Se não der certo, o currículo fica como é hoje.
3. O currículo **completo** (sem limite de páginas) aparece **só no currículo base**. No currículo de uma vaga, as
   opções continuam sendo 1 ou 2 páginas.

## Contexto

Hoje o pedido à IA diz só "Páginas: até 2". A IA não consegue medir páginas e não recebe nenhum limite concreto de
conteúdo, então escreve tudo o que o perfil tem. Depois de gerar, a ferramenta mede as páginas do PDF e só anota que
o currículo passou do limite. A lista de currículos mostra "3 página(s) (acima do limite de 2)", sem dizer por quê nem
o que fazer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - O currículo cabe no limite com mais frequência, e o aviso diz o que fazer quando não cabe (Priority: P1)

A pessoa gera um currículo (base ou de uma vaga) com "Até 2 páginas", como sempre. O pedido à IA passa a trazer um
limite concreto de conteúdo:
- um resumo curto;
- as experiências mais recentes com poucos itens cada;
- as antigas só com uma linha ou um item;
- poucos cursos;
- um total aproximado de palavras.

Com isso, a maior parte dos currículos cabe nas 2 páginas. Quando ainda passa, a lista de currículos mostra um aviso
claro: o perfil tem conteúdo demais para o limite, e a pessoa pode marcar "Limite de páginas obrigatório" para a IA
encurtar.

**Why this priority**: é a queixa principal e beneficia todo currículo gerado, sem a pessoa mudar nada.

**Independent Test**: gerar um currículo base com "Até 2 páginas" a partir de um perfil com 7 experiências. O pedido à
IA traz o limite de conteúdo. Se o PDF passar de 2 páginas, a lista mostra o aviso com a sugestão da opção
obrigatória.

**Acceptance Scenarios**:

1. **Given** o limite de 2 páginas, **When** a ferramenta monta o pedido à IA, **Then** o pedido traz o limite
   concreto de conteúdo para 2 páginas (resumo, quantas experiências completas, quantos itens, cursos e total de
   palavras), e não só "até 2 páginas".
2. **Given** o limite de 1 página, **When** o pedido é montado, **Then** ele traz um limite de conteúdo menor que o de
   2 páginas.
3. **Given** um currículo que passou do limite sem a opção obrigatória, **When** a pessoa olha a lista de currículos,
   **Then** vê um ponto "conferir" dizendo quantas páginas deram, qual era o objetivo e que marcar "Limite de páginas
   obrigatório" faz a IA encurtar.

---

### User Story 2 - Limite de páginas obrigatório (Priority: P1)

No diálogo do currículo, a pessoa marca a caixa **Limite de páginas obrigatório**, que vem desmarcada. Se o currículo
gerado passar do limite, a ferramenta pede à IA uma versão mais curta:
- mantém completas as 3 experiências mais recentes;
- resume ou tira as mais antigas;
- corta itens menos ligados ao alvo;
- nunca acrescenta fato.

Durante o encurtamento, a página mostra a etapa "encurtando". A ferramenta mede de novo e tenta no máximo duas vezes.
Se a IA não conseguir, o currículo fica na versão longa, como hoje, com um aviso.

**Why this priority**: é a garantia pedida pelo usuário para quem precisa do limite à risca.

**Independent Test**: IA falsa que devolve primeiro um currículo de 3 páginas e depois uma versão menor que cabe em 2.
Com a caixa marcada, o resultado final tem 2 páginas, foram duas chamadas à IA e o registro do currículo diz que ele
foi encurtado de 3 para 2. Com a caixa desmarcada, há uma chamada só e o aviso da US1 aparece.

**Acceptance Scenarios**:

1. **Given** a caixa marcada e um currículo que deu 3 páginas para um limite de 2, **When** a geração continua,
   **Then** a ferramenta pede a versão mais curta à IA, monta de novo, mede de novo e fica com a versão que cabe.
2. **Given** a versão encurtada, **When** ela é gravada, **Then** o registro do currículo diz de quantas páginas
   para quantas ele foi e em quantas tentativas.
3. **Given** uma resposta da IA ao encurtar que fica **maior** que a anterior (mais texto ou mais experiências),
   **When** a ferramenta a recebe, **Then** descarta essa resposta e fica com a anterior.
4. **Given** uma falha da IA ao encurtar (erro, resposta inválida ou ainda acima do limite depois de 2 tentativas),
   **When** a geração termina, **Then** o currículo fica com a melhor versão que tiver, a geração não é dada como
   falha e a lista mostra um ponto "conferir" dizendo que a IA não conseguiu deixar no limite, com sugestões do que
   cortar.
5. **Given** a versão final, **When** a conferência roda, **Then** ela confere essa versão contra o perfil, como
   qualquer currículo.

---

### User Story 3 - Currículo completo no currículo base (Priority: P2)

Em Meu perfil, ao gerar o currículo base, a escolha "Páginas" ganha a opção **Completo (sem limite, tudo do perfil)**.
Com ela, a IA escreve um currículo com todos os fatos do perfil e dos relatos:
- todas as experiências com todos os itens;
- formação, certificações, cursos, projetos e idiomas.

Ela não corta nada e não tem limite de páginas, mas mantém o layout para ATS e só fatos confirmados. O arquivo leva
"completo" no nome. No diálogo do currículo de uma vaga, essa opção não aparece.

**Why this priority**: é um tipo novo de currículo pedido pelo usuário, útil como referência e para pedidos que aceitam
um currículo longo. Não corrige um problema, por isso fica atrás das US1 e US2.

**Independent Test**: o catálogo do diálogo sem vaga tem a opção Completo; com vaga, não tem. Gerar com Completo envia
à IA a instrução de não cortar nada, não marca "acima do limite", não pede encurtamento e grava o arquivo como
`AAAA-MM-DD-base-completo`.

**Acceptance Scenarios**:

1. **Given** o diálogo do currículo base, **When** ele abre, **Then** "Páginas" tem as opções 1 página, Até 2 páginas e
   Completo.
2. **Given** o diálogo do currículo de uma vaga, **When** ele abre, **Then** a opção Completo não aparece. Um pedido
   que a envie mesmo assim é recusado com mensagem clara.
3. **Given** a escolha Completo, **When** o currículo é gerado, **Then** o pedido à IA diz para usar todos os fatos do
   perfil e dos relatos sem cortar, e o currículo nunca é marcado como acima do limite nem encurtado, mesmo com
   "Limite de páginas obrigatório" marcado.

---

### Edge Cases

- **Sem programa para gerar o PDF** (sem LibreOffice nem Word): as páginas não são medidas. Não há aviso nem
  encurtamento, e o currículo sai como hoje ("páginas não medidas").
- **Currículo pelo chat** (`curriculo.py` direto, sem a IA da página): continua como hoje, com as sugestões de corte
  impressas. Com "Completo" (limite 0), o comando nunca acusa que passou do limite.
- **JSON antigo** sem a técnica nova: continua válido e é montado igual a antes.
- **Análise de reprovação** (spec 049): o "Reescrever e gerar" usa as mesmas técnicas e o mesmo caminho de geração,
  então herda o encurtamento. A opção Completo não existe ali, porque é sempre de uma vaga.
- **Encurtar sem itens antigos para tirar** (3 experiências ou menos): a IA corta itens e o resumo. Se não couber, vale
  a regra da falha.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O pedido de currículo à IA MUST trazer um limite concreto de conteúdo para cada limite de páginas (1 e
  2): tamanho do resumo, quantas experiências recentes ficam completas, quantos itens cada uma tem, o que fica das
  antigas, quantos cursos entram e o total aproximado de palavras.
- **FR-002**: O catálogo de técnicas MUST ter a caixa "Limite de páginas obrigatório", desmarcada por padrão, com uma
  explicação curta do que ela faz.
- **FR-003**: Com a caixa marcada e o currículo medido acima do limite, a ferramenta MUST pedir à IA uma versão mais
  curta, com estas regras:
  - só tirar ou condensar;
  - nunca acrescentar fato;
  - manter completas as 3 experiências mais recentes;
  - números só como estão no perfil.
- **FR-004**: A ferramenta MUST tentar encurtar no máximo 2 vezes. Ela MUST descartar uma resposta com mais texto ou
  mais experiências que a versão anterior.
- **FR-005**: Uma falha ao encurtar MUST manter a melhor versão disponível, sem dar a geração como falha.
- **FR-006**: O registro do currículo MUST guardar o encurtamento: páginas antes, páginas depois e tentativas.
- **FR-007**: Um currículo que termina acima do limite MUST ganhar na conferência um ponto de nível "conferir". A
  mensagem MUST ser diferente com e sem a caixa obrigatória e MUST dizer o que a pessoa pode fazer.
- **FR-008**: A página MUST mostrar a etapa "encurtando" enquanto a IA encurta.
- **FR-009**: A escolha "Páginas" MUST ter a opção Completo (sem limite) só no catálogo do currículo base. A ferramenta
  MUST recusar essa opção num currículo de vaga.
- **FR-010**: Com Completo, o pedido à IA MUST instruir a usar todos os fatos do perfil e dos relatos, sem cortar,
  mantendo o layout para ATS e as regras de fatos confirmados. O currículo MUST NOT ser marcado como acima do limite
  nem encurtado.
- **FR-011**: O currículo base completo MUST ser gravado com "completo" no nome (`AAAA-MM-DD-base-completo`, com o
  sufixo -2, -3… de sempre).
- **FR-012**: A página (front React) MUST NOT precisar de mudança: a caixa nova, a opção nova e a etapa nova chegam
  pelo catálogo e pelo estado da geração, que ela já mostra de forma genérica.
- **FR-013**: As instruções do chat (skill gerar-curriculo) e o contrato da API MUST descrever o limite concreto, a
  opção obrigatória (no chat, quem encurta é o próprio assistente) e o currículo completo.

### Key Entities

- **Técnicas do currículo**: as escolhas da pessoa no diálogo (caixas e opções). Ganham a caixa "Limite de páginas
  obrigatório" e a opção de páginas Completo (valor 0, só no base).
- **Registro do currículo gerado** (meta): ganha o encurtamento (antes, depois, tentativas). O aviso de limite fica nos
  pontos da conferência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o perfil do usuário (7 experiências), o currículo base com "Até 2 páginas" e a opção obrigatória
  sai com 2 páginas em pelo menos 4 de 5 gerações.
- **SC-002**: Sem a opção obrigatória, todo currículo que passa do limite mostra o aviso com a sugestão. Nenhum fica
  só com "(acima do limite de 2)".
- **SC-003**: O currículo completo traz todas as experiências do perfil (7 de 7) e nenhum fato que não esteja no
  perfil ou nos relatos (conferência sem ponto "bloquear" por fato novo).
- **SC-004**: A opção Completo nunca aparece no diálogo de uma vaga.
- **SC-005**: Os currículos e testes que já existem continuam funcionando: a suíte inteira fica verde.

## Assumptions

- Os números do limite de conteúdo (palavras, itens, cursos) são o ponto de partida. O ajuste fino vem dos testes
  com o perfil real do usuário, dentro desta spec.
- "Experiências mais recentes" segue a ordem em que o currículo as lista (da mais recente para a mais antiga), que é a
  ordem pedida à IA hoje.
- O encurtamento usa a mesma IA escolhida no painel IA, com as reservas da spec 032.
- O aviso entra nos pontos da conferência, que a lista de currículos já mostra, e faz o veredito passar a
  "conferir". Isso é aceitável, porque a pessoa deve olhar o currículo.
- Gerar o currículo pela página já exige IA. Por isso, "sem IA fica como hoje" vale para o caminho do chat e para a
  falha da IA ao encurtar.
