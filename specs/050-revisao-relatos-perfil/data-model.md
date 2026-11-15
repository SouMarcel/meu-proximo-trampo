# Data Model: Revisão do perfil ao levar relatos (spec 050)

Arquivo `dash/dados/revisao_perfil.json` (fora do Git): `{ "<origem>": Revisao }`, com origem `vaga:<id>` ou
`relatos`. Uma revisão por origem; a nova substitui a anterior.

## Revisao

| Campo | Tipo | Regra |
|---|---|---|
| `origem` | str | `vaga:<id>` ou `relatos` |
| `vaga` | `{id, titulo, empresa}` \| null | Cópia curta, na origem da vaga |
| `relatos` | `[str]` | Ids dos relatos incluídos (1 a 20) |
| `criada_em` | ISO | Hora em que a proposta ficou pronta |
| `perfil_sha` | str | sha256 do perfil em que a proposta se baseou (R5) |
| `itens` | `[Item]` | Até 40 |
| `discordancias` | `[Discordancia]` | Até 10 |
| `sem_fato` | `[str]` | Ids dos relatos sem fato para o perfil ("este relato não traz fato para o perfil") |
| `avisos` | `[str]` | Gerais (IA de reserva, itens descartados) |
| `ia` | objeto | `ia.marca()`, quem respondeu |
| `gravada_em` | ISO \| null | Hora do Gravar no perfil |
| `anterior` | str \| null | Nome da versão anterior do perfil guardada |
| `aceitos` | int \| null | Quantos itens entraram |

**Situação** (calculada): `pronta` (à espera da decisão) ou `gravada`. O andamento (`revisando`) e a falha vêm do
estado do gerador.

## Item

| Campo | Tipo | Regra |
|---|---|---|
| `id` | str | `i1`, `i2`… estável na revisão |
| `tipo` | `entra` \| `muda` \| `sai` | |
| `secao` | str | Uma das seções do perfil; permitidas: Resumo, Experiência, Habilidades, Formação, Certificações, Idiomas (e Relatos só para `sai`) |
| `cargo` | str \| null | O título `###` do cargo, como está no perfil, quando a seção é Experiência |
| `atual` | str \| null | A linha atual (obrigatória em `muda` e `sai`; ≤ 600) |
| `novo` | str \| null | O texto novo (obrigatório em `entra` e `muda`; ≤ 600) |
| `relatos` | `[str]` | Ids dos relatos de origem |
| `avisos` | `[str]` | Da conferência sem IA (R3) |
| `valido` | bool | `false` quando a linha atual ou o lugar não existem: não pode ser aceito |
| `aceito` | bool | Padrão: `true` sem avisos, `false` com avisos; a pessoa muda |
| `origem` | `ia` \| `ferramenta` \| `discordancia` | `ferramenta` = o "sai" da linha crua (FR-009) |

## Discordancia

| Campo | Tipo | Regra |
|---|---|---|
| `id` | str | `d1`, `d2`… |
| `assunto` | str (≤ 200) | Ex.: "Método de trabalho na Empresa Alfa" |
| `trecho_relato` | str (≤ 500) | Precisa estar no relato |
| `trecho_perfil` | str (≤ 500) \| null | Precisa estar no perfil; null quando a dúvida é de lugar (em qual cargo) |
| `relatos` | `[str]` | |
| `opcao_relato` | Item \| null | O item que "usar o relato" produz (`muda` ou `entra`) |
| `escolha` | `perfil` \| `relato` \| `correcao` \| null | null = sem escolha (bloqueia o Gravar) |
| `correcao` | str (≤ 600) | Obrigatória quando `escolha = correcao`; vira um item `muda` (com `trecho_perfil`) ou `entra` no lugar do `opcao_relato` |
| `valido` | bool | `false` quando o trecho do perfil não existe: só "manter o perfil" é possível |

## Mudanças em entidades existentes

- **Relato** (`relatos.json`, spec 035): sem campo novo. `no_perfil` passa a `true` também pela revisão (algum item
  aceito vindo dele).
- **Resposta da análise** (`reprovacao.json`, spec 049): `levado` (id do relato) passa a ser gravado no Reescrever e
  gerar com o relato à espera de revisão. Campo novo `revisado_em` (ISO), quando a revisão é gravada.
- **Análise** (calculado no `com_calculos`): `para_revisar` (`[id]` dos relatos das respostas "Levar ao meu perfil"
  ainda fora do perfil) e `levadas_em` (a última `gravada_em` da revisão `vaga:<id>`).

## Transições

```text
(nenhuma) --Revisar e levar ao perfil--> revisando --ok--> pronta --decisões--> pronta
revisando --falha--> (a revisão anterior continua; o gerador mostra a falha e "Tentar de novo")
pronta --Gravar (perfil igual, sem discordância aberta)--> gravada
pronta --Gravar (perfil mudou)--> 409, continua pronta
pronta --Descartar--> (nenhuma)
(sem IA) --Revisar e levar ao perfil--> relatos levados como hoje + aviso
```
