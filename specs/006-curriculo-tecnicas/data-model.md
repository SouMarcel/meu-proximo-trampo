# Data Model: Currículo com técnicas

Tudo local; currículos em `curriculos/` (fora do Git).

## Técnicas e escolhas (`curriculo.TECNICAS`, `curriculo.ESCOLHAS`)

| Chave | Tipo | Padrão | O que faz |
|---|---|---|---|
| `ats` | caixa | marcada | leitura fácil por sistemas de triagem; conferência de ATS e palavras-chave |
| `foco` | caixa | desmarcada | experiências e itens escolhidos e ordenados para o alvo; seção de destaques |
| `xyz` | caixa | desmarcada | conquistas como "realizou X, medido por Y, fazendo Z", só com número confirmado |
| `resultado_primeiro` | caixa | desmarcada | cada item começa pelo resultado |
| `competencias_primeiro` | caixa | desmarcada | competências antes da experiência |
| `paginas` | 1 ou 2 | 2 | limite medido no PDF |
| `formato` | `br`, `us`, `eu` | `br` | papel e idioma: A4/pt, Letter/en (sem dados pessoais), A4/en |
| `estilo` | `padrao`, `compacto`, `executivo` | `padrao` | margens, espaços e fonte (corpo ≥ 10 pt) |

## Currículo (JSON em `curriculos/<nome>.json`)

Campos de hoje (`modelo.json`) mais `tecnicas` (objeto acima, opcional) e `destaques` (lista de até 3
textos, opcional). Com `tecnicas.formato`, o idioma dos títulos vem do formato. Sem `tecnicas`,
comportamento de hoje.

## Conferência (`conferir.conferir(...)`)

```text
{veredito: ok|conferir|bloquear,
 ats: [{nivel, mensagem, trecho}], cobertura: {achadas, total, faltando[]} | null,
 requisitos: [{texto, situacao: tem|sustentado|lacuna, evidencia}],
 fatos: [{tipo: numero|empresa|cargo|data, valor, trecho, nivel}]}
```

`nivel` de cada ponto: `conferir` ou `bloquear`; o veredito é o mais grave.
