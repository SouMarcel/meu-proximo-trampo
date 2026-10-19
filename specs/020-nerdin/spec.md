# Feature Specification: Nerdin na busca de vagas

**Feature Branch**: `020-nerdin` (pasta da spec; o trabalho acontece numa worktree saída da `master`)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Vamos adicionar um novo portal de pesquisa: https://www.nerdin.com.br/vagas.php. O
portal fica ativo por padrão na pesquisa de vagas."

## Contexto

A Nerdin é um portal brasileiro só de vagas de tecnologia (desenvolvimento, dados, infraestrutura, QA, produto e
áreas próximas). A busca e as páginas das vagas são públicas, sem login, e as regras do site para robôs permitem
ler a lista e as vagas (bloqueiam só login, candidatura e áreas internas). Não há API aberta, então vale a regra da
constituição (princípio VI) para portais sem API: só a parte pública, pausa entre consultas e parar no primeiro
bloqueio.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas da Nerdin na busca de sempre (Priority: P1)

A pessoa clica em "Buscar vagas" (ou pede no chat, ou roda no terminal). Com os mesmos cargos e a mesma janela de
tempo que já configurou, a busca traz também as vagas da Nerdin, com a etiqueta do portal, para o Relatório de
Vagas, junto das do Indeed e da Gupy.

**Why this priority**: é o pedido central; a Nerdin reúne vagas de TI que nem sempre estão nos outros portais.

**Independent Test**: com respostas do portal simuladas, rodar a busca e ver as vagas da Nerdin no relatório com o
título, a empresa, o local, a data, o modelo de trabalho e o link para a vaga original.

**Acceptance Scenarios**:

1. **Given** a Nerdin ligada, **When** a pessoa busca, **Then** as vagas da Nerdin aparecem no relatório com a
   etiqueta "Nerdin" e o link da vaga original.
2. **Given** a Nerdin desligada, **When** a pessoa busca, **Then** nenhuma consulta vai à Nerdin e o resultado é o
   mesmo de antes desta funcionalidade.
3. **Given** a mesma vaga na Nerdin e em outro portal, **When** a busca encontra as duas, **Then** o relatório mostra
   uma vaga só, com os dois portais, como já acontece entre Indeed e Gupy.
4. **Given** uma vaga da Nerdin que já está no quadro, **When** a busca a encontra de novo, **Then** ela não aparece
   como nova.
5. **Given** uma vaga da Nerdin publicada antes da janela de tempo da busca, **When** a busca roda, **Then** ela não
   entra, e a ferramenta não pede páginas mais antigas da lista.

---

### User Story 2 - Ligada por padrão, desligável no painel (Priority: P1)

Quem começa a usar a ferramenta já busca na Nerdin sem configurar nada. No painel "Filtros da busca", a seção Portais
mostra a Nerdin marcada, com uma linha sobre o que ela é; a pessoa desmarca se não procura vaga de TI.

**Why this priority**: foi pedido que o portal venha ativo; a pessoa precisa conseguir desligar sem editar arquivo.

**Independent Test**: com uma configuração nova, abrir o painel e ver a Nerdin marcada; desmarcar, salvar e ver o
contador de consultas cair.

**Acceptance Scenarios**:

1. **Given** uma configuração nova (ou sem a lista de portais), **When** a pessoa busca, **Then** a Nerdin é
   consultada junto com Indeed e Gupy.
2. **Given** uma configuração que já tem a lista de portais escolhida pela pessoa, **When** a ferramenta é
   atualizada, **Then** a lista dela não muda sozinha; a Nerdin aparece desmarcada no painel para ela ligar.
3. **Given** o painel de filtros, **When** a pessoa desmarca a Nerdin e salva, **Then** a próxima busca não a
   consulta, e o contador de consultas deixa de somar as dela.

---

### User Story 3 - Descrição completa para a nota de aderência (Priority: P2)

A lista da Nerdin não traz o texto da vaga. Para as vagas que vão para o relatório, a ferramenta lê a página da vaga
e guarda a descrição completa, que a análise com IA usa para dar a nota.

**Why this priority**: sem a descrição a nota fica pobre; mas a vaga já é útil só com o que a lista mostra.

**Independent Test**: com uma página de vaga simulada, conferir que a vaga do relatório recebe a descrição completa
e que vagas fora dos critérios ou já no quadro não geram leitura da página.

**Acceptance Scenarios**:

1. **Given** uma vaga da Nerdin que vai para o relatório, **When** a busca termina, **Then** ela tem a descrição
   completa da página da vaga.
2. **Given** uma vaga fora dos critérios pelo título ou já no quadro, **When** a busca termina, **Then** a página dela
   não foi lida.
3. **Given** a leitura da página falhar, **When** a busca termina, **Then** a vaga entra com o que veio da lista e
   fica marcada com descrição pendente, como nas outras fontes.

---

### User Story 4 - Adicionar uma vaga da Nerdin pelo link (Priority: P3)

A pessoa cola o link de uma vaga da Nerdin no Adicionar Vaga do dashboard. A ferramenta reconhece o portal, preenche
título, empresa, local, modelo e descrição, e a vaga não se repete quando a busca a encontra depois.

**Why this priority**: completa a integração; hoje esse link cairia como portal "Outra".

**Independent Test**: colar um link `nerdin.com.br/vaga_emprego/…` e ver a vaga com a etiqueta "Nerdin" e os dados
preenchidos; rodar uma busca que a encontra e ver que ela não volta como nova.

**Acceptance Scenarios**:

1. **Given** um link de vaga da Nerdin, **When** a pessoa adiciona, **Then** a vaga entra com a etiqueta "Nerdin" e os
   dados da página.
2. **Given** a vaga adicionada pelo link, **When** a busca a encontra, **Then** ela é reconhecida como a mesma vaga.

---

### User Story 5 - Respeito ao portal e bloqueio sem susto (Priority: P2)

A busca na Nerdin usa só a parte pública do site, com pausa entre os pedidos, e lê a página da vaga só quando
precisa. Se a Nerdin recusar os pedidos ou limitar as consultas, a ferramenta para de consultá-la pelo resto daquela
busca, avisa, e as outras fontes continuam.

**Why this priority**: segue a constituição (princípio VI) e evita que a busca inteira falhe por um portal.

**Independent Test**: simular a Nerdin respondendo "muitas consultas" na segunda página; conferir que não há nova
tentativa, que os pedidos seguintes à Nerdin são pulados, que o aviso aparece e que as vagas do Indeed e da Gupy
chegam ao relatório.

**Acceptance Scenarios**:

1. **Given** uma busca com vários cargos, **When** ela roda, **Then** há pausa entre os pedidos à Nerdin e nenhum
   pedido usa login, conta ou cookies da pessoa.
2. **Given** a Nerdin bloqueando no meio da busca, **When** a ferramenta recebe o bloqueio, **Then** não tenta de
   novo, pula os pedidos restantes à Nerdin, mostra o aviso no resumo da busca e entrega as vagas das outras fontes e
   as da Nerdin já lidas.

---

### Edge Cases

- **Busca sem nenhuma vaga** (cargo raro): segue normalmente, sem erro.
- **Vaga sem local** (a lista nem sempre mostra cidade): entra sem local; "Home Office" vira vaga remota.
- **"Salário a combinar"**: a vaga entra sem salário (nada é estimado).
- **Página da Nerdin mudou e nada é reconhecido**: a busca avisa "não consegui ler as vagas da Nerdin" e segue com
  as outras fontes, sem quebrar.
- **Busca na cidade**: a ferramenta mantém as vagas da cidade e do estado da pessoa; as outras cidades ficam de
  fora. As de Home Office chegam pela consulta remota, se ela aceita remoto.
- **Busca ampla do site**: a busca da Nerdin traz vagas que só citam o cargo no texto (ex.: "analista de dados"
  traz "Analista de Suporte"); ficam só as vagas cujo título bate com o cargo, como nas fontes do exterior.
- **País da busca nacional diferente do Brasil**: a Nerdin não é consultada (o portal é só do Brasil).
- **Busca internacional**: a Nerdin não entra nas consultas de fora do país.
- **Mesma vaga em duas páginas da lista** (a lista mudou entre os pedidos): aparece uma vez.
- **Configuração com a lista de portais vazia**: a ferramenta pede pelo menos um portal, como hoje.
- **Busca pelo terminal com `--fontes nerdin`**: funciona sem passar pelo painel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A Nerdin MUST ser um portal da busca nacional, ligado ou desligado pela pessoa, e MUST vir ligado em
  configuração nova ou sem a lista de portais, junto com Indeed e Gupy.
- **FR-002**: Uma configuração que já tem a lista de portais escolhida MUST continuar com essa lista; a Nerdin só
  entra nela quando a pessoa marca.
- **FR-003**: Com a Nerdin ligada, cada cargo da busca nacional MUST gerar uma consulta à busca pública da Nerdin, só
  quando o país da busca é o Brasil.
- **FR-004**: A ferramenta MUST ler as páginas da lista da mais nova para a mais antiga e MUST parar ao chegar ao
  número de vagas por cargo, a uma vaga mais antiga que a janela de tempo ou a um teto de páginas por cargo.
- **FR-005**: Cada vaga da Nerdin MUST trazer título, empresa, local (quando houver), data de publicação, modelo de
  trabalho (remoto, híbrido ou presencial, quando informado), tipo de contratação (CLT, PJ, freelancer, quando
  informado), salário só quando houver valor, e o link da vaga original; o identificador MUST vir do número da vaga
  na Nerdin e ser o mesmo da vaga adicionada pelo link.
- **FR-006**: A consulta remota MUST ficar só com as vagas Home Office; a consulta da cidade MUST ficar só com as
  vagas da cidade ou do estado da pessoa, nos modelos que ela marcou (híbrido, presencial); a consulta do país
  inteiro fica com todas, nos modelos marcados.
- **FR-007**: A vaga da Nerdin MUST passar pelos mesmos passos das outras: critérios de título, senioridade, tipo de
  emprego, empresas excluídas, Fora dos critérios com o motivo, junção com o mesmo anúncio em outro portal e análise
  com IA.
- **FR-008**: A descrição MUST ser lida da página da vaga só para as vagas que vão para o relatório, com um limite de
  leituras por busca; as que ficarem sem texto saem com descrição pendente.
- **FR-009**: Os pedidos à Nerdin MUST usar só a parte pública do site, sem login nem conta, senhas ou cookies da
  pessoa, MUST respeitar as regras do site para robôs e MUST ter pausa entre um pedido e outro.
- **FR-010**: Ao receber um sinal de bloqueio (recusa ou limite de consultas), a ferramenta MUST parar de consultar a
  Nerdin pelo resto da busca, sem nova tentativa, MUST mostrar o aviso no resumo da busca (página, terminal e chat) e
  MUST continuar com as outras fontes.
- **FR-011**: O painel "Filtros da busca" MUST mostrar a Nerdin na seção Portais, com uma linha sobre o que ela é (só
  vagas de TI, busca pública, consulta não oficial), e o contador de consultas MUST somar as dela.
- **FR-012**: O Adicionar Vaga MUST reconhecer links da Nerdin, com a etiqueta "Nerdin" e os dados da página.
- **FR-013**: O dashboard MUST mostrar a etiqueta "Nerdin" com cor própria e aceitar "Nerdin" no filtro e no
  formulário de portal.
- **FR-014**: A busca pelo terminal e pela skill MUST aceitar a Nerdin como as outras fontes.
- **FR-015**: AGENTS.md, o README (portais, padrão da chave de portais, termos e avisos), o README do dashboard e a
  skill buscar-vagas MUST citar o novo portal.
- **FR-016**: A busca na Nerdin MUST usar a janela de tempo que a pessoa marcou no painel, como os outros
  portais (máximo de 30 dias); o painel MUST oferecer também "Últimos 15 dias", útil para portais com poucas vagas
  novas por semana.

### Key Entities

- **Portal Nerdin**: fonte nacional de vagas de TI, ligada por padrão, com a linha de aviso do painel.
- **Consulta à Nerdin**: um cargo, a janela de tempo e, na busca na cidade, a cidade e o estado da pessoa.
- **Vaga da Nerdin**: uma vaga como as outras, identificada pelo número da vaga no portal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa configuração nova, a primeira busca já traz vagas da Nerdin, sem a pessoa mexer em nada.
- **SC-002**: 100% das vagas da Nerdin no relatório têm título, empresa, data e link que abrem a vaga certa no portal
  (conferido em amostra de 10 vagas).
- **SC-003**: Nenhuma vaga da Nerdin aparece duas vezes no relatório, nem quando já está no quadro.
- **SC-004**: Com a Nerdin desligada, a saída da busca é idêntica à de antes desta funcionalidade.
- **SC-005**: Num bloqueio simulado, há zero novas tentativas à Nerdin depois do primeiro sinal, o aviso aparece e
  100% das vagas das outras fontes chegam ao relatório.
- **SC-006**: Uma busca com 5 cargos faz no máximo 5 × o teto de páginas pedidos de lista, mais o limite de leituras
  de vaga, à Nerdin.
- **SC-007**: A pessoa desliga a Nerdin pelo painel em menos de 1 minuto, sem editar arquivos.

## Assumptions

- A busca pública da Nerdin segue disponível como foi vista em 18/10/2026: lista renderizada no site, 20 vagas por
  página, ordenada da mais nova para a mais antiga, e páginas de vaga com os dados estruturados da vaga. Quando isso
  mudar, a ferramenta avisa e segue com as outras fontes.
- A Nerdin é só de vagas do Brasil e só de TI; quem procura em outras áreas desliga o portal no painel.
- Ligada por padrão vale para configuração nova ou sem a lista de portais; quem já escolheu os portais liga a Nerdin
  no painel (a ferramenta não muda a escolha da pessoa).
- Teto de 5 páginas (100 vagas) por cargo e até 30 leituras de vaga por busca bastam; a janela de tempo costuma
  parar antes.
- Senioridade, tipo de contratação e modelo de trabalho não vão como filtro do site (a busca é por texto); os
  critérios de sempre decidem.
- Não há emenda da constituição: a Nerdin segue a regra já existente para portais sem API aberta.
- Verificação só no Windows, como nas specs anteriores.
