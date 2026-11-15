# Contrato da API: revisão do perfil (spec 050)

Rotas novas em `dash/servidor.py`. As marcadas **[local]** só aceitam pedidos deste computador (403 de fora). A origem é
`vaga:<id>` (análise de reprovação) ou `relatos` (Seus relatos).

## `POST /api/perfil/revisao` [local]

"Revisar e levar ao perfil".

- Corpo: `{origem, relatos?: [id]}`. Na origem `vaga:<id>`, `relatos` é ignorado: entram os `para_revisar` da análise.
  Em `relatos`, `relatos` é obrigatório (1 a 20 ids).
- 202: o estado do gerador (`tipo: "revisao_perfil"`, `situacao: "revisando"`).
- 200 sem IA: `{sem_ia: true, levados: [id], anterior, aviso}`. Os relatos foram para a seção "Relatos", como hoje.
- 400: origem inválida, nenhum relato para revisar, relato inexistente, sem perfil.
- 404: vaga sem análise de reprovação.
- 409: outra geração rodando.

## `GET /api/perfil/revisao?origem=`

`{revisao: Revisao|null, pode_alterar}`. `Revisao` segue o [data-model](../data-model.md), sem o `perfil_sha`, com:
- `pode_gravar` (bool) e `motivo` (ex.: "responda às discordâncias", "o seu perfil mudou desde a proposta; revise de
  novo");
- `relatos_info`: `[{id, pergunta, relato}]`, para mostrar de onde veio cada item.

## `PUT /api/perfil/revisao/decisoes` [local]

- Corpo: `{origem, itens?: {<id>: bool}, discordancias?: {<id>: {escolha: "perfil"|"relato"|"correcao", correcao?}}}`.
  Decisões parciais são aceitas.
- 200: `{revisao}`.
- 400: item inválido (`valido: false`) marcado como aceito, escolha desconhecida, correção vazia, revisão já gravada.
- 404: sem revisão nessa origem.

## `POST /api/perfil/revisao/gravar` [local]

- Corpo: `{origem}`.
- 200: `{revisao, anterior, aceitos, relatos: [id levados]}`.
- 400: discordância sem escolha, nenhum item aceito, documento ou conflito recusado pela gravação do perfil.
- 404: sem revisão.
- 409: o perfil mudou desde a proposta (nada é gravado).

## `DELETE /api/perfil/revisao?origem=` [local]

Descarta a proposta (não mexe no perfil nem nos relatos). 200 `{revisao: null}`.

## Mudanças em rotas existentes

- `GET /api/curriculo/reprovacao?vaga=`: `analise` ganha `para_revisar: [id]` e `levadas_em: ISO|null`.
- `POST /api/curriculo/reprovacao/{id}/gerar`: as respostas "Levar ao meu perfil" vão para Seus relatos, à espera de
  revisão, e não para o `perfil.md`.
- `POST /api/perfil/relatos/{id}/perfil`: sem mudança (caminho sem IA; a página usa a revisão quando há IA).
- `GET /api/curriculo/estado`: `tipo` ganha `revisao_perfil`, `situacao` ganha `revisando`, `alvo` pode ser
  `{perfil: true}`.
