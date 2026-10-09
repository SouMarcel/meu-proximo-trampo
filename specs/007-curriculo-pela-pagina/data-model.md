# Data Model: Currículo pela página

Tudo local e fora do Git (`curriculos/`, banco).

## Currículo gerado (`curriculos/<nome>.json`, `.docx`, `.pdf`, `.meta.json`)

`<nome>` = `AAAA-MM-DD-empresa-cargo` (vaga) ou `AAAA-MM-DD-base`, com `-2`… se repetir.

`<nome>.meta.json`:

| Campo | Regra |
|---|---|
| `nome` | o nome base dos arquivos |
| `alvo` | `{tipo: vaga, id, titulo, empresa}` ou `{tipo: base}` |
| `tecnicas` | as técnicas e escolhas usadas (catálogo da Fase 5) |
| `arquivos` | `{json, docx, pdf}` (pdf `null` se não saiu) |
| `paginas` | número ou `null` (não medidas); `acima_do_limite` bool |
| `conferencia` | o resultado de `conferir.conferir` (veredito, fatos, requisitos, cobertura, ats) |
| `pronto` | `false` quando o veredito é `bloquear` |
| `ia` | `{provedor, modelo}` que escreveu |
| `criado_em` | data e hora |

## Vaga (já existe)

Campo novo `curriculos: [nome]`, na ordem em que foram gerados.

## Geração em andamento (memória do servidor; `dash/gerador.py`)

`{situacao: ociosa|escrevendo|gerando|conferindo|pronto|falha, alvo, tecnicas, inicio, fim, nome,
mensagem}`; o último pedido com falha fica para `tentar`.
