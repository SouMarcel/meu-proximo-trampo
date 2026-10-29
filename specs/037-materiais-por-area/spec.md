# Feature Specification: Materiais do Meu perfil em três áreas

**Feature Branch**: `037-materiais-por-area` (worktree `../mpt-037-materiais-por-area`, saída da `master`; o front na
`frontend-react`)

**Created**: 2026-10-29

**Status**: Aprovada em 2026-10-29 (o botão de leitura se chama OCR, a pedido do usuário)

**Input**: Pedido do usuário em 29/10/2026. Em Meu perfil → Materiais, dividir em temas:
- um campo específico para o perfil do LinkedIn;
- outro para anexar currículos;
- um último para os demais arquivos, documentos e certificações.

Motivo: um certificado de curso enviado como material apareceu como currículo, com o botão "Usar este currículo e ir
para as vagas".

**Decisões do usuário (29/10)**:
1. Cada arquivo já enviado ganha **Mover para** (LinkedIn, Currículo, Documento). O arquivo não é reenviado nem muda
   de pasta.
2. Quando um arquivo parece de outra área, a ferramenta **avisa** numa linha amarela, sem mudar sozinha.
3. Os documentos e as certificações **vão para a IA** no rascunho do perfil, como fonte de Formação e Certificações,
   marcados como certificado ou documento. Nunca viram currículo.
4. Pedido seguinte, no mesmo dia: os PDFs de certificado que são só imagem (sem texto) devem ser lidos. A leitura usa
   o **OCR que o Windows já traz**, entra **nesta spec** (User Story 5) e não instala nada.
5. Os PDFs já enviados sem texto ganham o botão **OCR**. Os novos são lidos sozinhos, no envio.

## Contexto

Hoje a página tem uma área única, "Escolher ou arrastar arquivos". A ferramenta adivinha o tipo pelo conteúdo:
- PDF com "linkedin.com/in/" e títulos como "Experience" vira PDF do LinkedIn;
- ZIP vira exportação do LinkedIn;
- qualquer outro PDF ou Word vira **currículo**.

Daí vêm três problemas:
- **Botão errado**: todo PDF ou Word ganha "Usar este currículo e ir para as vagas", inclusive certificados.
- **Listas misturadas**: "Currículos que já estão na pasta anexos" e o seletor **Seu currículo** (aba Currículo base)
  listam todo PDF e Word da pasta `anexos/`, inclusive os certificados enviados como material.
- **IA sem contexto**: no rascunho, a IA recebe os materiais só com o nome do arquivo, sem saber que um deles é um
  certificado.

Há ainda um quarto problema: o PDF que é só imagem (certificado gerado como figura, documento escaneado) fica sem
texto, com o aviso "PDF digitalizado (só imagem, sem texto)". A ferramenta só lê o texto que já vem escrito no PDF.
No teste com 7 certificados assim:
- o OCR do Windows (português do Brasil) leu os 7, em menos de 2 segundos no total, sem rede;
- sobrou ruído de logotipos e trocas de letra (ex.: "8 noras");
- uma página de 2.400 pixels de largura falhou, e a mesma página com 1.600 pixels saiu quase perfeita.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cada coisa na sua área (Priority: P1)

No passo Materiais, a pessoa vê três áreas, cada uma com o seu envio de arquivo e a sua lista.

1. **Perfil do LinkedIn**
   - **Aceita**: o PDF do perfil e o ZIP da exportação de dados.
   - **Também tem**: o campo do link do perfil e o "Como baixar do LinkedIn".
2. **Currículos**
   - **Aceita**: PDF e Word (.docx).
   - **Também tem**: os currículos que já estão na pasta anexos e o "Cole o texto do currículo".
   - Só aqui aparece "Usar este currículo e ir para as vagas".
3. **Outros documentos e certificações**
   - **Aceita**: PDF e Word, como certificados, diplomas e cartas de recomendação.
   - Esses arquivos nunca ganham o botão de currículo.

O arquivo vale como a área em que foi enviado: um certificado enviado em Documentos é documento, mesmo sendo um PDF.

**Why this priority**: é o pedido e corrige o erro do print.

**Independent Test**: enviar um certificado em PDF na área Outros documentos e certificações. Ele aparece só nessa
área, sem "Usar este currículo e ir para as vagas".

**Acceptance Scenarios**:

1. **Given** o passo Materiais, **When** a pessoa abre, **Then** vê as três áreas, nesta ordem: Perfil do LinkedIn,
   Currículos, Outros documentos e certificações.
2. **Given** um PDF enviado em Outros documentos e certificações, **When** ele aparece na lista, **Then** fica nessa
   área, com o rótulo "Documento (PDF)" e sem o botão de currículo.
3. **Given** um PDF ou Word enviado em Currículos, **When** ele aparece, **Then** tem "Usar este currículo e ir para as
   vagas".
4. **Given** a área Perfil do LinkedIn, **When** a pessoa tenta enviar um Word, **Then** a ferramenta explica que ali
   vão o PDF do perfil ou o ZIP da exportação.
5. **Given** as áreas Currículos e Outros documentos, **When** a pessoa tenta enviar um ZIP, **Then** a ferramenta
   explica que o ZIP do LinkedIn vai na área do LinkedIn.

---

### User Story 2 - Mover um arquivo de área (Priority: P1)

Cada arquivo da lista tem **Mover para**, com as outras áreas que aceitam aquele formato:
- um PDF pode ir para qualquer área;
- um Word, só para Currículo ou Documento;
- um ZIP fica no LinkedIn.

O arquivo não é reenviado e não muda de pasta: só a área muda, e com ela os botões e as listas onde ele aparece. O
texto colado é sempre currículo e não tem Mover para.

**Why this priority**: o certificado do print já está nos materiais como currículo. Sem mover, a pessoa teria de
remover e enviar de novo.

**Independent Test**: um PDF que está como currículo é movido para Documento. Ele sai da área Currículos, perde o
botão de currículo e some da lista "Currículos que já estão na pasta anexos" e do seletor Seu currículo.

**Acceptance Scenarios**:

1. **Given** um certificado listado como currículo, **When** a pessoa escolhe Mover para → Documento, **Then** ele passa
   para Outros documentos e certificações, sem o botão de currículo.
2. **Given** um documento movido para Currículo, **When** a pessoa olha a área Currículos, **Then** ele está lá, com o
   botão.
3. **Given** um Word, **When** a pessoa abre Mover para, **Then** a opção LinkedIn não aparece.

---

### User Story 3 - Aviso de área trocada (Priority: P2)

Quando o conteúdo do arquivo não combina com a área, aparece uma linha amarela. Os casos são:
- **Certificado em Currículos**: o texto é curto e tem marcas de certificado ("certificado", "certificamos", "carga
  horária", "concluiu o curso", "certificate of completion"). O aviso diz: "Parece um certificado. Mover para Outros
  documentos e certificações?"
- **PDF do LinkedIn em Currículos ou Documentos**: o aviso diz: "Parece o PDF do seu perfil do LinkedIn. Mover para
  Perfil do LinkedIn?"
- **Arquivo que não parece LinkedIn na área do LinkedIn**: o aviso diz: "Não parece o PDF do perfil do LinkedIn.
  Mover para Currículos ou Outros documentos?"

O aviso traz o botão da área sugerida. A ferramenta nunca muda a área sozinha.

**Why this priority**: evita o erro mesmo quando a pessoa usa a área errada. É secundário porque a área escolhida já
resolve o caso principal.

**Independent Test**: enviar um certificado curto na área Currículos. Aparece o aviso com o botão "Mover para Outros
documentos e certificações", e o arquivo continua em Currículos até o clique.

**Acceptance Scenarios**:

1. **Given** um certificado enviado em Currículos, **When** ele aparece, **Then** mostra o aviso e o botão para
   Documentos.
2. **Given** um currículo de verdade, longo e com experiências, que cita "certificado" em Certificações, **When** ele
   aparece em Currículos, **Then** não há aviso.
3. **Given** o aviso, **When** a pessoa clica no botão sugerido, **Then** o arquivo muda de área e o aviso some.

---

### User Story 4 - Documentos no perfil, nunca como currículo (Priority: P2)

Os documentos e certificações:
- entram no rascunho do perfil feito pela IA, marcados como "certificado ou documento", para ela usar em Formação e
  Certificações e não como experiência;
- saem da lista "Currículos que já estão na pasta anexos" e do seletor **Seu currículo** (aba Currículo base).

Os PDFs do LinkedIn também saem dessas duas listas, porque não são currículo.

**Why this priority**: completa a correção (o certificado também aparecia nessas listas) e dá uso aos documentos.

**Independent Test**:
- Com um certificado em Documentos, o pedido à IA traz o arquivo com a marca "certificado ou documento".
- O seletor Seu currículo não mostra o certificado.

**Acceptance Scenarios**:

1. **Given** um certificado em Documentos, **When** a IA monta o rascunho, **Then** recebe o texto dele marcado como
   certificado ou documento, com a regra de usá-lo só para formação e certificações.
2. **Given** um certificado em Documentos, **When** a pessoa abre o seletor Seu currículo, **Then** ele não aparece.
3. **Given** o rascunho sem IA, **When** é montado, **Then** os documentos não mudam nada, como hoje.

### User Story 5 - Ler o texto de PDF que é só imagem (Priority: P1)

Quando o PDF não tem texto, a ferramenta lê a imagem das páginas com o OCR do Windows, no próprio computador:
- **Na hora do envio**, em qualquer área.
- **Nos materiais já enviados sem texto**, pelo botão **OCR**.
- **Texto lido**: entra como o texto do material, com CPF, RG e data de nascimento mascarados. Ganha o aviso "Texto
  lido da imagem (OCR): confira nomes, datas e números" e vai para a IA com a mesma marca.
- **Leitura curta**: a ferramenta tenta outro tamanho de imagem e fica com a leitura mais completa.
- **Leitura vazia ou fora do Windows**: continua o aviso de hoje ("PDF digitalizado"), com a sugestão de colar o texto.

**Why this priority**: sem isso, cerca de um em cada sete arquivos enviados no teste (7 de 51) fica fora do perfil.

**Independent Test**: no Windows, enviar um certificado em PDF só de imagem. O material aparece com o texto do curso
(nome, instituição, carga horária) e o aviso de OCR.

**Acceptance Scenarios**:

1. **Given** um PDF só de imagem, **When** a pessoa envia no Windows, **Then** o material mostra o texto lido e o
   aviso de OCR, sem o aviso de PDF digitalizado.
2. **Given** um material antigo sem texto, **When** a pessoa clica em OCR, **Then** o texto aparece
   em "Texto lido", e o aviso de área trocada passa a valer para ele.
3. **Given** um PDF com texto, **When** é enviado, **Then** o OCR não roda.
4. **Given** um PDF só de imagem com um CPF, **When** é lido, **Then** o CPF aparece mascarado.
5. **Given** um computador sem o OCR do Windows (outro sistema, ou sem o idioma), **When** o PDF só de imagem é
   enviado, **Then** fica o aviso de hoje, sem erro.
6. **Given** um currículo escaneado em PDF, **When** a pessoa usa "Usar este currículo e ir para as vagas", **Then**
   a leitura usa o mesmo OCR.

### Edge Cases

- **OCR que demora ou trava**: cada leitura tem tempo limite (cerca de 30 segundos por arquivo). Ao estourar, fica o
  aviso de PDF digitalizado.
- **PDF longo só de imagem**: são lidas até 5 páginas, com aviso quando há mais.
- **Política de scripts do Windows restrita**: a leitura não depende dela; se o Windows bloquear, fica o aviso de
  hoje.
- **Material antigo**: os materiais enviados antes desta spec mantêm a área que a ferramenta adivinhou (LinkedIn ou
  currículo). O Mover para e o aviso valem para eles também.
- **Envio sem área** (skill de chat, página antiga): continua a adivinhação de hoje.
- **Documento que também é currículo** (ex.: um portfólio com experiências): a pessoa escolhe a área; o aviso só
  aparece nos casos claros da User Story 3.
- **Arquivo marcado como Seu currículo e movido para Documento**: a marcação sai junto, e a pessoa é avisada de que o
  seletor Seu currículo ficou vazio naquele idioma.
- **PDF escaneado** (sem texto) em qualquer área: a ferramenta tenta o OCR (User Story 5). Se não houver texto
  nenhum, o aviso de área trocada não aparece, porque não há o que conferir.
- **Arrastar arquivos** para uma área: valem a área e as regras de formato daquela área.
- **Outro aparelho**: as três áreas aparecem só para ver, como hoje.

## Requirements *(mandatory)*

### Functional Requirements

**Áreas**

- **FR-001**: O passo Materiais MUST ter três áreas, nesta ordem: Perfil do LinkedIn, Currículos, Outros documentos e
  certificações. Cada área tem o seu envio (escolher ou arrastar) e a lista dos seus arquivos.
- **FR-002**: Formatos por área:
  - Perfil do LinkedIn MUST aceitar PDF e ZIP;
  - Currículos e Outros documentos MUST aceitar PDF e Word (.docx).

  Formato fora disso MUST ser recusado, com a mensagem que diz a área certa.
- **FR-003**: O arquivo MUST valer como a área em que foi enviado. O rótulo mostra a área e o formato, ex.: "Documento
  (PDF)", "Currículo (Word)", "LinkedIn (exportação de dados)".
- **FR-004**: O que fica em cada área:
  - "Usar este currículo e ir para as vagas" MUST aparecer só em Currículos;
  - "Currículos que já estão na pasta anexos" e o "Cole o texto do currículo" ficam em Currículos;
  - o link do LinkedIn e o "Como baixar do LinkedIn" ficam no LinkedIn.
- **FR-005**: Sem a área informada no envio, a ferramenta MUST classificar como hoje, para a skill de chat e a página
  antiga.

**Mover para**

- **FR-006**: Cada arquivo MUST ter Mover para, com as áreas que aceitam o seu formato. A mudança MUST valer sem
  reenviar o arquivo e sem mudar a pasta dele.
- **FR-007**: Ao mover para Documento ou LinkedIn um arquivo marcado como Seu currículo, a marcação MUST sair, com um
  aviso para a pessoa.

**Aviso**

- **FR-008**: A ferramenta MUST mostrar o aviso de área trocada nos três casos da User Story 3, com o botão da área
  sugerida, e MUST NOT mudar a área sem o clique.
- **FR-009**: O aviso de documento aparece em três casos, para não acusar um currículo longo que cita "certificado":
  - texto curto com marca de certificado, ou com nome de arquivo de certificado, diploma, declaração ou histórico;
  - texto bem curto com só a carga horária;
  - marca forte de documento acadêmico (histórico escolar, colação de grau), em qualquer tamanho.

  O aviso de LinkedIn MUST usar a mesma regra que já reconhece o PDF do LinkedIn. A regra foi ajustada na
  implementação com os arquivos reais do teste: os 44 materiais com texto passaram a ter aviso, e nenhum currículo de
  teste recebeu aviso.

**Uso dos documentos**

- **FR-010**: No pedido do rascunho à IA, cada material MUST levar a sua área: currículo, LinkedIn ou certificado ou
  documento. Também MUST ir a regra de usar documentos só para formação e certificações, nunca como experiência.
- **FR-011**: Documentos e PDFs do LinkedIn MUST sair da lista "Currículos que já estão na pasta anexos" e do seletor
  Seu currículo. Os candidatos a currículo ficam sendo os arquivos da pasta anexos que não estão nos materiais como
  documento ou LinkedIn.
- **FR-012**: As regras de hoje continuam:
  - CPF, RG e data de nascimento são mascarados em qualquer área;
  - limite de 10 MB por arquivo;
  - nada é gravado no perfil sem a Revisão.

**Leitura de PDF só de imagem**

- **FR-014**: Quando o PDF não tem texto, a ferramenta MUST tentar o OCR do Windows. O OCR roda no computador, sem
  rede e sem programa novo. Fora do Windows, ou sem o OCR disponível, MUST ficar o aviso de hoje.
- **FR-015**: Como ler:
  - tentar o primeiro tamanho de página;
  - se a leitura vier curta, tentar outro e ficar com a mais completa;
  - ler até 5 páginas;
  - respeitar o tempo limite por arquivo.
- **FR-016**: O texto lido por OCR MUST passar pela máscara de documentos e levar o aviso "Texto lido da imagem (OCR):
  confira nomes, datas e números". No pedido à IA, MUST ir marcado como lido por OCR, com a regra de não usar número
  ou data duvidosa.
- **FR-017**: Material sem texto MUST ter o botão OCR. O botão relê o arquivo com o OCR e atualiza
  o texto e os avisos, sem mudar a área.
- **FR-018**: A mesma leitura MUST valer onde a ferramenta já lê PDF: materiais, "Usar este currículo e ir para as
  vagas" e currículos da pasta anexos.

**Textos**

- **FR-013**: README, `dash/API.md` e a skill `analisar-perfil` MUST descrever as três áreas. No chat, a skill MUST
  perguntar o que é cada arquivo quando não estiver claro.

### Key Entities

- **Material**: um arquivo ou texto enviado no passo Materiais.
  - **Área**: `linkedin`, `curriculo` ou `documento`.
  - **Formato**: PDF, Word, ZIP ou texto colado.
  - **Também tem**: o texto lido (mascarado), os avisos e o aviso de área sugerida (quando há).
  - O tipo de hoje (`curriculo_pdf`, `linkedin_zip`…) ganha `documento_pdf` e `documento_docx`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nenhum arquivo da área Outros documentos e certificações mostra "Usar este currículo e ir para as vagas"
  nem aparece no seletor Seu currículo (0 em 100% dos casos de teste).
- **SC-002**: O certificado do print passa de currículo para documento em 2 cliques (Mover para → Documento), sem
  reenviar.
- **SC-003**: Num conjunto de teste com certificados curtos e currículos longos que citam "certificado", 100% dos
  certificados recebem o aviso e nenhum currículo recebe.
- **SC-004**: O pedido do rascunho à IA identifica a área de 100% dos materiais.
- **SC-005**: Os testes automáticos do projeto continuam passando, e o tipo do front confere sem erro.
- **SC-006**: No Windows, os 7 certificados só de imagem do teste passam a ter o nome do curso legível no texto lido.
  Cada leitura leva até 5 segundos por arquivo.

## Assumptions

- O formato Word aceito continua sendo só .docx. O .doc antigo continua recusado, com a mensagem de hoje.
- Imagens soltas (JPG, PNG) não entram nesta spec. O OCR vale para PDF só de imagem.
- O OCR do macOS e do Linux fica para a lista de desejos (Windows primeiro). O do Windows depende do idioma português
  instalado, que vem com o Windows em português.
- Os arquivos continuam na mesma pasta de hoje (`anexos/primeiros-passos/`), qualquer que seja a área. A área fica no
  progresso do perfil, fora do Git como hoje.
- O texto colado continua sendo tratado como currículo.
- A página antiga (antes do PR do front) continua enviando sem área e vendo os materiais como hoje. Ela mostra o
  rótulo do tipo novo `documento_*` pelo próprio nome do tipo.
