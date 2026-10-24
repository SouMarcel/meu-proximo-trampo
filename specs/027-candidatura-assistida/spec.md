# Feature Specification: Candidatura assistida ("preencher e parar")

**Feature Branch**: `027-candidatura-assistida` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-23

**Status**: Em implementação

**Input**: User description: "Analise a possibilidade de a própria IA que estamos colocando no sistema via API
fazer a aplicação na plataforma que homologamos. Ex.: quando clico em seguir com a vaga no Gupy, ela segue com o
processo de aplicação até a confirmação, respondendo perguntas etc. Quero que seja para qualquer portal, mas só
dentro do domínio do portal; imagino que seria necessário anotar no .env os valores de login e senha."

## Contexto

Depois de "Seguir com a vaga", a pessoa ainda tem trabalho manual pela frente:
1. abre o portal e faz o login;
2. responde às mesmas perguntas de formulário de sempre ("por que você?", anos de experiência, nível de inglês);
3. copia trechos do perfil.

A ferramenta já escreve essas respostas: o kit da candidatura tem "Preparar respostas" a partir de perguntas
coladas. Hoje, porém, o caminho é sempre copiar e colar.

A constituição 3.0.0 proíbe que a ferramenta mexa no portal:
- **V:** "nunca clica em 'enviar'";
- **VI:** "Sem automação de candidatura", "Só leitura" e "nunca pede, guarda ou digita senha".

Esta spec propõe um meio-termo. A ferramenta **preenche** os campos da página aberta numa janela dela. **Quem
clica** em Entrar, Continuar e Enviar é sempre a pessoa. Isso exige uma emenda MAJOR da constituição, para a versão
4.0.0, nos itens do VI. O V continua: o envio é da pessoa.

## Clarifications

### Session 2026-10-23

- Q: A ferramenta vai até a confirmação ou para antes? → A: Para antes. Ela preenche, e a pessoa confere e clica em
  Continuar/Enviar.
- Q: Qual IA o recurso pode exigir? → A: Qualquer provedor já aceito, inclusive o gratuito. A ferramenta lê o
  formulário e a IA só escreve as respostas.
- Q: Quais portais? → A: Qualquer portal, só dentro do domínio dele. Vem uma lista de domínios conhecidos, e um
  domínio fora dela só entra se a pessoa liberar.
- Q: Como fica o login? → A: Login e senha da pessoa no `.env`. A ferramenta digita na tela de login do portal, e
  quem clica em "Entrar" é a pessoa. Isso muda a decisão da spec 018 (2026-10-18), que tinha recusado guardar a senha.
- Q: O LinkedIn entra? → A: Não. Continua bloqueado, como na spec 018.
- Pesquisa (2026-10-23, research.md §1): os termos do Indeed e do Nerdin proíbem automação na candidatura. Os dois
  ficam bloqueados como o LinkedIn, sem opção de liberar (princípio VI: seguir os termos de cada fonte). Os termos
  de candidato da Gupy não foram encontrados; a Gupy fica na lista com essa pendência anotada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preencher as perguntas da candidatura (Priority: P1)

A pessoa decidiu seguir com uma vaga da Gupy e clica em "Candidatar com ajuda". A ferramenta abre a página da vaga
na janela dela. A pessoa clica em "Candidatar-se" no portal e avança até as perguntas. Volta ao dashboard e clica em
"Preencher esta página".

A ferramenta lê as perguntas da página e mostra uma lista. Cada pergunta vem com a resposta proposta, escrita com
fatos do perfil:
- nas de múltipla escolha, a opção escolhida;
- nas sensíveis (salário, visto, deficiência…), "responda você na página";
- nas que a ferramenta não tem como responder, "sem base no perfil".

A pessoa ajusta o que quiser e clica em "Preencher no formulário". Os campos aparecem preenchidos na janela. Ela
confere e clica em "Continuar" no portal.

**Why this priority**: é o ganho principal, porque tira o trabalho repetitivo de responder formulários. Dá para usar
mesmo sem o login automático e sem outros portais.

**Independent Test**: com uma página de formulário de teste num domínio liberado, conferir:
- a lista proposta (texto, escolha, sensível, sem base);
- que só os campos confirmados foram preenchidos;
- que nenhum botão ou link foi acionado.

**Acceptance Scenarios**:

1. **Given** uma vaga em "seguir" e o recurso ligado, **When** a pessoa clica em "Candidatar com ajuda", **Then** a
   página da vaga abre na janela da ferramenta, com o aviso "Avance no portal até as perguntas e clique em Preencher
   esta página".
2. **Given** a janela numa página de perguntas de um domínio liberado, **When** a pessoa clica em "Preencher esta
   página", **Then**:
   - aparece a lista de perguntas com a resposta proposta para cada uma;
   - nada é escrito na página ainda.
3. **Given** a lista proposta, **When** a pessoa edita uma resposta e clica em "Preencher no formulário", **Then**:
   - cada campo recebe o texto confirmado, ou a opção confirmada;
   - campos sensíveis, de senha e de arquivo ficam intactos;
   - nenhum botão é clicado.
4. **Given** uma pergunta de múltipla escolha, **When** a IA propõe uma resposta que não está entre as opções,
   **Then** o campo fica sem proposta, marcado "sem base no perfil".
5. **Given** uma pergunta com limite de caracteres, **When** a proposta é gerada, **Then** ela respeita o limite.
6. **Given** um campo que já tem valor, **When** a pessoa preenche a página, **Then** o valor existente fica, a menos
   que ela tenha marcado "trocar".
7. **Given** a candidatura enviada pela pessoa, **When** ela usa "Atualizar candidaturas" (Gupy ou Indeed), **Then**
   a vaga é proposta como "aplicada", como já acontece hoje.

---

### User Story 2 - Domínios liberados (Priority: P1)

A vaga de uma empresa leva para um sistema de candidatura fora da lista, como `empresa.workday.com`. A pessoa clica
em "Preencher esta página". A ferramenta avisa: "Este endereço (empresa.workday.com) não está liberado. Liberar o
preenchimento nele?". Se a pessoa liberar, a resposta fica guardada e a lista de perguntas aparece. Se não liberar,
nada é preenchido.

**Why this priority**: é a trava que impede a ferramenta de escrever em qualquer página. Sem ela, o recurso não pode
ir para a ferramenta pública.

**Independent Test**:
- Conferir que uma página fora da lista não é preenchida.
- Conferir que um endereço parecido com um conhecido (`gupy.io.exemplo.com`) não é tratado como conhecido.
- Conferir que um domínio liberado passa a valer nas próximas vezes e que "Revogar" o tira.

**Acceptance Scenarios**:

1. **Given** uma página num domínio da lista conhecida, **When** a pessoa pede o preenchimento, **Then** ele segue
   sem pergunta extra.
2. **Given** uma página num domínio fora da lista, **When** a pessoa pede o preenchimento, **Then** a ferramenta
   pergunta se libera aquele domínio e não preenche nada antes da resposta.
3. **Given** um domínio bloqueado (LinkedIn, ou portal cujos termos proíbem automação, como Indeed e Nerdin),
   **When** a pessoa pede o preenchimento, **Then** a ferramenta recusa, explica o motivo e não oferece liberação.
4. **Given** a lista de domínios liberados na configuração, **When** a pessoa revoga um deles, **Then** o próximo
   preenchimento naquele domínio pergunta de novo.

---

### User Story 3 - Login com a credencial guardada (Priority: P2)

A janela abre na tela de login da Gupy. A pessoa clica em "Preencher login" no dashboard. A ferramenta digita o
e-mail e a senha que ela guardou na configuração. A pessoa clica em "Entrar" no portal. Se aparecer captcha ou
código de verificação, a ferramenta para, e quem resolve é a pessoa.

**Why this priority**: poupa a digitação do login, mas não é essencial, porque a pessoa pode fazer o login à mão,
como já faz na spec 018. Também é a parte de mais risco, por envolver a senha.

**Independent Test**:
- Com uma tela de login de teste no domínio de login cadastrado, conferir que usuário e senha são digitados e que o
  botão "Entrar" não é acionado.
- Num domínio diferente, mesmo que parecido, conferir que nada é digitado.
- Conferir que a senha não aparece em nenhuma resposta, registro ou mensagem de erro.

**Acceptance Scenarios**:

1. **Given** credenciais da Gupy guardadas, **When** a pessoa abre a configuração, **Then** vê o usuário e só os
   últimos 4 caracteres da senha, com "Trocar" e "Apagar".
2. **Given** a janela na tela de login da Gupy (domínio de login cadastrado), **When** a pessoa clica em "Preencher
   login", **Then** os dois campos são preenchidos e nada é clicado.
3. **Given** a janela num domínio que não é o de login daquele portal, **When** a pessoa clica em "Preencher login",
   **Then** nada é digitado e a ferramenta diz por quê.
4. **Given** um captcha, 2FA ou aviso de atividade suspeita, **When** a ferramenta lê a página, **Then** ela para e
   pede que a pessoa resolva na janela, sem tentar de novo.
5. **Given** nenhuma credencial guardada para o portal, **When** a pessoa abre a tela de login, **Then** o botão
   "Preencher login" não aparece e ela faz o login à mão.

---

### User Story 4 - Ligar o recurso (Priority: P2)

O recurso vem desligado. Na configuração, a pessoa liga "Candidatura assistida". Na primeira vez, aparece um aviso:
- **o portal pode restringir a conta** se perceber automação;
- **a senha fica em texto no `.env`** deste computador, fora do Git, mas legível por programas da máquina;
- **o envio é sempre dela.**

Ela confirma, e o botão "Candidatar com ajuda" passa a aparecer nas vagas em "seguir".

**Why this priority**: garante que ninguém da ferramenta pública recebe o recurso sem escolher.

**Independent Test**:
- Com o recurso desligado, o botão não aparece e as rotas recusam.
- Ao ligar, o aviso aparece uma única vez.

**Acceptance Scenarios**:

1. **Given** o recurso desligado, **When** a pessoa abre uma vaga em "seguir", **Then** não há "Candidatar com
   ajuda".
2. **Given** o recurso desligado, **When** algo chama a leitura ou o preenchimento, **Then** a ferramenta recusa.
3. **Given** a pessoa liga o recurso pela primeira vez, **When** confirma o aviso, **Then** o recurso fica ligado e o
   aviso não volta.

### Edge Cases

- **Página que a ferramenta não reconhece como formulário:** "não reconheci perguntas nesta página", sem preencher
  nada.
- **Etapa de teste** (comportamental, lógica, vídeo, técnico) **ou anexo de arquivo:** "esta etapa é com você", sem
  preencher nada.
- **Página mudou entre "Preencher esta página" e "Preencher no formulário"** (a pessoa avançou de etapa): a
  ferramenta confere de novo a página. Se as perguntas não batem, pede para ler outra vez em vez de preencher no
  lugar errado.
- **Formulário em inglês:** as respostas propostas saem no idioma da pergunta.
- **Pergunta que a IA tenta responder sendo sensível:** a resposta é descartada, como já acontece em "Preparar
  respostas".
- **IA indisponível ou sem chave:** os campos de múltipla escolha e texto ficam sem proposta. A pessoa pode digitar
  as respostas na lista e preencher do mesmo jeito.
- **Janela fechada ou navegador ausente (Edge/Chrome):** mesma mensagem da spec 018.
- **Credencial com caracteres especiais** (aspas, `=`, `#`): é guardada e digitada sem alteração.
- **A pessoa clica em "Preencher" duas vezes:** o segundo pedido espera o primeiro terminar e não preenche em dobro.

## Requirements *(mandatory)*

### Functional Requirements

**Limites (valem para todo o recurso)**

- **FR-001**: A ferramenta MUST escrever somente em campos de formulário: texto, área de texto, seleção, opção única
  e caixas de resposta. Ela MUST NOT:
  - clicar em botão ou link;
  - acionar envio de formulário;
  - simular a tecla Enter;
  - fazer pedido de escrita ao servidor do portal.
- **FR-002**: Toda escrita MUST partir de um clique da pessoa no dashboard, sobre uma proposta que ela viu. Nada
  roda sozinho ou em segundo plano.
- **FR-003**: Antes de escrever, a ferramenta MUST conferir que o endereço da página atual pertence a um domínio
  conhecido ou liberado pela pessoa. A comparação é pelo nome exato do domínio ou de um subdomínio dele, nunca por
  "contém". MUST ser sempre recusados: os domínios do LinkedIn e os de portais cujos termos proíbem automação
  (Indeed e Nerdin, research.md §1).
- **FR-004**: A ferramenta MUST NOT preencher campos de pergunta sensível (autorização de trabalho, visto,
  cidadania, salário ou pretensão, deficiência, relocação, diversidade), campos de arquivo nem campos de senha fora
  do login.
- **FR-005**: Diante de captcha, verificação em duas etapas, código por e-mail ou pedido de nova verificação, a
  ferramenta MUST parar e pedir que a pessoa resolva na janela, sem tentar contornar.
- **FR-006**: O recurso MUST vir desligado e só funcionar depois que a pessoa ligar na configuração e confirmar o
  aviso de risco.

**Perguntas e respostas**

- **FR-007**: A ferramenta MUST ler da página atual cada pergunta com:
  - o rótulo;
  - o tipo de campo;
  - as opções, quando houver;
  - o limite de caracteres;
  - se é obrigatória;
  - o valor que já tem.

  Ela MUST também identificar se a página é de login, de perguntas, de teste ou desconhecida.
- **FR-008**: As respostas propostas MUST usar só fatos do perfil e do currículo da pessoa e a descrição da vaga.
  Elas passam pela mesma conferência de fatos dos textos de candidatura.
- **FR-009**: Em múltipla escolha, a proposta MUST ser uma das opções existentes. Se não for, a pergunta fica sem
  proposta.
- **FR-010**: A proposta MUST respeitar o limite de caracteres da pergunta.
- **FR-011**: Perguntas sensíveis MUST NOT ser enviadas à IA.
- **FR-012**: Credenciais MUST NOT ser enviadas à IA, em nenhuma hipótese.
- **FR-013**: A pessoa MUST poder editar, apagar ou marcar "trocar" em cada resposta antes de preencher.
- **FR-014**: Um campo que já tem valor MUST ser mantido, salvo se a pessoa marcou "trocar".
- **FR-015**: Antes de escrever, a ferramenta MUST conferir que as perguntas da página ainda são as que foram lidas.
  Se não forem, MUST pedir nova leitura.
- **FR-016**: As respostas confirmadas MUST ser guardadas junto às respostas do kit daquela vaga, para consulta e
  reaproveitamento.
- **FR-017**: Depois do preenchimento, a ferramenta MUST mostrar:
  - o que foi preenchido;
  - o que ficou para a pessoa (sensíveis, sem base, arquivo, teste);
  - o lembrete "Confira na janela e clique você em Continuar/Enviar".

**Domínios**

- **FR-018**: A ferramenta MUST trazer uma lista de domínios conhecidos de candidatura, com o domínio de login de
  cada portal que tem login central. A lista inicial, da pesquisa desta spec, é Gupy, Greenhouse, Lever e Workday.
- **FR-019**: Para um domínio fora da lista, a ferramenta MUST perguntar se a pessoa libera. Ela MUST guardar a
  resposta na configuração pessoal, que fica fora do Git.
- **FR-020**: A pessoa MUST poder ver e revogar os domínios que liberou.

**Login**

- **FR-021**: A pessoa MUST poder guardar, trocar e apagar usuário e senha por portal na configuração. Eles ficam no
  arquivo `.env` local, fora do Git.
- **FR-022**: A página MUST mostrar só o usuário e os últimos 4 caracteres da senha. A senha MUST NOT aparecer em
  respostas do dashboard, registros, mensagens de erro, banco de vagas nem arquivos do kit.
- **FR-023**: A ferramenta MUST digitar a credencial de um portal somente se:
  - a página estiver no domínio de login cadastrado para aquele portal (nome exato);
  - a página tiver um único campo de senha.
- **FR-024**: Depois de digitar a credencial, a ferramenta MUST parar. O clique em "Entrar" é da pessoa.

**Fluxo**

- **FR-025**: Numa vaga em "seguir", com o recurso ligado, MUST existir a ação "Candidatar com ajuda": um botão no
  card do quadro enquanto a vaga está em Salva (pedido do usuário em 2026-10-24) e o painel na aba Candidatura do
  detalhe. Ela abre o
  endereço da vaga na janela da ferramenta, a mesma da spec 018, com perfil próprio e nunca o navegador do dia a dia.
- **FR-026**: Depois que a pessoa envia, o andamento segue o fluxo atual:
  - Gupy e Indeed: o "Atualizar candidaturas" propõe a etapa "aplicada";
  - outros portais: a pessoa marca à mão.

  A ferramenta MUST NOT marcar "aplicada" sozinha só porque preencheu.

### Key Entities

- **Domínio de candidatura:** endereço onde o preenchimento é permitido. Tem o nome do portal, a origem (conhecido
  ou liberado pela pessoa), a data de liberação e o domínio de login do portal, se houver.
- **Credencial de portal:** usuário e senha de um portal, guardados no `.env` local. São identificados pelo portal e
  nunca saem do computador, a não ser digitados na tela de login dele.
- **Pergunta lida:** rótulo, tipo, opções, limite, obrigatória, valor atual e marcação (comum, sensível, arquivo,
  senha).
- **Proposta de resposta:** texto ou opção sugerida, com a base no perfil, ou "sem base", ou "responda você". A
  pessoa pode editar.
- **Preenchimento:** o registro de uma página preenchida para uma vaga, com o que foi escrito e o que ficou para a
  pessoa. Nunca guarda a senha.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa página de 5 a 10 perguntas, a pessoa vai de "Preencher esta página" a ter os campos preenchidos
  e conferidos em menos de 2 minutos, contando a revisão da proposta.
- **SC-002**: Em nenhum teste, automático ou ponta a ponta, a ferramenta aciona um botão, um link ou um envio no
  portal. Todo avanço de etapa e todo envio são da pessoa.
- **SC-003**: Em nenhum teste uma pergunta sensível é preenchida pela ferramenta ou enviada à IA.
- **SC-004**: A senha não aparece em nenhuma resposta do dashboard, registro, mensagem de erro ou arquivo gerado.
  Isso é verificado procurando a senha de teste em toda a saída.
- **SC-005**: Em 100% dos testes com domínio fora da lista, ou parecido com um conhecido, nada é preenchido antes
  da liberação explícita.
- **SC-006**: Em múltipla escolha, 100% das propostas preenchidas são opções existentes na página.
- **SC-007**: O recurso funciona com o provedor de IA gratuito padrão da ferramenta, sem exigir um provedor pago.
- **SC-008**: Na prova ponta a ponta com o usuário, uma candidatura real na Gupy e uma num sistema externo chegam à
  confirmação com o envio feito por ele e as perguntas não sensíveis preenchidas pela ferramenta.

## Assumptions

- A janela do navegador da ferramenta (spec 018) continua sendo o único lugar onde a ferramenta mexe em portais.
  Nada de navegador invisível nem de biblioteca de automação nova.
- O formulário dos portais é lido da página como ela aparece para a pessoa, de forma genérica. Pode haver ajuste
  por portal quando a pesquisa mostrar necessidade.
- **Portão de pesquisa:** antes do plano técnico, a pesquisa lê os termos de uso dos portais da lista inicial. Um
  portal cujos termos proíbam automação de preenchimento fica bloqueado (research.md §1).
- **Constituição:** depende de emenda MAJOR para a 4.0.0, aprovada pelo usuário antes da implementação. O princípio
  VI passa a admitir:
  - preenchimento de campos no clique, em domínio liberado, nunca botões;
  - credencial guardada pela pessoa no `.env`, digitada só no domínio de login do portal.

  Os princípios IV (sensíveis com a pessoa) e V (envio sempre da pessoa) ficam como estão.
- O botão e os painéis são feitos no código-fonte da página (branch `frontend-react`), como nas specs 022 e 025. O
  contrato da API fica em `dash/API.md`.
- Windows primeiro, com Edge ou Chrome, como na spec 018.
- **Risco aceito pelo usuário:** a senha fica em texto puro no `.env`. O Gerenciador de Credenciais do Windows vai
  para a lista de desejos como melhoria futura.
