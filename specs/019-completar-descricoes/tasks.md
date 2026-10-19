---

description: "Tarefas da feature 019: Completar descrições pendentes (Windows)"
---

# Tasks: Completar descrições pendentes

**Plano** (curto, como a mudança):
- `vagas.completar_pendentes()` reaproveita `ler_descricoes` (spec 015) com a lista de vagas novas vazia e grava com
  `banco.completar_descricao`;
- `dash/buscador.Completar` roda em segundo plano, recusa com busca rodando ou na espera e pede a análise no fim;
- rotas `GET` e `POST /api/busca/pendentes`;
- aviso e botão no topo do Relatório;
- o comando `vagas.py completar`.

**Constitution Check**:
- VI: mesmos limites, pausa, espera e parada no bloqueio da busca, e só o necessário (sem consultas novas);
- V: no clique;
- III: biblioteca padrão.

Passa.

- [X] T001 `vagas.py`: `fontes_com_pendentes`, `contar_pendentes`, `completar_pendentes` e o comando `completar`
  (código 5 na espera).
- [X] T002 `dash/buscador.py`: `Completar` (estado, iniciar com recusas, `_rodar` com `analise.FILA.pedir`).
- [X] T003 `dash/servidor.py`: `GET /api/busca/pendentes` e `POST /api/busca/pendentes` (só deste computador).
- [X] T004 `dash/dashboard.html`: `pdAviso` no topo do Relatório, botão `data-completar`, andamento e recarga no fim.
- [X] T005 Testes em `tests/test_busca.py`: completa só as pendentes, sem consulta; espera e limite; pela página.
- [X] T006 README, AGENTS.md e a skill buscar-vagas (`sincronizar_skills.py`).
- [X] T007 Merge na branch pessoal, reiniciar o dashboard e a pessoa testa com as 10 pendentes reais.
- [X] T008 Com o OK: merge na `master`, push, merge na branch pessoal, apagar a worktree e a branch.
