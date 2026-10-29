# Data Model: Materiais em três áreas e OCR

## Material (`.cache/primeiros-passos.json` → `materiais[]`, fora do Git)

| Campo | Mudança | Regra |
|---|---|---|
| `id`, `nome`, `arquivo`, `texto`, `campos`, `avisos`, `contato` | — | Como hoje. `texto` com CPF, RG e data de nascimento mascarados, inclusive o lido por OCR. |
| `tipo` | +2 valores | `linkedin_pdf`, `linkedin_zip`, `curriculo_pdf`, `curriculo_docx`, `texto`, **`documento_pdf`**, **`documento_docx`**. A área sai do tipo. |
| `ocr` | novo, opcional | `true` quando o texto veio do OCR. Ausente = `false`. |

## Área (derivada do tipo)

| Área | Tipos | Formatos aceitos no envio e no Mover para |
|---|---|---|
| `linkedin` | `linkedin_pdf`, `linkedin_zip` | .pdf, .zip |
| `curriculo` | `curriculo_pdf`, `curriculo_docx`, `texto` | .pdf, .docx (texto colado não se move) |
| `documento` | `documento_pdf`, `documento_docx` | .pdf, .docx |

Ao mover, o tipo é recalculado pela extensão. Por exemplo, um `.pdf` movido para documento vira `documento_pdf`.

## Material na página (`GET /api/perfil/estado` → `materiais[]`)

São os campos de hoje (`id, tipo, nome, avisos, trecho, tem_texto, arquivo`) mais:
- `area`: `linkedin`, `curriculo` ou `documento`;
- `sugestao`: `{area, motivo}` ou `null`, o aviso de área trocada, calculado a cada pedido;
- `ocr`: `bool`.

## Sugestão de área (`sugestao_de_area`)

| Área atual | Condição | Sugere |
|---|---|---|
| curriculo | o texto parece LinkedIn | linkedin |
| curriculo | texto até 3.000 caracteres com marca de certificado | documento |
| documento | o texto parece LinkedIn | linkedin |
| linkedin (PDF) | o texto não parece LinkedIn e tem marca de certificado | documento |
| linkedin (PDF) | o texto não parece LinkedIn e não tem marca de certificado | curriculo |
| qualquer | sem texto, ou ZIP | — |

## Seu currículo (`config.json` → `curriculo_base`)

- **Sem mudança de formato**: a marcação continua igual.
- **Ao mover**: a marcação de um arquivo movido para documento ou LinkedIn é apagada.
- **Candidatos**: `candidatos()` deixa de oferecer esses arquivos.
