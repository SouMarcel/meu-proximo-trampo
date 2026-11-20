---
description: "Tarefas da spec 053: currículo e carta com resultado à vista"
---

# Tasks: Currículo e carta com resultado à vista

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Tests**: cada tarefa de código traz os próprios testes (`python -m unittest discover -s tests`), com textos
fictícios.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.
Rodam uma depois da outra, porque mexem nos mesmos arquivos (`conferir.py` e `tests/test_conferir.py`).

## Format: `[ID] [D tamanho?] [Story] Description`

---

## Phase 1: Conferência (funcionários)

- [X] T001 [D minor] [US2] Avisos de contato sem e-mail e, no formato Brasil, sem telefone (D2), em
  `conferir.conferir_ats`. Testes em `tests/test_conferir.py`. → agy, GO na tentativa 1
- [X] T002 [D minor] [US2] `conferir.itens_de_tarefa(cv)` e os pontos "N de M itens…" em `conferir()` (D3). Testes
  com 20 itens fictícios marcados à mão em `tests/test_conferir.py`. → copilot, GO na tentativa 1
- [X] T003 [D minor] [US4] `avaliar_requisitos`: "em preparação" não conta como "tem" (D4) e requisito de vários
  idiomas com um faltando sai "lacuna" (D5). Testes em `tests/test_conferir.py`. → agy, GO na tentativa 1 (marca só
  entre parênteses: ajuste meu depois do teste com perfil real)
- [X] T004 [D minor] [US3] Confissão de lacuna em `conferir_carta` e `conferir_respostas` (D6). Testes em
  `tests/test_conferir.py`. → copilot, GO na tentativa 1 (frase longa: ajuste meu)

## Phase 2: Instruções e documentação (eu)

- [X] T005 [US1] Guia de técnicas com resultado primeiro e exemplo do `modelo.json` sem expressão vaga (D1), em
  `.agents/skills/gerar-curriculo/`, depois `python sincronizar_skills.py`.
- [X] T006 [US3] `REGRA_FALTAS` nos pedidos da carta, do Verificar e das respostas (D7), em `candidatura_ia.py`.
- [X] T007 Documentação (D8): `dash/API.md` (pontos novos da conferência) e `specs/lista-de-desejos.md` ("caça de
  números").

## Phase 3: Fechamento (eu)

- [X] T008 Suíte inteira verde; merge na branch pessoal; dashboard reiniciado; teste do usuário (currículo base e
  carta de uma vaga com diferencial que o perfil não tem).
