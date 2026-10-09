# Contrato: fontes internacionais, configuração e páginas

## Fonte

```text
NOME, PLATAFORMA, AREAS = ("internacional",), POR_PAIS = False, TERMOS = "…"
buscar(consulta, horas, por_termo) -> (vagas, erros)    # contrato de fontes/__init__.py
```

Cada vaga no formato comum + `restricao_local`, `moeda`, `ats` quando houver. Id prefixado
(`remotive-123`, `greenhouse-empresa-456`…).

## `fontes/ats.py`

```text
reconhecer(url) -> {sistema, id, nome, url}     # ValueError com explicação se não for Greenhouse/Lever/Ashby
```

## Rotas

| Rota | Mudança |
|---|---|
| `GET /api/config` | `opcoes.fontes_int` (nome, rótulo, termos de cada fonte); `filtros.internacional` com `fontes`, `empresas`, `frases_*` |
| `PUT /api/config` | aceita os campos novos; empresas por link (normalizadas); `400` com a explicação |
| `POST /api/vagas/link` | reconhece Greenhouse, Lever, Ashby e as fontes novas |
