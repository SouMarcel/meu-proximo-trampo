# Implementation Plan: Começar pelo currículo que a pessoa já tem

**Branch**: `011-curriculo-existente` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-curriculo-existente/spec.md`

## Summary

Um módulo `curriculo_base.py` lê um currículo da pessoa (material dos primeiros passos ou arquivo de `anexos/`),
monta o perfil com o próprio texto (mascarado, com a origem), tira cargos, cidade e modelo de trabalho (sem IA por
padrões do texto; com IA, um pedido curto) e propõe os filtros pelo `propor_filtros` que já existe. Uma tela só, em
Meu perfil, mostra a proposta; confirmar grava perfil, filtros e o currículo base e abre o painel de busca. O
currículo base (um por idioma, em `config.json`) aparece no item Currículo do checklist de cada vaga, com link e
"Pronto". A anamnese fica para completar depois. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão; pypdf e python-docx, que já existem); JavaScript ES5 no
`dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `config.json → curriculo_base` e `perfil.md` (fora do Git); nada novo no banco
([data-model.md](data-model.md)).

**Testing**: `unittest` com currículos fictícios (PDF e DOCX gerados no teste) e IA falsa; quickstart com servidor
no roteiro e Chrome sem janela.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: proposta em poucos segundos sem IA; checklist com o currículo base sem atraso na listagem.

**Constraints**: nada gravado sem confirmação; só o texto do currículo no perfil; documentos de identificação
nunca no perfil nem na IA; link do currículo só para o arquivo marcado e só neste computador.

**Scale/Scope**: `curriculo_base.py` (novo), `primeiros_passos.py` (material de `anexos/` sem copiar, origem do
perfil), `dash/kit.py` e `dash/banco.py` (item Currículo com o currículo base), `dash/servidor.py` (rotas),
`dash/dashboard.html` (botão, tela de confirmação, seção "Seu currículo", aviso em Meu perfil, item do checklist),
skill analisar-perfil, README, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Currículo e perfil só neste computador; o arquivo só é servido para o próprio computador. |
| II. Pública, sem dados pessoais | ✅ Testes com currículos fictícios gerados no teste; `curriculo_base` só no `config.json`. |
| III. Simples, sem IA obrigatória | ✅ Caminho inteiro sem IA; IA só melhora a proposta dos filtros. |
| IV. Só fatos confirmados | ✅ Perfil = texto do próprio currículo; máscara de documentos; filtros editáveis. |
| V. A pessoa decide | ✅ Uma confirmação antes de gravar; a busca só começa no clique. |
| VI. Respeito aos portais | ✅ Não muda as consultas. |
| Restrições técnicas | ✅ Sem dependência nova. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/011-curriculo-existente/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── curriculo-base.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
curriculo_base.py              # novo: candidatos, leitura, perfil do currículo, dados e proposta, confirmar, marcar
primeiros_passos.py            # adicionar_existente (arquivo de anexos/ sem copiar); perfil_do_curriculo no estado
dash/kit.py, dash/banco.py     # item Currículo com o currículo base do idioma da vaga
dash/servidor.py               # rotas /api/perfil/curriculos, /do-curriculo, /api/curriculo-base, arquivo do currículo base
dash/dashboard.html            # "Usar este currículo", tela de confirmação, "Seu currículo", aviso, item do checklist
.agents/skills/analisar-perfil/SKILL.md (+ sincronizar_skills.py), README.md, AGENTS.md
tests/test_curriculo_base.py
```

**Structure Decision**: a regra do "começar pelo currículo" fica num módulo próprio que reaproveita a leitura e a
gravação dos primeiros passos e a proposta de filtros; o checklist só recebe a informação do currículo base.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
