# Data Model: LinkedIn com menos pedidos

## Vaga (documento JSON no SQLite, `dash/banco.py`): campo novo

| Campo | Tipo | Regra |
|---|---|---|
| `descricao_pendente` | bool (ausente = falso) | Verdadeiro numa vaga do LinkedIn salva pela busca sem descrição (limite de 20, bloqueio ou espera). Só candidatas recebem a marca. |

Transições:

```text
(busca, sem texto) ──► descricao_pendente=true, analise_status = o de sempre ("pendente" com IA, "sem_analise" sem)
        │
        ├─ busca seguinte lê o texto ──► descricao + tipo_emprego gravados, marca removida, aplicar_criterios;
        │                                com analise_status "pendente", a análise automática pega a vaga
        ├─ busca seguinte: vaga não existe mais / erro da vaga ──► marca removida; segue com o que tem
        └─ pessoa descarta (triagem "visitada") ou leva ao quadro (etapa) ──► sai da fila (a marca fica, sem efeito)
```

Efeitos da marca:
- `analise.precisa(v)` → falso (a IA da página não analisa);
- `banco.precisa_analise(v)` → falso (a análise pelo chat não pega);
- página: chip "Descrição pendente" no lugar de "Aguardando análise"; no lugar da nota, "descrição pendente";
- `banco.py quadro`/`pendentes`: mostram "descrição pendente".

Vagas antigas sem o campo não mudam.

## Consulta agrupada (em memória, `vagas.executar`)

Igual à consulta de `filtros.consultas`, com:

| Campo | Regra |
|---|---|
| `termos` | lista dos cargos do grupo (na ordem da configuração) que cabem nesta parte |
| `termo` | a expressão (`filtros.expressao_or(termos)`); com um cargo só, o próprio cargo |
| `agrupada` | verdadeiro |

## Espera do LinkedIn (`.cache/linkedin-espera.json`, fora do Git)

```json
{"desde": "2026-10-15T09:12:00", "motivo": "excesso de pedidos"}
```

- **Quando é gravado**: só no bloqueio. Um bloqueio novo sobrescreve o anterior.
- **Validade**: até `min(desde, agora) + 6 h`. Arquivo ilegível ou ausente significa que não há espera.
- **Quando é lido**: por `linkedin.espera()` em `buscar`, `descrever`, `buscador.plano` e `vagas.cmd_buscar`.

## Resultado da busca (`executar` → `candidatas.json`): chaves novas

| Chave | Conteúdo |
|---|---|
| `descricoes_completadas` | `[{id, descricao, tipo_emprego?, erro?}]` das pendentes do banco tratadas nesta busca (`erro`: a vaga não existe mais; a marca sai) |
| `espera` | `[{portal, ate, motivo}]` das fontes que ficaram de fora por espera |
| `aviso_cargos` | texto ou `null` |

Nas candidatas, `descricao_pendente: true` quando ficaram sem texto; `gravar_resultado` copia o campo para o
documento.
