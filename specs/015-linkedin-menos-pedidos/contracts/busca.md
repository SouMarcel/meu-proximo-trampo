# Contrato: começar uma busca durante a espera e com muitos cargos

## Página (`dash/buscador.py`, `dash/servidor.py`)

`GET /api/busca/plano` (o `plano()` de hoje) ganha:

```json
{
  "espera": [{"portal": "LinkedIn", "ate": "2026-10-15T15:12", "motivo": "excesso de pedidos"}],
  "so_espera": false,
  "aviso_cargos": "Mais de 5 cargos com LinkedIn ou Indeed aumentam o risco de bloqueio."
}
```

`espera` vem vazia fora da espera, e `aviso_cargos` vem `null` sem aviso.

`POST /api/busca` aceita `confirmar_espera` (bool):

| Situação | Resposta |
|---|---|
| `so_espera` | 409 `"O LinkedIn está em espera até HH:MM e é o único portal ligado: não há o que buscar agora."` |
| `espera` não vazia e sem `confirmar_espera` | 409 com `precisa_confirmar`: `"O LinkedIn está em espera até HH:MM (motivo) e vai ficar de fora. Confirme para buscar só com os outros portais."` |
| confirmado | a busca começa; o resumo traz o aviso de espera em `erros` |

A recusa da busca recente (`confirmar_recente`) continua igual. O diálogo manda as duas confirmações quando mostra os
dois avisos.

Diálogo de busca:
- linha "LinkedIn em espera até HH:MM (motivo): fica de fora desta busca";
- linha com `aviso_cargos`, quando houver;
- botão "Buscar sem o LinkedIn" quando há espera;
- com `so_espera`, o botão fica desligado e a mensagem explica.

## Terminal (`vagas.py buscar`)

| Situação | Comportamento | Código de saída |
|---|---|---|
| `aviso_cargos` | imprime o aviso antes da primeira consulta e segue | — |
| espera e todas as fontes em espera | imprime o aviso; não busca | 5 |
| espera, terminal interativo | pergunta `Seguir sem o LinkedIn? [s/N]`; "s" segue, qualquer outra coisa sai | 0 / 5 |
| espera, sem terminal interativo e sem `--confirmar-espera` | imprime o aviso e como confirmar; não busca | 5 |
| espera com `--confirmar-espera` | busca sem o LinkedIn; o resumo repete o aviso | o de sempre |

Os códigos 2, 3 e 4 continuam com o mesmo sentido.

## Skill buscar-vagas (chat)

Se `vagas.py buscar` sair com o código 5:
1. mostrar o aviso à pessoa;
2. perguntar, com opções, se segue só com os outros portais;
3. se ela confirmar, repetir o comando com `--confirmar-espera`.

Não repetir a busca por conta própria.
