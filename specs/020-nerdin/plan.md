# Implementation Plan: Nerdin na busca de vagas

**Branch**: `020-nerdin` (worktree saída da `master`) | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/020-nerdin/spec.md`

## Summary

Uma fonte nova, `fontes/nerdin.py`, lê a busca pública da Nerdin (`vagas.php?busca=<cargo>&pagina=N`) com `urllib`
e `html.parser`, no molde do `fontes/linkedin.py`:
- a lista de cada cargo é lida uma vez por busca (até 5 páginas de 20 vagas, parando na primeira vaga mais antiga
  que a janela) e guardada para as outras consultas do mesmo cargo;
- cada consulta filtra essa lista: título que bate com o cargo (`_comum.bate_cargo`), modelo de trabalho do grupo
  e, na consulta da cidade, a cidade ou o estado;
- a descrição vem da página da vaga pelo JSON-LD `JobPosting`, reaproveitando `link.extrair_jobposting`, só para
  as vagas do relatório (`MAX_DESCRICOES = 30`);
- pausa de 3 s entre pedidos e, no primeiro bloqueio (403, 429, 503), a Nerdin sai do resto da busca, sem nova
  tentativa.

A Nerdin entra em `filtros.FONTES_NAC` e em `FONTES_PADRAO` (ligada por padrão); o `vagas.py` passa a usar
`FONTES_PADRAO` como padrão em vez da lista fixa. Dashboard, banco, Adicionar Vaga, README, AGENTS.md e a skill
buscar-vagas ganham o nome do portal. As decisões estão em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão: `urllib`, `html.parser`); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: nenhuma mudança de formato. `config.json` continua com a chave `fontes`; sem a chave, vale
`filtros.FONTES_PADRAO`, que passa a incluir `nerdin`. Vagas gravadas com `plataforma = "Nerdin"` e id `nerdin-<n>`.

**Testing**: `unittest` com HTML fictício em `tests/dados/nerdin/` e `nerdin._baixar` substituído; busca real pequena
na worktree; teste da página no dashboard da branch pessoal.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: pausa de 3 s por pedido. Uma busca com 3 cargos e janela de 24 h costuma fazer 1 página por
cargo (3 pedidos) mais até 30 páginas de vaga; no pior caso, 5 páginas × cargos + 30.

**Constraints**:
- só a parte pública, sem login nem cookies (o `PHPSESSID` que o site manda é ignorado: `urllib` não guarda cookie);
- parar no primeiro bloqueio, sem nova tentativa;
- descrição só das vagas do relatório;
- com a Nerdin desligada, saída idêntica à de antes.

**Scale/Scope**:
- `fontes/nerdin.py` (novo);
- `fontes/__init__.py`, `fontes/link.py`, `filtros.py`, `vagas.py`, `dash/banco.py`, `dash/dashboard.html`,
  `config.exemplo.json`;
- README, `dash/README.md`, AGENTS.md, skill buscar-vagas;
- testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o cargo vai à Nerdin; sem login, sem cookies, sem dado da pessoa. |
| II. Pública, sem dados pessoais | ✅ HTML de teste fictício (empresas e vagas inventadas); nada do usuário no código. |
| III. Simples, sem IA obrigatória | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos confirmados | ✅ Não se aplica; salário "a combinar" fica vazio (nada estimado). |
| V. A pessoa decide | ✅ Ligada por padrão só quando o config não tem a lista de portais; a lista que a pessoa escolheu não é alterada (FR-002); ela desliga no painel. Nada é gravado no config sem o clique dela. |
| VI. Respeito aos portais | ✅ Portal sem API aberta: só a busca pública, robots.txt permite `vagas.php` e `vaga_emprego/`, pausa de 3 s (maior que os 2 s das fontes com API), descrição só das candidatas, parar no primeiro bloqueio sem nova tentativa, sem candidatura automática. User-Agent da ferramenta, que se identifica. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` sem mudança; id prefixado (`nerdin-`). ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa**. Re-checado depois do desenho: sem mudança.

## Project Structure

### Documentation (this feature)

```text
specs/020-nerdin/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── nerdin.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
fontes/nerdin.py               # novo: lista por cargo (páginas, janela), leitura dos cards, filtro por consulta,
                               # pausa, bloqueio, descrever (JSON-LD), id_do_link
fontes/__init__.py             # registrar nerdin
fontes/link.py                 # plataforma("nerdin.") e ler() com o id nerdin-<n>
filtros.py                     # FONTES_NAC e FONTES_PADRAO com nerdin
vagas.py                       # fontes_da_busca: padrão = filtros.FONTES_PADRAO
dash/banco.py                  # PLATAFORMAS + "Nerdin"
dash/dashboard.html            # PLATAFORMAS, plataformaDoLink, cor da etiqueta
config.exemplo.json            # "fontes": ["indeed", "gupy", "nerdin"]
README.md, dash/README.md, AGENTS.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_nerdin.py, tests/dados/nerdin/{lista.html, lista-2.html, vaga.html}; ajustes em tests/test_linkedin.py
```

**Structure Decision**: uma fonte nova no molde do `linkedin.py` (HTML, pausa e bloqueio próprios), sem mudar o
contrato das fontes nem o `vagas.py` além do padrão de portais. A leitura da página da vaga reaproveita o
`link.extrair_jobposting`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
