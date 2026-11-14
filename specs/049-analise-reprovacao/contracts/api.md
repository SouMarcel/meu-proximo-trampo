# Contrato: análise de reprovação (entra em `dash/API.md` §3.8)

Todas as rotas que alteram algo são **[local]**: só funcionam neste computador (403 fora dele). A análise e a
reescrita usam a mesma fila do currículo, da carta e das respostas (409 `{erro, estado}` com outra geração rodando).

## Mudanças em rotas existentes

**`GET /api/curriculo/catalogo?vaga={id}`** ganha, só com `vaga`:

```json
"reprovacao": {"disponivel": true, "motivo": "", "anterior": "2026-11-12T14:30:00" }
```

- `disponivel: false` quando a vaga não tem descrição. Nesse caso, `motivo` traz "a vaga não tem descrição para
  analisar".
- `anterior` é a data da análise que será substituída, ou `null`.

**`GET /api/curriculo/estado`**:
- `tipo` ganha `"reprovacao"`;
- `situacao` ganha `"analisando"` e `"reescrevendo"`, que entram nas situações ativas;
- `etapa_texto` mostra "Analisando como um recrutador…" e "Reescrevendo os trechos genéricos…".

**`GET /api/curriculo/lista?vaga={id}`**: o meta do currículo gerado pela etapa 3 ganha `"reprovacao": true`.

## Rotas novas

**`POST /api/curriculo/reprovacao`** **[local]**: "Gerar" com o checkbox marcado.
- Corpo: `{vaga_id, tecnicas}`, com as mesmas técnicas de `POST /api/curriculo`.
- 202: estado (`tipo: "reprovacao"`, `situacao: "analisando"`).
- 400: sem IA, sem perfil, vaga sem descrição, técnica inválida. 404: vaga não encontrada. 409: ocupado.

**`GET /api/curriculo/reprovacao?vaga={id}`**: a última análise da vaga.
- 200: `{analise: Analise | null, pode_alterar}`.
- `Analise` segue [data-model.md](../data-model.md), com estes campos calculados:
  - `motivos[].estado`: `nao_tenho` | `tenho` | `sem_resposta` | `sem_pergunta`;
  - `resumo`: `{nao_tenho, tenho, sem_resposta}`;
  - `pronta_para_gerar`: bool;
  - `respostas_mudaram`: bool.

**`PUT /api/curriculo/reprovacao/{vaga_id}/respostas`** **[local]**: grava as respostas, também parciais.
- Corpo: `{respostas: {"<n>": {resposta: "nao"|"tenho"|"pular", relato?, destino?: "perfil"|"so_aqui"}}}`.
- 200: `{analise}`, com os campos calculados.
- 400:
  - pergunta inexistente;
  - resposta inválida;
  - destino inválido;
  - mudança do destino de uma resposta já levada ao perfil.
- 404: sem análise para a vaga.
- Um `tenho` com relato vazio é gravado, mas não conta como respondido.

**`POST /api/curriculo/reprovacao/{vaga_id}/gerar`** **[local]**: Reescrever e gerar o currículo.
- Corpo: `{}`.
- 202: estado (`tipo: "curriculo"`, `situacao: "reescrevendo"`).
- 400: perguntas sem resposta (`"responda ou pule as perguntas"`), sem IA, sem perfil. 404: sem análise. 409: ocupado.
- **`POST /api/curriculo/tentar`** repete a análise ou a reescrita que falhou.
