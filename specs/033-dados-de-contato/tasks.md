---
description: "Tarefas da feature 033: Dados de contato na candidatura assistida, sem IA (Windows)"
---

# Tasks: Dados de contato na candidatura assistida, sem IA

**Input**: spec.md, plan.md, research.md (R1–R4, D1–D6), data-model.md, contracts/contato.md, quickstart.md.

**Testes**: incluídos (fluxo da constituição). Ficam em `tests/test_dados_contato.py`, sem rede e sem navegador:
`PaginaFalsa` como em `tests/test_candidatura_assistida.py`, `banco.ARQUIVO` e `filtros.CONFIG` temporários, um texto
de currículo fictício e `ia.responder` trocado para provar que a IA não é chamada.

**Formato**: `[P]` = pode rodar em paralelo (arquivo diferente, sem dependência pendente); `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Base de testes em `tests/test_dados_contato.py`:
  - diretório temporário para `banco.ARQUIVO` (os dados vão ao lado) e `filtros.CONFIG` com
    `localidade: {pais: "Brasil", estado: "SP", cidade: "São Paulo"}`;
  - `PaginaFalsa` com campos configuráveis (`rotulo`, `tipo`, `tipo_html`, `autocomplete`, `nome`, `opcoes`, `valor`),
    importada de `tests/test_candidatura_assistida.py` ou com uma versão mínima;
  - currículo fictício em texto ("Ana Exemplo Silva", "ana.exemplo@email.com", "(11) 90000-0000",
    "linkedin.com/in/ana-exemplo").

## Phase 2: Foundational (bloqueia as histórias)

- [X] T002 `candidatura/contato.py`, armazenamento:
  - `CAMPOS`, `arquivo()` (`banco.ARQUIVO.parent / "contato.json"`), `ler()` (`{}` sem arquivo ou com arquivo
    ilegível) e `apagar()`;
  - `gravar(dados)` com a validação do data-model:
    - textos de **até 200**, telefone de **até 40**;
    - e-mail no formato `a@b.c`; LinkedIn com `linkedin.com/`; portfólio `http(s)://…` ou um domínio;
    - valor com cara de **CPF, RG ou data de nascimento** (as expressões `CPF`, `RG` e `NASCIMENTO` de
      `primeiros_passos`) recusado, com o nome do campo;
    - campo vazio não é gravado;
  - escrita em `.tmp` com `os.replace`, sob uma trava.

**Checkpoint**: `tests/test_candidatura_assistida.py` passa sem mudança.

## Phase 3: User Story 1 - Cadastrar e confirmar (P1) 🎯 MVP

**Goal**: a proposta vem do currículo, da memória e dos filtros; a pessoa confere e salva; nada é gravado antes.

**Independent Test**: proposta com nome, e-mail, telefone e LinkedIn; `contato.json` não existe até o `gravar`.

- [X] T003 [US1] `contato.propor()`:
  - **currículo base**: `curriculo_base.marcados()` (pt, depois en), lido por `primeiros_passos.extrair`;
    `reconhecer_contato` dá e-mail, telefone e LinkedIn;
  - **nome**: a primeira linha do texto com **de 2 a 6 palavras, só letras, até 60 caracteres e sem "@"**. O primeiro
    nome vai para `nome`, e o resto para `sobrenome`;
  - **memória** (`memoria._carregar()`), pelas chaves conhecidas (first name, last name, email address, email, phone,
    city, postal, address e os sinônimos em português), só no que faltou;
  - **filtros** (`filtros.efetivos(filtros.ler_config())["localidade"]`): cidade, estado e país;
  - `fontes` por campo e `avisos` (ex.: "o currículo traz 2 e-mails; ficou o primeiro", "sem currículo base marcado");
  - erro de leitura do currículo vira aviso e não derruba a proposta.
- [X] T004 [US1] `dash/servidor.py`, dentro de `_candidatura`:
  - `GET /api/candidatura` passa a trazer `contato` e `campos_contato`;
  - `POST /api/candidatura/contato/proposta` → `contato.propor()`;
  - `PUT /api/candidatura/contato` → `{contato: contato.gravar(corpo["dados"])}`, com 400 no `ValueError`;
  - `DELETE /api/candidatura/contato` → `{contato: contato.apagar()}`.
- [X] T005 [P] [US1] Testes:
  - proposta do currículo fictício (`primeiros_passos.extrair` trocado para devolver o texto): nome "Ana", sobrenome
    "Exemplo Silva", e-mail, telefone e LinkedIn; `contato.json` não existe depois (SC-003);
  - memória preenche o que o currículo não trouxe; filtros dão cidade, estado e país;
  - primeira linha que não parece nome ("Currículo 2026", com número) fica sem nome;
  - `gravar` recusa e-mail inválido, LinkedIn sem `linkedin.com` e CPF; aceita e lê de volta; `apagar` remove;
  - rotas pelo servidor real numa porta livre (`GET`, `PUT` com 400 e 200, `DELETE` e proposta).

**Checkpoint**: US1 testável sozinha.

## Phase 4: User Story 2 - Preencher em qualquer formulário (P1)

**Goal**: em "Preencher esta página", os campos de contato reconhecidos recebem os dados salvos, sem IA.

**Independent Test**: página com "Full name", "E-mail", "Celular", "LinkedIn profile" e campos com `autocomplete`;
todos preenchidos com a fonte "seus dados de contato" e zero chamadas à IA.

- [X] T006 [US2] `contato.reconhecer(campo)` (D2):
  - `None` para marca `sensivel`;
  - **`autocomplete`**: `given-name`, `family-name`, `name`, `email`, `tel`/`tel-national`, `address-level2`,
    `address-level1`, `country`/`country-name`, `postal-code`, `address-line1`/`street-address`, `url`;
  - **tipo**: `email`, `tel`; `url` vira LinkedIn se a pergunta ou o `name` falam de LinkedIn, senão portfólio;
  - **sinônimos**: a pergunta inteira (sem acento, sem `*`, "obrigatório", "required", "optional") precisa bater com a
    lista de R4. O `name` do campo também conta (ex.: `first_name`, `email`, `phone`).
- [X] T007 [US2] `contato.valor_para(campo, dados)` (D5):
  - texto: o valor; `nome_completo` = nome + sobrenome;
  - lista ou seleção de país: a opção cujo texto normalizado bate com o país ou com o nome em inglês
    (`filtros.PAISES`);
  - estado: a sigla ou o nome (`fontes._comum.UFS`);
  - sem opção que bata, `None`.
- [X] T008 [US2] `candidatura/auto.preencher_pagina`:
  - antes da memória, para cada campo fora de `NA_JANELA`, sem valor e com marca `cadastro` ou `comum`: `k =
    contato.reconhecer(c)` e `v = contato.valor_para(c, dados)`;
  - os achados vão por `preencher(..., da_pessoa=True)`, com `fonte: "seus dados de contato"`;
  - os campos preenchidos saem dos passos seguintes (memória e IA).
- [X] T009 [P] [US2] Testes:
  - "Full name", "Nome", "E-mail", "Celular" e "LinkedIn profile" reconhecidos e preenchidos (SC-001);
  - `autocomplete=given-name` e `family-name`;
  - "Nome da empresa anterior" não reconhecido;
  - "País de cidadania" (sensível) não preenchido;
  - lista de país com "Brazil" escolhida; estado "SP";
  - campo já preenchido não trocado;
  - IA trocada por um erro: os campos de contato são preenchidos mesmo assim (SC-002); a IA não recebe nenhum dado de
    contato (SC-003);
  - sem dados salvos, o campo vira pergunta, como hoje.

## Phase 5: Polish & Cross-Cutting

- [X] T010 Front, na `frontend-react` (worktree própria saída de `origin/frontend-react`, branch
  `front-033-dados-de-contato`):
  - `src/services/api/candidatura.ts`: `contato`, `campos_contato` e os clientes de proposta, salvar e apagar;
  - em `src/components/modals/ConfigCandidatura.tsx`, a seção "Seus dados de contato" (ou componente
    `DadosContato.tsx`): os campos (endereço e CEP opcionais), "Propor a partir do currículo" com a fonte de cada
    valor, Salvar, Apagar e a dica de privacidade;
  - `npm run build` sem erro e commit local, **sem push** antes do back-end na master;
  - build de teste copiado no `dash/front` da branch pessoal, sem commit.
- [X] T011 [P] Documentação: `dash/API.md` §3.11b (rotas e fonte "seus dados de contato"), README (candidatura
  assistida) e uma linha na spec 027 apontando para a 033.
- [ ] T012 Verificação:
  - `PY -m unittest discover -s tests` inteiro;
  - na branch pessoal de teste: proposta com o currículo base do usuário (SC-004), salvar, e "Preencher esta página"
    num formulário real;
  - `graphify update .`.
- [ ] T013 Procurar dados pessoais nos arquivos alterados; commit; merge na branch pessoal; teste da pessoa; com o OK,
  master, push e o front.

## Dependencies & Execution Order

- **T001** → **T002** → histórias.
- **US1 (T003–T005)** é o MVP. **US2 (T006–T009)** só depende de T002, e pode andar junto com US1, mas `auto.py` vem
  depois de T006 e T007.
- **T010** (front) depende das rotas de T004. **T011** em paralelo. T012 e T013 por último.

## Parallel Opportunities

- US1 e US2 tocam funções diferentes de `contato.py` e podem ser escritas em sequência curta. Os testes ficam no mesmo
  arquivo, um bloco depois de cada tarefa.
- T010 e T011: arquivos diferentes.

## Implementation Strategy

1. **MVP**: T001–T005. Cadastrar e confirmar os dados pelos testes e pelas rotas.
2. US2: reconhecer e preencher.
3. Front e documentação; verificação com o currículo real; master.
