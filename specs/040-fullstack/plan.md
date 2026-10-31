# Implementation Plan: FullStack (talent.fullstack.com) na busca de vagas

**Branch**: `039-ey` (worktree `../mpt-039-ey`, saída da `master`; mesma da spec 039) | **Date**: 2026-10-30 |
**Spec**: [spec.md](spec.md)

## Summary

**Fonte nova `fontes/fullstack.py`**, no molde de `fontes/jobgether.py` (JSON, espera de 24 horas):
- lista: `GET https://api-v1.fullstack.com/api/job-postings/public?page=N&take=30&filter=countryId=<id do país>`, os
  mesmos pedidos que a página faz, sem login e sem cookies;
- lida **uma vez por busca** (não por cargo), até 10 páginas (a API não ordena por data; a janela é filtrada aqui), e
  guardada para todas as consultas; cada consulta filtra pelo título (`_comum.bate_cargo`) e pela data;
- a mesma vaga publicada em várias cidades vira uma (`jobId`); id `fullstack-<jobId>`;
- descrição pelo detalhe da publicação (`GET /api/job-postings/<id>`, seções em HTML), só das vagas do relatório,
  `MAX_DESCRICOES = 30`;
- e-mail do recrutador e ids internos descartados na leitura;
- pausa sorteada de 3 a 7 s (`FULLSTACK_PAUSA`, de 3 a 60); no primeiro 401, 403, 429 ou 503, sem nova tentativa,
  fora do resto da busca e 24 horas em espera (`.cache/fullstack-espera.json`), com os helpers de `fontes/_comum.py`.

**Área**: nacional, consultas remota e do país, só com o país da pessoa = Brasil (o único identificador de país
conhecido; os outros não fazem pedido). A consulta da cidade não faz pedido.

**Desligada por padrão**: entra em `filtros.FONTES_NAC`, fora de `FONTES_PADRAO`, com `TERMOS` dizendo que os termos
proíbem acesso automatizado.

**Adicionar Vaga**: `talent.fullstack.com/jobs/<id>` (com ou sem `/apply`) é reconhecido; `fullstack.ler(url)` faz um
pedido ao detalhe e devolve a vaga com o mesmo id da busca. Na espera, nenhum pedido: `LinkErro` com o link e a
plataforma, e a pessoa completa à mão.

**Candidatura assistida**: sem mudança (FR-011).

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`urllib`, `json`). Front em TypeScript, na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- `.cache/fullstack-espera.json`, fora do Git;
- vagas com `plataforma = "FullStack"` e id `fullstack-<uuid da vaga>`;
- `config.json` sem mudança de formato: `"fullstack"` na lista `fontes`, quando a pessoa liga.

**Testing**: `unittest` com JSON fictício em `tests/dados/fullstack/` (duas páginas da lista, com a mesma vaga em duas
cidades, e um detalhe) e `fullstack._baixar` trocado, sem rede. Os testes de pausa, JobGether, link e integridade
servem de não regressão. No fim, uma busca real pequena na worktree, com a FullStack ligada só nela.

**Constraints**:
- desligada por padrão; desligada, nenhum pedido;
- só os pedidos públicos que a página faz, sem login e sem cookies;
- parar no primeiro bloqueio; nenhum pedido durante a espera (busca, descrição e Adicionar Vaga);
- nenhum e-mail de recrutador gravado.

**Scale/Scope**:
- até 10 páginas de lista (264 publicações do Brasil hoje = 9 páginas) e 30 detalhes por busca, com qualquer número
  de cargos: cerca de 3 minutos de pausa no pior caso; a lista do Brasil (9 páginas hoje) custa cerca de 45 s de
  pausa por busca.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o país vai à FullStack (o cargo é filtrado aqui), sem login, cookies ou dados da pessoa. A espera fica em `.cache/`. |
| II. Pública, sem dados pessoais | ✅ JSON de teste fictício (títulos, cidades, ids e e-mails trocados). O `ownerEmail` da API não é gravado. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos | ✅ Modelo, contrato, senioridade e data como a API informa; FULL_TIME no exterior fica sem código de CLT, como no JobGether. |
| V. A pessoa decide | ✅ Desligada por padrão; a espera pergunta antes de seguir sem ela (código 5). |
| VI. Respeito aos portais | ⚠️ Os termos proíbem acesso automatizado (research R1). Coberto pela regra "Termos contrários": decisão da pessoa registrada na spec (30/10/2026), termos resumidos no painel, desligada por padrão. Sem API oficial, só os pedidos públicos da página. Mitigações: lista uma vez por busca, pausa sorteada, parada no primeiro bloqueio, espera de 24 h. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` sem mudança; id prefixado. |
| Fluxo | ✅ Spec aprovada em 30/10 → plano → tarefas. |

Resultado: passa, sem emenda (a regra de "Termos contrários" já existe).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Termos da FullStack contra acesso automatizado | Decisão da pessoa (30/10/2026), desligada por padrão | Deixar de fora foi oferecido e recusado |
| API interna, não documentada | É o único jeito de ler as vagas: a página é um app em JavaScript e não há API oficial | Ler o HTML: não traz as vagas |
| Candidatura assistida liberada mesmo com os termos | Decisão da pessoa (30/10/2026, FR-011) | Bloquear o domínio, como no JobGether, foi proposto e recusado |

## Project Structure

### Documentation (this feature)

```text
specs/040-fullstack/
├── spec.md, plan.md, research.md (R1–R5 + decisões técnicas D1–D7)
├── contracts/fullstack.md (funções, formato da vaga)
├── quickstart.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
fontes/fullstack.py     # novo: buscar, descrever, ler, pausa, aviso_pausa, espera, parada, id_do_link
fontes/__init__.py      # import e registro em FONTES
filtros.py              # FONTES_NAC (fora de FONTES_PADRAO)
fontes/link.py          # PLATAFORMAS_LINK; ler(): link da FullStack por fullstack.ler
integridade.py          # PORTAIS: "FullStack": ("talent.fullstack.com",)
dash/banco.py           # PLATAFORMAS
.env.exemplo            # FULLSTACK_PAUSA comentada
README.md, dash/README.md, dash/API.md, AGENTS.md (portal com termos contrários, desligado)
.agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_fullstack.py, tests/dados/fullstack/{lista-1.json, lista-2.json, detalhe.json}
frontend-react: src/types/api.ts, src/utils/formatters.ts, src/components/modals/AddJobModal.tsx (com a spec 039)
```

**Structure Decision**: fonte nova no molde do JobGether: `_baixar` próprio (GET com `Accept: application/json`,
sem nova tentativa; 401, 403, 429 e 503 viram bloqueio), espera e parada com os helpers de `_comum`. A leitura do link
fica em `fullstack.ler`, porque o id da busca (`jobId`) só vem do detalhe.
