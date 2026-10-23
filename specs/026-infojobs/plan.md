# Implementation Plan: InfoJobs na busca de vagas e pausa por portal

**Branch**: `026-infojobs` (worktree `../meu-proximo-trampo-026`, saída da `master`) | **Date**: 2026-10-23 |
**Spec**: [spec.md](spec.md)

## Summary

**Mecanismos comuns** em `fontes/_comum.py`, chamados com os atributos de cada módulo, para que trocar `ARQ_ESPERA`,
`PAUSA` ou `segredos.ler` nos testes continue valendo:
- `pausa_do_env(var, padrao, minimo, maximo, faixa)`: a pausa de `<NOME>_PAUSA`;
- `aviso_pausa(...)`: o aviso do começo da busca;
- `pausar(estado, faixa)`: o sorteio e o sono entre os pedidos;
- `gravar_espera(arq, motivo)` / `ler_espera(arq, duracao)`: a espera depois de um bloqueio;
- `baixar_pagina(...)`: um pedido HTML sem cookies, sem nova tentativa, com bloqueio em 403/429/503 ou login;
- `UFS` e `na_regiao(...)`, movidos da Nerdin.

**Portais que já existem**: o LinkedIn passa a usar esses helpers com o mesmo comportamento. A Nerdin ganha
`NERDIN_PAUSA` (padrão e mínimo de 3 s, sem sorteio). `vagas.aviso_pausa` junta o aviso de cada portal com a
variável definida.

**Fonte nova `fontes/infojobs.py`**:
- lista `empregos.aspx?palabra=<cargo>&Antiguedad=<n>`, uma página por cargo (a URL não pagina, research R2);
- na consulta da cidade, a lista `vagas-de-emprego-<cargo>-em-<cidade>.aspx` com o mesmo filtro de data;
- filtro por título, modelo e cidade/UF;
- descrição pelo `JobPosting`, no máximo 30 por busca;
- pausa sorteada de 3 a 7 s (`INFOJOBS_PAUSA`) e espera de 24 h em `.cache/infojobs-espera.json`.

Registro em `fontes/__init__.py`, `filtros.FONTES_NAC` e `FONTES_PADRAO`, `fontes/link.py`, `dash/banco.py`,
`.env.exemplo`, `config.exemplo.json`, documentação e skill. O front fica na branch `frontend-react`.

## Technical Context

**Language/Version**: Python 3.10+, biblioteca padrão (`urllib`, `html.parser`). Front: TypeScript na
`frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- `.cache/infojobs-espera.json` (fora do Git, como a do LinkedIn);
- vagas com `plataforma = "InfoJobs"` e id `infojobs-<n>`;
- `config.json` sem mudança de formato.

**Testing**: `unittest` com HTML fictício em `tests/dados/infojobs/`, sem rede; os testes atuais do LinkedIn e da
Nerdin como não regressão; uma busca real pequena na worktree.

**Constraints**: só a parte pública, sem cookies; parar no primeiro bloqueio; nenhum pedido durante a espera;
`LINKEDIN_PAUSA` idêntica.

**Scale/Scope**: uma busca com 3 cargos e cidade faz até 6 pedidos de lista e até 30 de vaga ao InfoJobs. Com 3 a
7 s de pausa, são cerca de 3 a 4 min só de pausa no pior caso.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o cargo e a cidade vão ao InfoJobs; sem login, cookies ou dados da pessoa. A espera fica em `.cache/`. |
| II. Pública, sem dados pessoais | ✅ HTML de teste fictício; `.env.exemplo` sem valores. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos | ✅ Salário só quando informado; empresa "Confidencial" como o portal mostra. |
| V. A pessoa decide | ✅ Ligado por padrão só sem a lista de portais (FR-002); a espera pergunta antes de seguir. |
| VI. Respeito aos portais | ⚠️ Os termos do InfoJobs proíbem scripts e crawlers sem autorização (research R1). A pessoa decidiu seguir como no LinkedIn (23/10/2026), ciente disso. Mitigações: só a busca pública, pausa sorteada, 1 página por cargo, descrição só das candidatas, parar no primeiro bloqueio, espera de 24 h, aviso no painel. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` sem mudança; id prefixado. |
| Fluxo | ✅ Spec → plano → tarefas; testes; verificação rodando. A pessoa dispensou a aprovação etapa por etapa nesta spec. |

Resultado: passa, com o desvio do princípio VI justificado abaixo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Termos do InfoJobs contra robôs | Decisão da pessoa: o InfoJobs traz vagas generalistas e presenciais que faltam nos outros portais | "Só o link" ou pedir autorização ao InfoJobs foram oferecidos e recusados (23/10/2026) |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |

## Project Structure

```text
fontes/_comum.py        # pausa_do_env, aviso_pausa, pausar, gravar_espera, ler_espera, baixar_pagina, UFS, na_regiao
fontes/linkedin.py      # pausa(), aviso_pausa(), _pausar, _bloquear, espera() pelos helpers (mesmo comportamento)
fontes/nerdin.py        # NERDIN_PAUSA, aviso_pausa(); UFS do _comum
fontes/infojobs.py      # novo
fontes/__init__.py, fontes/link.py, filtros.py, vagas.py (aviso_pausa genérico), dash/banco.py
.env.exemplo (novo), config.exemplo.json, README.md, dash/README.md, dash/API.md, AGENTS.md, docs/novo-portal.md,
.agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_infojobs.py, tests/test_pausa_portal.py, tests/dados/infojobs/{lista.html, vaga.html}
frontend-react: src/types/api.ts, src/utils/formatters.ts, src/components/modals/AddJobModal.tsx
```
