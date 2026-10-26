# Feature Specification: Empresas acompanhadas na busca nacional

**Feature Branch**: `031-empresas-acompanhadas` (worktree `../meu-proximo-trampo-031`, saída da `master`)

**Created**: 2026-10-25

**Status**: Aprovada em 2026-10-25

**Input**: User description: "vamos agora configurar os portais jobgether e greenhouse e vamos usar o novo processo
criado". A pesquisa barrou o Greenhouse como portal, porque a busca entre empresas exige login (research R1). Em
25/10/2026, a pessoa escolheu melhorar "Empresas acompanhadas":
- a lista roda também na busca nacional e fica no painel principal;
- "acompanhar esta empresa" aparece no Adicionar Vaga e no detalhe da vaga;
- a busca para no primeiro bloqueio.

## Contexto

Empresas que contratam pelo Greenhouse, pelo Lever ou pelo Ashby publicam as vagas numa API pública, sem login. A
ferramenta já consulta essas APIs desde a spec 009, mas hoje há três limites:
- **Só na busca internacional**: com ela desligada, as empresas não são consultadas, mesmo quando têm vagas remotas
  abertas a quem mora no Brasil ("Remote, Brazil").
- **A lista fica escondida**: ela está no painel internacional, e a pessoa só descobre empresas colando o link de cada
  uma.
- **O bloqueio não para a busca**: um 429 ganha nova tentativa, e as outras empresas do mesmo sistema seguem
  recebendo pedidos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas das empresas acompanhadas na busca nacional (Priority: P1)

Com empresas na lista, a busca nacional traz as vagas delas no país da pessoa, mesmo com a busca internacional
desligada:
- as remotas abertas a quem mora no país;
- as presenciais e híbridas na cidade dela.

**Independent Test**: listas simuladas de Greenhouse, Lever e Ashby; vagas "Remote, Brazil" entram como nacionais e
"Remote, United States" não entram.

**Acceptance Scenarios**:

1. **Given** uma empresa acompanhada e a internacional desligada, **When** a pessoa busca, **Then** as vagas remotas
   cujo local cita o país dela (ou uma região que o inclui, como América Latina) entram como nacionais.
2. **Given** uma vaga "Remote, United States", **When** a busca nacional roda, **Then** ela fica de fora. Ela só entra
   pela busca internacional, quando ligada.
3. **Given** a busca da cidade (híbrido ou presencial), **When** a busca roda, **Then** entram as vagas não remotas na
   cidade ou no estado da pessoa.
4. **Given** a internacional também ligada, **When** a busca roda, **Then** a lista de cada empresa é baixada uma vez
   só e serve às duas áreas.

### User Story 2 - A lista no painel principal (Priority: P1)

A seção "Empresas que você acompanha" sai do painel internacional e vai para "Filtros da busca". A lista que a pessoa
já tem continua valendo, sem refazer nada.

**Acceptance Scenarios**:

1. **Given** um `config.json` antigo, com as empresas dentro de `internacional`, **When** a pessoa abre o painel,
   **Then** vê as mesmas empresas na seção nova.
2. **Given** a pessoa salva o painel, **When** a configuração é gravada, **Then** a lista fica no lugar novo e não se
   duplica.

### User Story 3 - Parar no primeiro bloqueio (Priority: P1)

Se o Greenhouse, o Lever ou o Ashby recusar ou limitar (403 ou 429), a busca não tenta de novo e não faz mais nenhum
pedido àquele sistema nessa busca. As empresas dos outros sistemas seguem.

**Acceptance Scenarios**:

1. **Given** três empresas no Greenhouse e uma no Lever, **When** a primeira do Greenhouse responde 429, **Then** as
   outras duas do Greenhouse não recebem pedido, a do Lever recebe, e o aviso sai uma vez.
2. **Given** uma empresa que saiu do sistema (404), **When** a busca roda, **Then** o aviso diz que a página de vagas
   dela não existe mais e sugere remover ou trocar o link. As outras seguem.

### User Story 4 - Acompanhar pelo Adicionar Vaga (Priority: P2)

Ao colar um link de vaga do Greenhouse, do Lever ou do Ashby, a vaga entra como hoje. A página também oferece
"Acompanhar <empresa>", ou mostra que a empresa já é acompanhada.

**Acceptance Scenarios**:

1. **Given** um link de vaga do Lever de uma empresa fora da lista, **When** a vaga é adicionada, **Then** aparece o
   botão "Acompanhar", e um clique põe a empresa na lista.
2. **Given** uma empresa já na lista, **When** a pessoa cola outra vaga dela, **Then** a página mostra que ela já é
   acompanhada.

### User Story 5 - Acompanhar pelo detalhe da vaga (Priority: P2)

No detalhe de uma vaga cujo link (ou link de candidatura) é de uma página de vaga do Greenhouse, do Lever ou do Ashby,
há o botão "Acompanhar empresa". Isso vale também para as vagas que vieram do Indeed ou do LinkedIn.

**Acceptance Scenarios**:

1. **Given** uma vaga do Indeed com candidatura em `job-boards.greenhouse.io/empresa/jobs/…`, **When** a pessoa abre
   o detalhe, **Then** vê "Acompanhar empresa", e um clique põe a empresa na lista.

### Edge Cases

- **Mesma empresa duas vezes** (mesmo sistema e nome, maiúsculas ou minúsculas): fica uma.
- **Lista cheia** (50 empresas): o botão avisa que a lista está cheia.
- **Local "Remote" sem país**: não entra na nacional. Em empresas dos EUA, costuma ser "remoto nos EUA".
- **"Anywhere", "Worldwide" ou "Global"**: entra na nacional, porque está aberta a quem mora no país.
- **"Remote, Brazil; Remote, Mexico"**: entra na nacional.
- **Cargo em português**: os títulos dessas vagas costumam vir em inglês. A busca nacional usa os cargos nacionais, e
  o painel sugere incluir o cargo em inglês.
- **Empresa sem vagas**: nenhum aviso.
- **Erro de rede ou 500 numa empresa**: aviso daquela empresa, e as outras seguem.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A fonte "Empresas acompanhadas" MUST atender a busca nacional:
  - nas consultas remota e do país, as vagas cujo local cita o país da pessoa, uma região que o inclui ou "Anywhere",
    "Worldwide" ou "Global";
  - na consulta da cidade, as vagas não remotas na cidade ou no estado da pessoa.
- **FR-002**: Na nacional, valem os cargos da busca nacional. Na internacional, tudo segue como hoje (consulta global,
  cargos em inglês).
- **FR-003**: A lista de cada empresa MUST ser baixada no máximo uma vez por busca, servindo às duas áreas.
- **FR-004**: A lista de empresas MUST ficar no `config.json` em `empresas`, no nível de cima, com no máximo 50.
  - A lista antiga em `internacional.empresas` é lida e passa para `empresas` ao salvar, sem duplicar.
  - A busca internacional usa a mesma lista.
- **FR-005**: A página MUST mostrar a seção "Empresas que você acompanha" no painel "Filtros da busca" e tirá-la do
  painel internacional (front na `frontend-react`).
- **FR-006**: No primeiro 403 ou 429 de um sistema (Greenhouse, Lever ou Ashby), numa busca ou numa leitura de link:
  - sem nova tentativa;
  - nenhum pedido a mais a esse sistema até o fim da busca;
  - um aviso só;
  - os outros sistemas seguem.

  Não há espera entre buscas.
- **FR-007**: Um 404 da lista de uma empresa MUST virar o aviso "a página de vagas de <empresa> no <sistema> não
  existe mais (a empresa pode ter mudado de sistema ou de nome); remova ou troque o link".
- **FR-008**: O Adicionar Vaga, com link de vaga do Greenhouse, do Lever ou do Ashby, MUST informar a empresa
  reconhecida e se ela já é acompanhada. A página oferece "Acompanhar".
- **FR-009**: O detalhe da vaga MUST oferecer "Acompanhar empresa" quando o link da vaga ou o de candidatura é de uma
  página de vaga desses sistemas, e mostrar "Acompanhando" quando a empresa já está na lista.
- **FR-010**: Acompanhar MUST gravar só com o clique da pessoa (princípio V), sem pedido ao sistema da empresa.
- **FR-011**: `specs/lista-de-desejos.md` MUST registrar o Greenhouse como portal barrado: a busca entre empresas exige
  login. A ideia da conta conectada fica registrada, com o motivo de não seguir.
- **FR-012**: Documentação atualizada:
  - README e `dash/README.md`;
  - `dash/API.md`: `empresas` na configuração, o pedido de acompanhar e a empresa na resposta do link;
  - skill buscar-vagas.

### Key Entities

- **Empresa acompanhada**: `{sistema: greenhouse|lever|ashby, id, nome, url}`, na lista `empresas` do `config.json`,
  com no máximo 50.

## Success Criteria *(mandatory)*

- **SC-001**: Com a busca internacional desligada, uma empresa acompanhada com uma vaga "Remote, Brazil" que bate com
  o cargo aparece na busca nacional.
- **SC-002**: Num bloqueio simulado de um sistema, zero novas tentativas e zero pedidos a mais a esse sistema.
- **SC-003**: Um `config.json` antigo, com as empresas no painel internacional, traz as mesmas empresas sem ação da
  pessoa.
- **SC-004**: Acompanhar uma empresa a partir de uma vaga leva um clique.

## Assumptions

- **Região que inclui o país**: a mesma tabela da elegibilidade (spec 009, `filtros.PAISES_DA_REGIAO`), por exemplo
  América Latina e Américas para o Brasil.
- **Sem espera entre buscas**: são APIs públicas e oficiais, uma por empresa. Parar até o fim da busca já evita
  insistir. Se um sistema bloquear com frequência, a espera fica para outra spec.
- **Cargos**: a nacional usa os cargos nacionais, como os outros portais.
- **Constituição**: sem emenda. Vale "preferir APIs públicas e oficiais", e a parada no bloqueio fica mais rígida do
  que hoje.
- **Verificação**: só no Windows.
