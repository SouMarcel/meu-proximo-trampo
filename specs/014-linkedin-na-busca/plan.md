# Implementation Plan: LinkedIn na busca de vagas

**Branch**: `014-linkedin-na-busca` (trabalho na `master` por worktree) | **Date**: 2026-10-12 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-linkedin-na-busca/spec.md`

## Summary

Uma fonte nova, `fontes/linkedin.py`, consulta a busca pública de convidado do LinkedIn com `urllib`. Cada grupo de
`filtros.consultas` vira uma consulta com o local e o modelo certos:
- remoto no país;
- país inteiro;
- cidade com raio;
- cada país de fora;
- mudança;
- "Worldwide".

Os tipos de emprego e a janela vão como filtro do próprio LinkedIn.

A descrição vem por `descrever()`, que reaproveita `link._ler_linkedin`, só para as candidatas. O módulo controla a
pausa de 3 a 7 s e para no primeiro bloqueio, sem nova tentativa. O contrato das fontes ganha `GLOBAL` para o
LinkedIn rodar também na consulta global.

Os portais nacionais (Indeed, Gupy, LinkedIn, startup.jobs) passam a ser escolhidos no painel "Filtros da busca", com
o LinkedIn desligado por padrão.

A constituição recebe a emenda 2.0.0 do princípio VI, e o AGENTS.md, o README e a skill buscar-vagas são atualizados.
As decisões estão em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão: `urllib`, `html.parser`); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova. O LinkedIn não passa pelo jobspy.

**Storage**: `config.json` ganha `fontes` pelo painel (a chave já existia, só pelo arquivo ou pelo terminal).

**Testing**: `unittest` com HTML fictício e `_baixar` substituído; servidor no roteiro e Chrome sem janela; busca real
pequena com o OK do usuário.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: pausa de 3 a 7 s por pedido ao LinkedIn. Uma busca típica (3 termos, remoto + 1 país) faz
cerca de 6 consultas, mais as descrições das candidatas.

**Constraints**:
- sem login nem conta da pessoa;
- parar no primeiro bloqueio;
- descrição só das candidatas;
- com o LinkedIn desligado, saída idêntica à de antes.

**Scale/Scope**:
- `fontes/linkedin.py` (novo);
- `fontes/__init__.py`, `vagas.py`, `filtros.py`, `dash/dashboard.html`;
- a constituição, o AGENTS.md, o README e a skill buscar-vagas;
- os testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nenhum dado da pessoa vai ao LinkedIn além do termo e do local da busca; sem login, sem cookies. |
| II. Pública, sem dados pessoais | ✅ HTML de teste fictício; nada do usuário no código. |
| III. Simples, sem IA obrigatória | ✅ Biblioteca padrão; nenhuma dependência nova; funciona sem IA. |
| IV. Só fatos confirmados | ✅ Não se aplica (a busca não escreve nada sobre a pessoa). |
| V. A pessoa decide | ✅ O LinkedIn vem desligado; a pessoa liga no painel. |
| VI. Respeito aos portais | ⚠️ **Muda nesta spec** (emenda MAJOR 2.0.0, decisão do usuário): sai "sem raspar o LinkedIn". Entram: só a busca pública, sem login, pausa maior, descrição só das candidatas, parar no primeiro bloqueio sem contornar, sem automação de candidatura, perfil nunca lido de portais. Com a emenda, passa. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` (ganha `GLOBAL`, documentado); ids prefixados (`li-`). ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa com a emenda do princípio VI**, registrada em Complexity Tracking. Re-checado depois do desenho:
sem mudança.

## Project Structure

### Documentation (this feature)

```text
specs/014-linkedin-na-busca/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── linkedin.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
fontes/linkedin.py             # novo: parâmetros, leitura dos cards, pausa, bloqueio, descrever, tipo de emprego
fontes/__init__.py             # registrar linkedin; documentar GLOBAL
vagas.py                       # atende com GLOBAL; documento copia tipo_emprego da fonte
filtros.py                     # FONTES_NAC, opcoes()["fontes_nac"], validar/efetivos com fontes; grupo global com o LinkedIn
dash/dashboard.html            # seção Portais em "Filtros da busca"; contador com as consultas do LinkedIn
.specify/memory/constitution.md, AGENTS.md, README.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_linkedin.py, tests/dados/linkedin/{lista.html, vaga.html}
```

**Structure Decision**: uma fonte nova no molde das fontes existentes. A leitura da vaga reaproveita o `link.py`; os
critérios, a área e a elegibilidade continuam em `filtros.py`, sem caminho especial para o LinkedIn.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Emenda do princípio VI (sai "sem raspar o LinkedIn") | Decisão do usuário: o LinkedIn concentra a maior parte das vagas | Importar a busca feita no navegador: rejeitada pelo usuário, que quer o LinkedIn na busca automática |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
