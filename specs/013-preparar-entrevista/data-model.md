# Data Model: Preparação para entrevista

Tudo em `entrevistas/` (fora do Git).

## `entrevistas/historias.json`

```text
{"historias": [{id, titulo, situacao, tarefa, acao, resultado, reflexao, conquista, perguntas: [..],
                conferir: [..], criada_em, atualizada_em}]}
```

Cada campo de texto até 1.200 caracteres; título até 120; no máximo 60 histórias.

## `entrevistas/vaga-<id>.json`

```text
{
  "vaga_id", "texto_empresa" (até 20.000),
  "resumo": {"itens": [{ponto, origem: vaga|texto|deducao, trecho}], "data", "ia"},
  "perguntas_ia": {"itens": [{texto, tipo: comportamental|tecnica, porque}], "data"},
  "simulacao": {"idioma": pt|en, "respostas": [{pergunta, resposta, retorno: {funcionou, faltou, mais_forte, conferir}, data}]},
  "rodadas": [{data, etapa, perguntas: [..], bem, mal, proximos}]
}
```

## Calculados (não gravados)

- `dossie`: dados da vaga, da análise e do kit, anotações e o texto colado.
- `perguntas`: lista padrão + técnicas pelos requisitos + lacunas + perguntas que caíram + as da IA, `{texto, tipo,
  porque, origem}`.
- `salario`: `{faixa, moeda, pretensao, pontos}`.
