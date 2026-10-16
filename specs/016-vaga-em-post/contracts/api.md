# Contrato: rotas do servidor local

Todas seguem as regras de hoje do `dash/servidor.py`: host e origem validados e JSON. Pedidos de escrita passam por
`_escrita_ok`.

## POST /api/vagas/link (muda)

Corpo: `{"url": "<link>"}`.

| Caso | Status | Resposta |
|---|---|---|
| Link de vaga (como hoje) | 201/200 | `{"vaga", "nova", "analise_automatica"}` |
| Link de vaga ilegível (como hoje) | 422 | `{"erro", "parcial"}` |
| **Link de post, id `lip-…` já no banco** | 200 | `{"vaga", "nova": false}` (sem pedido ao LinkedIn) |
| **Link de post lido** | 200 | `{"post": {...}, "parcial": {...}, "ia": {...}}`; nada é gravado |
| **Link de post, canônico já no banco** | 200 | `{"vaga", "nova": false}` |
| **Link de post não lido** (bloqueio, privado, fora do ar) | 422 | `{"erro": "<motivo>", "parcial": {"url", "plataforma": "LinkedIn", "formato": "post"}, "sugestao": "colar"}` |

Os campos da resposta de post lido:
- `post`: `{"id", "url", "texto", "autor", "autor_tipo"}`;
- `parcial`: `{"url", "plataforma": "LinkedIn", "formato": "post", "post_id", "descricao", "empresa"` (só se
  `autor_tipo` for empresa)`, "publicado_por"` (só se for pessoa)`, "area", "pais_vaga"}`;
- `ia`: `{"disponivel": bool, "local": bool, "provedor", "modelo"}`. Diz se a página pode chamar a extração.

## POST /api/vagas/extrair (nova; só deste computador)

Corpo: `{"texto": "<até 20.000 caracteres>", "autor": "<opcional>", "autor_tipo": "empresa|pessoa|"}`.

| Caso | Status | Resposta |
|---|---|---|
| Extração feita | 200 | `{"campos": {"titulo", "empresa", "local", "url", "email_candidatura", "assunto_candidatura"}, "parece_vaga", "vagas", "provedor", "modelo"}` |
| Sem IA configurada | 409 | `{"erro": "nenhuma IA configurada"}` |
| Erro da IA (cota, chave, tempo, JSON inválido) | 502 | `{"erro": "<motivo legível, sem chave>"}` |
| Outro aparelho da rede | 403 | `SO_LOCAL_PERFIL` |
| Texto vazio | 400 | `{"erro": "cole o texto do post ou da mensagem"}` |

Nada é gravado. O texto não é guardado em log.

## POST /api/vagas (muda)

Aceita também `formato` (`"post"`), `post_id` (`lip-…`), `email_candidatura`, `assunto_candidatura` e
`publicado_por`. Com `post_id` já no banco, responde 200 `{"vaga", "nova": false}` sem gravar. E-mail inválido dá
400.

## PATCH /api/vagas/<id> (muda)

Aceita também `email_candidatura` e `assunto_candidatura`. Texto vazio apaga o campo. E-mail inválido dá 400
`"e-mail de candidatura inválido"`.
