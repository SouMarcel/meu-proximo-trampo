# Contrato: rotas de material (dash/API.md §3.6)

Todas **[local]**, como hoje. A resposta é o estado da página, com os campos novos do material (`area`, `sugestao`,
`ocr`).

| Rota | Corpo | Resposta | Botão |
|---|---|---|---|
| `POST /api/perfil/material` | `{nome, base64, area?: "linkedin"\|"curriculo"\|"documento"}` ou `{nome, texto}` | 201 `{material, estado}` | envio de cada área; Adicionar texto |
| `PUT /api/perfil/material/{id}` (nova) | `{area}` | `{estado, aviso?}` | Mover para; botão do aviso |
| `POST /api/perfil/material/{id}/ocr` (nova) | `{}` | `{material, estado}` | OCR |
| `DELETE /api/perfil/material/{id}` | — | estado | Remover |

## Erros (400, com a mensagem)

| Caso | Mensagem |
|---|---|
| formato fora da área | ver research.md R2 |
| área desconhecida | "área inválida: use linkedin, curriculo ou documento" |
| mover texto colado | "o texto colado fica em Currículos" |
| OCR em material sem PDF ou já com texto | "o OCR é só para PDF sem texto" |

## Compatibilidade

- **Sem `area`**: o envio usa a adivinhação de hoje. É o caso da página antiga e da skill.
- **OCR sem resultado** (fora do Windows, sem idioma, tempo esgotado): `POST …/ocr` responde 200 com o material sem
  texto e o aviso com o motivo.
