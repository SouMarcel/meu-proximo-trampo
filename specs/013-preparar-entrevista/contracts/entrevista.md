# Contrato: preparação para entrevista

## Rotas (as que gravam ou chamam a IA, só deste computador)

| Rota | O que faz |
|---|---|
| `GET /api/entrevista/<vaga>` | preparação da vaga: dossiê, perguntas, histórias, salário, simulação, rodadas, se há IA |
| `PUT /api/entrevista/<vaga>/empresa` | `{texto}` grava o texto colado sobre a empresa |
| `POST /api/entrevista/<vaga>/resumo` | IA: resumo do dossiê com a origem de cada ponto |
| `POST /api/entrevista/<vaga>/perguntas` | IA: perguntas prováveis a mais |
| `POST /api/entrevista/<vaga>/historias` | IA: rascunhos de histórias (não grava) |
| `POST /api/entrevista/historias` | `{historia}` grava (confirmação da pessoa); com `id`, atualiza |
| `DELETE /api/entrevista/historias/<id>` | remove uma história |
| `POST /api/entrevista/<vaga>/simulacao` | `{pergunta, resposta, idioma}` → grava a resposta e, com IA, o retorno |
| `POST /api/entrevista/<vaga>/rodada` | `{etapa, perguntas, bem, mal, proximos}` grava como foi |

## Módulo `entrevista.py`

```text
preparacao(vaga) -> dict          dossie(vaga, prep) -> dict          perguntas(vaga, perfil, prep) -> list
salario(vaga, perfil) -> dict     resumo_ia(vaga, texto) -> dict      perguntas_ia(vaga, perfil) -> list
historias_ia(perfil, perguntas) -> list     salvar_historia(h) / listar_historias() / remover_historia(id)
retorno_ia(pergunta, resposta, perfil, historias, idioma) -> dict     registrar_resposta / registrar_rodada
```

## Linha de comando

```text
PY entrevista.py preparar <vaga>     # dossiê, perguntas e salário (sem IA)
PY entrevista.py historias           # o banco de histórias
```
