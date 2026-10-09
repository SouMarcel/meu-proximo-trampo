# Data Model: Área de vagas internacionais

## Configuração (`config.json`)

```text
idiomas_aceitos: [pt|en|es|fr|de|it]           # vazio = todos (filtro geral)
moedas_aceitas: [USD|EUR|GBP|CAD|CHF]          # já existe
internacional: {
  ativo: bool,                                  # padrão false
  paises: [país em português],                  # já existe
  termos: [cargo em inglês],                    # já existe
  regioes: [brasil|latam|americas|mundo],
  salario_min_anual_usd: número (0 = sem mínimo),
  fuso_horas: 0–12 (horas de sobreposição; 0 = não informado),
  contratacao: [contractor|eor|pj|clt],
  aceita_mudar: bool, paises_mudanca: [país],
  passaporte: bool, autorizacao_trabalho: [país], precisa_sponsor: bool
}
```

Regras: `ativo` exige pelo menos um país e um cargo; não exige `modelos.remoto`. Valores fora das
listas → erro de validação. Config sem os campos novos → padrões (nada muda).

## Consulta (`filtros.consultas`)

Ganha `area` (`nacional` | `internacional`). Internacional: grupo `internacional:<país>`, remoto; com
`aceita_mudar`, grupo `mudanca:<país>`, sem filtro de remoto.

## Fonte (`fontes/*.py`)

Atributo opcional `AREAS` (conjunto); ausente = as duas.

## Vaga (banco, documento JSON)

| Campo | Regra |
|---|---|
| `area` | `nacional` ou `internacional` (novo; ausente = deduzido pelos grupos) |
| `pais_vaga` | país em português ou região ("mundo todo"…), quando internacional |
| `idioma` | `pt`, `en`, `es`, `fr`, `de`, `it` (detectado ou da análise) |
| `moeda` | já existe (análise) |
| `motivo_fora` | ganha os motivos de idioma e salário |
