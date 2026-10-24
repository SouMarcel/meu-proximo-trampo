# Feature Specification: Vagas.com na busca de vagas

**Feature Branch**: `026-infojobs` (mesma worktree da spec 026, que criou a pausa por portal e a espera comum)

**Created**: 2026-10-23

**Status**: Implementada (aguarda o teste da pessoa)

**Input**: User description: "seguir como o linkedin e adicionar tbm o portal vagas.com.br" (resposta à pergunta sobre
os termos do InfoJobs, 23/10/2026).

## Contexto

O Vagas.com é um portal brasileiro generalista, como o InfoJobs, e segue o roteiro `docs/novo-portal.md`:
- sem API oficial para candidatos;
- busca e páginas de vaga públicas, sem login;
- robots.txt sem bloqueio para a busca (`/vagas-de-<cargo>`) e para as vagas (`/vagas/v<id>/…`).

Os termos de uso proíbem "dispositivo, software ou outro recurso que venha a interferir nas atividades e operações"
do site e a reprodução do conteúdo sem autorização, mas não citam robôs (research). A ferramenta lê pouco, espaçado,
e guarda as vagas só no computador da pessoa, para uso dela.

As decisões não pedidas explicitamente seguem as do InfoJobs, que a pessoa tomou para o portal do mesmo tipo
(Assumptions).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas do Vagas.com na busca de sempre (Priority: P1)

Com os mesmos cargos, local e janela, a busca traz as vagas do Vagas.com, com a etiqueta do portal, para o Relatório.

**Independent Test**: respostas simuladas; vagas com título, empresa, local, data e link.

**Acceptance Scenarios**:

1. **Given** o Vagas.com ligado, **When** a pessoa busca, **Then** as vagas dele entram com a etiqueta "Vagas.com".
2. **Given** o Vagas.com desligado, **When** a pessoa busca, **Then** nenhum pedido vai a ele.
3. **Given** a janela de tempo, **When** a busca roda, **Then** a ferramenta para de pedir páginas ao chegar a vagas
   mais antigas que ela.

### User Story 2 - Ligado por padrão (Priority: P1)

Configuração nova já busca no Vagas.com; quem já escolheu os portais liga no painel.

### User Story 3 - Pausa, bloqueio e espera (Priority: P1)

Pausa sorteada de 3 a 7 s, `VAGASCOM_PAUSA` no `.env`; no primeiro bloqueio, sai da busca e fica 24 horas em espera,
com a mesma pergunta do LinkedIn antes de buscar sem ele.

### User Story 4 - Descrição e Adicionar Vaga (Priority: P2)

Descrição pela página da vaga só para as do relatório (até 30 por busca); o link colado no Adicionar Vaga entra com o
mesmo id da busca, sem pedido durante a espera.

### Edge Cases

- **Datas relativas**: "Hoje", "Ontem", "Há N dias" e "dd/mm/aaaa"; outra forma fica sem data (a vaga entra).
- **"100% Home Office"**: vaga remota; nas outras a lista não diz o modelo (fica para a análise com IA).
- **"Localização não informada"**: a vaga entra sem local.
- **Selo "Exclusivo para PCD"**: aparece no `tipo` ("Exclusiva para PCD"); a ferramenta não filtra.
- **Busca ampla do site**: ficam só as vagas cujo título bate com o cargo.
- **Mesma vaga em duas páginas**: aparece uma vez.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O Vagas.com MUST ser um portal da busca nacional, ligado por padrão em configuração nova ou sem a lista
  de portais; a lista escolhida pela pessoa não muda.
- **FR-002**: A lista de cada cargo MUST ser lida uma vez por busca, das mais recentes para as mais antigas, até 3
  páginas ou a janela de tempo, e servir às consultas remota, do país e da cidade.
- **FR-003**: A consulta remota fica com as vagas 100% home office; a da cidade, com as da cidade ou do estado da
  pessoa (não remotas); a do país, com todas.
- **FR-004**: Pausa sorteada de 3 a 7 s entre os pedidos, ajustável por `VAGASCOM_PAUSA` (3 a 60 s), com linha
  comentada no `.env.exemplo`.
- **FR-005**: No primeiro bloqueio (403, 429, 503 ou pedido de login): sem nova tentativa, fora do resto da busca, 24
  horas em espera, aviso com o fim da espera, e nenhum pedido durante ela (busca, descrição e Adicionar Vaga).
- **FR-006**: Descrição pelo `JobPosting` da página da vaga, só das vagas do relatório, até 30 por busca.
- **FR-007**: O Adicionar Vaga reconhece links `vagas.com.br/vagas/v<id>/…` com o id `vagascom-<id>`.
- **FR-008**: Etiqueta "Vagas.com" no dashboard (front na `frontend-react`), README, `dash/README.md`, `dash/API.md`,
  AGENTS.md e skill buscar-vagas.

## Success Criteria *(mandatory)*

- **SC-001**: Numa configuração nova, a primeira busca já consulta o Vagas.com.
- **SC-002**: Num bloqueio simulado, zero novas tentativas e zero pedidos durante a espera.
- **SC-003**: Com o Vagas.com desligado, nenhum pedido a ele.

## Assumptions

- **Decisões por analogia ao InfoJobs**: ligado por padrão, pausa sorteada de 3 a 7 s, espera de 24 horas. A pessoa
  pediu o portal "também", logo depois de decidir essas regras para o InfoJobs, e pode mudar no painel ou no `.env`.
- **Formato do site** (visto em 23/10/2026): 40 vagas por página, ordenação "mais recentes" e `pagina=N` na URL. Se
  mudar, a ferramenta avisa e segue com os outros portais.
- **Constituição**: sem emenda; vale a regra de portais sem API aberta.
- **Verificação**: só no Windows.
