# Research: FullStack (talent.fullstack.com) na busca de vagas

**Data**: 2026-10-30. Pedidos espaçados, só à parte pública e sem login: robots.txt, o código da página, quatro pedidos
à API que a própria página usa e os termos de uso do fullstack.com.

## R1. Termos de uso

Fonte: `https://www.fullstack.com/website-terms-of-use` ("Last Modified: June 6, 2023"), lido em 30/10/2026. Define o
"Website" como "FullStack.com, including any content, functionality, and services offered on or through FullStack.com".
Não cita o talent.fullstack.com, mas nada o exclui, e a página de carreiras do fullstack.com
(`/talent/for-talent`) manda para `talent.fullstack.com/jobs`. Não há termos próprios no talent.fullstack.com.

Trechos literais (seção "Prohibited Uses"):

- "Use any robot, spider, or other automatic device, process, or means to access the Website for any purpose,
  including monitoring or copying any of the material on the Website."
- "Use any manual process to monitor or copy any of the material on the Website, or for any other purpose not
  expressly authorized in these Terms of Use, without our prior written consent."

E em "Intellectual Property Rights": "You must not reproduce, distribute, modify, create derivative works of, publicly
display, publicly perform, republish, download, store, or transmit any of the material on our Website, except as
follows: […]".

**Conclusão**: os termos proíbem acesso automatizado. Vale a constituição, princípio VI, "Termos contrários": só por
decisão explícita da pessoa registrada na spec, com os termos resumidos no painel e, sendo portal novo, desligado por
padrão.

## R2. robots.txt e indexação

- `talent.fullstack.com/robots.txt` não existe: o endereço devolve a própria página do app (HTML com `<div id="root">`).
- A página tem `<meta name="robots" content="noindex">` (pede para não indexar; não fala de leitura).

## R3. Formato

- **Página**: app em JavaScript ("FullStack Connect"); o HTML não traz as vagas.
- **API que a página usa** (base `https://api-v1.fullstack.com/api/`, vista no código da página; não é documentada
  para terceiros e não há API oficial para candidatos):
  - Lista: `GET /job-postings/public?page=N&take=30` — sem login. `take=5` e `take=10` deram 400 ("Invalid take
    value."); a página usa 30.
  - Filtro por país: `filter=countryId=<uuid>`. Brasil: `1ae07c37-d911-413f-9160-8cd2a5d93257`.
  - Resposta: `{"data": [...], "meta": {"page", "take", "filteredCount", "pageCount", "hasNextPage", …}}`.
  - Detalhe: `GET /job-postings/<id>` — sem login; traz os mesmos campos e `sections` (descrição em HTML, com
    `title` e `body`), `questions` e `skills`.
- **Campos de cada publicação**: `id` (da publicação), `jobId` (da vaga), `jobTitle` ("Senior .NET Engineer - Remote
  - Latin America"), `city`, `state`, `region` (país), `regionGroup` ("Latam", "USA"), `linkedInWorkplaceType`
  ("Remote", "Hybrid"), `linkedInJobType` ("FULL_TIME"…), `linkedInSeniority`, `createdAt`, `skillsNames`,
  `departmentName`, `trackName`.
- **Dado pessoal na resposta**: `ownerEmail` (e-mail do recrutador) — descartado pela ferramenta.
- **Volume (30/10/2026)**: 2.806 publicações no mundo; 264 no Brasil (9 páginas de 30).
- **Repetição por cidade**: a mesma vaga (`jobId`) é publicada em várias cidades e países. Na primeira página do
  Brasil, 30 publicações eram 16 vagas. Todas "Remote – Latin America".
- **Link da vaga**: rota `talent.fullstack.com/jobs/<id da publicação>` (e `/jobs/<id>/apply` para se candidatar).
- **Ordenação**: a página passa `order` e `orderBy`; a ordem por data (`createdAt`) fica conferida na implementação.

## R4. O que já existe na ferramenta

- O Adicionar Vaga não reconhece `talent.fullstack.com`; a página não tem HTML de vaga nem JSON-LD.
- A candidatura assistida (spec 027) teve a prova real em `talent.fullstack.com` em 27/10/2026; hoje o domínio está
  liberado. Com os termos de R1, a regra seguida no JobGether (spec 030, FR-010) seria bloquear o domínio.
- Molde de portal com espera: `fontes/jobgether.py` (JSON, 24 horas de espera) e `fontes/infojobs.py`.

## R5. Bloqueio

Nenhum bloqueio nos pedidos da pesquisa. Sem login, a API respondeu 200 (e 400 para `take` inválido; 404 sem o
prefixo `/api/`). O comportamento ao limitar não foi observado; vale a regra comum: 401, 403, 429 e 503 viram bloqueio.

## Decisões técnicas (plano, 30/10/2026)

- **D1. Os pedidos da própria página.** Decisão: `GET /api/job-postings/public` e `GET /api/job-postings/<id>`, com
  `Accept: application/json`, sem login e sem cookies. Motivo: não há API oficial, e a página só mostra as vagas por
  esses pedidos. Alternativa rejeitada: ler o HTML (vem vazio).
- **D2. Só o Brasil.** Decisão: o filtro de país usa o identificador do Brasil, visto na pesquisa; outro país da
  pessoa não faz pedido. Motivo: o único identificador conhecido, e a área nacional da ferramenta é o Brasil na prática
  (como o Vagas.com). Outro país fica para quando alguém pedir.
- **D3. Ordem por data.** Proposta: pedir `orderBy=createdAt&order=DESC` e parar na janela. **Conferido em
  30/10/2026**: a API ignora essa ordem (as datas vêm misturadas), e a própria página não ordena por data (as colunas
  ordenáveis são departamento, trilha, país, cidade, habilidades e cargo; `orderBy` vazio). Decisão: ler até
  `MAX_PAGINAS` (10; o Brasil tinha 9) e filtrar a janela aqui. `take` só aceita 30 (5, 10, 50 e 100 dão 400).
- **D4. Uma lista por busca.** Decisão: a lista do país é lida uma vez e serve a todos os cargos. Motivo: a API não
  tem busca por palavra documentada, e a lista do Brasil é pequena (9 páginas).
- **D5. Uma vaga por `jobId`.** Decisão: as publicações da mesma vaga em várias cidades viram uma; o link é a primeira
  publicação do país. O id `fullstack-<jobId>` não muda quando a FullStack publica a vaga numa cidade nova.
- **D6. Adicionar Vaga com um pedido.** Decisão: o link traz o id da publicação, e o id da busca (`jobId`) só vem do
  detalhe; `fullstack.ler` faz esse pedido (fora da espera). Na espera, a pessoa completa à mão, e a vaga fica com o
  id comum de link (pode repetir quando a busca a trouxer depois; caso raro).
- **D7. Bloqueio.** Decisão: 401, 403, 429 e 503 param a FullStack e gravam 24 horas de espera, como o JobGether.
  Outros erros (400, 404, 500) valem só para aquele pedido.
