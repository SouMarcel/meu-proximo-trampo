# Feature Specification: JobGether na busca de vagas

**Feature Branch**: `030-jobgether` (worktree `../meu-proximo-trampo-030`, saída da `master`)

**Created**: 2026-10-25

**Status**: Implementada e testada pela pessoa (2026-10-25)

**Input**: User description: "vamos agora configurar os portais jobgether e greenhouse e vamos usar o novo processo
criado". Decisões de 25/10/2026, depois da pesquisa: o JobGether entra por decisão da pessoa, mesmo com os termos
(research R1), nas áreas nacional e internacional. O Greenhouse ficou barrado como portal, porque a busca exige
login; as melhorias de "Empresas acompanhadas" ficam numa spec própria (031).

## Contexto

O JobGether (jobgether.com) junta vagas remotas de empresas do mundo todo. Ele oferece uma API oficial para
assistentes de IA: sem chave, em JSON, com filtro de local (`brazil`, `anywhere`, países). Segue o roteiro
`docs/novo-portal.md`.

O que pesa contra:
- **Os termos de uso proíbem acesso automatizado** ("by automated means (bots, scrapers, crawlers)", seção 4.5) e
  guardar os dados sem autorização por escrito (seção 9). Isso vale mesmo com a API para assistentes de IA e com o
  `ai-input=yes` do robots.txt (research R1). A pessoa decidiu seguir assim mesmo: a ferramenta é local, só pede
  vagas no clique e guarda as vagas no computador dela, para uso dela.
- **A lista não traz a descrição**, e a página da vaga recusa a ferramenta (403). Imitar navegador fica fora (R2).
  As vagas entram sem descrição, com a nota provisória da spec 021.

Como os termos proíbem, o portal veio **desligado por padrão**, com os termos à vista no painel. **Em 2026-10-26, a
pessoa decidiu ligá-lo por padrão** também na ferramenta pública (configuração nova); quem não concordar desliga no
painel, e quem já escolheu os portais continua com a lista que tinha.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas remotas abertas ao Brasil na busca nacional (Priority: P1)

Com o JobGether ligado, a busca de sempre traz as vagas remotas que aceitam quem mora no país da pessoa (Brasil,
América do Sul, América Latina ou "Anywhere"), com a etiqueta "JobGether", para o Relatório.

**Independent Test**: respostas simuladas da API; vagas com título, empresa, local aceito, data, link e salário quando
informado.

**Acceptance Scenarios**:

1. **Given** o JobGether ligado e a busca remota no Brasil, **When** a pessoa busca, **Then** a ferramenta consulta a
   API com o local do país e as vagas entram com a etiqueta "JobGether".
2. **Given** a janela de tempo, **When** a busca roda, **Then** a ferramenta para de pedir páginas ao chegar a vagas
   mais antigas que ela.
3. **Given** um cargo que não bate com o título (busca ampla da API), **When** a busca roda, **Then** a vaga fica de
   fora.

### User Story 2 - Na busca internacional, por país e no mundo todo (Priority: P1)

Com a busca internacional ligada, o JobGether roda em cada país escolhido e na consulta "mundo todo" (vagas
"Anywhere"), com os cargos da área internacional.

**Acceptance Scenarios**:

1. **Given** a internacional ligada com Portugal, **When** a pessoa busca, **Then** há uma consulta com o local de
   Portugal.
2. **Given** a consulta global, **When** a busca roda, **Then** o JobGether pede as vagas "Anywhere".
3. **Given** um país que o JobGether não reconhece (400), **When** a busca roda, **Then** a ferramenta avisa e segue
   com os outros.

### User Story 3 - Desligado por padrão, com os termos à vista (Priority: P1)

O JobGether aparece na lista de portais do painel "Filtros da busca", desligado, com o resumo dos termos. A pessoa
liga se quiser.

**Acceptance Scenarios**:

1. **Given** uma configuração nova, **When** a primeira busca roda, **Then** nenhum pedido vai ao JobGether.
2. **Given** o painel de filtros, **When** a pessoa vê o JobGether, **Then** lê que os termos proíbem acesso
   automatizado e que a ferramenta usa a API para assistentes.

### User Story 4 - Pausa, bloqueio e espera (Priority: P1)

Pausa de 2 s entre os pedidos (o `Crawl-delay` do site), ajustável por `JOBGETHER_PAUSA` no `.env`. No primeiro
bloqueio, a ferramenta para, sem nova tentativa, e fica 24 horas em espera. Durante a espera, a busca pergunta antes
de seguir sem ele, como faz com o LinkedIn.

### User Story 5 - Sem descrição e Adicionar Vaga (Priority: P2)

As vagas entram sem descrição, e a nota da IA fica marcada como provisória (spec 021). A pessoa usa "Forçar
verificar" ou cola o texto. Um link `jobgether.com/offer/…` colado no Adicionar Vaga é reconhecido com o mesmo id da
busca, sem pedido à página.

### Edge Cases

- **Vaga republicada**: volta com `id` e data novos, mas o id da URL é o mesmo e a vaga não reaparece no dashboard.
  Uma vaga republicada que ainda não está lá entra com a data da republicação.
- **Mesma vaga com ids diferentes** (ou empresa agregadora, como "Indeed.com"): entram as duas, como hoje com vagas
  repetidas entre portais.
- **Cargos em português**: a API não acha nada (as vagas estão em inglês). A consulta volta vazia, sem erro. O README
  sugere incluir o cargo em inglês.
- **"Latin America" com restrição de fuso dos EUA**: o local vai para `restricao_local`, e a análise de elegibilidade
  (spec 009) decide.
- **Salário sem período** ("6000-10200 USD"): mostrado como o portal informa, com a moeda e sem "por ano".
- **Título com caractere quebrado**: fica como veio.
- **504 (timeout) ou 500**: vira erro só daquela consulta, sem nova tentativa. Não é bloqueio.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O JobGether MUST ser um portal da lista do painel "Filtros da busca", **ligado por padrão** (decisão de
  2026-10-26; antes, desligado). A lista de
  portais que a pessoa já escolheu não muda.
- **FR-002**: Na área nacional, MUST atender as consultas remota e do país, com o local do país da pessoa (`brazil`
  para o Brasil). A consulta da cidade fica de fora (o JobGether não filtra por cidade). Na do país, as híbridas
  entram quando a pessoa aceita híbrido.
- **FR-003**: Na área internacional, MUST atender as consultas por país (o slug do país) e a global (`anywhere`). As de
  mudança (presencial ou híbrido no exterior) ficam de fora.
- **FR-004**: Cada consulta MUST usar a API oficial por POST (`/api/v1/jobs`, sem query string, como pede o
  robots.txt), com o cargo sem aspas, ordenada por data e com 25 por página. A busca vai até 3 páginas ou até a janela
  de tempo.
- **FR-005**: Pausa de 2 s entre os pedidos, ajustável por `JOBGETHER_PAUSA` (2 a 60 s), com linha comentada no
  `.env.exemplo`.
- **FR-006**: No primeiro 403 ou 429: sem nova tentativa, fora do resto da busca, 24 horas em espera, aviso com o fim
  da espera e nenhum pedido durante ela. Um 400 de país desconhecido vira aviso daquele país; 500 e 504, erro daquela
  consulta.
- **FR-007**: Cada vaga MUST trazer o que a API informa:
  - título, empresa e data (`postedAt`);
  - local "Remoto (<locais aceitos>)" e `restricao_local` com os locais;
  - modelo remoto, ou híbrido quando a API diz;
  - salário e moeda (`salaryRange`), quando houver;
  - tipo de contratação (`contractType`, em `tipo` e `tipo_emprego`);
  - o link da vaga no JobGether.
  A descrição fica vazia, sem pedido à página.
- **FR-008**: O id MUST ser `jobgether-<id da URL>`. Sem id na URL, vale o `id` da API.
- **FR-009**: O Adicionar Vaga MUST reconhecer links `jobgether.com/offer/<id>-…`, com plataforma "JobGether" e o mesmo
  id da busca, sem pedir a página. O formulário abre com o que deu para ler, e a pessoa completa cargo, empresa e
  descrição.
- **FR-010**: A candidatura assistida (spec 027) MUST tratar `jobgether.com` como domínio bloqueado, pelos termos 4.5.
  A candidatura no sistema da empresa segue as regras de cada domínio.
- **FR-011**: O resumo dos termos no painel (`TERMOS`) e o README MUST dizer que os termos do JobGether proíbem acesso
  automatizado e que a ferramenta usa a API para assistentes, por decisão registrada nesta spec.
- **FR-012**: A constituição MUST ganhar uma emenda no princípio VI, que hoje manda "seguir os termos de cada fonte".
  A emenda diz que um portal cujos termos proíbem acesso automatizado só entra:
  - por decisão explícita da pessoa, registrada na spec;
  - pela API oficial, quando houver;
  - com os termos à vista no painel;
  - desligado por padrão, salvo outra decisão da pessoa registrada na spec. Isso preserva InfoJobs e Nerdin, ligados
    por decisão das suas specs (ajuste aprovado no plano, 25/10/2026).
  Liberado: JobGether, ligado por padrão por decisão de 2026-10-26.
- **FR-013**: Etiqueta "JobGether" no dashboard (front na `frontend-react`: tipo, cor da etiqueta, domínio do link e
  texto do Adicionar Vaga). Também atualizar `dash/banco.py` (`PLATAFORMAS`), `dash/API.md` (`plataforma` e `fontes`),
  README, `dash/README.md`, AGENTS.md e a skill buscar-vagas.

### Key Entities

- **Vaga do JobGether**: vaga no formato comum (`fontes/__init__.py`) com id `jobgether-<id da URL>`, sem descrição e
  com `restricao_local`.
- **Espera do JobGether**: `.cache/jobgether-espera.json`, fora do Git, com o fim e o motivo.

## Success Criteria *(mandatory)*

- **SC-001**: Com o JobGether desligado pela pessoa, nenhum pedido vai a ele. Numa configuração nova, ele vem ligado
  (decisão de 2026-10-26).
- **SC-002**: Num bloqueio simulado, zero novas tentativas e zero pedidos durante a espera.
- **SC-003**: Uma vaga republicada (outro `id` da API, mesmo id da URL) não volta ao Relatório.
- **SC-004**: Numa busca real pequena no Windows, com cargo em inglês e o Brasil, vagas entram com a etiqueta
  "JobGether" e o link abre a vaga no site.

## Assumptions

- **Área**: nacional e internacional (decisão da pessoa). No Brasil, a API devolve remotas abertas a quem mora aqui:
  25 vagas de "project manager" em 14 dias (research R3).
- **Desligado por padrão**: proposta aceita ao abrir esta spec, porque os termos proíbem e a decisão vale para quem
  usa a ferramenta pública.
- **Pausa de 2 s, até 3 páginas por consulta e espera de 24 horas**:
  - a pausa segue o `Crawl-delay` do robots.txt;
  - o mínimo de 2 s vale porque é API (o roteiro pede 3 s para portal sem API);
  - a espera segue a do InfoJobs e do Vagas.com;
  - o limite da API é de 60 pedidos por minuto.
- **Cargos**: cada área usa os seus, como os outros portais. Os títulos do JobGether vêm em inglês.
- **Slugs de país**: o do Brasil (`brazil`) foi visto. Os dos outros países saem do nome em inglês, e um slug que a API
  recusar vira aviso (FR-006).
- **Verificação**: só no Windows.
