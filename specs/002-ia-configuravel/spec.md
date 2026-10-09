# Feature Specification: IA configurável

**Feature Branch**: `002-ia-configuravel` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Fase 1 do roteiro: IA configurável. A pessoa escolhe o provedor de
IA usado nas chamadas diretas da ferramenta (análise automática das vagas agora; currículo, carta
e anamnese nas fases seguintes): Claude Code pela assinatura, Anthropic, OpenAI e compatíveis
(OpenRouter, Groq, DeepSeek) e Gemini por chave, ou sem IA. Painel "IA" na página para escolher
provedor e modelo, informar a chave (só no arquivo local de chaves, nunca devolvida à página nem
ao config), testar a conexão e ver avisos de custo, de variação das notas e de privacidade. Sem
IA, a ferramenta continua funcionando. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher o provedor e conectar (Priority: P1)

Uma pessoa que não usa o Claude Code, mas tem uma chave de outro provedor (ex.: Gemini ou OpenAI),
abre o painel "IA" na página, escolhe o provedor, aceita o modelo sugerido ou informa outro, cola a
chave, testa a conexão e salva. A partir daí a ferramenta usa esse provedor.

**Why this priority**: hoje só quem tem o Claude Code instalado ganha a nota de aderência; abrir
para outros provedores é o que torna a IA da ferramenta acessível a qualquer pessoa.

**Independent Test**: com uma chave válida de um provedor, configurar pelo painel, testar a
conexão e ver a confirmação de sucesso; conferir que a chave não aparece em nenhum lugar da página
nem da configuração.

**Acceptance Scenarios**:

1. **Given** nenhum provedor configurado por chave, **When** a pessoa escolhe um provedor, cola a
   chave e clica em testar, **Then** a página mostra em poucos segundos se a conexão funcionou ou,
   se não, o motivo em linguagem simples.
2. **Given** a conexão testada, **When** a pessoa salva, **Then** a escolha passa a valer, a chave
   fica guardada só no arquivo local de chaves e a página passa a mostrar apenas que há uma chave
   cadastrada (com os últimos 4 caracteres), nunca a chave inteira.
3. **Given** uma chave já salva, **When** a pessoa troca ou remove a chave, **Then** a mudança
   vale na hora e as outras chaves do arquivo local continuam intactas.

---

### User Story 2 - A análise automática usa o provedor escolhido (Priority: P1)

Depois de configurar, a pessoa adiciona uma vaga pelo link ou à mão e ela recebe a nota de
aderência pelo provedor escolhido, com o mesmo formato e as mesmas regras de hoje. No detalhe da
vaga aparece qual provedor e modelo deram a nota.

**Why this priority**: é o uso real da IA hoje; sem ele, configurar o provedor não serve para nada.

**Independent Test**: com um provedor por chave configurado, adicionar uma vaga com descrição e
ver a nota aparecer no relatório, com o provedor e o modelo indicados no detalhe.

**Acceptance Scenarios**:

1. **Given** um provedor por chave configurado, **When** uma vaga com descrição é adicionada,
   **Then** ela recebe nota, encaixes, lacunas e alertas como hoje, e o detalhe mostra o provedor e
   o modelo usados.
2. **Given** o Claude Code instalado e nada configurado, **When** uma vaga é adicionada, **Then** a
   análise roda pelo Claude Code como hoje, sem nenhuma ação da pessoa.
3. **Given** uma falha do provedor (chave recusada, sem crédito, limite de uso, fora do ar), **When**
   a análise roda, **Then** a vaga continua esperando nota, a ferramenta não para e a página mostra
   o motivo.

---

### User Story 3 - Usar sem IA (Priority: P2)

Quem não quer enviar dados a nenhum provedor escolhe "Sem IA". A ferramenta continua buscando
vagas, mostrando o relatório e o quadro; as vagas ficam sem nota e nada é enviado a provedores.

**Why this priority**: a constituição garante que a IA é opcional; a escolha precisa ser explícita
e fácil de ver.

**Independent Test**: escolher "Sem IA", adicionar uma vaga e confirmar que ela fica sem nota, que
nenhum provedor é chamado e que busca, relatório e quadro funcionam.

**Acceptance Scenarios**:

1. **Given** "Sem IA" escolhido, **When** uma vaga é adicionada, **Then** ela fica sem nota e
   nenhuma chamada é feita a provedores.
2. **Given** a configuração antiga que desliga a análise automática, **When** a ferramenta abre,
   **Then** ela é tratada como "Sem IA", sem a pessoa precisar refazer nada.

---

### User Story 4 - Saber o que significa usar cada IA (Priority: P2)

No painel, antes de salvar, a pessoa vê de forma clara: se o uso é cobrado por chamada (chave de
API) ou pela assinatura que já tem; que notas de modelos diferentes podem variar para a mesma vaga;
que o perfil e o texto das vagas vão para o provedor escolhido; e que planos gratuitos de alguns
provedores podem usar os dados enviados, então vale conferir os termos.

**Why this priority**: o princípio "local e privado" exige que a pessoa saiba para onde vão os
dados antes de escolher; evita surpresa com custo.

**Independent Test**: abrir o painel e conferir os quatro avisos, e que eles mudam conforme o
provedor (ex.: assinatura × cobrança por uso).

**Acceptance Scenarios**:

1. **Given** o painel aberto, **When** a pessoa escolhe um provedor por chave, **Then** os avisos de
   custo por uso, variação das notas, envio de dados e termos de planos gratuitos aparecem antes do
   botão de salvar.

---

### Edge Cases

- Chave recusada ou expirada: o teste e a análise mostram "chave recusada pelo provedor"; nada
  quebra.
- Sem crédito ou limite de uso atingido: mensagem dizendo isso; a vaga continua esperando e entra
  na próxima tentativa.
- Sem internet ou provedor fora do ar: mesma regra; a ferramenta segue funcionando.
- Modelo inexistente ou sem acesso: mensagem com o nome do modelo e a sugestão do padrão.
- Resposta da IA fora do formato esperado: a vaga continua esperando, com o motivo registrado; nada
  é gravado pela metade.
- "Claude Code" escolhido sem o Claude Code instalado: o painel avisa e o teste falha com essa
  explicação.
- Troca de provedor durante uma análise em andamento: a rodada em curso termina com o provedor
  anterior; a próxima já usa o novo.
- O arquivo local de chaves já tem outras chaves (ex.: de uma fonte de vagas): todas são
  preservadas ao salvar ou remover a chave da IA.
- A chave aparece numa mensagem de erro do provedor: ela é escondida antes de chegar à página ou
  aos registros.
- Página aberta por outro aparelho da rede local: ela pode ver qual provedor está ativo, mas não
  pode trocar o provedor nem gravar ou remover chave.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A página MUST ter um painel "IA" com estas opções: Claude Code (assinatura), Anthropic
  (chave), OpenAI (chave), OpenRouter (chave), Groq (chave), DeepSeek (chave), Gemini (chave), outro
  serviço compatível com OpenAI (endereço e chave) e Sem IA.
- **FR-002**: Para cada provedor, o painel MUST sugerir um modelo padrão e permitir trocar o modelo
  por outro nome.
- **FR-003**: A chave MUST ser gravada só no arquivo local de chaves do projeto (fora do controle de
  versão), uma por provedor, preservando as demais linhas do arquivo; MUST NOT ir para a
  configuração nem voltar para a página — a página mostra apenas "chave cadastrada" e os últimos 4
  caracteres.
- **FR-004**: A pessoa MUST poder trocar e remover a chave de um provedor pelo painel.
- **FR-005**: O painel MUST oferecer "testar conexão", que faz uma chamada mínima ao provedor e
  mostra sucesso ou o motivo da falha (chave recusada, sem crédito, limite de uso, modelo
  inexistente, sem internet, Claude Code não instalado).
- **FR-006**: A análise automática das vagas MUST usar o provedor e o modelo escolhidos, com as
  mesmas regras de nota e a mesma validação de hoje.
- **FR-007**: Cada análise MUST registrar o provedor e o modelo que a fizeram, e o detalhe da vaga
  MUST mostrá-los.
- **FR-008**: Com "Sem IA", a ferramenta MUST NOT chamar nenhum provedor; as vagas ficam sem nota e
  busca, relatório e quadro continuam funcionando.
- **FR-009**: O painel MUST mostrar, antes de salvar, avisos sobre: custo por uso (chave) ou
  assinatura; variação das notas entre modelos; envio do perfil e do texto das vagas ao provedor;
  e termos de planos gratuitos que podem permitir o uso dos dados.
- **FR-010**: Nenhum dado MUST ser enviado a um provedor que a pessoa não tenha escolhido e salvo.
- **FR-011**: Trocar o provedor, gravar ou remover chave MUST ser aceito só de páginas abertas no
  próprio computador, nunca de outro aparelho da rede local.
- **FR-012**: Chaves MUST NOT aparecer na página, na configuração, nas mensagens de erro nem nos
  registros da ferramenta.
- **FR-013**: Falhas do provedor MUST NOT derrubar a ferramenta; a vaga continua esperando nota e o
  motivo da última falha aparece na página.
- **FR-014**: Sem nenhuma configuração de IA, a ferramenta MUST se comportar como hoje: usa o
  Claude Code se estiver instalado; senão, fica sem IA. A configuração antiga que desliga a análise
  automática MUST valer como "Sem IA".
- **FR-015**: A escolha de provedor MUST ser única para toda a ferramenta, para que as chamadas
  diretas das fases seguintes (currículo, carta, anamnese) usem a mesma.
- **FR-016**: Todos os textos MUST estar em português do Brasil.

### Key Entities

- **Escolha de IA**: provedor, modelo e, para "outro compatível", o endereço do serviço. Vive na
  configuração local (sem chave).
- **Chave do provedor**: segredo de um provedor, guardado só no arquivo local de chaves; a página
  conhece apenas se existe e os últimos 4 caracteres.
- **Registro da análise**: na vaga analisada, o provedor, o modelo e quando a análise foi feita;
  em caso de falha, o motivo da última tentativa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa com a chave em mãos configura um provedor e testa a conexão em até
  2 minutos, sem editar arquivo nenhum.
- **SC-002**: O teste de conexão mostra o resultado em até 15 segundos.
- **SC-003**: Buscando a chave em todos os arquivos do projeto (exceto o arquivo local de chaves) e
  em todas as respostas da página, ela aparece 0 vezes.
- **SC-004**: Uma vaga adicionada com descrição recebe nota pelo provedor escolhido em até
  2 minutos.
- **SC-005**: Com "Sem IA", nenhuma chamada a provedores acontece durante o uso normal (adicionar
  vaga, buscar, abrir o relatório e o quadro).
- **SC-006**: Quem já usava o Claude Code e não configura nada continua com a análise automática
  funcionando, sem nenhuma ação.
- **SC-007**: Todas as falhas listadas nos casos-limite terminam com uma mensagem que diz o motivo.

## Assumptions

- A pessoa obtém a própria chave no site do provedor; criar conta e conseguir a chave está fora do
  escopo (o painel pode apontar onde conseguir).
- A ferramenta não mede nem estima gasto; o custo é responsabilidade do provedor e da pessoa.
- Modelos: um padrão sugerido por provedor, atualizável na implementação, e campo livre para outro
  nome; sem listar modelos dinamicamente.
- Fora do escopo: modelos rodando localmente (decisão do usuário); as skills de conversa, que
  continuam no Claude Code nesta fase (portabilidade é a Fase 2 do roteiro); busca pela página e os
  novos usos de IA (currículo, carta, anamnese), que vêm nas fases seguintes e usarão esta escolha.
- Uma configuração de IA por computador (sem perfis por pessoa).
- Foco em Windows (decisão do usuário); macOS e Linux seguem a lista de desejos.
