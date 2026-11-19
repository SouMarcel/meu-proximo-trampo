# Feature Specification: Páginas em duas opções (Completo ou Até N) e apagar currículo gerado

**Feature Branch**: `052-paginas-ate-n` (worktree saída da `master`)

**Created**: 2026-11-19

**Status**: Aprovada e concluída em 2026-11-19

**Input**: Pedido do usuário no diálogo Gerar currículo. Hoje o campo Páginas tem três opções: "Completo (sem limite,
tudo do perfil)", "1 página" e "Até 2 páginas". Ele quer só duas: **Completo** e **Até N páginas**, com N escolhido de
1 a 5. A caixa "Limite de páginas obrigatório", que hoje fica na lista de Técnicas, passa para a área de Páginas.
No mesmo dia, ele pediu um botão de lixeira para apagar um currículo gerado, depois dos botões PDF e .docx de cada
currículo da lista.

## Contexto

A spec 051 criou o limite concreto de conteúdo enviado à IA (o "orçamento": tamanho do resumo, experiências completas,
itens, cursos e total de palavras), mas só para 1 e 2 páginas. Ela também criou a caixa "Limite de páginas
obrigatório", que faz a IA encurtar o currículo que passou do limite, e a opção Completo, que só aparece no currículo
base. A caixa ficou junto das técnicas de escrita (Foco, XYZ etc.), longe da escolha de páginas a que ela se refere.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher Completo ou Até N páginas, de 1 a 5 (Priority: P1)

No diálogo do currículo, a área **Páginas** tem duas opções:
- **Completo (sem limite, tudo do perfil)**;
- **Até N páginas**, com N escolhido numa lista de 1 a 5. A lista vem com 2, o padrão de hoje.

A pessoa escolhe, por exemplo, "Até 3 páginas", e o currículo é pedido à IA com o limite concreto de conteúdo para 3
páginas.

**Why this priority**: é o pedido central. Perfis longos precisam de 3 páginas ou mais, e hoje a única saída é o
Completo, sem limite nenhum.

**Independent Test**: abrir o diálogo do currículo base e ver as duas opções, com a lista de 1 a 5 marcada em 2.
Gerar com "Até 4 páginas" e conferir que o pedido à IA traz o limite de conteúdo de 4 páginas e que o registro do
currículo guarda o limite 4.

**Acceptance Scenarios**:

1. **Given** o diálogo do currículo base, **When** ele abre, **Then** a área Páginas mostra "Completo" e "Até N
   páginas", com "Até 2 páginas" marcado.
2. **Given** a opção "Até N páginas", **When** a pessoa abre a lista, **Then** ela vê os números de 1 a 5, e só eles.
3. **Given** qualquer N de 1 a 5, **When** a ferramenta monta o pedido à IA, **Then** o pedido traz o limite concreto
   de conteúdo daquele N. O limite de conteúdo cresce com N: mais palavras, mais itens e mais experiências completas.
4. **Given** um currículo gerado com "Até N páginas" que passou de N páginas, **When** a pessoa olha a lista de
   currículos, **Then** o aviso diz quantas páginas deram e qual era o limite N, como hoje faz para 1 e 2.
5. **Given** o diálogo do currículo de uma vaga, **When** ele abre, **Then** a opção Completo não aparece (regra da
   spec 051) e a área Páginas mostra só "Até N páginas", com a lista de 1 a 5.
6. **Given** um pedido de geração com um número de páginas fora de 1 a 5 (nem Completo), **When** ele chega à
   ferramenta, **Then** é recusado com uma mensagem clara.

---

### User Story 2 - Limite obrigatório junto da escolha de páginas (Priority: P1)

A caixa **Limite de páginas obrigatório** sai da lista de Técnicas e passa a ficar na área Páginas, logo abaixo da
opção "Até N páginas". Ela continua desmarcada por padrão e faz o mesmo que hoje: se o currículo passar de N páginas,
a IA encurta.

A caixa só vale para "Até N páginas". Com Completo escolhido, ela fica desabilitada, porque não há limite para
obrigar.

**Why this priority**: faz parte do mesmo pedido. A caixa só tem sentido junto do limite que ela torna obrigatório.

**Independent Test**: abrir o diálogo e ver a caixa na área Páginas, e não em Técnicas. Escolher Completo e ver a
caixa desabilitada. Voltar para "Até N páginas" e ver a caixa habilitada de novo, com a marcação que tinha.

**Acceptance Scenarios**:

1. **Given** o diálogo aberto, **When** a pessoa olha a lista de Técnicas, **Then** a caixa "Limite de páginas
   obrigatório" não está lá; ela aparece na área Páginas, com a mesma explicação de hoje.
2. **Given** a opção Completo escolhida, **When** a pessoa olha a caixa, **Then** ela está desabilitada, e o pedido
   de geração não liga o encurtamento.
3. **Given** "Até 3 páginas" com a caixa marcada e um currículo que deu 4 páginas, **When** a geração continua,
   **Then** a IA encurta para caber em 3 páginas, com as regras da spec 051 (no máximo 2 tentativas, só tirar ou
   condensar, nunca acrescentar fato).

---

### User Story 3 - Apagar um currículo gerado (Priority: P2)

Na lista de currículos gerados (do currículo base, em Meu perfil, e do currículo de uma vaga), cada currículo ganha
um botão de **lixeira**, depois dos botões PDF e .docx. Ao clicar, a página pede confirmação, dizendo que o currículo
será apagado de vez. Com a confirmação, a ferramenta apaga todos os arquivos daquele currículo (PDF, .docx e os dados
dele) e o tira da lista e da vaga a que estava ligado.

**Why this priority**: a pasta acumula versões de teste e currículos que a pessoa não vai usar, e hoje só dá para
apagá-los à mão na pasta. Não muda como o currículo é gerado, por isso fica atrás das US1 e US2.

**Independent Test**: gerar dois currículos base, clicar na lixeira do mais antigo e confirmar. Ele some da lista, os
arquivos dele somem da pasta e o outro continua. Clicar na lixeira e cancelar não apaga nada.

**Acceptance Scenarios**:

1. **Given** a lista de currículos, **When** a pessoa olha um currículo, **Then** vê a lixeira depois dos botões PDF e
   .docx, com a dica "Apagar este currículo".
2. **Given** um clique na lixeira, **When** a pessoa cancela a confirmação, **Then** nada é apagado.
3. **Given** a confirmação, **When** a ferramenta apaga, **Then** somem o PDF, o .docx e os dados do currículo, ele
   sai da lista e deixa de estar ligado à vaga. Os outros currículos, cartas e respostas não mudam.
4. **Given** um arquivo do currículo aberto em outro programa (por exemplo, o .docx no Word), **When** a ferramenta
   tenta apagar, **Then** nada fica pela metade e a página diz para fechar o arquivo e tentar de novo.
5. **Given** um pedido para apagar algo que não é um currículo gerado (outro nome, caminho fora da pasta, carta ou
   respostas), **When** ele chega à ferramenta, **Then** é recusado.

---

### Edge Cases

- **Currículos já gerados** com limite 1 ou 2: continuam válidos e aparecem na lista como antes.
- **Escolha sugerida** com o valor antigo (1 ou 2): continua sendo um N válido.
- **Análise de reprovação** (spec 049): usa as mesmas técnicas e o mesmo caminho de geração, então herda as opções
  novas. Como é sempre de uma vaga, não tem Completo.
- **Currículo pelo chat** (`curriculo.py` direto): aceita limite de 1 a 5 e Completo, com as sugestões de corte de
  sempre quando passa do limite.
- **Encurtar com limite alto** (4 ou 5 páginas) e poucas experiências: a regra das 3 experiências recentes completas
  continua; se não couber, vale a regra da falha da spec 051.
- **Sem programa para gerar o PDF**: as páginas não são medidas, e nada muda em relação a hoje.
- **Apagar o currículo que saiu de uma análise de reprovação** (spec 049): a análise continua, e o currículo apagado
  deixa de aparecer como o currículo gerado por ela.
- **Apagar enquanto uma geração está em andamento**: o currículo que está sendo gerado ainda não está na lista; os
  outros podem ser apagados normalmente.
- **Currículo marcado como "seu currículo"** (o arquivo que a pessoa enviou, em anexos/): não é um currículo gerado,
  não aparece nessa lista e não tem lixeira.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A escolha Páginas MUST oferecer duas opções: Completo (só no currículo base, como na spec 051) e "Até N
  páginas", com N de 1 a 5.
- **FR-002**: O N padrão MUST ser 2.
- **FR-003**: A ferramenta MUST aceitar qualquer N de 1 a 5 e Completo, e MUST recusar outros valores com mensagem
  clara. Completo continua recusado num currículo de vaga.
- **FR-004**: O pedido à IA MUST trazer um limite concreto de conteúdo para cada N de 1 a 5. Os de 1 e 2 ficam como
  estão. Os de 3, 4 e 5 MUST crescer com N: total de palavras, experiências recentes completas, itens por experiência
  e cursos.
- **FR-005**: O pedido para encurtar MUST usar o limite de conteúdo do N escolhido.
- **FR-006**: A caixa "Limite de páginas obrigatório" MUST aparecer na área Páginas, e não na lista de Técnicas, com
  a mesma explicação e desmarcada por padrão.
- **FR-007**: Com Completo escolhido, a caixa MUST ficar desabilitada e o encurtamento MUST NOT acontecer (isso a
  ferramenta já garante hoje).
- **FR-008**: Os rótulos MUST usar o singular para 1 ("Até 1 página") e o plural de 2 a 5 ("Até 3 páginas").
- **FR-009**: As instruções do chat (skill gerar-curriculo e guia de técnicas) e o contrato da API MUST descrever as
  opções novas e os limites de conteúdo de 3 a 5 páginas.
- **FR-010**: Cada currículo da lista de currículos gerados MUST ter um botão de lixeira depois dos botões PDF e .docx.
- **FR-011**: Apagar MUST pedir confirmação antes e MUST NOT apagar nada sem ela.
- **FR-012**: Apagar MUST remover todos os arquivos daquele currículo e a ligação dele com a vaga, e MUST NOT mexer em
  outros currículos, cartas, respostas ou no "seu currículo" de anexos/.
- **FR-013**: A ferramenta MUST aceitar apagar só currículos gerados, pelo nome validado, dentro da pasta de
  currículos. Uma falha no meio MUST NOT deixar o currículo pela metade sem avisar a pessoa.
- **FR-014**: A mudança na página MUST seguir o processo do front (código na branch `frontend-react`, montado pela
  Action no PR `front/atualizacao`), sem edição à mão em `dash/front/`.

### Key Entities

- **Escolha de páginas**: Completo (valor 0, só no base) ou um N de 1 a 5. Fica no registro do currículo gerado, como
  hoje.
- **Limite de conteúdo por N**: o orçamento que vai no pedido à IA, um para cada N de 1 a 5.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A pessoa escolhe qualquer limite de 1 a 5 páginas, ou Completo, em no máximo dois cliques na área
  Páginas.
- **SC-002**: A caixa do limite obrigatório fica na mesma área da escolha de páginas e nunca aparece entre as
  técnicas de escrita.
- **SC-003**: Com um perfil de 6 ou mais experiências, "Até 3 páginas" com a caixa obrigatória sai com no máximo 3
  páginas em pelo menos 4 de 5 gerações.
- **SC-004**: A pessoa apaga um currículo gerado em dois cliques (lixeira e confirmação), sem abrir a pasta.
- **SC-005**: Os currículos e testes que já existem continuam funcionando: a suíte inteira fica verde.

## Assumptions

- Os limites de conteúdo de 3 a 5 páginas seguem a proporção dos de 1 e 2 (cerca de 400 palavras por página) e são o
  ponto de partida. O ajuste fino vem do teste com o perfil real, dentro desta spec, como na spec 051.
- O limite máximo é 5 páginas. Quem precisa de mais usa o Completo, no currículo base.
- No currículo de uma vaga, o Completo continua fora (decisão da spec 051), então a área Páginas mostra só "Até N
  páginas".
- O nome do arquivo gerado não muda: só o Completo leva "completo" no nome.
