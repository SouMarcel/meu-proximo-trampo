# Feature Specification: Faixa salarial da vaga

**Feature Branch**: `028-faixa-salarial` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-24

**Status**: Concluída em 2026-10-24

**Input**: User description: "Adicione um botão também para sugestão de salário de acordo com a vaga. A ferramenta pode
procurar no Glassdoor sobre a empresa, vaga e salário."

## Contexto

Antes de se candidatar e antes da entrevista, a pessoa precisa saber quanto pedir. Hoje a ferramenta mostra só a
faixa que a vaga informa. Ela não mostra quanto pagam vagas parecidas, nem onde pesquisar.

Pesquisa feita em 2026-10-23 e 2026-10-24:

- **O Glassdoor recusa acesso automatizado.** As páginas de termos, de desenvolvedores e de salários deram HTTP 403.
  A constituição VI manda parar no primeiro bloqueio, sem contornar, e seguir os termos de cada fonte. Por isso a
  ferramenta não lê o Glassdoor: ela monta links que a pessoa abre no navegador dela.
- **Poucas vagas no Brasil publicam salário.** No banco de uso real, 0 de 128 vagas tinham o campo preenchido.
  Numa busca de 100 vagas de "analista de dados" no MCP da Gupy:
  - 91 vieram sem informação;
  - 6 com remuneração variável;
  - 3 com salário a combinar;
  - nenhuma com valor.

  O botão precisa, então, ser útil mesmo sem dados no banco: links de pesquisa e espaço para a pessoa anotar o que
  viu.

## Clarifications

### Session 2026-10-24

- Q: De onde vêm os números? → A: Vagas parecidas do banco que informam salário, mais links de pesquisa no Glassdoor.
  Ao ver que os dados são escassos, o usuário escolheu também o campo para colar a faixa que viu.
- Q: Onde fica o botão? → A: No card do quadro e numa seção da aba Candidatura do detalhe.
- Q: Novo CAGED (dado oficial)? → A: Fica para uma spec própria (lista de desejos), porque exige baixar arquivos
  grandes e uma dependência nova.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver a faixa de uma vaga do quadro (Priority: P1)

No card de uma vaga do quadro, a pessoa clica no ícone de nota. Abre a janela **Faixa salarial** com quatro partes:
- o que a vaga informa;
- as vagas parecidas do banco que informam salário, com a faixa por mês, a mediana (com 3 ou mais) e o link de cada
  uma;
- os links de pesquisa no Glassdoor e nos salários do Indeed, com o cargo e a empresa;
- o que ela já anotou.

**Independent Test**: com um banco de teste com uma vaga sem salário e três parecidas com salário, conferir a faixa, a
mediana e os links.

**Acceptance Scenarios**:

1. **Given** uma vaga do quadro (etapa diferente de Encerrada), **When** a pessoa clica no ícone de nota do card,
   **Then** abre a janela Faixa salarial, e não o detalhe da vaga.
2. **Given** vagas com cargo parecido, mesma moeda e nível compatível que informam salário, **When** a janela abre,
   **Then**:
   - ela mostra a menor e a maior faixa por mês e a mediana (com 3 ou mais);
   - cada vaga aparece com o texto original e o link.
3. **Given** uma vaga com cargo diferente, outra moeda ou outro nível, **When** a faixa é calculada, **Then** ela
   fica fora.
4. **Given** um "salário" que é benefício (VR, VA, auxílio), **When** a faixa é calculada, **Then** ele não conta.
5. **Given** nenhuma parecida com salário, **When** a janela abre, **Then** ela explica que poucas vagas publicam
   salário e destaca os links de pesquisa.

### User Story 2 - Anotar o que viu (Priority: P1)

A pessoa abre o link do Glassdoor no navegador dela, vê uma faixa, volta, cola "R$ 7 mil a R$ 10 mil por mês" com a
fonte "Glassdoor" e clica em Guardar. A anotação fica na vaga e aparece na preparação de entrevista, na parte de
salário.

**Acceptance Scenarios**:

1. **Given** texto e fonte preenchidos, **When** a pessoa clica em Guardar, **Then** a anotação aparece com a fonte e
   a data e fica gravada na vaga.
2. **Given** texto ou fonte vazios, **When** ela tenta guardar, **Then** a ferramenta recusa e diz o que falta.
3. **Given** uma anotação, **When** ela clica em apagar, **Then** a anotação some.
4. **Given** anotações na vaga, **When** ela abre o Preparar entrevista, **Then** a parte de salário mostra as
   anotações.

### User Story 3 - No detalhe e no terminal (Priority: P2)

A mesma seção aparece na aba Candidatura do detalhe da vaga, e `PY salarios.py <ID>` mostra tudo no terminal.

### Edge Cases

- **Salário em hora, dia ou ano:** é convertido para o mês só para comparar (ano ÷ 12, hora × 220, dia × 22), e o
  texto original continua visível.
- **Formatos diferentes:** formatos do Brasil ("R$ 5.000,00 a R$ 7.000") e de fora ("US$ 80k - 100k/yr", "$90,000",
  "€ 4.200 per month").
- **Empresa confidencial:** não entra nos links de pesquisa.
- **Vaga internacional:** os links usam glassdoor.com e indeed.com, e "salary".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo número mostrado MUST ter fonte: a vaga, uma vaga parecida com link ou uma anotação da pessoa com a
  fonte. Nenhum valor é estimado pela IA (constituição IV).
- **FR-002**: A ferramenta MUST NOT ler o Glassdoor nem outro site de salários. Os links MUST abrir no navegador da
  pessoa (constituição VI).
- **FR-003**: Vagas parecidas MUST ter:
  - semelhança de cargo ≥ 0,5, sem contar nível, modelo de trabalho e palavras comuns;
  - a mesma moeda;
  - nível compatível, quando os dois informam.

  Benefícios MUST NOT contar como salário.
- **FR-004**: O resumo MUST trazer o menor valor, o maior e, com 3 vagas ou mais, a mediana dos pontos médios, por mês.
- **FR-005**: A pessoa MUST poder guardar e apagar anotações (texto até 300 caracteres e fonte até 120, no máximo 20
  por vaga). Elas aparecem na preparação de entrevista.
- **FR-006**: O botão MUST aparecer no card de vagas do quadro, exceto as encerradas, e a seção MUST aparecer na aba
  Candidatura do detalhe.

### Key Entities

- **Anotação de salário:** `{texto, fonte, em}` em `salario_pesquisa` da vaga.

## Success Criteria *(mandatory)*

- **SC-001**: Em nenhum teste aparece número sem fonte.
- **SC-002**: O módulo não faz pedido de rede nem chama a IA (verificado no código pelos testes).
- **SC-003**: Da janela, a pessoa chega aos links de pesquisa e guarda uma anotação em menos de 1 minuto.

## Assumptions

- O banco é local e compartilhado com a busca. Quanto mais buscas, mais parecidas aparecem.
- O Novo CAGED e uma integração oficial do Glassdoor ficam na lista de desejos.
