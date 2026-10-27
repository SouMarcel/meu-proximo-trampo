# Data Model: IA com reserva e aviso de indisponibilidade

## Escolha de IA (`config.json` → `ia`)

| Campo | Tipo | Regra |
|---|---|---|
| `provedor` | id de `ia.PROVEDORES` | a principal; "nenhum" desliga a IA, e as reservas não são usadas |
| `modelo` | texto, até 120 | vazio = o padrão do provedor |
| `url_base` | texto | só em "outro compatível" (`https://`, ou `http://` local) |
| `reservas` | lista, até 3 | opcional; cada item `{provedor, modelo, url_base}` com as mesmas regras |

**Validação das reservas**:
- provedor da lista e diferente de "nenhum";
- nenhuma repetida: o mesmo provedor, modelo efetivo e endereço da principal ou de outra reserva;
- no máximo 3;
- nunca a chave.

Exemplo (configuração do usuário):

```json
"ia": {"provedor": "gemini", "modelo": "gemini-3.8-flash", "url_base": "",
       "reservas": [{"provedor": "openrouter", "modelo": "openrouter/free", "url_base": ""}]}
```

## Situação de cada IA (`.cache/ia-estado.json`, fora do Git)

```json
{"gemini|gemini-3.8-flash": {"ok": false, "em": "2026-10-27T14:32", "motivo": "o provedor está com problema agora (erro 503); tente mais tarde"},
 "openrouter|openrouter/free": {"ok": true, "em": "2026-10-27T14:32", "motivo": ""}}
```

- A chave é `provedor|modelo efetivo`.
- O registro é gravado a cada tentativa, inclusive no "Testar". Sem chave e sem texto do pedido.

## Última resposta (memória, por thread)

`{provedor, modelo, nome, falhas: [{provedor, nome, modelo, motivo}]}`, quem respondeu e quem falhou antes no último
`ia.responder` da thread. Serve a `ia.marca()` e a `ia.aviso_reserva()`.

## Marca da IA nos documentos

Os documentos gerados (currículo, carta, respostas, análises do perfil) guardam `ia: {provedor, modelo}` de quem
respondeu. Quando foi reserva, também `reserva: true` e `aviso: "<texto>"`.
