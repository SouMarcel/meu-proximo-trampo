# Research: EY (careers.ey.com) na busca de vagas

**Data**: 2026-10-30. Pedidos espaçados, só à parte pública: robots.txt, três buscas, uma página de vaga e os termos
(Declaração Legal do ey.com).

## R1. Termos de uso

O site de carreiras não tem termos próprios; o rodapé aponta para `https://www.ey.com/en_us/legal-and-privacy`, que
leva à Declaração Legal (`/legal-and-privacy/legal-statement`; em português, `/pt_br/legal-and-privacy/legal-statement`).
Ela fala do "ey.com Web site" e não cita o careers.ey.com, que é outro endereço, hospedado na SAP SuccessFactors.

Não há cláusula sobre robôs, crawlers, scraping ou data mining. Trechos literais que tocam no assunto:

- "No part of the materials on this Site, including but not limited to the text, graphics and html code, may be
  reproduced or transmitted in any form, or by any means without EYGM's written permission […]".
- "Any other use is prohibited, including copying, reproducing, republishing, uploading, posting, transmitting, or
  distributing our feeds or podcasts in any way by any means." (só RSS e podcasts)

É a mesma cláusula genérica de reprodução do Vagas.com (spec 029). A ferramenta lê pouco, espaçado, e guarda as vagas
só no computador da pessoa, sem republicar.

## R2. robots.txt

`User-agent: *` bloqueia `/applybutton/`, `/talentcommunity/`, `/emailsubscribe/`, `/services/`, `/preapply/`,
`/error`, `/unsubscribe/` e `/reset/`. A busca (`/ey/search/`) e as vagas (`/ey/job/…`) ficam livres. O RSS do
SuccessFactors fica em `/services/rss/…`, então **não** é usado.

## R3. Formato do site

- **Sistema**: SAP SuccessFactors (Career Site Builder), páginas montadas no servidor, sem login e sem JavaScript
  para a lista.
- **Busca**: `https://careers.ey.com/ey/search/?q=<palavra>&locationsearch=<país>&sortColumn=referencedate&sortDirection=desc`.
  - `locationsearch=Brazil` deu cerca de 200 vagas (última página em `startrow=175`); `q=desenvolvedor` com Brazil, 18.
  - Paginação: `&startrow=25`, `&startrow=50`… (25 por página), com links `paginationItem` e `paginationItemLast`.
  - O cabeçalho oferece ordenação por título e local; `sortColumn=referencedate` foi aceito (ordem diferente da
    alfabética). A ordem por data fica conferida na implementação, pelas datas das páginas das vagas.
- **Lista**: linhas `tr.data-row` com:
  - `a.jobTitle-link` (título e link `/ey/job/<Cidade>-<Título>-<UF>-<CEP>/<número>/`);
  - `span.jobLocation` ("São Paulo JK, SP, BR, 04543-011" e, se houver mais locais, `+15 more…`);
  - **sem data e sem modelo de trabalho** (a terceira coluna vem vazia).
- **Página da vaga**: sem JSON-LD; tem **microdados schema.org** (`itemprop`):
  - `datePosted` ("Thu Oct 22 00:00:00 UTC 2026"), `description`, `hiringOrganization` ("EY");
  - um `jobLocation` com vários `PostalAddress` (`addressLocality`, `addressRegion`, `addressCountry`, `postalCode`),
    um por local.
  - Também há `data-careersite-propertyid` = `title`, `city`, `date` ("22 de out. de 2026") e `description`.
- **Id estável**: o número no fim da URL (`/1450493933/`).
- **Títulos**: muitas vagas do Brasil são "Banco de Talentos" (cadastro sem vaga aberta naquele momento), e algumas
  dizem "Vaga Exclusiva PCD" no título.

## R4. O que já existe na ferramenta

- `fontes/link.extrair_jobposting` lê só JSON-LD; os microdados da EY precisam de um leitor novo (no módulo da EY).
- O Adicionar Vaga não reconhece `careers.ey.com` hoje.
- Molde de portal que lê páginas: `fontes/vagascom.py` (lista com páginas) e `fontes/nerdin.py` (bloqueio sem espera).

## R5. Bloqueio

Nenhum bloqueio nos pedidos da pesquisa (todos 200). O comportamento ao limitar não foi observado; vale a regra comum
(`_comum.baixar_pagina`: 403, 429, 503 e redirecionamento para login viram bloqueio).

## Decisões técnicas (plano, 30/10/2026)

- **D1. Página da vaga dentro da busca.** Decisão: abrir a página das vagas que passaram no filtro do título, para ter
  a data. Motivo: a lista não tem data, e a janela de tempo é um filtro da busca. Alternativa rejeitada: entrar sem
  data e completar na descrição (a janela não valeria, e vagas antigas entrariam na primeira busca).
- **D2. Ordem por data.** Decisão: `sortColumn=referencedate&sortDirection=desc` e parar na primeira vaga mais antiga
  que a janela. A implementação confere, com as datas das páginas, se a ordem é mesmo por data; se não for, lê até o
  limite de páginas de vaga sem a parada antecipada (o resultado é o mesmo, com mais pedidos). **Conferido em
  30/10/2026**: "desenvolvedor" no Brasil, 8 páginas de vaga, datas de 30/10 a 18/10 na ordem da lista (as vagas de
  "Banco de Talentos" aparecem com a data do dia: a EY as republica). `ORDEM_POR_DATA = True`.
- **D3. Memória de datas.** Decisão: `.cache/ey-datas.json` com número, data e locais de cada vaga lida, por 60 dias.
  Motivo: sem saber o que o dashboard já tem, cada busca reabriria as mesmas páginas. Alternativa rejeitada: consultar
  o banco do dashboard dentro da fonte (as fontes não dependem do `dash/`).
- **D4. Microdados na própria fonte.** Decisão: `ey.ler_pagina` lê `itemprop` (datePosted, description, PostalAddress).
  Alternativa rejeitada: generalizar `link.extrair_jobposting` para microdados (só a EY usa hoje).
- **D5. País na URL.** Decisão: `locationsearch` com o nome do país em inglês ("brazil" → "Brazil"; "usa" → "United
  States"; "uk" → "United Kingdom"; os outros com a inicial maiúscula).
- **D6. Bloqueio sem espera.** Decisão: como a Nerdin (fora do resto da busca, com aviso). Motivo: poucos pedidos por
  busca; com a memória de datas, as buscas seguintes pedem ainda menos.
