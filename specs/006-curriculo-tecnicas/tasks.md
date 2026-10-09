---

description: "Tarefas da feature 006: currículo com técnicas (Windows)"
---

# Tasks: Currículo com técnicas

**Input**: Design documents from `/specs/006-curriculo-tecnicas/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-curriculo.md, quickstart.md

**Tests**: `unittest` para o motor e a conferência (constituição), com currículo, perfil e vaga
fictícios; o resto pelo quickstart.

**Organization**: por história (US1–US4). **Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Guardar a referência de hoje: gerar o `.docx` do `.agents/skills/gerar-curriculo/modelo.json` com o `curriculo.py` atual numa pasta temporária e salvar o XML do documento (`word/document.xml` e `word/styles.xml`, sem as propriedades com data) para comparar depois (SC-006)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 Em `curriculo.py`, o catálogo (research.md §1, data-model.md): `TECNICAS` (`ats`, `foco`, `xyz`, `resultado_primeiro`, `competencias_primeiro`: nome, explicação, padrão) e `ESCOLHAS` (`paginas` 1|2 padrão 2, `formato` br|us|eu padrão br, `estilo` padrao|compacto|executivo padrão padrao), `ler_tecnicas(cv) -> dict | None` (padrões preenchidos; `None` sem a chave) e a validação em `validar()` (chaves e valores conhecidos; `destaques` lista de até 3 textos; no `us`, recusar `foto`, `nascimento`, `estado_civil`, `nacionalidade`, `documentos`); `CHAVES` ganha `tecnicas` e `destaques`
- [X] T003 [P] `tests/test_curriculo.py`: validação das técnicas (valores inválidos, `destaques` com mais de 3, dados pessoais no `us`) e o JSON sem `tecnicas` gerando o mesmo XML da referência de T001

**Checkpoint**: catálogo e validação; currículo sem técnicas igual ao de hoje

---

## Phase 3: User Story 1 - Escolher as técnicas do currículo (Priority: P1) 🎯 MVP

**Goal**: o motor segue formato, estilo e ordem escolhidos; catálogo com sugestão para a skill.

**Independent Test**: quickstart.md cenários 1 a 6.

- [X] T004 [US1] Em `curriculo.py`, o formato (research.md §3): papel (A4 ou Letter 21,59 × 27,94 cm) e idioma dos títulos (`br` pt, `us`/`eu` en) a partir de `tecnicas.formato`; `LARGURA_TEXTO` calculada do papel e das margens no `Montador` (não mais constante)
- [X] T005 [US1] Em `curriculo.py`, os estilos como tabela de valores (margens, fonte do corpo, espaços, tamanho do nome e dos títulos): `padrao` = valores de hoje, `compacto` (margens e espaços menores, corpo 10 pt), `executivo` (corpo 10,5 pt, mais respiro); nunca abaixo de 10 pt no corpo
- [X] T006 [US1] Em `curriculo.py`, a ordem e os destaques: sem `ordem` no JSON e com `competencias_primeiro`, Competências antes de Experiência; seção `destaques` (título "Destaques"/"Highlights") logo depois do Resumo; técnicas gravadas nas propriedades do `.docx` (comentários) (FR-006)
- [X] T007 [US1] Em `curriculo.py`, `sugerir(vaga=None) -> dict` (research.md §6: idioma por palavras comuns de PT e EN; local nos Estados Unidos → `us`; país europeu → `eu`; senão `br`; ATS marcado) e `--tecnicas [--vaga-id ID | --vaga arquivo]` imprimindo o catálogo com a sugestão em JSON (vaga do dashboard por `dash/banco.py`)
- [X] T008 [P] [US1] Testes em `tests/test_curriculo.py`: papel e idioma por formato; fonte do corpo por estilo; Competências antes de Experiência; Destaques depois do Resumo; propriedades com as técnicas; `sugerir` com vaga brasileira, americana e europeia fictícias
- [X] T009 [US1] Validar US1 pelo quickstart.md cenários 1 a 6

**Checkpoint**: currículo no formato e estilo escolhidos

---

## Phase 4: User Story 2 - Conferência antes de entregar (Priority: P1)

**Goal**: conferência sem IA com veredito ok, conferir ou bloquear.

**Independent Test**: quickstart.md cenários 7 a 11.

- [X] T010 [US2] Criar `conferir.py` com a parte de **fatos** (research.md §5): extrair do currículo números (percentuais, valores com R$/US$/€ e mil/k/M/bi, "N vezes"/"Nx", número + substantivo), normalizar ("1,5 mil" = "1.500" = "1500"; "30%" = "30 %") e procurar no perfil (ausente → `bloquear`); empresas e cargos da experiência fora do perfil → `conferir`; datas mês/ano que não batem → `conferir`; cada ponto com trecho
- [X] T011 [US2] Em `conferir.py`, **requisitos × perfil**: separar os requisitos da vaga pelos cabeçalhos PT/EN (ou pelas linhas com marcador), termos significativos sem palavras vazias, tabela pequena de famílias equivalentes, situação `tem`/`sustentado`/`lacuna` com a evidência; lacuna cujo termo está em Competências → `bloquear`; cobertura das palavras-chave (achadas, total, faltando)
- [X] T012 [US2] Em `conferir.py`, **ATS** no `.docx` (python-docx): títulos de seção do catálogo, contato no corpo (nada em cabeçalho ou rodapé), sem tabelas, imagens, caixas de texto ou várias colunas, fonte comum; no `us`, dados pessoais no contato; sem `.docx`, "não conferida"
- [X] T013 [US2] Em `conferir.py`, `conferir(cv, perfil_texto, vaga_texto=None, docx=None) -> dict` (data-model.md) com o veredito mais grave, e a linha de comando do contrato (`--vaga`, `--vaga-id`, `--perfil`, `--json`; códigos 0, 1, 3, 2); em `curriculo.py`, rodar a conferência no fim quando houver perfil (caminho do `config.json`) e mostrar o veredito (código 3 com "bloquear")
- [X] T014 [P] [US2] `tests/test_conferir.py`: número inventado (bloquear), número escrito de outro jeito (não aponta), empresa a mais (conferir), lacuna em Competências (bloquear), requisito sustentado por equivalente, `.docx` com tabela e com contato no cabeçalho, cobertura de palavras-chave, tempo ≤ 5 s
- [X] T015 [US2] Validar US2 pelo quickstart.md cenários 7 a 11

**Checkpoint**: conferência pronta e usada pelo motor

---

## Phase 5: User Story 3 - Técnicas de escrita aplicadas pela skill (Priority: P2)

**Goal**: a skill pergunta as técnicas, escreve conforme elas e confere antes de entregar.

**Independent Test**: quickstart.md cenário 12.

- [X] T016 [P] [US3] Criar `.agents/skills/gerar-curriculo/tecnicas.md`: como escrever cada técnica (bullet = ação + escopo + ferramenta + resultado; XYZ só com número confirmado, senão qualitativo e pergunta; foco: seleção, ordem e até 3 destaques; resultado primeiro; competências primeiro com 6 a 8 itens só de tem/sustentado; palavras-chave reformuladas a partir do que a pessoa tem; formato `us` em inglês fiel ao perfil, sem dados pessoais; expressões vazias a evitar)
- [X] T017 [US3] Em `.agents/skills/gerar-curriculo/SKILL.md`: passo "Técnicas" depois do alvo (lê `PY curriculo.py --tecnicas [--vaga-id ID]`, pergunta as caixas com múltipla escolha e as três escolhas pela ferramenta de opções do assistente, sugestão marcada), leitura do `tecnicas.md`, conferência obrigatória (`PY conferir.py … --vaga-id ID`) antes de entregar, "bloquear" = não entrega até resolver, e limite de páginas pelo `tecnicas.paginas`; `modelo.json` com `tecnicas` e `destaques` de exemplo; conferir se `sincronizar_skills.py` copia os arquivos extras da pasta da skill e rodar
- [ ] T018 [US3] Validar US3 pelo quickstart.md cenário 12 (Claude Code)

---

## Phase 6: User Story 4 - Páginas sob controle (Priority: P2)

**Goal**: limite de páginas medido, com aviso e sugestões de corte.

**Independent Test**: quickstart.md cenário 3.

- [X] T019 [US4] Em `curriculo.py`: com `tecnicas.paginas`, comparar as páginas do PDF com o limite; acima, sair com código 3 e "deu N páginas; o limite é M", com sugestões (experiências mais antigas, cargos com mais de 5 itens, cursos antigos, resumo com mais de 4 linhas); sem PDF, "páginas não medidas"; sem `tecnicas`, o aviso de hoje (acima de 2)
- [X] T020 [P] [US4] Testes em `tests/test_curriculo.py` das sugestões de corte (função pura sobre o JSON) e do compacto ocupando menos que o padrão no mesmo conteúdo (comparando páginas quando houver PDF, senão a altura estimada)
- [X] T021 [US4] Validar US4 pelo quickstart.md cenário 3

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T022 [P] `README.md` (seção Currículo: técnicas, formatos, estilos, páginas e a conferência com `conferir.py`) e `AGENTS.md` (comando `conferir.py`)
- [X] T023 Rodar `python -m unittest discover -s tests` e o quickstart.md; registrar os resultados no `quickstart.md`
- [X] T024 Busca de dados pessoais no diff, mostrar ao usuário e, com o OK, commit na `master`, push, merge na branch pessoal e `graphify update .`

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T003) → histórias.
- **US1 (T004–T009)** e **US2 (T010–T015)** podem andar em paralelo (`curriculo.py` × `conferir.py`),
  exceto T013, que mexe no fim do `curriculo.py` depois de T004–T006.
- **US3 (T016–T018)** depende de US1 e US2 (a skill usa os dois).
- **US4 (T019–T021)** depende de US1.
- Polish por último; T024 só com o OK do usuário.

## Parallel Opportunities

- Testes (T003, T008, T014, T020) em arquivos próprios.
- `conferir.py` (T010–T012) em paralelo com o motor (T004–T007).
- `tecnicas.md` (T016) e README (T022) a qualquer momento depois do desenho.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 + US2 → currículo nas técnicas escolhidas e conferido.
2. US3 (skill) e US4 (páginas).
3. Validação completa e commit com OK.
