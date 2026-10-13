# Contrato: LinkedIn na busca

## Fonte `fontes/linkedin.py` (contrato de `fontes/__init__.py`)

```text
NOME = "linkedin"   PLATAFORMA = "LinkedIn"   AREAS = ("nacional", "internacional")
POR_PAIS = True     GLOBAL = True             TERMOS = "<o que é, consulta não oficial, risco de bloqueio>"

buscar(consulta, horas, por_termo) -> (vagas, erros)     # uma página por consulta (10 vagas)
descrever(vaga) -> str                                    # só para as candidatas; levanta FonteErro se bloqueado
parametros(consulta, horas) -> dict                       # puro (tipos e modelos vêm na consulta), testável: keywords, location, distance, f_WT, f_JT, f_TPR
ler_lista(html) -> list[dict]                             # puro, testável: os cards
tipo_emprego(texto) -> list[str]                          # "Full-time" -> ["tempo_integral"]
```

Erros (em `erros`, sem quebrar a busca):
- `"o LinkedIn limitou as consultas; tente mais tarde"`: o primeiro bloqueio. Os seguintes saem com
  `repetido=True` e não fazem pedido.
- `"não consegui ler as vagas do LinkedIn"`: a resposta chegou, mas não tem nenhum card reconhecível e não está vazia.

## Atributo novo do contrato

`GLOBAL = True` (opcional, padrão falso): a fonte também roda na consulta global (`internacional:global`), além das
consultas por país. `vagas.atende`:

```text
global  -> not POR_PAIS or GLOBAL
por país -> POR_PAIS
```

## Configuração e página

- `GET /api/config` → `opcoes.fontes_nac`: `[{nome, rotulo, termos, precisa}]`; `filtros.fontes`: a lista escolhida.
- `PUT /api/config` aceita `fontes` (pelo menos um, só os conhecidos).
- `python vagas.py buscar --fontes indeed gupy linkedin` continua valendo.
