# Implementation Plan: Análise de perfil contínua

**Branch**: `012-analise-perfil` (trabalho na `master` por worktree) | **Date**: 2026-10-10 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-analise-perfil/spec.md`

## Summary

Um módulo `analise_perfil.py` faz as três análises. Lacunas das vagas, sem IA: junta as lacunas da análise de cada
vaga e os requisitos do anúncio que a conferência de requisitos (spec 006) marca como lacuna, agrupa por termos
significativos, pesa pela aderência e por a pessoa ter seguido a vaga, e classifica em níveis, com mínimo de 5
vagas e as visões "seguidas" e "todas". Cargos-alvo e plano de estudo, com IA, só no clique, com a evidência
conferida no perfil. Prontidão internacional, sem IA, pelo perfil, pelos filtros internacionais e pelos currículos.
Cargos escolhidos vão para os filtros pela mesma montagem da spec 011, só com confirmação. As análises ficam em
`dash/dados/analises-perfil.json`. A página ganha o passo "Análises" em Meu perfil; a skill de perfil, os
comandos. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `dash/dados/analises-perfil.json` (fora do Git) ([data-model.md](data-model.md)).

**Testing**: `unittest` com vagas e perfil fictícios e IA falsa; quickstart com servidor no roteiro e Chrome sem
janela.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: ranking de lacunas em poucos segundos para centenas de vagas, sem IA.

**Constraints**: só no clique; só fatos do perfil; filtros só com confirmação; texto da internet é dado.

**Scale/Scope**: `analise_perfil.py` (novo), `dash/servidor.py` (rotas), `dash/dashboard.html` (passo Análises),
skill analisar-perfil, README, AGENTS.md, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Análises em `dash/dados/`; IA só no clique, com o perfil mascarado. |
| II. Pública, sem dados pessoais | ✅ Testes com dados fictícios. |
| III. Simples, sem IA obrigatória | ✅ Lacunas e prontidão sem IA; cargos e plano pedem IA (ou o chat). |
| IV. Só fatos confirmados | ✅ Evidência dos cargos conferida no perfil; plano não afirma experiência. |
| V. A pessoa decide | ✅ Tudo no clique; filtros só com confirmação. |
| VI. Respeito aos portais | ✅ Não consulta portais. |
| Restrições técnicas | ✅ Sem dependência nova. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/012-analise-perfil/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── analises.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
analise_perfil.py              # novo: lacunas, prontidão, cargos-alvo, plano, filtros com cargos, salvar, linha de comando
dash/servidor.py               # rotas /api/analises-perfil…
dash/dashboard.html            # passo "Análises" em Meu perfil (três seções)
.agents/skills/analisar-perfil/SKILL.md (+ sincronizar_skills.py), README.md, AGENTS.md
tests/test_analise_perfil.py
```

**Structure Decision**: um módulo próprio que reaproveita a conferência de requisitos (spec 006), a montagem de
filtros (spec 011), o seu currículo (spec 011) e a IA escolhida (spec 002).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
