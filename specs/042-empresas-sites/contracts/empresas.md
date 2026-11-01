# Contrato: leitura das empresas acompanhadas

## `fontes/ats.py`

| Nome | Comportamento |
|---|---|
| `SISTEMAS` | `greenhouse`, `lever`, `ashby`, `teamtailor`, `ey` e `pagina`, com o rótulo de cada um ("Página própria (lida pela IA)") |
| `reconhecer(url) -> dict` | Sem pedido. Greenhouse, Lever, Ashby, `*.teamtailor.com` e `careers.ey.com`. Link de portal de vagas: `ValueError` com a dica de Portais. Outro domínio: `ValueError` "use o botão Adicionar" (`Desconhecido`, subclasse). |
| `descobrir(url) -> dict` | `reconhecer`; se o domínio for desconhecido, **um** GET à página: feed do Teamtailor anunciado → `teamtailor`; senão → `pagina`. O nome vem do feed, de `og:site_name` ou do `<title>`. Erro de rede ou 4xx/5xx: `ValueError` com o motivo. |
| `conferir(e: dict) -> dict` | Sem pedido. Empresa já reconhecida (do painel): confere `sistema`, `url` (http/https, host coerente com o `id`) e devolve a empresa normalizada. |
| `vaga_do_link(url)` | Também links de vaga de `*.teamtailor.com/jobs/<n>-…` e da EY (`/<site>/job/<título>/<n>`). |
| `buscar(consulta, horas, por_termo)` | Para cada empresa: Greenhouse, Lever e Ashby como hoje; `teamtailor` e `pagina` pela lista do módulo (uma por busca, `_comum.lembrar`), filtrada por cargo, janela e área (`_na_area`); `ey` por `ey.buscar(consulta, …)`. |
| bloqueio | Greenhouse, Lever e Ashby por sistema, como hoje; Teamtailor e página própria por host, no primeiro 403, 429 ou 503, até o fim da busca. 404: "a página de vagas de <empresa> não existe mais; remova ou troque o link". |

## `fontes/teamtailor.py`

- `feed(host) -> str`: `https://<host>/jobs.rss`.
- `ler_feed(xml, empresa) -> list[dict]`: as vagas no formato comum (data-model.md). XML inválido ou sem `channel`:
  `_comum.FonteErro("a lista de vagas do Teamtailor veio num formato inesperado")`.
- `lista(e) -> list[dict]`: GET ao feed (`_comum.baixar`, sem nova tentativa), `ler_feed`.
- `ID = re.compile(r"/jobs/(\d+)")` no link da vaga.

## `fontes/pagina_empresa.py`

| Nome | Comportamento |
|---|---|
| `MAX_IA = 10` | páginas lidas pela IA por busca |
| `LIMITE_TEXTO = 20000` | caracteres do texto enviado à IA |
| `PASTA` | `.cache/empresas-paginas/` |
| `texto(html, url) -> str` | Texto visível (`link.texto_de_html`) do trecho do `#âncora` do link, se existir; senão, do `<body>`. Passa por `integridade.limpar`, até `LIMITE_TEXTO`. |
| `pedido(texto, empresa) -> str` | O pedido à IA: devolve só JSON `{"vagas": [{titulo, modelo, local, requisitos, email_candidatura, url}]}`, copiando do texto, sem inventar; texto entre marcadores, como dado. |
| `limpar(dados, texto, e) -> list[dict]` | Cargo precisa estar no texto (comparação sem acento e sem diferença de maiúsculas); e-mail e link só se escritos no texto; modelo só `remoto`, `hibrido` ou `presencial`; tamanhos limitados; vagas no formato comum (data-model.md). |
| `lista(e) -> list[dict]` | GET à página; mesma marca da memória: as vagas da memória; senão, com a IA disponível e abaixo de `MAX_IA`, pede à IA, grava a memória e devolve. A data de cada vaga vem de `vistas`. Sem IA: `FonteErro("ligue a IA para ler a página de vagas de <empresa>")`. Acima do limite: `FonteErro("…fica para a próxima busca")`. IAs falhando: `FonteErro` com o motivo mascarado. Nenhuma vaga: lista vazia e aviso informativo. |

## `fontes/ey.py`

- Busca sem resultado ("There are currently no open positions"): zero vagas, sem aviso.
- `ILEGIVEL` só quando a página tem linha de vaga no HTML (`<tr class="data-row…">`) e nenhuma foi lida.
