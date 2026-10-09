# Implementation Plan: Currículo pela página

**Branch**: `007-curriculo-pela-pagina` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-curriculo-pela-pagina/spec.md`

## Summary

Um módulo novo, `curriculo_ia.py`, monta o pedido à IA (perfil sem documentos, vaga, técnicas, guia
`tecnicas.md`, `modelo.json` e a análise de requisitos da conferência), lê e valida a resposta e gera
os arquivos pelo motor da Fase 5 (`.json`, `.docx`, `.pdf`), roda a conferência e grava um
`.meta.json` ao lado. O servidor ganha `dash/gerador.py` (uma geração por vez, em segundo plano, com
andamento e "tentar de novo"), as rotas `/api/curriculo…` e a entrega dos arquivos da pasta
`curriculos/` com validação de nome e caminho. A vaga guarda a lista dos currículos gerados. A página
ganha a seção Currículos no detalhe da vaga (botão, diálogo de técnicas, lista com veredito e links)
e o Currículo base no diálogo Meu perfil. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+; JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: biblioteca padrão + `python-docx`; IA por `ia.py`; PDF pelo Word ou
LibreOffice. Nenhuma dependência nova.

**Storage**: `curriculos/` (fora do Git) com o `.meta.json`; campo `curriculos` na vaga
([data-model.md](data-model.md)).

**Testing**: `unittest` com `ia.responder` substituído; quickstart com servidor no roteiro, IA falsa
local e Word.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor Python + página).

**Performance Goals**: do clique ao PDF em até 3 minutos (dominado pela IA).

**Constraints**: nada enviado à IA sem confirmação; uma geração por vez; escrita só do próprio
computador; só arquivos de `curriculos/` servidos; "bloquear" nunca marcado como pronto.

**Scale/Scope**: 2 módulos novos (`curriculo_ia.py`, `dash/gerador.py`), rotas, seção na página,
uma função no banco, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Arquivos locais; à IA vai só perfil (mascarado), vaga, técnicas e guias; escrita só do próprio computador; entrega de arquivos restrita a `curriculos/`. |
| II. Pública, sem dados pessoais | ✅ Testes e exemplos fictícios. |
| III. Simples, leve, sem IA obrigatória | ✅ Sem dependência nova; sem IA, a página explica e o chat continua sendo o caminho. |
| IV. Só fatos confirmados | ✅ Pedido com as regras e as lacunas; conferência sem IA em todo currículo; "bloquear" = não pronto. |
| V. A pessoa decide | ✅ Só no clique, com técnicas escolhidas e aviso de custo; nada sobrescrito. |
| VI. Respeito aos portais | ✅ Não se aplica. |
| Restrições técnicas | ✅ Campo novo na vaga sem migração; servidor mantém host/origem. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/007-curriculo-pela-pagina/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-curriculo.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
curriculo_ia.py                  # novo: pedido à IA, leitura e validação, nomes, geração dos arquivos, meta, lista
dash/gerador.py                  # novo: geração em segundo plano (uma por vez, andamento, tentar de novo)
dash/servidor.py                 # rotas /api/curriculo… e /arquivos/curriculos/…
dash/banco.py                    # registrar_curriculo(vid, nome)
dash/dashboard.html              # seção Currículos no detalhe, diálogo de técnicas, currículo base em Meu perfil
README.md, dash/README.md        # currículo pela página
tests/test_curriculo_ia.py       # novo
```

**Structure Decision**: o pedido e a geração ficam na raiz (`curriculo_ia.py`), ao lado de
`curriculo.py` e `conferir.py`; o que é do servidor (segundo plano, rotas) fica em `dash/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
