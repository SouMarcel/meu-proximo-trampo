---
description: "Tarefas da spec 051: limite de páginas que vale e currículo completo"
---

# Tasks: Limite de páginas que vale e currículo completo

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: cada tarefa de código traz os próprios testes (`python -m unittest discover -s tests`).

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.
São sequenciais porque mexem nos mesmos arquivos.

## Format: `[ID] [D tamanho?] [Story] Description`

---

## Phase 1: Catálogo (US2, US3)

- [X] T001 [D minor] [US2][US3] Em `curriculo.py`, mudar o catálogo:
  - criar a técnica `paginas_obrigatorio` (padrão False);
  - criar a opção `paginas` 0 "Completo (sem limite, tudo do perfil)";
  - `catalogo(vaga)` tira a opção 0 com vaga;
  - `descrever_tecnicas` e o `main` tratam 0 como sem limite.

  Testes em `tests/test_curriculo.py`. → agy, GO na tentativa 1

## Phase 2: Pedido (US1, US3)

- [X] T002 [D minor] [US1][US3] Em `curriculo_ia.py`, criar `ORCAMENTO` (D1) e usá-lo em `montar_pedido` para 1 e 2
  páginas. Com 0, a instrução de completo.
  - `validar_tecnicas(dados, vaga=None)` recusa 0 com vaga;
  - `gerar` repassa a vaga;
  - `nome_arquivo(..., completo=False)` gera `-base-completo`;
  - `dash/gerador.py` passa a vaga nas duas chamadas de `validar_tecnicas`.

  Testes em `tests/test_curriculo_ia.py`. → copilot, GO na tentativa 1

## Phase 3: Encurtar e avisar (US1, US2)

- [ ] T003 [D minor] [US1][US2] Em `curriculo_ia.py`, criar `montar_pedido_encurtar` e o laço de encurtar em `gerar`
  (D3), mais o ponto de aviso e o veredito recalculado (D4). Em `dash/gerador.py`, `ETAPAS["encurtando"]` (D5).
  Testes com IA e páginas falsas em `tests/test_curriculo_ia.py`.

## Phase 4: Fechamento (eu)

- [ ] T004 [US2] Conferir que `reprovacao.reescrever_e_gerar` passa pelo `cia.gerar` com as técnicas da análise e herda
  o encurtar. Rodar `tests/test_reprovacao.py`.
- [ ] T005 Documentação: limite concreto, opção obrigatória (no chat, quem encurta é o assistente) e Completo.
  - `.agents/skills/gerar-curriculo/tecnicas.md` e `SKILL.md`, depois `python sincronizar_skills.py`;
  - `dash/API.md` (catálogo, técnica, etapa, `meta.encurtado`).
- [ ] T006 Teste real na `marcel` com o perfil do usuário e ajuste dos números de `ORCAMENTO`. Os 3 cenários do
  quickstart estão no plano da sessão.
