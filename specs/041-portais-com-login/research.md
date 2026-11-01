# Pesquisa: portais com login na busca (MyGreenhouse Jobs)

**Data**: 2026-11-01.
- Os termos foram lidos nas páginas públicas.
- O formato da busca foi lido na janela da ferramenta, com a pessoa logada (pelo LinkedIn) e com o OK dela:
  - a ferramenta só leu a página e repetiu uma vez o pedido que a própria página faz;
  - a rolagem e o filtro de local foram feitos pela pessoa;
  - nenhum botão foi clicado e nenhum dado da conta foi guardado.

Isto não é parecer jurídico.

## R1. Termos de uso

- **MyGreenhouse User Agreement** (`my.greenhouse.io/users/agreement`, "Effective Date: January 29, 2025"). Vale para os
  usuários do MyGreenhouse, ou seja, os candidatos.
  - Seção 3, o que o usuário concorda em não fazer: "(z) use automated means, including spiders, robots, crawlers, or
    similar means or processes to access or use the Services". Também: "(v) override any security features or bypass or
    circumvent any access controls or use limits of the Services".
  - Seção 4: "Greenhouse reserves the right to limit your use of the Services and/or to restrict, suspend or terminate
    your account […] as determined by Greenhouse at our sole discretion".
- **Política de privacidade** (`greenhouse.com/privacy-policy`, atualizada em 01/10/2026): a seção do MyGreenhouse
  "requires authentication and agreement with the MyGreenhouse User Agreement". Não trata de automação.
- **robots.txt**:
  - `my.greenhouse.io`: `User-agent: *` / `Allow: /`;
  - `boards.greenhouse.io`: `Disallow: /embed/`.

  Não é permissão contratual.
- Endereços que não existem (404): `greenhouse.com/legal/terms-of-service`, `my.greenhouse.io/terms` e
  `my.greenhouse.io/privacy`.

**Conclusão**:
- Os termos **proíbem acesso automatizado**, e o risco recai na **conta da pessoa** (limitar, suspender ou encerrar).
- Vale a regra de "Termos contrários" (constituição VI): o portal entra só por decisão explícita da pessoa, registrada
  aqui, e desligado por padrão.
- **Decisão da pessoa em 2026-11-01: seguir mesmo assim**, depois de ler os trechos acima.

## R2. Formato da busca

- **Página**: `my.greenhouse.io/jobs/search` é um app Inertia (o atributo `data-page` traz `component: "jobs"` e
  `version`).
  - A lista não vem no HTML. É uma "deferred prop" (`deferredProps.jobPosts`): `browsing`, `page`,
    `moreResultsAvailable`, `jobPosts`, `trackingData` e `recentSearches`.
  - A página busca a lista com um pedido ao **mesmo endereço**, com os cabeçalhos do Inertia: `X-Inertia: true`,
    `X-Inertia-Version: <version>`, `X-Inertia-Partial-Component: jobs` e `X-Inertia-Partial-Data: <props>`.
  - A resposta é JSON (200, `application/json`, cerca de 2,4 KB comprimidos por página).
- **Filtros no endereço**:
  - `query=<texto>` e `work_type[]=remote`;
  - `date_posted=past_five_days` (os outros valores não foram vistos);
  - `location=Brazil&lat=-11.929178&lon=-49.542799&location_type=country&country_short_name=BR`. O local escolhido na
    página vira coordenadas por um serviço de geocodificação da Greenhouse.
- **Paginação**: `&page=N`, com 12 vagas por página e `moreResultsAvailable: true|false`. A página junta as seguintes
  ao rolar (`mergeProps`). A pessoa rolou até a página 15 sem filtro de local.
- **Vaga** (`jobPosts[]`):
  - `id`, `title`, `companyName`, `logoUrl`;
  - `publicUrl`, o link público, ex.: `https://job-boards.greenhouse.io/<empresa>/jobs/<id>`;
  - `urlToken`, o identificador da empresa no Greenhouse, o mesmo das empresas acompanhadas;
  - `departmentId`, `viewJobPath`;
  - `firstPublished` (data ISO);
  - `locations` (lista de textos), `workType` (`remote`…);
  - `payRanges`, `summary` e `description`, todos `null` no que foi visto;
  - `viewed`, `appliedAt` e `saved`. **São dados da conta da pessoa e ficam de fora.**
- **Descrição**: o `publicUrl` e o par `urlToken`/`id` levam à API pública do quadro da empresa (spec 031, R2). A
  descrição pode vir de lá, sem a sessão.
- **Login**: sem sessão, a busca leva a `/users/sign_in` (spec 031, R1). Com o login pelo LinkedIn, a aba volta para
  `/dashboard`.

## R3. O que a busca traz para o perfil de teste (scrum, remoto)

- **Sem filtro de local, 1ª página** (12 vagas, em ordem de relevância aproximada):
  - 6 têm "Scrum Master" no título;
  - os locais são EUA (Mclean, VA; Harrisburg, PA; Miami, FL; Washington, DC), Reino Unido e "Argentina, Colombia";
  - as outras 6 não têm relação com o cargo (ex.: "Senior .NET Fullstack Engineer").
- **Com local Brasil**: das 39 vagas carregadas (página 1 até a 4), **nenhuma** tem Scrum, Agile ou Delivery Manager no
  título. A busca é aproximada e devolve vagas de tecnologia no Brasil em geral.
- **"agile coach", local Brasil, remoto, até 5 dias** (`date_posted=past_five_days`, busca refeita pela pessoa): 1 vaga, sem relação com o cargo ("Senior Full Stack Engineer").
- **Conclusão**:
  - hoje, na área nacional, o filtro de cargo e o de país deixariam pouca ou nenhuma vaga deste perfil;
  - as vagas de Scrum Master que aparecem são, na maioria, remotas restritas a outros países;
  - elas só serviriam com a busca internacional ligada e com esses países escolhidos.
- Empresas com vagas remotas no Brasil vistas na busca: Nortal, NTT DATA, BEES/AB InBev, Ília, Encora, Exadel, Grupo
  QuintoAndar, Clara e CarOnSale. Elas podem ser acompanhadas pela API pública, sem login, e as vagas ágeis futuras
  delas entram em toda busca.

## R4. O que já existe na ferramenta

- **Janela e leitura logada**:
  - `navegador.py`: `abrir`, `abrir_para_leitura` (aba em segundo plano), `Aba.ir`, `avaliar`, `frente`, `minimizar`
    e `fechar_aba`;
  - `contas/`: `buscar_json` (fetch de dentro da aba, os cookies não saem do navegador) e `PortalErro(login=)`;
  - `dash/sincronia.py`: `_esperar_login` (180 s, passo de 3 s, só pelo endereço da aba).
- **A busca da página roda no próprio servidor**: `dash/buscador.py` chama `vagas.executar` numa thread, então a
  janela fica ao alcance. A busca pelo terminal (`vagas.py buscar`) não fala com o navegador.
- **Empresas acompanhadas** (`fontes/ats.py`):
  - id `greenhouse-<empresa>-<id da vaga>` (`_comum.ident`);
  - `ats.ler(url)` lê a vaga pela API pública;
  - `filtros.aberta_ao_pais` é a regra de país da área nacional;
  - o "Acompanhar empresa" usa o campo `ats` da vaga.
- **Espera**: `_comum.gravar_espera` e `ler_espera`; a busca pergunta antes de seguir sem um portal em espera
  (`vagas.fontes_em_espera`).
- **Perfil da janela compartilhado**: as contas conectadas, a candidatura assistida e os portais com login usam o mesmo
  perfil (`.cache/navegador`). Hoje, desconectar a última conta apaga o perfil inteiro.

## Decisões técnicas (plano, 2026-11-01)

- **D1. Dois módulos.**
  - `fontes/mygreenhouse.py` é a fonte, no contrato de `fontes/__init__.py`: filtros, junção pelo id e relatório de
    graça.
  - `fontes/_sessao.py` concentra as regras comuns da área: contexto da página, aba, espera de login, estado da
    conexão e pedido JSON de dentro da aba.

  Um portal novo é um módulo a mais. Alternativa rejeitada: um módulo em `contas/`, porque ele devolve candidaturas e
  roda fora da busca.
- **D2. Só na página.**
  - O buscador da página abre o contexto `_sessao.na_pagina(esperar_login=…)` em volta de `vagas.executar`.
  - Fora dele (terminal, chat), `buscar` devolve só o aviso "só pelo botão Buscar da página", sem abrir a janela.
  - `vagas.fontes_em_espera` ignora as fontes com login fora da página, para não perguntar por um portal que não vai
    rodar.
- **D3. Pedido.**
  - É o JSON do Inertia: o mesmo endereço da busca com os cabeçalhos `X-Inertia`, por fetch de dentro da aba.
  - A versão vem do `data-page` da primeira carga da aba em cada busca.
  - Resposta 409 (versão nova do site): recarrega a aba uma vez. Se repetir, a resposta é "o portal mudou".
- **D4. Consulta.**
  - Área nacional, grupo remoto, só com país conhecido (`PAISES`: Brasil, com os parâmetros de R2). Os grupos do país e
    da cidade não fazem pedido.
  - Cada cargo vai como `query`, sem aspas, com `work_type[]=remote`.
  - Vai `date_posted=past_five_days` quando a janela for de até 120 h.
  - Até 3 páginas, ou até `moreResultsAvailable: false`.
  - Busca internacional ligada: só a consulta global, sem local.
  - O título filtra pelo cargo (`_comum`), porque a busca do portal é aproximada (R3).
- **D5. Vaga.**
  - id `greenhouse-<urlToken>-<id>`, o mesmo das empresas acompanhadas, então junta sozinho;
  - plataforma "MyGreenhouse", `ats: "greenhouse"`, `url = publicUrl`;
  - `viewed`, `appliedAt` e `saved` são descartados na leitura.
- **D6. Descrição.** Vem pela API pública do quadro (`ats.ler`), sem a sessão, só das vagas do relatório, até 30 por
  busca.
- **D7. Login caído.**
  - `logado(url)` decide só pelo endereço; nenhuma leitura de página de outro domínio.
  - A espera é de 180 s, com passo de 3 s, pelo callback do buscador (situação "aguardando_login" no estado da busca).
  - Cancelar a busca interrompe a espera.
- **D8. Parada.**
  - 403, 429, 503 ou resposta de desafio: 24 h de espera (`.cache/mygreenhouse-espera.json`).
  - Captcha visível na carga: para nesta busca e traz a janela para a frente, sem espera.
  - Resposta sem `props.jobPosts`: "o portal mudou".
- **D9. Conexão.**
  - Estado próprio em `.cache/portais-login.json`.
  - Desconectar apaga as origens do portal e as do login por outro serviço (LinkedIn), que nada mais na ferramenta usa.
  - O perfil inteiro só é apagado se não sobrar nenhum portal conectado, somando contas e portais com login. O
    Desconectar das contas passa a considerar os portais com login.
- **D10. Ligar.**
  - `"mygreenhouse"` entra na lista `fontes` do config, como a FullStack.
  - Fica em `filtros.FONTES_LOGIN`, fora de `FONTES_PADRAO`.
  - A página pede a confirmação do aviso antes de ligar.
- **D11. Pausa.** De 3 a 7 s entre os pedidos à lista (`MYGREENHOUSE_PAUSA`, de 3 a 60 s). A carga da página conta
  como um pedido. Cerca de 13 pedidos por busca com 4 cargos, perto de 1 minuto.
