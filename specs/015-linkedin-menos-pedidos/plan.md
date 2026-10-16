# Implementation Plan: LinkedIn com menos pedidos

**Branch**: `015-linkedin-menos-pedidos` (worktree saída da `master`) | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-linkedin-menos-pedidos/spec.md`

## Summary

Quatro mudanças, todas dentro do que já existe:

1. **Consulta combinada.** Uma fonte pode declarar `AGRUPAR = True` (só o LinkedIn). Nela, `vagas.executar` junta as
   consultas de um mesmo grupo numa só, com `termos` (a lista) e `termo` (a expressão `"a" OR "b" OR c`, montada
   por `filtros.expressao_or`). A consulta lê até 3 páginas. As vagas recebem os cargos que aparecem no título.
2. **Limite de descrições e descrição pendente.** Uma fonte pode declarar `MAX_DESCRICOES = 20`. Em `executar`, a
   fila de descrições dessa fonte começa pelas vagas do banco com `descricao_pendente` e segue com as candidatas
   novas, das mais recentes para as mais antigas. Ela para no limite ou no bloqueio. As candidatas que ficarem sem
   texto saem com `descricao_pendente: true`. As pendentes lidas voltam no resultado e `gravar_resultado` as
   completa no banco (`banco.completar_descricao`). A análise automática (`analise.precisa`) e a do chat
   (`banco.precisa_analise`) pulam as pendentes. A página mostra "Descrição pendente".
3. **Espera de 6 horas.** No bloqueio, `fontes/linkedin.py` grava `.cache/linkedin-espera.json` com a hora e o
   motivo. `linkedin.espera()` diz até quando a espera vale. `buscar`/`descrever` não fazem pedido durante a
   espera. Antes de começar, a página (`buscador.plano`/`iniciar`), o terminal (`vagas.py buscar`) e a skill
   perguntam se a busca segue sem o LinkedIn. O aviso de bloqueio traz o motivo (429, 999, login, 401/403) e o
   horário.
4. **Aviso de cargos.** `filtros.aviso_cargos(f, fontes)` avisa quando há mais de 5 cargos e LinkedIn ou Indeed estão
   ligados. O aviso aparece no painel de filtros (ao lado do contador de consultas), no diálogo de busca e no começo
   da saída do terminal.

Decisões em [research.md](research.md); dados em [data-model.md](data-model.md); interfaces em
[contracts/](contracts/); roteiro em [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão); JavaScript ES5 no `dash/dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- SQLite com documentos JSON: campo novo `descricao_pendente` na vaga, sem migração;
- arquivo novo `.cache/linkedin-espera.json`, fora do Git.

**Testing**:
- `unittest` com o `abridor` falso de `tests/test_linkedin.py` e o banco temporário de `tests/test_busca.py`;
- o servidor e a página pelo roteiro;
- um único pedido real ao LinkedIn para conferir o OR (pendente, com o OK da pessoa, fora da espera).

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor + página) e linha de comando.

**Performance Goals**: com 7 cargos e 2 grupos, até 26 pedidos ao LinkedIn por busca (2 × 3 páginas + 20
descrições), contra até ~154 hoje.

**Constraints**:
- sem login nem conta;
- nenhuma nova tentativa depois do bloqueio;
- com o LinkedIn e o Indeed desligados, a saída é idêntica à de antes;
- configuração e banco antigos continuam funcionando.

**Scale/Scope**:
- `fontes/linkedin.py`, `fontes/__init__.py` (contrato), `vagas.py`, `filtros.py`;
- `dash/banco.py`, `dash/analise.py`, `dash/buscador.py`, `dash/servidor.py` (repassar `confirmar_espera`),
  `dash/dashboard.html`;
- README, AGENTS.md e a skill buscar-vagas (com `sincronizar_skills.py`);
- os testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A espera fica em `.cache/` (fora do Git). Nada novo sai do computador; o LinkedIn recebe só cargos e local, como hoje. |
| II. Pública, sem dados pessoais | ✅ Testes com cargos fictícios; nenhum dado do usuário no código, nos exemplos ou na documentação. |
| III. Simples, sem IA obrigatória | ✅ Biblioteca padrão; funciona sem IA (a pendente só espera o texto). |
| IV. Só fatos confirmados | ✅ Melhora: a IA deixa de dar nota sem a descrição da vaga. |
| V. A pessoa decide | ✅ Durante a espera, nenhuma busca começa sem a confirmação da pessoa; o aviso de cargos não bloqueia. |
| VI. Respeito aos portais | ✅ Reforça o princípio: menos pedidos ("só o necessário"), parar no bloqueio e agora também não voltar antes de 6 horas. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` ganha `AGRUPAR`, `MAX_DESCRICOES` e `espera()`, todos opcionais; campo novo sem migração. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas, com aprovação; testes; verificação rodando. |

Resultado: **passa**, sem emenda. Re-checado depois do desenho: sem mudança.

## Project Structure

### Documentation (this feature)

```text
specs/015-linkedin-menos-pedidos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── fontes.md          # AGRUPAR, MAX_DESCRICOES, espera() no contrato das fontes
│   └── busca.md           # plano/iniciar da página, terminal (código 5, --confirmar-espera) e skill
├── checklists/
│   └── requirements.md
└── tasks.md               # (/speckit-tasks)
```

### Source Code (repository root)

```text
fontes/linkedin.py      # AGRUPAR, MAX_PAGINAS 3 na combinada, MAX_DESCRICOES 20, parametros com a expressão,
                        # _bloquear(motivo) + espera gravada, espera(), buscar/descrever sem pedido na espera
fontes/__init__.py      # documentar AGRUPAR, MAX_DESCRICOES, espera()
filtros.py              # expressao_or(termos, maximo), termos_no_titulo(titulo, termos), aviso_cargos(f, fontes)
vagas.py                # executar: agrupar consultas, fila de descrições com limite e pendentes do banco,
                        # descricao_pendente; contar_consultas com agrupamento; gravar_resultado completa pendentes;
                        # cmd_buscar: aviso de cargos, pergunta da espera, --confirmar-espera, código 5
dash/banco.py           # pendentes_de_descricao(plataforma), completar_descricao(vid, texto, tipo_emprego),
                        # precisa_analise pula pendentes
dash/analise.py         # precisa() pula descricao_pendente
dash/buscador.py        # plano(): espera e aviso_cargos; iniciar(confirmar_espera); FILA também para pendentes completadas
dash/servidor.py        # POST /api/busca repassa confirmar_espera
dash/dashboard.html     # contador/aviso de cargos; diálogo de busca com a espera; chip "Descrição pendente"
README.md, AGENTS.md, .agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_linkedin.py, tests/test_busca.py (+ casos de banco/análise)
```

**Structure Decision**: o comportamento novo fica atrás de atributos opcionais no contrato das fontes (`AGRUPAR`,
`MAX_DESCRICOES`, `espera()`), e não de "se for o LinkedIn" espalhado pelo código. As outras fontes não declaram
nada e seguem iguais. O Indeed poderia usar o mesmo mecanismo depois, mas isso fica fora desta spec.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
