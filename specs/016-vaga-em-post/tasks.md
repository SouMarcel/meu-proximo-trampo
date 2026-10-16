---

description: "Tarefas da feature 016: Vaga publicada em post (Windows)"
---

# Tasks: Vaga publicada em post

**Input**: Design documents from `/specs/016-vaga-em-post/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, contracts/extracao-ia.md,
quickstart.md

**Tests**: `unittest` sem rede (constituição: funções puras novas ganham testes). Para o LinkedIn, abridor falso
como em `tests/test_linkedin.py`; para a IA, `ia.responder` falso; banco temporário como em `tests/test_busca.py`.
A página é verificada pelo quickstart.

**Organization**: por história, na ordem de prioridade da spec. A US1 traz a leitura, a extração e a gravação. A US2
traz o e-mail no cartão e no kit. A US3 e a US4 reaproveitam a extração e o formulário da US1.

**Plataforma**: Windows 10/11.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivo diferente, sem dependência pendente)
- **[Story]**: história da spec (US1–US4)

---

## Phase 1: Setup

- [X] T001 Rodar `.venv\Scripts\python.exe -m unittest discover -s tests` na worktree e anotar o total de testes que
  passam (linha de base: 245).
- [X] T002 [P] Criar os dados de teste fictícios `tests/dados/linkedin/post.html` (autor página de empresa) e
  `tests/dados/linkedin/post-pessoa.html` (autor pessoa). Eles reproduzem só a estrutura da página pública de
  incorporação (research §1):
  - o elemento de classe `attributed-text-segment-list__content` com o texto;
  - o link com `data-tracking-control-name="public_post_embed_feed-actor-name"` e `href` com `/company/<slug>` ou
    `/in/<slug>`;
  - a meta `og:url` com `https://www.linkedin.com/feed/update/urn:li:activity:7000000000000000001`;
  - o `<time>` com "1 d".

  O texto é inventado ("Empresa Exemplo", cargo, requisitos em lista, `vagas@empresa-exemplo.com.br` com assunto,
  hashtags), sem nada do post real (princípio II).

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Em `dash/banco.py`, criar `limpar_contato(email, assunto) -> dict` (usada pela US1 e pela US2):
  - `email_candidatura`: "texto ≤ 254", regex `^[^@\s]+@[^@\s]+\.[^@\s]+$`, "vazio apaga";
  - `assunto_candidatura`: "texto ≤ 200", uma linha, "vazio apaga".

  E-mail inválido levanta `ValueError("e-mail de candidatura inválido")`. Devolve só as chaves recebidas, com `None`
  para apagar.

**Checkpoint**: nada muda no comportamento; os 245 testes continuam passando.

---

## Phase 3: User Story 1 - Adicionar uma vaga pelo link de um post (Priority: P1) 🎯 MVP

**Goal**: colar o link de um post público abre o formulário preenchido pela IA. A vaga só é gravada no clique e
entra no Relatório com a etiqueta Post.

**Independent Test**: quickstart cenários 1 e 2; `tests/test_post.py` (leitura com o HTML fictício, extração com a
IA falsa, gravação com `post_id`).

### Leitura do post

- [X] T004 [US1] Criar `fontes/post.py` com `PostErro(motivo)` e `id_do_post(url) -> dict | None` (research §2):
  - reconhece `linkedin.com/feed/update/urn:li:activity:N` (com ou sem query);
  - reconhece `linkedin.com/posts/<slug>-activity-N-<sufixo>`;
  - reconhece `urn:li:share:N` e `urn:li:ugcPost:N` em qualquer parte do link, inclusive codificados (`%3A`);
  - devolve `{"urn": "urn:li:<tipo>:N", "id": "lip-N" | "lip-sN" | "lip-uN"}`; outro link, inclusive
    `/jobs/view/…`, devolve `None`.
- [X] T005 [US1] Em `fontes/post.py`, criar `ler(url, abridor=None) -> dict`:
  - um único pedido a `https://www.linkedin.com/embed/feed/update/<urn>`, sem cookies, sem seguir redirecionamento
    (como `linkedin._SemRedirecionar`) e com o `User-Agent` de `fontes.link.NAVEGADOR`;
  - 429, 999, 401, 403 e 3xx levantam `PostErro` com `linkedin._motivo(codigo)`, **sem** chamar `_bloquear`, sem
    gravar `.cache/linkedin-espera.json` e sem consultar `espera()` (FR-003, FR-004);
  - 404 e 410 levantam "o post não existe mais ou não é público"; erro de rede levanta o motivo; mais de 3.000.000
    bytes levanta "página grande demais";
  - o texto sai de `link._Classes(("attributed-text-segment-list__content",))` + `link.texto_de_html`, cortado em
    20.000 caracteres;
  - o autor é o texto do link `public_post_embed_feed-actor-name`; `autor_tipo` é `"empresa"` se o `href` tem
    `/company/`, `"pessoa"` se tem `/in/`, e `""` se não há autor;
  - o id vem de `og:url` com `urn:li:activity:N` (canônico) e, sem ele, do link;
  - sem texto, levanta "não achei o texto do post";
  - devolve `{"id", "url", "texto", "autor", "autor_tipo"}`.
- [X] T006 [US1] Em `fontes/link.py`, `ler()` passa a levantar `LinkErro` ("é um post, não uma página de vaga") quando
  `post.id_do_post(url)` reconhece o link, em vez de tentar o número da vaga. O servidor trata o post antes (T010);
  esta é só a defesa para outros chamadores.

### Extração com IA

- [X] T007 [US1] Criar `post_ia.py` com `ExtracaoErro` e `extrair(texto, autor="", autor_tipo="") -> dict`, conforme
  `contracts/extracao-ia.md`:
  - remove do texto as marcas `<<<TEXTO`/`TEXTO>>>` e corta em 20.000 caracteres;
  - monta o pedido com o texto entre as marcas como dado e as regras de lá;
  - chama `ia.responder(pedido, tempo=120)`, e `ia.IAErro` vira `ExtracaoErro` com `ia.mascarar`;
  - lê o JSON entre o primeiro `{` e o último `}`; sem JSON ou JSON inválido levanta `ExtracaoErro`;
  - limpa os campos: `titulo` "≤ 200", `empresa` "≤ 120", `local` "≤ 120", `url` "http/https e presente literalmente
    no texto; senão vazio", `email_candidatura` "válido e presente literalmente no texto; senão vazio",
    `assunto_candidatura` "≤ 200", `parece_vaga` booleano, `vagas` "inteiro 0–20";
  - sem empresa na resposta e com `autor_tipo == "empresa"`, usa o autor;
  - devolve também `provedor` e `modelo` (`ia.escolha_efetiva()` / `ia.modelo_efetivo`).

### Gravação e servidor

- [X] T008 [US1] Em `dash/banco.py`, `criar_manual(campos)` passa a aceitar:
  - `formato` (só `"post"`);
  - `post_id` (precisa casar com `^lip-[su]?\d{1,25}$` e `ID_VALIDO`), que vira o id da vaga no lugar do `m-…`;
  - `email_candidatura` e `assunto_candidatura`, via `limpar_contato`;
  - `publicado_por` ("≤ 120"), que entra em `anotacao` como "Publicado por: [nome]".

  Com `post_id` já no banco, ou repetida por `achar_repetida`, devolve a vaga existente sem gravar. Para isso, a
  função passa a devolver `(vaga, nova)`. Ajustar o único chamador em `dash/servidor.py` e os testes que usam
  `criar_manual`.
- [X] T009 [US1] Em `dash/servidor.py`, `POST /api/vagas`: com `nova` falso, responde 200
  `{"vaga", "nova": false}`; com `nova` verdadeiro, responde 201 como hoje, com `"nova": true`.
- [X] T010 [US1] Em `dash/servidor.py`, `POST /api/vagas/link`, antes de `link.ler`, quando `post.id_do_post(url)`
  reconhece o link (contrato `contracts/api.md`):
  1. se `banco` já tem o id do link, responde 200 `{"vaga", "nova": false}` sem pedido ao LinkedIn;
  2. chama `post.ler(url)`. Com `PostErro`, responde 422 `{"erro", "parcial": {"url", "plataforma": "LinkedIn",
     "formato": "post"}, "sugestao": "colar"}`;
  3. se o id canônico já está no banco, responde 200 `{"vaga", "nova": false}`;
  4. senão, responde 200 com:
     - `post`;
     - `parcial`: `url` canônico, `plataforma` LinkedIn, `formato` post, `post_id`, `descricao` (o texto),
       `empresa` (se o autor é empresa), `publicado_por` (se é pessoa), `area` e `pais_vaga` via
       `filtros.area_da_vaga`;
     - `ia`: `{"disponivel": ia.disponivel(), "local": self._local(), "provedor", "modelo"}`.
- [X] T011 [US1] Em `dash/servidor.py`, nova rota `POST /api/vagas/extrair`:
  - só deste computador (`SO_LOCAL_PERFIL`, 403);
  - corpo `{"texto", "autor", "autor_tipo"}`; texto vazio dá 400 "cole o texto do post ou da mensagem";
  - sem IA dá 409 "nenhuma IA configurada";
  - `ExtracaoErro` dá 502 com o motivo;
  - sucesso dá 200 `{"campos", "parece_vaga", "vagas", "provedor", "modelo"}`;
  - nada é gravado nem escrito em log.

  A rota fica antes do `_id_da_rota`, para não ser confundida com uma vaga de id "extrair".

### Página

- [X] T012 [US1] Em `dash/dashboard.html`, o formulário do Adicionar Vaga ganha:
  - os campos "E-mail de candidatura" (`a-email`, `type="email"`, maxlength 254) e "Assunto" (`a-assunto`,
    maxlength 200);
  - os ocultos `a-formato`, `a-post-id` e `a-publicado-por`;
  - `mostrarFormulario(etapa, parcial)` preenche todos eles;
  - o envio inclui os campos novos;
  - com resposta `nova: false`, mostra `jaEstava(v)`.
- [X] T013 [US1] Em `dash/dashboard.html`, `buscarLink()` trata a resposta com `j.post` (research §5):
  - se `j.ia.disponivel && j.ia.local`: status "Em análise pela IA (provedor · modelo), aguarde…", chamada a
    `POST /api/vagas/extrair` com `{texto, autor, autor_tipo}`, e então `mostrarFormulario("relatorio", parcial +
    campos)`. Os avisos ficam no status:
    - `parece_vaga` falso: "o texto não parece uma vaga";
    - `vagas > 1`: "o post traz N vagas; esta é a primeira. Para as outras, use Colar texto";
    - descrição com menos de 200 caracteres: "a vaga pode estar na imagem do post; cole o texto dela";
  - senão, abre direto o formulário com o `parcial` e o aviso "Sem IA: confira e complete cargo e local" (ou "a
    leitura com IA só funciona no computador onde a ferramenta roda");
  - erro da extração abre o formulário com o `parcial` e "A IA não conseguiu ler (motivo). Complete os dados.";
  - com o botão Buscar desabilitado durante a espera, Cancelar fecha o diálogo, e uma resposta que chegue depois de
    fechado é ignorada;
  - 422 com `sugestao: "colar"` mostra o motivo e o botão "Colar texto de post ou mensagem" (a US3 o liga).
- [X] T014 [P] [US1] Em `dash/dashboard.html`, criar `postTag(v)`, que devolve a etiqueta "Post" quando
  `v.formato === "post"`, e mostrá-la ao lado de `platTags` nos cartões do relatório e do quadro e no título do
  detalhe (junto de `intTag`).

### Testes

- [X] T015 [P] [US1] Criar `tests/test_post.py` com:
  - `id_do_post` para os quatro formatos, query, codificação e links de vaga (`None`);
  - `ler` com abridor falso servindo `post.html` e `post-pessoa.html` (texto, autor, `autor_tipo`, id canônico, URL
    pedida = embed, um único pedido);
  - `extrair` com `ia.responder` falso (casos de `contracts/extracao-ia.md`);
  - `criar_manual` com `post_id` (id `lip-…`, repetido devolve `nova` falso, `publicado_por` vai para a anotação,
    `formato` post).

**Checkpoint**: US1 completa; um link de post vira vaga com etiqueta Post depois do clique.

---

## Phase 4: User Story 2 - E-mail de candidatura na vaga (Priority: P1)

**Goal**: e-mail e assunto editáveis no cartão expandido de qualquer vaga, com "Enviar por e-mail" (`mailto:`) e
com o kit mostrando a candidatura por e-mail.

**Independent Test**: quickstart cenário 6; testes de `PATCH` com e-mail válido, inválido e vazio.

- [X] T016 [US2] Em `dash/banco.py`, `_validar_usuario` aceita `email_candidatura` e `assunto_candidatura` via
  `limpar_contato`. Inválido dá 400 "e-mail de candidatura inválido"; vazio apaga o campo.
- [X] T017 [US2] Em `dash/dashboard.html`, `renderDetalhe` ganha, acima das Anotações:
  - dois campos, "E-mail de candidatura" (`d-email`) e "Assunto" (`d-assunto`), preservando o que foi digitado entre
    renders, como `notaAtual`;
  - o botão do rodapé muda de "Salvar anotações" para "Salvar" e envia `anotacao`, `email_candidatura` e
    `assunto_candidatura` num só `PATCH`. Um e-mail que não passa no `checkValidity` do navegador avisa e não salva;
  - com e-mail salvo, o link "Enviar por e-mail":
    `mailto:<email>?subject=<encodeURIComponent(assunto)>`, com o título "Só abre o seu programa de e-mail; nada é
    enviado".
- [X] T018 [US2] Em `dash/dashboard.html`, no kit:
  - `ktSistema(v)` devolve "e-mail" quando há `email_candidatura` e não há `ats`/`url_candidatura`;
  - `ktCampos` mostra a linha "Candidatura por e-mail" com o e-mail e o assunto;
  - no item `candidatar` de `ktItem`, com e-mail, a ação é o mesmo link `mailto:` ("Enviar por e-mail").
- [X] T019 [P] [US2] Em `tests/test_post.py`, testar:
  - `limpar_contato` (válido, inválido, vazio apaga, assunto de várias linhas vira uma);
  - `atualizar_usuario` com os campos novos;
  - que os outros campos continuam recusados.

**Checkpoint**: US2 completa; qualquer vaga guarda e mostra o e-mail de candidatura.

---

## Phase 5: User Story 3 - Colar o texto de um post ou mensagem (Priority: P2)

**Goal**: "Colar texto de post ou mensagem", ao lado de "Preencher à mão", leva ao mesmo formulário pela mesma
extração.

**Independent Test**: quickstart cenário 5.

- [X] T020 [US3] Em `dash/dashboard.html`, o link "Colar texto de post ou mensagem" fica ao lado de "Preencher à mão"
  (e também é mostrado pelo 422 com `sugestao: "colar"`). Ele abre:
  - uma `textarea` (`a-colar`, maxlength 20000);
  - o botão "Continuar", que segue o mesmo fluxo da T013 com `{texto}`, sem autor. Os dados de ia vêm de
    `IA.e.disponivel` e da origem da página. O `parcial` tem a descrição com o texto colado, a plataforma "LinkedIn"
    (editável), `formato` post e o link do 422, se houver.

  Texto vazio pede "Cole o texto". Texto com mais de 20.000 caracteres é cortado, com aviso.
- [X] T021 [P] [US3] Em `tests/test_post.py`, testar `extrair` com texto colado sem autor e com um link de candidatura
  escrito no texto: o link vai para `url`. Testar também que um link inventado pela IA (fora do texto) é descartado.

**Checkpoint**: US3 completa; WhatsApp, Instagram, e-mail ou post privado viram vaga pelo texto.

---

## Phase 6: User Story 4 - Sem IA, com falha ou com bloqueio: o formulário resolve (Priority: P2)

**Goal**: em todo caminho sem IA ou com erro, o formulário abre com o que houver e diz o motivo. Um bloqueio para no
primeiro pedido e não grava a espera.

**Independent Test**: quickstart cenários 3 e 4; testes de bloqueio sem rede.

- [X] T022 [US4] Em `dash/dashboard.html`, conferir e completar as mensagens dos caminhos de reserva:
  - sem IA;
  - IA de outro aparelho;
  - erro da IA;
  - 422 do post (bloqueio, privado, fora do ar), com o motivo e o botão "Colar texto de post ou mensagem".

  Nenhum caminho grava sem o clique em Adicionar (SC-003).
- [X] T023 [P] [US4] Em `tests/test_post.py`, testar:
  - 429, 999, 302 e 403 levantam `PostErro` com o motivo de `linkedin._motivo`, com um único pedido e sem criar
    `ARQ_ESPERA` (apontar `linkedin.ARQ_ESPERA` para uma pasta temporária);
  - 404 dá "não é público";
  - com a espera ativa (arquivo de espera recente), `post.ler` faz o pedido normalmente;
  - página sem texto dá `PostErro`.
- [X] T024 [P] [US4] Em `tests/test_post.py`, testar `extrair` sem IA (`ia.responder` levantando "a IA está desligada")
  e com JSON inválido: os dois levantam `ExtracaoErro` com motivo legível.

**Checkpoint**: todas as histórias funcionam de forma independente.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T025 [P] Atualizar a documentação (FR-017):
  - `README.md`: Adicionar Vaga com link de post ou texto colado; uma consulta pública, sem login; extração com a IA
    escolhida; e-mail de candidatura no cartão;
  - `AGENTS.md`: uma linha em "Respeite os portais" sobre a leitura pontual de post;
  - `.agents/skills/buscar-vagas/SKILL.md`: vagas de post adicionadas no dashboard e o e-mail de candidatura;
  - rodar `python sincronizar_skills.py` e `python sincronizar_skills.py --conferir`.
- [X] T026 Rodar `.venv\Scripts\python.exe -m unittest discover -s tests`: total da T001 + os novos, todos passando.
- [X] T027 Verificação na página (Windows), pelo quickstart:
  - servidor da worktree com `--sem-navegador --porta 8766`, para não mexer no da branch pessoal;
  - cenários 1–7 com um post público real e a IA da pessoa, com o OK dela para cada pedido real ao LinkedIn;
  - nada do post real fica em arquivo do repositório.
- [ ] T028 (adiada em 2026-10-16: a pessoa não tinha link nesse formato; os testes automáticos cobrem os formatos) Com o OK da pessoa, um pedido real com um link de post no formato `share` ou `ugcPost` (research §2,
  quickstart cenário 8). Se o id canônico não vier, registrar em research.md.
- [X] T029 Antes do commit:
  - procurar dados pessoais no diff (nomes, empresas, e-mails reais, cargos do usuário, caminhos pessoais) e no
    `tests/dados/linkedin/post*.html`;
  - mostrar o resultado à pessoa;
  - com o OK dela: commit na branch, merge na `master`, push, merge na branch pessoal e
    `graphify update .`.

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003)** → as histórias.
- **US1 (T004–T015)**:
  - T004 → T005 → T006;
  - T007 é independente de T004–T006;
  - T008 → T009;
  - T010 depende de T005 e T008;
  - T011 depende de T007;
  - T012 → T013, que depende de T010 e T011;
  - T014 é independente;
  - T015 vem depois de T005, T007 e T008.
- **US2 (T016–T019)**: depende só da T003. Pode correr em paralelo com a US1 (arquivos em comum: `dash/banco.py` e
  `dash/dashboard.html`; alternar com cuidado).
- **US3 (T020–T021)**: depende da T011 e da T013.
- **US4 (T022–T024)**: depende da T005, da T007 e da T013.
- **Polish (T025–T029)**: depois das histórias. A T027 e a T028 pedem o OK da pessoa para os pedidos reais. A T029
  pede o OK para commit e push.

### Parallel Opportunities

- T002 em paralelo com a T001.
- Na US1: T007 (`post_ia.py`) em paralelo com T004–T006 (`fontes/post.py`); T014 em paralelo com T012–T013.
- Testes [P] (T015, T019, T021, T023, T024) no mesmo arquivo: escrever em sequência, mas cada um logo depois do
  código que cobre.
- T025 (documentação) em paralelo com a US3 e a US4.

### Parallel Example: User Story 1

```text
T004–T006  fontes/post.py, fontes/link.py   leitura do post
T007       post_ia.py                       extração com IA
T014       dash/dashboard.html              etiqueta Post
```

---

## Implementation Strategy

1. **MVP = Phases 1–3 (US1).** O link de post vira vaga preenchida pela IA, com etiqueta Post. O e-mail já é gravado
   pelo formulário.
2. **Incremento: Phase 4 (US2).** O e-mail fica editável no cartão de qualquer vaga, com `mailto:` e o kit.
3. **Incremento: Phases 5–6 (US3, US4).** Colar texto e todos os caminhos de reserva.
4. **Polish e entrega**, com o OK da pessoa em cada passo público (pedidos reais ao LinkedIn, commit, push).
