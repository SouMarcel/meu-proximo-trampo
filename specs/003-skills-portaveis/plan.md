# Implementation Plan: Skills portáveis

**Branch**: `003-skills-portaveis` (trabalho na `master` por worktree) | **Date**: 2026-10-08 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-skills-portaveis/spec.md`

## Summary

As três skills de usuário passam a ter a fonte em `.agents/skills/` (lida por Codex, Gemini CLI,
OpenCode e Antigravity) e uma cópia gerada e versionada em `.claude/skills/` (o Claude Code só lê
lá), mantida por `sincronizar_skills.py` com conferência que falha em qualquer diferença — sem links
simbólicos. `AGENTS.md` vira a fonte das instruções comuns (`CLAUDE.md` com `@AGENTS.md`;
`.gemini/settings.json` apontando para ele). O texto das skills troca as quatro dependências
exclusivas por instruções neutras com alternativa, e a consulta à Gupy ganha um comando
(`PY consultar_gupy.py …`) para assistentes sem o MCP. README com uma seção por assistente. Decisões
em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (script de sincronização e comando da Gupy); Markdown (skills,
AGENTS.md); JSON (`.gemini/settings.json`).

**Primary Dependencies**: biblioteca padrão; nenhuma nova.

**Storage**: arquivos do repositório; nenhum dado.

**Testing**: `unittest` (`tests/test_skills.py`: cópias iguais à fonte; `tests/test_gupy_cli.py`:
conversão de `chave=valor`); verificação manual pelo [quickstart.md](quickstart.md) no Claude Code
e, se houver chave paga, no Gemini CLI.

**Target Platform**: Windows 10/11; assistentes: Claude Code, Codex CLI, Gemini CLI, OpenCode.

**Project Type**: aplicação local; esta feature mexe em instruções e skills.

**Performance Goals**: consulta à Gupy pelo comando em até 30 s.

**Constraints**: sem links simbólicos; uma fonte por skill; Claude Code sem mudança de
comportamento; `AGENTS.md` < 32 KiB; conteúdo das skills (regras, formatos) intacto.

**Scale/Scope**: 3 skills, 1 script, 1 comando novo no `fontes/gupy.py`, 3 arquivos de instrução e
configuração, README, 2 testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nada novo sai do computador; o comando da Gupy usa o mesmo serviço público. |
| II. Pública, sem dados pessoais | ✅ AGENTS.md e skills genéricos; a seção pessoal do graphify vai para o `CLAUDE.local.md` (fora do Git). |
| III. Simples, leve, sem IA obrigatória | ✅ Biblioteca padrão; "skills de conversa portáveis" é parte do princípio (provedor não exclusivo). |
| IV. Só fatos confirmados | ✅ Regras das skills inalteradas; sem ferramenta de leitura, pede o texto em vez de supor. |
| V. A pessoa decide | ✅ Mantido nas skills e repetido no AGENTS.md. |
| VI. Respeito aos portais | ✅ Gupy pelo serviço oficial (MCP ou o mesmo endpoint), nunca pelo site. |
| Restrições técnicas | ⚠️ Verificação só no Windows e só nos assistentes instalados (Claude Code; Gemini CLI se houver chave paga). |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; conferência automática das cópias. |

Resultado: **passa**, com os desvios de verificação registrados.

## Project Structure

### Documentation (this feature)

```text
specs/003-skills-portaveis/
├── plan.md
├── research.md
├── quickstart.md
├── contracts/
│   └── estrutura-e-comandos.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

(Sem `data-model.md`: a feature não tem dados.)

### Source Code (repository root)

```text
AGENTS.md                         # novo: instruções comuns
CLAUDE.md                         # novo: "@AGENTS.md"
.gemini/settings.json             # novo: context.fileName + MCP da Gupy
.agents/skills/                   # novo: fonte das 3 skills (movidas de .claude/skills)
.claude/skills/{buscar-vagas,consultar-gupy,gerar-curriculo}/   # cópia gerada
sincronizar_skills.py             # novo: gerar e conferir as cópias
fontes/gupy.py                    # + uso por linha de comando (main)
consultar_gupy.py                 # novo: script na raiz que chama gupy.main()
dash/analise.py                   # SKILL aponta para .agents/skills/buscar-vagas/SKILL.md
tests/test_skills.py, tests/test_gupy_cli.py   # novos
README.md, dash/README.md         # caminhos e seção por assistente
```

**Structure Decision**: a pasta neutra `.agents/skills/` é a fonte porque três dos quatro
assistentes (e o Antigravity) a leem nativamente; o Claude Code recebe a cópia gerada.

**Passo na branch pessoal (fora da master)**: antes do merge, mover a seção do graphify do
`CLAUDE.md` local para o `CLAUDE.local.md`, apagar o `CLAUDE.md` local e tirar `CLAUDE.md` do
`.git/info/exclude`; senão o merge recusa sobrescrever o arquivo não versionado.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cópia gerada e versionada em `.claude/skills/` | O Claude Code só lê essa pasta e não aceita outra | Links simbólicos quebram no Windows; plugin local prefixa as skills e pede diálogo de confiança |
| Verificação só no Windows e só nos assistentes instalados | Decisão do usuário (Windows) e Codex/OpenCode ausentes nesta máquina | Instalar todos os assistentes só para testar foge da economia combinada |
