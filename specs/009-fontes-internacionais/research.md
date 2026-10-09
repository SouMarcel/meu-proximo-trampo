# Research: Fontes internacionais e elegibilidade

## 1. As fontes

Todas públicas, sem login e sem chave (conferidas em 06/10/2026). Formato exato de cada resposta
conferido de novo no início da implementação, com **uma consulta real por fonte** (gravada em
`tests/dados/` para os testes, sem dados pessoais).

| Fonte | Endereço público | Como consultar | Campos úteis |
|---|---|---|---|
| Remotive | `remotive.com/api/remote-jobs` | uma lista recente por busca, filtrada pelos cargos aqui | `candidate_required_location`, `salary`, `job_type`, `url`, `description` (HTML) |
| Himalayas | `himalayas.app/jobs/api` (paginado) | uma página recente por busca, filtrada aqui | `locationRestrictions`, `timezoneRestrictions`, `minSalary`/`maxSalary`, `currency`, `applicationLink`, `description` |
| RemoteOK | `remoteok.com/api` (o item 0 é o aviso legal) | uma lista por busca, filtrada aqui | `location`, `salary_min`/`salary_max`, `apply_url`, `url`, `tags`, `description` |
| Jobicy | `jobicy.com/api/v2/remote-jobs` | por cargo (`tag`), poucas | `jobGeo`, `annualSalaryMin/Max`, `salaryCurrency`, `url`, `jobDescription` |
| We Work Remotely | RSS `weworkremotely.com/remote-jobs.rss` | um RSS por busca, filtrado aqui | `region`, `type`, `link`, `description` |
| Get on Board | `getonbrd.com/api/v0/search/jobs` | por cargo (`query`) | `remote`, `remote_modality`, `countries`, `min_salary`/`max_salary`, `lang`, `description` |
| Greenhouse | `boards-api.greenhouse.io/v1/boards/<empresa>/jobs?content=true` | uma por empresa por busca | `location.name`, `absolute_url`, `content` |
| Lever | `api.lever.co/v0/postings/<empresa>?mode=json` | uma por empresa por busca | `categories.location`, `workplaceType`, `hostedUrl`, `applyUrl`, `salaryRange`, `descriptionPlain` + `lists` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/<empresa>?includeCompensation=true` | uma por empresa por busca | `location`, `isRemote`, `workplaceType`, `jobUrl`, `applyUrl`, `compensation`, `descriptionPlain` |

- **Uma consulta por fonte por busca** (lista recente, filtrada aqui pelos cargos em inglês) nas
  fontes sem busca por termo ou com limite apertado (Remotive, Himalayas, RemoteOK, We Work
  Remotely, empresas); por cargo só em Jobicy e Get on Board. Resultado guardado na memória da busca
  (não consulta de novo para o segundo cargo).
- Filtro pelo cargo: o título contém todas as palavras significativas do cargo (frase exata entre
  aspas, como nos filtros de hoje).
- Descrição: HTML → texto (reaproveita `link.texto_de_html`), até 12.000 caracteres.
- Datas: a janela de publicação vale como nas outras fontes.

## 2. Encaixe nas consultas

- **Decision**: fontes com atributo `POR_PAIS = False` (as novas) rodam numa consulta internacional
  **global** por cargo (`grupo: internacional:global`), e as `POR_PAIS = True` (Indeed) seguem nas
  consultas por país. `filtros.consultas` cria as globais quando a busca internacional está ligada.
  Fontes novas: `AREAS = ("internacional",)`.
- Fontes ligadas: `internacional.fontes` (lista de nomes; vazia por padrão) somada às `fontes` de
  hoje quando a busca internacional está ligada. Empresas: `internacional.empresas`
  (`[{sistema, id, nome, url}]`), normalizadas por `fontes/ats.py reconhecer(url)` na validação.
- Área e país: consulta global → país/região pela restrição da vaga (`pais_do_local`) ou "mundo
  todo".

## 3. Vaga

- Campos novos: `restricao_local` (texto do portal), `ats` (`greenhouse`, `lever`, `ashby`…), `sinais`
  (["Oferece patrocínio de visto", "Oferece relocation"]); `moeda` e `salario` quando a fonte
  informa (a análise da IA continua podendo preencher `moeda`); `url_candidatura` (já existe).

## 4. Elegibilidade sem IA (`filtros.elegibilidade`)

- Entrada: `restricao_local`, título e descrição (normalizados), modelo de trabalho (fonte ou IA).
- **Lê**: países e regiões exigidos (campo do portal + frases como "US only", "must be authorized to
  work in X", "must reside/be based in X", "only candidates in X", "X only"); "não patrocina" ("do not
  sponsor", "unable to sponsor", "no visa sponsorship", "without sponsorship"); "patrocina" ("visa
  sponsorship available", "we sponsor", "will sponsor"); "relocation" ("relocation package/
  assistance/support"); regiões ("LATAM", "Latin America", "Americas", "EMEA", "Europe", "North
  America", "worldwide", "anywhere").
- **Decide** (só para vaga internacional):
  1. Exige país X (autorização ou residência), X não é o país da pessoa e não está em
     `autorizacao_trabalho`: corta, **a não ser que** a vaga patrocine e a pessoa precise
     ("Exige autorização de trabalho nos Estados Unidos e não patrocina visto" / "Só para quem mora em
     X").
  2. Exige região que não inclui o país da pessoa (Europa, América do Norte…) e a pessoa não tem
     autorização num país dela: corta.
  3. Pessoa marcou regiões aceitas e a região da vaga não está entre elas (LATAM ⊂ Américas ⊂ mundo):
     corta.
  4. Presencial ou híbrido no exterior: sem `aceita_mudar` corta; com lista de países e o país fora
     dela, corta.
  5. Frase própria de restrição encontrada: corta citando a frase.
  6. Nada reconhecido: passa.
- **Sinais**: patrocínio, relocation e frases próprias positivas → `sinais`.
- Frases próprias: `internacional.frases_restricao` e `frases_positivas` (texto simples, sem
  diferença de maiúsculas e acento).
- Patrocínio vence restrição quando a pessoa precisa de sponsor e o anúncio diz que patrocina.

## 5. Adicionar Vaga

- `link.py` reconhece Greenhouse (`boards.greenhouse.io/<e>/jobs/<id>`,
  `job-boards.greenhouse.io/…`), Lever (`jobs.lever.co/<e>/<id>`) e Ashby (`jobs.ashbyhq.com/<e>/<id>`)
  e lê pela API pública da vaga; Remotive, Himalayas, RemoteOK, Jobicy, We Work Remotely e Get on
  Board pelos dados estruturados da página (como hoje para outros sites), com a plataforma certa.
  Elegibilidade e sinais aplicados na gravação.

## 6. Respeito aos portais e termos

- Pausa entre consultas como hoje; uma consulta por fonte por busca nas listas; `User-Agent`
  identificando a ferramenta; nunca mais que uma busca por vez (spec 005).
- README: citar a fonte e linkar a vaga original (a página da vaga já mostra a plataforma e o link);
  termos de cada fonte resumidos.

## 7. Página

- Painel internacional: **Fontes** (caixas com o nome e uma linha sobre a fonte), **Empresas que você
  acompanha** (colar o link → reconhecida na gravação; lista com remover), **Frases** (duas caixas de
  texto, uma frase por linha).
- Vaga: sinais como etiqueta verde ("Patrocina visto", "Relocation") na listagem e no detalhe;
  detalhe mostra a restrição do portal, o sistema de candidatura e o botão "Candidatar no <ATS>".

## 8. Testes

- `tests/test_fontes_int.py`: cada fonte com a resposta gravada (normalização, filtro pelo cargo,
  restrição, salário, link); `ats.reconhecer`; consultas globais.
- `tests/test_elegibilidade.py`: conjunto de anúncios com resultados esperados (SC-002, SC-003).
- SC-001: referência do `vagas.py` (specs 005/008) com as fontes novas desligadas.

## 9. Notas da implementação (formato real conferido em 09/10/2026)

Uma consulta real por fonte, gravada em `tests/dados/` (recortada a poucas vagas, e-mails trocados).
Diferenças em relação ao previsto acima:

- **Remotive**: o aviso legal da própria API pede no máximo 4 consultas por dia; a lista recente
  (`limit=300`) é guardada em disco por 6 horas (`.cache/fontes/`, fora do Git) e as vagas chegam com
  24 horas de atraso. Salário em texto livre (`$45-$120/Hour`). Na busca real de 09/10/2026, a lista
  pública veio com só 17 vagas (a Remotive vende uma API completa à parte): fonte de pouco volume.
- **Himalayas**: páginas de 20 com cursor; a busca lê até 3 páginas por busca.
- **Jobicy**: o salário vem em `salaryMin`/`salaryMax`/`salaryCurrency`/`salaryPeriod` (os campos
  `annualSalary*` também são aceitos).
- **Get on Board**: o nome da empresa só vem com `expand=["company"]`; o salário é mensal, em dólar;
  `remote_modality` diz se é remoto de qualquer lugar, remoto só no país, híbrido ou presencial.
- **Remote OK**: parte do texto chega com a acentuação quebrada (UTF-8 lido como Latin-1); a fonte
  conserta.
- **Ashby**: não há endpoint público de uma vaga só; o Adicionar Vaga lê a lista da empresa e pega a
  vaga pelo número.
- **Ids**: o banco aceita até 64 caracteres; slugs longos (Himalayas, Get on Board, We Work Remotely)
  viram o começo do slug mais um resumo dele, estável entre buscas.
- **Modelo de trabalho**: Lever, Ashby e Get on Board informam (remoto, híbrido, presencial) e o dado
  vai para `modelo_trabalho` (a análise da IA pode corrigir). Na vaga do exterior, os modelos do Brasil
  não valem: vale "aceito morar fora" (regra 4).
- **Patrocínio**: a vaga que diz que patrocina visto não é cortada pela exigência de país, mesmo que a
  pessoa não tenha marcado "preciso de sponsor" (quem não tem autorização no país precisaria do visto
  de qualquer jeito; na dúvida, a vaga passa).
- **Consultas remotas**: sem "aceito morar fora", as consultas globais ficam só com as vagas remotas;
  com ele, trazem também as presenciais e híbridas, e a regra 4 confere o país.
- **Correção da spec 008**: o filtro de salário mínimo não lia faixas com travessão
  ("US$ 100.000–150.000/ano"); agora lê.
