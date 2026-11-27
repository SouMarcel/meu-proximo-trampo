# Data Model: Nota sem desperdício de IA

Nada muda no banco (SQLite) nem no formato da análise gravada. As entidades abaixo vivem em arquivo ou em memória.

## Regras da nota (arquivo)

`.agents/skills/buscar-vagas/regras-da-nota.md`; formato em [contracts/regras-da-nota.md](contracts/regras-da-nota.md).

| Parte | Vai no pedido | Onde |
|---|---|---|
| `## Resposta`, `## Campos`, `## Como dar a nota` | sempre | começo (parte fixa) |
| `## Portais` → `### <PLATAFORMA>` | só para as plataformas do grupo | depois de `## Vagas` |

Validação: as quatro seções existem; a parte fixa tem no máximo 5,5 mil caracteres (teste).

## Pedido de nota (texto)

```text
[fixo]   abertura · Resposta · Campos · Como dar a nota · Perfil (sem Contato) · Filtros
[varia]  ## Vagas · aviso · (nota sem descrição?) · Portais do grupo · blocos das vagas
```

Regra: duas chamadas com o mesmo perfil e os mesmos filtros têm o `[fixo]` idêntico, byte a byte.

## Lote da análise automática (memória, `Fila`)

| Campo | Tipo | Regra |
|---|---|---|
| tamanho | int | 10 → 5 → 3 → 1, a cada 429; volta a 10 na rodada seguinte |
| recusas | int | 429 seguidos; zera no lote respondido; 3 → fim da rodada |
| tentadas | set[str] | só os ids de lotes que a IA respondeu (ou de uma falha que não é limite) |

Transições de uma vaga pendente numa rodada:

```text
pendente ──lote respondido──▶ com nota (ou problema registrado) ∈ tentadas
pendente ──429──▶ pendente (espera, lote menor)
pendente ──3 recusas──▶ pendente, fora de tentadas (volta no próximo pedir())
pendente ──outro erro──▶ ∈ tentadas, ultimo_erro (como hoje)
```

## Grupo do Forçar verificar (memória, `Fila`)

| Campo | Tipo | Regra |
|---|---|---|
| _grupo | list[str] | até 3 vagas prontas, tiradas da fila; esvazia depois do pedido |
| _lendo | str \| None | a vaga cuja descrição está sendo lida |

`verificando()` = `_grupo` + `_lendo` + fila (sem repetir); `agora()` = `_lendo` ou `_grupo[0]`.

## IAErro (`ia.py`)

| Atributo | Tipo | Padrão | Preenchido |
|---|---|---|---|
| limite | bool | False | HTTP 429 (ou, no erro final de `responder`, alguma falha por limite) |
| espera | float \| None | None | `Retry-After` em segundos ou `retryDelay` do corpo; no erro final, a maior |

## Configuração (`.env`)

| Variável | Padrão | Faixa | Uso |
|---|---|---|---|
| `ANALISE_PAUSA` | 20 | 5 a 120 s | entre dois lotes da análise automática (nova) |
| `FORCAR_PAUSA` | 5 | 0 a 60 s | entre dois pedidos do Forçar (sem mudança) |

## Relatório da calibração (`.cache/calibracao-AAAAMMDD-HHMM.json`, fora do Git)

```json
{"em": "...", "ia": {"provedor": "...", "modelo": "..."}, "pedido_1_vaga": {"total": 0, "regras": 0, "perfil": 0,
 "filtros": 0, "vaga": 0},
 "vagas": [{"id": "...", "nota_antes": 0, "nota_depois": 0, "diferenca": 0, "fora_antes": false,
            "fora_depois": false, "modelo_antes": "...", "erro": null}],
 "resumo": {"respondidas": 0, "dentro_de_10": 0.0, "trocas_fora": 0, "passa": true}}
```
