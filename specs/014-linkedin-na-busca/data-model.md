# Data Model: LinkedIn na busca de vagas

## Configuração (`config.json`)

| Chave | Tipo | Regra |
|---|---|---|
| `fontes` | lista | portais da busca nacional, entre `indeed`, `gupy`, `linkedin`, `startupjobs`; pelo menos um; sem a chave, `["indeed","gupy"]` (o LinkedIn fica desligado) |

Nada muda nas outras chaves. `internacional.fontes` continua só com as fontes do exterior sem filtro de país.

## Consulta ao LinkedIn (por grupo de `filtros.consultas`)

| Campo | Origem |
|---|---|
| `keywords` | `consulta["termo"]` |
| `location` | `consulta["local"]` (cidade) → senão o país em inglês → senão "Worldwide" (global) |
| `distance` | `consulta["raio_km"]` em milhas, só com cidade |
| `f_WT` | pelo grupo (research §2) |
| `f_JT` | `tipos_emprego` marcados (vazio = todos) |
| `f_TPR` | `r` + janela em segundos |
| `start` | 0 (uma página de 10 vagas por consulta) |

## Vaga do LinkedIn (o que `buscar` devolve)

| Campo | Valor |
|---|---|
| `id` | `li-<número>` (o mesmo do "Adicionar pelo link") |
| `plataforma` | "LinkedIn" |
| `titulo`, `empresa`, `local` | do card ("Empresa não informada" se vier vazio) |
| `publicada_em` | `datetime` do card (AAAA-MM-DD) ou nulo |
| `url` | `https://www.linkedin.com/jobs/view/<número>/` |
| `url_candidatura` | nulo (a candidatura é no LinkedIn) |
| `remoto` | `f_WT == "2"` ou "remote/remoto" no local |
| `modelo_trabalho` | remoto, presencial ou hibrido quando o `f_WT` da consulta tem um valor só |
| `salario`, `tipo`, `descricao` | nulos na lista; `descrever()` traz a descrição com os critérios |
| `tipo_emprego` | lista de códigos de `TIPOS_EMPREGO`, quando o card ou a descrição informam |

## Estado da busca

| Estado | Ciclo |
|---|---|
| `_bloqueado` (no módulo) | falso no `_comum.esquecer()` (início da busca); verdadeiro no primeiro sinal de bloqueio; enquanto verdadeiro, `buscar` e `descrever` não fazem pedido e levantam o erro repetido |
| `_ultimo_pedido` | momento do último pedido ao LinkedIn, para a pausa de 3 a 7 s |
