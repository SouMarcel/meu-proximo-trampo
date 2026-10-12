# Implementation Plan: Preparação para entrevista

**Branch**: `013-preparar-entrevista` (trabalho na `master` por worktree) | **Date**: 2026-10-12 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-preparar-entrevista/spec.md`

## Summary

Um módulo `entrevista.py` monta a preparação de cada vaga: dossiê (vaga, análise, kit, anotações, texto colado sobre
a empresa) e perguntas prováveis (lista padrão comportamental, técnicas pelos requisitos do anúncio, lacunas da análise
e perguntas que caíram antes), sem IA; com IA e no clique, o resumo do dossiê com a origem de cada ponto, mais
perguntas, rascunhos de histórias STAR conferidos contra o perfil e o retorno da simulação, conferido contra o perfil
e as histórias. Salário só com a faixa da vaga e a pretensão do perfil. Histórias (banco comum) e preparações (por
vaga) ficam em `entrevistas/`, nova pasta fora do Git. Botão no card de Entrevista e no detalhe; skill nova
preparar-entrevista. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `entrevistas/historias.json` e `entrevistas/vaga-<id>.json` (fora do Git) ([data-model.md](data-model.md)).

**Testing**: `unittest` com perfil e vagas fictícios e IA falsa; quickstart com servidor no roteiro e Chrome sem janela.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: preparação sem IA em poucos segundos.

**Constraints**: só no clique; só fatos do perfil; nada de pesquisa na internet; salário sem valor inventado; dados da
pessoa fora do Git.

**Scale/Scope**: `entrevista.py` (novo), `dash/servidor.py` (rotas), `dash/dashboard.html` (botão e diálogo),
skill preparar-entrevista, `.gitignore`, AGENTS.md, README, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ `entrevistas/` fora do Git; IA só no clique, com o perfil mascarado; sem pesquisa na internet. |
| II. Pública, sem dados pessoais | ✅ Testes com dados fictícios; `.gitignore` ganha `entrevistas/`. |
| III. Simples, sem IA obrigatória | ✅ Dossiê, perguntas, histórias à mão, simulação sem retorno, salário e anotações sem IA. |
| IV. Só fatos confirmados | ✅ Histórias e retornos conferidos contra o perfil; salário só com valores da vaga e do perfil. |
| V. A pessoa decide | ✅ Tudo no clique; histórias salvas só na confirmação. |
| VI. Respeito aos portais | ✅ Não consulta portais nem a internet. |
| Restrições técnicas | ✅ Sem dependência nova. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/013-preparar-entrevista/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── entrevista.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
entrevista.py                  # novo: preparação, dossiê, perguntas, histórias, simulação, salário, rodadas, linha de comando
dash/servidor.py               # rotas /api/entrevista/…
dash/dashboard.html            # botão "Preparar entrevista" (card de Entrevista e detalhe) e o diálogo
.agents/skills/preparar-entrevista/SKILL.md (+ sincronizar_skills.py), AGENTS.md, README.md, .gitignore
tests/test_entrevista.py
```

**Structure Decision**: um módulo próprio que reaproveita a leitura de requisitos e a conferência de fatos
(`conferir.py`), a máscara de documentos (`primeiros_passos.py`) e a IA escolhida.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
