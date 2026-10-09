# Implementation Plan: Fontes internacionais e elegibilidade

**Branch**: `009-fontes-internacionais` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-fontes-internacionais/spec.md`

## Summary

Sete módulos de fonte novos (`fontes/remotive.py`, `himalayas.py`, `remoteok.py`, `jobicy.py`,
`weworkremotely.py`, `getonboard.py` e `ats.py` para Greenhouse, Lever e Ashby), todos com
`AREAS = ("internacional",)` e `POR_PAIS = False`, rodando numa consulta internacional global por
cargo, com uma consulta por fonte por busca nas listas (filtradas aqui pelos cargos). As fontes e as
empresas ficam no `config.json → internacional` (desligadas/vazias por padrão). `filtros.elegibilidade`
lê a restrição do portal e frases do anúncio e decide, sem IA, contra as caixas da pessoa; os motivos
entram nos critérios (Fora dos critérios) e os sinais (patrocínio, relocation) vão para a vaga. O
Adicionar Vaga lê Greenhouse, Lever e Ashby pela API pública da vaga. A página ganha, no painel
internacional, fontes, empresas e frases; e os sinais e a restrição na vaga. Decisões em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão: `urllib`, `json`, `xml.etree` para o RSS);
JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `config.json` (campos novos) e campos novos na vaga, sem migração
([data-model.md](data-model.md)).

**Testing**: `unittest` com respostas gravadas de cada fonte em `tests/dados/`; referência do
`vagas.py`; quickstart com servidor no roteiro e Chrome sem janela; uma consulta real por fonte (para
gravar as respostas) e uma busca real pequena no fim, as duas com o OK do usuário.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local e linha de comando.

**Performance Goals**: uma consulta por fonte por busca nas listas; elegibilidade instantânea.

**Constraints**: fontes desligadas por padrão; ambíguo passa; patrocínio vence restrição; fonte que
falha não trava as outras; consultas espaçadas.

**Scale/Scope**: 7 módulos de fonte, `filtros.py` (config, consultas globais, elegibilidade),
`vagas.py` (fontes internacionais ligadas, campos novos), `fontes/link.py` (ATS),
`dash/dashboard.html` (painel e vaga), README, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nada da pessoa vai às fontes (só os cargos em inglês, e só para as que buscam por termo). |
| II. Pública, sem dados pessoais | ✅ Respostas gravadas sem dados pessoais (vagas públicas); padrões neutros. |
| III. Simples, leve, sem IA obrigatória | ✅ Sem dependência nova; elegibilidade sem IA. |
| IV. Só fatos confirmados | ✅ Só corta pelo que o anúncio diz; ambíguo passa. |
| V. A pessoa decide | ✅ Fontes desligadas até escolher; Fora dos critérios com motivo e "seguir mesmo assim". |
| VI. Respeito aos portais | ✅ APIs públicas oficiais, uma consulta por fonte por busca, pausa, termos citados no README e na vaga. |
| Restrições técnicas | ✅ Contrato de fontes respeitado, ids prefixados; campos novos sem migração. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/009-fontes-internacionais/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── fontes-e-config.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
fontes/remotive.py, himalayas.py, remoteok.py, jobicy.py, weworkremotely.py, getonboard.py   # novas
fontes/ats.py                  # nova: Greenhouse, Lever, Ashby (empresas acompanhadas) e reconhecer(url)
fontes/_comum.py               # nova: baixar JSON/RSS com limites, filtro pelo cargo, HTML → texto
fontes/__init__.py             # registro e contrato (POR_PAIS, TERMOS)
fontes/link.py                 # vaga do Greenhouse, Lever e Ashby pela API pública
filtros.py                     # config (fontes, empresas, frases), consultas globais, elegibilidade
vagas.py                       # fontes internacionais ligadas; restricao_local, ats, sinais na vaga
dash/dashboard.html            # painel internacional (fontes, empresas, frases); sinais e restrição na vaga
README.md                      # fontes e termos de uso
tests/dados/*.json|.rss        # respostas gravadas
tests/test_fontes_int.py, tests/test_elegibilidade.py
```

**Structure Decision**: uma fonte por módulo, no contrato que já existe; o que é comum (baixar,
filtrar pelo cargo, HTML → texto) num módulo de apoio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
