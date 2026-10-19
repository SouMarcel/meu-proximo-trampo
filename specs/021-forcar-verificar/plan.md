# Implementation Plan: Forçar verificar a nota de uma vaga

**Branch**: `021-forcar-verificar` (worktree saída da `master`) | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/021-forcar-verificar/spec.md`

## Summary

A fila da análise automática (`dash/analise.py`, `Fila`) ganha os **pedidos da pessoa**: `FILA.forcar(id)` guarda o
id num conjunto "verificando" e acorda a thread. Na rodada, as vagas forçadas vêm primeiro, sem passar pelo filtro
`precisa()` nem pelo "uma tentativa por vaga":
- vaga com descrição pendente (ou sem descrição) de um portal que lê descrições: `vagas.descrever_uma(id)` faz um
  pedido só, fora da espera do portal e fora de uma busca, e grava o texto com `banco.completar_descricao`;
- sem texto, a vaga vai para a IA marcada "nota sem a descrição": o pedido diz à IA para avaliar pelo que há, e a
  nota é gravada com `nota_sem_descricao: true`;
- a vaga que não volta da IA (ou volta sem nota) fica em `FILA.falhas[id]` com o motivo.

Uma rota nova, `POST /api/vagas/<id>/analisar` (só deste computador), chama `FILA.forcar`. O `GET /api/versao`
passa a mandar `verificando` e `falhas`; a página, que já consulta essa rota a cada 4 s, mostra "verificando…" no
cartão e o erro quando houver. O cartão de toda vaga sem nota ganha o botão **Forçar verificar** embaixo dos botões
de decisão. Quando a descrição de uma vaga com "nota sem a descrição" chega depois, `banco.completar_descricao` tira
a marca e põe a vaga em `pendente`, e a nota é refeita pela fila automática.

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão: `threading`); JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: nenhuma nova. A IA é a de `ia.py`, já configurada pela pessoa.

**Storage**: SQLite com documento JSON (campo novo sem migração): `nota_sem_descricao` (bool) na vaga. O estado
"verificando" e as falhas ficam na memória do servidor.

**Testing**: `unittest`: `Fila` com `analisar` e `vagas.descrever_uma` substituídos; servidor de teste como em
`tests/test_post.py` (`TestServidor`); `banco.completar_descricao` e `validar_analise` com a marca; IA falsa como em
`tests/test_ia.py`. Verificação na página da branch pessoal com uma vaga sem nota.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor + página).

**Performance Goals**: o clique responde na hora (202); a nota sai no tempo da IA (cerca de 1 minuto; até 10 no
pior caso). A página atualiza em até 4 s depois do fim (consulta que já existe).

**Constraints**:
- no máximo 1 pedido ao portal por vaga forçada, nunca na espera nem durante uma busca;
- a IA só é chamada com a vaga forçada (lote de 1, ou junto com as automáticas da mesma rodada);
- sem IA, nada gravado;
- só deste computador.

**Scale/Scope**:
- `dash/analise.py` (Fila, montar_pedido, analisar);
- `vagas.py` (`descrever_uma`);
- `dash/banco.py` (`validar_analise`, `aplicar_analises`, `completar_descricao`);
- `dash/servidor.py` (rota nova, `/api/versao`);
- `dash/dashboard.html` (botão, estado, selo e banner);
- `dash/README.md`, skill buscar-vagas;
- testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A vaga vai só para a IA que a pessoa escolheu, como na análise automática; a rota só aceita pedidos deste computador. |
| II. Pública, sem dados pessoais | ✅ Nada da pessoa no código; testes com vagas fictícias. |
| III. Simples, sem IA obrigatória | ✅ Sem IA, o botão só avisa; o resto da ferramenta segue igual. |
| IV. Só fatos confirmados | ✅ A nota sem a descrição leva a marca visível e o resumo diz que é provisória; nada é inventado sobre a vaga nem sobre a pessoa. |
| V. A pessoa decide | ✅ Só no clique; a nota não muda decisões da pessoa (Seguir, Não seguir). |
| VI. Respeito aos portais | ✅ Um pedido de descrição por clique, pela mesma `descrever()` da busca (pausa e bloqueio do portal); nenhum pedido na espera nem durante uma busca; o bloqueio grava a espera como sempre. |
| Restrições técnicas | ✅ Campo novo no documento sem migração; servidor com as checagens de host e origem de sempre. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa**. Re-checado depois do desenho: sem mudança.

## Project Structure

### Documentation (this feature)

```text
specs/021-forcar-verificar/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forcar-verificar.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
dash/analise.py        # Fila.forcar, verificando(), falhas; rodada com as forçadas; pedido com "sem a descrição"
vagas.py               # descrever_uma(id): uma descrição, fora da espera e fora de uma busca
dash/banco.py          # nota_sem_descricao em validar_analise/aplicar_analises; completar_descricao refaz a nota
dash/servidor.py       # POST /api/vagas/<id>/analisar; /api/versao com verificando e falhas
dash/dashboard.html    # botão Forçar verificar, "verificando…", erro, selo e banner "nota sem a descrição"
dash/README.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_forcar.py   # novo
```

**Structure Decision**: tudo em cima da fila que já existe (uma análise por vez, thread única), sem fila nova. A
leitura da descrição reaproveita `descrever()` de cada fonte e as regras de espera de `vagas.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
