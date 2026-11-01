# Feature Specification: Empresas acompanhadas em qualquer página de vagas

**Feature Branch**: `042-empresas-sites` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-01

**Status**: Concluída em 2026-11-01 (validada pela pessoa na branch pessoal)

**Input**: User description: "a EY é uma empresa e essa é a área dela para vagas (careers.ey.com/ey/search); em Filtros
da busca temos Empresas que acompanho e a EY deveria estar lá. Assim como a Varejista (exemplo) tem o seu próprio
(carreiras.varejista.com.br/jobs) e a consultoria (consultoria.com.br/carreira/#vagas). Como já tem um campo para
adicionar mais nesse local de filtros, podemos deixar esse campo para a pessoa adicionar a empresa que deseja
acompanhar." (01/11/2026; as duas empresas citadas pela pessoa aparecem aqui como exemplos genéricos, varejista
e consultoria). Decisões da mesma data em Clarifications.

## Contexto

- **Empresas acompanhadas** (spec 031) é a lista, no painel Filtros da busca, das empresas cujas vagas a pessoa quer
  ver em toda busca, nas duas áreas:
  - na nacional, as remotas abertas ao país dela e as presenciais ou híbridas na cidade;
  - na internacional, a consulta global.

  Hoje o campo só aceita a página de vagas de empresas que usam o Greenhouse, o Lever ou o Ashby.
- A **EY** entrou como portal (spec 039), ligada por padrão. Mas o site `careers.ey.com` é o site de vagas de uma
  empresa só: o lugar dela é a lista de empresas acompanhadas.
- **Pesquisa de 01/11/2026**, com um pedido a cada site:

  | Empresa | O que há por trás | O que a ferramenta consegue ler |
  |---|---|---|
  | EY | o sistema de vagas da SAP (SuccessFactors) | a busca do site, como hoje |
  | Varejista (exemplo) | o Teamtailor, um sistema de vagas comum entre empresas | a lista pública de vagas que o próprio site oferece (feed RSS) |
  | Consultoria de TI (exemplo) | uma página feita à mão no site da empresa | só o texto: cargo, modelo de trabalho e requisitos, sem link nem data por vaga, candidatura por e-mail |

- Na busca de 01/11, a EY deu o aviso "não consegui ler as vagas da EY" na consulta "agilista". A causa é conferida no
  plano.

## Clarifications

### Session 2026-11-01

- Q: Página de vagas sem sistema por trás (como a da consultoria): como ler? → A: A IA que a pessoa já usa lê o texto da
  página e separa as vagas: cargo, modelo, local e requisitos. O texto passa pelo filtro de integridade (spec 034).
  - Precisa da IA ligada.
  - A data da vaga passa a ser o dia em que a ferramenta a viu pela primeira vez.
- Q: A EY é hoje um portal ligado por padrão. Ao virar empresa acompanhada, quem recebe? → A: Quem já tem a EY ligada
  nos portais passa a tê-la na lista automaticamente. Quem instala agora começa sem ela e adiciona se quiser.
  - A EY sai da lista de portais.
  - As vagas mantêm o mesmo identificador, sem duplicar.
- Q: Escopo do campo? → A: A página de vagas de qualquer empresa. A ferramenta reconhece os sistemas que conhece e lê o
  resto como página própria, pela IA.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acompanhar uma empresa pelo link da página de vagas (Priority: P1)

Em Filtros da busca → Empresas que você acompanha, a pessoa cola o link da página de vagas de uma empresa. A ferramenta
reconhece a empresa e o sistema por trás da página e põe a empresa na lista, com o nome e o tipo de leitura.

**Independent Test**: com páginas simuladas: o link da varejista entra como "Teamtailor", o da EY como "site de vagas
da EY", o da consultoria como "página própria (lida pela IA)", e o de um portal de vagas é recusado com a dica de ligá-lo em
Portais.

**Acceptance Scenarios**:

1. **Given** o link de uma página de vagas do Teamtailor (ex.: uma varejista), **When** a pessoa adiciona, **Then** a
   empresa entra na lista com o nome dela e "Teamtailor".
2. **Given** o link do site de vagas da EY, **When** a pessoa adiciona, **Then** a EY entra na lista.
3. **Given** o link de uma página sem sistema conhecido (ex.: uma consultoria de TI), **When** a pessoa adiciona, **Then** a empresa
   entra como "página própria, lida pela IA". Se a IA estiver desligada, a área avisa que a página só é lida com a IA
   ligada.
4. **Given** o link de um portal de vagas (LinkedIn, Indeed, Gupy, InfoJobs, Vagas.com, Nerdin e afins), **When** a
   pessoa tenta adicionar, **Then** a ferramenta recusa e explica que portais se ligam em Portais.
5. **Given** a mesma empresa já na lista, **When** a pessoa cola o link de novo, **Then** ela não se repete.

---

### User Story 2 - Vagas das empresas Teamtailor e EY na busca (Priority: P1)

A cada busca, as vagas das empresas acompanhadas no Teamtailor e da EY entram como as das outras empresas: nas duas
áreas, com os filtros de sempre, no relatório e esperando nota.

**Independent Test**: com uma lista simulada do Teamtailor, vagas que batem com o cargo, na cidade da pessoa ou remotas
abertas ao país, aparecem com título, empresa, local, data e link; as outras ficam de fora.

**Acceptance Scenarios**:

1. **Given** uma empresa do Teamtailor na lista, **When** a busca roda, **Then** a lista de vagas dela é lida uma vez e
   serve a todos os cargos e às duas áreas.
2. **Given** a EY na lista, **When** a busca roda, **Then** as vagas da EY chegam como chegam hoje pelo portal: os mesmos
   campos e o mesmo identificador.
3. **Given** uma vaga presencial em outra cidade, **When** a busca nacional roda, **Then** ela fica de fora, como nas
   outras empresas acompanhadas.

---

### User Story 3 - A EY muda de lugar sem perder nada (Priority: P1)

Quem já usa a ferramenta com a EY ligada nos portais encontra a EY em Empresas acompanhadas, e as vagas da EY que já
estão no dashboard não voltam como novas.

**Independent Test**: um config com "ey" nos portais passa a ter a EY na lista de empresas e não tem mais "ey" nos
portais. Uma vaga da EY já gravada não reaparece. Um config novo não tem a EY.

**Acceptance Scenarios**:

1. **Given** um config antigo com a EY ligada, **When** a pessoa abre o painel ou busca, **Then** a EY está na lista de
   empresas e não aparece mais na lista de portais.
2. **Given** um config antigo com a EY desligada, **When** a pessoa abre o painel, **Then** a EY não entra na lista.
3. **Given** vagas da EY já no dashboard, **When** a busca roda, **Then** elas não voltam como novas.
4. **Given** uma instalação nova, **When** a pessoa abre o painel, **Then** a EY não está nem nos portais nem na lista
   de empresas, e pode ser adicionada pelo link.

---

### User Story 4 - Página própria lida pela IA (Priority: P2)

Algumas empresas publicam as vagas numa página feita à mão, sem sistema por trás. Com a IA ligada, a ferramenta lê o
texto dessa página e separa as vagas, para que entrem no relatório como as outras.

**Independent Test**: com uma página simulada no formato da consultoria e uma IA simulada:
- cada bloco de vaga vira uma vaga com cargo, modelo, local e requisitos;
- nenhum campo é preenchido sem estar no texto;
- a mesma página sem mudança, numa segunda busca, não chama a IA;
- sem IA, a empresa fica de fora com um aviso.

**Acceptance Scenarios**:

1. **Given** a consultoria na lista e a IA ligada, **When** a busca roda, **Then** as vagas da página que batem com os cargos
   entram no relatório. Cada uma leva:
   - o cargo, o modelo de trabalho e o local que a página informa;
   - os requisitos como descrição;
   - o link da página da empresa;
   - o e-mail de candidatura, quando a página traz.
2. **Given** uma informação que a página não traz (ex.: salário, data), **When** a IA separa a vaga, **Then** o campo
   fica vazio. A data da vaga é o dia em que a ferramenta a viu pela primeira vez.
3. **Given** a página sem mudança desde a última leitura, **When** a busca roda, **Then** a IA não é chamada de novo, e
   as vagas já vistas não voltam como novas.
4. **Given** a IA desligada, **When** a busca roda, **Then** a empresa fica de fora com o aviso "ligue a IA para ler a
   página de vagas de <empresa>", e o resto da busca segue.
5. **Given** um texto escondido na página que mira a IA, **When** a página é lida, **Then** o filtro de integridade age
   antes da IA, e a vaga com o achado leva o alerta.

---

### User Story 5 - Parar no primeiro problema, empresa por empresa (Priority: P2)

Cada empresa é um site diferente. Um site que recusa, sai do ar ou muda não atrapalha os outros.

**Acceptance Scenarios**:

1. **Given** um site que recusa ou limita as consultas, **When** isso aparece, **Then** a ferramenta para naquele site,
   sem nova tentativa, até o fim da busca, com um aviso. As outras empresas seguem.
2. **Given** uma página de vagas que não existe mais, **When** a busca roda, **Then** o aviso diz que a página saiu do
   ar e sugere remover ou trocar o link.
3. **Given** uma página própria em que a IA não acha nenhuma vaga, **When** a busca roda, **Then** o aviso diz que nenhuma
   vaga foi encontrada na página, sem erro.

---

### Edge Cases

- **Link de uma vaga em vez da página de vagas** (ex.: uma vaga da varejista): a ferramenta reconhece a empresa e
  acompanha a página de vagas dela.
- **Página própria muito grande**: só o trecho de vagas, até um limite de tamanho; o resto fica de fora com aviso.
- **Página própria que muda pouco** (ex.: só a data no rodapé): conta como mudada, e a IA lê de novo. As vagas já vistas
  não voltam.
- **Vaga que some da página**: a que já está no dashboard fica onde está.
- **Página em outra língua**: a IA separa as vagas como estão, sem traduzir.
- **Muitas páginas próprias**: há um limite de páginas lidas pela IA por busca. As que passarem ficam para a próxima,
  com aviso.
- **A IA principal falha**: vale a IA reserva (spec 032). Se as duas falharem, a empresa fica de fora com aviso.
- **EY na consulta sem resultado**: zero vagas, sem aviso de erro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O campo "Empresas que você acompanha" MUST aceitar o link da página de vagas de qualquer empresa. A
  ferramenta reconhece:
  - Greenhouse, Lever e Ashby, como hoje;
  - Teamtailor;
  - o site de vagas da EY.

  Página sem sistema reconhecido entra como "página própria".
- **FR-002**: Ao adicionar, a ferramenta MUST mostrar o nome da empresa e o tipo de leitura. Link de portal de vagas
  (LinkedIn, Indeed, Gupy, InfoJobs, Vagas.com, Nerdin, JobGether, FullStack, MyGreenhouse e afins) MUST ser recusado,
  com a dica de ligá-lo em Portais. A mesma empresa não se repete. O limite continua de 50 empresas.
- **FR-003**: Empresa no Teamtailor MUST ser lida pela lista pública de vagas que o próprio site oferece, no máximo uma
  vez por busca, servindo às duas áreas e a todos os cargos.
- **FR-004**: A EY MUST ser lida como hoje (a busca do site, com a pausa e as regras da spec 039), só que como empresa
  acompanhada. Ela MUST sair da lista de portais.
- **FR-005**: Na migração:
  - config com a EY ligada nos portais MUST ganhar a EY na lista de empresas, uma vez, e perder "ey" dos portais;
  - config com a EY desligada não ganha a EY;
  - config novo começa sem a EY;
  - as vagas da EY MUST manter o identificador de hoje.
- **FR-006**: Página própria, com a IA ligada:
  - a ferramenta MUST ler o texto visível da página pública, depois do filtro de integridade;
  - a IA separa as vagas, cada uma com cargo, modelo de trabalho, local, requisitos e o e-mail ou link de candidatura
    que a página mostrar;
  - campo que não está no texto MUST ficar vazio. Nada é estimado nem inventado (princípio IV).
- **FR-007**: Página própria com a IA desligada, ou com as IAs falhando, MUST ficar de fora da busca com um aviso só,
  sem interromper a busca.
- **FR-008**: Vaga de página própria:
  - MUST ter um identificador estável, pela empresa e pelo cargo, para não voltar como nova;
  - a data é o dia em que a ferramenta a viu pela primeira vez;
  - o link é o da página da empresa.
- **FR-009**: Página própria sem mudança desde a última leitura MUST NOT ser enviada de novo à IA: valem as vagas
  separadas da última vez.
- **FR-010**: Toda vaga de empresa acompanhada MUST passar pelos filtros de sempre:
  - cargo e janela de tempo (na página própria, pela data em que foi vista);
  - local: na nacional, remota aberta ao país ou presencial/híbrida na cidade; na internacional, a consulta global;
  - idioma, senioridade, empresas excluídas e integridade (spec 034).
- **FR-011**: Respeito aos sites:
  - só páginas públicas, sem login nem cookies;
  - uma leitura por empresa por busca (a EY segue as regras dela);
  - pausa entre pedidos ao mesmo site;
  - no primeiro bloqueio, o site sai do resto da busca, sem nova tentativa, com um aviso;
  - página que não existe mais vira o aviso "remova ou troque o link".
- **FR-012**: Página própria em que a IA não achou vaga MUST gerar um aviso informativo, não um erro.
- **FR-013**: Um limite de páginas próprias lidas pela IA por busca MUST existir. As que passarem ficam para a próxima
  busca, com aviso.
- **FR-014**: "Acompanhar empresa" no detalhe da vaga e no Adicionar Vaga MUST valer também para links de vaga do
  Teamtailor e da EY.
- **FR-015**: A consulta da EY sem resultado MUST NOT gerar o aviso "não consegui ler as vagas da EY". A causa do aviso
  de 01/11 é conferida e corrigida no plano.
- **FR-016**: Documentação atualizada: README, `dash/README.md`, `dash/API.md`, AGENTS.md (a EY sai da lista de
  portais), a skill buscar-vagas e o roteiro `docs/novo-portal.md` (sistema novo de empresa acompanhada).

### Key Entities

- **Empresa acompanhada**: nome, link da página de vagas, tipo de leitura (Greenhouse, Lever, Ashby, Teamtailor, EY ou
  página própria) e o identificador dela no sistema.
- **Leitura da página própria**: guardada localmente, fora do Git. Tem a marca do texto lido (para saber se mudou), as
  vagas separadas pela IA e a data.
- **Vaga de página própria**: cargo, modelo, local, requisitos, contato de candidatura, empresa, link da página e o dia em
  que foi vista primeiro.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A pessoa adiciona a EY, a varejista e a consultoria pelo link em menos de 1 minuto cada, vendo o tipo de
  leitura reconhecido.
- **SC-002**: Depois de um Buscar, todas as vagas da varejista que o site mostra para o cargo e o local da pessoa
  aparecem no relatório.
- **SC-003**: Para quem tinha a EY ligada, nenhuma vaga da EY aparece duplicada, e a EY aparece em Empresas
  acompanhadas, não em Portais.
- **SC-004**: Na página própria, todas as vagas visíveis que batem com os cargos entram no relatório, e todo campo
  preenchido está no texto da página.
- **SC-005**: Numa página própria sem mudança, a busca faz zero pedidos à IA.
- **SC-006**: Num bloqueio simulado, zero novas tentativas ao site bloqueado, e as outras empresas trazem as vagas.
- **SC-007**: Sem a IA ligada, uma página própria gera um aviso e nenhum erro na busca.

## Assumptions

- **Decisões da pessoa** em 01/11/2026: ver Clarifications.
- **Sistemas reconhecidos nesta spec**: os três atuais, o Teamtailor e o site da EY. O plano confere se a leitura da EY
  serve a outros sites do mesmo sistema da SAP. Se não servir, esses sites entram como página própria. Outros sistemas
  (ex.: Workday, SmartRecruiters) ficam para specs futuras, pelo roteiro de sistema novo.
- **Limite de páginas próprias por busca**: 10, a conferir no plano. O texto enviado à IA também tem um limite de
  tamanho.
- **IA**: a mesma que dá a nota, com a reserva (spec 032). A leitura da página não manda dados da pessoa à IA: só o texto
  público da página.
- **Termos de cada site**: conferidos no plano (Teamtailor, EY e consultoria). Se algum proibir acesso automatizado, vale a
  regra de "Termos contrários" da constituição.
- **Data na página própria**: a ferramenta não sabe quando a vaga foi publicada. A primeira busca depois de adicionar a
  empresa traz todas as vagas que batem com os cargos.
- **Front**: as mudanças da página são feitas na branch `frontend-react`. A verificação é feita no Windows.
