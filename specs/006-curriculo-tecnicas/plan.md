# Implementation Plan: Currículo com técnicas

**Branch**: `006-curriculo-tecnicas` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-curriculo-tecnicas/spec.md`

## Summary

O `curriculo.py` ganha o catálogo único de técnicas e escolhas (`TECNICAS`, `ESCOLHAS`, `sugerir`,
`--tecnicas`) e passa a ler `tecnicas` e `destaques` do JSON: formato do país (papel e idioma),
estilo (margens, espaços e fonte, corpo ≥ 10 pt), ordem (competências primeiro, destaques) e limite
de páginas medido no PDF, com sugestões de corte. Sem `tecnicas`, gera como hoje. Um módulo novo,
`conferir.py`, faz a conferência sem IA: ATS no documento, requisitos da vaga × perfil (tem,
sustentado, lacuna) e fatos (números, empresas, cargos, datas) contra o perfil, com veredito ok,
conferir ou bloquear. A skill `gerar-curriculo` pergunta as técnicas com caixas de marcar, segue o
novo guia `tecnicas.md` e roda a conferência antes de entregar. Decisões em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+.

**Primary Dependencies**: biblioteca padrão + `python-docx` (já existe); PDF pelo Word ou
LibreOffice (já existe). Nenhuma dependência nova.

**Storage**: `curriculos/` (fora do Git); o JSON do currículo guarda as técnicas
([data-model.md](data-model.md)).

**Testing**: `unittest` com currículo, perfil e vaga fictícios; quickstart com o Word do Windows.

**Target Platform**: Windows 10/11.

**Project Type**: ferramenta de linha de comando + skill de chat (a página fica para a Fase 6).

**Performance Goals**: conferência ≤ 5 s sem IA.

**Constraints**: nada inventado; corpo ≥ 10 pt; uma coluna, sem tabelas nem imagens; sem foto em
nenhum formato; currículo sem técnicas igual ao de hoje.

**Scale/Scope**: `curriculo.py` (técnicas, formato, estilo, páginas), 1 módulo novo (`conferir.py`),
skill (`SKILL.md`, `tecnicas.md`, `modelo.json`), testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Currículos e conferência locais; nada sai da máquina. |
| II. Pública, sem dados pessoais | ✅ Testes e exemplos fictícios (`modelo.json`). |
| III. Simples, leve, sem IA obrigatória | ✅ Sem dependência nova; motor e conferência sem IA. |
| IV. Só fatos confirmados | ✅ Conferência bloqueia número fora do perfil e aponta lacuna como competência; XYZ só com número confirmado. |
| V. A pessoa decide | ✅ Técnicas por caixas de marcar; sugestão trocável; nada gerado sem pedido. |
| VI. Respeito aos portais | ✅ Não se aplica (sem consultas). |
| Restrições técnicas | ✅ Campo novo no JSON sem quebrar o antigo. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/006-curriculo-tecnicas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-curriculo.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
curriculo.py                              # TECNICAS, ESCOLHAS, sugerir, --tecnicas; formato, estilo, ordem, destaques, limite de páginas; conferência no fim
conferir.py                               # novo: ATS, requisitos × perfil, fatos, veredito; linha de comando
.agents/skills/gerar-curriculo/SKILL.md   # passo Técnicas, conferência antes de entregar (cópia via sincronizar_skills.py)
.agents/skills/gerar-curriculo/tecnicas.md   # novo: como escrever cada técnica
.agents/skills/gerar-curriculo/modelo.json   # + tecnicas e destaques
sincronizar_skills.py                     # (se preciso) copiar arquivos extras da skill
README.md                                 # currículo com técnicas e conferência
tests/test_curriculo.py, tests/test_conferir.py   # novos
```

**Structure Decision**: o motor continua em `curriculo.py`; a conferência fica num módulo próprio
na raiz porque também será usada pela página na Fase 6.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
