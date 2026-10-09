---

description: "Tarefas da feature 002: IA configurável (Windows)"
---

# Tasks: IA configurável

**Input**: Design documents from `/specs/002-ia-configuravel/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-ia.md, quickstart.md

**Tests**: incluídos para `ia.py` e `segredos.py` (constituição: `unittest` em função pura nova); o
resto é validado pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Criar `segredos.py` na raiz (docstring; `RAIZ`, `ENV = RAIZ / ".env"`, `LIMITE_VALOR = 400`) e `ia.py` na raiz (docstring do contrato em contracts/api-ia.md; `class IAErro(Exception)` com o motivo legível; constantes `TEMPO_TESTE = 15`, `TEMPO_TESTE_CLAUDE = 30`, `MAX_TOKENS_ANTHROPIC = 16000`), só biblioteca padrão
- [X] T002 [P] Criar `tests/test_segredos.py` e `tests/test_ia.py` (`unittest`, importando da raiz como `tests/test_iniciar.py`)

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T003 Implementar em `segredos.py`: `ler(nome)` (variável de ambiente vence o `.env`; aceita `export NOME=` e aspas), `origem(nome)` (`"ambiente"`, `"arquivo"` ou `None`), `final(nome)` (últimos 4 caracteres), `gravar(nome, valor)` e `remover(nome)` reescrevendo o `.env` de forma atômica e **preservando todas as outras linhas e comentários**; `gravar` recusa valor vazio, com quebra de linha ou acima de `LIMITE_VALOR` (data-model.md, "Chave do provedor")
- [X] T004 [P] Testes de T003 em `tests/test_segredos.py`: `.env` com `MCP_STARTUP_JOBS` e comentário preservados ao gravar e remover; ambiente vence arquivo; valor inválido recusado; `final` e `origem` (usar `tempfile` e apontar `segredos.ENV` para ele)
- [X] T005 Em `fontes/startupjobs.py`, trocar o leitor próprio de `_chave()` por `segredos.ler(VAR_CHAVE)` (mesmo comportamento: ambiente vence o `.env`)
- [X] T006 Em `ia.py`, criar o catálogo `PROVEDORES` da research.md §2 (id, nome, adaptador, url_padrao, variável da chave, cobrança `"uso"`/`"assinatura"`, onde_obter_chave, modelo_padrao); modelo padrão da Anthropic `claude-opus-5-5`; os dos demais conferidos na documentação oficial de cada provedor nesta tarefa, com a data da conferência em comentário
- [X] T007 Em `ia.py`: `escolha_efetiva(cfg=None)` (sem `"ia"`: `analise_automatica == false` → `nenhum`; comando `claude` existe → `claude_code`; senão `nenhum`), `validar_escolha(dados)` (provedor do catálogo; modelo até 120; `url_base` obrigatório só em `compativel`, começando com `https://` ou `http://127.0.0.1`/`http://localhost`), `disponivel()` e `salvar_escolha(dados)` (grava `"ia"` no `config.json` de forma atômica, preservando as outras chaves; sem config, cria `{"ia": …}`) — data-model.md
- [X] T008 Em `ia.py`: `mascarar(texto)` (troca por `••••` os valores de todas as variáveis de chave do catálogo vindos de `segredos.ler` e os padrões `sk-…`, `AIza…`, `gsk_…`) e `motivo_http(status, corpo, modelo)` com as mensagens da research.md §4
- [X] T009 Em `ia.py`, os adaptadores: `_pedido_anthropic(escolha, chave, pedido, sistema)` e `_pedido_openai(...)` devolvendo `(url, cabeçalhos, corpo)` sem rede; `_texto(adaptador, resposta_json)`; `_postar(url, cabecalhos, corpo, tempo)` com `urllib` (HTTPError → `IAErro(motivo_http(...))`, URLError/timeout → "sem conexão com o provedor"); `_claude_code(pedido, modelo, tempo)` com os argumentos de `dash/analise.py:115-119`, `--model` quando houver modelo, `CREATE_NO_WINDOW` no Windows e "Claude Code não está instalado neste computador" sem o comando
- [X] T010 Em `ia.py`: `responder(pedido, sistema=None, tempo=600, escolha=None, chave=None)` (escolha efetiva por padrão; `nenhum` → `IAErro("IA desligada (Sem IA)")`; chave do provedor via `segredos.ler`; ausente → "falta a chave do provedor"; toda mensagem passa por `mascarar`) e `testar(escolha, chave=None)` → `(ok, mensagem)` com "Responda apenas: ok" e `TEMPO_TESTE` (ou `TEMPO_TESTE_CLAUDE`)
- [X] T011 [P] Testes de T006–T010 em `tests/test_ia.py`: escolha efetiva e legado; validação; pedidos montados de cada adaptador (url, cabeçalhos, corpo); extração de texto; `motivo_http` para 401, 402, 429, 404; `mascarar`; ponta a ponta com um `http.server` falso local em thread imitando `/chat/completions` (provedor `compativel`): sucesso, 401 e resposta que ecoa a chave (sai mascarada)
- [X] T012 Em `dash/banco.py`, `validar_analise` passa a aceitar `analise_provedor` (id do catálogo, ou vazio) e `analise_modelo` (texto até 120) — data-model.md, "Registro da análise"

**Checkpoint**: `python -m unittest discover -s tests` passa

---

## Phase 3: User Story 1 - Escolher o provedor e conectar (Priority: P1) 🎯 MVP

**Goal**: painel "IA" para escolher provedor e modelo, gravar a chave no `.env`, testar e salvar;
chave nunca volta à página; mudança só pelo próprio computador.

**Independent Test**: quickstart.md cenários 3, 8, 9, 10 e 11.

- [X] T013 [US1] Em `filtros.py`, `salvar()`: se o config ainda não tem `termos`, partir do `config.exemplo.json` e sobrepor as chaves existentes (preserva `"ia"`); em `dash/servidor.py`, `GET /api/config` passa a devolver `existe = bool(termos)` (research.md §5)
- [X] T014 [US1] Em `dash/servidor.py`: `_local()` (`client_address[0]` em `127.0.0.1`/`::1`) e `GET /api/ia` com o corpo de contracts/api-ia.md (`escolha`, `efetiva`, `provedores`, `chaves` só com `cadastrada`/`final`/`origem`, `claude_instalado`, `pode_alterar = _local()`, `ultimo_erro`)
- [X] T015 [US1] Em `dash/servidor.py`: `PUT /api/ia` (valida com `ia.validar_escolha`, grava chave com `segredos.gravar` quando vier, `ia.salvar_escolha`, `analise.FILA.pedir()` se `ia.disponivel()`), `POST /api/ia/testar` (`ia.testar`, chave do corpo não gravada) e `DELETE /api/ia/chave/<provedor>` (`segredos.remover`; chave do ambiente não é removida e a resposta avisa); as três só com `_local()`, senão `403 {"erro": "Só dá para mudar a IA no computador onde a ferramenta roda."}`; mensagens passam por `ia.mascarar`
- [X] T016 [P] [US1] Em `dash/dashboard.html`: botão "IA" no cabeçalho e diálogo (padrão dos diálogos atuais) com seletor de provedor, campo de modelo (placeholder = padrão), endereço só para `compativel`, chave em campo `password` sempre vazio, situação "chave cadastrada …<final> (arquivo/ambiente)" com "Remover", "Testar conexão" com o resultado, "Salvar" e link "onde conseguir a chave"; com `pode_alterar: false`, tudo desabilitado com a frase da rota
- [X] T017 [US1] Validar US1 pelo quickstart.md cenários 3, 8, 9, 10 e 11 (servidor e config temporários, porta 8799, servidor falso para `compativel`)

**Checkpoint**: configurar e testar pela página, sem a chave aparecer em lugar nenhum

---

## Phase 4: User Story 2 - A análise automática usa o provedor escolhido (Priority: P1)

**Goal**: a nota sai pelo provedor escolhido, com provedor e modelo no detalhe; falha não quebra e
aparece na página.

**Independent Test**: quickstart.md cenários 1, 4, 5 e 6.

- [X] T018 [US2] Reescrever `dash/analise.py`: `comando()` → `ia.disponivel()`; `analisar()` em lotes de 10 com `ia.responder(montar_pedido(lote))`, mesma extração do array e mesmo `banco.aplicar_analises`, acrescentando `analise_provedor`/`analise_modelo` da escolha efetiva; `Fila` com `ultimo_erro`/`ultimo_erro_em` (motivo de `IAErro`, já mascarado) limpos na próxima rodada boa; manter os marcadores de recorte da skill (linhas 67-68)
- [X] T019 [US2] Em `dash/servidor.py`, `GET /api/versao` acrescenta `ia_erro` (`{"motivo", "em"}` ou `null`)
- [X] T020 [P] [US2] Em `dash/dashboard.html`: aviso no topo do Relatório quando houver `ia_erro` ("A análise automática não rodou: <motivo>. Ajuste em IA.", com botão que abre o painel) e, no detalhe da vaga, "Nota por <nome do provedor> · <modelo>"
- [X] T021 [US2] Validar US2 pelo quickstart.md cenários 1, 4, 5 e 6 (cenário 12 com chave real, se o usuário quiser)

**Checkpoint**: vaga nova recebe nota pelo provedor escolhido; falhas viram aviso legível

---

## Phase 5: User Story 3 - Usar sem IA (Priority: P2)

**Goal**: "Sem IA" desliga tudo de forma visível; o resto funciona.

**Independent Test**: quickstart.md cenários 2 e 7.

- [X] T022 [US3] Em `dash/dashboard.html`, mostrar no topo do Relatório qual IA está ativa ("IA: <nome> · <modelo>" ou "IA: desligada — as vagas ficam sem nota") e garantir que "Sem IA" no painel grava `provedor: "nenhum"`
- [X] T023 [US3] Validar US3 pelo quickstart.md cenários 2 e 7 (servidor falso sem receber pedido nenhum)

---

## Phase 6: User Story 4 - Saber o que significa usar cada IA (Priority: P2)

**Goal**: avisos claros antes de salvar.

**Independent Test**: abrir o painel e trocar entre um provedor por uso e o Claude Code.

- [X] T024 [US4] Em `dash/dashboard.html`, no painel, antes de "Salvar": aviso de cobrança conforme `cobranca` ("cobrado por uso na sua conta do provedor" × "usa a sua assinatura do Claude"), "notas de modelos diferentes podem variar para a mesma vaga", "o seu perfil e o texto das vagas vão para <provedor>" e "em planos gratuitos, alguns provedores podem usar os dados enviados; confira os termos"; para Anthropic, a dica de que Sonnet e Haiku custam menos que o Opus
- [ ] T025 [US4] Validar US4 olhando o painel com cada tipo de provedor

---

## Phase 7: Polish & Cross-Cutting

- [X] T026 [P] `README.md`: seção sobre a IA (provedores aceitos, painel "IA", onde fica a chave, avisos de custo e privacidade, "Sem IA", `analise_automatica: false` legado) e linha `ia` na tabela do `config.json`
- [X] T027 Rodar `python -m unittest discover -s tests` e o quickstart.md completo; registrar os resultados no `quickstart.md`; buscar a chave de teste em todos os arquivos e respostas (SC-003)
- [X] T028 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push e merge na branch pessoal

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T012) → histórias.
- **US1 (T013–T017)**: depende da Foundational. MVP junto com a US2.
- **US2 (T018–T021)**: depende da Foundational; usa o painel da US1 para configurar, mas a
  análise funciona com a escolha gravada à mão.
- **US3 (T022–T023)** e **US4 (T024–T025)**: dependem do painel (T016).
- Polish (T026–T028) por último; T028 depois do OK do usuário.

## Parallel Opportunities

- T002 com T001; T004 e T011 (testes) em paralelo com o fim das funções.
- T016 (`dashboard.html`) em paralelo com T013–T015 (servidor e filtros).
- T020 (`dashboard.html`) em paralelo com T018–T019.
- T026 (README) em paralelo com as validações.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → configurar um provedor e ver a nota sair por ele.
2. US3 e US4 (painel completo e transparente).
3. README, validação completa e commit com OK.
