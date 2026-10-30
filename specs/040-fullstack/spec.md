# Feature Specification: FullStack (talent.fullstack.com) na busca de vagas

**Feature Branch**: `039-ey` (mesma worktree da spec 039)

**Created**: 2026-10-30

**Status**: Aprovada em 2026-10-30; implementada na worktree (aguarda o teste da pessoa)

**Input**: User description: "adicionar novo portal de vagas. careers.ey.com e talent.fullstack.com". Decisões de
30/10/2026, depois da pesquisa: "Dois portais novos" e, como os termos proíbem robôs, "Desligada por padrão".

## Contexto

O talent.fullstack.com ("FullStack Connect") é o portal de vagas da FullStack, uma empresa só, com vagas remotas para a
América Latina. A página é um app em JavaScript que lê as vagas de uma API interna, sem login (research R3). Não há API
oficial para candidatos.

- **Os termos de uso proíbem acesso automatizado** ("any robot, spider, or other automatic device […] to access the
  Website for any purpose", research R1).
- Vale a constituição, princípio VI, "Termos contrários": a FullStack entra por **decisão explícita da pessoa** (esta
  spec), com os termos resumidos no painel, **desligada por padrão** e com as regras de sempre (pausa, parar no primeiro
  bloqueio, sem contornar).
- Sem API oficial, a ferramenta usa os mesmos pedidos públicos que a página faz ao abrir a lista de vagas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas da FullStack na busca de sempre (Priority: P1)

Com a FullStack ligada, a busca traz as vagas publicadas para o país da pessoa, com a etiqueta "FullStack", para o
Relatório.

**Independent Test**: respostas simuladas; vagas com título, empresa "FullStack", local, modelo remoto, data e link.

**Acceptance Scenarios**:

1. **Given** a FullStack ligada, **When** a pessoa busca, **Then** as vagas dela entram com a etiqueta "FullStack".
2. **Given** a mesma vaga publicada em várias cidades do país, **When** a busca roda, **Then** ela aparece uma vez.
3. **Given** a janela de tempo, **When** a busca roda, **Then** vagas mais antigas que ela não entram.

### User Story 2 - Desligada por padrão, com os termos à vista (Priority: P1)

A FullStack aparece no painel "Filtros da busca", desligada, com o resumo dos termos. A pessoa liga se quiser.

**Acceptance Scenarios**:

1. **Given** uma configuração nova ou sem a lista de portais, **When** a pessoa busca, **Then** nenhum pedido vai à
   FullStack.
2. **Given** o painel de filtros, **When** a pessoa vê a FullStack, **Then** lê que os termos proíbem acesso
   automatizado e que a consulta usa a API interna da página.

### User Story 3 - Pausa, bloqueio e espera (Priority: P1)

Pausa sorteada de 3 a 7 s, `FULLSTACK_PAUSA` no `.env`. No primeiro bloqueio, a ferramenta para, sem nova tentativa, e
fica 24 horas em espera; durante a espera, a busca pergunta antes de seguir sem ela (como o JobGether).

### User Story 4 - Descrição e Adicionar Vaga (Priority: P2)

Descrição só das vagas do relatório. O link de uma vaga da FullStack colado no Adicionar Vaga entra com o mesmo id da
busca, sem pedido durante a espera.

### Edge Cases

- **Vaga publicada em várias cidades e países**: uma vaga só, pelo identificador da vaga; o link aponta para a
  publicação no país da pessoa.
- **Título com o modelo e a região** ("… - Remote - Latin America"): o título fica inteiro; o modelo vem do campo
  próprio.
- **Vaga por tempo determinado** ("3 month-long", "6 month engagement"): entra; o tipo de contrato vem do campo próprio.
- **Vaga híbrida ou presencial fora do país da pessoa**: não entra (o filtro é o país).
- **País da pessoa sem vagas na FullStack**: nenhuma vaga, sem erro.
- **Formato da resposta mudou** (sem `data` ou sem `meta`): aviso, e a busca segue com os outros portais.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A FullStack MUST ser um portal da busca nacional, **desligado por padrão** (decisão de 30/10/2026); a
  lista de portais escolhida pela pessoa não muda.
- **FR-002**: Na área nacional, MUST atender as consultas remota e do país; a da cidade não faz pedido (as vagas são
  remotas).
- **FR-003**: A lista do país da pessoa MUST ser lida uma vez por busca e servir a todos os cargos, até 10 páginas (a
  API não ordena por data, research D3); a janela de tempo é filtrada pela data de cada vaga. Só entram as vagas cujo
  título bate com um cargo.
- **FR-004**: A mesma vaga publicada em várias cidades MUST aparecer uma vez.
- **FR-005**: Cada vaga MUST trazer o que a API informa: título, empresa "FullStack", local (país da pessoa, remoto),
  modelo, tipo de contrato, senioridade, data e habilidades. O e-mail do recrutador e os ids internos MUST ficar de
  fora.
- **FR-006**: A descrição MUST vir do detalhe da publicação, só das vagas do relatório, até 30 por busca.
- **FR-007**: Pausa sorteada de 3 a 7 s entre os pedidos, ajustável por `FULLSTACK_PAUSA` (3 a 60 s), com linha
  comentada no `.env.exemplo`.
- **FR-008**: No primeiro bloqueio (401, 403, 429 ou 503): sem nova tentativa, fora do resto da busca, 24 horas em
  espera, aviso com o fim da espera e nenhum pedido durante ela (busca, descrição e Adicionar Vaga). Na espera, a busca
  pergunta antes de seguir sem a FullStack (`vagas.py buscar` sai com código 5).
- **FR-009**: O id MUST ser `fullstack-<id da vaga>`. O Adicionar Vaga MUST reconhecer links
  `talent.fullstack.com/jobs/<id>`, com plataforma "FullStack" e o mesmo id.
- **FR-010**: O resumo dos termos no painel (`TERMOS`) e o README MUST dizer que os termos da FullStack proíbem acesso
  automatizado, que não há API oficial e que a consulta usa os pedidos públicos da página.
- **FR-011**: A candidatura assistida (spec 027) MUST seguir liberada em `talent.fullstack.com`, como hoje: decisão da
  pessoa em 30/10/2026, mesmo com os termos (é onde ela fez a prova real de 27/10/2026). Nada muda nos domínios
  bloqueados.
- **FR-012**: Etiqueta "FullStack" no dashboard (front na `frontend-react`: tipo, cor da etiqueta, domínio do link e
  texto do Adicionar Vaga), README, `dash/README.md`, `dash/API.md`, AGENTS.md e skill buscar-vagas.

### Key Entities

- **Espera da FullStack**: `.cache/fullstack-espera.json`, fora do Git, com o fim e o motivo.

## Success Criteria *(mandatory)*

- **SC-001**: Com a FullStack desligada (o padrão), nenhum pedido vai a ela e a busca sai igual à de antes.
- **SC-002**: Num bloqueio simulado, zero novas tentativas e zero pedidos durante a espera.
- **SC-003**: Uma busca faz no máximo 10 pedidos de lista e 30 de descrição à FullStack, com qualquer número de cargos.
- **SC-004**: Nenhum e-mail de recrutador fica gravado nas vagas.

## Assumptions

- **Desligada por padrão**: decisão da pessoa em 30/10/2026, pela regra de "Termos contrários".
- **Candidatura assistida liberada**: decisão da pessoa em 30/10/2026 (a proposta era bloquear, como no JobGether).
- **Pausa de 3 a 7 s e espera de 24 horas**: a pausa segue a de portal sem API oficial (mínimo 3 s); a espera segue a
  do JobGether, o outro portal com termos contrários.
- **Só a área nacional**: as vagas são "Remote – Latin America", publicadas por país; a busca internacional fica para
  outra spec, se a pessoa quiser.
- **Formato** (visto em 30/10/2026): páginas de 30, filtro por país pelo identificador. Se mudar, a ferramenta avisa e
  segue com os outros portais.
- **Constituição**: sem emenda; aplica a regra de "Termos contrários" que já existe.
- **Verificação**: só no Windows.
