# Contrato: currículo pela página

Escrita só do próprio computador (`403` com "Só dá para fazer isso no computador onde a ferramenta
roda."), com as proteções atuais. `400 {"erro"}` para validação; `409 {"erro"}` com outra geração.

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/curriculo/catalogo?vaga=ID` | — | `{tecnicas, escolhas, sugestao, ia: {ligada, nome, modelo, cobranca}, perfil_ok}` |
| `GET /api/curriculo/estado` | — | estado da geração (data-model.md) + `pode_alterar` |
| `GET /api/curriculo/lista?vaga=ID` ou `?base=1` | — | `{curriculos: [meta, …]}` (mais recente primeiro; `disponivel` por arquivo) |
| `POST /api/curriculo` | `{vaga_id?: ID, tecnicas: {…}}` | `202` estado; `400` sem IA, sem perfil, vaga inexistente ou técnicas inválidas; `409` outra geração |
| `POST /api/curriculo/tentar` | `{}` | `202` estado; `409` sem pedido com falha ou outra geração |
| `GET /arquivos/curriculos/<nome>.pdf\|.docx` | — | o arquivo (PDF inline, .docx anexo); fora do padrão ou da pasta → `404` |
