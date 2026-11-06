# Data Model: Regiões e continentes

## Região (constante em `filtros.py`)

| Campo | Descrição |
|---|---|
| nome | em português, chave do catálogo (`REGIOES_PAISES`): "União Europeia", "Oceania"… |
| países | conjunto de nomes de `PAISES` (research D1) |
| nome em inglês | `REGIAO_EN[nome]`, usado na busca por região (só as marcáveis) |
| marcável | as 10 regiões da spec; EMEA, Ásia-Pacífico e Oriente Médio só no texto |

"mundo todo" não é região do catálogo: quer dizer todos os países.

## config.json → `internacional` (campos que mudam)

| Campo | Antes | Agora |
|---|---|---|
| `regioes` | `brasil`, `latam`, `americas`, `mundo` | `pais`, `america_norte`, `america_central`, `america_sul`, `latam`, `americas`, `ue`, `europa`, `asia`, `oceania`, `africa`; `brasil` lido como `pais`; `mundo` ignorado |
| `paises` | países | países ou regiões (nomes em português) |
| `paises_mudanca` | países | países ou regiões |
| `autorizacao_trabalho` | países | países ou regiões |

Validação (`filtros.validar`):
- **`regioes`:** só os códigos acima. `brasil` vira `pais` e `mundo` sai sem erro; qualquer outro código dá
  "região inválido", como hoje.
- **Campos de lugar:**
  - nome desconhecido dá "<campo>: país ou região desconhecido: X";
  - o país da pessoa sai de `paises` e de `paises_mudanca`, mas a região que o contém fica;
  - repetidos saem.

## Consulta (`filtros.consultas`)

Quando o lugar é região, a consulta ganha estes campos:

| Campo | Valor |
|---|---|
| `grupo` | `internacional:<Região>` ou `mudanca:<Região>` |
| `pais` | `None` |
| `pais_nome` | nome da região em português |
| `regiao` | nome em inglês (`REGIAO_EN`) |

Fonte (`fontes/<nome>.py`): o atributo opcional `POR_REGIAO = True` diz que o portal procura por região. Hoje só o
LinkedIn tem. O padrão é `False`.

## Vaga (campos gravados que mudam de conteúdo)

| Campo | Mudança |
|---|---|
| `pais_vaga` | pode ser uma região nova ("União Europeia", "Oceania", "Ásia", "África", "América do Sul", "EMEA", "Ásia-Pacífico") |
| `motivo_fora` | o motivo de região passa a ser "Vaga aberta a: <lugares>; você aceita <regiões marcadas>" para qualquer lugar declarado |

### Revisão (`dash/banco.py regioes`)

Para cada vaga em `triagem: "fora"` com motivo de região:
- os motivos de região são refeitos pela regra nova; os outros motivos ficam;
- sem motivo restante → `triagem: "pendente"`, sem `motivo_fora` nem `triada_em`.

## Perfil (`perfil.md`, seção Trabalho no exterior)

- **A linha muda:** "Países de interesse" → "Países e regiões de interesse".
- **A resposta** pode trazer regiões.
- **A proposta de filtros** leva países e regiões reconhecidos para `internacional.paises`.
