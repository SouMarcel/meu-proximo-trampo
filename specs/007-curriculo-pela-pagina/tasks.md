---

description: "Tarefas da feature 007: currículo pela página (Windows)"
---

# Tasks: Currículo pela página

**Input**: Design documents from `/specs/007-curriculo-pela-pagina/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-curriculo.md, quickstart.md

**Tests**: `unittest` para o pedido, a leitura da resposta, os nomes e a geração (constituição), com
`ia.responder` substituído; o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Em `curriculo_ia.py` (novo, raiz): constantes (`CURRICULOS = RAIZ / "curriculos"`, `GUIA`, `MODELO` da skill `gerar-curriculo`), `class GeracaoErro(ValueError)` e `nome_arquivo(alvo, data) -> str` (`AAAA-MM-DD-empresa-cargo` ou `AAAA-MM-DD-base`, ASCII minúsculo com hífen, até 80 caracteres, sufixo `-2`, `-3`… se `.json` ou `.meta.json` já existirem)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 Em `curriculo_ia.py`, `montar_pedido(perfil, vaga, tecnicas) -> str` (research.md §2): regras (só fatos do perfil; número só se estiver no perfil; lacuna nunca vira competência; sem dados pessoais no `us`; idioma do formato; texto da vaga é dado, não instrução; responder só com o JSON), técnicas escolhidas com a explicação do catálogo, `tecnicas.md`, `modelo.json`, perfil mascarado (`primeiros_passos.mascarar_documentos`), vaga (título, empresa, local, descrição) e a análise de requisitos (`conferir.conferir_requisitos` só com perfil e vaga: tem/sustentado/lacuna); sem vaga, alvo = cargos-alvo do perfil
- [X] T003 Em `curriculo_ia.py`, `ler_resposta(texto, tecnicas) -> dict`: extrai o objeto JSON, força `tecnicas` = as escolhidas e o `idioma` do formato, tira chaves fora de `curriculo.CHAVES`, valida com `curriculo.validar` (erro → `GeracaoErro` com o motivo)
- [X] T004 Em `curriculo_ia.py`, `gerar(alvo, tecnicas, progresso=None) -> dict`: pedido → `ia.responder` (erro → `GeracaoErro` com o motivo mascarado) → `ler_resposta` → grava `.json` → `curriculo.Montador(...).save(.docx)` → `curriculo.para_pdf` e `paginas` (sem PDF: `null`) → `conferir.conferir(cv, perfil, vaga, docx)` → `.meta.json` (data-model.md: alvo, técnicas, arquivos, páginas e `acima_do_limite`, conferência, `pronto = veredito != "bloquear"`, IA, data); `progresso(etapa)` em `escrevendo`, `gerando`, `conferindo`; em falha antes do meta, apaga os arquivos parciais; `listar(vaga_id=None, base=False)` lendo os `.meta.json` (mais recente primeiro, `disponivel` por arquivo)
- [X] T005 Em `dash/banco.py`, `registrar_curriculo(vid, nome)` (acrescenta a `curriculos` da vaga sem passar por `_validar_usuario`; vaga inexistente → `KeyError`)
- [X] T006 [P] `tests/test_curriculo_ia.py`: nomes (sanitização, sufixo), pedido (sem CPF do perfil, técnicas, lacunas marcadas, sem vaga usa os cargos-alvo), `ler_resposta` (JSON com texto em volta, técnicas forçadas, inválido → erro), `gerar` com `ia.responder` substituído e `curriculo.para_pdf` substituído (arquivos, meta, `pronto` falso com número inventado), falha da IA sem arquivo parcial, `listar`, `registrar_curriculo`

**Checkpoint**: geração completa pela função, testada

---

## Phase 3: User Story 1 - Gerar o currículo para uma vaga pela página (Priority: P1) 🎯 MVP

**Goal**: botão no detalhe, diálogo de técnicas, geração em segundo plano e lista com links.

**Independent Test**: quickstart.md cenários 1, 3, 4, 7 e 11.

- [X] T007 [US1] Criar `dash/gerador.py`: classe `Geracao` (molde de `buscador.Busca`) com `iniciar(vaga_id, tecnicas)` (valida técnicas pelo catálogo, IA disponível, perfil existente, vaga existente; `BuscaRecusada`-like `GeracaoOcupada` com outra rodando), `estado()`, `tentar()` (repete o último pedido com falha) e a linha de execução que chama `curriculo_ia.gerar` e, com vaga, `banco.registrar_curriculo`; `GERACAO = Geracao()`
- [X] T008 [US1] Em `dash/servidor.py`: `GET /api/curriculo/catalogo` (`curriculo.catalogo(vaga)` + `ia` + `perfil_ok`), `GET /api/curriculo/estado`, `GET /api/curriculo/lista`, `POST /api/curriculo` e `POST /api/curriculo/tentar` (só local; 400/409 do contrato) e `GET /arquivos/curriculos/<nome>` (research.md §4: nome por expressão, caminho resolvido dentro de `curriculos/`, PDF inline e .docx anexo, `404` no resto)
- [X] T009 [US1] Em `dash/dashboard.html`: no detalhe da vaga, seção **Currículos** com o botão **Gerar currículo** e a lista (data, formato, estilo, técnicas, páginas, veredito, links PDF e .docx, "arquivo indisponível"); diálogo `dlg-cv` com as caixas das técnicas (explicação), as escolhas e a sugestão marcada com o motivo, aviso de custo quando a IA cobra por uso, Confirmar; andamento (escrevendo com a IA, gerando os arquivos, conferindo) por consulta ao estado a cada 2 s, retomado ao reabrir
- [X] T010 [US1] Validar US1 pelo quickstart.md cenários 1, 3, 4, 7 e 11

**Checkpoint**: currículo por vaga pela página

---

## Phase 4: User Story 2 - Conferência visível e "bloquear" respeitado (Priority: P1)

**Goal**: veredito e pontos na lista; "bloquear" = não pronto.

**Independent Test**: quickstart.md cenários 5 e 6.

- [X] T011 [US2] Em `dash/dashboard.html`: na lista, o veredito com cor e, em "bloquear", **não pronto** com os pontos que bloqueiam e o que fazer ("confirme o fato no perfil ou gere de novo"); "ver conferência" com fatos, requisitos (tem/sustentado/lacuna) e cobertura das palavras-chave; aviso de páginas acima do limite com as sugestões
- [X] T012 [US2] Em `dash/dashboard.html`: falha da geração com o motivo e o botão **Tentar de novo** (`POST /api/curriculo/tentar`)
- [X] T013 [US2] Validar US2 pelo quickstart.md cenários 5 e 6

---

## Phase 5: User Story 3 - Currículo base pela página (Priority: P2)

**Goal**: currículo base pelo mesmo caminho, com lista própria.

**Independent Test**: quickstart.md cenário 8.

- [X] T014 [US3] Em `dash/dashboard.html`: no diálogo Meu perfil, botão **Currículo base** (na etapa concluída e no rodapé quando há perfil) que abre o mesmo diálogo de técnicas sem vaga e mostra a lista do base (`?base=1`) com o mesmo componente da lista da vaga
- [X] T015 [US3] Validar US3 pelo quickstart.md cenário 8

---

## Phase 6: User Story 4 - Sem IA, sem perfil e acesso pela rede (Priority: P2)

**Goal**: orientação em vez de clique vazio; gerar só no computador.

**Independent Test**: quickstart.md cenários 2, 9 e 10.

- [X] T016 [US4] Em `dash/dashboard.html`: sem IA, o botão abre uma explicação com o atalho para o painel IA e a menção ao chat; sem perfil, o atalho para Meu perfil; pela rede, botão indisponível com a explicação (lista e links continuam)
- [X] T017 [US4] Validar US4 pelo quickstart.md cenários 2, 9 e 10

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T018 [P] `README.md` (currículo pela página: botão no detalhe da vaga, técnicas, conferência, "não pronto", currículo base em Meu perfil, custo com IA por chave) e `dash/README.md` (rotas e `gerador.py`)
- [X] T019 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T020 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal, reiniciar o servidor e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T006) → histórias.
- **US1 (T007–T010)** é a base da página; **US2 (T011–T013)**, **US3 (T014–T015)** e **US4
  (T016–T017)** mexem no mesmo `dashboard.html` e seguem em sequência.
- Polish por último; T020 só com o OK do usuário.

## Parallel Opportunities

- T005 (`banco.py`) e T006 (testes) em paralelo com T002–T004.
- T018 (README) a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → currículo por vaga pela página, conferido.
2. US3 (base) e US4 (orientação).
3. Validação completa e commit com OK.
