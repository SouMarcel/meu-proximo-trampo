# Implementation Plan: Buscar vagas pela página

**Branch**: `005-buscar-pela-pagina` (trabalho na `master` por worktree) | **Date**: 2026-10-09 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-buscar-pela-pagina/spec.md`

## Summary

A busca de `vagas.py` vira uma função reutilizável (`executar`, com ganchos de progresso e
cancelamento) e a gravação também (`gravar_resultado`), de modo que terminal e página rodam o mesmo
código e chegam ao mesmo resultado. O servidor ganha `dash/buscador.py`, que roda a busca numa linha
de execução em segundo plano (molde da análise automática), com estado em memória, cancelamento
entre consultas e as rotas `/api/busca…`. Uma trava do sistema operacional em `.cache/busca.trava`
impede duas buscas ao mesmo tempo entre página, terminal e chat; `.cache/busca.json` guarda quem
buscou e quando, base do intervalo mínimo (30 min) e do aviso de busca recente (6 h). Com IA e
perfil, as vagas novas entram como `pendente` e a análise automática existente dá as notas; sem IA,
`sem_analise`. A página ganha o botão **Buscar vagas**, a confirmação com o plano e o painel de
andamento e resumo. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+; JavaScript ES5 no `dashboard.html`.

**Primary Dependencies**: biblioteca padrão (`threading`, `msvcrt`/`fcntl` para a trava); nenhuma
dependência nova. As fontes continuam como estão (python-jobspy no Indeed).

**Storage**: banco atual (tabela `buscas` com `origem` e `situacao`), `.cache/busca.json`,
`.cache/busca.trava`, `.cache/pagina/` — tudo fora do Git ([data-model.md](data-model.md)).

**Testing**: `unittest` com uma fonte falsa e o provedor de IA falso; validação do quickstart com o
servidor subido no roteiro (sem portais de verdade).

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor Python + página).

**Performance Goals**: andamento na página ≤ 5 s depois de cada consulta; cancelamento em no máximo
uma consulta; a página continua respondendo durante a busca.

**Constraints**: uma busca por vez no computador; pausa entre consultas igual à do terminal;
intervalo mínimo de 30 min para iniciar pela página; nada gravado em busca cancelada ou
interrompida; escrita só do próprio computador; terminal e skill com o mesmo uso de hoje.

**Scale/Scope**: refatoração de `vagas.py` (sem mudar o uso), 1 módulo novo no servidor, rotas
novas, botão e painéis na página, linha na skill `buscar-vagas`, testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Tudo local; arquivos de trabalho em `.cache/` (fora do Git); escrita só do próprio computador. |
| II. Pública, sem dados pessoais | ✅ Testes com fonte e vagas fictícias. |
| III. Simples, leve, sem IA obrigatória | ✅ Sem dependência nova; sem IA, a busca grava sem nota e nada vai a provedores. |
| IV. Só fatos confirmados | ✅ Sem texto novo gerado; a nota vem da análise existente. |
| V. A pessoa decide | ✅ Plano mostrado e confirmado antes de consultar; cancelar a qualquer momento; aviso de custo da IA. |
| VI. Respeito aos portais | ✅ Mesma pausa entre consultas, uma busca por vez, intervalo mínimo de 30 min e aviso abaixo de 6 h; falha geral conta para o intervalo. |
| Restrições técnicas | ✅ Campo novo no registro de busca sem migração; servidor mantém host/origem. ⚠️ Verificação só no Windows (desvio já registrado). |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes; verificação rodando. |

Resultado: **passa** (re-checado depois do desenho: sem mudança).

## Project Structure

### Documentation (this feature)

```text
specs/005-buscar-pela-pagina/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-busca.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
vagas.py                         # executar(...) e gravar_resultado(...) sem imprimir; trava e busca.json; código 4 com busca da página
dash/buscador.py                 # novo: Busca em segundo plano (estado, iniciar, cancelar, plano, intervalo)
dash/servidor.py                 # rotas /api/busca…; /api/versao com o estado da busca
dash/dashboard.html              # botão Buscar vagas, confirmação com o plano, andamento, resumo, tentar a nota de novo
dash/banco.py                    # (se preciso) contagem de vagas que esperam nota para o andamento
.agents/skills/buscar-vagas/SKILL.md  # busca pela página e a recusa do terminal (cópia via sincronizar_skills.py)
README.md, dash/README.md        # uso pela página, intervalo, rotas
tests/test_busca.py              # novo
```

**Structure Decision**: a lógica da busca continua em `vagas.py` (fonte única); o que é do servidor
(segundo plano, estado, rotas) fica em `dash/`, ao lado da `analise.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Trava por sistema operacional (`msvcrt`/`fcntl`) | Uma busca por vez entre processos diferentes (servidor e terminal) | Arquivo com PID exige testar se o processo vive, o que no Windows não tem um jeito simples e seguro na biblioteca padrão |
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
