# Contrato: config, API e comando

## `GET /api/config` → `opcoes`

Os campos de hoje não mudam. Mudam `regioes` e entram dois campos novos:

```jsonc
{
  "regioes": {"pais": "Seu país", "america_norte": "América do Norte", "america_central": "América Central",
              "america_sul": "América do Sul", "latam": "América Latina", "americas": "Américas",
              "ue": "União Europeia", "europa": "Europa", "asia": "Ásia", "oceania": "Oceania", "africa": "África"},
  "regioes_lugar": ["América do Norte", "América Central", "América do Sul", "América Latina", "Américas",
                    "União Europeia", "Europa", "Ásia", "Oceania", "África"],
  "fontes_regiao": ["linkedin"]
}
```

- `regioes_lugar`: nomes que os campos de país aceitam, além dos países (`paises`).
- `fontes_regiao`: portais que procuram por região.
- Página sem os dois campos novos (servidor antigo): não mostra a linha Regiões nem o aviso.

## `PUT /api/config` (corpo como hoje)

- `internacional.regioes`: códigos de `opcoes.regioes`. `brasil` (vira `pais`) e `mundo` (sai) são aceitos sem erro.
- `internacional.paises`, `paises_mudanca` e `autorizacao_trabalho`: países ou nomes de `regioes_lugar`, em português,
  com ou sem acento, ou o nome em inglês. O servidor grava o nome em português.
- Erro 400 com a mensagem "<campo>: país ou região desconhecido: X" para nome fora das listas.

## Comando `python dash/banco.py regioes [--gravar]`

- **Sem `--gravar`:** não grava nada. A saída tem uma linha de resumo, uma linha por vaga e a instrução para gravar:

  ```text
  N vaga(s) perderiam o motivo de região; M voltariam ao relatório.
  - <id> | <cargo> | <empresa>: <motivo antigo> → <volta | continua em Fora: motivos>
  Nada foi gravado. Para gravar: python dash/banco.py regioes --gravar
  ```

- **Com `--gravar`:** aplica as mesmas mudanças e diz "perderam" e "voltaram".
- Retorno: 0.

## Fonte (contrato em `fontes/__init__.py`)

- `POR_REGIAO` (opcional, padrão `False`): com `True`, o portal recebe consultas com `regiao` (nome em inglês) e
  `pais: None`. Sem ele, o portal não recebe essas consultas.
