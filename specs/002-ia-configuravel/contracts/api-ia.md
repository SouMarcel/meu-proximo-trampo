# Contrato: rotas de IA do servidor local

Todas seguem as proteções atuais de `dash/servidor.py` (host permitido; escrita só com JSON e
origem local). As de escrita exigem também pedido vindo do próprio computador (127.0.0.1/::1);
senão `403 {"erro": "Só dá para mudar a IA no computador onde a ferramenta roda."}`.

## `GET /api/ia`

```json
{
  "escolha": {"provedor": "gemini", "modelo": "<nome>", "url_base": ""},
  "efetiva": "gemini",
  "provedores": [
    {"id": "gemini", "nome": "Gemini (Google)", "precisa_chave": true, "cobranca": "uso",
     "modelo_padrao": "<nome>", "url_padrao": "https://…", "onde_obter_chave": "https://…"}
  ],
  "chaves": {"gemini": {"cadastrada": true, "final": "a1B2", "origem": "arquivo"}},
  "claude_instalado": true,
  "pode_alterar": true,
  "ultimo_erro": null
}
```

Nunca devolve chave.

## `PUT /api/ia`

Corpo: `{"provedor", "modelo"?, "url_base"?, "chave"?}`. `chave` presente e não vazia → grava no
`.env`; ausente → mantém a atual. Valida pelo [data-model.md](../data-model.md); erro → `400`.
Resposta: igual ao `GET`. Efeito: agenda `FILA.pedir()` se a escolha efetiva tiver IA.

## `POST /api/ia/testar`

Corpo: `{"provedor", "modelo"?, "url_base"?, "chave"?}` (a `chave` do corpo é usada só no teste e
não é gravada; sem ela, usa a salva). Resposta `200 {"ok": true, "mensagem": "Conexão funcionando
(gemini · <modelo>)."}` ou `200 {"ok": false, "mensagem": "<motivo legível>"}`. Tempo limite: 15 s
(30 s no Claude Code).

## `DELETE /api/ia/chave/<provedor>`

Remove a variável do provedor no `.env`. `200` com o mesmo corpo do `GET`. Chave vinda do ambiente
do sistema não é removida (a resposta avisa que está definida fora da ferramenta).

## `GET /api/versao` (existente, campo novo)

Acrescenta `"ia_erro": {"motivo": "...", "em": "AAAA-MM-DDTHH:MM"}` ou `null`.

## `GET /api/config` (existente, ajuste)

`existe` passa a ser `true` só quando há cargos (`termos`) configurados.

# Contrato: `ia.py` (para as fases seguintes)

```text
ia.escolha_efetiva(cfg=None) -> {"provedor", "modelo", "url_base"}
ia.disponivel() -> bool                      # há IA e, no claude_code, o comando existe
ia.responder(pedido, sistema=None, tempo=600, escolha=None, chave=None) -> str   # levanta IAErro
ia.testar(escolha, chave=None) -> (ok: bool, mensagem: str)
ia.mascarar(texto) -> str
ia.PROVEDORES                                 # catálogo da research.md §2
```
