# Modelo de dados: empresas acompanhadas em qualquer página de vagas

## Empresa acompanhada (`config.json` → `empresas[]`)

`{sistema, id, nome, url}`, como na spec 031, com sistemas novos:

| `sistema` | `id` | `url` | Exemplo |
|---|---|---|---|
| `greenhouse`, `lever`, `ashby` | o nome no sistema | a página de vagas | como hoje |
| `teamtailor` | o host | `https://<host>/jobs` | `carreiras.varejista.com.br` |
| `ey` | `ey` | `https://careers.ey.com/ey/` | a EY |
| `pagina` | host + caminho, sem `#`, sem barra final | o link colado, com o `#` | `consultoria.com.br/carreira` |

- A mesma empresa (`sistema` + `id`, sem diferença de maiúsculas) não se repete; até 50.
- `nome`: do feed (Teamtailor), "EY", ou do título da página (página própria); a pessoa pode trocar no painel.

## Migração da EY (`filtros.efetivos`)

```text
"ey" em fontes                      → EY em empresas (se não estiver); "ey" sai de fontes
sem "fontes" e com "termos"         → EY em empresas (o padrão antigo tinha a EY)
config novo (sem termos)            → nada
```

Grava no próximo salvamento do painel (ou no Acompanhar). Até lá, a busca já usa o resultado de `efetivos`.

## Vaga (formato comum)

| Campo | Teamtailor | EY | Página própria |
|---|---|---|---|
| `id` | `teamtailor-<host>-<número>` | `ey-<número>` (como hoje) | `pagina-<empresa>-<cargo e local>` (estável) |
| `plataforma` | `Teamtailor` | `EY` | `Site da empresa` |
| `ats` | `teamtailor` | — | — |
| `titulo` | `title` | como hoje | da IA, conferido no texto |
| `empresa` | o nome da empresa | `EY` | o nome da empresa |
| `local` | `cidade, país` de cada local, com "; " | como hoje | da IA |
| `remoto`, `modelo_trabalho` | `remoteStatus` | como hoje | da IA (`remoto`, `hibrido`, `presencial`) |
| `restricao_local` | o país, na remota | — | — |
| `publicada_em` | `pubDate` | como hoje | o dia em que a ferramenta a viu primeiro |
| `url` | `link` | como hoje | o link da página |
| `url_candidatura`, `email_candidatura` | — | — | só se escritos na página |
| `descricao` | `description` em texto | como hoje | os requisitos |

## Memória da página própria (`.cache/empresas-paginas/<hash do id>.json`)

```json
{"marca": "<sha256 do texto>", "lida_em": "2026-11-01", "vagas": [{...vaga...}],
 "vistas": {"pagina-consultoria.com.br-...": "2026-11-01"}}
```

- Texto com a mesma marca: as vagas da memória, sem IA.
- `vistas` guarda a primeira data de cada vaga, que continua valendo quando a página muda.
