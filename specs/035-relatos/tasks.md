---
description: "Tarefas da feature 035: Relatos — a candidatura assistida aprende com a pessoa (Windows)"
---

# Tasks: Relatos

**Input**: spec.md, plan.md. **Testes**: `tests/test_relatos.py` (sem rede e sem navegador).

## Phase 1: Base

- [X] T001 `relatos.py`: guardar, listar, editar, apagar, bloco, com_relatos, levar_ao_perfil e a linha de comando.
- [X] T002 Constituição IV (5.2.0) com relatório de impacto.

## Phase 2: US3 — fatos e classificação (P2, base para as outras)

- [X] T003 `candidatura_ia.SENSIVEIS`: remuneração atual × pretensão salarial.
- [X] T004 `formulario.PESSOAL` → cadastro em campo de texto longo.
- [X] T005 `memoria`: NAO_LEMBRAR e `fato()` com o fallback em `valor_para`.

## Phase 3: US1 — relato vira resposta (P1) 🎯

- [X] T006 `candidatura_ia.adaptar_relatos`.
- [X] T007 `auto.responder`: relatos adaptados, fontes e gravação; `servidor` passa `guardar_relatos`.

## Phase 4: US2 — relato vira conhecimento (P1)

- [X] T008 `com_relatos` em curriculo_ia, entrevista, analise_perfil, dash/analise e conferir.
- [X] T009 Rotas `/api/perfil/relatos`.

## Phase 5: Testes, front e documentação

- [X] T010 `tests/test_relatos.py` (SC-001 a SC-004).
- [X] T011 Front (branch `front-035-relatos` sobre `front-034-vaga-segura`): painel, Seus relatos, tipos; `tsc` e
  build; build de teste na branch pessoal, sem commit.
- [X] T012 API.md, README, AGENTS.md, skills (+ `sincronizar_skills.py`).
- [ ] T013 Suíte inteira; dados pessoais; commit; merge na branch pessoal; dashboard reiniciado; teste do usuário.

## Phase 6: US4 — carta que vende a pessoa (P1; pedido do usuário no teste, 28/10)

- [X] T014 `candidatura_ia`: perguntas opcionais (`validar_respostas`), pedido com primeiro parágrafo que vende,
  solução, fechamento e ATS (`montar_pedido_carta`), respostas escritas guardadas como relato
  (`guardar_relatos_da_carta`).
- [X] T015 Testes em `tests/test_candidatura.py`, com a pasta dos dados isolada; front (`Kit.tsx`: perguntas
  opcionais, "Guardar o que eu escrever como relato"); README, API.md e skill `gerar-curriculo`.

## Phase 7: US5 — palavras-chave e Verificar (P1; pedidos do usuário no teste, 28/10)

- [X] T016 `conferir.avaliar_requisitos` (extraída de `conferir_requisitos`), `cobertura_palavras_chave`; equivalência
  entre idiomas em `FAMILIAS`; palavras que não são habilidade em `VAZIAS`; pedido da carta com as palavras-chave e os
  requisitos não achados; `palavras_chave` na conferência da carta.
- [X] T017 `candidatura_ia.verificar_carta` (com `_gravar_carta` e `acrescimos`); gerador com o tipo `verificar`; rota
  `POST /api/kit/verificar`; testes em `tests/test_candidatura.py`.
- [X] T018 Front: "Editar e verificar" na carta, palavras-chave usadas e faltando, "O que a IA ajustou", aviso de fim
  da geração com o tipo `verificar` (e a concordância "a carta … conferida"); README, API.md e skill.

## Phase 8: US6 — carta em PDF (P2; pedido do usuário, 28/10)

- [X] T019 `_gravar_carta` com o PDF (`_pdf`), `pdf_da_carta` e a rota `POST /api/kit/carta/{nome}/pdf`; testes com o
  PDF simulado; conversão real conferida com o Word (texto com acentos extraído pelo pypdf).
- [X] T021 (US7) `SAUDACAO`, `ABERTURA`, `PEDE`, `DESPEDIDA`; pedido da carta no padrão do usuário;
  `moldura_da_carta` (cabeçalho e despedida dos dados de contato), `_sem_despedida`, `.docx` com linhas e nome em
  negrito; Verificar sem mandar cabeçalho e despedida à IA; testes; front (aviso sem dados de contato, descrição); README,
  API.md, skill e spec.
- [X] T020 Front: "Exportar: .pdf .docx .txt", "Gerar PDF" e o motivo quando o PDF não sai; README, API.md e spec.
