# Implementation Plan: Primeiros passos e anamnese

**Branch**: `004-primeiros-passos` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-primeiros-passos/spec.md`

## Summary

Um módulo `primeiros_passos.py` (raiz) concentra a lógica: ler PDF (`pypdf`, única dependência
nova), Word (`python-docx`) e a exportação do LinkedIn (`zipfile` + `csv`); mascarar documentos de
identificação e reconhecer contato; pedir o rascunho à IA escolhida (`ia.responder`) com fonte por
item e conflitos; catálogo da anamnese; diagnóstico por regras; montar o `perfil.md` no formato do
modelo; comparar com o perfil atual e guardar a versão anterior; propor filtros. O servidor ganha as
rotas `/api/perfil/…` (escrita só do próprio computador) e a página um assistente "Primeiros passos"
em etapas, que abre sozinho sem perfil. A mesma lógica serve a uma skill de chat
(`analisar-perfil`), pelos comandos `extrair` e `diagnostico`. Decisões em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+; JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: biblioteca padrão; `python-docx` (já existe); **`pypdf` (nova)** para PDF.

**Storage**: `anexos/primeiros-passos/` (arquivos), `.cache/primeiros-passos.json` (progresso),
`perfil.md` e `anexos/perfis-anteriores/` (versões), `config.json` (filtros) — tudo fora do Git
([data-model.md](data-model.md)).

**Testing**: `unittest` com materiais fictícios gerados nos testes (docx por python-docx, PDF mínimo
gerado à mão, ZIP com CSVs) e provedor de IA falso local; quickstart.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor Python + página).

**Performance Goals**: rascunho com IA ≤ 2 min; ZIP do LinkedIn lido ≤ 10 s; primeiros passos
completos ≤ 15 min.

**Constraints**: nada gravado sem confirmação; documentos de identificação nunca vão à IA nem ao
perfil; escrita só do próprio computador; arquivos ≤ 10 MB; sem abrir o LinkedIn.

**Scale/Scope**: 1 módulo novo, rotas novas no servidor, um assistente em etapas na página, 1 skill
nova, ajuste no `perfil.exemplo.md`, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Arquivos e progresso locais, fora do Git; CPF/RG/nascimento retirados antes da IA; contato só com confirmação; escrita só do próprio computador. |
| II. Pública, sem dados pessoais | ✅ Testes e exemplos com dados fictícios; nenhum material real no repositório. |
| III. Simples, leve, sem IA obrigatória | ⚠️ Uma dependência nova (`pypdf`, puro Python), justificada: a biblioteca padrão não lê PDF e o currículo/LinkedIn quase sempre vem em PDF. Todos os passos funcionam sem IA. |
| IV. Só fatos confirmados | ✅ Rascunho só com o que está nos materiais, com fonte; números só confirmados; conflitos resolvidos pela pessoa. |
| V. A pessoa decide | ✅ Gravação só na revisão confirmada; comparação antes de sobrescrever; filtros propostos, não aplicados. |
| VI. Respeito aos portais | ✅ O LinkedIn não é acessado; só arquivos que a pessoa baixou. |
| Restrições técnicas | ⚠️ Verificação só no Windows (desvio já registrado nas specs anteriores). |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa**, com a dependência nova e o desvio de plataforma justificados.

## Project Structure

### Documentation (this feature)

```text
specs/004-primeiros-passos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-perfil.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
primeiros_passos.py              # novo: extração, máscara, rascunho, anamnese, diagnóstico, perfil, filtros, CLI
requirements.txt                 # + pypdf
perfil.exemplo.md                # comentário corrigido + seções opcionais (Contato, Trabalho no exterior, Regras de verbo)
dash/servidor.py                 # rotas /api/perfil/… (limite de 15 MB só no envio de material)
dash/dashboard.html              # botão "Meu perfil" e assistente "Primeiros passos" em etapas
.agents/skills/analisar-perfil/SKILL.md   # nova skill (fonte); cópia em .claude/skills/ via sincronizar_skills.py
sincronizar_skills.py            # SKILLS ganha "analisar-perfil"
AGENTS.md, README.md             # skill nova e primeiros passos
tests/test_primeiros_passos.py   # novo
```

**Structure Decision**: módulo na raiz, como `ia.py`, porque é usado pelo servidor e pela skill de
chat (por linha de comando).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dependência nova `pypdf` | Ler o texto de currículos e do PDF do LinkedIn | A biblioteca padrão não lê PDF; mandar o PDF à IA não funciona sem IA nem no Claude Code sem ferramentas |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
