---
description: "Tarefas da feature 036: Informações básicas no Meu perfil e idiomas com nível (Windows)"
---

# Tasks: Informações básicas no Meu perfil e idiomas com nível

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md).

**Testes**: pedidos pela constituição (função pura nova ganha `unittest`) e pelo SC-006. Ficam em
`tests/test_primeiros_passos.py` e `tests/test_analise_perfil.py`, sem rede e sem navegador. O front não tem testes
automáticos: `tsc --noEmit`, `vite build` e o teste do usuário na página.

**Caminhos**:
- **Backend**: na worktree `../mpt-036-informacoes-basicas` (branch `036-informacoes-basicas`).
- **Front**: na worktree `../mpt-front-027b`, numa branch `front-036-informacoes-basicas` saída da `frontend-react`.
  Os caminhos `src/…` são dessa worktree.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (arquivo diferente, sem depender de tarefa aberta)
- **[USn]**: história da spec

---

## Phase 1: Setup

- [X] T001 Na worktree `../mpt-front-027b`:
  1. conferir `git status` limpo;
  2. `git pull` da `frontend-react` (deve ficar em f117f3b ou depois);
  3. criar a branch `front-036-informacoes-basicas`;
  4. `npx -y pnpm@10.34.3 install --frozen-lockfile`;
  5. `npx -y pnpm@10.34.3 exec tsc --noEmit` deve passar antes de qualquer mudança.

## Phase 2: Foundational

Sem tarefa bloqueante. As histórias usam os dados e as rotas de hoje (`GET /api/candidatura`, `GET /api/perfil`).

---

## Phase 3: User Story 1 - Informações básicas no Meu perfil (Priority: P1) 🎯 MVP

**Goal**: a aba Informações básicas no Meu perfil, com dados de contato, respostas guardadas e sites, com ou sem perfil.

**Independent Test**:
- Meu perfil → Informações básicas: mudar o telefone e salvar; a próxima carta usa o telefone novo.
- Apagar uma resposta guardada: ela some da lista.

- [X] T002 [US1] Mover `src/components/modals/DadosContato.tsx` para `src/components/perfil/DadosContato.tsx` com `git mv`:
  - ajustar os imports relativos (`../../services/api/candidatura`, `../curriculo/Curriculos`);
  - ajustar o comentário do topo ("Meu perfil → Informações básicas");
  - não mudar o comportamento.
- [X] T003 [US1] Criar `src/components/perfil/InformacoesBasicas.tsx`:
  - **Props**: `{so: boolean, onAviso}`.
  - **Carga**:
    - com `so`, mostra "Só dá para ver e mudar estes dados no computador onde a ferramenta roda." e não chama a rota;
    - sem `so`, carrega `api.estado()` de `services/api/candidatura`;
    - um erro 403 (`ehErroApi(err) && err.status === 403`) mostra o mesmo texto.
  - **Seções**:
    - `<DadosContato>`;
    - "Respostas que você já deu": a lista com Apagar (`api.apagarMemoria`), como em `ConfigCandidatura.tsx:130-158`,
      com o texto "A ferramenta reaproveita estas respostas nas próximas vagas, sem perguntar de novo. A pretensão
      salarial e a relocação nunca ficam guardadas. Apague a que estiver errada ou desatualizada.";
    - "Onde a ferramenta preenche": conhecidos, liberados com Revogar (`api.dominio(d, "revogar")`) e bloqueados com o
      motivo, como em `ConfigCandidatura.tsx:160-183`.
  - **Depois de cada ação**: `Promise.all([carregar(), recarregarCandidatura()])`.
  - **Estilo**: as classes `SEC`, `H` e `DICA` do `MeuPerfil`.
- [X] T004 [US1] Em `src/components/perfil/MeuPerfil.tsx`:
  - `type Tela` ganha `"basicas"`, e `Props.telaInicial` aceita esse valor;
  - na navegação, depois de `PASSOS` e antes de "Currículo base", entra o botão "Informações básicas", **sempre
    visível**, com o mesmo estilo e `aria-current`;
  - o corpo de `tela === "basicas"` é `<InformacoesBasicas so={so} onAviso={onAviso} />`;
  - o rodapé tem `botaoIr(e.etapa && e.etapa !== "concluido" ? e.etapa : "concluido", "Voltar ao perfil")`;
  - `ir()` não salva o progresso para `"basicas"`;
  - `mostraRecomecar` exclui `"basicas"`;
  - o efeito de abertura respeita `telaInicial === "basicas"`.
- [X] T005 [US1] Em `src/App.tsx`: `perfilAberto` passa a ser `{ tela?: "analises" | "basicas" } | null`.

**Checkpoint**: a aba funciona sozinha. O diálogo de candidaturas ainda tem as seções duplicadas até a US2.

---

## Phase 4: User Story 2 - "Atualizar candidaturas" só com o acesso aos portais (Priority: P1)

**Goal**: o diálogo com Portais, Login guardado e a leitura, mais a linha que leva às Informações básicas.

**Independent Test**: abrir "Atualizar candidaturas". Aparecem só Portais, Login guardado e a leitura, e **Abrir**
leva ao Meu perfil na aba.

- [X] T006 [US2] Renomear `src/components/modals/ConfigCandidatura.tsx` para `src/components/modals/LoginGuardado.tsx`
  com `git mv`:
  - deixar só o bloco "Login guardado (opcional)": credenciais, Guardar, Trocar e Apagar, com a senha nunca voltando;
  - título "Login guardado da candidatura assistida (opcional)";
  - tirar `DadosContato`, a memória e os domínios;
  - atualizar o comentário do topo.
- [X] T007 [US2] Em `src/components/modals/ConnectedAccountsModal.tsx`:
  - trocar `<ConfigCandidatura>` por `<LoginGuardado>`;
  - acrescentar a prop `onAbrirInformacoes: () => void`;
  - logo depois do login guardado, a linha `DICA`: "Seus dados de contato, respostas guardadas e sites da candidatura
    assistida ficam em Meu perfil → Informações básicas." e o botão `BTN_MINI` **Abrir**, que chama
    `onAbrirInformacoes`.
- [X] T008 [US2] Em `src/App.tsx`, passar ao `ConnectedAccountsModal`
  `onAbrirInformacoes={() => { setIsAccountsModalOpen(false); setPerfilAberto({ tela: "basicas" }) }}` (depende de
  T005 e T007).

**Checkpoint**: US1 e US2 completas. Cada item fica num lugar só.

---

## Phase 5: User Story 3 - Idiomas com nível, numa lista (Priority: P1)

**Goal**: a pergunta de idiomas com as linhas de idioma e nível, o + e o ×, a descrição do nível e a validação.

**Independent Test**: responder Inglês B2, Português (BR) Nativo e Outro "Italiano" A2. A Revisão traz as três
linhas no formato `Idioma — Sigla (Nome)`.

- [X] T009 [P] [US3] Testes em `tests/test_primeiros_passos.py` (classe nova `TestIdiomas`):
  - `ler_idioma("Inglês — B2 (Intermediário superior)")` → `{idioma: "Inglês", outro: "", nivel: "B2", original: ""}`;
  - "Português — nativo" e "Portuguese (Native or bilingual)" → Português (BR), Nativo;
  - "English: C1" → Inglês, C1;
  - "Espanhol - b1" → Espanhol, B1;
  - "Inglês — Professional Working" → Inglês, nível `""`, `original` com o texto;
  - "Italiano — A2 (Básico)" → Outro, `outro: "Italiano"`, A2;
  - "Português (Portugal) — C2" → Outro, `outro: "Português (Portugal)"`, C2;
  - "Libras — intermediário" → Outro, "Libras", nível `""`, com o original;
  - a sigla só como palavra solta: "B2B" não é nível;
  - `ler_idiomas(None)` e `ler_idiomas([])` → `[]`;
  - `perguntas_para({})` traz a pergunta `idiomas` com `tipo == "lista"` e:
    - `idiomas == ["Inglês", "Português (BR)", "Francês", "Alemão", "Espanhol"]`;
    - 7 `niveis`, na ordem A1…C2 e Nativo, com o `rotulo` "B2 (Intermediário superior)" e "Nativo";
    - `linhas == []`;
  - com `respostas.idiomas` no estado, `linhas` vêm convertidas;
  - `PERGUNTAS` não é alterada (a pergunta é copiada).
- [X] T010 [P] [US3] Teste em `tests/test_analise_perfil.py`:
  - perfil com "- Inglês — B2 (Intermediário superior)" → `prontidao()` traz o inglês `pronto`;
  - "- Inglês — A2 (Básico)" → `falta`;
  - "- Inglês — Nativo" → `pronto`.
- [X] T011 [US3] Em `primeiros_passos.py`:
  - `IDIOMAS_PERFIL = ("Inglês", "Português (BR)", "Francês", "Alemão", "Espanhol")`;
  - `NIVEIS_IDIOMA` com `valor`, `rotulo` e `descricao`, igual à tabela de [data-model.md](data-model.md): "A1 (Iniciante)"
    → "Frases básicas do cotidiano, apresentações simples"… "Nativo" → "Língua materna";
  - `ler_idioma(texto) -> dict` e `ler_idiomas(lista) -> list[dict]`, pelas regras de [research.md](research.md) R3:
    - separadores `—`, `–`, ` - `, `:`, `(`, `,`;
    - sinônimos comparados com `filtros.sem_acento`, e Portugal/europeu viram Outro;
    - nível só pela sigla `\b[abc][12]\b` ou por nativo/nativa/native/língua materna;
    - `outro` com até 60 caracteres;
  - a pergunta `idiomas` em `PERGUNTAS` com o texto "Quais idiomas você fala e em que nível?", `tipo: "lista"`,
    `idiomas: list(IDIOMAS_PERFIL)` e `niveis: NIVEIS_IDIOMA`;
  - `perguntas_para(estado)` devolve uma cópia da pergunta com
    `linhas = ler_idiomas((estado.get("respostas") or {}).get("idiomas"))`.
- [X] T012 [P] [US3] Em `src/services/api/perfil.ts`, `Pergunta` ganha os campos opcionais:
  - `idiomas?: string[]`;
  - `niveis?: { valor: string; rotulo: string; descricao: string }[]`;
  - `linhas?: { idioma: string; outro: string; nivel: string; original: string }[]`.
- [X] T013 [US3] Criar `src/components/perfil/PerguntaIdiomas.tsx`, componente controlado:
  - **Props**: `{idiomas, niveis, linhas, onMudar, desabilitado}`.
  - **Cada linha**:
    - `<select>` de idioma, com as opções de `idiomas` + "Outro" e uma opção vazia "Idioma";
    - com Outro, `<input maxLength={60} placeholder="Qual idioma?">`;
    - `<select>` de nível, com `rotulo` como texto e uma opção vazia "Nível";
    - abaixo do nível, `descricao` em `DICA`;
    - com `original`, "você tinha escrito: …";
    - botão × com `aria-label="Remover {idioma}"`.
  - **Botão "+ Adicionar idioma"** no fim da lista.
  - **Layout**: as linhas quebram no celular (`flex-wrap`), cada select tem `<label>` acessível (`sr-only`) e os
    campos usam a classe `CAMPO`.
- [X] T014 [US3] Em `src/components/perfil/MeuPerfil.tsx`, `PerguntaAtual`:
  - **Quando usar**: quando `p.niveis?.length && p.idiomas?.length`, mostra `<PerguntaIdiomas>`.
  - **Estado inicial**: `p.linhas`, ou uma linha vazia se não houver.
  - **Conferência na Próxima** (FR-010), com um `role="alert"` que nomeia a linha:
    - ignora as linhas sem idioma e sem nível;
    - "Escolha o nível de {idioma}." quando falta o nível;
    - "Escreva o nome do idioma na linha {n}." quando o Outro está sem nome;
    - "{idioma} aparece duas vezes." quando há repetição, comparando com `sem acento + minúsculas` do nome final e
      contando "Outro: português" igual a Português (BR).
  - **Resposta**: `"{nome} — {rotulo do nível}"`. Uma lista vazia vira `null`.
  - **Botões**: Pular e Voltar continuam como estão.
  - **Página sem os campos novos**: continua a caixa de texto de hoje.

**Checkpoint**: a pergunta nova funciona, e a página antiga continua gravando texto livre.

---

## Phase 6: User Story 4 - Respostas antigas e a pergunta de inglês (Priority: P2)

**Goal**: sem a pergunta "Qual o seu nível de inglês?" e sem o inglês repetido no perfil.

**Independent Test**:
- "Inglês — Professional Working" reabre com o nível em branco e "você tinha escrito".
- Com "Inglês — B2 (…)" na lista e `respostas.ingles` antiga, o perfil não traz "Inglês (nível declarado)".

- [X] T015 [US4] Testes em `tests/test_primeiros_passos.py` (depende de T011):
  - nenhum id `ingles` em `perguntas_para({})`;
  - `validar_respostas({"ingles": "avancado"})` continua aceito;
  - montagem do perfil (a função que gera o Markdown a partir de `resp`):
    - com `idiomas: ["Inglês — B2 (Intermediário superior)"]` e `ingles: "avancado"`, sem "nível declarado";
    - com `idiomas: ["Inglês — Professional Working"]` e `ingles: "avancado"`, com "Inglês (nível declarado): avancado";
    - sem idiomas e com `ingles`, com a linha.
- [X] T016 [US4] Em `primeiros_passos.py` (depende de T011, mesmo arquivo):
  - tirar a pergunta `ingles` de `PERGUNTAS`;
  - `IDS` ganha `| {"ingles"}` (id antigo, com comentário);
  - na montagem, `if resp.get("ingles") and not _ingles_no_formato_novo(resp.get("idiomas"))`, em que o formato novo
    é uma linha com `ler_idioma(...)["idioma"] == "Inglês"` e `nivel` preenchido.

---

## Phase 7: User Story 5 - Os avisos apontam o lugar novo (Priority: P3)

**Goal**: nenhum texto manda mais a pessoa para "Atualizar candidaturas" atrás de dados de contato ou de sites.

**Independent Test**: carta sem dados de contato → o aviso diz "Meu perfil → Informações básicas".

- [X] T017 [P] [US5] Em `candidatura_ia.py:406-407`, o aviso passa a "… salve-os em Meu perfil → Informações básicas →
  Seus dados de contato.".
- [X] T018 [P] [US5] Em `src/components/kit/CandidaturaAssistida.tsx:299`, "Você pode revogar depois em Meu perfil →
  Informações básicas.".
- [X] T019 [P] [US5] `README.md`:
  - linhas 44, 58, 70-71, 81 e 378: os dados de contato, as respostas e os sites ficam em Meu perfil → Informações
    básicas; os logins guardados continuam em "Atualizar candidaturas";
  - a pergunta de idiomas, se o README a descrever.
- [X] T020 [P] [US5] `dash/API.md`:
  - §3.6: a pergunta `idiomas` com `idiomas`, `niveis` e `linhas`, e o fim da pergunta `ingles`, conforme
    [contracts/pergunta-idiomas.md](contracts/pergunta-idiomas.md);
  - título e texto da §3.11b: "Meu perfil → Informações básicas → contato, respostas e sites; Atualizar candidaturas →
    logins".
- [X] T021 [P] [US5] Em `.agents/skills/analisar-perfil/SKILL.md:114`, "idiomas com o nível (A1 a C2 do CEFR ou
  nativo), no formato 'Inglês — B2 (Intermediário superior)'; sem pergunta separada de inglês". Depois,
  `python sincronizar_skills.py` e `python sincronizar_skills.py --conferir`.

---

## Phase 8: Polish e entrega

- [X] T022 Rodar `python -m unittest discover -s tests` na worktree do backend: tudo passa.
- [X] T023 Rodar `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./` na worktree
  do front. Depois, commit na `front-036-informacoes-basicas`.
- [X] T024 Procurar dados pessoais no diff do backend e do front (nomes, empresas, números). Depois, commit na
  `036-informacoes-basicas`.
- [ ] T025 Na pasta principal (branch pessoal):
  - `git merge 036-informacoes-basicas`;
  - copiar o `dist/` do front para `dash/front/`, sem commit;
  - rodar os testes;
  - reiniciar o dashboard com `--sem-navegador`;
  - pedir o teste do usuário pelo [quickstart.md](quickstart.md).
- [ ] T026 Com o OK do usuário:
  1. `git checkout -- dash/front` na branch pessoal e apagar os assets novos;
  2. merge `--no-ff` da `036-informacoes-basicas` na `master` e `git push origin master`, só com os testes passando;
  3. merge da `front-036-informacoes-basicas` na `frontend-react` e push;
  4. `gh workflow run front.yml` e merge do PR `front/atualizacao` com squash;
  5. `git merge origin/master` na branch pessoal;
  6. apagar a worktree e as branches da feature;
  7. `graphify update .`.

---

## Dependencies & Execution Order

- **Setup (T001)** vem antes de todo o front.
- **US1 (T002–T005)** é o MVP e não depende das outras.
- **US2 (T006–T008)** depende de T005 (o tipo de `perfilAberto`) para o botão Abrir. O resto é independente.
- **US3**:
  - backend: T009–T011;
  - front: T012–T014, que dependem só de T011 para testar de ponta a ponta;
  - T009 e T010 vêm antes de T011, porque os testes devem falhar primeiro.
- **US4 (T015–T016)** depende de T011, por ser o mesmo arquivo e usar `ler_idioma`.
- **US5 (T017–T021)** é independente; todas as tarefas são [P].
- **Polish (T022–T026)** vem no fim, nessa ordem.

## Parallel Opportunities

- O backend (T009–T011, T015–T016, T017, T019–T021) e o front (T002–T008, T012–T014, T018) andam em paralelo,
  porque estão em worktrees diferentes.
- Na US3: T009, T010 e T012 em paralelo.
- Na US5: T017 a T021 em paralelo.

## Implementation Strategy

1. **MVP**: Setup e US1. A aba Informações básicas já atende o pedido central.
2. US2 completa a mudança de lugar, e cada item fica num lugar só.
3. US3 e US4: idiomas com nível, sem inglês repetido.
4. US5: textos e documentos.
5. Polish e entrega na ordem de T022 a T026. A master, o push e o PR do front só depois do OK do usuário.
