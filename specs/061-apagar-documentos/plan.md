# Implementation Plan: Documento apagado na página some da pasta

**Branch**: `061-apagar-documentos` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

Generalizar a lixeira do currículo (spec 052) para cartas e respostas, apagar em lote os documentos de uma vaga (tudo
ou nada) ao remover a vaga do quadro e ao arquivar pela Limpeza, e um comando para os documentos órfãos de hoje.

## Technical Context

Python 3 só com biblioteca padrão (backend), React + TypeScript na branch `frontend-react` (front). Documentos ficam
em `curriculo_ia.CURRICULOS` (`curriculos/`, fora do Git): `<nome>.meta.json` com `tipo` (sem tipo = currículo,
`carta`, `respostas`), `alvo` (`{"tipo": "base"}` ou `{"tipo": "vaga", "id": ...}`) e `arquivos` (`{json|txt|docx|pdf:
nome do arquivo}`). A vaga guarda os nomes em `curriculos` (lista) e `documentos` (`[{tipo, nome, criado_em}]`); na
junção de vagas repetidas (spec 058, `banco.py` ~1185) os nomes da vaga que sai passam para a que fica, mas o
`meta.alvo.id` continua com o id antigo.

## Constitution Check

- V (a pessoa decide): toda exclusão tem confirmação; o comando de órfãos só apaga com `--gravar` e o OK.
- Dados pessoais fora do Git: nada muda; os testes usam pasta temporária e nunca tocam `curriculos/` real.
- Sem dependência nova.

## Decisões

**D1. Apagar em lote** (`curriculo_ia.apagar_lote(nomes) -> list[dict]`): valida todos os nomes (`NOME_VALIDO`; sem
`.meta.json`: `FileNotFoundError`); para cada documento, os arquivos são os de `meta["arquivos"]` mais
`<nome>.meta.json` (e, por segurança, `<nome>.json|.txt|.docx|.pdf` se existirem). Fase 1: renomeia **todos** os
arquivos de **todos** os documentos para `…apagando`; um `OSError` desfaz tudo e levanta `GeracaoErro("um arquivo …
está aberto em outro programa; feche e tente de novo")`. Fase 2: `unlink(missing_ok=True)`. Devolve
`[{nome, tipo, alvo}]`. `apagar(nome)` vira `apagar_lote([nome])[0]` e passa a aceitar carta e respostas (sai o
bloqueio de hoje). Lista vazia devolve `[]`.

**D2. Documentos de uma vaga** (`curriculo_ia.documentos_da_vaga(vaga: dict) -> list[dict]`): os metas (com `nome`,
`tipo`) cujo nome está em `vaga["curriculos"]` ou em `vaga["documentos"][*]["nome"]`, ou cujo `alvo.id` é o
`vaga["id"]` ou está em `vaga["ids_relacionados"]`. Nunca os de `alvo.tipo == "base"`.

**D3. Órfãos** (`curriculo_ia.documentos_orfaos(vagas: list[dict]) -> list[dict]`): metas com `alvo.tipo == "vaga"`
que nenhuma vaga **viva** reclama (pela regra da D2). Vaga viva = não arquivada (`arquivada_em` vazio) e não
removida (removida = `triagem == "visitada"` e sem `etapa`). Cada item: `{nome, tipo, vaga_id, titulo, empresa,
criado_em, motivo}`, motivo `removida`, `arquivada` ou `vaga não encontrada` (pela vaga de `alvo.id`).

**D4. Ligações**: `banco.desligar_documento(vid, nome)` tira o nome de `doc["documentos"]` (como
`desligar_curriculo`). `DELETE /api/curriculo/<nome>` chama `desligar_curriculo` ou `desligar_documento` conforme o
tipo devolvido (e `reprovacao.esquecer_curriculo` só para currículo, como hoje).

**D5. Remover a vaga** (`DELETE /api/vagas/<id>`, `dash/servidor.py` ~1084): lê a vaga, `documentos_da_vaga`,
`apagar_lote` (409 com a mensagem se aberto, e a vaga fica), `reprovacao.esquecer_curriculo` para cada currículo,
depois `banco.remover(vid)` e zera `curriculos`/`documentos` da vaga se ela continuar no banco (não manual). Resposta
`{ok: true, documentos_apagados: [nomes]}`.

**D6. Limpeza** (`banco.limpar`): para cada vaga que vai ser **arquivada**, `documentos_da_vaga` + `apagar_lote`
antes de gravar a ficha. Falha: a vaga não é arquivada e entra em `nao_arquivadas: [{id, motivo}]` no retorno. A
ficha (`_ficha_curta`) troca `curriculos`/`documentos` por `documentos_apagados: {"curriculo": n, "carta": n,
"respostas": n, "em": "AAAA-MM-DD"}` (só quando havia algum). Encerrar (grupo `sem_resposta`) não apaga nada.
`banco` importa `curriculo_ia` sob demanda (como faz com `curriculo_base`).

**D7. Comando** `PY dash/banco.py documentos-orfaos [--gravar]`: sem `--gravar` lista (tipo, vaga, empresa, data,
motivo) e o total por tipo; com `--gravar`, `apagar_lote` dos listados e o resumo. Erro de arquivo aberto: sai com
código 1 e a mensagem.

**D8. Front, lixeira de carta e respostas** (`src/components/kit/Kit.tsx`, `ItemCarta` e `ItemRespostas`): botão
`Trash2` como o de `ItemCurriculo` (`curriculo/Curriculos.tsx` ~298-342), `window.confirm` com o texto da spec
(respostas: "as respostas que você editou também somem"), `curriculoApi.apagar(m.nome)`, recarrega a lista; erro
409 mostrado abaixo do item.

**D9. Front, remover vaga e Limpeza**: em `JobCard.tsx` (~222-262) e `modals/JobDetailModal.tsx` (~640-660), o texto
da confirmação conta os documentos pelo que a vaga já traz (`vaga.curriculos.length`, `vaga.documentos` por tipo):
"Também serão apagados: 1 currículo, 2 cartas e 3 respostas gerados para esta vaga." Sem documentos, texto de hoje.
Erro 409 do servidor aparece como aviso. Em `modals/LimpezaAba.tsx`, o aviso das destacadas diz que arquivar apaga
os documentos, e o resumo mostra `nao_arquivadas` quando houver.

## Estrutura

Backend: `curriculo_ia.py`, `dash/banco.py`, `dash/servidor.py`; testes em `tests/test_curriculo_ia.py`,
`tests/test_limpeza.py`. Front (`frontend-react`): `src/components/kit/Kit.tsx`, `src/components/JobCard.tsx`,
`src/components/modals/JobDetailModal.tsx`, `src/components/modals/LimpezaAba.tsx`, `src/services/api/*.ts`.
Docs: `dash/API.md`, `README.md`, `AGENTS.md`, nota em `specs/054-limpeza-vagas/spec.md`.
