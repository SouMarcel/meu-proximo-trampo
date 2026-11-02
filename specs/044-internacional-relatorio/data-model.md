# Data Model: Aba Internacional com o layout do Relatório de Vagas

Nada muda no servidor, no banco (`dash/dados/`) nem no `config.json`. O único dado novo fica no navegador da pessoa.

## Preferências da aba (no navegador)

| Chave | Área | Campos |
|---|---|---|
| `mpt_pref_triage_filtros` | Relatório de Vagas (nacional) | igual a hoje: `triageOrdem`, `niveis`, `modos`, `ader`, `dias`, `analisadas` |
| `mpt_pref_internacional_filtros` | Internacional (nova) | os mesmos, mais `moeda` e `visto` |

Regras de leitura (valor inválido ou ausente vira o padrão):

- `triageOrdem`: `"aderencia"` (padrão), `"publicacao"`, `"plataforma"` ou `"modo"`;
- `niveis`: lista com `"junior"`, `"pleno"`, `"senior"` e `"ni"`; padrão `[]`;
- `modos`: lista com `"remoto"`, `"hibrido"`, `"presencial"` e `"ni"`; padrão `[]`;
- `ader`: número de 1 a 100 ou `null` (padrão);
- `dias`: número de 0 a 365 ou `null` (padrão);
- `analisadas`: `true` ou `false` (padrão);
- `moeda` (só na Internacional): `"todas"` (padrão), `"usd"` ou `"eur"`;
- `visto` (só na Internacional): `true` ou `false` (padrão).

Não são guardados, nas duas áreas: a aba interna (abre sempre em Para decidir), a busca no texto e Baixa aderência
aberta ou fechada.

## Campos da vaga usados pela aba (já existem, `dash/API.md` §2)

`triagem`, `aderencia`, `nota_sem_descricao`, `senioridade`, `modelo_trabalho`, `remoto`, `publicada_em`, `plataforma`,
`termos`, `titulo`, `empresa`, `local`, `salario`, `descricao`, `motivo_fora`, `resumo`, `encaixe`, `lacunas`,
`pais_vaga`, `grupos`, `contratacao` e `sinais`. Nenhum campo novo.
