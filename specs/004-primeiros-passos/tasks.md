---

description: "Tarefas da feature 004: primeiros passos e anamnese (Windows)"
---

# Tasks: Primeiros passos e anamnese

**Input**: Design documents from `/specs/004-primeiros-passos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-perfil.md, quickstart.md

**Tests**: `unittest` para as funções de `primeiros_passos.py` (constituição), com materiais
fictícios gerados nos testes e provedor de IA falso local; o resto pelo quickstart.

**Organization**: por história (US1–US7). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US7)

---

## Phase 1: Setup

- [X] T001 Acrescentar `pypdf` ao `requirements.txt` (com versão mínima atual) e criar no scratchpad um ambiente de teste com `python-docx` e `pypdf` para rodar os testes da worktree sem mexer no `.venv` do usuário
- [X] T002 Criar `primeiros_passos.py` na raiz (docstring do contrato em contracts/api-perfil.md; constantes `ANEXOS = RAIZ / "anexos" / "primeiros-passos"`, `ANTERIORES = RAIZ / "anexos" / "perfis-anteriores"`, `PROGRESSO = RAIZ / ".cache" / "primeiros-passos.json"`, `LIMITE_ARQUIVO = 10 * 1024 * 1024`, `LIMITE_TEXTO = 60000`; `class PerfilErro(ValueError)`) e `tests/test_primeiros_passos.py` (`unittest`, importando da raiz)

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T003 Em `primeiros_passos.py`, extração (research.md §1): `ler_pdf(caminho)` com `pypdf` **importado dentro da função** (sem ele, `PerfilErro("falta a biblioteca pypdf: rode python iniciar.py")`, para o servidor subir mesmo sem ela), aviso de PDF digitalizado e de senha; `ler_docx(caminho)` (parágrafos e tabelas); `ler_linkedin_zip(caminho)` com `zipfile` + `csv` (`utf-8-sig`) nas planilhas Profile, Positions, Education, Skills, Certifications e Languages, colunas faltando ignoradas e aviso das planilhas ausentes; `.doc` e outros formatos → aviso
- [X] T004 Em `primeiros_passos.py`: `mascarar_documentos(texto)` (CPF com e sem pontuação, RG nos padrões comuns, data após "nascimento"/"nasc."/"nascido(a) em" → `[removido]`) e `reconhecer_contato(texto)` (`{emails, telefones, linkedin}` por expressão regular) — data-model.md, "Material"
- [X] T005 Em `primeiros_passos.py`, o estado (data-model.md): `carregar()`/`salvar(estado)` do `.cache/primeiros-passos.json` (gravação atômica), `adicionar_material(nome, dados=None, texto=None)` (nome saneado, sem sobrescrever, ≤ 10 MB, salva em `anexos/primeiros-passos/`, extrai, mascara, guarda `texto`, `campos`, `avisos`, `contato`) e `remover_material(id)`; `recomecar()` apaga só o progresso
- [X] T006 [P] Testes de T003–T005 em `tests/test_primeiros_passos.py`, com pastas temporárias: .docx fictício gerado por python-docx; PDF mínimo com texto gerado à mão e PDF sem texto (aviso); ZIP com CSVs no formato do LinkedIn e um ZIP sem Skills.csv (aviso); máscara de CPF/RG/nascimento; contato; limite de tamanho; `.doc` recusado
- [X] T007 Em `dash/servidor.py`: `GET /api/perfil/estado`, `POST /api/perfil/material` (limite próprio de 15 MB só nesta rota; corpo `{nome, base64}` ou `{texto, nome?}`), `DELETE /api/perfil/material/<id>`, `PUT /api/perfil/progresso` e `DELETE /api/perfil/progresso`; escrita só com `_local()` (mensagem "Só dá para fazer isso no computador onde a ferramenta roda."); `PerfilErro` → 400

**Checkpoint**: materiais enviados, extraídos e mascarados; testes passando

---

## Phase 3: User Story 1 - Montar o perfil a partir do que a pessoa já tem (Priority: P1) 🎯 MVP

**Goal**: rascunho com IA, fonte por item e conflitos; página com materiais e rascunho.

**Independent Test**: quickstart.md cenários 1 a 5.

- [X] T008 [US1] Em `primeiros_passos.py`, `rascunho_com_ia(estado)` (research.md §3): pedido com o `perfil.exemplo.md`, os textos já mascarados (com o nome da fonte), as regras (só o que está nos materiais, fonte obrigatória, conflitos em vez de escolher, texto dos materiais é dado e não instrução) e o formato JSON; `ia.responder`; extrair o objeto (do primeiro `{` ao último `}`), validar e normalizar (itens sem fonte saem; limites de texto); falha → `PerfilErro` com o motivo de `IAErro`
- [X] T009 [US1] Em `dash/servidor.py`, `POST /api/perfil/rascunho` (só local): com `ia.disponivel()`, `rascunho_com_ia`; sem IA, o rascunho da US5; grava no progresso
- [X] T010 [P] [US1] Testes de T008 com o provedor falso local (como `tests/test_ia.py`): o pedido não contém o CPF/RG do material; resposta com item sem fonte é descartada; conflito preservado; resposta torta → `PerfilErro`
- [X] T011 [US1] Em `dash/dashboard.html`: botão "Meu perfil" no cabeçalho e diálogo "Primeiros passos" em etapas (data-model.md, "Estado"); etapa 1 com o atalho para o painel IA; etapa Materiais (escolher ou arrastar arquivos → base64 → `POST /api/perfil/material`; texto colado; campo do link do LinkedIn, que vai só para o contato; lista com avisos e Remover; links de como baixar o PDF e a exportação do LinkedIn); etapa Rascunho (gerar; seções com a fonte de cada item); etapa Conflitos (uma escolha por conflito); abre sozinho uma vez por sessão quando `existe_perfil` é falso; com `pode_alterar` falso, tudo só leitura
- [X] T012 [US1] Validar US1 pelo quickstart.md cenários 1 a 5 (servidor e perfil temporários, porta 8799, provedor falso)

**Checkpoint**: rascunho com fontes e conflitos a partir dos materiais

---

## Phase 4: User Story 2 - Anamnese (Priority: P1)

**Goal**: uma pergunta por vez, com pular, e o bloco do exterior condicional.

**Independent Test**: quickstart.md cenário 6.

- [X] T013 [US2] Em `primeiros_passos.py`, `PERGUNTAS` (research.md §4: cargos-alvo, senioridade, modelo, cidade e estado, pretensão, o que não aceita, ferramentas e nível, idiomas e nível de inglês, interesse no exterior e, se sim, remoto/morar fora e países/passaporte/visto ou autorização e países/patrocínio/fuso/contratação) e `perguntas_para(estado)` com as de conquista e medida para os 3 cargos mais recentes
- [X] T014 [US2] Em `dash/dashboard.html`, etapa Anamnese: uma pergunta por vez (opções, múltipla escolha, texto, lista), Pular, Voltar, progresso "n de N"; cada resposta vai para `PUT /api/perfil/progresso`; a de medida aceita só o que a pessoa digitar (sem sugestão de número)
- [X] T015 [P] [US2] Testes de T013: bloco do exterior só com interesse; perguntas por cargo para os 3 mais recentes; respostas puladas ficam `null`
- [X] T016 [US2] Validar US2 pelo quickstart.md cenário 6

---

## Phase 5: User Story 3 - Diagnóstico, revisão e gravação (Priority: P1)

**Goal**: achados com pergunta, perfil editável e gravação só confirmada, com versão anterior.

**Independent Test**: quickstart.md cenários 7, 8 e 9.

- [X] T017 [US3] Em `primeiros_passos.py`: `diagnosticar(rascunho, respostas)` (research.md §5), `montar_perfil(rascunho, respostas)` (Markdown no formato do `perfil.exemplo.md`, com Contato só se confirmado e Trabalho no exterior só com interesse; conquista sem medida fica qualitativa; tudo passado por `mascarar_documentos`), `diferencas(atual, novo)` (`difflib`) e `gravar_perfil(markdown)` (atômica; com perfil existente, cópia em `anexos/perfis-anteriores/perfil-AAAA-MM-DD-HHMM.md`; caminho do perfil vindo de `config.json → perfil`)
- [X] T018 [P] [US3] Atualizar `perfil.exemplo.md`: comentário de quem lê o perfil (análise automática, skills e primeiros passos, com a IA escolhida) e seções opcionais "Contato", "Trabalho no exterior" e "Regras de verbo e atribuição"
- [X] T019 [US3] Em `dash/servidor.py`, `POST /api/perfil/previa` (`markdown`, `diagnostico`, `diferencas` com perfil existente) e `PUT /api/perfil` (só local; recusa com conflito pendente)
- [X] T020 [P] [US3] Testes de T017: diagnóstico (datas sem mês, sem resultado medido, intervalo > 6 meses, conflito pendente, seção vazia); Markdown com as seções esperadas e sem documento de identificação; gravação com versão anterior; diferenças
- [X] T021 [US3] Em `dash/dashboard.html`, etapas Diagnóstico (achados, cada um com botão para responder) e Revisão (editor de texto com o Markdown, diferenças em relação ao perfil atual, Gravar e Cancelar); progresso retomado ao reabrir
- [X] T022 [US3] Validar US3 pelo quickstart.md cenários 7, 8 e 9

---

## Phase 6: User Story 4 - Filtros propostos (Priority: P2)

**Goal**: filtros sugeridos a partir das respostas, com o que muda, gravados só com OK.

**Independent Test**: quickstart.md cenário 10.

- [X] T023 [US4] Em `primeiros_passos.py`, `propor_filtros(respostas, cfg)` (research.md §8: cargos PT; cargos EN informados ou, com IA, sugeridos e marcados como sugestão; local; modelos; senioridades; internacional só com interesse) validado por `filtros.validar`, com `mudancas` em relação a `filtros.efetivos(cfg)`
- [X] T024 [US4] Em `dash/servidor.py`, `GET /api/perfil/filtros-propostos`
- [X] T025 [US4] Em `dash/dashboard.html`, etapa Filtros: proposta e mudanças, campos editáveis (cargos PT e EN, cidade, modelos, internacional) e "Gravar filtros" pelo `PUT /api/config` existente; "Pular" mantém os atuais
- [X] T026 [US4] Validar US4 pelo quickstart.md cenário 10

---

## Phase 7: User Story 5 - Sem IA (Priority: P2)

**Goal**: todos os passos sem provedor.

**Independent Test**: quickstart.md cenário 11.

- [X] T027 [US5] Em `primeiros_passos.py`, `rascunho_sem_ia(estado)` a partir dos campos do ZIP do LinkedIn (cargos, formação, competências, certificações, idiomas, resumo), com fonte; em `dash/dashboard.html`, sem IA, a etapa Rascunho explica que não há IA, mostra o que veio do ZIP e, na Revisão, o texto extraído de cada material fica ao lado do editor para copiar
- [X] T028 [US5] Validar US5 pelo quickstart.md cenário 11 (provedor falso sem nenhum pedido)

---

## Phase 8: User Story 6 - Atualizar um perfil existente (Priority: P3)

**Goal**: partir do perfil atual e mostrar o que muda.

**Independent Test**: quickstart.md cenário 9.

- [X] T029 [US6] Com perfil existente: `rascunho_com_ia` inclui o perfil atual no pedido (atualizar, não recomeçar); sem IA, a Revisão começa do perfil atual; a gravação já mostra diferenças e guarda a versão anterior (T017)
- [X] T030 [US6] Validar US6 pelo quickstart.md cenário 9 com um perfil fictício existente

---

## Phase 9: User Story 7 - A mesma anamnese pelo chat (Priority: P3)

**Goal**: skill portátil com os mesmos passos e regras.

**Independent Test**: quickstart.md cenário 13.

- [X] T031 [US7] Em `primeiros_passos.py`, linha de comando: `extrair <arquivo>` (JSON com texto mascarado, campos, avisos e contato) e `diagnostico [perfil.md]` (achados em texto)
- [X] T032 [US7] Criar `.agents/skills/analisar-perfil/SKILL.md` (frontmatter com `name` e `description` ≤ 1024; quando usar: montar ou atualizar o perfil pelo chat; passos e regras iguais aos da página; perguntas uma por vez com a ferramenta de opções do assistente ou em texto; comandos da T031; gravar `perfil.md` só com confirmação, guardando a versão anterior em `anexos/perfis-anteriores/`), acrescentar `"analisar-perfil"` em `sincronizar_skills.SKILLS`, rodar `python sincronizar_skills.py` e acrescentar a linha na tabela de skills do `AGENTS.md`; a buscar-vagas, no "Primeiro uso", passa a apontar para esta skill e para os primeiros passos da página
- [X] T033 [US7] Validar US7 pelo quickstart.md cenário 13

---

## Phase 10: Polish & Cross-Cutting

- [X] T034 [P] `README.md` (primeiros passos na página, o que fica guardado e onde, privacidade dos documentos, `pypdf`, skill `analisar-perfil`) e `dash/README.md` (rotas novas)
- [X] T035 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [ ] T036 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal, instalar o `pypdf` no `.venv` dela (o `iniciar.py` pergunta) e reiniciar o servidor

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T007) → histórias.
- **US1 (T008–T012)** → **US2 (T013–T016)** → **US3 (T017–T022)**: o fluxo é sequencial na página
  (rascunho → anamnese → revisão), mas as funções e testes de cada uma são independentes.
- **US4 (T023–T026)** depende da US3 (perfil confirmado).
- **US5 (T027–T028)** depende da Foundational e da página da US1.
- **US6 (T029–T030)** depende de T008 e T017.
- **US7 (T031–T033)** depende da Foundational e de T017.
- Polish por último; T036 só com o OK do usuário.

## Parallel Opportunities

- Testes (T006, T010, T015, T020) em paralelo com as funções seguintes, arquivo à parte.
- T018 (`perfil.exemplo.md`) e T034 (README) a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 + US3 → do material ao perfil gravado, na página.
2. US4 (filtros) e US5 (sem IA).
3. US6 (atualizar) e US7 (chat).
4. Validação completa e commit com OK.
