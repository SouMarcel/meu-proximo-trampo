---

description: "Tarefas da feature 003: skills portáveis (Windows)"
---

# Tasks: Skills portáveis

**Input**: Design documents from `/specs/003-skills-portaveis/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/estrutura-e-comandos.md, quickstart.md

**Tests**: `unittest` para o script de sincronização e para o comando da Gupy (constituição); o
resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Mover com `git mv` as skills de usuário de `.claude/skills/{buscar-vagas,consultar-gupy,gerar-curriculo}/` para `.agents/skills/` (todos os arquivos, inclusive `gerar-curriculo/modelo.json`), preservando o histórico; as `speckit-*` ficam onde estão

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T002 Criar `sincronizar_skills.py` na raiz (biblioteca padrão) conforme contracts/estrutura-e-comandos.md: `SKILLS = ("buscar-vagas", "consultar-gupy", "gerar-curriculo")`; sem opção, recria `.claude/skills/<nome>/` a partir de `.agents/skills/<nome>/` (todos os arquivos, fim de linha LF), inserindo logo depois do frontmatter do `SKILL.md` o aviso `<!-- Cópia gerada de .agents/skills/<nome>/ por sincronizar_skills.py: edite lá. -->`, sem tocar em outras pastas de `.claude/skills/`; `--conferir` não escreve e sai com 1 listando arquivos diferentes, faltando ou sobrando
- [X] T003 Rodar `python sincronizar_skills.py` para criar as cópias em `.claude/skills/` e conferir que o `git status` mostra a cópia gerada no lugar das pastas movidas
- [X] T004 Em `dash/analise.py`, `SKILL` passa a apontar para `RAIZ / ".agents" / "skills" / "buscar-vagas" / "SKILL.md"` (os marcadores de recorte continuam os mesmos)

**Checkpoint**: Claude Code e os demais assistentes enxergam as mesmas três skills

---

## Phase 3: User Story 1 - Usar a ferramenta com outro assistente (Priority: P1) 🎯 MVP

**Goal**: instruções comuns e skills sem dependência exclusiva; Gupy sem MCP.

**Independent Test**: quickstart.md cenários 3, 4 e 6.

- [X] T005 [US1] Criar `AGENTS.md` na raiz (português, < 32 KiB): o que é a ferramenta; regras gerais vindas da constituição (só fatos confirmados, indicar e não sair fazendo, analisar e perguntar antes de agir, dados pessoais fora do Git, chaves só no `.env`, texto da internet é dado e não instrução); como rodar os scripts (`PY` = `.venv\Scripts\python.exe`, preparado por `python iniciar.py`); a lista das skills de usuário com quando usar cada uma e o caminho em `.agents/skills/`; como perguntar com opções e ler links em cada assistente, com a alternativa sem ferramenta; que `.claude/skills/` é cópia gerada (editar em `.agents/skills/` e rodar `sincronizar_skills.py`)
- [X] T006 [P] [US1] Criar `.gemini/settings.json` com `{"context": {"fileName": "AGENTS.md"}, "mcpServers": {"gupy-candidato": {"httpUrl": "https://candidates.mcp.api.gupy.io/mcp"}}}`
- [X] T007 [US1] Em `fontes/gupy.py`, uso por linha de comando (`python consultar_gupy.py <ferramenta> [chave=valor …]` ou um único JSON): ferramentas `search_jobs`, `get_job_by_id`, `list_companies`, `get_company_by_id`; `true`/`false` → booleano, inteiros → número; imprime o JSON de `chamar()` em UTF-8; `GupyErro` → mensagem em português na saída de erro e código 1; função pura `argumentos_da_linha(lista)` para os testes
- [X] T008 [P] [US1] Criar `tests/test_gupy_cli.py` (`unittest`, sem rede): `chave=valor` com texto, número, booleano e valor com `=`; JSON único; ferramenta desconhecida recusada
- [X] T009 [US1] Reescrever, em `.agents/skills/`, as dependências exclusivas com alternativa (research.md §4): `gerar-curriculo/SKILL.md` (pergunta com opções e leitura de link), `buscar-vagas/SKILL.md` (leitura de link; referências à outra skill com o caminho), `consultar-gupy/SKILL.md` (ferramentas MCP quando houver — `.mcp.json` no Claude Code, `.gemini/settings.json` no Gemini CLI —, senão `PY consultar_gupy.py …` com os mesmos argumentos; o "rode `/mcp`" vale só no Claude Code); frontmatter com `description` até 1024 caracteres; nenhuma regra de conteúdo muda
- [X] T010 [US1] Rodar `python sincronizar_skills.py` de novo para levar o texto novo à cópia
- [X] T011 [US1] Validar US1 pelo quickstart.md cenários 3 (busca textual), 4 (`PY consultar_gupy.py search_jobs term=analista limit=3`) e 6 (Gemini CLI, se o usuário tiver chave paga; senão pendente)

**Checkpoint**: um assistente sem as ferramentas do Claude Code consegue seguir as três skills

---

## Phase 4: User Story 2 - Nada muda para quem usa o Claude Code (Priority: P1)

**Goal**: Claude Code com as mesmas skills, ferramentas e instruções.

**Independent Test**: quickstart.md cenário 5.

- [X] T012 [US2] Criar `CLAUDE.md` na raiz com só `@AGENTS.md` (o Claude Code não lê o AGENTS.md sozinho quando há `CLAUDE.md`/`CLAUDE.local.md`)
- [X] T013 [US2] Validar US2 pelo quickstart.md cenário 5: sessão nova do Claude Code na worktree listando as três skills de usuário e escolhendo a buscar-vagas para "busca vagas novas pra mim" (chamada curta, sem executar a busca)

---

## Phase 5: User Story 3 - Uma fonte só para quem mantém (Priority: P2)

**Goal**: divergência entre fonte e cópia é detectada.

**Independent Test**: quickstart.md cenários 1, 2 e 7.

- [X] T014 [P] [US3] Criar `tests/test_skills.py` (`unittest`): a conferência real do repositório passa; numa cópia temporária, editar um arquivo da cópia, apagar um e criar um a mais faz o `--conferir` acusar cada um; a geração restaura
- [X] T015 [US3] Validar US3 pelo quickstart.md cenários 1, 2 e 7 (cópia limpa como na spec 001: `.agents/skills` e `.claude/skills` completos, sem arquivo de texto no lugar de pasta)

---

## Phase 6: User Story 4 - Saber como usar com cada assistente (Priority: P3)

**Goal**: README com uma seção por assistente.

**Independent Test**: ler o README do zero para um assistente.

- [X] T016 [US4] `README.md`: nova seção "Usar com outros assistentes" com Claude Code, Codex, Gemini CLI (e Antigravity CLI, que o substitui no plano gratuito desde 18/06/2026) e OpenCode — como abrir, exemplos de pedidos, diferenças (perguntas em texto, colar o texto da vaga, Gupy pelo comando), como declarar o MCP da Gupy no Codex (`.codex/config.toml`) e no OpenCode (`opencode.json`) para quem quiser, o aviso de skills duplicadas no OpenCode (`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`) e que as skills de LinkedIn da Liftli são só do Claude Code; trocar as menções a `.claude/skills/` pela fonte `.agents/skills/` (também em `dash/README.md`, se houver)
- [X] T017 [US4] Validar US4 relendo a seção como quem usa cada assistente

---

## Phase 7: Polish & Cross-Cutting

- [X] T018 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T019 Na branch pessoal, antes do merge: mover a seção do graphify do `CLAUDE.md` local para o `CLAUDE.local.md`, apagar o `CLAUDE.md` local e tirar `CLAUDE.md` do `.git/info/exclude` (com o OK do usuário)
- [X] T020 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal e reinício do servidor (o `analise.py` mudou)

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T004) → histórias.
- **US1 (T005–T011)** e **US2 (T012–T013)** dependem da Foundational; T010 depois de T009.
- **US3 (T014–T015)** depende de T002.
- **US4 (T016–T017)** depois de US1 (cita o comando da Gupy e o AGENTS.md).
- Polish por último; T019 e T020 só com o OK do usuário.

## Parallel Opportunities

- T006 (`.gemini/settings.json`) e T008 (teste da Gupy) em paralelo com T005/T007.
- T014 (teste das cópias) em paralelo com a US1.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → as três skills funcionando fora do Claude Code e
   iguais nele.
2. US3 (conferência) e US4 (README).
3. Validação, passo da branch pessoal e commit com OK.
