# Research: Empresas acompanhadas na busca nacional

**Data**: 2026-10-25. Pesquisa do Greenhouse como portal (roteiro `docs/novo-portal.md`, seção 1), feita junto com a da
spec 030, e leitura do código que já existe ("Empresas acompanhadas", spec 009). Foram 15 pedidos web, espaçados, só à
parte pública e sem login.

## R1. Greenhouse como portal: barrado

- **Busca entre empresas: só com login.** A única busca que junta as empresas é o MyGreenhouse Jobs
  (support.greenhouse.io, artigo "Coming soon: MyGreenhouse Jobs", atualizado em 30/12/2025).
  - Ela mostra "open roles from across all participating Greenhouse customers". Só entram as empresas que ligaram o
    recurso.
  - Sem sessão, `my.greenhouse.io/jobs?query=…` redireciona para `/jobs/search`, depois para `/` e por fim para
    `/users/sign_in`.
  - Não há API documentada para esse recurso.
- **Pelo roteiro, a busca que "exige login" barra o portal.** Login guardado no `.env` ou feito pela pessoa na janela
  da ferramenta exigiria emenda da constituição:
  - a "Conta conectada" cobre só a área da própria pessoa;
  - a credencial do `.env` serve só à candidatura assistida.

  A pessoa escolheu, em 25/10/2026, melhorar as empresas acompanhadas em vez disso.
- **Termos**: `greenhouse.com/legal` só traz documentos para clientes. Não há termos para visitantes nem cláusula sobre
  robôs. Os termos do MyGreenhouse não foram localizados.

## R2. API pública do quadro de vagas (o que a ferramenta já usa)

- **Endereço**: `https://boards-api.greenhouse.io/v1/boards/{empresa}/jobs` (com `content=true` traz a descrição).
  Documentação em `docs.greenhouse.io/job-board.html`, onde se lê: "Job Board data is publicly available, so
  authentication is not required for any GET endpoints."
- **Por empresa**: não há busca entre empresas, filtro na URL nem paginação. A lista vem inteira (GitLab: 239 vagas,
  169 KB sem descrição).
- **Local**: texto livre, como "Remote, Brazil" ou "Remote, Brazil; Remote, Mexico; Remote, United States".
- **Página da vaga**: sem JSON-LD `JobPosting` (amostra do GitLab). A ferramenta lê a vaga pela API (`ats.ler`).
- **robots.txt**:
  - `job-boards.greenhouse.io` sem regras;
  - `boards.greenhouse.io` e `boards-api.greenhouse.io` só fecham `/embed/`.
- **Limites**: a documentação não fala deles. Na frente do serviço há CloudFront e um firewall (Signal Sciences), que
  costuma responder 403 ou 429. Não foi visto.
- **Lever e Ashby**: APIs públicas equivalentes, já usadas desde a spec 009.

## R3. O que já existe na ferramenta

- **Fonte `fontes/ats.py`**: `PLATAFORMA = "Empresas acompanhadas"`, com `AREAS = ("internacional",)` e
  `POR_PAIS = False`.
  - Roda só na consulta internacional global, e só com a busca internacional ligada (`vagas.fontes_da_busca`).
  - Usa os cargos da área internacional.
  - Uma lista por empresa por busca (`_comum.lembrar`), filtrada pelo título, pela janela e pelo remoto.
- **Lista**: `config.json` → `internacional.empresas`, uma lista de `{sistema, id, nome, url}`, com no máximo 50
  (`filtros.MAX_EMPRESAS`).
  - O `filtros._empresas` valida pelo `ats.reconhecer`.
  - A página edita a lista no painel da busca internacional (`SearchFiltersModal.tsx`, seção "Empresas que você
    acompanha"), e o front tem o `configApi.empresaDoLink`.
- **Bloqueio**: o `_comum.baixar` faz uma nova tentativa no 429 (espera de 5 a 60 s). Qualquer outro erro vale só para
  aquela empresa, e a busca segue para as próximas, todas do mesmo sistema. Isso foge da regra "parar no primeiro
  bloqueio, sem nova tentativa".
- **Área da vaga**: `filtros.area_da_vaga` usa a consulta que achou a vaga. Achada por consulta nacional, a vaga é
  nacional.
- **Adicionar Vaga**: link de vaga do Greenhouse, do Lever ou do Ashby já é lido pela API (`link._ler_ats`), com o id
  da busca.
- **Detalhe da vaga**: as vagas dessas fontes trazem `ats`. As de outros portais (Indeed, LinkedIn) podem ter o
  `url_candidatura` num desses sistemas, e o front já põe a etiqueta pelo link de candidatura.

## R4. Como descobrir empresas

Não há diretório oficial de empresas que usam Greenhouse, Lever ou Ashby. Raspadores de terceiros (Apify, GitHub)
ficam fora: a constituição não permite.

O caminho que respeita as regras é a pessoa achar a empresa numa vaga: pelo link colado no Adicionar Vaga ou pelo link
de candidatura de uma vaga que veio de outro portal.

## Decisões técnicas (plano, 25/10/2026)

### D1. Onde fica a lista
- **Decisão**: `config.json` → `empresas`, no nível de cima.
  - `efetivos` lê `empresas` ou, sem ela, `internacional.empresas`.
  - `validar` usa `empresas` do pedido quando a chave vem, e `internacional.empresas` só quando ela não vem.
  - `salvar` grava só em cima.
- **Motivo**: a lista vale para as duas áreas, e o formato antigo continua lido (restrição técnica da constituição).
- **Alternativa**: manter a lista em `internacional` com uma caixa "também na nacional". A pessoa preferiu o painel
  principal.

### D2. Áreas e consultas da fonte
- **Decisão**: `AREAS = ("nacional", "internacional")`, `POR_PAIS = True` e `GLOBAL = True`. O `buscar` atende:
  - `remoto` e `pais`: vagas abertas ao país;
  - `local`: as da cidade;
  - global: como hoje.

  As consultas `internacional:<país>` e `mudanca:<país>` devolvem `([], [])` sem pedido. As listas ficam em
  `_comum.lembrar`, então nacional e internacional usam o mesmo download.
- **Alternativa**: uma fonte nova só para a nacional. Seriam dois módulos com a mesma API e dois downloads.

### D3. O que é "aberta ao país"
- **Decisão**: uma função pública, `filtros.aberta_ao_pais(texto, pais)`, sobre `_lugares` e `_inclui` da elegibilidade.
  - Vale se algum lugar citado no local é o país, uma região que o inclui (`PAISES_DA_REGIAO`) ou "mundo todo"
    (Anywhere, Worldwide, Global).
  - "Remote" sozinho não cita lugar e não vale.
- **Consulta da cidade**: vaga não remota cujo local cita a cidade da pessoa ou o nome do estado (`_comum.UFS`), e
  nenhum outro país.
- **Consulta do país** (sem cidade, com híbrido ou presencial): remotas abertas ao país mais as não remotas no país.

### D4. Bloqueio por sistema
- **Decisão**:
  - `_comum.baixar(..., nova_tentativa=True)`: o `ats` passa `False`;
  - `FonteErro(motivo, repetido=False, codigo=None)`;
  - no `ats`, um `_estado["bloqueados"]` (zerado em `_comum.AO_ESQUECER`) guarda os sistemas parados;
  - 403 ou 429 põe o sistema na lista, e as empresas dele não fazem pedido até o fim da busca;
  - aviso: "o <Sistema> limitou as consultas (código N); as outras empresas dele ficam para a próxima busca".
- **Motivo**: o roteiro pede parada no primeiro bloqueio, sem nova tentativa. São APIs oficiais, uma por empresa,
  então não há espera entre buscas (spec, Assumptions).
- **Alternativa**: espera de horas, como o InfoJobs. Seria exagerada para API oficial e prenderia o sistema inteiro
  por um erro de uma empresa.

### D5. 404
O aviso é: "a página de vagas de <empresa> no <Sistema> não existe mais (a empresa pode ter mudado de sistema ou de
nome); remova ou troque o link". Ele vale só para a empresa.

### D6. Acompanhar
- **API**:
  - `POST /api/empresas` com `{url}` reconhece o link pelo `ats.reconhecer`, deduplica (sistema e id, sem diferença
    de maiúsculas), respeita o máximo de 50 e grava pelo `filtros.acompanhar`, que mexe só na chave `empresas` do
    config. Devolve `{empresa, nova, empresas}`.
  - `GET /api/empresas` devolve `{empresas, maximo}`.
  - No `POST /api/vagas/link`, quando o link é de vaga de um desses sistemas, a resposta ganha
    `empresa: {sistema, id, nome, url, acompanhada}`.
- **Detalhe da vaga**: o front calcula a empresa por `configApi.empresaDoLink(url_candidatura || url)`, que já existe,
  e compara com `GET /api/empresas`.
- **Alternativa**: um campo `empresa_ats` em cada vaga do `GET /api/vagas`. Mexeria na listagem toda por um botão.

### D7. Ordem de entrega
- **Risco**: o front novo manda a lista em `empresas`. Um back-end antigo ignoraria essa chave e gravaria a
  configuração sem a lista.
- **Ordem**: back-end na master antes do push do front para a `frontend-react`. O back-end novo aceita o front antigo
  (D1). O PR #14, que hoje só traz a etiqueta do JobGether, pode entrar antes.

### D8. Lista de desejos
O Greenhouse como portal fica barrado: o MyGreenhouse Jobs exige login. A ideia de conta conectada ou login no `.env`
fica registrada, com o motivo: exigiria emenda e leria uma busca interna sem API documentada.
