# Feature Specification: LinkedIn na busca de vagas

**Feature Branch**: `014-linkedin-na-busca` (pasta da spec; o trabalho acontece na `master` por worktree, conforme a
constituição)

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "LinkedIn como fonte da busca de vagas. O LinkedIn entra na busca (página, terminal e
skill) como o Indeed, cobrindo tudo o que ele oferece: vaga nacional ou de fora, remota, híbrida ou presencial,
mudança de país e os tipos de contratação. Cada grupo de consulta que a ferramenta já monta vira uma busca do LinkedIn
com o modelo de trabalho e o local certos; a janela de tempo e os tipos de emprego vão como filtro do próprio
LinkedIn. A vaga passa pelos mesmos critérios das outras e não se repete com a adicionada pelo link. A pessoa liga e
desliga o LinkedIn (e os outros portais nacionais) numa seção Portais do painel de filtros; desligado por padrão.
Respeito ao portal: só a busca pública, sem login nem a conta da pessoa; pausa entre as consultas; descrição só das
vagas que vão para o relatório; no primeiro bloqueio o LinkedIn para pelo resto da busca, com aviso, e as outras
fontes seguem. Emenda MAJOR da constituição (princípio VI); o perfil da pessoa continua sem ser lido do LinkedIn.
AGENTS.md, README e a skill buscar-vagas atualizados. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vagas do LinkedIn na busca de sempre (Priority: P1)

A pessoa marca o LinkedIn nos portais da busca e clica em "Buscar vagas" (ou pede no chat, ou roda no terminal). Com
os mesmos cargos, país, cidade e modelos de trabalho que ela já configurou, a busca traz também as vagas do LinkedIn,
com a etiqueta do portal, para o Relatório de Vagas, junto das do Indeed e da Gupy.

**Why this priority**: é o pedido central; o LinkedIn é onde está a maior parte das vagas que a pessoa procura.

**Independent Test**: com o LinkedIn ligado e respostas do portal simuladas, rodar a busca e ver as vagas do LinkedIn
no relatório com o título, a empresa, o local, a data e o link para a vaga original.

**Acceptance Scenarios**:

1. **Given** o LinkedIn marcado nos portais, **When** a pessoa busca, **Then** as vagas do LinkedIn aparecem no
   relatório com a etiqueta "LinkedIn" e o link da vaga original.
2. **Given** o LinkedIn desmarcado, **When** a pessoa busca, **Then** nenhuma consulta vai ao LinkedIn e o resultado é
   o mesmo de antes desta funcionalidade.
3. **Given** uma vaga do LinkedIn que a pessoa já adicionou pelo link, **When** a busca a encontra, **Then** ela não
   aparece de novo.
4. **Given** a mesma vaga no LinkedIn e em outro portal, **When** a busca encontra as duas, **Then** o relatório mostra
   uma vaga só, com os dois portais, como já acontece entre Indeed e Gupy.

---

### User Story 2 - Todos os tipos de vaga: nacional, de fora, remota, híbrida, presencial e mudança (Priority: P1)

A pessoa configura o que aceita: remoto no país, híbrido e presencial na cidade dela, vagas remotas de outros países
e, se aceita se mudar, presenciais ou híbridas em países escolhidos. Cada uma dessas buscas também consulta o LinkedIn
com o modelo de trabalho e o local corretos, inclusive a busca "mundo todo" para vagas remotas sem país. O tipo de
contratação que ela aceita (tempo integral, contrato/PJ, meio período, estágio, temporário) e a janela de tempo vão
como filtro do próprio LinkedIn.

**Why this priority**: sem isso o LinkedIn traria vagas fora do que a pessoa procura e encheria "Fora dos critérios".

**Independent Test**: com uma configuração que tem remoto no país, cidade com híbrido, um país de fora e mudança para
outro país, conferir que cada busca do LinkedIn pede o local e o modelo certos, e que as vagas encontradas recebem a
área (nacional ou internacional, com o país) e passam pelos critérios de sempre.

**Acceptance Scenarios**:

1. **Given** remoto no país marcado, **When** a busca roda, **Then** o LinkedIn é consultado no país da pessoa só com
   vagas remotas.
2. **Given** cidade com raio e híbrido ou presencial marcados, **When** a busca roda, **Then** o LinkedIn é consultado
   na cidade, com o raio e só com os modelos marcados.
3. **Given** a busca internacional ligada com um país, **When** a busca roda, **Then** o LinkedIn é consultado nesse
   país com vagas remotas, e as vagas recebem a etiqueta "Internacional · país".
4. **Given** "aceito me mudar" com um país, **When** a busca roda, **Then** o LinkedIn é consultado nesse país com
   vagas presenciais e híbridas; uma vaga presencial num país fora da lista de mudança vai para Fora dos critérios com
   o motivo.
5. **Given** a busca internacional ligada, **When** a busca roda, **Then** o LinkedIn também é consultado para vagas
   remotas no mundo todo, e a elegibilidade (país exigido, autorização de trabalho, sponsor, região) decide se cada
   uma fica no relatório.
6. **Given** só "tempo integral" e "PJ / contrato" marcados, **When** a busca roda, **Then** o LinkedIn é consultado só
   com esses tipos, e uma vaga de estágio que apareça vai para Fora dos critérios com o motivo.

---

### User Story 3 - Ligar e desligar os portais na página (Priority: P2)

No painel "Filtros da busca", uma seção Portais mostra Indeed, Gupy, LinkedIn e startup.jobs com caixas de marcar,
cada um com o aviso do que ele é (oficial ou não, risco de bloqueio, o que precisa). A pessoa liga o LinkedIn ali e vê
o número de consultas da próxima busca mudar.

**Why this priority**: hoje os portais nacionais só mudam editando o arquivo de configuração ou pelo terminal.

**Independent Test**: no painel, marcar o LinkedIn e salvar; a configuração passa a ter o LinkedIn e o contador de
consultas soma as dele.

**Acceptance Scenarios**:

1. **Given** o painel de filtros, **When** a pessoa marca o LinkedIn e salva, **Then** a próxima busca inclui o
   LinkedIn, e o contador de consultas mostra quantas vão para ele.
2. **Given** uma configuração nova, **When** a pessoa abre o painel, **Then** o LinkedIn aparece desmarcado.
3. **Given** todos os portais desmarcados, **When** a pessoa tenta salvar, **Then** a ferramenta pede pelo menos um.

---

### User Story 4 - Respeito ao portal e bloqueio sem susto (Priority: P2)

A busca no LinkedIn usa só a parte pública do site, sem login e sem a conta da pessoa, com pausa entre as consultas,
e busca a descrição só das vagas que vão para o relatório. Se o LinkedIn limitar as consultas ou pedir login, a
ferramenta para de consultá-lo pelo resto daquela busca, avisa, e as outras fontes continuam.

**Why this priority**: protege a pessoa (a conta dela nunca é usada) e evita que a busca inteira falhe por um portal.

**Independent Test**: simular o LinkedIn respondendo "muitas consultas" na segunda busca; conferir que não há nova
tentativa, que as consultas seguintes ao LinkedIn são puladas, que o aviso aparece e que as vagas do Indeed e da Gupy
chegam ao relatório.

**Acceptance Scenarios**:

1. **Given** uma busca com várias consultas ao LinkedIn, **When** ela roda, **Then** há uma pausa entre elas e nenhuma
   consulta usa login, conta ou cookies da pessoa.
2. **Given** o LinkedIn bloqueando no meio da busca, **When** a ferramenta recebe o bloqueio, **Then** não tenta de
   novo, pula as consultas restantes ao LinkedIn, mostra "o LinkedIn limitou as consultas; tente mais tarde" no
   resumo da busca e entrega as vagas das outras fontes.
3. **Given** vagas do LinkedIn que ficam fora dos critérios ou já estão no quadro, **When** a busca termina, **Then**
   a descrição delas não foi buscada.

---

### Edge Cases

- **Busca do LinkedIn sem nenhuma vaga** (termo raro, país sem vagas): segue normalmente, sem erro.
- **Vaga sem empresa ou sem data**: entra com "Empresa não informada" e sem data, como nas outras fontes.
- **Descrição não chega** (bloqueio só na leitura da vaga): a vaga entra com o que veio da lista e fica para a análise
  pedir o texto (como no Indeed sem descrição).
- **Página do LinkedIn mudou e nada é reconhecido**: a busca avisa "não consegui ler as vagas do LinkedIn" e segue com
  as outras fontes, sem quebrar.
- **Vaga marcada como remota no LinkedIn mas com "híbrido" no texto**: a análise e os critérios de sempre decidem, com o
  modelo que o texto mostrar.
- **Mesma vaga encontrada por dois grupos** (por exemplo, remoto no país e mundo todo): aparece uma vez, com os dois
  grupos.
- **Configuração antiga sem a lista de portais**: continua com Indeed e Gupy, como hoje.
- **Busca pelo terminal com `--fontes linkedin`**: funciona sem passar pelo painel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O LinkedIn MUST ser um portal da busca, ligado ou desligado pela pessoa, e MUST vir desligado em
  configuração nova ou antiga sem a lista de portais.
- **FR-002**: Com o LinkedIn ligado, cada grupo de consulta da busca MUST gerar uma consulta ao LinkedIn com o local e
  o modelo de trabalho do grupo: remoto no país (país, remoto); país inteiro sem cidade (país, só os modelos
  presencial/híbrido marcados); cidade (cidade com o raio, presencial/híbrido marcados); país de fora (país, remoto);
  mudança (país, presencial e híbrido); mundo todo, quando a busca internacional está ligada (sem país, remoto; também
  presencial e híbrido se a pessoa aceita se mudar).
- **FR-003**: A janela de tempo da busca e os tipos de emprego marcados MUST ir como filtro da consulta ao LinkedIn.
- **FR-004**: Cada vaga do LinkedIn MUST trazer título, empresa, local, data de publicação (quando houver) e o link da
  vaga original; o identificador MUST ser o mesmo usado quando a vaga é adicionada pelo link, para não duplicar.
- **FR-005**: Quando a consulta pediu um único modelo de trabalho, a vaga MUST receber esse modelo; o tipo de emprego
  informado pelo LinkedIn na vaga MUST ser convertido para os tipos da ferramenta.
- **FR-006**: A vaga do LinkedIn MUST passar pelos mesmos passos das outras: área e país, etiqueta internacional,
  elegibilidade (país exigido, autorização, sponsor, região, mudança), idioma, moeda, senioridade, tipo de emprego,
  empresas excluídas, Fora dos critérios com o motivo, junção com o mesmo anúncio em outro portal e análise com IA.
- **FR-007**: A descrição de uma vaga do LinkedIn MUST ser buscada só quando ela vai para o relatório.
- **FR-008**: As consultas ao LinkedIn MUST usar só a parte pública do site, sem login, sem a conta, as senhas ou os
  cookies da pessoa, e com pausa entre uma consulta e outra (maior que a usada nos outros portais).
- **FR-009**: Ao receber um sinal de bloqueio (limite de consultas ou pedido de login), a ferramenta MUST parar de
  consultar o LinkedIn pelo resto da busca, sem nova tentativa, MUST mostrar o aviso no resumo da busca (página,
  terminal e chat) e MUST continuar com as outras fontes.
- **FR-010**: O painel "Filtros da busca" MUST ter uma seção Portais com Indeed, Gupy, LinkedIn e startup.jobs, cada um
  com uma linha sobre o que ele é; MUST exigir pelo menos um portal; e o contador de consultas MUST somar as do
  LinkedIn.
- **FR-011**: A busca pelo terminal e pela skill MUST aceitar o LinkedIn como as outras fontes.
- **FR-012**: A constituição MUST receber a emenda MAJOR do princípio VI: sai "sem raspar o LinkedIn" e entram as
  regras desta spec (só a busca pública, sem login nem conta da pessoa, pausa, descrição só do necessário, parar no
  bloqueio sem contornar, sem automação de candidatura); o perfil da pessoa continua sem ser lido do LinkedIn (só os
  arquivos que ela baixa).
- **FR-013**: AGENTS.md, o README (fontes, termos de uso, aviso de consulta não oficial e de bloqueio temporário,
  roteiro) e a skill buscar-vagas MUST refletir a nova regra e o novo portal.
- **FR-014**: Com o LinkedIn desligado, a busca MUST dar exatamente o mesmo resultado de antes desta funcionalidade.

### Key Entities

- **Portal da busca**: uma fonte de vagas que a pessoa liga ou desliga (Indeed, Gupy, LinkedIn, startup.jobs), com o
  que ele é e as regras de uso.
- **Consulta ao LinkedIn**: o cargo, o local (país, cidade com raio ou mundo todo), os modelos de trabalho, os tipos de
  emprego e a janela de tempo de um grupo da busca.
- **Vaga do LinkedIn**: uma vaga como as outras, com o mesmo identificador da vaga adicionada pelo link.
- **Bloqueio do LinkedIn na busca**: o estado que faz a ferramenta pular o LinkedIn até o fim daquela busca, com o
  aviso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o LinkedIn ligado, 100% dos grupos de consulta da configuração geram uma consulta ao LinkedIn com o
  local e o modelo de trabalho certos (conferido em configuração com os seis tipos de grupo).
- **SC-002**: Nenhuma vaga do LinkedIn aparece duas vezes no relatório quando já está no quadro (adicionada pelo link)
  ou quando outro grupo ou portal a encontrou.
- **SC-003**: Com o LinkedIn desligado, a saída da busca é idêntica à de antes desta funcionalidade.
- **SC-004**: Num bloqueio simulado, há zero novas tentativas ao LinkedIn depois do primeiro sinal, o aviso aparece e
  100% das vagas das outras fontes chegam ao relatório.
- **SC-005**: Nenhuma consulta ao LinkedIn leva login, conta ou cookies da pessoa, e a descrição só é buscada para as
  vagas que vão para o relatório.
- **SC-006**: A pessoa liga o LinkedIn pelo painel em menos de 1 minuto, sem editar arquivos.

## Assumptions

- A busca pública de vagas do LinkedIn (sem login) segue disponível; quando ela mudar, a ferramenta avisa e segue com
  as outras fontes (como acontece com o Indeed, também consultado de forma não oficial).
- O usuário decidiu remover a proibição de buscar no LinkedIn; a emenda da constituição é parte desta spec e o
  respeito ao portal fica nas regras do FR-008 e do FR-009.
- Uma página de resultados (10 vagas) por consulta basta (como nas outras fontes, o número de vagas por termo já é limitado).
- Tipos de emprego: tempo integral, PJ/contrato, meio período, estágio e temporário têm equivalente direto no
  LinkedIn; "voluntário" e "outro" do LinkedIn não entram no filtro.
- Senioridade não vai como filtro do LinkedIn (os níveis dele não batem com Jr/Pl/Sr); continua decidida pelos
  critérios de sempre.
- O LinkedIn conta para o intervalo mínimo entre buscas da página e para o aviso de muitas consultas, como os outros.
- O perfil e o "Adicionar pelo link" não mudam nesta spec.
- Verificação só no Windows, como nas specs anteriores.
