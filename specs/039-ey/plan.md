# Implementation Plan: EY (careers.ey.com) na busca de vagas

**Branch**: `039-ey` (worktree `../mpt-039-ey`, saída da `master`; serve também à spec 040) | **Date**: 2026-10-30 |
**Spec**: [spec.md](spec.md)

## Summary

**Fonte nova `fontes/ey.py`**, no molde de `fontes/vagascom.py` (lista em HTML com páginas), com o bloqueio da Nerdin
(sem espera):
- lista: `careers.ey.com/ey/search/?q=<cargo>&locationsearch=<país>&sortColumn=referencedate&sortDirection=desc`,
  `startrow` de 25 em 25, até 2 páginas por cargo, lida uma vez por busca e guardada para as consultas do mesmo cargo;
- filtro pelo título (`_comum.bate_cargo`) antes de abrir qualquer página de vaga;
- a lista não tem data: **a busca abre a página da vaga** das que passaram no título, para ler data, locais e
  descrição (microdados schema.org), até 20 páginas por busca, e para ao chegar à primeira vaga mais antiga que a janela;
- **memória de datas** (`.cache/ey-datas.json`, fora do Git): número da vaga → data de publicação e locais. Uma vaga
  já lida não tem a página aberta de novo nas próximas buscas (as que já estão no dashboard só custariam pedidos);
- `descrever()` devolve a descrição lida na busca, sem pedido; só abre a página quando a vaga ainda não tem texto
  (Forçar verificar, spec 021);
- id `ey-<número>`; pausa sorteada de 3 a 7 s (`EY_PAUSA`, de 3 a 60); no primeiro bloqueio, a EY sai do resto da
  busca, sem nova tentativa e sem espera.

**Adicionar Vaga**: `careers.ey.com/<site>/job/…/<número>/` é reconhecido; a página é lida pelos microdados
(`ey.ler_pagina`), com o mesmo id da busca.

**Ligada por padrão**: entra em `filtros.FONTES_NAC` e `FONTES_PADRAO` e no `config.exemplo.json`.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`urllib`, `html.parser`, `json`). Front em TypeScript, na
`frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- `.cache/ey-datas.json`, fora do Git: `{"<número>": {"data": "AAAA-MM-DD" | null, "locais": [[cidade, UF], …],
  "lida_em": "AAAA-MM-DD"}}`; entradas lidas há mais de 60 dias saem na gravação seguinte;
- vagas com `plataforma = "EY"` e id `ey-<número>`;
- `config.json` sem mudança de formato: `"ey"` na lista `fontes`.

**Testing**: `unittest` com HTML fictício em `tests/dados/ey/` (lista com 2 páginas, página de vaga com microdados,
página de vaga sem data) e `ey._baixar` trocado, sem rede. Os testes atuais de pausa, Vagas.com, Nerdin, link e
integridade servem de não regressão. No fim, uma busca real pequena na worktree.

**Constraints**:
- só as páginas liberadas no robots.txt (`/ey/search/` e `/ey/job/`); nada em `/services/` (FR-009);
- sem cookies e sem login;
- parar no primeiro bloqueio, sem nova tentativa;
- EY desligada pela pessoa: nenhum pedido.

**Scale/Scope**:
- 3 cargos: até 6 páginas de lista e 20 páginas de vaga na primeira busca, cerca de 2 minutos de pausa no pior caso;
- nas buscas seguintes, as vagas já lidas vêm da memória: em geral só as páginas de lista.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o cargo e o país vão à EY, sem login, cookies ou dados da pessoa. A memória de datas fica em `.cache/` e não guarda nada da pessoa. |
| II. Pública, sem dados pessoais | ✅ HTML de teste fictício (títulos, cidades e textos trocados). `.env.exemplo` sem valores. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos | ✅ Data e locais como a página informa; sem data legível, a vaga entra sem data. "Banco de talentos" e PCD só no `tipo`, sem filtro. |
| V. A pessoa decide | ✅ Ligada por padrão por decisão da pessoa (30/10/2026); desliga no painel. |
| VI. Respeito aos portais | ✅ robots.txt respeitado (sem RSS), termos sem cláusula contra robôs (research R1), pausa sorteada, até 26 pedidos por busca, memória que evita repetir pedidos, parada no primeiro bloqueio. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` sem mudança; id prefixado. |
| Fluxo | ✅ Spec aprovada em 30/10 → plano → tarefas. |

Resultado: passa, sem emenda.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Páginas de vaga abertas dentro da busca | A lista não tem data; sem ela, a janela de tempo não vale e vagas antigas ("Banco de Talentos" de meses atrás) entrariam no relatório | Deixar sem data: o relatório encheria de vagas velhas na primeira busca |
| Memória de datas em `.cache/` | As fontes não sabem quais vagas o dashboard já tem; sem a memória, cada busca reabriria as mesmas páginas | Reabrir sempre: até 20 pedidos repetidos por busca, contra "só o necessário" |

## Project Structure

### Documentation (this feature)

```text
specs/039-ey/
├── spec.md, plan.md, research.md (R1–R5 + decisões técnicas D1–D6)
├── contracts/ey.md (funções, formato da vaga e da memória)
├── quickstart.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
fontes/ey.py            # novo: buscar, descrever, ler_pagina, pausa, aviso_pausa, parada, id_do_link
fontes/__init__.py      # import e registro em FONTES
filtros.py              # FONTES_NAC e FONTES_PADRAO
fontes/link.py          # PLATAFORMAS_LINK; ler(): link da EY pela página (ey.ler_pagina), mesmo id
integridade.py          # PORTAIS: "EY": ("careers.ey.com",)
dash/banco.py           # PLATAFORMAS
.env.exemplo            # EY_PAUSA comentada
config.exemplo.json     # "ey" em fontes
README.md, dash/README.md, dash/API.md, AGENTS.md
.agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_ey.py, tests/dados/ey/{lista-1.html, lista-2.html, vaga.html, vaga-sem-data.html}
frontend-react: src/types/api.ts, src/utils/formatters.ts, src/components/modals/AddJobModal.tsx (com a spec 040)
```

**Structure Decision**: uma fonte nova no molde do Vagas.com (lista guardada por cargo, `_comum.baixar_pagina`,
pausa por `.env`), sem espera, como a Nerdin. O leitor de microdados fica em `fontes/ey.py` (`ler_pagina`), porque só
a EY usa; `link.extrair_jobposting` continua só com JSON-LD. O front muda uma vez para as duas specs.
