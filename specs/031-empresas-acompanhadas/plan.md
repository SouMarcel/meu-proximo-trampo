# Implementation Plan: Empresas acompanhadas na busca nacional

**Branch**: `031-empresas-acompanhadas` (worktree `../meu-proximo-trampo-031`, saída da `master`) | **Date**: 2026-10-25 |
**Spec**: [spec.md](spec.md)

## Summary

**Configuração** (`filtros.py`):
- a lista sobe para `empresas`, no nível de cima;
- `efetivos` lê a lista nova ou, num config antigo, `internacional.empresas`;
- `validar` usa a lista de cima quando ela vem no pedido, e a de `internacional` só quando ela não vem (front antigo);
- `salvar` grava só em cima, e `internacional.empresas` some;
- `consultas` leva `empresas` também nas consultas nacionais, e a consulta global passa a depender de `f["empresas"]`;
- uma função nova, `acompanhar(url)`, põe uma empresa na lista sem revalidar os outros filtros.

**Fonte `fontes/ats.py`**:
- `AREAS` com as duas áreas, `POR_PAIS = True` e `GLOBAL = True`, como o LinkedIn e o JobGether;
- atende as consultas nacionais (remota, do país e da cidade) e a global; as por país e de mudança não fazem pedido;
- filtro nacional por `filtros.aberta_ao_pais`, a regra da elegibilidade exposta como função pública;
- na consulta da cidade, as não remotas na cidade ou no estado;
- cada empresa é baixada uma vez por busca (`_comum.lembrar`);
- o primeiro 403 ou 429 de um sistema para esse sistema até o fim da busca, sem nova tentativa;
- um 404 vira o aviso de empresa que saiu do sistema.

**Comum** (`fontes/_comum.py`): `baixar` ganha `nova_tentativa=True` (o padrão de hoje), e `FonteErro` passa a guardar o
`codigo` HTTP.

**Busca** (`vagas.py`): `fontes_da_busca` inclui `ats` sempre que há empresas na lista, com ou sem a internacional.

**Servidor e API**:
- `GET /api/empresas` traz a lista e o máximo;
- `POST /api/empresas` com `{url}` acompanha uma empresa;
- `POST /api/vagas/link` passa a devolver `empresa` (com `acompanhada`) quando o link é de vaga do Greenhouse, do Lever ou
  do Ashby.

**Front** (`frontend-react`):
- a seção "Empresas que você acompanha" vai para o painel principal;
- "Acompanhar" no Adicionar Vaga e no detalhe (`Kit.tsx`, junto do "Candidatar no …").

**Ordem de entrega** (research D7): o push do front só depois de o back-end chegar à master.

**Outros**: lista de desejos (Greenhouse barrado), documentação e skill.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão. Front em TypeScript, na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `config.json` → `empresas: [{sistema, id, nome, url}]`, no máximo 50. Nenhuma tabela nova.

**Testing**: `unittest` sem rede, com as amostras que já existem em `tests/dados/{greenhouse,lever,ashby}.json` e locais
trocados nos testes. Os testes de `tests/test_fontes_int.py` e `tests/test_internacional.py` servem de não regressão.

**Constraints**:
- APIs públicas, sem login;
- uma lista por empresa por busca;
- zero novas tentativas no 403 ou 429;
- um config antigo continua funcionando (princípio "formato antigo do `config.json` continua funcionando").

**Scale/Scope**: até 50 empresas, uma lista cada por busca, com 2 s entre pedidos ao mesmo host (`_comum.INTERVALO`).
Com 10 empresas no Greenhouse, são cerca de 20 s.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A lista fica no `config.json`, fora do Git. Os pedidos levam só o nome da empresa no sistema. |
| II. Pública, sem dados pessoais | ✅ Amostras fictícias que já existem; nenhum nome de empresa da pessoa no código. |
| III. Simples | ✅ Biblioteca padrão; sem IA. |
| IV. Só fatos | ✅ A vaga entra como o sistema informa. A área sai do local, pela mesma regra da elegibilidade. |
| V. A pessoa decide | ✅ "Acompanhar" só grava no clique. A lista é dela, no painel. |
| VI. Respeito aos portais | ✅ APIs públicas e oficiais. A parada no bloqueio fica mais rígida (sem nova tentativa, sistema parado até o fim da busca). O Greenhouse como portal com login fica de fora. |
| Restrições técnicas | ✅ O formato antigo do `config.json` continua lido. O contrato das fontes não muda. |
| Fluxo | ✅ Spec aprovada em 25/10 → plano → tarefas. |

Resultado: passa, sem desvio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão da pessoa | Mesmo motivo das specs anteriores |

## Project Structure

### Documentation (this feature)

```text
specs/031-empresas-acompanhadas/
├── spec.md, plan.md, research.md (R1–R4 + decisões D1–D8)
├── data-model.md, quickstart.md
├── contracts/empresas.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
fontes/_comum.py        # baixar(..., nova_tentativa=True); FonteErro.codigo
fontes/ats.py           # áreas, filtro nacional, bloqueio por sistema, 404, ler() sem nova tentativa
filtros.py              # empresas no nível de cima (efetivos, validar, salvar, consultas, resumo); aberta_ao_pais; acompanhar
vagas.py                # fontes_da_busca com ats quando há empresas
dash/servidor.py        # GET/POST /api/empresas; empresa na resposta do POST /api/vagas/link
dash/API.md, dash/README.md, README.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
specs/lista-de-desejos.md   # Greenhouse como portal: barrado (exige login)
tests/test_empresas_acompanhadas.py
frontend-react: src/services/api/config.ts, src/components/modals/SearchFiltersModal.tsx,
  src/components/modals/AddJobModal.tsx, src/components/kit/Kit.tsx (+ cliente de /api/empresas)
```

**Structure Decision**: tudo cabe nos módulos que já existem. A regra de "aberta ao país" sai da elegibilidade
(`filtros._lugares` e `_inclui`) como função pública, para a fonte e a elegibilidade usarem a mesma.
