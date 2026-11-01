# Feature Specification: Portais com login na busca (primeiro: MyGreenhouse Jobs)

**Feature Branch**: `041-portais-com-login` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-01

**Status**: Aprovada em 2026-11-01; plano em 2026-11-01

**Input**: User description: "eu procurei vagas no portal greenhouse e lá tem muito scrum master mas aqui não aparece"
(31/10/2026), com o link da busca `my.greenhouse.io/jobs/search?query=scrum&work_type[]=remote`. Depois: "e abrir a
janela e eu logar?" e "devemos ter no futuro outras páginas que exigem login antes de expor a pesquisa, assim podemos
criar uma área específica para esse tipo de portal". Decisões de 31/10 e 01/11/2026 em Clarifications.

## Contexto

Hoje o Greenhouse só entra na busca pelas **empresas acompanhadas** (spec 031): a pessoa cola a página de vagas de cada
empresa, e a ferramenta lê a API pública dela. Não há busca por cargo entre empresas.

- A única busca do Greenhouse entre empresas é o **MyGreenhouse Jobs** (spec 031, research R1):
  - **exige login**: sem sessão, a busca leva à tela de entrada;
  - não tem API documentada;
  - só mostra as empresas que aderiram ao recurso;
  - os termos do MyGreenhouse não foram localizados.

  Por isso foi barrada em 25/10/2026.
- A constituição (princípio VI) não cobre ler uma busca com a sessão da pessoa:
  - nos portais, só vale a busca pública, sem login;
  - a "Conta conectada" lê só a área da própria pessoa (o andamento das candidaturas), portal por portal, e hoje só na
    Gupy e no Indeed.

  Esta spec pede uma **emenda** com uma regra nova para a busca com login. O texto vem no plano e é aprovado pela pessoa
  antes da implementação.
- Em 31/10/2026, a pessoa decidiu seguir com o MyGreenhouse, com o login feito por ela na janela da ferramenta. Em
  01/11/2026, ampliou o pedido: outros portais devem mostrar a busca só depois do login, então a spec cria uma **área
  própria para portais com login**, e o MyGreenhouse Jobs é o primeiro deles.

## Clarifications

### Session 2026-11-01

- Q: Só o MyGreenhouse ou uma área para portais desse tipo? → A: Uma área "Portais com login", com o MyGreenhouse Jobs
  como primeiro portal. Cada portal novo entra em spec própria, com análise de risco. A busca do LinkedIn continua fora.
- Q: Quando a busca nesses portais roda? → A: No botão **Buscar da página**, junto da busca normal, com o portal
  conectado e ligado e a janela minimizada. Na busca pelo terminal ou pelo chat, o portal fica de fora com um aviso: o
  assistente não usa a sessão da pessoa.
- Q: Onde fica a área? → A: Numa seção **"Portais com login"** do painel Filtros da busca.
- Q: E se o login tiver caído quando a busca chegar ao portal? → A: A janela vem para a frente e espera **até 3
  minutos**, como no "Atualizar candidaturas". Se a pessoa entrar, a leitura segue; se não, o portal é pulado nesta
  busca, com aviso.
- Q: O login pelo LinkedIn (SSO) pode ser usado na janela? → A: Sim, com aviso de risco. Durante o login, a ferramenta
  não lê nem age nas páginas do LinkedIn. Se o portal tiver login próprio, a área recomenda esse.
- Q (plano): Os termos do MyGreenhouse proíbem acesso automatizado e permitem suspender a conta (research R1). Seguir?
  → A: Sim, mesmo assim, pela regra de "Termos contrários": desligado por padrão, com o risco no aviso.
- Q (plano): A pesquisa mostrou pouca vaga ágil aberta ao Brasil hoje (research R3). Pausar? → A: Não. Seguir com a
  spec e, à parte, considerar acompanhar empresas que contratam no Brasil (a pessoa decidiu não acompanhar nenhuma por
  enquanto).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conectar um portal com login (Priority: P1)

Em Filtros da busca → Portais com login, a pessoa vê o MyGreenhouse Jobs desligado, com o resumo dos termos e dos riscos.
Ela liga o portal (confirmando o aviso de risco) e clica em Conectar. A janela da ferramenta abre na página de login, a
pessoa entra (pelo e-mail ou pelo LinkedIn) e clica em Pronto. O portal fica "conectado".

**Independent Test**: com páginas simuladas: ligar pede o aviso; Conectar abre a página de login; Pronto com sessão
marca "conectado"; Pronto sem sessão avisa que o login não foi encontrado; Desconectar apaga a sessão.

**Acceptance Scenarios**:

1. **Given** o portal desligado (o padrão), **When** a pessoa busca, **Then** nenhum pedido vai a ele.
2. **Given** a área, **When** a pessoa liga o portal, **Then** a ferramenta pede a confirmação do aviso de risco. Depois
   de confirmado, o portal fica ligado e "desconectado" até o login.
3. **Given** Conectar, **When** a pessoa entra na janela e clica em Pronto, **Then** o portal fica "conectado". Se ela
   ainda não entrou, a área diz que o login não foi encontrado.
4. **Given** o login pelo LinkedIn, **When** a janela passa pelas páginas do LinkedIn, **Then** a ferramenta não lê nem
   age nelas, e a área mostra o aviso de risco da conta do LinkedIn.
5. **Given** um portal conectado, **When** a pessoa clica em Desconectar, **Then** a sessão daquele portal sai da janela
   da ferramenta e a situação volta para "desconectado".

### User Story 2 - Vagas do MyGreenhouse no Buscar da página (Priority: P1)

Com o portal ligado e conectado, o Buscar da página consulta o MyGreenhouse com os cargos da busca e o filtro de
trabalho remoto. As vagas passam pelos filtros de sempre e entram no relatório com a etiqueta "MyGreenhouse", esperando
nota.

**Independent Test**: com resultados simulados: vagas com título, empresa, local, modelo, data e link, filtradas como
as das outras fontes.

**Acceptance Scenarios**:

1. **Given** o portal conectado e ligado, **When** a pessoa clica em Buscar, **Then** a ferramenta lê os resultados de
   cada cargo com o filtro remoto, com a janela minimizada, e a busca dos outros portais segue igual.
2. **Given** uma vaga remota só para outro país, **When** a busca roda, **Then** ela não entra na área nacional (a mesma
   regra das empresas acompanhadas).
3. **Given** a mesma vaga vinda também das empresas acompanhadas, **When** as duas chegam, **Then** ela aparece uma vez.
4. **Given** uma vaga com texto escondido que mira a IA, **When** ela entra, **Then** o filtro de integridade age como
   nas outras fontes.

### User Story 3 - Login caído (Priority: P2)

A sessão expira de tempos em tempos. Quando a busca chega ao portal e o login caiu, a ferramenta mostra a janela e dá à
pessoa a chance de entrar de novo, sem travar a busca.

**Acceptance Scenarios**:

1. **Given** a sessão expirada, **When** a busca chega ao portal, **Then** a janela vem para a frente na página de login
   e a página do dashboard mostra "aguardando login" com o tempo que falta.
2. **Given** a pessoa entra em até 3 minutos, **When** o login é reconhecido, **Then** a leitura segue e a janela volta
   a ficar minimizada.
3. **Given** a pessoa não entra em 3 minutos, **When** o tempo acaba, **Then** o portal é pulado nesta busca com aviso,
   e as vagas dos outros portais entram normalmente.

### User Story 4 - Bloqueio, captcha, portal mudado e busca fora da página (Priority: P2)

A ferramenta para no primeiro sinal de problema, sem tentar contornar, e nunca usa a sessão da pessoa fora do clique
dela na página.

**Acceptance Scenarios**:

1. **Given** recusa, limite de consultas, aviso de atividade incomum ou conta restrita, **When** o sinal aparece,
   **Then** a ferramenta para no primeiro sinal, sem nova tentativa, e o portal fica 24 horas em espera. Durante a
   espera, a busca pergunta antes de seguir sem ele.
2. **Given** um captcha ou uma verificação, **When** aparece durante a leitura, **Then** a ferramenta para aquele portal
   nesta busca, traz a janela para a pessoa ver e avisa. Ela não toca no captcha.
3. **Given** uma página de resultados que a ferramenta não reconhece (o portal mudou), **When** a leitura tenta ler,
   **Then** para com o aviso "o portal mudou; a leitura precisa de ajuste", e a busca segue com os outros portais.
4. **Given** a busca pelo terminal ou pelo chat, **When** ela roda, **Then** os portais com login ficam de fora com o
   aviso "só pelo botão Buscar da página", sem abrir a janela.

### User Story 5 - Acompanhar a empresa da vaga (Priority: P3)

Muitas vagas do MyGreenhouse são de empresas com página pública no Greenhouse. A pessoa pode acompanhar a empresa a
partir da vaga, e daí em diante as vagas dela entram pela API pública em toda busca, inclusive pelo terminal.

**Acceptance Scenarios**:

1. **Given** uma vaga do MyGreenhouse de empresa com página pública no Greenhouse, **When** a pessoa abre a vaga,
   **Then** vê "Acompanhar empresa", o mesmo das vagas do Greenhouse adicionadas pelo link.

### Edge Cases

- **Sem navegador compatível ou janela fechada no meio da busca**: o portal é pulado com aviso, e a busca segue.
- **Login com código por e-mail ou duas etapas**: feito pela pessoa na janela, ao conectar ou dentro dos 3 minutos.
- **Vários portais com login**: cada um tem a sua situação; um portal parado não impede os outros.
- **Vaga cuja candidatura fica no site da empresa**: entra com o link que o portal mostra.
- **Muitos resultados**: até 3 páginas por cargo; o resto fica para a próxima busca.
- **Nenhum resultado para um cargo**: nenhuma vaga, sem erro.
- **Conta da pessoa restrita pelo portal**: conta como bloqueio (24 horas de espera), com o aviso para conferir a conta e,
  se ela quiser, desconectar.
- **Busca agendada ou sem clique**: não existe; nada lê os portais com login sozinho.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O painel Filtros da busca MUST ter a seção "Portais com login", separada dos portais de busca pública. Para
  cada portal, ela mostra:
  - o nome e o resumo dos termos e dos riscos;
  - o liga/desliga;
  - os botões Conectar, Pronto e Desconectar;
  - a situação: desligado, desconectado, conectado, aguardando login ou em espera até uma data.
- **FR-002**: Cada portal com login MUST vir **desligado por padrão**. Ligar MUST pedir a confirmação do aviso de risco
  (o portal pode restringir a conta da pessoa).
- **FR-003**: Um portal novo na área MUST entrar por spec própria, com análise de risco (termos, login e formato),
  seguindo as regras comuns desta spec. O primeiro é o MyGreenhouse Jobs. A busca do LinkedIn MUST continuar fora.
- **FR-004**: O login MUST ser feito pela pessoa, na janela da ferramenta, que usa um perfil só dela, local e fora do
  Git. A ferramenta MUST NOT:
  - pedir, ler, guardar ou digitar senha;
  - clicar em botões de login;
  - copiar cookies ou a sessão para fora do navegador;
  - usar as credenciais que a pessoa guarda para a candidatura assistida.
- **FR-005**: O login por outro serviço (ex.: LinkedIn) é permitido. Durante o login, a ferramenta MUST NOT ler nem agir
  em páginas de outro domínio que não o do portal. A área MUST mostrar o aviso de risco desse serviço e recomendar o
  login próprio do portal, quando ele existir.
- **FR-006**: A leitura MUST rodar só a partir do botão Buscar da página, junto da busca normal, com o portal ligado e
  conectado e a janela minimizada. Na busca pelo terminal ou pelo chat, os portais com login MUST ficar de fora, com o
  aviso "só pelo botão Buscar da página" e sem abrir a janela. Nada roda agendado.
- **FR-007**: A leitura é só leitura. A ferramenta MUST só abrir os endereços de busca e de vaga do portal e ler o que
  eles mostram. Ela MUST NOT clicar em botões ou links, se candidatar, salvar vagas, seguir empresas, enviar mensagens
  ou mudar qualquer coisa na conta.
- **FR-008**: No MyGreenhouse, a consulta MUST:
  - usar cada cargo da busca com o filtro de trabalho remoto;
  - ler até 3 páginas por cargo;
  - fazer uma pausa sorteada de 3 a 7 s entre os pedidos, ajustável por `MYGREENHOUSE_PAUSA` (de 3 a 60 s), como nos
    outros portais.
- **FR-009**: As vagas MUST passar pelos filtros de sempre:
  - cargo e janela de tempo;
  - país: na área nacional, só as remotas abertas ao país da pessoa, a mesma regra das empresas acompanhadas; na
    internacional, se estiver ligada, os filtros dela;
  - idioma, senioridade e empresas excluídas;
  - integridade (spec 034).

  As vagas entram no relatório com a etiqueta do portal e esperam nota como as outras.
- **FR-010**: Cada vaga MUST ter um identificador estável. A mesma vaga vinda das empresas acompanhadas MUST aparecer
  uma vez.
- **FR-011**: Com o login caído:
  - a janela MUST vir para a frente na página de login;
  - a página do dashboard MUST mostrar "aguardando login";
  - a ferramenta MUST esperar até 3 minutos. Com o login, a leitura segue; sem ele, o portal é pulado nesta busca, com
    aviso.
- **FR-012**: Diante de um bloqueio explícito (recusa, limite de consultas, atividade incomum ou conta restrita), a
  ferramenta MUST:
  - parar no primeiro sinal, sem nova tentativa;
  - deixar o portal 24 horas em espera, com aviso e a hora em que a espera acaba;
  - não fazer nenhum pedido ao portal durante a espera.

  Durante a espera, a busca MUST perguntar antes de seguir sem o portal, como faz com os outros portais em espera.
- **FR-013**: Diante de um captcha ou de uma verificação durante a busca, a ferramenta MUST parar aquele portal nesta
  busca, trazer a janela para a pessoa ver e avisar. Ela MUST NOT tocar no captcha.
- **FR-014**: Se a página de resultados não for reconhecida (o portal mudou), a ferramenta MUST parar aquele portal com
  aviso, sem tentar outra forma de ler, e a busca segue com os outros portais.
- **FR-015**: Uma vaga do MyGreenhouse de empresa com página pública no Greenhouse MUST oferecer "Acompanhar empresa",
  como as vagas do Greenhouse adicionadas pelo link (spec 031).
- **FR-016**: Desconectar MUST apagar a sessão daquele portal da janela da ferramenta. Se não sobrar nenhum portal
  conectado, apaga o perfil inteiro, como na conta conectada.
- **FR-017**: O que for lido MUST ficar no computador da pessoa:
  - a sessão, no perfil local da janela;
  - o estado e a espera, na pasta local de cache;
  - as vagas, no banco local.

  Nada disso vai para o Git.
- **FR-018**: A constituição MUST ganhar, no princípio VI, a regra da busca com login (texto no plano). A documentação
  MUST explicar a área: README, AGENTS.md, contrato da API do dashboard, skill buscar-vagas e uma seção nova no roteiro
  de portal novo para os portais com login.

### Key Entities

- **Portal com login**:
  - nome e rótulo;
  - endereço de login e endereço da busca;
  - domínios que fazem parte do login, inclusive os de outro serviço;
  - resumo dos termos e dos riscos;
  - ligado ou desligado.
- **Situação da conexão**: por portal, guardada localmente (conectado, desde quando, última leitura).
- **Espera do portal**: o fim e o motivo, guardados localmente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o portal desligado (o padrão), nenhum pedido vai a ele, e a busca sai igual à de antes.
- **SC-002**: Com o MyGreenhouse conectado, todas as vagas da primeira página da mesma busca feita à mão (cargo e remoto)
  que passam nos filtros aparecem no relatório depois de um Buscar.
- **SC-003**: Em nenhum teste a ferramenta digita senha, clica em botão do portal ou lê página de outro domínio durante
  o login.
- **SC-004**: A busca pelo terminal ou pelo chat nunca abre a janela nem faz pedido a um portal com login.
- **SC-005**: Com o login caído, a busca leva no máximo 3 minutos a mais do que levaria sem o portal, e os outros
  portais trazem as vagas normalmente.
- **SC-006**: Num bloqueio simulado, há zero novas tentativas e zero pedidos ao portal até o fim da espera.
- **SC-007**: Uma busca lê no máximo 3 páginas de resultados do MyGreenhouse por cargo.
- **SC-008**: A pessoa liga e conecta o MyGreenhouse em menos de 2 minutos.

## Assumptions

- **Decisões da pessoa** em 31/10 e 01/11/2026: ver Clarifications.
- **Desligado por padrão, com aviso de risco ao ligar**: como na candidatura assistida.
- **Pausa de 3 a 7 s e espera de 24 horas**: como nos portais sem API oficial (FullStack, JobGether).
- **Até 3 páginas por cargo**: um padrão a conferir no plano, conforme o formato da busca.
- **Formato**: a busca do MyGreenhouse não tem API documentada. No plano, com a pessoa logada e com o OK dela, a
  ferramenta mapeia os pedidos que a própria página faz (preferidos, como na spec 018) ou, se não houver, a tela. Se o
  formato mudar, vale o FR-014.
- **Descrição da vaga**: vem da página pública da vaga no Greenhouse, quando houver (como nas empresas acompanhadas), e
  só para as vagas do relatório. Assim, a sessão é usada só para a lista de resultados.
- **Termos do MyGreenhouse**: o MyGreenhouse User Agreement (29/01/2025) proíbe acesso automatizado (research R1).
  Vale a regra de "Termos contrários": decisão da pessoa de 2026-11-01 registrada e o portal desligado por padrão.
- **Alcance**: só aparecem as empresas que aderiram ao MyGreenhouse Jobs. As demais continuam pelas empresas
  acompanhadas.
- **Constituição**: a emenda no princípio VI é escrita no plano e aprovada pela pessoa antes da implementação.
- **Front**: as mudanças da página são feitas na branch `frontend-react`. A verificação é feita no Windows.
