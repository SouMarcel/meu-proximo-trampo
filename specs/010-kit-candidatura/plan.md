# Implementation Plan: Kit de candidatura ("indica, não faz")

**Branch**: `010-kit-candidatura` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-kit-candidatura/spec.md`

## Summary

A análise automática ganha sete campos (autorização, contratação, inglês, fuso, sistema de
candidatura, o que a candidatura pede e riscos), cada um com a frase do anúncio, no mesmo pedido de
hoje. Um módulo `dash/kit.py` calcula, para toda vaga, o checklist "o que esta candidatura pede"
(itens de toda vaga, da análise, das palavras do anúncio e da pessoa, com o estado gravado na vaga)
e os lembretes de follow-up (7 e 14 dias em Aplicação Enviada, dia seguinte à entrevista). Um módulo
`candidatura_ia.py`, no molde do `curriculo_ia.py`, escreve a carta (quatro respostas obrigatórias)
e as respostas de formulário (perguntas sensíveis separadas antes da IA), com a conferência de fatos
do `conferir.py` estendida para texto corrido. A página mostra tudo no detalhe da vaga e nos cards; a
skill no chat segue as mesmas regras. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão; python-docx, que já existe, para a carta em
.docx); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: campos novos na vaga (sem migração) e documentos em `curriculos/` (fora do Git)
([data-model.md](data-model.md)).

**Testing**: `unittest` com IA falsa local, perfil e vagas fictícios; quickstart com servidor no
roteiro e Chrome sem janela; uma carta com a IA real só com o OK do usuário.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: checklist e lembretes calculados na listagem sem atraso perceptível (centenas
de vagas); análise com o mesmo número de chamadas de hoje.

**Constraints**: nada gerado, aberto ou enviado sem clique; perguntas sensíveis nunca vão à IA; carta
só com fatos do perfil e das respostas; texto da vaga é dado.

**Scale/Scope**: `dash/kit.py` e `candidatura_ia.py` (novos), `conferir.py`, `dash/banco.py`
(validação e linha de comando), `dash/analise.py`, `dash/gerador.py`, `dash/servidor.py`,
`dash/dashboard.html`, skills buscar-vagas e gerar-curriculo, README, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Cartas e respostas em `curriculos/`, fora do Git; só vão ao provedor de IA escolhido, no clique. |
| II. Pública, sem dados pessoais | ✅ Testes com perfil e vagas fictícios; padrões neutros. |
| III. Simples, sem IA obrigatória | ✅ Checklist, lembretes e conferências sem IA; carta e respostas pedem IA (ou o chat). |
| IV. Só fatos confirmados | ✅ Conferência bloqueia fato fora do perfil; perguntas sensíveis só com a pessoa; análise cita a frase. |
| V. A pessoa decide | ✅ Tudo no clique; botão de candidatura só abre o link; lembrete só lembra. |
| VI. Respeito aos portais | ✅ Nenhuma leitura ou automação de formulário de candidatura. |
| Restrições técnicas | ✅ Sem dependência nova; campos novos sem migração. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/010-kit-candidatura/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── kit.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
dash/kit.py                    # novo: checklist(v), lembretes(v, hoje), validação do estado da pessoa
candidatura_ia.py              # novo: carta e respostas pela IA; perguntas sensíveis; linha de comando
conferir.py                    # conferir_carta, conferir_respostas, --carta
dash/banco.py                  # validar_analise (campos novos), _validar_usuario (kit, lembretes, entrevista_em),
                               # documentos da vaga, comandos kit e lembretes
dash/analise.py                # campos novos no pedido (pela skill)
dash/gerador.py                # fila com o tipo (currículo, carta, respostas)
dash/servidor.py               # rotas /api/kit/…, checklist e lembretes na listagem, .txt servido
dash/dashboard.html            # detalhe (análise nova, checklist, carta, respostas), card com lembretes
.agents/skills/buscar-vagas/SKILL.md, .agents/skills/gerar-curriculo/SKILL.md (+ sincronizar_skills.py)
README.md, dash/README.md
tests/test_kit.py, tests/test_candidatura.py
```

**Structure Decision**: o que é da vaga (checklist, lembretes) fica junto do banco, em `dash/`; o que
escreve com IA fica na raiz, ao lado do `curriculo_ia.py`, reaproveitando a fila, a pasta e a
conferência que já existem.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
