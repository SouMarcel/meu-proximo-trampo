# Contratos: IA com reserva e aviso de indisponibilidade

## 1. `ia.py`

| Função | Contrato |
|---|---|
| `validar_escolha(dados)` | aceita `reservas` (lista, até 3); `ValueError` com a regra: "no máximo 3 reservas", "reserva repetida", "Sem IA não pode ser reserva", ou o erro da reserva (provedor, modelo, endereço) |
| `salvar_escolha(dados)` | grava `ia` com `reservas` (vazia = sem a chave `reservas`) |
| `sequencia(cfg=None)` | `[escolha principal, *reservas]`; `[]` quando a principal é "nenhum" |
| `responder(pedido, sistema=None, tempo=600, escolha=None, chave=None)` | sem `escolha`: percorre a sequência; com `escolha`: uma IA só. Devolve o texto; levanta `IAErro` (D4) |
| `ultima()` | `{provedor, modelo, nome, falhas}` da última chamada nesta thread, ou `None` |
| `aviso_reserva()` | o texto do aviso quando a última resposta veio de uma reserva; `None` se veio da principal ou não houve chamada |
| `marca()` | `{provedor, modelo}` de quem respondeu (+ `reserva`, `aviso` se foi reserva); sem chamada, a escolha efetiva |
| `situacao()` | `{"<provedor>|<modelo>": {ok, em, motivo}}` lido de `.cache/ia-estado.json` |
| `testar(escolha, chave=None)` | como hoje; também grava a situação |
| `estado_para_pagina(pode_alterar, ultimo_erro=None)` | o de hoje, mais `sequencia` e `alerta` (seção 2) |

## 2. Painel IA (`dash/API.md` §3.5)

**`GET /api/ia`**: o estado de hoje, mais:

```text
escolha: {provedor, modelo, url_base, reservas: [{provedor, modelo, url_base}]} | null
sequencia: [{provedor, nome, modelo, gratuito: bool, chave_ok: bool, principal: bool,
             situacao: {ok: bool, em: "AAAA-MM-DDTHH:MM", motivo: string} | null}]
alerta: {nome, modelo, motivo, em} | null      # a principal, quando a última tentativa com ela falhou
```

**`PUT /api/ia`**: o corpo de hoje (`{provedor, modelo, url_base, chave?}`), mais `reservas: [{provedor, modelo,
url_base}]`. Ele responde com o estado. Erro 400 com a regra do `validar_escolha`. Com `reservas` ausente, a lista
gravada continua como está; com `reservas: []`, a lista é apagada.

**`POST /api/ia/testar`**: o de hoje (`{provedor, modelo, url_base, chave?}` → `{ok, mensagem}`), e também grava a
situação daquela IA.

**`GET /api/versao`**: ganha `ia_alerta: {nome, modelo, motivo, em} | null`, o mesmo `alerta`.

## 3. Avisos nas funções

| Função | Onde o aviso aparece |
|---|---|
| Candidatura assistida: "Preencher esta página" | `aviso_ia` da resposta (já existe); com reserva, o texto de `aviso_reserva()` |
| Respostas de formulário, carta e currículo | `ia.aviso` no documento (`meta.ia`) |
| Análise do perfil | `ia.aviso` no resultado |
| Análise automática do relatório | situação no painel IA e alerta no botão IA |

## 4. Mensagens (D4)

- Reserva respondeu: `"{nome principal} fora: {motivo}. Respondeu o {nome da reserva} ({modelo})."`
- Todas falharam (mais de uma): `"nenhuma IA respondeu: {nome}: {motivo}; {nome}: {motivo}"`.
- Uma IA só, falhando: o motivo de hoje.
