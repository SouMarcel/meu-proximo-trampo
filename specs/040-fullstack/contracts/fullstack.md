# Contrato: `fontes/fullstack.py`

Segue `fontes/__init__.py`. Constantes:

| Nome | Valor |
|---|---|
| `NOME` | `"fullstack"` |
| `PLATAFORMA` | `"FullStack"` |
| `AREAS` | `("nacional",)` |
| `TERMOS` | consulta não oficial às vagas públicas da FullStack (vagas remotas para a América Latina), sem login; os termos de uso da FullStack proíbem acesso automatizado e não há API oficial: a ferramenta usa os pedidos públicos da página, por decisão registrada na spec 040, e vem desligada; pausa; 24 horas de espera se limitar |
| `API` | `https://api-v1.fullstack.com/api/` |
| `SITE` | `https://talent.fullstack.com/jobs/` |
| `POR_PAGINA`, `MAX_PAGINAS`, `MAX_DESCRICOES` | 30, 10, 30 |
| `PAISES` | `{"brazil": "1ae07c37-d911-413f-9160-8cd2a5d93257"}` |
| `PAUSA`, `VAR_PAUSA`, `PAUSA_MIN`, `PAUSA_FAIXA` | `(3.0, 7.0)`, `"FULLSTACK_PAUSA"`, 3.0, 4.0 |
| `ESPERA`, `ARQ_ESPERA` | 24 horas, `.cache/fullstack-espera.json` |
| `BLOQUEIOS` | 401, 403, 429, 503 |
| `VAGA` | `^https?://talent\.fullstack\.com/jobs/([0-9a-f-]{36})(?:/apply)?/?(?:[?#].*)?$` |

## Funções

- `pausa()`, `aviso_pausa(consultas)`: `aviso_pausa` conta `MAX_PAGINAS + MAX_DESCRICOES` (a lista é uma por busca).
- `espera()`, `parada()`: como no JobGether.
- `ler_lista(dados) -> list[dict]`: as publicações de uma página, agrupadas por `jobId`, no formato comum.
- `buscar(consulta, horas, por_termo)`: país fora de `PAISES` ou consulta da cidade → `([], [])` sem pedido; espera →
  aviso uma vez; senão filtra a lista guardada pelo cargo, pela janela e pelos `modelos`.
- `descrever(vaga) -> str`: o detalhe da publicação (id tirado da `url`); parada: devolve o que a vaga já tinha.
- `ler(url) -> dict`: Adicionar Vaga; espera → `link.LinkErro(…, {"plataforma": "FullStack", "url": url})`.
- `id_do_link(url) -> None`: o id da busca (`jobId`) não está no link; `ler` resolve com um pedido.

## Formato da vaga (data model)

| Campo | Origem |
|---|---|
| `id` | `fullstack-<jobId>` |
| `plataforma`, `empresa` | `"FullStack"` |
| `titulo` | `jobTitle`, inteiro |
| `local`, `restricao_local` | `"Remoto"` e `"América Latina"` (`regionGroup` "Latam"); outra região: o nome dela |
| `remoto`, `modelo_trabalho` | `linkedInWorkplaceType`: Remote → `True`, `"remoto"`; Hybrid → `"hibrido"`; On-site → `"presencial"` |
| `publicada_em` | `createdAt` (texto ISO na lista; milissegundos no detalhe) → `AAAA-MM-DD` |
| `url` | `https://talent.fullstack.com/jobs/<id da publicação>` (a primeira do país) |
| `url_candidatura`, `salario` | `None` |
| `tipo`, `tipo_emprego` | `linkedInSeniority` + `linkedInJobType`: FULL_TIME → "Tempo integral" (sem código); PART_TIME → "Meio período" (`meio_periodo`); CONTRACT → "Contrato" (`pj`); TEMPORARY → "Temporário" (`temporario`); INTERNSHIP → "Estágio" (`estagio`) |
| `idioma` | `"en"` |
| `descricao` | lista: `""`; `descrever`: as `sections` (título + corpo em texto, `link.texto_de_html`) e uma linha "Habilidades: …" com `skillsNames`, até 12.000 caracteres |

Campos da API **não gravados**: `ownerEmail`, `authorId`, `formId`, `locationId`, `status`, `questions` e os outros ids.
