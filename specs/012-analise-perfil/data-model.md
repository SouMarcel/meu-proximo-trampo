# Data Model: Análise de perfil contínua

## `dash/dados/analises-perfil.json` (fora do Git)

```text
{
  "lacunas": {"data", "visao": "seguidas"|"todas", "vagas": N, "itens": [Lacuna]},
  "cargos": {"data", "ia": {provedor, modelo}, "itens": [Cargo]},
  "plano": {"data", "ia", "itens": [{lacuna, passos: [..3], semanas}]},
  "marcas": {"linkedin_en": bool}
}
```

## Lacuna

| Campo | Regra |
|---|---|
| `rotulo` | termo mais frequente do grupo |
| `exemplo` | uma das frases originais |
| `variacoes` | até 5 frases do grupo |
| `peso`, `parte` | soma dos pesos das vagas; parte do peso total (0–1) |
| `nivel` | `critica` (≥ 0,5), `alta` (0,25–0,5), `media` (0,1–0,25) |
| `vagas` | número de vagas |
| `exemplos` | até 3 `{id, titulo, empresa}` |

## Cargo-alvo

`{titulo, titulo_en, tipo: lateral|degrau|vizinho, evidencia, lacuna, conferir: bool}`, de 5 a 10.

## Item de prontidão

`{item, rotulo, situacao: pronto|falta|nao_informado, origem, detalhe, acao}`; `acao`: `filtros_int`, `curriculo`,
`perfil`, `marcar`.
