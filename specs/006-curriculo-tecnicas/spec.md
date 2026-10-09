# Feature Specification: Currículo com técnicas

**Feature Branch**: `006-curriculo-tecnicas` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 5 do roteiro: currículo com técnicas escolhidas pela pessoa
(motor, conferências e skill de chat; a geração pela página é a Fase 6). Hoje o currículo sai num
formato só e só avisa acima de 2 páginas. A pessoa escolhe, por caixas de marcar, as técnicas de
cada currículo: ATS; foco numa carreira ou cargo-alvo; estilo Google XYZ (só com número
confirmado); resultado primeiro; competências primeiro. E escolhas: páginas (1 ou 2); formato do
país (Brasil, Estados Unidos, Europa); estilo visual (padrão, compacto, executivo). Antes de
entregar, uma conferência sem IA aponta problemas de ATS, requisitos da vaga cobertos, sustentados
ou em lacuna (lacuna nunca vira competência) e fatos que não estão no perfil, com veredito ok,
conferir ou bloquear. A skill de chat pergunta as técnicas com caixas de marcar e roda a
conferência antes de entregar. Nada é inventado; a pessoa decide. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher as técnicas do currículo (Priority: P1)

Ao pedir um currículo (base ou para uma vaga), a pessoa vê as técnicas disponíveis como caixas de
marcar, cada uma com uma frase do que faz: **ATS** (leitura fácil por sistemas de triagem),
**foco** num cargo ou carreira, **XYZ** (conquista + medida + como), **resultado primeiro** e
**competências primeiro**. E faz três escolhas: **páginas** (1 ou 2), **formato do país** (Brasil,
Estados Unidos ou Europa) e **estilo visual** (padrão, compacto ou executivo). Uma sugestão
aparece marcada conforme o alvo (ex.: vaga dos Estados Unidos sugere o formato americano em
inglês), mas ela pode trocar tudo. O currículo sai com o que ela marcou e o arquivo registra as
escolhas feitas.

**Why this priority**: cada vaga e cada país pedem um currículo diferente; sem escolha, a pessoa
recebe sempre o mesmo formato.

**Independent Test**: pelo chat, pedir um currículo, marcar foco + XYZ, 1 página, formato
americano e estilo compacto, e receber um arquivo que segue essas escolhas.

**Acceptance Scenarios**:

1. **Given** um pedido de currículo, **When** a skill pergunta as técnicas, **Then** as caixas e as
   três escolhas aparecem com a explicação de cada uma e uma sugestão marcada.
2. **Given** as técnicas escolhidas, **When** o currículo é gerado, **Then** o arquivo segue o
   tamanho de papel, o idioma dos títulos, o limite de páginas e o estilo escolhidos.
3. **Given** o formato dos Estados Unidos, **When** o currículo é gerado, **Then** ele sai em papel
   Letter, em inglês, sem foto, sem data de nascimento, estado civil ou documentos.
4. **Given** nenhuma técnica marcada, **When** o currículo é gerado, **Then** ele sai no formato de
   hoje (Brasil, padrão), que já é legível por ATS.

---

### User Story 2 - Conferência antes de entregar (Priority: P1)

Antes de entregar o currículo, a ferramenta confere, sem IA, três coisas e mostra o resultado com
um veredito: **ok**, **conferir** ou **bloquear**.

- **ATS**: seções com títulos padrão, contato no corpo do documento (não no cabeçalho), sem
  tabelas, colunas ou imagens, fonte comum e, com vaga, quantas palavras-chave da vaga aparecem.
- **Requisitos da vaga × perfil**: cada requisito como **tem** (está no perfil), **sustentado**
  (o perfil traz algo equivalente) ou **lacuna**; lacuna nunca aparece como competência no
  currículo.
- **Fatos**: números, empresas, cargos e datas do currículo que não estão no perfil são apontados;
  um número que não está no perfil bloqueia a entrega até a pessoa confirmar ou tirar.

**Why this priority**: o currículo é o documento mais sensível da ferramenta; um número inventado
ou uma competência que a pessoa não tem pode custar a vaga.

**Independent Test**: conferir um currículo fictício com um número que não está no perfil, uma
empresa a mais e um requisito em lacuna listado como competência, e ver o veredito "bloquear" com
cada ponto explicado.

**Acceptance Scenarios**:

1. **Given** um currículo com um número que não está no perfil, **When** a conferência roda,
   **Then** o veredito é "bloquear" e o número aparece com o trecho onde está.
2. **Given** um requisito da vaga que é lacuna, **When** ele aparece em Competências, **Then** a
   conferência aponta e pede para tirar.
3. **Given** um currículo sem problemas, **When** a conferência roda, **Then** o veredito é "ok" e
   a cobertura das palavras-chave da vaga aparece.
4. **Given** uma vaga, **When** a conferência roda, **Then** cada requisito aparece como tem,
   sustentado ou lacuna, com a parte do perfil que o sustenta.

---

### User Story 3 - Técnicas de escrita aplicadas pela skill (Priority: P2)

A skill de chat escreve o currículo seguindo as técnicas marcadas: com **foco**, escolhe e ordena
as experiências e itens que mais servem ao alvo e abre uma seção de destaques; com **XYZ**,
escreve as conquistas como "realizou X, medido por Y, fazendo Z" só quando a pessoa confirmou o
número (sem número, a conquista fica qualitativa); com **resultado primeiro**, cada item começa
pelo resultado; com **competências primeiro**, as competências vêm antes da experiência; com
**ATS**, as palavras-chave da vaga entram reformuladas a partir do que a pessoa tem, nunca
inventadas.

**Why this priority**: as técnicas de layout sozinhas não mudam o conteúdo; a escrita é onde elas
fazem diferença.

**Independent Test**: pedir o mesmo currículo com e sem XYZ e foco e ver a diferença na ordem e na
redação, sem nenhum número novo.

**Acceptance Scenarios**:

1. **Given** foco num cargo, **When** o currículo é escrito, **Then** as experiências mais ligadas
   ao cargo vêm primeiro e há uma seção de destaques com até 3 itens.
2. **Given** XYZ marcado e uma conquista sem número confirmado, **When** o currículo é escrito,
   **Then** a conquista fica sem número e a skill pergunta se há uma medida.
3. **Given** competências primeiro, **When** o currículo é gerado, **Then** a seção de competências
   vem antes da experiência.

---

### User Story 4 - Página e quantidade de páginas sob controle (Priority: P2)

Com 1 ou 2 páginas escolhidas, a ferramenta mede o resultado e, se passar do limite, avisa quanto
passou e sugere o que cortar (itens mais antigos, menos ligados ao alvo) em vez de encolher a
fonte além do legível.

**Why this priority**: recrutadores e sistemas de triagem cortam currículos longos; a pessoa precisa
saber antes de enviar.

**Independent Test**: gerar com 1 página um conteúdo que dá 2 e ver o aviso com as sugestões.

**Acceptance Scenarios**:

1. **Given** 1 página escolhida e um conteúdo maior, **When** o currículo é gerado, **Then** a
   ferramenta avisa quantas páginas deu e sugere cortes, sem gravar a versão como pronta.
2. **Given** o estilo compacto, **When** o mesmo conteúdo é gerado, **Then** ele ocupa menos
   espaço que o padrão, com fonte não menor que 10 pt.

---

### Edge Cases

- Formato americano com perfil em português: a skill escreve em inglês só o que está no perfil
  (tradução fiel) e avisa que a pessoa deve revisar o inglês.
- Vaga sem uma seção clara de requisitos: a conferência tenta pelos parágrafos e, se não achar,
  diz que não conseguiu separar os requisitos (sem inventar).
- Número escrito de outra forma (ex.: "30%" no perfil e "trinta por cento" no currículo, ou "1,5
  mil" e "1.500"): conta como o mesmo fato.
- Data só com ano no perfil e mês e ano no currículo: aponta como "conferir".
- Foto pedida pela pessoa no formato Brasil: fica fora do escopo (a ferramenta não põe foto em
  nenhum formato) e a skill diz isso.
- PDF indisponível (sem Word nem LibreOffice): o .docx sai e a contagem de páginas fica como
  "não medida", com o aviso.
- Currículo antigo (gerado antes desta fase): continua gerando igual, sem técnicas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta MUST oferecer as técnicas ATS, foco, XYZ, resultado primeiro e
  competências primeiro como caixas de marcar independentes, cada uma com uma frase do que faz.
- **FR-002**: A ferramenta MUST oferecer as escolhas páginas (1 ou 2), formato do país (Brasil,
  Estados Unidos, Europa) e estilo visual (padrão, compacto, executivo), com uma sugestão conforme
  o alvo (país e idioma da vaga) que a pessoa pode trocar.
- **FR-003**: O formato Brasil MUST sair em A4 e português; Estados Unidos em Letter e inglês, sem
  foto, data de nascimento, estado civil, nacionalidade ou documentos; Europa em A4 e inglês.
- **FR-004**: O estilo visual MUST mudar margens, espaçamento e tamanho de fonte dentro de limites
  legíveis (nunca abaixo de 10 pt no corpo), mantendo uma coluna, sem tabelas nem imagens.
- **FR-005**: Com o limite de páginas, a ferramenta MUST medir o resultado e, acima do limite, avisar
  quantas páginas deu e sugerir cortes.
- **FR-006**: O currículo gerado MUST registrar as técnicas e escolhas usadas.
- **FR-007**: A conferência MUST rodar sem IA e mostrar o veredito ok, conferir ou bloquear com os
  pontos de ATS, de requisitos e de fatos, cada um com o trecho e o motivo.
- **FR-008**: A conferência de ATS MUST verificar títulos de seção padrão, contato no corpo, ausência
  de tabelas, colunas e imagens, fonte comum e, com vaga, a cobertura das palavras-chave.
- **FR-009**: A conferência de requisitos MUST separar os requisitos da vaga e classificar cada um
  como tem, sustentado ou lacuna em relação ao perfil; uma lacuna listada como competência MUST
  ser apontada.
- **FR-010**: A conferência de fatos MUST apontar números (percentuais, valores, quantidades,
  "N vezes"), empresas, cargos e datas que não estão no perfil; número fora do perfil MUST resultar
  em "bloquear".
- **FR-011**: A skill de chat MUST perguntar as técnicas e escolhas com caixas de marcar (ou opções
  numeradas no assistente sem essa ferramenta) e MUST rodar a conferência antes de entregar.
- **FR-012**: A skill MUST aplicar as técnicas de escrita marcadas (foco, XYZ só com número
  confirmado, resultado primeiro, palavras-chave reformuladas e nunca inventadas).
- **FR-013**: Sem técnica marcada, o currículo MUST sair como hoje.
- **FR-014**: As técnicas e escolhas MUST vir de um catálogo único, que a skill de hoje e a página da
  Fase 6 usam.
- **FR-015**: Textos MUST estar em português do Brasil (os títulos do currículo seguem o formato).

### Key Entities *(include if feature involves data)*

- **Técnica**: caixa de marcar (ats, foco, xyz, resultado_primeiro, competencias_primeiro) com nome
  e explicação.
- **Escolha**: páginas (1, 2), formato (br, us, eu) e estilo (padrão, compacto, executivo), com o
  valor sugerido.
- **Currículo**: o conteúdo, o alvo (base ou vaga) e as técnicas e escolhas usadas.
- **Conferência**: veredito (ok, conferir, bloquear) e os pontos de ATS, requisitos (tem,
  sustentado, lacuna) e fatos, cada um com trecho e motivo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos currículos gerados seguem o papel, o idioma dos títulos e o estilo
  escolhidos.
- **SC-002**: Num conjunto de teste com números, empresas e cargos inventados, a conferência aponta
  100% deles; nenhum número fora do perfil passa com veredito "ok".
- **SC-003**: Nenhuma lacuna da vaga aparece como competência sem ser apontada.
- **SC-004**: Com o limite de 1 página, 100% dos currículos acima do limite recebem o aviso com as
  sugestões de corte.
- **SC-005**: A conferência de um currículo termina em até 5 segundos, sem IA.
- **SC-006**: Currículos pedidos sem técnica saem iguais aos de antes desta fase.

## Assumptions

- O motor continua gerando .docx e, quando há Word ou LibreOffice, PDF; nada de foto em nenhum
  formato.
- "Sustentado" = o perfil traz algo equivalente (sinônimo, ferramenta da mesma família ou
  experiência que cobre o requisito); a decisão final de usar fica com a pessoa.
- A tradução para inglês (formatos Estados Unidos e Europa) é feita pela skill a partir do perfil,
  fielmente, e a pessoa revisa; a ferramenta não traduz sozinha.
- A sugestão de formato vem do país e do idioma da vaga quando conhecidos; senão, Brasil.
- A geração pela página (botão "Gerar currículo" no detalhe da vaga) fica para a Fase 6; esta fase
  entrega o motor, a conferência e a skill de chat.
- Verificação só no Windows.
