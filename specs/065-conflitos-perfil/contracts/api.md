# Contrato: rotas do Meu perfil que mudam (spec 065)

Todas **[local]**, como hoje. Só o que muda; o resto segue `dash/API.md`.

## `GET /api/perfil/estado`

`rascunho.gerado_em?: string` e `rascunho.conflitos[].opcoes[].nota?: string` passam a vir.

## `POST /api/perfil/rascunho` `{sem_ia?: bool}`

Igual a hoje, mais: as escolhas do rascunho anterior que casam (mesmo `campo` e mesmo `valor`, normalizados) já vêm
marcadas no novo.

## `POST /api/perfil/previa` `{markdown?}`

Resposta de hoje mais:

```json
{
  "perfil_versao": "a1b2c3d4e5f60718",
  "aviso": {
    "rascunho_em": "2026-11-20T10:00:00",
    "perfil_em": "2026-11-27T16:19:00",
    "sairiam": ["- Item que está no perfil e não no texto novo", "### Um cargo"],
    "pode_refazer": true
  }
}
```

`aviso` é `null` quando não se aplica (sem perfil, rascunho sem IA, rascunho mais novo que o perfil, ou data
desconhecida e nada sairia). Com `markdown`, `sairiam` é recalculado sobre o texto editado.

## `PUT /api/perfil` `{markdown*, perfil_versao?}`

- `perfil_versao` igual ao do perfil gravado (ou ambos sem perfil): grava como hoje.
- Diferente: **409** `{"erro": "O perfil mudou depois que você abriu a Revisão. Veja de novo o que muda antes de gravar."}`.
- Sem `perfil_versao`: grava como hoje (compatível com chamadas antigas).
