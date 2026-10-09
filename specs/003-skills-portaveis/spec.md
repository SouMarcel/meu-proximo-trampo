# Feature Specification: Skills portáveis

**Feature Branch**: `003-skills-portaveis` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Fase 2 do roteiro: skills portáveis. As skills de conversa da
ferramenta (buscar-vagas, consultar-gupy, gerar-curriculo) só funcionam no Claude Code. A pessoa
deve poder usá-las em outros assistentes que leem o formato SKILL.md (Codex, Gemini CLI, OpenCode,
além do Claude Code), sem perder nada no Claude Code: AGENTS.md na raiz, skills num lugar que todos
leem com uma única fonte (atenção aos links simbólicos no Windows), texto sem depender de ferramenta
exclusiva e README explicando cada assistente. Skills de desenvolvimento (spec-kit, graphify) ficam
fora. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Usar a ferramenta com outro assistente (Priority: P1)

Uma pessoa que usa o Codex, o Gemini CLI ou o OpenCode (e não o Claude Code) abre a pasta da
ferramenta no assistente dela e pede, como faria no Claude Code: "busca vagas novas pra mim",
"monta meu currículo" ou "tem vaga de analista na empresa X na Gupy?". O assistente encontra as
mesmas instruções e conduz o mesmo fluxo. Onde o assistente não tem uma ferramenta específica,
as instruções têm um caminho alternativo: perguntas com opções viram perguntas em texto com
opções numeradas, e um link que ele não consegue abrir vira um pedido para a pessoa colar o texto.

**Why this priority**: a Fase 1 abriu a IA das chamadas diretas para outros provedores; sem as
skills portáveis, quem não usa o Claude Code continua sem a busca com nota pelo chat, sem o
currículo guiado e sem as consultas à Gupy.

**Independent Test**: num assistente diferente do Claude Code, fazer os três pedidos acima e ver o
assistente seguir as instruções da skill certa, sem a pessoa apontar o arquivo.

**Acceptance Scenarios**:

1. **Given** a pasta aberta em um dos assistentes suportados, **When** a pessoa pede uma busca de
   vagas, **Then** o assistente segue as instruções de busca da ferramenta (rodar a busca, avaliar
   as candidatas, gravar no dashboard) como no Claude Code.
2. **Given** um assistente sem ferramenta de perguntas com opções, **When** a skill precisa de uma
   decisão da pessoa, **Then** ele pergunta em texto, com as opções numeradas.
3. **Given** um assistente sem ferramenta de leitura de páginas, **When** a skill precisaria abrir o
   link de uma vaga, **Then** ele pede que a pessoa cole o texto da vaga.
4. **Given** um assistente sem a integração da Gupy configurada, **When** a pessoa faz uma pergunta
   pontual sobre a Gupy, **Then** a resposta vem pelo caminho próprio da ferramenta, que consulta o
   mesmo serviço público da Gupy.

---

### User Story 2 - Nada muda para quem usa o Claude Code (Priority: P1)

Quem já usa o Claude Code continua com tudo igual: as skills são acionadas pelos mesmos pedidos,
as perguntas continuam com opções clicáveis, os links continuam sendo abertos e a consulta à Gupy
continua pela integração já configurada.

**Why this priority**: o Claude Code é o caminho principal hoje; portabilidade não pode piorar a
experiência atual.

**Independent Test**: no Claude Code, repetir os três pedidos da US1 e conferir o mesmo
comportamento de antes (skills listadas e acionadas, perguntas com opções, leitura de links,
consulta à Gupy pela integração).

**Acceptance Scenarios**:

1. **Given** o Claude Code aberto na pasta, **When** a pessoa faz os pedidos de antes, **Then** as
   mesmas três skills aparecem e são acionadas, com as mesmas ferramentas de antes.

---

### User Story 3 - Uma fonte só para quem mantém (Priority: P2)

Quem mantém a ferramenta edita cada skill num único lugar. Se algum assistente exigir as skills em
outra pasta, a cópia é gerada a partir da fonte e há uma verificação que acusa qualquer diferença,
para que nenhum assistente fique com uma versão antiga.

**Why this priority**: cópias que divergem fazem assistentes diferentes darem respostas
diferentes; e links simbólicos do Git costumam virar arquivos quebrados no Windows.

**Independent Test**: alterar uma frase de uma skill na fonte, rodar a geração e a verificação, e
ver todas as cópias iguais; alterar uma cópia à mão e ver a verificação acusar.

**Acceptance Scenarios**:

1. **Given** uma skill editada só na fonte, **When** a verificação roda sem a geração, **Then** ela
   acusa quais cópias estão diferentes.
2. **Given** um clone novo no Windows sem suporte a links simbólicos, **When** a pessoa abre a pasta
   em qualquer assistente suportado, **Then** as skills aparecem completas, sem arquivos quebrados.

---

### User Story 4 - Saber como usar com cada assistente (Priority: P3)

O README explica, para Claude Code, Codex, Gemini CLI e OpenCode: como abrir a pasta, como pedir
(exemplos), o que muda em relação ao Claude Code (perguntas em texto, colar o texto da vaga,
consulta à Gupy pelo caminho próprio) e o que é exclusivo do Claude Code (as skills de LinkedIn
recomendadas, que vêm de um plugin dele).

**Why this priority**: sem orientação, a pessoa não sabe que a ferramenta funciona no assistente
dela; mas o funcionamento em si vem das histórias anteriores.

**Independent Test**: seguir o README do zero em um assistente e conseguir fazer um pedido.

**Acceptance Scenarios**:

1. **Given** o README, **When** a pessoa procura o assistente dela, **Then** encontra os passos e as
   diferenças daquele assistente.

---

### Edge Cases

- Assistente que lê só o arquivo de instruções da raiz e não descobre skills sozinho: as instruções
  da raiz listam cada skill, quando usar e o caminho do arquivo para ele ler.
- Clone no Windows com links simbólicos desligados: a estrutura não depende de links.
- Skill que chama outra skill ("isso é com a consultar-gupy"): a instrução diz qual skill e onde
  está o arquivo, sem depender de comando exclusivo de um assistente.
- Comando para rodar os scripts da ferramenta: as instruções dizem como chamar o Python do
  ambiente preparado pelo comando de iniciar, em qualquer assistente.
- Skills de desenvolvimento (spec-kit, graphify) continuam disponíveis no Claude Code para quem
  desenvolve, mas não aparecem como skills da ferramenta nos outros assistentes.
- Pessoa edita uma cópia gerada por engano: a verificação acusa e a próxima geração sobrescreve
  com a fonte (aviso no topo da cópia dizendo de onde ela vem).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A raiz MUST ter um arquivo de instruções comum, lido pelos assistentes suportados,
  com: o que é a ferramenta, as regras gerais de conduta (só fatos confirmados, indicar e não sair
  fazendo, dados pessoais fora do Git), como rodar os scripts da ferramenta e a lista das skills de
  usuário com quando usar cada uma e onde está o arquivo.
- **FR-002**: As skills de usuário (buscar-vagas, consultar-gupy, gerar-curriculo) MUST estar num
  local que Claude Code, Codex, Gemini CLI e OpenCode encontram, com todos os arquivos de apoio
  (modelos, referências).
- **FR-003**: Cada skill MUST ter uma única fonte editável. Se algum assistente exigir outro local,
  a cópia MUST ser gerada a partir da fonte, MUST trazer no topo de onde vem e MUST haver uma
  verificação que acusa qualquer diferença. A estrutura MUST NOT depender de links simbólicos.
- **FR-004**: O texto das skills MUST NOT exigir ferramenta exclusiva de um assistente: perguntas
  com opções usam a ferramenta de perguntas quando existir, senão texto com opções numeradas;
  leitura de link usa a ferramenta de leitura web quando existir, senão pede o texto à pessoa;
  referência a outra skill cita o nome e o arquivo.
- **FR-005**: A consulta pontual à Gupy MUST funcionar sem a integração de ferramentas configurada
  no assistente, por um caminho próprio da ferramenta que consulta o mesmo serviço público; quando a
  integração existir (como no Claude Code), ela continua sendo usada.
- **FR-006**: No Claude Code, o comportamento MUST ser o mesmo de antes: mesmas skills acionadas
  pelos mesmos pedidos, perguntas com opções, leitura de links e consulta à Gupy pela integração.
- **FR-007**: As skills de desenvolvimento (spec-kit, graphify) MUST NOT ser expostas como skills da
  ferramenta nos outros assistentes.
- **FR-008**: O README MUST ter uma seção por assistente (Claude Code, Codex, Gemini CLI, OpenCode)
  com como abrir, exemplos de pedidos, diferenças e o que é exclusivo do Claude Code.
- **FR-009**: O conteúdo das skills (regras de nota, formatos, fluxos, só fatos confirmados) MUST
  continuar o mesmo; a mudança é só na dependência de ferramentas e na localização.
- **FR-010**: Todos os textos MUST estar em português do Brasil.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em cada assistente suportado disponível para teste, os três pedidos-exemplo (buscar
  vagas, montar currículo, pergunta sobre a Gupy) levam à skill certa sem a pessoa indicar o
  arquivo.
- **SC-002**: Nas skills de usuário, 0 instruções exigem ferramenta exclusiva sem caminho
  alternativo.
- **SC-003**: A verificação de cópias passa sem diferenças logo depois da geração e acusa 100% das
  cópias editadas à mão.
- **SC-004**: No Claude Code, as três skills continuam listadas e acionadas pelos mesmos pedidos de
  antes.
- **SC-005**: A consulta à Gupy responde, num assistente sem a integração configurada, em até
  30 segundos.
- **SC-006**: Um clone novo no Windows mostra as skills completas em todos os assistentes
  suportados, sem nenhum arquivo quebrado.

## Assumptions

- A pessoa instala o assistente que quiser e abre a pasta nele; instalar e configurar cada
  assistente está fora do escopo (o README aponta a documentação oficial).
- Assistentes suportados nesta feature: Claude Code, Codex, Gemini CLI e OpenCode. Outros que
  leiam o mesmo formato tendem a funcionar, sem garantia.
- As skills de LinkedIn recomendadas no README continuam exclusivas do Claude Code (são um plugin
  dele, de terceiros).
- A sintaxe para chamar uma skill pelo nome muda entre assistentes; os pedidos em linguagem natural
  funcionam em todos.
- Assistentes não disponíveis nesta máquina para teste ficam com a verificação registrada como
  pendente no quickstart.
- Foco em Windows (decisão do usuário); macOS e Linux seguem a lista de desejos.
