# Data Model: Kit de candidatura

Tudo no documento da vaga (banco JSON, sem migração) ou em `curriculos/` (fora do Git).

## Análise (campos novos, gravados por `banco.validar_analise`)

| Campo | Formato | Regra |
|---|---|---|
| `autorizacao` | `{valor, frase}` | valor: `patrocina`, `nao_precisa`, `omisso`, `nao_patrocina`; fora disso, cai |
| `contratacao` | `[{valor, frase}]` | valor: `contractor`, `eor`, `empregado_brasil`, `relocation`, `clt`, `pj`; até 4 |
| `ingles` | `{nivel, frase}` | nível: `nao_pede`, `basico`, `intermediario`, `fluente`, `nativo` |
| `fuso` | `{texto, frase}` | texto até 80 |
| `sistema_candidatura` | texto | até 40; não substitui o `ats` da fonte |
| `pede` | `[{item, frase}]` | item: `curriculo_ingles`, `carta`, `formulario`, `portfolio`, `teste`, `video`; até 6 |
| `riscos` | `[{tipo, frase}]` | tipo: `remuneracao`, `remoto_hibrido`; até 4 |

Frase: até 200 caracteres, trecho do anúncio.

## Vaga (campos da pessoa, pela rota de atualização)

| Campo | Formato | Regra |
|---|---|---|
| `kit` | `{estados: {item: estado}, extras: [texto], removidos: [item]}` | estado: `a_fazer`, `pronto`, `nao_se_aplica`; até 10 extras de 80 |
| `lembretes` | `{base, follow1, follow2, agradecimento, parar}` | estados `feito` ou `dispensado`; `base` = "etapa:data" |
| `entrevista_em` | AAAA-MM-DD ou nulo | data da entrevista |

## Calculados (devolvidos com a vaga)

- `checklist`: `[{item, rotulo, origem: vaga|analise|anuncio|pessoa, estado, frase?, acao?}]`; `acao`:
  `curriculo`, `carta`, `respostas`, `candidatar`.
- `lembretes_pendentes`: `[{tipo: follow1|follow2|agradecimento, desde}]`.

## Documentos em `curriculos/`

- Carta: `AAAA-MM-DD-empresa-cargo-carta.txt` e `.docx`, `.meta.json` com `{tipo: "carta", alvo,
  respostas (as quatro), idioma, palavras, conferencia {veredito, itens}, ia, criado_em}`.
- Respostas: `AAAA-MM-DD-empresa-cargo-respostas.txt` e `.meta.json` com `{tipo: "respostas", alvo,
  itens: [{pergunta, resposta, sensivel, da_pessoa, conferir?}], ia, criado_em, atualizado_em}`.
- A vaga guarda os nomes em `documentos` (`[{tipo, nome, criado_em}]`), como `curriculos` hoje.
