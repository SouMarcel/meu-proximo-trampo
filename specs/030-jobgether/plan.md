# Implementation Plan: JobGether na busca de vagas

**Branch**: `030-jobgether` (worktree `../meu-proximo-trampo-030`, saída da `master`) | **Date**: 2026-10-25 |
**Spec**: [spec.md](spec.md)

## Summary

**Fonte nova `fontes/jobgether.py`**, que segue o contrato de `fontes/__init__.py` e lê a API oficial:
- `POST https://jobgether.com/api/v1/jobs` com corpo JSON, porque o robots.txt bloqueia query string;
- cargo sem aspas, local do país (`brazil`, `united-states`…) ou `anywhere` na consulta global, `sort: "date"` e
  `limit: 25`;
- até 3 páginas, parando na janela de tempo ou quando `hasMore` é falso;
- filtro pelo título (`_comum.bate_cargo`), sem descrição;
- id `jobgether-<id da URL>`;
- pausa de 2 s (`JOBGETHER_PAUSA`, de 2 a 60);
- no 403 ou 429, para sem nova tentativa e fica 24 h em espera (`.cache/jobgether-espera.json`), com os helpers da
  spec 026 em `fontes/_comum.py`.

**Áreas** (como o LinkedIn: `AREAS` com as duas, `POR_PAIS = True`, `GLOBAL = True`):
- nacional: consultas remota e do país;
- internacional: por país e a global (`anywhere`);
- fora: a da cidade e as de mudança.

O portal entra em `filtros.FONTES_NAC`, fora de `FONTES_PADRAO`. A consulta global passa a existir também quando o
JobGether está na lista de portais, como já acontece com o LinkedIn.

**Adicionar Vaga**: o link `jobgether.com/offer/<id>-…` é reconhecido, mas a página não é pedida. O `LinkErro` leva o
link e a plataforma, e o formulário abre para a pessoa completar. Ao gravar, `banco.criar_manual` usa o id
`jobgether-<id>` tirado do link. Assim, a vaga já trazida pela busca não duplica.

**Outros pontos**:
- `jobgether.com` entra em `candidatura/dominios.BLOQUEADOS`;
- emenda MINOR da constituição (4.0.0 → 4.1.0), com a seção "Termos contrários" no princípio VI;
- documentação, skill e front (na `frontend-react`).

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`urllib`, `json`). Front em TypeScript, na
`frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- `.cache/jobgether-espera.json`, fora do Git;
- vagas com `plataforma = "JobGether"` e id `jobgether-<24 hex>`;
- `config.json` sem mudança de formato: `"jobgether"` na lista `fontes`, quando a pessoa liga.

**Testing**: `unittest` com JSON fictício em `tests/dados/jobgether/` e `jobgether._baixar` trocado, sem rede. Os
testes atuais de pausa, LinkedIn, InfoJobs e fontes internacionais servem de não regressão. No fim, uma busca real
pequena na worktree.

**Constraints**:
- só a API oficial;
- sem cookies e sem pedido às páginas do site (403 e termos);
- parar no primeiro bloqueio;
- nenhum pedido durante a espera;
- portal desligado: nenhum pedido.

**Scale/Scope**:
- 4 cargos na busca nacional: até 12 pedidos (3 páginas por cargo), cerca de 24 s de pausa;
- cada país da internacional e a consulta global somam até 3 pedidos por cargo;
- o limite da API é de 60 pedidos por minuto (research R6).

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o cargo e o local vão ao JobGether, sem login, cookies ou dados da pessoa. A espera fica em `.cache/`. |
| II. Pública, sem dados pessoais | ✅ JSON de teste fictício, com empresas e títulos trocados. `.env.exemplo` sem valores. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos | ✅ Salário como o portal informa, sem período inventado. Sem descrição inventada: a nota fica provisória (spec 021). |
| V. A pessoa decide | ✅ Desligado por padrão. A espera pergunta antes de seguir sem ele (código 5). |
| VI. Respeito aos portais | ⚠️ Os termos (4.5 e 9) proíbem acesso automatizado (research R1). Resolvido pela emenda da spec (FR-012), abaixo. Mitigações: só a API para assistentes, pausa do `Crawl-delay`, até 3 páginas, parar no primeiro bloqueio, espera de 24 h e termos à vista no painel. |
| Restrições técnicas | ✅ O contrato de `fontes/__init__.py` não muda; id prefixado. |
| Fluxo | ✅ Spec aprovada em 25/10 → plano → tarefas, com testes e verificação rodando. |

**Emenda (FR-012)**: versão 4.1.0, MINOR porque é uma seção nova dentro do princípio VI. O texto proposto:

> **Termos contrários.** Um portal cujos termos proíbem acesso automatizado só entra na busca por decisão explícita
> da pessoa, registrada na spec, com os termos resumidos no painel e as regras acima (pausa, parar no primeiro
> bloqueio, sem contornar). Se o portal tem API oficial, só pela API. Portal novo nessa situação entra desligado por
> padrão, salvo outra decisão da pessoa registrada na spec. Exemplos: InfoJobs (spec 026), ligado por padrão;
> JobGether (spec 030), pela API para assistentes, desligado.

O texto não desliga portais que já existem: InfoJobs e Nerdin foram decididos nas suas specs. Ele registra como a
regra já vinha sendo aplicada.

Resultado: passa, com a emenda.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Termos do JobGether contra acesso automatizado | Decisão da pessoa (25/10/2026): vagas remotas abertas a quem mora no Brasil, que faltam nos portais nacionais | Pedir autorização por escrito ou deixar de fora foram oferecidos e recusados |
| Vagas sem descrição | A lista não traz o texto; a página dá 403, e imitar navegador está vetado | Descrição pela página: os termos e o bloqueio impedem |
| Verificação só no Windows | Decisão da pessoa | Mesmo motivo das specs anteriores |

## Project Structure

### Documentation (this feature)

```text
specs/030-jobgether/
├── spec.md, plan.md, research.md (R1–R7 + decisões técnicas D1–D8)
├── data-model.md, quickstart.md
├── contracts/jobgether.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
fontes/jobgether.py     # novo: buscar, pausa, aviso_pausa, espera, parada, id_do_link
fontes/__init__.py      # import e registro em FONTES
filtros.py              # FONTES_NAC; consulta global também com o JobGether (FONTES_GLOBAIS)
fontes/link.py          # plataforma(); ler(): LinkErro com o link e a plataforma, sem pedido
dash/banco.py           # PLATAFORMAS; criar_manual: id jobgether-<id> pelo link
candidatura/dominios.py # BLOQUEADOS: jobgether.com
.env.exemplo            # JOBGETHER_PAUSA comentada
.specify/memory/constitution.md   # emenda 4.1.0
README.md, dash/README.md, dash/API.md, AGENTS.md, docs/novo-portal.md (linha dos termos contrários)
.agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_jobgether.py, tests/dados/jobgether/{lista.json, lista-2.json, erro-local.json}
frontend-react: src/types/api.ts, src/utils/formatters.ts, src/components/modals/AddJobModal.tsx
```

**Structure Decision**: uma fonte nova no molde das que usam API (`remotive.py`, `himalayas.py`), com pausa, espera
e parada iguais às do InfoJobs. O POST fica dentro de `fontes/jobgether.py` (`_baixar`), porque só ele usa. O
`_comum.baixar` continua só com GET e mantém a nova tentativa no 429 que as outras fontes usam.
