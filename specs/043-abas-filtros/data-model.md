# Data Model: Abas no painel Filtros da busca

## Portal a mapear (`filtros.PORTAIS_A_MAPEAR`)

É parte da ferramenta, não dos filtros da pessoa: não vai para o `config.json`. É enviado em
`GET /api/config → opcoes.portais_a_mapear`, na ordem da constante.

| Campo | Tipo | Regra |
|---|---|---|
| `nome` | string | Obrigatório. É o nome do portal como a pessoa o conhece (ex.: "InHire"). Não pode coincidir, sem acento e sem diferença de maiúsculas, com o rótulo de um portal que já está na busca (`FONTES_NAC`, `FONTES_LOGIN`, `FONTES_INT`). |
| `situacao` | `"em_estudo"` \| `"nao_deu"` | Obrigatório. |
| `motivo` | string | Obrigatório quando `situacao` é `nao_deu`, com a data do que aconteceu. Vazio quando `em_estudo`. |

**Transições** (no roteiro de portal novo, `docs/novo-portal.md`):

- `em_estudo` → sai da lista, quando o portal entra na busca (spec própria).
- `em_estudo` → `nao_deu`, quando a pesquisa barra o portal. O motivo é o item da pesquisa que barrou.
- `nao_deu` → `em_estudo`, quando o motivo deixa de valer (ex.: o portal abre uma API). Só com uma pesquisa nova.

## Estado do painel (front, sem gravação)

| Estado | Valores | Começa em | Some quando |
|---|---|---|---|
| `aba` | `geral` \| `portais` \| `internacionais` \| `empresas` | `geral` | o painel fecha (Cancelar, X, clique fora ou depois de salvar) |

Trocar entre os modos nacional e internacional não zera `aba` nem o formulário `d`.

## Filtros (`config.json`)

Sem mudança. As seções só mudam de lugar no painel; os campos, a validação e a gravação são os de hoje
(`dash/API.md` §3.4).
