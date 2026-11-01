---
description: "Tarefas da feature 042: empresas acompanhadas em qualquer página de vagas (Windows)"
---

# Tasks: Empresas acompanhadas em qualquer página de vagas

**Input**: spec.md, plan.md, research.md (R1–R6, D1–D9), data-model.md, contracts/empresas.md, contracts/api.md,
quickstart.md. Molde: `fontes/ats.py` (spec 031), `post_ia.py` (pedido à IA que só copia), `fontes/ey.py`.

**Testes**: incluídos, em `tests/test_empresas_sites.py`, sem rede e sem IA de verdade (`_comum.baixar` e
`ia.responder` trocados, memória numa pasta temporária).

**Formato**: `[P]` = pode rodar em paralelo; `[USn]` = história da spec.

## Phase 1: Setup

- [X] T001 [P] Amostras fictícias em `tests/dados/empresas-sites/`:
  - `teamtailor.rss`: o formato da research R2, com nomes, endereços e números trocados. Itens:
    - vaga remota (`fully`) no Brasil;
    - vaga `onsite` em outra cidade;
    - vaga `hybrid` na cidade da pessoa;
    - vaga `none`;
    - vaga antiga, fora da janela;
  - `teamtailor-pagina.html`: a página de vagas com o `<link rel="alternate" … jobs.rss>` e "teamtailor";
  - `pagina-propria.html`: o formato da research R3, com uma seção `id="vagas"` de três blocos (um "Home Office", um
    "Presencial | <cidade>", um de outro cargo), o e-mail de recrutamento e um trecho oculto com instrução para a IA;
  - `ey-sem-resultado.html`: a página "There are currently no open positions", com `tr.data-row` no CSS.

## Phase 2: Foundational

- [X] T002 `fontes/ats.py`:
  - `SISTEMAS` e os rótulos;
  - `reconhecer` sem pedido, com `*.teamtailor.com` e `careers.ey.com`, e a recusa de portal de vagas
    (`integridade.PORTAIS` e Indeed, menos a EY), com a exceção `Desconhecido` para outro domínio;
  - `conferir(e)`;
  - `descobrir(url)` (um GET; feed do Teamtailor → `teamtailor`, senão `pagina`; o nome do feed, de `og:site_name` ou
    do `<title>`);
  - `vaga_do_link` para Teamtailor e EY.
- [X] T003 `filtros.py`:
  - `"ey"` sai de `FONTES_NAC` e de `FONTES_PADRAO`;
  - migração da EY em `efetivos` (data-model.md);
  - `_empresas` com `ats.conferir` para a empresa já reconhecida e `reconhecer` para o link solto;
  - `acompanhar` com `ats.descobrir`.
- [X] T004 `vagas.fontes_da_busca` usa `f["fontes"]` (de `efetivos`), no lugar da lista crua do config.

## Phase 3: User Story 1 - Acompanhar pelo link (P1) 🎯 MVP

- [X] T005 [US1] `dash/servidor.py`: `POST /api/empresas/reconhecer` (contracts/api.md), com `rotulo`,
  `ia_necessaria` e `ia_ligada`; `POST /api/empresas` com `descobrir`. Erros viram 400 com a mensagem.
- [X] T006 [US1] Testes:
  - reconhecer: Greenhouse como antes, `x.teamtailor.com`, `careers.ey.com`, LinkedIn recusado, domínio desconhecido
    pede Adicionar;
  - descobrir: página do Teamtailor → `teamtailor` com o nome; página própria → `pagina`, id sem `#`;
  - conferir e `_empresas` sem pedido;
  - a rota com o `_comum.baixar` trocado.

## Phase 4: User Story 2 - Teamtailor e EY na busca (P1)

- [X] T007 [US2] `fontes/teamtailor.py`: `feed`, `ler_feed` (`xml.etree`, limite de tamanho, mapeamento do
  data-model.md) e `lista`.
- [X] T008 [US2] `fontes/ats.py`: `_lista` e o filtro por sistema. Teamtailor e página própria vêm já normalizados; a
  EY delega a `ey.buscar`. Bloqueio por host (Teamtailor e página própria) e o aviso de 404.
- [X] T009 [US2] `dash/banco.py`: `"Teamtailor"` e `"Site da empresa"` em `PLATAFORMAS`. `integridade.ATS`:
  `"Teamtailor": ("teamtailor.com",)`.
- [X] T010 [US2] Testes:
  - `ler_feed`: campos, id, modelos, local e restrição, descrição em texto;
  - na busca: remota aberta ao Brasil e híbrida na cidade dentro; presencial em outra cidade e antiga fora;
  - uma leitura por busca para vários cargos;
  - EY por `ey.buscar`;
  - 429 por host sem nova tentativa, com as outras empresas seguindo;
  - 404 com o aviso.

## Phase 5: User Story 3 - A EY muda de lugar (P1)

- [X] T011 [US3] `fontes/ey.py`: a busca sem resultado não dá aviso; `ILEGIVEL` só com linha de vaga no HTML (research
  R4).
- [X] T012 [US3] Testes: migração (EY ligada, desligada, sem `fontes` com cargos, config novo, sem duplicar ao salvar),
  `fontes_da_busca` sem a EY e com `ats`, a EY fora de `fontes_nac`, e a página `ey-sem-resultado.html` sem aviso.

## Phase 6: User Story 4 - Página própria pela IA (P2)

- [X] T013 [US4] `fontes/pagina_empresa.py` (contracts/empresas.md):
  - `texto`, `pedido`, `limpar` e `lista`;
  - a memória em `.cache/empresas-paginas/`;
  - `MAX_IA` por busca, zerado por `_comum.AO_ESQUECER`;
  - os avisos de IA desligada, de limite e de nenhuma vaga.
- [X] T014 [US4] `fontes/ats.py`: página própria na área nacional. A remota sem lugar conta como aberta ao país
  (research D6); as presenciais e híbridas seguem a cidade.
- [X] T015 [US4] Testes, com `ia.responder` trocado:
  - uma vaga por bloco, com modelo e local;
  - o cargo inventado descartado;
  - o e-mail escrito vale, e o inventado não;
  - o trecho oculto fora do texto enviado;
  - a mesma marca sem IA, com as datas mantidas;
  - IA desligada dá aviso;
  - acima do limite, aviso;
  - nenhuma vaga dá aviso informativo.

## Phase 7: Polish

- [X] T016 [P] Documentação:
  - `README.md`, `dash/README.md`, `dash/API.md` (rota nova, sistemas, plataformas, EY fora dos portais);
  - `AGENTS.md` (lista de portais sem a EY; empresas em qualquer página);
  - `docs/novo-portal.md` (sistema novo de empresa acompanhada);
  - `.agents/skills/buscar-vagas/SKILL.md`, com `python sincronizar_skills.py`.
- [X] T017 [P] Front na `frontend-react`:
  - o botão Adicionar chama `POST /api/empresas/reconhecer` e mostra o rótulo e o aviso da IA;
  - a lista mostra o rótulo do sistema;
  - o texto de ajuda do painel;
  - as etiquetas "Teamtailor" e "Site da empresa", com o domínio `teamtailor.com`;
  - `npm run build` sem erro, commit local.
- [X] T018 Verificação e entrega:
  1. a suíte inteira;
  2. a busca por dados pessoais;
  3. o commit na branch da feature;
  4. o merge na branch pessoal, com a página copiada e o dashboard reiniciado;
  5. `graphify update .`.

  Master, push e PR do front só com o OK da pessoa depois do teste.

## Dependencies

- T001 → testes. T002 → T003 → T005, T008. T007 → T008. T013 → T014.
- US1 e US2 formam o MVP. US3 depende de T003. US4 depende de T008.
- `fontes/ats.py` muda em sequência: T002, T008 e T014.
