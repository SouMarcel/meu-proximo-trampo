# Feature Specification: Relatos — a candidatura assistida aprende com a pessoa

**Feature Branch**: `035-relatos` (worktree `../mpt-035-relatos`, saída da `master`)

**Created**: 2026-10-28

**Status**: Aprovada em 2026-10-28 (decisões do usuário nas quatro perguntas; autorizou seguir até o commit)

**Input**: Pedido do usuário depois de testar a candidatura assistida num formulário da Gupy. O nome e o estado foram
preenchidos, mas o "nome completo da mãe" e a "remuneração atual" ficaram no painel, à espera de uma resposta final
que iria para a página como estivesse escrita. Pedido:
- as perguntas devem ser preenchidas pela ferramenta com o que ela sabe da pessoa e do histórico dela;
- quando ela não souber, a pessoa escreve um **relato**, que vale como verdade;
- a IA adapta o relato para responder da melhor forma;
- o relato passa a fazer parte do conhecimento da ferramenta sobre a pessoa e melhora o currículo, as histórias STAR e
  as dúvidas que ficaram da anamnese.

**Decisões do usuário (28/10)**:
1. A remuneração atual, a autorização e a deficiência ficam guardadas e são preenchidas sozinhas, sem IA. A pretensão
   salarial e a relocação continuam perguntadas a cada vaga. Isso pede uma emenda na constituição IV.
2. Os relatos ficam numa base à parte. Valem como fato em tudo que usa o perfil, aparecem em Meu perfil para ver,
   corrigir e apagar, e vão para o `perfil.md` só com o OK da pessoa.
3. A resposta adaptada vai direto para a página, e a pessoa confere na janela.

## Contexto

Hoje o painel do "Preencher esta página" pede a resposta final. O que a pessoa escreve vai literal para a página, e a
memória só a reaproveita quando a pergunta tem exatamente o mesmo texto. O relato não volta para o perfil, para o
currículo nem para as histórias STAR. Há ainda dois problemas:
- O nome da mãe, num campo de texto longo, foi tratado como pergunta comum e mandado à IA. A regra de "dado
  cadastral" só olhava campos curtos.
- O contador "0 de 1000 caracteres" aparece grudado no motivo da pergunta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - O relato vira a melhor resposta (Priority: P1)

Numa pergunta comum que o perfil não responde ("Conte um projeto com Power BI"), a pessoa escreve com as próprias
palavras o que aconteceu. A ferramenta pede à IA uma resposta para aquela pergunta, no idioma dela e dentro do limite
de caracteres, usando o relato e o perfil sem acrescentar fatos. Em seguida preenche a página e mostra no painel o que
escreveu.

**Independent Test**: página falsa com uma pergunta comum de até 300 caracteres e uma IA falsa. Um relato de 600
caracteres vira uma resposta de até 300, preenchida com a fonte "seu relato".

**Acceptance Scenarios**:

1. **Given** uma pergunta comum sem resposta no perfil, **When** a pessoa escreve um relato e clica em Preencher,
   **Then** a página recebe a resposta adaptada, e o painel mostra o texto preenchido com a fonte "seu relato
   (adaptado pela IA)".
2. **Given** a IA fora do ar, **When** a pessoa preenche, **Then** a página recebe o próprio relato, cortado no limite,
   com um aviso.
3. **Given** um relato maior que o limite do campo, **When** a pessoa escreve, **Then** o painel aceita o texto e avisa
   que a ferramenta ajusta ao limite.

---

### User Story 2 - O relato vira conhecimento (Priority: P1)

Cada relato fica guardado no computador da pessoa e entra como fato confirmado em tudo que usa o perfil: as próximas
respostas de formulário, o currículo, a carta, as histórias STAR, a nota das vagas e as análises do perfil. Em **Meu
perfil → Seus relatos**, a pessoa vê, corrige e apaga os relatos, e pode **levar um relato ao perfil.md**. Nesse caso
a versão anterior do perfil é guardada.

**Independent Test**: um relato gravado aparece no pedido de currículo e no de respostas. Apagado, some dos dois.
"Levar ao perfil" acrescenta o relato ao `perfil.md` e guarda a versão anterior.

**Acceptance Scenarios**:

1. **Given** um relato gravado, **When** a ferramenta monta o pedido de currículo, carta, respostas, entrevista, nota
   ou análise do perfil, **Then** o relato aparece numa seção "Relatos da pessoa".
2. **Given** um relato, **When** a pessoa o apaga em Meu perfil, **Then** ele deixa de entrar em qualquer pedido.
3. **Given** um relato, **When** a pessoa clica em "Levar ao perfil", **Then** ele entra no `perfil.md` numa seção
   "Relatos", a versão anterior do perfil fica guardada e o relato deixa de entrar duas vezes nos pedidos.
4. **Given** a opção "Guardar meus relatos" desmarcada, **When** a pessoa preenche, **Then** a resposta vai para a
   página, mas o relato não é guardado.

---

### User Story 3 - Fato estável é preenchido sozinho (Priority: P2)

A remuneração atual, a autorização de trabalho e a deficiência são fatos: depois da primeira resposta, a ferramenta
preenche sozinha, sem IA. A remuneração atual é reconhecida mesmo com outra redação ("Qual sua remuneração atual?",
"Salário atual"). A pretensão salarial e a relocação continuam perguntadas a cada vaga. O nome da mãe e do pai, CPF, RG,
passaporte e data de nascimento são dados cadastrais: vão literais, nunca à IA, e ficam na memória para a próxima vez,
também com outra redação no caso do nome da mãe e do pai.

**Independent Test**: depois de responder "Poderia compartilhar sua remuneração atual?", a pergunta "Qual o seu
salário atual?" é preenchida sozinha. "Qual sua pretensão salarial?" continua perguntada. "Qual é o nome completo da
sua mãe?" num campo de texto longo é cadastral.

**Acceptance Scenarios**:

1. **Given** a remuneração atual respondida uma vez, **When** outro formulário pergunta o salário atual com outra
   redação, **Then** a ferramenta preenche sozinha com a fonte "sua resposta anterior".
2. **Given** a pergunta de pretensão salarial, **When** a ferramenta lê a página, **Then** a pergunta vai para a pessoa
   e a resposta não fica guardada.
3. **Given** "Qual é o nome completo da sua mãe?" num campo de texto longo, **When** a ferramenta lê a página, **Then**
   ele é dado cadastral: não vai à IA e não vira relato.
4. **Given** uma pergunta sensível ou cadastral, **When** a pessoa responde, **Then** a resposta vai literal, sem IA.

### User Story 4 - A carta vende a pessoa sem exigir respostas (Priority: P1)

Pedido do usuário no teste (28/10): a carta exigia as três perguntas antes de escrever. Agora ela é gerada direto, pelo
perfil, pelos relatos e pela vaga, e responde às perguntas da melhor forma possível. O que a pessoa escrever vale como
relato. O texto vende quem se candidata já no primeiro parágrafo, com foco no problema da empresa que ela ajuda a
resolver e nas habilidades e no histórico vindos da anamnese, de forma objetiva e em formato que o ATS lê.

**Independent Test**: gerar a carta sem nenhuma resposta funciona, e o pedido traz a estrutura (primeiro parágrafo
que vende, solução, fechamento) e manda a IA responder às perguntas em branco. As respostas escritas viram relatos.

**Acceptance Scenarios**:

1. **Given** nenhuma resposta, **When** a pessoa clica em Escrever, **Then** a carta é gerada pelo perfil, pelos
   relatos e pela vaga.
2. **Given** a resposta "que problema você resolveria", **When** a carta é gerada, **Then** a resposta entra no pedido
   como fato e fica guardada como relato.
3. **Given** "Guardar o que eu escrever como relato" desmarcado, **When** a carta é gerada, **Then** nada vai para os
   relatos.

### User Story 5 - Palavras-chave da vaga e Verificar a carta editada (Priority: P1)

Pedidos do usuário no teste (28/10):
1. O formato ATS deve focar nas palavras-chave da vaga que se ligam ao perfil profissional.
2. Quando a pessoa editar a carta, um botão **Verificar** faz a IA incorporar as melhorias dela ao texto gerado,
   corrigindo gramática e ortografia.

**Independent Test**:
- O pedido da carta lista os requisitos da vaga que o perfil sustenta, com a evidência, e separa os que não achou.
  "Fluent English" com "Inglês" no perfil conta; "Eastern Time" não casa com "time" (equipe).
- Verificar uma carta editada grava uma versão nova, com as mudanças da IA. A anterior continua, e o que a pessoa
  acrescentou não bloqueia a conferência e vira relato.

**Acceptance Scenarios**:

1. **Given** uma vaga com requisitos, **When** a carta é pedida, **Then** a IA recebe as palavras-chave que o perfil
   sustenta, cada uma com o trecho do perfil, e a regra de usar o termo exato do anúncio.
2. **Given** uma carta pronta, **When** a pessoa a lê, **Then** vê quantas dessas palavras-chave a carta usou e quais
   faltam.
3. **Given** uma carta editada pela pessoa, **When** ela clica em Verificar, **Then** sai uma versão nova revisada, com a
   lista do que a IA ajustou, e a anterior continua na lista.

### User Story 6 - Exportar a carta em PDF (Priority: P2)

Pedido do usuário (28/10): exportar a carta também em PDF. A carta completa sai em .pdf, .docx e .txt; o PDF vem do
.docx pelo LibreOffice ou pelo Word, como o do currículo, com texto selecionável (o ATS lê). Carta antiga ou com
conversão que falhou ganha o botão **Gerar PDF**. A mensagem curta continua só para copiar e colar.

### Edge Cases

- **Relato vazio**: a pergunta continua no painel.
- **Pergunta com opções** (lista, múltipla escolha, sim/não): a pessoa escolhe a opção, sem relato.
- **Relato com CPF, RG ou outros documentos**: os números são mascarados antes de guardar e antes da IA.
- **Mesmo relato para a mesma pergunta**: atualiza o relato que já existe, sem duplicar.
- **Página mudou** antes de preencher: o preenchimento para, como hoje, sem gravar o relato.
- **Muitos relatos**: até 300 guardados; os mais antigos que já foram para o perfil saem primeiro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Na pergunta comum de texto, a resposta da pessoa MUST ser tratada como relato. A ferramenta pede à IA
  uma resposta para aquela pergunta, no idioma dela e dentro do limite, usando só o relato e os fatos do perfil.
  Sem IA ou com falha dela, MUST preencher o próprio relato, cortado no limite, com aviso.
- **FR-002**: O relato MUST ser guardado em `dash/dados/relatos.json` (fora do Git) com a pergunta, o relato, a resposta
  preenchida, a vaga e a data, quando a opção "Guardar meus relatos" estiver marcada (o padrão).
- **FR-003**: Os relatos que ainda não estão no perfil MUST entrar, numa seção "Relatos da pessoa", no texto do perfil
  usado pela IA em todos os pedidos: respostas de formulário, adaptação de relato, currículo, carta, entrevista e
  histórias STAR, nota das vagas e análises do perfil. A conferência sem IA (`conferir.py`) também os conta como fato.
- **FR-004**: Meu perfil MUST ter "Seus relatos", com a lista, a edição do texto, Apagar e "Levar ao perfil". Esta
  última acrescenta o relato ao `perfil.md` (seção "Relatos") com a versão anterior guardada e marca o relato como
  levado.
- **FR-005**: Pergunta sensível e dado cadastral MUST ir literais à página, nunca à IA e nunca como relato.
- **FR-006**: "Salário ou pretensão" MUST virar duas categorias:
  - **remuneração atual**: guardada e reaproveitada também com outra redação;
  - **pretensão salarial**: perguntada a cada vaga e nunca guardada.

  A relocação continua perguntada a cada vaga.
- **FR-007**: Nome da mãe e do pai, CPF, RG, passaporte e data de nascimento MUST ser dado cadastral em qualquer campo
  de texto. Nome da mãe e do pai MUST ser reaproveitados também com outra redação.
- **FR-008**: O painel MUST mostrar, para cada pergunta, se é relato ("conte com suas palavras; a ferramenta ajusta ao
  limite") ou resposta literal. O contador de caracteres MUST ficar numa linha própria. Depois do preenchimento, MUST
  listar o que foi escrito em cada campo, com a fonte.
- **FR-009**: Constituição IV emendada (5.1.2 → 5.2.0) com a remuneração atual guardável e o relato como fato
  confirmado.
- **FR-010**: Documentação: `dash/API.md`, README, AGENTS.md, skills `analisar-perfil`, `gerar-curriculo` e
  `preparar-entrevista` (o assistente lê os relatos com `PY relatos.py lista`).
- **FR-011** (US4): As perguntas da carta e da mensagem curta MUST ser opcionais. A que ficar em branco, a IA responde
  pelo perfil, pelos relatos e pela vaga, sem afirmar fatos ou sentimentos que eles não sustentam. O que a pessoa
  escrever MUST valer como relato e ser guardado (opção "Guardar o que eu escrever como relato", padrão sim).
- **FR-012** (US4): O pedido da carta MUST pedir:
  - primeiro parágrafo de até 60 palavras que vende a pessoa: quem ela é, o problema ou objetivo da vaga que ela ajuda
    a resolver e a prova mais forte do perfil;
  - parágrafos de solução, com cada necessidade do anúncio ligada a um fato do perfil ou dos relatos;
  - motivação, primeiro movimento e um fechamento objetivo;
  - dois requisitos do anúncio ligados a fatos, com os termos do anúncio quando forem verdade;
  - formato que o ATS lê.

  A mensagem curta MUST vender já na primeira frase.
- **FR-013** (US5): O pedido da carta MUST trazer os requisitos da vaga que o perfil e os relatos sustentam (termos e
  evidência) e os que a ferramenta não achou. Estes últimos só podem ser citados com um fato que os sustente. A
  equivalência entre idiomas (english/inglês, dashboards/painéis, reports/relatórios) MUST contar, e palavras que não são
  habilidade ("time", "hours", "fluent") MUST ser ignoradas. A conferência da carta MUST trazer `palavras_chave` e
  apontar quando a carta usa menos da metade delas.
- **FR-014** (US5): Uma carta pronta MUST poder ser editada e verificada. A IA incorpora as mudanças, corrige gramática
  e ortografia e mantém estrutura, palavras-chave e tamanho, sem acrescentar fatos. Grava uma versão nova
  (`origem: "verificada"`, `base`, `mudancas`), e a anterior fica. O texto da pessoa conta como fato dela na
  conferência, e o que ela acrescentou vira relato (opção, padrão sim).
- **FR-015** (US6): A carta completa MUST sair também em PDF (`curriculo.para_pdf`), com `aviso_pdf` quando não sair, e
  `POST /api/kit/carta/{nome}/pdf` MUST gerar o PDF depois.

### Key Entities

- **Relato**: `{id, pergunta, relato, resposta, vaga: {id, titulo, empresa}?, em, no_perfil}`.
- **Memória** (já existe): ganha `fato` (`remuneração atual`, `nome da mãe`, `nome do pai`) para reaproveitar com
  outra redação.

## Success Criteria *(mandatory)*

- **SC-001**: No formulário de teste, um relato de 600 caracteres vira uma resposta de até 300, preenchida, com um só
  pedido à IA.
- **SC-002**: Um relato gravado aparece nos pedidos de currículo, de respostas e de nota; apagado, não aparece.
- **SC-003**: Depois de uma resposta, "salário atual" com outra redação é preenchido sem pergunta e sem IA; a pretensão
  continua perguntada.
- **SC-004**: Nenhuma pergunta sensível ou cadastral aparece em pedido à IA.
- **SC-005**: No formulário da Gupy do teste do usuário, só a pretensão (se houver) e o que a ferramenta nunca viu ficam no
  painel; na segunda vaga, o nome da mãe e a remuneração atual são preenchidos sozinhos.

## Assumptions

- **Uma chamada à IA por clique** em Preencher, com todos os relatos da página juntos.
- **A resposta adaptada também vai para a memória** quando "Lembrar" está marcado (como hoje com a resposta literal).
- **Perfil do LinkedIn**: a ferramenta usa o `perfil.md`, feito a partir do currículo e do LinkedIn. Os materiais
  originais não são relidos a cada pergunta.
- **Verificação**: só no Windows; teste do usuário na branch pessoal.
