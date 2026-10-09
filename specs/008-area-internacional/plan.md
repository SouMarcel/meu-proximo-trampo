# Implementation Plan: Área de vagas internacionais

**Branch**: `008-area-internacional` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-area-internacional/spec.md`

## Summary

A vaga ganha `area` (nacional ou internacional) e `pais_vaga`, calculados ao gravar pela consulta e
pelo local. A configuração `internacional` ganha regiões, salário mínimo anual em USD, fuso,
contratação e as caixas (morar fora, passaporte, autorização, sponsor), e o topo ganha
`idiomas_aceitos`. As consultas internacionais deixam de depender do remoto nacional e, com "aceito
morar fora", incluem presencial/híbrido nos países escolhidos; as fontes declaram `AREAS` e só rodam
nas consultas da sua área. Os critérios ganham idioma (detecção sem IA, confirmada pela análise) e
salário anual. A página ganha a aba Internacional (mesmo relatório, filtrado por área), o painel
Filtros da busca internacional, a etiqueta "Internacional · país · moeda" em todo lugar, o filtro de
área no quadro e o campo Área no Adicionar Vaga. Sem a busca ligada e sem idiomas, nada muda.
Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+; JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: biblioteca padrão; fontes atuais. Nenhuma dependência nova.

**Storage**: `config.json` (campos novos com padrão) e campos novos na vaga, sem migração
([data-model.md](data-model.md)).

**Testing**: `unittest` com fonte falsa; saída de referência do `vagas.py` (spec 005) para provar que
nada muda sem a área ligada; quickstart com servidor no roteiro e Chrome sem janela.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor Python + página) e linha de comando.

**Performance Goals**: sem consulta a mais para quem não liga; menos consultas para fontes só
nacionais.

**Constraints**: nada muda sem a internacional ligada e sem idiomas; na dúvida (idioma, salário,
moeda), não corta; sem câmbio.

**Scale/Scope**: `filtros.py` (config, consultas, critérios, idioma, salário, país do local),
`vagas.py` (área por fonte e da vaga), `fontes/*.py` (`AREAS`), `dash/banco.py` (análise com
`idioma`, área nas vagas manuais e por link), `dash/analise.py` (critérios no pedido),
`dash/dashboard.html`, skill `buscar-vagas`, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Tudo local; as caixas (passaporte, autorização) ficam no `config.json` e vão só para a IA escolhida, na análise. |
| II. Pública, sem dados pessoais | ✅ Padrões neutros (internacional desligada, idiomas vazios); testes fictícios. |
| III. Simples, leve, sem IA obrigatória | ✅ Idioma e salário sem IA; a IA só confirma. |
| IV. Só fatos confirmados | ✅ Na dúvida não corta; sem câmbio inventado. |
| V. A pessoa decide | ✅ Opcional e desligado; Fora dos critérios mostra o motivo e deixa seguir. |
| VI. Respeito aos portais | ✅ Fontes só nas consultas da sua área; o número de consultas aparece no painel. |
| Restrições técnicas | ✅ Campos novos sem migração; formato antigo do config lido. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/008-area-internacional/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── config-e-api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
filtros.py                 # config internacional e idiomas; consultas com área; critérios de idioma e salário; pais_do_local
vagas.py                   # fonte só nas consultas da sua área; area/pais_vaga/idioma ao gravar
fontes/indeed.py, gupy.py, startupjobs.py   # AREAS
dash/banco.py              # validar_analise com idioma; area nas vagas manuais e por link; criterios reaplicados
dash/analise.py            # critérios internacionais e idiomas no pedido
fontes/link.py             # palpite de área pelo local
dash/dashboard.html        # aba Internacional, painel internacional, etiqueta, filtro de área, campo Área
.agents/skills/buscar-vagas/SKILL.md   # campo idioma e alertas de vaga internacional
README.md, dash/README.md
tests/test_internacional.py
```

**Structure Decision**: as regras ficam em `filtros.py` (já dono dos filtros e critérios); a página
reaproveita o relatório e o painel de filtros existentes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
