# Data Model: Empresas acompanhadas na busca nacional

Não há tabela nova no banco. Muda só o lugar da lista no `config.json`.

## Empresa acompanhada

| Campo | Tipo | Regra |
|---|---|---|
| `sistema` | `"greenhouse"` \| `"lever"` \| `"ashby"` | pelo host do link (`ats.reconhecer`) |
| `id` | texto | o nome da empresa no sistema (`[A-Za-z0-9][A-Za-z0-9._-]{0,99}`) |
| `nome` | texto | do link ("acme-corp" → "Acme Corp") |
| `url` | texto | a página de vagas normalizada (ex.: `https://job-boards.greenhouse.io/acme`) |

**Validação**:
- duas empresas com o mesmo `sistema` e o mesmo `id` (sem diferença de maiúsculas) contam como uma;
- no máximo 50 (`filtros.MAX_EMPRESAS`);
- link que não é do Greenhouse, do Lever nem do Ashby dá erro com o exemplo.

## `config.json`

| Antes (até a spec 030) | Depois (spec 031) |
|---|---|
| `internacional.empresas: [...]` | `empresas: [...]`, no nível de cima |

O formato muda em três momentos:
- **Leitura**: `filtros.efetivos` usa `empresas` ou, sem ela, `internacional.empresas`.
- **Gravação pelo painel**: `filtros.validar` usa `empresas` do pedido quando a chave vem, e `internacional.empresas`
  só quando ela não vem (front antigo). O `salvar` grava em cima, e `internacional` deixa de ter `empresas`.
- **Gravação pelo "Acompanhar"**: `filtros.acompanhar(url)` lê o config, põe a empresa em `empresas` (passando a lista
  antiga para cima, se for o caso) e grava só essa mudança.

## Estado da busca na fonte (memória)

O `ats._estado["bloqueados"]` é o conjunto dos sistemas que responderam 403 ou 429 nesta busca. É zerado a cada busca
(`_comum.AO_ESQUECER`). Nenhum arquivo de espera.

## Vaga da empresa acompanhada

Os campos são os de hoje (`ats.normalizar`). A área sai da consulta que achou a vaga (`filtros.area_da_vaga`):
- achada por consulta nacional (remota, do país ou da cidade): **nacional**;
- achada só pela consulta global: **internacional**, como hoje.
