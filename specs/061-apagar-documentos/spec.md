# Feature Specification: Documento apagado na página some da pasta

**Feature Branch**: `061-apagar-documentos` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Fiz alguns testes e notei que os documentos gerados, como currículos e cartas, depois
de apagados do front continuam existindo nos arquivos. O documento apagado no front deve ser apagado totalmente."

## Contexto

A ferramenta gera, para cada vaga, currículos, cartas de apresentação e respostas de formulário, e guarda os arquivos
na pasta `curriculos/` do computador da pessoa (texto, Word, PDF e uma ficha com os dados de cada geração).

Hoje só o currículo tem lixeira (spec 052), e ela apaga todos os arquivos dele. Nos outros caminhos, o documento some
da página, mas o arquivo fica na pasta:

- **Remover a vaga** pela lixeira do quadro ("Remover de Aplicações"): a vaga sai do quadro e o currículo, a carta e
  as respostas dela ficam na pasta, sem aparecer em lugar nenhum da página.
- **Cartas e respostas** não têm lixeira: cada nova geração cria outro arquivo, e as versões se acumulam no kit da
  vaga.
- **Arquivar pela Limpeza** (spec 054) mantém os arquivos de propósito e guarda os nomes deles na ficha da vaga
  arquivada.

Na pasta de quem já usava a ferramenta havia currículos, cartas e respostas de vagas que já tinham saído do quadro.

Princípios da constituição: a pessoa decide (V) e os dados pessoais ficam só no computador dela (`curriculos/` fora
do Git). Apagar é uma ação que a pessoa pede, com confirmação antes.

## Clarifications

### Session 2026-11-26

- Q: Ao remover uma vaga do quadro, o que acontece com os documentos dela? → A: São apagados junto, e a confirmação
  avisa antes.
- Q: Como apagar cartas e respostas? → A: Uma lixeira em cada carta e em cada resposta do kit da vaga, como a do
  currículo.
- Q: A Limpeza continua guardando os arquivos ao arquivar? → A: Não. Arquivar apaga os documentos da vaga, e a ficha
  da vaga arquivada guarda só o registro de que existiram. Isso muda a decisão da spec 054 (FR-012 e US3, cenário 3).
- Q: E os arquivos que já ficaram para trás? → A: Um comando mostra os documentos de vagas que já saíram do quadro, e
  só apaga com o OK da pessoa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apagar uma carta ou uma resposta (Priority: P1)

No kit de uma vaga, cada carta e cada conjunto de respostas de formulário tem uma lixeira. A pessoa clica, confirma
("Apagar esta carta de vez? O texto, o Word e o PDF somem da pasta.") e o documento some da lista e da pasta.

**Why this priority**: é o caso mais visível. As versões se acumulam a cada nova geração (uma vaga do usuário tem 5
versões de respostas) e hoje não há como tirá-las.

**Independent Test**: gerar uma carta numa vaga de teste, apagar pelo kit e conferir que nenhum arquivo dela ficou na
pasta `curriculos/`.

**Acceptance Scenarios**:

1. **Given** uma vaga com duas cartas, **When** a pessoa apaga uma delas e confirma, **Then** essa carta some do kit e
   todos os arquivos dela saem da pasta; a outra continua.
2. **Given** um conjunto de respostas com respostas editadas pela pessoa, **When** ela clica na lixeira, **Then** a
   confirmação avisa que as respostas editadas também somem; só depois do OK elas são apagadas.
3. **Given** um arquivo da carta aberto em outro programa (ex.: o PDF no leitor), **When** a pessoa apaga, **Then**
   nada é apagado, a carta continua na lista e a página pede para fechar o arquivo e tentar de novo.
4. **Given** a pessoa cancela a confirmação, **When** a caixa fecha, **Then** nada muda.

---

### User Story 2 - Remover a vaga apaga os documentos dela (Priority: P1)

Quando a pessoa remove uma vaga do quadro pela lixeira, a confirmação avisa que os currículos, as cartas e as
respostas gerados para aquela vaga também serão apagados. Com o OK, a vaga sai do quadro como hoje e os documentos
saem da pasta.

**Why this priority**: é a origem dos arquivos esquecidos: depois que a vaga sai do quadro, a página não mostra mais
os documentos dela, então a pessoa não tem como apagá-los.

**Independent Test**: numa vaga de teste com um currículo e uma carta, remover pela lixeira e conferir que a pasta
não guarda nenhum arquivo dela.

**Acceptance Scenarios**:

1. **Given** uma vaga em Aplicações com currículo, carta e respostas, **When** a pessoa remove e confirma, **Then** a
   vaga sai do quadro e nenhum documento dela fica na pasta.
2. **Given** uma vaga sem documentos, **When** a pessoa remove, **Then** a confirmação não fala de documentos e o
   comportamento é o de hoje.
3. **Given** um documento da vaga aberto em outro programa, **When** a pessoa remove, **Then** nada é apagado, a vaga
   continua no quadro e a página pede para fechar o arquivo e tentar de novo.
4. **Given** a vaga tem relatos (o que a pessoa contou na candidatura assistida), **When** ela remove a vaga,
   **Then** os relatos continuam: são fatos dela, não documentos gerados.

---

### User Story 3 - Arquivar pela Limpeza apaga os documentos (Priority: P2)

Na Limpeza (spec 054), as vagas com documentos continuam destacadas e desmarcadas na prévia. O aviso passa a dizer
que arquivar apaga os currículos, as cartas e as respostas delas. Se a pessoa marcar e arquivar, os documentos saem
da pasta, e a ficha da vaga arquivada guarda só o registro de que existiram (quantos de cada tipo e a data em que
foram apagados).

**Why this priority**: a Limpeza existe para deixar a ferramenta leve; arquivar mantendo os arquivos contradiz isso,
mas o caso é menos frequente que os anteriores, porque as vagas com documentos já vêm desmarcadas.

**Independent Test**: com uma vaga fictícia destacada por ter carta, marcar, arquivar e conferir que a carta saiu da
pasta e que a ficha registra "1 carta apagada em 26/11/2026".

**Acceptance Scenarios**:

1. **Given** uma vaga destacada por ter currículo, **When** a pessoa a marca e arquiva, **Then** o currículo sai da
   pasta e a ficha da vaga registra que ele existiu.
2. **Given** uma vaga destacada que a pessoa não marcou, **When** ela arquiva as outras, **Then** os documentos dessa
   vaga continuam.
3. **Given** a limpeza pelo terminal com a opção que inclui as destacadas, **When** a gravação termina, **Then** os
   documentos dessas vagas foram apagados e o resumo diz quantos.
4. **Given** um documento aberto em outro programa durante a limpeza, **When** a gravação chega nessa vaga, **Then**
   essa vaga não é arquivada, as outras seguem, e o resumo diz qual ficou e por quê.

---

### User Story 4 - Limpar os documentos que já ficaram para trás (Priority: P2)

Um comando pelo terminal (ou pelo chat, com o assistente) lista os documentos de vagas que já saíram do quadro ou
foram arquivadas antes desta mudança: tipo, vaga, empresa e data. Sem a opção de gravar, não apaga nada. Com a opção
e o OK da pessoa, apaga e diz quantos.

**Why this priority**: resolve o que já existe na pasta de quem usava a ferramenta antes; roda uma vez.

**Independent Test**: com uma pasta de teste com documentos de vagas removidas, o comando mostra cada um e não apaga nada
sem a opção de gravar.

**Acceptance Scenarios**:

1. **Given** documentos de vagas removidas do quadro, **When** a pessoa roda o comando sem gravar, **Then** ele lista
   cada documento e não apaga nada.
2. **Given** a mesma lista, **When** a pessoa roda com a opção de gravar, **Then** os documentos listados saem da
   pasta e o resumo diz quantos de cada tipo.
3. **Given** documentos de vagas que estão no quadro, **When** o comando roda, **Then** eles não aparecem na lista.
4. **Given** um documento cuja vaga não existe mais no banco, **When** o comando roda, **Then** ele aparece na lista
   como "vaga não encontrada".

### Edge Cases

- Documento ligado a uma vaga que foi juntada a outra (vagas repetidas, spec 058): pertence à vaga que ficou, e só sai
  com ela.
- Currículo geral (sem vaga): não entra em remover vaga, Limpeza nem no comando de órfãos; só sai pela lixeira dele.
- Currículo que saiu da análise de reprovação (spec 049): apagar tira também a referência dele da análise, como a
  lixeira de hoje.
- Um arquivo de um documento já sumiu da pasta (apagado à mão): apagar o resto não dá erro.
- A pessoa abre a página em outro computador da rede: as lixeiras ficam desativadas, como os outros botões que gravam.
- Respostas salvas na memória da candidatura assistida (o que a pessoa respondeu e a ferramenta reaproveita) não são
  documentos da vaga e não são apagadas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada carta e cada conjunto de respostas no kit da vaga MUST ter uma lixeira que, depois da confirmação,
  apaga todos os arquivos daquele documento da pasta e o tira da lista.
- **FR-002**: A confirmação MUST dizer o que some (o texto, o Word e o PDF; nas respostas, também as respostas
  editadas pela pessoa).
- **FR-003**: Apagar MUST ser tudo ou nada por documento: se um arquivo estiver aberto em outro programa, nada daquele
  documento é apagado e a página pede para fechar e tentar de novo (como a lixeira do currículo, spec 052).
- **FR-004**: Remover uma vaga pela lixeira do quadro MUST apagar todos os currículos, cartas e respostas gerados para
  ela; a confirmação MUST dizer quantos documentos de cada tipo serão apagados (sem documentos, a confirmação de hoje).
- **FR-005**: Se algum documento da vaga não puder ser apagado, a vaga MUST continuar no quadro e nenhum documento dela
  é apagado.
- **FR-006**: Arquivar pela Limpeza MUST apagar os documentos da vaga arquivada; a ficha curta MUST trocar os nomes dos
  documentos pelo registro de que existiram (quantidade por tipo e data em que foram apagados). As vagas com
  documentos continuam destacadas e desmarcadas na prévia, e o aviso MUST dizer que arquivar apaga os documentos.
- **FR-007**: Na Limpeza, uma vaga cujo documento não pode ser apagado MUST ficar sem arquivar, sem impedir as outras,
  e o resumo MUST dizer qual ficou e por quê.
- **FR-008**: Um comando MUST listar os documentos cuja vaga saiu do quadro, foi arquivada ou não existe mais, com
  tipo, vaga, empresa e data, sem apagar nada; só com a opção de gravar (e o OK da pessoa) ele apaga e diz quantos.
- **FR-009**: Relatos, a memória de respostas da candidatura assistida, os dados de contato e o currículo geral (sem
  vaga) MUST NOT ser apagados por nenhum desses caminhos.
- **FR-010**: Apagar um currículo ligado a uma análise de reprovação MUST tirar a referência dele da análise.
- **FR-011**: As lixeiras MUST funcionar só no computador onde a ferramenta roda.
- **FR-012**: A documentação MUST registrar a mudança: o contrato da página (apagar cartas e respostas, remover vaga
  com documentos), a Limpeza (spec 054 passa a apagar os arquivos), o comando novo no `AGENTS.md` e no README.

### Key Entities

- **Documento gerado**: currículo, carta ou conjunto de respostas de uma vaga (ou currículo geral, sem vaga). Tem um
  nome, um tipo, a vaga a que pertence, a data e de 1 a 4 arquivos na pasta (texto, Word, PDF, dados).
- **Ficha da vaga arquivada** (spec 054): passa a guardar, no lugar dos nomes dos documentos, quantos de cada tipo
  existiam e quando foram apagados.
- **Documento órfão**: documento de uma vaga que saiu do quadro, foi arquivada ou não existe mais.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Depois de apagar uma carta ou uma resposta, ou de remover uma vaga, 0 arquivos daquele documento ou
  daquela vaga continuam na pasta.
- **SC-002**: Nenhum documento de uma vaga que ainda está no quadro é apagado pelo comando de órfãos nem pela Limpeza
  sem a vaga ter sido marcada.
- **SC-003**: Com um arquivo aberto em outro programa, 100% das tentativas de apagar terminam sem documento pela
  metade (ou todos os arquivos dele saem, ou nenhum).
- **SC-004**: Numa pasta com documentos de vagas que saíram do quadro, o comando de órfãos lista todos e, depois de
  gravar com o OK da pessoa, a pasta não tem nenhum documento de vaga fora do quadro.

## Assumptions

- "Documento da vaga" é o que a ferramenta gerou para ela (currículo, carta, respostas); arquivos que a pessoa enviou
  em Materiais (`anexos/`) não entram.
- Uma vaga "saiu do quadro" quando foi removida pela lixeira (hoje ela fica marcada como visitada, sem etapa) ou
  quando foi arquivada pela Limpeza.
- Não há lixeira de recuperação: apagar é definitivo, como na lixeira do currículo (spec 052). A confirmação existe
  para isso.
- O currículo geral (sem vaga) continua com a lixeira de hoje e não muda nesta spec.
