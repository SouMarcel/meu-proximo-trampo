---

description: "Tarefas da feature 010: kit de candidatura (Windows)"
---

# Tasks: Kit de candidatura ("indica, não faz")

**Input**: Design documents from `/specs/010-kit-candidatura/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/kit.md, quickstart.md

**Tests**: `unittest` com IA falsa local, perfil e vagas fictícios (constituição); o resto pelo
quickstart.

**Organization**: por história (US1–US5). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US5)

---

## Phase 1: Setup

- [X] T001 Conferir que as referências do `vagas.py` (scratchpad, specs 005, 008 e 009) e os 146 testes
  ainda batem, para provar que nada da busca muda
- [X] T002 [P] Perfil e vagas fictícios para os testes do kit em `tests/dados/kit/` (perfil com
  conquistas e números, vaga em inglês com sponsor, contrato, inglês, fuso, híbrido, carta e
  portfólio; vaga em português com teste técnico), sem dados pessoais

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Em `dash/banco.py`, `validar_analise` aceita os campos novos com as regras do data-model
  (`autorizacao` `{valor: patrocina|nao_precisa|omisso|nao_patrocina, frase}`, `contratacao` até 4 de
  `contractor|eor|empregado_brasil|relocation|clt|pj`, `ingles` `nao_pede|basico|intermediario|fluente|nativo`,
  `fuso` texto até 80, `sistema_candidatura` até 40, `pede` até 6 de
  `curriculo_ingles|carta|formulario|portfolio|teste|video`, `riscos` até 4 de `remuneracao|remoto_hibrido`;
  frase até 200; valor fora das opções faz o campo cair, sem erro)
- [X] T004 Em `dash/banco.py`, `_validar_usuario` aceita `kit` (`estados` por item:
  `a_fazer|pronto|nao_se_aplica`; até 10 `extras` de 80; `removidos`), `lembretes` (`base`,
  `follow1|follow2|agradecimento`: `feito|dispensado`, `parar`) e `entrevista_em` (AAAA-MM-DD ou nulo);
  `documentos` da vaga (`[{tipo, nome, criado_em}]`) com `registrar_documento`
- [X] T005 Criar `dash/kit.py`: `checklist(v)` (itens de toda vaga, `pede` da análise, palavras do anúncio
  PT/EN, extras da pessoa, menos os removidos; estado gravado; `acao` de cada item) e
  `lembretes(v, hoje)` (7 e 14 dias de `etapa_em` em Aplicação Enviada; dia seguinte a `entrevista_em`
  ou a `etapa_em` em Entrevista; estado só vale com a mesma `base`)
- [X] T006 Em `dash/servidor.py`, `GET /api/vagas` devolve `checklist` e `lembretes_pendentes`
  calculados; `dash/banco.py kit <id>` e `lembretes` na linha de comando
- [X] T007 [P] `tests/test_kit.py` (base): validação dos campos novos e do estado da pessoa

**Checkpoint**: referências do `vagas.py` iguais; listagem com os campos calculados

---

## Phase 3: User Story 1 - O que a candidatura pede e o que pode impedir (Priority: P1) 🎯 MVP

**Goal**: campos novos da análise, com a frase, no detalhe da vaga.

**Independent Test**: quickstart.md cenários 1 e 2.

- [X] T008 [US1] Em `.agents/skills/buscar-vagas/SKILL.md`, no trecho que a análise automática lê
  (entre "`modelo_trabalho`:" e "4. **Gravar.**"), os sete campos com as opções e a regra de
  autorização (cruzar com passaporte, países onde pode trabalhar e sponsor; "não precisa" só quando o
  anúncio aceita um país onde a pessoa pode trabalhar); `python sincronizar_skills.py`
- [X] T009 [US1] Em `dash/analise.py`, conferir que o pedido leva os campos novos e a situação da pessoa
  (ajustar o recorte se preciso); teste com IA falsa que devolve os campos
- [X] T010 [US1] Em `dash/dashboard.html`, bloco "Para se candidatar" no detalhe: autorização,
  contratação, inglês, fuso, sistema de candidatura e riscos, cada um com a frase; "não informado";
  sem IA, o que já se lê sem IA e o aviso de que o resto vem com a análise
- [X] T011 [P] [US1] Testes em `tests/test_kit.py`: anúncios com frases conhecidas e a resposta da IA
  falsa gravada com as opções certas (SC-001); valor fora das opções cai
- [X] T012 [US1] Validar US1 pelo quickstart.md cenários 1 e 2

---

## Phase 4: User Story 2 - Checklist "o que esta candidatura pede" (Priority: P1)

**Goal**: checklist com estado da pessoa, botões por item e botão de candidatura que só abre o link.

**Independent Test**: quickstart.md cenários 3 e 4.

- [X] T013 [US2] Em `dash/dashboard.html`, checklist no detalhe: estado por item (a fazer, pronto, não
  se aplica), tirar e acrescentar item, gravação pela rota de atualização; botões "Gerar currículo"
  (diálogo da spec 007), "Escrever carta", "Preparar respostas"; botão "Candidatar no <sistema>"
  como link `target=_blank` (url_candidatura, senão url)
- [X] T014 [P] [US2] Testes em `tests/test_kit.py`: checklist com e sem análise, por palavras do anúncio,
  currículo em inglês para vaga em inglês, estado preservado com análise refeita (SC-006)
- [X] T015 [US2] Validar US2 pelo quickstart.md cenários 3 e 4

---

## Phase 5: User Story 3 - Carta de apresentação (Priority: P2)

**Goal**: carta com as quatro respostas, só fatos do perfil, conferida antes de entregar.

**Independent Test**: quickstart.md cenários 5 e 6.

- [X] T016 [US3] Em `conferir.py`, `conferir_carta(texto, perfil, vaga, respostas)` (número ou data fora
  do perfil e das respostas → bloquear; fora de 350–420 palavras, empresa da vaga não citada, nenhum
  requisito do anúncio citado, expressões vazias PT/EN, empresa ou cargo citado fora do perfil →
  conferir) e `--carta arquivo.txt [--vaga-id] [--respostas]`
- [X] T017 [US3] Criar `candidatura_ia.py` com `gerar_carta(vaga, respostas)`: valida as quatro respostas
  (tom: direto, caloroso, formal), pedido com perfil, vaga, respostas e regras, JSON `{texto, idioma}`,
  conferência, `.txt`, `.docx` e `.meta.json` em `curriculos/`, nada pela metade em falha;
  `listar(vaga_id)`
- [X] T018 [US3] Em `dash/gerador.py`, a fila com `tipo` (curriculo, carta, respostas) e o estado com o
  tipo; em `dash/servidor.py`, `POST /api/kit/carta`, `GET /api/kit/lista`, `.txt` em
  `/arquivos/curriculos/`; `registrar_documento` na vaga
- [X] T019 [US3] Em `dash/dashboard.html`, diálogo "Escrever carta" (as quatro perguntas, obrigatórias),
  progresso, carta com o veredito, os trechos apontados, a contagem de palavras, baixar (.docx) e
  copiar; sem IA, a explicação de como escolher uma IA ou pedir no chat
- [X] T020 [P] [US3] `tests/test_candidatura.py`: resposta faltando → erro dizendo qual; conferência
  (fato inventado bloqueia, carta correta passa, genérica, curta e sem empresa viram conferir; SC-003);
  geração com IA falsa grava os arquivos
- [X] T021 [US3] Validar US3 pelo quickstart.md cenários 5 e 6

---

## Phase 6: User Story 4 - Respostas de formulário sem inventar (Priority: P2)

**Goal**: perguntas sensíveis só com a pessoa; as outras rascunhadas com fatos do perfil.

**Independent Test**: quickstart.md cenário 7.

- [X] T022 [US4] Em `candidatura_ia.py`: `separar(texto)` (uma pergunta por linha ou numeradas),
  `sensivel(pergunta)` (lista PT/EN: autorização, visto/sponsor, cidadania, salário/pretensão,
  deficiência/PCD, relocação/mudança, gênero, raça, veterano), `gerar_respostas(vaga, perguntas)` (só
  as não sensíveis vão à IA; resposta da IA a uma sensível é descartada; `conferir_respostas` marca
  fato fora do perfil), `gravar_da_pessoa(nome, respostas)`; linha de comando `sensiveis arquivo.txt`
- [X] T023 [US4] Em `dash/servidor.py`, `POST /api/kit/respostas` e `PUT /api/kit/respostas/<nome>`; em
  `dash/dashboard.html`, diálogo "Preparar respostas" (colar as perguntas), lista com as rascunhadas,
  as para conferir e as sensíveis com campo para a pessoa, salvar e copiar
- [X] T024 [P] [US4] Testes em `tests/test_candidatura.py`: sensíveis PT/EN de um conjunto de teste
  ficam com a pessoa mesmo com IA falsa que responde tudo (SC-002); resposta da pessoa gravada igual
- [X] T025 [US4] Validar US4 pelo quickstart.md cenário 7

---

## Phase 7: User Story 5 - Lembretes de follow-up (Priority: P3)

**Goal**: lembretes no quadro que só lembram.

**Independent Test**: quickstart.md cenário 8.

- [X] T026 [US5] Em `dash/dashboard.html`: etiqueta no card ("Hora do follow-up", "2º follow-up",
  "Agradecer a entrevista") com "feito", "dispensar" e "parar lembretes"; contagem no topo do quadro;
  campo "Data da entrevista" no detalhe de vaga em Entrevista
- [X] T027 [P] [US5] Testes em `tests/test_kit.py`: 6, 7, 14, 15 e 22 dias; entrevista ontem e sem data;
  mudança de etapa zera; parar encerra; nunca um terceiro (SC-005)
- [X] T028 [US5] Validar US5 pelo quickstart.md cenário 8

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T029 [P] Em `.agents/skills/gerar-curriculo/SKILL.md`: "Carta de apresentação" (as quatro
  perguntas, regras, `PY conferir.py --carta`) e "Respostas de formulário" (`PY candidatura_ia.py
  sensiveis`; sensíveis só com a pessoa); em `.agents/skills/buscar-vagas/SKILL.md`, "o que a
  candidatura pede" e "follow-ups" (`PY dash/banco.py kit` e `lembretes`); `python sincronizar_skills.py`
- [X] T030 [P] `README.md` (kit de candidatura, carta, respostas, lembretes; nada é enviado) e
  `dash/README.md` (campos novos da vaga e da análise); `AGENTS.md` com os comandos novos
- [X] T031 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no
  `quickstart.md`
- [ ] T032 Com o OK do usuário, uma carta com a IA configurada por ele (cenário 12)
- [X] T033 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push,
  merge na branch pessoal, reiniciar o servidor e `graphify update .`; marcar a T031 da spec 009

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T007) → histórias.
- **US1 (T008–T012)** e **US2 (T013–T015)** dependem da Foundational; o checklist usa o `pede` da US1,
  mas funciona sem ele (palavras do anúncio).
- **US3 (T016–T021)** depende da Foundational; **US4 (T022–T025)** reaproveita a fila e o
  `candidatura_ia.py` da US3.
- **US5 (T026–T028)** depende só da Foundational (T005).
- Polish por último; T032 e T033 só com o OK do usuário.

## Parallel Opportunities

- T002 em paralelo com T001; os testes [P] de cada história junto da implementação.
- US5 (lembretes) em paralelo com US3/US4.
- T029 e T030 a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → a vaga mostra o que pede e o que pode impedir, com o
   checklist da pessoa.
2. US3 e US4 (carta e respostas), depois US5 (lembretes).
3. Validação completa, carta com a IA real (com OK) e commit com OK.
