# Feature Specification: Análise de perfil contínua

**Feature Branch**: `012-analise-perfil` (pasta da spec; o trabalho acontece na `master` por worktree, conforme a
constituição)

**Created**: 2026-10-10

**Status**: Draft

**Input**: User description: "Fase 10 do roteiro: análise de perfil contínua. Três análises, na página (Meu perfil,
'Análises do perfil') e pela skill analisar-perfil no chat, só no clique ou no pedido. (1) Carreiras e cargos-alvo:
de 5 a 10 cargos (lateral, degrau, vizinho), com evidência do perfil, lacuna e termos em português e inglês; levar
os escolhidos para os filtros, só com confirmação. (2) Lacunas das vagas: ranking das lacunas mais frequentes nas
vagas analisadas (lacunas da IA e requisitos que o perfil não mostra), com peso maior nas de maior aderência e nas
seguidas, em níveis (crítica, alta, média), mínimo de 5 vagas; 'vagas que você seguiu' e 'todas'; plano de estudo
só se pedir. (3) Prontidão internacional: inglês, fuso, contratação, currículo e LinkedIn em inglês, o que está
pronto e o que falta. Sem IA, o que dá para calcular; com IA, cargos-alvo e plano de estudo. Só fatos do perfil;
nada gravado sem confirmação. Análises salvas com a data. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - O que as vagas pedem e eu não mostro (Priority: P1)

Em Meu perfil, na área "Análises do perfil", a pessoa abre "Lacunas das vagas". A ferramenta junta o que as vagas
já analisadas dizem que falta no perfil (as lacunas da análise e os requisitos do anúncio que o perfil não mostra) e
mostra um ranking: cada lacuna com o número de vagas em que aparece, exemplos de vagas, e um nível (crítica, alta,
média). Vagas com aderência maior e vagas que a pessoa seguiu pesam mais. Duas visões: "vagas que você seguiu" e
"todas". Com menos de 5 vagas analisadas, a ferramenta diz quantas faltam em vez de mostrar um ranking fraco. Se a
pessoa pedir, a IA escreve um plano de estudo curto para as lacunas do topo.

**Why this priority**: é a análise que transforma as vagas já vistas em direção prática (o que estudar, o que
destacar), e funciona sem IA.

**Independent Test**: com 8 vagas fictícias analisadas, abrir "Lacunas das vagas" e ver o ranking com níveis,
contagens e exemplos; trocar para "vagas que você seguiu"; com 3 vagas, ver o aviso de que faltam vagas.

**Acceptance Scenarios**:

1. **Given** 5 ou mais vagas analisadas, **When** a pessoa abre "Lacunas das vagas", **Then** vê as lacunas em
   ordem de peso, cada uma com o nível, o número de vagas e até 3 vagas de exemplo (com link para abrir).
2. **Given** a mesma lacuna escrita de jeitos diferentes nas vagas ("Power BI avançado", "experiência com Power BI"),
   **When** o ranking é montado, **Then** elas aparecem juntas.
3. **Given** menos de 5 vagas analisadas na visão escolhida, **When** a pessoa abre a análise, **Then** vê quantas
   vagas analisadas há e quantas faltam, sem ranking.
4. **Given** o ranking, **When** a pessoa pede o plano de estudo, **Then** a IA escreve um plano curto para as
   lacunas do topo, sem inventar experiência; sem IA, o botão explica como escolher uma.
5. **Given** a análise feita, **When** a pessoa volta outro dia, **Then** vê a última análise com a data e pode
   refazer.

---

### User Story 2 - Que outros cargos eu posso buscar (Priority: P1)

Em "Carreiras e cargos-alvo", a pessoa pede a análise e a IA lê o perfil e propõe de 5 a 10 cargos possíveis, cada
um como lateral (o mesmo nível em outra área ou tipo de empresa), degrau (o próximo nível) ou vizinho (área
próxima), com a evidência do perfil que sustenta, a lacuna principal e os termos de busca em português e em inglês.
A pessoa marca os que quer e leva para os filtros da busca: a ferramenta mostra o que muda e só grava com a
confirmação.

**Why this priority**: a pessoa costuma buscar sempre os mesmos títulos; ver cargos sustentados pelo próprio perfil
abre mais vagas boas.

**Independent Test**: com um perfil fictício e uma IA de teste, pedir a análise, ver os cargos com tipo, evidência,
lacuna e termos, marcar dois e confirmar a mudança nos filtros.

**Acceptance Scenarios**:

1. **Given** um perfil e uma IA configurada, **When** a pessoa pede os cargos-alvo, **Then** vê de 5 a 10 cargos,
   cada um com tipo (lateral, degrau, vizinho), evidência citada do perfil, lacuna e termos PT/EN.
2. **Given** um cargo cuja evidência não está no perfil, **When** a análise volta da IA, **Then** esse cargo é
   descartado ou marcado para conferir.
3. **Given** cargos marcados, **When** a pessoa escolhe "levar para os filtros", **Then** vê os cargos que entram
   (e os que já estavam), e nada muda até confirmar; os outros filtros ficam como estão.
4. **Given** nenhuma IA, **When** a pessoa abre a análise, **Then** vê a explicação e a opção de pedir pelo chat.

---

### User Story 3 - Estou pronto para vagas de fora? (Priority: P2)

Em "Prontidão internacional", a ferramenta mostra uma lista do que já está pronto e do que falta para se candidatar
no exterior: nível de inglês (pelo perfil), fuso e horas em comum aceitas, formas de contratação aceitas, passaporte
e autorização de trabalho (pelos filtros internacionais), currículo em inglês (o seu currículo em inglês marcado ou
um gerado) e LinkedIn em inglês (a pessoa marca). Cada item que falta tem o caminho para resolver (abrir o painel,
gerar o currículo em inglês, completar o perfil).

**Why this priority**: junta num lugar o que hoje está espalhado entre perfil, filtros e currículos; não depende de
IA.

**Independent Test**: com um perfil com "Inglês — avançado", currículo em inglês marcado e sem fuso nos filtros, ver
inglês e currículo como prontos e fuso como "falta", com o botão para abrir o painel.

**Acceptance Scenarios**:

1. **Given** o perfil e os filtros, **When** a pessoa abre a prontidão, **Then** vê cada item como pronto, falta ou
   não informado, com de onde veio a informação.
2. **Given** um item que falta, **When** a pessoa clica no caminho, **Then** abre o lugar certo (painel
   internacional, currículo, Meu perfil).
3. **Given** o item LinkedIn em inglês, **When** a pessoa marca como pronto, **Then** a marcação fica salva.

---

### User Story 4 - As mesmas análises pelo chat (Priority: P3)

Pela skill de perfil no chat, a pessoa pede qualquer das três análises e recebe o mesmo resultado, com as mesmas
regras (mínimo de vagas, só fatos do perfil, mudança nos filtros só com o OK).

**Why this priority**: a ferramenta vale igual pela página e pelo chat.

**Independent Test**: pelo chat, pedir as lacunas das vagas e ver o mesmo ranking da página.

**Acceptance Scenarios**:

1. **Given** vagas analisadas, **When** a pessoa pede as lacunas pelo chat, **Then** recebe o ranking igual ao da
   página.

---

### Edge Cases

- Vagas sem análise (sem IA): entram só pelos requisitos do anúncio que o perfil não mostra.
- Vaga fora dos critérios ou marcada "não seguir": entra em "todas", com peso menor; nunca em "vagas que você seguiu".
- Lacuna que já foi resolvida no perfil (a pessoa acrescentou a ferramenta depois): sai do ranking ao refazer.
- Perfil vazio: as análises explicam que precisam do perfil e apontam Meu perfil.
- Resposta da IA com cargo repetido ou fora do formato: o cargo é descartado; se sobrarem menos de 5, a análise
  avisa.
- Texto das vagas e do perfil é dado, nunca instrução para a IA.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Meu perfil MUST ter a área "Análises do perfil" com as três análises; cada uma só roda no clique.
- **FR-002**: "Lacunas das vagas" MUST juntar as lacunas da análise de cada vaga e os requisitos do anúncio que o
  perfil não mostra, agrupar o que é a mesma lacuna escrita de jeitos diferentes e ordenar por peso.
- **FR-003**: O peso MUST crescer com a aderência da vaga e ser maior nas vagas que a pessoa seguiu; vaga fora dos
  critérios ou "não seguir" pesa menos.
- **FR-004**: Cada lacuna MUST ter um nível (crítica, alta, média) conforme a parte do peso total em que aparece,
  o número de vagas e até 3 vagas de exemplo.
- **FR-005**: O ranking MUST exigir pelo menos 5 vagas analisadas na visão escolhida; abaixo disso, mostra quantas
  faltam.
- **FR-006**: MUST haver as visões "vagas que você seguiu" e "todas".
- **FR-007**: O plano de estudo MUST ser gerado só a pedido, com a IA escolhida, para as lacunas do topo, sem
  afirmar experiência que o perfil não tem.
- **FR-008**: "Carreiras e cargos-alvo" MUST propor de 5 a 10 cargos com tipo (lateral, degrau, vizinho), evidência
  do perfil, lacuna e termos PT/EN; cargo sem evidência no perfil é descartado ou marcado para conferir.
- **FR-009**: Levar cargos para os filtros MUST mostrar o que muda e gravar só com confirmação, mantendo o resto
  dos filtros.
- **FR-010**: "Prontidão internacional" MUST mostrar inglês, fuso, contratação, passaporte e autorização, currículo
  em inglês e LinkedIn em inglês como pronto, falta ou não informado, com a origem e o caminho para resolver.
- **FR-011**: A pessoa MUST poder marcar itens que a ferramenta não consegue saber (LinkedIn em inglês), e a
  marcação fica salva.
- **FR-012**: Cada análise MUST ficar salva com a data, para rever e refazer; fica fora do Git, neste computador.
- **FR-013**: Sem IA, MUST funcionar o ranking de lacunas e a prontidão; cargos-alvo e plano de estudo explicam que
  precisam de IA (ou do chat).
- **FR-014**: A skill de perfil no chat MUST oferecer as três análises com as mesmas regras.
- **FR-015**: Textos MUST estar em português do Brasil.

### Key Entities

- **Lacuna**: texto representativo, variações agrupadas, peso, nível, número de vagas, vagas de exemplo, visão.
- **Cargo-alvo**: título PT e EN, tipo (lateral, degrau, vizinho), evidência (trecho do perfil), lacuna principal.
- **Item de prontidão**: nome, situação (pronto, falta, não informado), origem, caminho para resolver, marcação da
  pessoa.
- **Análise salva**: tipo, data, resultado, IA usada (quando houver).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Num conjunto de teste de vagas com lacunas conhecidas, a lacuna mais frequente nas vagas de maior
  aderência fica em primeiro lugar, e variações da mesma lacuna aparecem juntas em 100% dos casos do conjunto.
- **SC-002**: Com menos de 5 vagas analisadas, nenhum ranking é mostrado (100% dos casos de teste).
- **SC-003**: 100% dos cargos-alvo mostrados têm evidência que aparece no perfil; os de uma IA de teste que inventa
  evidência são descartados ou marcados.
- **SC-004**: Nenhum filtro muda sem a confirmação da pessoa.
- **SC-005**: A prontidão mostra a situação certa em 100% dos itens de um perfil e filtros de teste.

## Assumptions

- Os níveis seguem a parte do peso total em que a lacuna aparece: crítica a partir de metade, alta de um quarto a
  metade, média de 10% a um quarto; abaixo de 10% não entra.
- O agrupamento de lacunas sem IA usa as palavras significativas (ferramentas, certificações, idiomas, anos de
  experiência), como a conferência de requisitos do currículo.
- As análises ficam salvas na pasta de dados da ferramenta, fora do Git.
- Verificação no Windows, como nas fases anteriores.
