# Data Model: Forçar verificar a nota de uma vaga

## Vaga (documento JSON em `vagas`, campo novo sem migração)

| Campo | Tipo | Regra |
|---|---|---|
| `nota_sem_descricao` | bool (ausente = falso) | `true` quando a nota foi dada sem a descrição (R4); sai quando a descrição chega (R5) ou numa nota normal |
| `analise_status` | texto | sem mudança de valores (`pendente`, `feita`, `sem_dados`, `sem_analise`); `completar_descricao` volta para `pendente` a vaga com `nota_sem_descricao` |
| `aderencia`, `resumo`, `encaixe`, `lacunas`, `alertas` | — | os de sempre; a nota sem a descrição usa os mesmos campos |

## Estado na memória do servidor (`analise.FILA`)

| Campo | Tipo | Regra |
|---|---|---|
| `_forcadas` | conjunto de ids | entra no `forcar(id)`; sai quando a rodada termina aquela vaga (com ou sem nota) |
| `falhas` | `{id: {"motivo": str, "em": "AAAA-MM-DDTHH:MM"}}` | gravada quando a vaga forçada não ganha nota; apagada no próximo `forcar(id)` ou quando a vaga ganha nota |
| `rodando`, `ultimo_erro` | — | sem mudança |

## Transições de uma vaga forçada

```text
sem nota ──forcar──▶ verificando ──(descrição pendente? lê 1 vez, se der)──▶ IA
   ▲                                                                         │
   └──────── falha (motivo) ◀── sem nota / erro ◀────────────────────────────┤
                                                                             ▼
                                         nota (feita) ── com ou sem nota_sem_descricao
nota_sem_descricao ──descrição chega──▶ pendente ──fila automática──▶ nota nova (sem a marca)
```
