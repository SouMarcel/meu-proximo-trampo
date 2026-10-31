# Feature Specification: EY (careers.ey.com) na busca de vagas

**Feature Branch**: `039-ey` (a mesma worktree serve à spec 040, FullStack)

**Created**: 2026-10-30

**Status**: Aprovada em 2026-10-30; implementada na worktree (aguarda o teste da pessoa)

**Input**: User description: "adicionar novo portal de vagas. careers.ey.com e talent.fullstack.com". Depois da
pesquisa, a pessoa escolheu "Dois portais novos" (em vez de pôr os dois em Empresas acompanhadas), uma spec por portal.
Na aprovação (30/10/2026), escolheu a EY **ligada por padrão**.

## Contexto

O careers.ey.com é o site de vagas da EY, uma empresa só, no SAP SuccessFactors. Segue o roteiro `docs/novo-portal.md`
(research):
- sem API para candidatos; o RSS do SuccessFactors fica numa área bloqueada pelo robots.txt e não é usado;
- busca e páginas de vaga públicas, sem login, liberadas no robots.txt;
- os termos (Declaração Legal do ey.com) não citam robôs; só proíbem reproduzir o conteúdo sem permissão, como os do
  Vagas.com.

A lista não traz data nem modelo de trabalho: a data vem da página da vaga, junto com a descrição.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas da EY na busca de sempre (Priority: P1)

Com os mesmos cargos, local e janela, a busca traz as vagas da EY no país da pessoa, com a etiqueta "EY", para o
Relatório.

**Independent Test**: respostas simuladas; vagas com título, empresa "EY", local, data e link.

**Acceptance Scenarios**:

1. **Given** a EY ligada, **When** a pessoa busca, **Then** as vagas dela entram com a etiqueta "EY".
2. **Given** a EY desligada, **When** a pessoa busca, **Then** nenhum pedido vai a ela.
3. **Given** a janela de tempo, **When** a busca roda, **Then** vagas mais antigas que ela não entram, e a ferramenta
   para de abrir páginas de vaga ao chegar à primeira mais antiga.

### User Story 2 - Ligada por padrão (Priority: P1)

Configuração nova já busca na EY; quem já escolheu os portais liga no painel "Filtros da busca". A lista de portais já
escolhida não muda.

### User Story 3 - Pausa e bloqueio (Priority: P1)

Pausa sorteada de 3 a 7 s, `EY_PAUSA` no `.env`; no primeiro bloqueio, a EY sai do resto da busca, com aviso, sem
espera de horas (como a Nerdin).

### User Story 4 - Adicionar Vaga pelo link (Priority: P2)

O link de uma vaga da EY colado no Adicionar Vaga entra com o mesmo id da busca, com título, data, locais e descrição.

### Edge Cases

- **Vaga em vários locais** ("+15 more"): entra uma vez; os locais vêm da página da vaga.
- **"Banco de Talentos"** no título: a vaga entra, com "Banco de talentos" no `tipo`; a ferramenta não filtra.
- **"Vaga Exclusiva PCD"** no título: aparece no `tipo` ("Exclusiva para PCD"), como no Vagas.com.
- **Busca ampla do site**: ficam só as vagas cujo título bate com o cargo.
- **Mesma vaga em dois cargos ou duas páginas**: aparece uma vez.
- **Página da vaga sem data** legível: a vaga entra sem data.
- **Formato do site mudou** (nenhuma linha reconhecida numa página com resultados): aviso, e a busca segue com os
  outros portais.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A EY MUST ser um portal da busca nacional, **ligado por padrão** em configuração nova ou sem a lista de
  portais (decisão de 30/10/2026); a lista de portais escolhida pela pessoa não muda.
- **FR-002**: Cada cargo MUST ser buscado uma vez por busca, com a palavra do cargo e o país da pessoa, das mais
  recentes para as mais antigas, até 2 páginas (50 vagas), e servir às consultas remota, do país e da cidade.
- **FR-003**: Só entram as vagas cujo título bate com o cargo. A consulta da cidade fica com as que têm um local na
  cidade ou no estado da pessoa; a remota, com as que dizem remoto ou home office no título ou no local; a do país, com
  todas.
- **FR-004**: Data, locais e descrição MUST vir da página da vaga (microdados), só para as vagas que passaram no filtro
  do título, na ordem da lista, até 20 páginas de vaga por busca.
- **FR-005**: Pausa sorteada de 3 a 7 s entre os pedidos, ajustável por `EY_PAUSA` (3 a 60 s), com linha comentada no
  `.env.exemplo`.
- **FR-006**: No primeiro bloqueio (403, 429, 503 ou pedido de login): sem nova tentativa, a EY fica fora do resto da
  busca, as vagas já lidas seguem, e a busca avisa. Não há espera entre buscas.
- **FR-007**: O id MUST ser `ey-<número da vaga>`. O Adicionar Vaga MUST reconhecer links
  `careers.ey.com/<site>/job/…/<número>/`, com plataforma "EY" e o mesmo id.
- **FR-008**: "Banco de Talentos" e "Vaga Exclusiva PCD" no título MUST aparecer no `tipo` da vaga, sem filtro.
- **FR-009**: O RSS (`/services/`) e as áreas bloqueadas no robots.txt MUST ficar sem pedido.
- **FR-010**: Etiqueta "EY" no dashboard (front na `frontend-react`), README, `dash/README.md`, `dash/API.md`, AGENTS.md
  e skill buscar-vagas.

## Success Criteria *(mandatory)*

- **SC-001**: Numa configuração nova, a primeira busca já consulta a EY. Com a EY desligada pela pessoa, nenhum pedido
  vai a ela e a busca sai igual à de antes.
- **SC-002**: Num bloqueio simulado, zero novas tentativas e zero pedidos à EY no resto da busca.
- **SC-003**: Uma busca com 3 cargos faz no máximo 6 pedidos de lista e 20 de página de vaga à EY.
- **SC-004**: Um link de vaga da EY no Adicionar Vaga entra com título, data e descrição, com o mesmo id da busca.

## Assumptions

- **Ligada por padrão**: decisão da pessoa em 30/10/2026 (a proposta era desligada, por ser uma empresa só). Os termos
  não proíbem, e são poucos pedidos por busca (SC-003).
- **Pausa de 3 a 7 s e bloqueio sem espera**, como a Nerdin: são poucos pedidos por busca e um site de uma empresa só.
- **Só a área nacional**: o site é global; a EY na busca internacional fica para outra spec, se a pessoa quiser.
- **Formato do site** (visto em 30/10/2026): 25 vagas por página, `startrow` e `sortColumn=referencedate` na URL. Se
  mudar, a ferramenta avisa e segue com os outros portais.
- **Constituição**: sem emenda; os termos não proíbem a consulta automatizada (research R1).
- **Candidatura assistida**: fora do escopo; a candidatura da EY pede conta no próprio site.
- **Verificação**: só no Windows.
