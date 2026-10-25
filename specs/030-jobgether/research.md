# Research: JobGether na busca de vagas

**Data**: 2026-10-25. Pedidos espaçados, só à parte pública, sem login nem cookies:
- robots.txt;
- documentação da API, `/.well-known/api-catalog` e `/.well-known/ai-plugin.json`;
- três buscas pela API;
- lista de ferramentas do `/mcp`;
- a home e uma página de vaga;
- os termos de uso, lidos duas vezes.

Uma primeira pesquisa, de 24/10/2026, já tinha achado a API e o robots.txt.

## R1. Termos de uso

Fonte: `https://jobgether.com/terms-of-use`, "Last update on 7th of September 2026". O link veio dos avisos legais
(`/legal-notices`), apontados pelo `legal_info_url` do manifesto `/.well-known/ai-plugin.json`. A empresa é a
Jobgether SRL, de Bruxelas. Valem a lei belga e o foro de Bruxelas (seção 12). `/terms` dá 404.

Trechos literais, conferidos no original:

- **4.5 "Your undertakings"**: "You also agree to (non-exhaustive list): […] refrain from accessing the Platform or
  extracting its content by automated means (bots, scrapers, crawlers) and from using Platform content to train,
  fine-tune or operate machine-learning models; […] refrain from any action that imposes a disproportionate burden
  on the Platform's infrastructure […]; refrain from selling, monetising or conceding to a third party all or part of
  the access to the Platform or the information contained therein".
- **9 "Intellectual property"**: "You may not store or record (except to the extent necessary for the use of the
  Platform), reproduce, modify, translate, disseminate to the public, distribute, rent, sell or transfer to third
  parties any of the elements of the Platform or any of the data or information made available on the Platform, nor
  use them in any way without our prior written authorisation." e "All acts of extraction, data mining, scraping and
  similar acts with respect to the elements (or certain elements) of the Platform are strictly prohibited."
- **6.3**: o "AI Auto-Apply" do plano Premium "complete[s] and submit[s] applications in your name". É do próprio
  JobGether e fica fora da ferramenta.

Os termos não falam da API.

**Na API, o JobGether diz o contrário.** A documentação (`/astroapi/ai/jobs/docs`) diz "Intended for AI
agents/assistants answering user job-search queries", sem chave e sem condições de uso. O manifesto declara
`"auth": {"type": "none"}`, e o robots.txt traz `Content-Signal: search=yes, ai-input=yes, ai-train=no`.

**Decisão da pessoa (25/10/2026)**: usar a API mesmo com os termos (spec, Contexto).

## R2. robots.txt e site

- `Crawl-delay: 2`.
- Liberados: `Allow: /`, `Allow: /astroapi/ai/jobs.json` e `Allow: /astroapi/ai/jobs.json?*`.
- Bloqueados: `Disallow: /*?*`, `/proxy/*?*`, `/_server-islands/` e `/active-offers`.
- O `/api/v1/jobs` com query string cai no `Disallow: /*?*`. Por POST, com corpo JSON, fica livre.
- A página da vaga (`/offer/<id>-<slug>`) é liberada.
- **Páginas do site**: respondem 403 do Cloudflare a quem não é navegador, inclusive ao agente da ferramenta
  (`_comum.AGENTE`), já no primeiro pedido.
- **Uma tentativa negada**: nesta pesquisa, a página foi pedida com agente de navegador, e o modo automático do
  assistente negou como "Bot Check Circumvention". Imitar navegador fica fora da ferramenta: os termos (4.5) também
  vetam.

## R3. API oficial

**Endpoint**: `POST https://jobgether.com/api/v1/jobs`, com corpo JSON (`Content-Type: application/json`).
- É a superfície estável e versionada. O GET responde igual.
- O alias `/astroapi/ai/jobs.json` também responde.
- `/astroapi/ai/jobs`, sem `.json`, está descontinuado desde 28/09/2026.
- Não precisa de chave.

Exemplo que respondeu 200:

```
{"keyword": "project manager", "locations": ["brazil"], "sort": "date", "limit": 25}
```

**Parâmetros**:

| Parâmetro | O quê |
|---|---|
| `keyword` | busca em título, função, habilidades, empresa, contrato e idioma |
| `locations` | slugs de país, continente ou cidade (`brazil`, `europe`, `anywhere`); não há lista na doc |
| `jobReferences`, `industries` | slugs de função e de setor |
| `contractType` | `full-time`, `part-time`, `fixed-term`, `freelance`, `internships` |
| `experience` | `entry-level-graduate`, `junior-1-2-years`, `mid-level-2-5-years`, `senior-5-10-years`, `expert-10-years` |
| `remoteType` | `full-remote`, `remote-first`, `hybrid`; o padrão é Full Remote |
| `includeHybrid` | inclui as híbridas |
| `salaryMin`, `salaryMax`, `currency` | faixa de salário |
| `sort` | `relevance` (padrão) ou `date` |
| `page` | de 1 a 10 |
| `limit` | até 25 |

- **Não há filtro de data**: a janela de tempo se aplica com `sort: "date"` e o `postedAt`.
- No máximo 250 vagas por consulta.
- Um slug ou valor desconhecido dá 400 (`invalid_parameter`, com `field` e `allowedValues`).
- O formato dos erros segue a RFC 9457 (`application/problem+json`, campo `code`). Erros vistos: 400
  `invalid_parameter` e `invalid_body`, 404 `not_found`, 500 `internal_error` e 504 `timeout` ("Retry with a narrower
  query").

**Resposta**: `jobs`, `pagination` (`page`, `limit`, `hasMore`), `browseOnSiteUrl` (link para pessoas) e `docs`.

**Campos de cada vaga**:

| Campo | Exemplo ou observação |
|---|---|
| `id` | ObjectId de 24 hex; muda na republicação (R5) |
| `title`, `company` | |
| `url` | página no JobGether |
| `location` | texto com países e regiões, ex.: "South America, Latin America, Brazil" |
| `remote` | "Full Remote" em todas as amostras |
| `contractType` | "Full time" |
| `experience` | "Senior (5-10 years)", às vezes vazio |
| `salaryRange` | só quando informado, ex.: "65000-70000 USD"; sem período (ano ou mês) |
| `jobFunctions` | lista |
| `postedAt` | ISO 8601 em UTC |

**A descrição não vem na lista.**

**Chamadas reais**:
- "project manager" no Brasil (`locations: ["brazil"]`, por data): 25 vagas em 14 dias, e `hasMore`.
  - O filtro de local é hierárquico. Vieram 12 com Brasil, 7 "Anywhere" e 6 com "Latin America" ou continentes.
- "gerente de projetos" em `anywhere`: 0 vagas.
- "project manager" sem local: 25 vagas em cerca de 24 horas, quase todas restritas aos EUA ou ao Canadá.
- **Idioma**: as 50 vagas estão em inglês.
- **Busca ampla**: "project manager" trouxe "NetSuite Consultant". O filtro pelo título continua necessário.
- **Detalhes**:
  - há vagas repetidas com ids diferentes;
  - a empresa às vezes é um agregador ("Indeed.com");
  - um título veio com caractere quebrado.

## R4. Página da vaga

- Endereço: `https://jobgether.com/offer/<id de 24 hex>-<slug-do-titulo>`.
- Tem JSON-LD `JobPosting` (lido pelo WebFetch):
  - `description` em HTML;
  - `datePosted` no formato do `Date` do JavaScript, não ISO;
  - `validThrough`, `employmentType`, `hiringOrganization`, `jobLocationType: "TELECOMMUTE"`;
  - `applicantLocationRequirements` com centenas de países.
- **A ferramenta não consegue ler a página**: ela responde 403 ao agente da ferramenta (R2). A descrição fica sem
  fonte automática.

## R5. Identificador estável

Os dois ids são ObjectId, que trazem a data de criação nos 8 primeiros hex:
- o `id` da API nasce no `postedAt`;
- o id da URL nasce na publicação original.

Em 3 das 50 vagas os dois diferiam. Exemplo: o `id` da API era de 20/10, e o id da URL, de 15/08, igual ao
`datePosted` da página. É uma vaga republicada, que volta com `id` e `postedAt` novos. **O id estável é o da URL.**
Ainda não foi conferido entre buscas de dias diferentes.

## R6. Limites e bloqueio

- **API**:
  - cabeçalhos `RateLimit-Limit: 60` e `RateLimit-Policy: "ai-jobs";q=60;w=60` (60 pedidos por minuto);
  - o 429 não foi visto nem aparece na doc.
- **Site**: 403 do Cloudflare para quem não é navegador.

## R7. MCP e candidatura

- **MCP**:
  - `POST /mcp` (JSON-RPC) tem uma ferramenta, `searchJobs`, com os mesmos parâmetros da API;
  - limites de 60 pedidos em 10 s e 240 por minuto;
  - a ferramenta usa a API, sem MCP.
- **Candidatura**:
  - o "APPLY" leva ao sistema da empresa (numa amostra, www1.jobdiva.com), sem login;
  - ao lado fica o "AUTO APPLY" pago do JobGether.
  - Pelos termos (4.5), `jobgether.com` deve entrar nos domínios bloqueados da candidatura assistida (spec 027).

## Respostas à tabela do roteiro

| Pergunta | Resposta |
|---|---|
| API ou MCP oficial? Chave? | Sim, `/api/v1/jobs` e `/mcp`; sem chave |
| robots.txt permite? | Sim, por POST no `/api/v1/jobs`; página da vaga liberada |
| Termos proíbem? | **Sim** (4.5 e 9); entra por decisão da pessoa |
| Busca sem login? | Sim, pela API; as páginas dão 403 à ferramenta |
| Formato | JSON |
| Filtros na consulta | keyword, locations, contractType, experience, remoteType, includeHybrid, salário, sort=date; sem data |
| Paginação | `page` de 1 a 10, `limit` até 25, `hasMore` |
| JobPosting | Sim, mas a página não abre para a ferramenta |
| Id estável | O da URL |
| Como limita | 60 pedidos/min na API (429 não visto); 403 no site |

## Decisões técnicas (plano, 25/10/2026)

Mais dois pedidos à API no plano, para os nomes de país:
- um local inválido responde 400 e manda ver a doc, sem lista;
- `united-states` e `united-kingdom` são aceitos;
- `czech-republic` é recusado.

### D1. POST dentro da fonte
- **Decisão**: `fontes/jobgether.py` faz o POST com `urllib` (`_baixar(corpo)`), com o agente da ferramenta, sem
  cookies e sem nova tentativa.
- **Motivo**: o robots.txt bloqueia `/*?*`, e o `_comum.baixar` só faz GET, com uma nova tentativa no 429 que o roteiro
  não quer aqui.
- **Alternativas**:
  - GET no alias `/astroapi/ai/jobs.json?…`, liberado no robots: é um alias, não a superfície versionada;
  - um `_comum.enviar_json`: só uma fonte usaria.

### D2. Respostas da API

| Resposta | O que a ferramenta faz |
|---|---|
| 200 | lê `jobs` e `pagination.hasMore` |
| 403 ou 429 | bloqueio: espera de 24 h, sem nova tentativa |
| 400 com `field: "locations"` | aviso "o JobGether não reconhece o local <x>", uma vez por busca; as outras consultas seguem |
| outro 400, 404, 500 ou 504 | erro só daquela consulta, sem nova tentativa |
| resposta fora do formato | "não consegui ler as vagas do JobGether" |

### D3. Local de cada consulta
- **Nacional**, nas consultas remota e do país: o país da pessoa.
- **Internacional**: o país da consulta, ou `anywhere` na global.
- **Nome do país**: o nome do jobspy (`filtros.PAISES`), com hífen no lugar do espaço. As exceções ficam numa tabela
  (`usa` → `united-states`, `uk` → `united-kingdom`).
- Na consulta do país, quando a pessoa aceita híbrido, vai `includeHybrid: true`.
- As consultas da cidade e de mudança não fazem pedido.

### D4. Páginas e janela
- `sort: "date"` e `limit: 25`; a próxima página só quando `hasMore` é verdadeiro e a vaga mais antiga da página ainda
  está na janela.
- No máximo 3 páginas (`MAX_PAGINAS`).
- A mesma consulta (cargo, local, híbrido) é lida uma vez por busca (`_estado["listas"]`).

### D5. Id e data
- **Id**: `jobgether-<24 hex>` tirado da `url` (`/offer/<id>-<slug>`); sem ele, o `id` da API.
- **Data**: `publicada_em` vem do `postedAt` (`_comum.data_iso`). A data embutida no id da URL não é usada, porque é
  inferida e não está documentada.

### D6. Campos

| Campo da vaga | De onde vem |
|---|---|
| `local` | "Remoto (<location>)" |
| `restricao_local` | `location` (curto) |
| `remoto` | sempre verdadeiro |
| `modelo_trabalho` | "hibrido" se `remote` falar em hybrid; senão "remoto" |
| `salario` e `moeda` | `salaryRange` ("65000-70000 USD") pelo `_comum.salario`, sem período |
| `tipo` | `contractType` em português |
| `tipo_emprego` | só quando é inequívoco: part time → meio_periodo, internships → estagio, fixed term → temporario, freelance → pj |
| `url_candidatura` | `None` (a candidatura sai da página no JobGether) |
| `descricao` | vazia |

"Full time" fica só em `tipo`, porque tempo integral no exterior não é CLT.

### D7. Adicionar Vaga
- **Decisão**: `link.ler` reconhece o link e levanta `LinkErro` com `{plataforma: "JobGether", url}`, sem pedido. O
  `banco.criar_manual` usa `jobgether.id_do_link(url)` como id; se a vaga já existe, devolve a que existe.
- **Alternativa**: achar a vaga pela API com as palavras do endereço. É incerta e gasta um pedido a cada link.

### D8. Emenda da constituição
Seção "Termos contrários" no princípio VI, versão 4.1.0 (texto no plano). A emenda é escrita para não desligar
InfoJobs e Nerdin, decididos nas suas specs.
