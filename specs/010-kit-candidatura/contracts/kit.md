# Contrato: kit de candidatura

## Rotas

| Rota | O que faz |
|---|---|
| `GET /api/vagas` | cada vaga traz também `checklist` e `lembretes_pendentes` (calculados) |
| `PATCH /api/vagas/<id>` | aceita `kit`, `lembretes` e `entrevista_em` (validados); `400` com a explicação |
| `POST /api/kit/carta` | `{vaga_id, respostas: {por_que, problema, primeiro_movimento, tom}}` → inicia a geração; `400` se falta resposta, IA ou perfil; `409` se já há geração |
| `POST /api/kit/respostas` | `{vaga_id, perguntas: texto}` → separa as sensíveis e inicia a geração das outras |
| `PUT /api/kit/respostas/<nome>` | `{pessoa: {indice: texto}}` → grava as respostas da pessoa como ela escreveu |
| `GET /api/kit/lista?vaga_id=` | cartas e respostas da vaga (pelos `.meta.json`) |
| `GET /api/curriculo/estado` | o estado da geração, agora com `tipo` |
| `GET /arquivos/curriculos/<nome>` | também `.txt` |

## Módulos

```text
dash/kit.py        checklist(v) -> list ; lembretes(v, hoje) -> list ; validar_kit(d) ; validar_lembretes(d)
candidatura_ia.py  sensivel(pergunta) -> str|None ; separar(texto) -> list ; gerar_carta(vaga, respostas) ; gerar_respostas(vaga, perguntas)
conferir.py        conferir_carta(texto, perfil, vaga, respostas) -> {veredito, itens} ; conferir_respostas(itens, perfil)
```

## Linha de comando

```text
PY conferir.py --carta carta.txt [--vaga-id ID] [--respostas respostas.json]
PY candidatura_ia.py sensiveis perguntas.txt
PY dash/banco.py kit <id>          # checklist e lembretes da vaga
PY dash/banco.py lembretes         # lembretes pendentes de todas as vagas
```
