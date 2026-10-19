# Research: Nerdin na busca de vagas

Sondagem feita em 18 e 19/10/2026, com poucos pedidos espaçados, só à parte pública.

## R1. Como ler as vagas

- **Decision**: ler o HTML de `https://www.nerdin.com.br/vagas.php?busca=<cargo>&pagina=N`.
- **Rationale**: não há API, JSON nem RSS públicos. A lista vem pronta do servidor (Apache/PHP), 20 vagas por
  página, com "Mostrando vagas 21–40 de 150" e "Página 2 de 8", ordenada da mais nova para a mais antiga.
  O `robots.txt` tem `Allow: /` e bloqueia só login, candidatura, cadastro e áreas internas.
- **Alternatives considered**: `sitemap.xml` (traz links, não os dados, e pediria uma consulta por vaga); filtros
  `Cargo=`, `Plataforma=`, `Area=` (são etiquetas fixas do site, não texto livre).

## R2. Qual campo de busca

- **Decision**: `busca` (o campo único "Cargo/Stack/Cidade"), com o cargo sem aspas.
- **Rationale**: `busca_vaga` deu o mesmo resultado que `busca` ("analista de dados": 153 × 149); cargo entre aspas
  zera a lista. Os dois são amplos: "analista de dados" traz "Analista de Suporte", "Product Designer".
- **Consequence**: cada consulta fica só com as vagas cujo título bate com o cargo, por `_comum.bate_cargo` (frase
  exata se o cargo vier entre aspas; senão, todas as palavras significativas no título), como nas fontes do exterior.

## R3. Campos do card

Cada vaga é um `div.vaga-card` com `data-href="vaga_emprego/vaga-<slug>-<número>.php"`:

| Elemento | Exemplo | Uso |
|---|---|---|
| `h3.vaga-titulo` (sem o `span.vaga-nova-badge` "Nova" nem o ícone de urgente) | Desenvolvedor(a) Power BI - Híbrido | `titulo` |
| `p.vaga-resumo-linha` | `CLT • Pleno • Híbrido`, `PJ • Senior • Home Office`, `Junior` | `tipo` (texto), `modelo_trabalho`, `remoto`, `tipo_emprego` |
| `div.vaga-salario-destaque span` | `Salário a combinar`, faixa ou valor | `salario` (vazio se "a combinar" ou ausente) |
| `span.vaga-empresa-nome` | Empresa Exemplo | `empresa` |
| `div.vaga-local-linha span` | `São Paulo • SP`, `Home Office` ou ausente | `local` |
| `time[datetime]` | `2026-10-18T17:03:37-04:00` | `publicada_em` (os 10 primeiros caracteres) |

Modelo: "Home Office" → remoto; "Híbrido" → hibrido; "Presencial" → presencial; sem modelo → não informado.
Tipo: CLT → `tempo_integral`; PJ e Freelancer → `pj`; Estágio → `estagio`; Temporário → `temporario`.

## R4. Paginação e janela

- **Decision**: ler até `MAX_PAGINAS = 5` por cargo; parar antes se a página tiver menos de 20 vagas, se vier sem
  vagas ou se a última vaga da página for mais antiga que a janela (`horas`, arredondado para dias como em
  `_comum.filtrar`).
- **Rationale**: a lista é ordenada por data; com janela de 1 a 3 dias, uma página costuma bastar.
- **Note**: o limite `por_termo` vale depois do filtro de título, não para a paginação (o filtro descarta muitas).

## R5. Uma leitura por cargo, várias consultas

- **Decision**: guardar a lista lida de cada cargo durante a busca (memória do módulo, zerada por
  `_comum.AO_ESQUECER`); as consultas "remoto", "país" e "cidade" do mesmo cargo filtram a mesma lista.
- **Rationale**: o site não filtra modelo nem cidade de forma confiável pelo texto; consultar de novo traria a
  mesma lista. Com cidade e remoto marcados, a busca faz a metade dos pedidos.
- **Alternatives considered**: `_comum.lembrar` (perde as páginas já lidas quando uma página do meio falha).

## R6. Filtro por consulta

- `grupo == "remoto"` (ou `consulta["remoto"]`): só vagas com modelo remoto.
- `grupo == "local"`: vaga não remota cuja cidade bate com `consulta["cidade"]` ou cuja UF bate com
  `consulta["estado"]` (sigla ou nome do estado, sem acento e sem diferença de maiúsculas; tabela das 27 UFs);
  modelo, quando informado, entre os `modelos` da consulta.
- `grupo == "pais"`: todas, com modelo (quando informado) entre os `modelos` da consulta.
- `consulta["pais"] != "brazil"`: nenhuma consulta (a Nerdin é só do Brasil). Com `AREAS = ("nacional",)` ela já
  fica fora da busca internacional.

## R7. Pedidos, pausa e bloqueio

- **Decision**: `_baixar` próprio, como no LinkedIn: `urllib` sem cookies, User-Agent `_comum.AGENTE` (a ferramenta
  se identifica; o site respondeu 200 com ele), pausa de 3 s entre pedidos, tempo limite de 20 s, sem nova tentativa.
  403, 429 e 503 marcam a Nerdin como parada nesta busca e viram o aviso "a Nerdin limitou as consultas; a busca
  seguiu sem ela". Outro erro de rede vira erro da consulta, sem parar a fonte.
- **Rationale**: princípio VI (portal sem API: parar no primeiro bloqueio, sem nova tentativa). O `_comum.baixar`
  tenta de novo no 429, por isso não serve aqui.
- **Alternatives considered**: espera de horas gravada em `.cache/` como no LinkedIn: desnecessária por ora (a
  Nerdin não mostrou limite); fica para depois se aparecer bloqueio de verdade.

## R8. Descrição

- **Decision**: `descrever(vaga)` baixa a página da vaga e usa `link.extrair_jobposting(pagina, "Nerdin")`; devolve
  a descrição (até 12 000 caracteres). `MAX_DESCRICOES = 30`; `parada()` devolve o estado de bloqueio, para o
  `vagas.ler_descricoes` marcar `descricao_pendente`.
- **Rationale**: a página traz `<script type="application/ld+json">` com `JobPosting` completo (title,
  description, hiringOrganization, datePosted, validThrough, employmentType, jobLocationType `TELECOMMUTE`,
  jobLocation, identifier). O `employmentType` vem `FULL_TIME` até em vaga PJ, então o tipo continua o do card.

## R9. Adicionar Vaga pelo link

- **Decision**: `link.plataforma` reconhece `nerdin.`; `link.ler` usa `nerdin.id_do_link(url)` (import dentro da
  função, como o `post`, porque `nerdin` importa `link`) para o id `nerdin-<n>` e lê a página pelo
  `extrair_jobposting`.
- **Rationale**: o id igual ao da busca evita a vaga repetida (SC-003).

## R10. Ligada por padrão

- **Decision**: `FONTES_PADRAO = ["indeed", "gupy", "nerdin"]`; `vagas.fontes_da_busca` usa `filtros.FONTES_PADRAO`
  quando o config não tem `fontes`; `config.exemplo.json` traz a Nerdin. Configs com `fontes` não mudam.
- **Rationale**: pedido do usuário, com o princípio V (nada gravado no config sem o clique da pessoa).
- **Order in the panel**: `FONTES_NAC` = Indeed, Gupy, Nerdin, LinkedIn, startup.jobs (as ligadas por padrão primeiro).

## R11. Cor da etiqueta

- **Decision**: `.plat[data-p="Nerdin"] i { background: #f0a43a; }` (âmbar), diferente das cores em uso e visível
  nos dois temas. O azul-marinho da marca (#011B45) some no tema escuro.
