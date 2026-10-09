# Feature Specification: Primeiros passos e anamnese

**Feature Branch**: `004-primeiros-passos` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Fase 3 do roteiro: primeiros passos e anamnese na página. Sem perfil
(ou por um botão), a página guia: escolher a IA ou seguir sem; enviar currículos (PDF ou Word) e o
LinkedIn (PDF do perfil e/ou exportação de dados em ZIP); extrair o texto e, com IA, propor um
rascunho do perfil com a fonte de cada item e os conflitos lado a lado (sem IA, formulário com o
texto ao lado); anamnese, uma pergunta por vez; diagnóstico do que falta; revisão e só então gravar
o perfil e propor os filtros da busca. Nada é gravado sem confirmação; perfil existente nunca é
sobrescrito sem mostrar o que muda. A mesma anamnese pelo chat, numa skill. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Montar o perfil a partir do que a pessoa já tem (Priority: P1)

Na primeira vez que abre a ferramenta, sem perfil, a pessoa é convidada para os primeiros passos.
Ela escolhe a IA (ou segue sem), arrasta o currículo e o PDF do LinkedIn (ou o arquivo de
exportação de dados do LinkedIn) e, em poucos instantes, vê um rascunho do perfil no formato do
modelo: objetivo, resumo, experiências, formação, certificações, ferramentas e idiomas. Cada item
mostra de qual arquivo veio, e onde dois arquivos discordam (datas, cargos) os dois valores
aparecem lado a lado para ela escolher.

**Why this priority**: o perfil é a base de tudo (nota das vagas, currículo); hoje ele só nasce pelo
chat de um assistente, o que exclui quem usa só a página.

**Independent Test**: num ambiente sem perfil, com IA configurada, enviar um currículo e um PDF do
LinkedIn fictícios e ver o rascunho com as fontes e os conflitos; nada fica gravado até a revisão.

**Acceptance Scenarios**:

1. **Given** nenhum perfil, **When** a pessoa abre a página, **Then** os primeiros passos aparecem
   (e podem ser fechados e retomados depois pelo botão).
2. **Given** um currículo e um PDF do LinkedIn enviados, com IA, **When** a extração termina,
   **Then** o rascunho do perfil aparece com a fonte de cada item e os conflitos lado a lado.
3. **Given** a exportação de dados do LinkedIn (ZIP), **When** enviada, **Then** cargos, formação,
   competências e certificações são lidos dela sem precisar de IA.
4. **Given** o endereço do perfil do LinkedIn, **When** informado, **Then** ele entra só como link
   de contato, sem a ferramenta abrir a página.

---

### User Story 2 - Anamnese: as perguntas que os arquivos não respondem (Priority: P1)

Depois do rascunho, a ferramenta faz uma pergunta por vez sobre o que os arquivos não dizem:
cargos que busca, senioridade, modelo de trabalho, cidade, pretensão e o que não aceita; a maior
conquista de cada um dos últimos cargos e como foi medida; ferramentas e nível; idiomas e nível de
inglês; e interesse em vagas do exterior (remoto, aceita morar fora, passaporte, visto ou
autorização de trabalho, precisa de patrocínio, fuso, forma de contratação). Números só entram se
a pessoa confirmar; ela pode pular qualquer pergunta.

**Why this priority**: sem objetivo, preferências e conquistas medidas, a nota das vagas e o
currículo ficam genéricos.

**Independent Test**: responder a anamnese inteira (pulando algumas perguntas) e ver as respostas
refletidas no rascunho, com as puladas marcadas como pendentes.

**Acceptance Scenarios**:

1. **Given** o rascunho, **When** a anamnese começa, **Then** aparece uma pergunta por vez, com
   opções quando fizer sentido, e a opção de pular.
2. **Given** uma conquista sem número, **When** a pessoa não confirma uma métrica, **Then** a
   conquista entra sem número (descrição qualitativa), nunca com número sugerido.
3. **Given** a pessoa diz que tem interesse em vagas do exterior, **When** a anamnese segue,
   **Then** aparecem as perguntas sobre morar fora, passaporte, visto ou autorização, patrocínio,
   fuso e contratação.

---

### User Story 3 - Diagnóstico, revisão e gravação (Priority: P1)

Antes de gravar, a ferramenta mostra o diagnóstico do que ainda falta ou está fraco (datas sem mês,
resultados sem medida, ferramentas sem nível, lacunas entre empregos, conflitos não resolvidos),
com perguntas para completar. A pessoa revisa e edita o perfil inteiro e confirma; só então o
perfil é gravado.

**Why this priority**: a constituição exige confirmação antes de gravar e só fatos confirmados.

**Independent Test**: chegar à revisão, editar um item, confirmar e ver o perfil gravado igual ao
revisado; cancelar e ver que nada foi gravado.

**Acceptance Scenarios**:

1. **Given** a revisão, **When** a pessoa confirma, **Then** o perfil é gravado exatamente como
   revisado.
2. **Given** a revisão, **When** a pessoa cancela ou fecha a página, **Then** nenhum perfil é
   gravado e o progresso pode ser retomado depois.
3. **Given** conflitos não resolvidos, **When** a pessoa tenta confirmar, **Then** a ferramenta
   pede a escolha antes de gravar.

---

### User Story 4 - Filtros da busca propostos a partir do perfil (Priority: P2)

Com o perfil confirmado, a ferramenta propõe os filtros da busca a partir das respostas: cargos em
português e em inglês, local, modelos de trabalho e busca internacional. A pessoa edita e confirma;
só então os filtros são gravados.

**Why this priority**: fecha o caminho até a primeira busca; mas o perfil sozinho já tem valor.

**Independent Test**: confirmar o perfil e ver a proposta de filtros coerente com as respostas;
editar e gravar; conferir o painel de filtros com os valores gravados.

**Acceptance Scenarios**:

1. **Given** o perfil confirmado, **When** a proposta de filtros aparece, **Then** ela traz cargos
   em português e inglês, local, modelos e a busca internacional ligada só se a pessoa demonstrou
   interesse.
2. **Given** filtros já existentes, **When** a proposta aparece, **Then** ela mostra o que muda em
   relação aos atuais antes de gravar.

---

### User Story 5 - Sem IA (Priority: P2)

Quem segue sem IA também faz os primeiros passos: os arquivos são lidos (texto extraído e, no ZIP
do LinkedIn, os campos já organizados) e o formulário do perfil vem em branco, com o texto ao lado
para copiar; a anamnese e a revisão funcionam igual. Nada é enviado a provedores.

**Why this priority**: a IA é opcional pela constituição.

**Independent Test**: com "Sem IA", fazer os primeiros passos e gravar um perfil; conferir que
nenhum provedor foi chamado.

**Acceptance Scenarios**:

1. **Given** "Sem IA", **When** a pessoa envia os arquivos, **Then** o texto extraído aparece ao
   lado do formulário e os campos do ZIP do LinkedIn já vêm preenchidos para revisão.

---

### User Story 6 - Atualizar um perfil que já existe (Priority: P3)

Quem já tem perfil usa o botão para atualizá-lo (novo emprego, novo currículo). A ferramenta parte
do perfil atual, junta o que vier de arquivos novos e das respostas, e mostra o que muda (o que
entra, sai e é alterado) antes de gravar; a versão anterior fica guardada.

**Why this priority**: a carreira muda; mas o primeiro uso vem antes.

**Independent Test**: com um perfil existente, enviar um currículo novo, ver a comparação, confirmar
e encontrar a versão anterior guardada.

**Acceptance Scenarios**:

1. **Given** um perfil existente, **When** a pessoa confirma a atualização, **Then** a versão
   anterior fica guardada e a comparação foi mostrada antes.

---

### User Story 7 - A mesma anamnese pelo chat (Priority: P3)

Quem prefere conversar pede ao assistente ("monta meu perfil", "atualiza meu perfil"); uma skill de
análise de perfil conduz os mesmos passos (materiais, rascunho com fontes, anamnese, diagnóstico,
revisão, filtros), com as mesmas regras, gravando só com confirmação.

**Why this priority**: a página atende a maioria; o chat é a alternativa para quem já usa um
assistente.

**Independent Test**: no assistente, pedir para montar o perfil a partir de um currículo fictício e
ver os mesmos passos e a confirmação antes de gravar.

**Acceptance Scenarios**:

1. **Given** um assistente aberto na pasta, **When** a pessoa pede para montar o perfil, **Then** a
   skill segue os mesmos passos e só grava depois da confirmação.

---

### Edge Cases

- PDF digitalizado (só imagem, sem texto): aviso de que não dá para ler e sugestão de enviar outro
  formato ou colar o texto.
- PDF protegido por senha ou arquivo corrompido: mensagem clara; os outros arquivos seguem.
- Word antigo (.doc) ou formato não aceito: aviso para salvar como .docx ou PDF.
- Exportação do LinkedIn incompleta (sem algumas planilhas): usa o que veio e diz o que faltou.
- Arquivo grande demais: recusa com o limite.
- Currículos com versões diferentes (datas, cargos): conflitos lado a lado, com a fonte de cada um.
- IA falha no meio (chave, limite, sem internet): os textos extraídos ficam; a pessoa pode tentar de
  novo ou seguir sem IA.
- Página fechada no meio: o progresso fica guardado localmente e é retomado.
- Documento com texto que parece instrução para a IA: tratado como dado.
- Documentos de identificação no currículo (CPF, RG, data de nascimento): não vão para a IA nem para
  o perfil; e-mail e telefone são reconhecidos sem IA e só entram se a pessoa confirmar.
- Página aberta por outro aparelho da rede local: pode ver, mas não enviar arquivos nem gravar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sem perfil, a página MUST oferecer os primeiros passos automaticamente na primeira
  abertura; MUST existir um botão para abrir os primeiros passos a qualquer momento (criar ou
  atualizar).
- **FR-002**: O primeiro passo MUST permitir escolher a IA (o painel de IA existente) ou seguir sem
  IA.
- **FR-003**: A pessoa MUST poder enviar currículos em PDF ou Word (.docx), o PDF do perfil do
  LinkedIn, a exportação de dados do LinkedIn (ZIP) e texto colado; os arquivos MUST ficar na pasta
  local de anexos (fora do controle de versão).
- **FR-004**: O endereço do perfil do LinkedIn MUST entrar só como link de contato; a ferramenta
  MUST NOT abrir ou ler a página do LinkedIn.
- **FR-005**: A ferramenta MUST extrair o texto dos arquivos e, da exportação do LinkedIn, os campos
  organizados (cargos, formação, competências, certificações, idiomas, resumo) sem IA.
- **FR-006**: Com IA, a ferramenta MUST propor um rascunho do perfil no formato do modelo de perfil,
  com a fonte (arquivo) de cada item e os conflitos entre fontes lado a lado; MUST NOT incluir nada
  que não esteja nos arquivos ou nas respostas.
- **FR-007**: Documentos de identificação (CPF, RG, data de nascimento) MUST ser retirados do texto
  antes de ir para a IA e MUST NOT entrar no perfil; e-mail e telefone MUST ser reconhecidos sem IA
  e só entrar no perfil com confirmação.
- **FR-008**: A anamnese MUST fazer uma pergunta por vez, com opções quando couber e com a opção de
  pular, cobrindo: cargos-alvo, senioridade, modelo de trabalho, cidade, pretensão e o que não
  aceita; maior conquista dos últimos cargos e a métrica; ferramentas e nível; idiomas e nível de
  inglês; e, se houver interesse, vagas do exterior (remoto, morar fora e países, passaporte, visto
  ou autorização de trabalho e países, patrocínio, fuso, forma de contratação).
- **FR-009**: Números (métricas, anos, valores) MUST entrar no perfil só se a pessoa os confirmar;
  sem confirmação, a conquista entra em forma qualitativa.
- **FR-010**: Antes da revisão, a ferramenta MUST mostrar o diagnóstico do que falta ou está fraco,
  com perguntas para completar.
- **FR-011**: O perfil MUST ser gravado só depois da revisão e da confirmação explícita; conflitos
  não resolvidos MUST ser resolvidos antes.
- **FR-012**: Com perfil existente, a ferramenta MUST mostrar a comparação (entra, sai, muda) antes
  de gravar e MUST guardar a versão anterior.
- **FR-013**: Depois do perfil, a ferramenta MUST propor os filtros da busca (cargos em português e
  inglês, local, modelos, busca internacional) a partir das respostas, mostrar o que muda em relação
  aos atuais e gravar só com confirmação.
- **FR-014**: Sem IA, todos os passos MUST funcionar, com o formulário do perfil em branco e o texto
  extraído ao lado (e os campos do ZIP do LinkedIn já preenchidos); nada é enviado a provedores.
- **FR-015**: O progresso (arquivos enviados, rascunho, respostas) MUST ficar guardado localmente
  até a gravação, para ser retomado se a página fechar.
- **FR-016**: Enviar arquivos, gerar rascunho e gravar MUST ser aceito só de páginas abertas no
  próprio computador, como as mudanças de IA.
- **FR-017**: Uma skill de análise de perfil MUST oferecer os mesmos passos pelo chat, com as mesmas
  regras e gravando só com confirmação, no formato portátil das outras skills.
- **FR-018**: Textos MUST estar em português do Brasil.

### Key Entities

- **Material**: arquivo ou texto enviado pela pessoa (currículo, PDF do LinkedIn, exportação do
  LinkedIn, texto colado), com o texto extraído e, no caso da exportação, os campos organizados.
- **Rascunho do perfil**: o perfil no formato do modelo, com a fonte de cada item, os conflitos
  pendentes e as respostas da anamnese; vive só localmente até a confirmação.
- **Perfil**: o perfil gravado (o arquivo de perfil local), com a versão anterior guardada quando
  atualizado.
- **Proposta de filtros**: os filtros da busca sugeridos a partir do perfil, comparados com os
  atuais.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com um currículo e o LinkedIn em mãos, a pessoa termina os primeiros passos (perfil e
  filtros gravados) em até 15 minutos.
- **SC-002**: Com IA, o rascunho aparece em até 2 minutos depois do envio dos arquivos.
- **SC-003**: 100% dos itens do rascunho mostram de qual arquivo ou resposta vieram.
- **SC-004**: 0 gravações de perfil ou filtros sem confirmação explícita; 100% das atualizações de
  perfil existente mostram a comparação e guardam a versão anterior.
- **SC-005**: Nenhum documento de identificação (CPF, RG, data de nascimento) aparece no pedido
  enviado à IA nem no perfil gravado.
- **SC-006**: Sem IA, a pessoa completa os primeiros passos e grava um perfil sem nenhuma chamada a
  provedores.
- **SC-007**: A exportação do LinkedIn é lida (campos organizados) em até 10 segundos, sem IA.

## Assumptions

- A pessoa obtém a exportação de dados do LinkedIn pelo próprio LinkedIn (o pedido leva algum tempo
  para ficar pronto); o PDF do perfil é o "Salvar como PDF" do LinkedIn. A ferramenta aponta onde
  conseguir, mas não acessa o LinkedIn.
- PDFs digitalizados (sem texto) ficam fora do escopo: reconhecimento de texto em imagem não entra
  nesta fase.
- O formato do perfil é o do modelo atual de perfil, acrescido de seções opcionais para contato,
  trabalho no exterior e regras de verbo e atribuição; o modelo é atualizado junto.
- As preferências do exterior (morar fora, passaporte, visto, patrocínio) ficam registradas no
  perfil nesta fase; elas passam a filtrar vagas na fase da área internacional.
- A análise contínua do perfil (lacunas das vagas, cargos-alvo, prontidão internacional) é a Fase 10
  do roteiro; aqui entra só o diagnóstico inicial.
- Uma pessoa por computador.
- Foco em Windows (decisão do usuário).
