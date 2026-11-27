# Data Model: Conflitos do Meu perfil mais claros e seguros

Tudo em `.cache/primeiros-passos.json` (fora do Git), dentro de `rascunho`. Campos novos em **negrito**.

## Rascunho

| Campo | Tipo | Regra |
|---|---|---|
| origem | `"ia"` \| `"sem_ia"` | como hoje |
| **gerado_em** | ISO 8601 (segundos) | quando o rascunho foi montado; ausente nos rascunhos de antes desta spec |
| conflitos | Conflito[] | a posição é o N de `{{conflito:N}}` (nada sai da lista) |
| … | | demais seções como hoje |

## Conflito

| Campo | Tipo | Regra |
|---|---|---|
| campo | string (≤120) | como hoje |
| opcoes | Opção[] | como hoje |
| escolha | int \| null | índice em `opcoes`; herdável ao refazer (research R5) |

## Opção

| Campo | Tipo | Regra |
|---|---|---|
| valor | string (≤300) | só o dado; é o que entra no perfil |
| **nota** | string (≤200) | explicação da IA; só na tela; `""` quando não vem |
| fonte | string | nome de um material ou `"perfil atual"` |

## Prévia (resposta, não guardada)

| Campo | Tipo | Regra |
|---|---|---|
| **perfil_versao** | string \| null | SHA-256 (16 hex) do perfil gravado; `null` sem perfil |
| **aviso** | Aviso \| null | research R3 |

## Aviso

| Campo | Tipo | Regra |
|---|---|---|
| rascunho_em | ISO \| null | `gerado_em`; `null` = data desconhecida |
| perfil_em | ISO | data de modificação do perfil gravado |
| sairiam | string[] (≤60) | itens e títulos do perfil atual ausentes no texto que seria gravado |
| pode_refazer | bool | há IA ligada |

## Transições

- Gerar ou refazer o rascunho → novo `gerado_em`; escolhas herdadas onde casam.
- Gravar com `perfil_versao` diferente do atual → recusado (409); a pessoa vê o que muda de novo.
