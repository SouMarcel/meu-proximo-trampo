# Data Model: Contas conectadas

## Lida (uma candidatura lida de um portal; não gravada)

| Campo | Exemplo (fictício) | Regra |
|---|---|---|
| `portal` | `gupy`, `indeed`, `linkedin` | nome do módulo em `contas/` |
| `plataforma` | `Gupy` | igual a `banco.PLATAFORMAS` |
| `id` | `gupy-9000001`, `0123456789abcdef`, `li-123` | formato que o banco já usa; na Gupy sem `job.id`, `gupya-<applicationId>` |
| `titulo`, `empresa`, `local` | | texto do portal, cortado como no banco |
| `url` | link da vaga ou da candidatura | http(s) |
| `status` | `in_process · closed`, `REJECTED` | texto do portal, para a anotação |
| `etapa`, `resultado` | `encerrada`, `nao_aprovado` | de `etapa_do_status`; `None` = só informa |
| `data` | `2026-10-04` | data do status (Indeed: timestamp; Gupy: hoje; LinkedIn: aproximada) |
| `nota` | `Gupy: etapa 2 de 5 (Triagem)` | linha extra da anotação |
| `avisos` | `["vaga fechada ou expirada no Indeed"]` | só informam |
| `ativa` | `true` | candidatura em andamento (decide se uma "nova" vem marcada) |

## Item da proposta

`{chave, portal, tipo, vaga_id, lida, de: {etapa, resultado}, para: {etapa, resultado}, marcado}`:
- `tipo`:
  - `mudar` (vaga do quadro com etapa atrás);
  - `quadro` (vaga no Relatório, sem etapa);
  - `nova` (não está no banco);
  - `info` (sem mudança de etapa, só avisos);
- `marcado` padrão: verdadeiro para `mudar` e `quadro`; para `nova`, verdadeiro só se `ativa`.

## Vaga (sem campo novo)

Aplicar usa os campos de sempre:
- `etapa`, `etapa_em` (a data do portal) e `resultado`;
- `triagem: "seguir"` e `triada_em`, quando a vaga sai do Relatório;
- uma linha em `anotacao`: "Etapa atualizada pela [portal] em AAAA-MM-DD: [status] · [nota] · [avisos]".

Vagas novas entram por `banco.criar_de_link`, com o id do portal.

## Ordem das etapas (para não rebaixar)

`salva < aplicada < entrevista < proposta < encerrada`. Encerrada é final.

## Arquivos locais (fora do Git)

- `.cache/navegador/`: perfil do navegador (sessões);
- `.cache/contas/gupy.json`: `{applicationId: jobId}`;
- `.cache/contas/ultima.json`: a última proposta e a data, para o painel mostrar "última leitura".
