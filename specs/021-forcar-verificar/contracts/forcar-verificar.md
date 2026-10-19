# Contrato: Forçar verificar

## `POST /api/vagas/<id>/analisar`

- Checagens de sempre: host permitido, `Content-Type: application/json`, mesma origem. Corpo: `{}`.
- Só deste computador (`127.0.0.1`/`::1`); de outro → 403 com a mensagem de "só neste computador".

| Situação | Resposta |
|---|---|
| Aceito (ou já verificando) | 202 `{"verificando": ["<id>", …]}` |
| Sem IA ligada | 409 `{"erro": "Para dar nota, ligue uma IA", "sem_ia": true}` (nada gravado) |
| Vaga com nota e sem `nota_sem_descricao` | 409 `{"erro": "a vaga já tem nota"}` |
| Vaga não existe | 404 `{"erro": "vaga não encontrada"}` |
| Id inválido | 404 |

## `GET /api/versao` (campos novos)

```json
{"versao": 12, "analisando": true, "ia_erro": null, "busca": {…},
 "verificando": ["li-4000000001"],
 "falhas": {"nerdin-99556": {"motivo": "a IA não devolveu a vaga", "em": "2026-10-19T16:02"}}}
```

## `analise.Fila`

```python
FILA.forcar(vid: str) -> bool        # False sem IA; True = está (ou já estava) verificando
FILA.verificando() -> list[str]
FILA.falhas: dict[str, dict]
```

Rodada (`_rodar`): primeiro as forçadas (cada uma: `banco.obter`; com nota e sem a marca → sai; descrição pendente ou
vazia → `vagas.descrever_uma`; sem texto → `sem_descricao`), em seguida as automáticas (`precisa` e `tentadas`, sem
as forçadas desta rodada). Uma chamada a `analisar(forcadas, sem_descricao=…)` e outra às automáticas.

## `analise.analisar(vagas, sem_descricao: set[str] = frozenset())`

Igual à de hoje; para os ids em `sem_descricao`, o pedido avisa a IA (research R4) e as análises voltam com
`nota_sem_descricao: true`.

## `vagas.descrever_uma(vid: str) -> dict`

`{"descricao": str, "motivo": None | "sem_fonte" | "busca" | "espera" | "erro" | "bloqueio" | "vazia"}`; grava a
descrição com `banco.completar_descricao` quando vier texto. No máximo um pedido ao portal.

## `dash/banco.py`

- `validar_analise`: aceita `nota_sem_descricao` (bool) com `analise_status == "feita"`.
- `aplicar_analises`: tira `nota_sem_descricao` do documento quando a análise não traz a marca.
- `completar_descricao`: com texto e `nota_sem_descricao` → tira a marca e grava `analise_status = "pendente"`.

## Página

- Botão `[data-forcar=<id>]` "Forçar verificar" em `.decide`, embaixo dos botões de decisão, em vaga sem nota (ou com
  `nota_sem_descricao`) na triagem `pendente` ou `fora`.
- Verificando: "Verificando…" desligado e a dica do tempo. Falha: dica com o motivo e o botão de volta.
- `nota_sem_descricao`: rótulo "sem a descrição" no selo, chip e banner no detalhe.
