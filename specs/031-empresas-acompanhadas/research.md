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
