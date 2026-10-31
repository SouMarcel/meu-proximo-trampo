# Contrato: `fontes/ey.py`

Segue `fontes/__init__.py`. Constantes:

| Nome | Valor |
|---|---|
| `NOME` | `"ey"` |
| `PLATAFORMA` | `"EY"` |
| `AREAS` | `("nacional",)` |
| `TERMOS` | consulta não oficial à busca pública do site de vagas da EY, sem login; pausa entre as consultas; se a EY limitar, a busca segue sem ela; candidatura no próprio site |
| `SITE` | `https://careers.ey.com/ey/` |
| `POR_PAGINA`, `MAX_PAGINAS` | 25, 2 |
| `MAX_VAGAS` | 20 páginas de vaga por busca (busca + `descrever`) |
| `PAUSA`, `VAR_PAUSA`, `PAUSA_MIN`, `PAUSA_FAIXA` | `(3.0, 7.0)`, `"EY_PAUSA"`, 3.0, 4.0 |
| `ARQ_DATAS`, `VALIDADE_DATAS` | `.cache/ey-datas.json`, 60 dias |
| `VAGA` | `^https?://careers\.ey\.com/[A-Za-z0-9_-]+/job/[^/?#]+/(\d+)/?(?:[?#].*)?$` |

## Funções

- `pausa()`, `aviso_pausa(consultas)`: como no Vagas.com; `aviso_pausa` conta `consultas × MAX_PAGINAS + MAX_VAGAS`.
- `parada() -> bool`: bloqueou nesta busca (sem espera entre buscas, então não há `espera()`).
- `url_lista(termo, pais, startrow=0) -> str`.
- `ler_lista(pagina) -> list[dict]`: as linhas `tr.data-row` (título, link, primeiro local); sem data.
- `ler_pagina(pagina) -> dict`: dos microdados: `titulo`, `empresa` ("EY"), `publicada_em`, `locais` ([(cidade, UF)]),
  `local` (o primeiro), `remoto`, `descricao`, `tipo`. Levanta `link.LinkErro` sem título.
- `buscar(consulta, horas, por_termo)`: só `pais` da área nacional; cidade, país ou remoto conforme FR-003.
- `descrever(vaga) -> str`: a descrição já lida na busca; senão abre a página (conta em `MAX_VAGAS`); parada: devolve o
  que a vaga já tinha.
- `id_do_link(url) -> str | None`: `ey-<número>`.

## Formato da vaga (data model)

| Campo | Origem |
|---|---|
| `id` | `ey-<número da URL>` |
| `plataforma`, `empresa` | `"EY"` |
| `titulo` | `a.jobTitle-link` (lista) |
| `local` | o primeiro local da página da vaga ("Cidade, UF"; país fora do Brasil: "Cidade, País"); sem página, o da lista |
| `remoto`, `modelo_trabalho` | "remoto", "home office" ou "remote" no título ou no local → `True`, `"remoto"`; senão `False`, sem `modelo_trabalho` |
| `publicada_em` | `itemprop="datePosted"` ("Thu Oct 22 00:00:00 UTC 2026") → `2026-10-22`; ilegível → `None` |
| `url` | `https://careers.ey.com/ey/job/…/<número>/` |
| `url_candidatura`, `salario` | `None` |
| `tipo` | "Banco de talentos" e/ou "Exclusiva para PCD" (pelo título), juntos com " • "; senão `None` |
| `descricao` | `itemprop="description"` em texto (`link.texto_de_html`), até 12.000 caracteres |

## Memória de datas (`.cache/ey-datas.json`)

`{"<número>": {"data": "AAAA-MM-DD" | null, "locais": [["São Paulo", "SP"], …], "lida_em": "AAAA-MM-DD"}}`.
Lida no começo da busca e gravada no fim de `_lista`; arquivo ausente ou ilegível vale como vazio. Só números de vaga,
datas e cidades: nada da pessoa.

## Consultas

| Consulta | O que entra |
|---|---|
| remota (`remoto: True`) | vagas com `remoto` |
| cidade (`cidade`) | vagas não remotas com algum local na cidade ou no estado (`_comum.na_regiao`) |
| país | todas (respeitando `modelos`, como no Vagas.com) |

Em todas: título que bate com o cargo e data dentro da janela (sem data, entra).
