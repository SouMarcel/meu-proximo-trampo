---
description: "Tarefas da feature 045: O que as vagas pedem, no painel Métricas & Funil (Windows)"
---

# Tasks: O que as vagas pedem, no painel Métricas & Funil

**Input**: spec.md, plan.md, research.md (D1–D12), data-model.md, contracts/api-requisitos.md,
contracts/painel-requisitos.md, quickstart.md.

**Testes**: `tests/test_requisitos.py` (constituição: funções puras novas ganham `unittest`). O banco é temporário e
a IA é falsa, no molde de `tests/test_forcar.py`. O front é conferido com `tsc --noEmit`, `vite build`, a conferência
por CDP só com leituras e o roteiro do quickstart.

**Caminhos**:
- Python e documentos: a worktree da branch `045-requisitos-vagas`;
- front: a worktree da `frontend-react` ao lado da pasta do projeto, abreviada como `FR/`.

**Formato**: `[P]` = pode rodar em paralelo; `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 Conferir a worktree do front `FR/`:
  - `git fetch origin`;
  - a `frontend-react` igual à `origin/frontend-react` e sem mudanças;
  - o `node_modules` presente, ou então `npx -y pnpm@10.34.3 install --frozen-lockfile`.

## Phase 2: Foundational

- [X] T002 `dash/requisitos.py` (novo), a base (data-model §1, research D2 e D7):
  - **Cabeçalho:** a docstring do módulo; `_raiz()` como em `analise.py`; os imports de `banco` e `analise` no topo.
  - **`chave(nome)`:** `conferir.norm`, sem espaços e sem pontuação, mas mantendo `+` e `#`.
  - **`validar(r, provedor="", modelo="")`:** devolve o objeto limpo ou `None`. Segue as regras da tabela do
    data-model §1:
    - habilidades: até 30, nome de 1 a 60, `tipo` `tecnica`/`comportamental` (outro vira `tecnica`), `exigida` bool;
    - certificações: até 15, nome de 1 a 80, `tipo` `certificacao`/`curso` (outro vira `curso`);
    - os cortes do FR-002: nomes que começam por "N anos", "anos de", "experiência", "vivência", "conhecimento em",
      "years", "experience", e nomes de idioma;
    - um item por chave, com `exigida` se algum for;
    - `experiencia.anos`: inteiro de 0 a 40 ou `null`; `em` até 80; `frase` até 200. Sem `anos` e sem `frase`, sai;
    - `formacao.nivel`: `tecnico`, `graduacao`, `pos`, `mestrado` ou `doutorado` (outro tira o objeto); `areas` até 5,
      de até 60;
    - `idiomas`: até 6; `nivel` `basico`, `intermediario`, `fluente` ou `nativo` ("avancado" vira `fluente`); um item
      por idioma, com o maior nível;
    - `lido_em` = hoje; `provedor` e `modelo` no formato de `analise_provedor`.
- [X] T003 `dash/banco.py` (data-model §1):
  - **`validar_analise`:** com `a["requisitos"]`, grava `requisitos.validar(a["requisitos"], provedor, modelo)` em
    `limpos["requisitos"]`, com o import dentro da função. O `None` não grava, e um campo inválido não derruba a
    análise.
  - **`aplicar_requisitos(lista)`:** cada `{"id", "requisitos"}` troca só `requisitos` e `atualizada_em`, sem
    `aplicar_criterios`. Devolve `(ids, problemas)`, como `aplicar_analises`.
- [X] T004 [P] `tests/test_requisitos.py` (novo), a base:
  - os cortes do FR-002 ("5+ anos de experiência", "Experiência com SQL", "Inglês" saem; "Gestão de projetos" fica);
  - tipos e limites; um item por chave; "avançado" virando "fluente";
  - `chave("Power BI") == chave("PowerBI")` e `chave("C#") != chave("C++")`;
  - `aplicar_analises` com `requisitos` grava o campo com a IA e a data;
  - `aplicar_requisitos` muda só `requisitos` e `atualizada_em` (nota, resumo, encaixe, lacunas, alertas, triagem e
    etapa iguais).

**Checkpoint**: o campo `requisitos` existe, é validado e gravado pelas duas portas.

## Phase 3: User Story 1 - Habilidades, certificações e tempo de experiência (Priority: P1) 🎯 MVP

**Goal**: a análise traz os requisitos; a leitura avulsa preenche as vagas antigas; a seção mostra as habilidades, as
certificações e o tempo de experiência da seleção.

**Independent Test**: quickstart, passos 1 a 6.

- [X] T005 [US1] `.agents/skills/buscar-vagas/SKILL.md`, o item `requisitos` (FR-001 a FR-003, research D3):
  - vai entre os campos do passo 3, depois de `riscos` e antes de "Critérios da nota em…", dentro do trecho que
    `analise._secao` copia;
  - diz o formato e as regras:
    - só o que o anúncio diz;
    - experiência não é habilidade;
    - nomes curtos: em português quando há nome comum, ferramentas e métodos pelo nome próprio, e o nome do perfil
      quando é a mesma habilidade;
    - técnica ou comportamental, exigida ou desejável;
    - o mínimo de anos da atividade principal;
    - o nível mínimo de formação;
    - os idiomas com a escala do `ingles`;
  - depois, `python sincronizar_skills.py`.
- [X] T006 [US1] `dash/analise.py`: a linha de formato de `montar_pedido` ganha `"requisitos" {…}` entre os opcionais
  (contrato). Os requisitos da análise passam pela IA que respondeu (o `analise_provedor`/`analise_modelo` que já vai em
  cada análise).
- [X] T007 [US1] `dash/requisitos.py`, a seleção e as contas do US1 (research D6 e D9, data-model §2 e §3):
  - **Seleção:** `na_aplicacao(v)` (regra `noQuadro`), `area_de(v)` (regra `areaDe`), `selecionar(vagas, vagas_sel,
    area)` e a normalização dos parâmetros (inválido volta ao padrão).
  - **`contagem`:** `selecao`, `com_requisitos`, `a_ler`, `sem_texto` e `sem_analise`, mais `poucas`.
  - **Habilidades e certificações:** grupos por `chave`, uma vez por vaga, com nome na grafia mais frequente. Cada item
    leva `vagas`, `exigida`, `parte`, `ids` e `perfil` ("nao" até o US2), na ordem do data-model. As habilidades se
    dividem em `tecnicas` e `comportamentais`.
  - **Tempo de experiência:** as faixas `ate1`, `2a3`, `4a5`, `6a9`, `10mais` e `nao_diz`, mais o `destaque`.
  - **`resumo(vagas, perfil, vagas_sel, area)`:** devolve o dicionário do data-model §3 com essas partes. Os outros
    blocos ficam vazios até o US2 e o US3.
- [X] T008 [US1] `dash/requisitos.py`, a leitura avulsa (research D4, contrato):
  - **`a_ler(vagas)`:** as vagas que o botão lê.
  - **`montar_pedido(vagas, nomes_perfil)`:** a abertura, o item `requisitos` da skill por `analise._secao`, os nomes
    do perfil, o aviso de texto da internet e as vagas com `integridade.limpar` e `analise.LIMITE_DESCRICAO`.
  - **`ler_lote(lote, nomes)`:** chama `ia.responder` e lê o array, ignorando ids fora do lote. Grava com
    `banco.aplicar_requisitos`, com a `ia.marca()` em cada item.
  - **Classe `Leitura`:**
    - `iniciar(vagas_sel, area)`: não abre uma segunda leitura e devolve False sem IA;
    - `parar()` e `estado()` (data-model §4);
    - a thread roda os lotes de `analise.lotes(a_ler(...))`, espera enquanto `analise.FILA.rodando` e confere a marca de
      parar entre os lotes;
    - na falha, guarda o erro com `ia.mascarar` e para;
    - nunca derruba o servidor.
  - **Instância:** `LEITURA = Leitura()`.
- [X] T009 [US1] `dash/servidor.py` (contrato):
  - **`GET /api/requisitos`:** lê `vagas` e `area` da consulta e devolve `requisitos.resumo(...)` com `leitura` e `ia`
    (`analise.ligada()`, `analise.descricao_ia()`).
  - **`POST /api/requisitos/ler` e `/api/requisitos/parar`:** só deste computador (`SO_LOCAL_PERFIL`); 202, 200 ou 409,
    como no contrato.
  - **Rota no `_tratar`:** entra antes da rota genérica de vagas.
- [X] T010 [P] [US1] `tests/test_requisitos.py`, US1:
  - **Seleção:** Em Aplicações (manual e seguida com etapa, encerrada incluída; seguida sem etapa fora); Todas (só
    `analise_status` feita); área pela `area` gravada e pelos `grupos`.
  - **Contas:** contagem e `poucas`; uma vez por vaga; grafia mais frequente; ordem; `parte`; as faixas de anos (0, 1,
    2, 3, 5, 6, 10, `null`, ausente) e o desempate do destaque.
  - **Pedido:** traz os nomes do perfil, não traz o resto do perfil, usa o texto limpo e o item da skill.
  - **`Leitura` com IA falsa:**
    - lotes gravados e notas intactas;
    - parar depois do primeiro lote;
    - falha que para e guarda o motivo;
    - retomar sem reler (SC-004);
    - vaga suspeita num lote só dela;
    - sem IA, não começa.
  - **Rotas:** o GET com parâmetro inválido; o POST de fora do computador (403); sem IA (409); já rodando (200).
  - **Skill:** o pedido de `analise.montar_pedido` contém o item `requisitos`.
- [X] T011 [P] [US1] `FR/src/types/api.ts`, `FR/src/services/api/requisitos.ts` (novo) e `FR/src/services/storage.ts`:
  - os tipos `Requisitos` (opcional em `Vaga`), `ResumoRequisitos` e `EstadoLeitura` (data-model §1, §3 e §4);
  - `resumo(vagas, area)`, `ler(vagas, area)` e `parar()` com `pedir`;
  - `PREF_KEYS.METRICAS_REQUISITOS = "mpt_pref_metricas_requisitos"` e `get`/`saveMetricasRequisitos`, validando os
    valores (inválido volta ao padrão).
- [X] T012 [US1] `FR/src/components/RequisitosVagas.tsx` (novo), o US1 (contrato de tela):
  - **Cabeçalho:** o título e o subtítulo.
  - **Seletor:** Vagas e Área, com `aria-pressed`, guardado pelo `storage`.
  - **Linha de contagem:** com os complementos que existirem.
  - **Leitura:** o botão com a IA, o estado sem IA (link para `onAbrirIA`), "Lendo X de N…" com Parar, parada e erro.
    Durante a leitura, pede o resumo a cada 3 s.
  - **Recarga:** o resumo é pedido de novo quando a seleção ou a `versao` mudam.
  - **Poucas vagas e nenhuma vaga com requisitos:** os textos do contrato.
  - **Blocos:**
    - Habilidades mais pedidas: abas Técnicas e ferramentas / Comportamentais, 15 linhas com "Ver todas (N)", a etiqueta
      do perfil quando vier diferente de "nao" e o rodapé da base;
    - Certificações e cursos;
    - Tempo de experiência, com a faixa mais pedida marcada.
- [X] T013 [US1] `FR/src/components/FunnelAnalytics.tsx` e `FR/src/App.tsx` (FR-022, research D10):
  - sai o cálculo `topSkills` e o quadro "Habilidades Mais Valorizadas nas Vagas";
  - a seção `RequisitosVagas` entra depois do funil;
  - a Distribuição por plataforma vai para o fim, na largura toda;
  - as props novas `versao`, `onSelectVaga`, `onAbrirIA` e `onAbrirPerfil`, passadas pelo App (`versaoInfo?.versao`,
    `setDetalheId`, `setIsAIModalOpen(true)` e `setPerfilAberto({})`);
  - saem os ícones que ficarem sem uso.

**Checkpoint**: US1 completa. Com a IA, a leitura enche as três listas e as notas não mudam (SC-002, SC-003, SC-004).

## Phase 4: User Story 2 - Suas habilidades (Priority: P2)

**Goal**: o quadro com as habilidades e certificações da pessoa e as etiquetas do perfil nas listas.

**Independent Test**: quickstart, passo 7.

- [X] T014 [US2] `dash/requisitos.py`, o perfil (research D7 e D8, data-model §3 `suas`):
  - **`ler_perfil(texto)`:** as seções pelo título ("Habilidades", "Competências" ou "Skills"; "Certificações",
    "Cursos" ou "Certifications"). Só linhas de lista; "Rótulo: a, b, c" dá um item por nome; "Nome — nível" e
    "Nome (detalhe)"; os nomes com barra viram partes; a linha de exemplo com "ex.:" é ignorada. Devolve as linhas e o
    texto fora dessas seções.
  - **`combina(pedido, item)`:** chave igual, ou o nome menor (3 letras ou mais) inteiro no outro, por
    `conferir._contem`. Ferramentas parecidas não contam (sem `conferir.FAMILIAS`).
  - **`citada(pedido, texto_fora)`.**
  - **No `resumo`:** a marca `perfil` (`habilidade`/`certificacao`, `citada`, `nao`) em habilidades e certificações, e o
    bloco `suas`, com as linhas em ordem, os ids, `destaque` nas 5 primeiras com vagas, os zeros no fim, `aparecem`,
    `total`, `existe_perfil` e `tem_secao`. O perfil vem de `analise_perfil.perfil_texto()`, com os relatos.
- [X] T015 [P] [US2] `tests/test_requisitos.py`, US2, com um perfil fictício:
  - "Ferramenta — nível", "Stack geral: Jira, Confluence", "Python/Pandas — profissional" e "PSM I (em preparação)";
  - a linha de exemplo ignorada; títulos "Competências" e "Skills";
  - `combina`: Jira com Jira Software; C fora de C#; Power BI fora de Looker;
  - citada fora das seções, incluindo um relato;
  - ordem, destaque, zeros no fim e `aparecem`/`total`;
  - perfil sem a seção dá `tem_secao` false.
- [X] T016 [US2] `FR/src/components/RequisitosVagas.tsx`, US2:
  - o bloco Suas habilidades: o resumo "N das suas M habilidades…", as linhas com o nível e "N vagas", o destaque nas
    cinco e as de zero apagadas com "nenhuma vaga desta seleção";
  - "Suas certificações";
  - sem a seção, o texto e o botão Meu perfil (`onAbrirPerfil`);
  - as etiquetas com texto nas listas ("✓ nas suas habilidades", "• citada no seu perfil", "não está no seu perfil").

**Checkpoint**: US2 completa. O quadro e as etiquetas batem com o perfil.

## Phase 5: User Story 3 - Formação, idiomas, senioridade, modelo e contratação (Priority: P2)

**Goal**: os outros indicadores da seleção.

**Independent Test**: quickstart, passo 1 (indicadores sem leitura), e o passo 3 com formação e idiomas.

- [X] T017 [US3] `dash/requisitos.py`, os indicadores (research D9, data-model §3):
  - **Formação:** os níveis, mais `nao_diz`, e as áreas agrupadas por `chave`.
  - **Idiomas:** o idioma pela chave, com os níveis. O inglês da vaga sem `requisitos` vem do campo `ingles` (sem
    `nao_pede`).
  - **Senioridade e modelo:** sem `nao_informado`.
  - **Contratação:** junta `tipo_emprego` e `contratacao`; `tempo_integral`/`clt` viram "CLT", os dois `pj` viram
    "PJ"; os rótulos vêm de `kit.CONTRATACAO` e de `filtros.TIPOS_EMPREGO`.
  - **Contagem:** cada vaga uma vez por valor, com `base` e `ids`.
- [X] T018 [P] [US3] `tests/test_requisitos.py`, US3:
  - formação "Não diz";
  - áreas agrupadas;
  - o inglês pelo `ingles` quando não há `requisitos`, e pelo `requisitos` quando há;
  - a vaga "CLT ou PJ" uma vez em cada, e `tempo_integral` com `clt` uma vez só;
  - modelo sem `nao_informado`;
  - as bases diferentes de cada bloco.
- [X] T019 [US3] `FR/src/components/RequisitosVagas.tsx`, US3: os blocos Formação (níveis e "Áreas mais citadas"),
  Idiomas (idioma com os níveis em etiquetas), Senioridade e modelo e Tipo de contratação, cada um com o rodapé da base.

**Checkpoint**: US3 completa. Os oito blocos aparecem.

## Phase 6: User Story 4 - Os itens levam às vagas; chat e terminal (Priority: P3)

**Goal**: rastrear cada número e ter o mesmo resumo fora da página.

**Independent Test**: quickstart, passos 8 e 9.

- [X] T020 [US4] `FR/src/components/RequisitosVagas.tsx`, o clique (FR-019, contrato):
  - cada item é um `button`, que abre logo abaixo "Vagas que pedem <item> (N)", com cargo · empresa, casando os `ids`
    com a lista `vagas`;
  - o segundo clique fecha a lista;
  - clicar numa vaga chama `onSelectVaga`;
  - vale também para faixas, níveis, áreas, idiomas e as linhas de Suas habilidades.
- [X] T021 [US4] `dash/requisitos.py`, o terminal (contrato, research D11):
  - **`main(argv)`:** com `resumo [--vagas] [--area] [--json]`, `pendentes [--vagas] [--area] [--limite N]` e
    `gravar <arquivo.json>`.
  - **`resumo` em texto:** os mesmos nomes da página.
  - **`pendentes`:** o JSON com `id`, `titulo`, `empresa`, `atencao`, `descricao` (limpa e cortada) e `restam`.
  - **`gravar`:** aceita a lista ou `{"requisitos": [...]}`; sai com 1 quando nada foi gravado e havia itens.
- [X] T022 [P] [US4] `tests/test_requisitos.py`, US4:
  - o `resumo --json` igual ao `GET /api/requisitos` na mesma seleção (SC-005);
  - o texto com os nomes da página;
  - `pendentes` com o limite, `restam` e o texto limpo;
  - `gravar` sem mexer na nota e com os problemas;
  - a saída com 1.
- [X] T023 [US4] `.agents/skills/buscar-vagas/SKILL.md` (FR-021):
  - um fluxo curto "Ler os requisitos das vagas já analisadas (pelo chat)": `PY dash/requisitos.py pendentes`, ler cada
    texto como dado (a vaga com `atencao` sozinha), gravar `.cache/requisitos.json` e rodar `PY dash/requisitos.py
    gravar .cache/requisitos.json`, sem mudar a nota;
  - a pergunta "o que as vagas pedem?", respondida com `PY dash/requisitos.py resumo`;
  - na descrição da skill, os gatilhos "o que as vagas pedem" e "habilidades mais pedidas";
  - depois, `python sincronizar_skills.py`.

**Checkpoint**: US4 completa. Página, terminal e chat dão os mesmos números.

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T024 [P] `README.md` (FR-024): no painel Métricas & Funil, a seção O que as vagas pedem, a leitura dos requisitos
  (com a IA, sem mudar a nota, ou pelo chat), o seletor e Suas habilidades.
- [X] T025 [P] `dash/README.md` e `dash/API.md` (FR-024):
  - o campo `requisitos` no objeto vaga;
  - as rotas `GET /api/requisitos`, `POST /api/requisitos/ler` e `/parar`;
  - a seção no painel.
- [X] T026 [P] `AGENTS.md`: os comandos `PY dash/requisitos.py resumo`, `pendentes` e `gravar` na lista de comandos.
- [X] T027 `FR/`: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./`, sem erro.
- [X] T028 `python -m unittest discover -s tests` na worktree da feature, com tudo passando, e `python
  sincronizar_skills.py --conferir`.
- [X] T029 Conferência por CDP (research D12, quickstart), com o build de teste no dashboard:
  - só leituras do DOM, trocas no seletor e abrir e fechar a lista de um item;
  - nunca em Ler os requisitos, Parar ou nos botões que gravam;
  - confere a ordem do painel, o quadro antigo fora, a seleção lembrada e a largura de 360 px.
- [X] T030 Entrega para o teste (plan, Entrega 1 e 2):
  - busca de dados pessoais no diff;
  - commit local na `045-requisitos-vagas` e na `frontend-react`;
  - merge na branch pessoal;
  - o build em `dash/front/` sem commit;
  - o dashboard reiniciado.

## Phase 8: Ajustes do teste (03/11)

- [X] T031 `FR/src/components/RequisitosVagas.tsx` (FR-025): Senioridade e Modelo de trabalho em blocos separados, cada
  um com o título e a base; o contrato de tela acompanha.
- [X] T032 `dash/analise.py` e `dash/requisitos.py` (FR-026):
  - `analise.lista_json` (bloco de código, vírgula sobrando, resposta cortada), usada também por `analise.analisar`;
  - `analise.lotes(vagas, tamanho)`;
  - na leitura, `LOTE_LEITURA = 5`, o lote dividido ao meio quando volta ilegível ou com vagas de fora,
    `ILEGIVEIS_SEGUIDAS = 3` e a última resposta ilegível em `.cache/`;
  - a regra da `frase` curta na skill;
  - na validação, "Experiência com X", "Conhecimento em X" e afins viram a habilidade X, e os códigos com acento
    ("avançado", "Pós-graduação", "Comportamental") valem, como veio da IA gratuita no diagnóstico;
  - testes em `tests/test_requisitos.py`.

## Dependencies & Execution Order

- T001 → T002 → T003 → T004.
- **US1:**
  - T005 e T006 podem ir juntos;
  - T007 → T008 → T009 (mesmo módulo e rotas);
  - T010 depois de T009;
  - T011 a qualquer momento depois de T001;
  - T012 depois de T011;
  - T013 depois de T012.
- **US2 e US3:** mexem em `dash/requisitos.py` e em `RequisitosVagas.tsx` depois do US1, em sequência (T014 → T017;
  T016 → T019). Os testes (T015, T018) vão logo depois de cada parte.
- **US4:** T020 depois de T019; T021 depois de T017; T022 depois de T021; T023 depois de T021.
- **Polish:** T024 a T026 a qualquer momento depois de T023; T027 a T030 no fim, nesta ordem.

## Parallel Example

```text
T005 (skill) junto com T006 (analise.py) e T011 (tipos e API do front)
T024 (README) junto com T025 (dash/README e API.md) e T026 (AGENTS.md)
```

## Implementation Strategy

- **MVP:** Phases 1 a 3. A seção já mostra as habilidades, as certificações e o tempo de experiência, e a leitura enche
  as vagas antigas.
- **Depois:** US2 (Suas habilidades), US3 (os outros indicadores) e US4 (rastrear, terminal e chat).
- **Entrega:** uma só, para o teste na branch pessoal (T030). Master, push e PR esperam o OK da pessoa.
