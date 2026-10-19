# Research: Contas conectadas

Pesquisa feita em 2026-10-18 com a pessoa logada na janela da ferramenta (`navegador.py`), com o OK dela. As respostas
reais ficaram só no computador dela, fora do repositório. As respostas com dados de conta (CPF, celular, perfil) foram
apagadas na hora. Aqui ficam só a estrutura e os valores de status.

## 1. Janela da ferramenta (DevTools Protocol com a biblioteca padrão)

- **Decision:** Edge (preferido) ou Chrome, com:
  - `--user-data-dir=.cache/navegador`;
  - `--remote-debugging-port=0`, com a porta lida de `DevToolsActivePort`;
  - `--no-first-run`, `--no-default-browser-check`, `--disable-sync`;
  - `--start-minimized` na leitura.

  A conversa é por WebSocket (cliente mínimo, RFC 6455) com `Runtime.evaluate`, `Page.navigate`,
  `Page.bringToFront` e `Browser.close`.
- **Rationale:**
  - funciona com o Edge aberto no dia a dia: outro perfil é outra instância;
  - a porta só aceita 127.0.0.1;
  - a primeira aba nasce em `about:blank`, então `abrir()` espera a URL real.
- **Alternatives considered:** Playwright/Selenium (dependência nova, proibida pela constituição III); headless
  (descartado pela pessoa: o Indeed e o LinkedIn detectam com mais facilidade).

## 2. Ler pela API que a própria página usa, não pela tela

- **Decision:** a leitura roda `fetch(..., {credentials: "include"})` de dentro da aba do portal (`Aba.avaliar`) e
  usa o JSON que a própria página de candidaturas pede.
- **Rationale:**
  - é mais estável que ler o HTML: os nomes de classe mudam, o JSON da página muda menos;
  - traz ids, datas completas e status codificados;
  - os cookies nunca saem do navegador; a ferramenta só recebe o JSON das candidaturas.
- **Alternatives considered:** ler `document.body.innerText` (frágil, datas sem ano, sem ids).

## 3. Gupy

- **Lista:** `GET https://private-api.gupy.io/selection-process/candidate/applications`, pedida de
  `portal.gupy.io`. Devolve `{"results": [...]}`, todas as candidaturas de uma vez, sem paginação. Cada item tem:
  - `applicationId`, `applicationStatus`, `jobName`, `jobType`, `workplaceType`, `jobStatus`, `isPwd`;
  - `jobStepCount`, `jobStepCurrent`, `addressCity`, `addressStateShortName`;
  - `careerPageName`, `careerPageSubdomain`, `careerPageUrlLogo`, `quickApply`.

  **Não traz o id da vaga.**
- **Detalhe:** `GET https://private-api.gupy.io/selection-process/candidate/application/<applicationId>/step`.
  - Só responde 200 quando pedido de `https://<careerPageSubdomain>.gupy.io/candidates/applications/<applicationId>`
    (a Gupy deduz a empresa pela origem). De `portal.gupy.io`, dá 400.
  - Traz `status`, `currentStepId`, `job.id` (o número do `gupy-N`), `job.status`, `job.jobSteps[]` com `id`,
    `name`, `order`, `type` e **`category`** (`registration`, `evaluation`, `screening`, `interview`, `hiring`).
  - Também traz `candidate` com só `id`, `currentProfileId` e `externalProfileTestDone`, que são ignorados.
- **Valores vistos:**
  - `applicationStatus`: `in_process`, `reproved`;
  - `jobStatus`: `published`, `closed`, `canceled`, `frozen`;
  - `jobType`: `vacancy_type_effective`, `vacancy_type_autonomous`, `vacancy_legal_entity`,
    `vacancy_type_talent_pool`.
- **Abas da tela:**
  - Em andamento = `in_process` + vaga `published` (ou `frozen`), fora de banco de talentos;
  - Em banco de talentos = `jobType` `vacancy_type_talent_pool`. É a **candidatura ao banco de talentos da empresa**,
    não uma reprovação. Isso corrige a premissa do plano;
  - Finalizadas = o resto.
- **Decision (detalhe só das ativas):** o detalhe é pedido só para as candidaturas em andamento (hoje poucas). Cada
  uma pede navegar à página da empresa. O par `applicationId → job.id` fica guardado em
  `.cache/contas/gupy.json`, e leituras seguintes não repetem. As finalizadas se resolvem com a lista e casam por
  cargo + empresa.
- **Sessão:** a Gupy **perde o login quando a janela fecha**. O "continuar de onde parou" do perfil não resolveu e
  foi desfeito.
  - **Decision (da pessoa, revista no teste de 2026-10-18):** a janela da ferramenta fica **aberta e minimizada
    enquanto o dashboard roda** e fecha no "Desconectar" ou quando o dashboard para. Assim a Gupy pede login uma vez
    por sessão do dashboard, não a cada leitura.
  - Quando pedir, a janela vem para a frente e a leitura espera a página **voltar logada à Gupy**
    (`gupy.logado`), até 3 minutos. O "Entrar com LinkedIn" passa pelo linkedin.com no meio: a primeira versão
    tratava isso como fim do login e interrompia o caminho.
  - A ferramenta não clica no botão de login (constituição VI: quem faz o login é a pessoa).
- **Tradução:**

  | Gupy | Etapa | Resultado | Anotação |
  |---|---|---|---|
  | `reproved` | encerrada | nao_aprovado | |
  | `in_process` + vaga `canceled` | encerrada | cancelada | |
  | `in_process` + vaga `closed` | encerrada | — | "vaga encerrada na Gupy sem resultado para você" |
  | banco de talentos | aplicada | — | "banco de talentos da empresa" |
  | em andamento, etapa atual `registration`/`evaluation`/`screening` | aplicada | — | "Gupy: etapa k de N (nome)" |
  | em andamento, etapa atual `interview` | entrevista | — | nome da etapa |
  | em andamento, etapa atual `hiring` | proposta | — | nome da etapa |
  | outro status | — (só informa) | | "status na Gupy: …" |

  Outros `applicationStatus` possíveis (ex.: contratado, desistência) entram quando aparecerem. Até lá, viram só
  informação.

## 4. Indeed

- **Lista:** `GET https://myjobs.indeed.com/api/v1/appStatusJobs?type=POST_APPLY&co=<país>`, pedida de
  `myjobs.indeed.com`. Devolve `{"success", "body": {"appStatusJobs": [...]}}`. Cada item tem:
  - **`jobKey`** (o `jk` que o dashboard já usa), `jobTitle`, `jobUrl`, `company.name`, `location`;
  - `applyTime` (ms), `jobExpired`, `withdrawn`, `applicationStatus` (`DELIVERY_SUCCESS` ou nulo);
  - `statuses` com os blocos:
    - `candidateStatus`: o que a empresa marcou (`APPLIED`, `REJECTED`);
    - `selfReportedStatus`: o que a pessoa marcou em "Atualizar status" (`APPLIED`, `REJECTED`, `NOT_INTERESTED`);
    - `employerJobStatus`: `OPEN` ou `CLOSED`;
    - `userJobStatus`: `POST_APPLY`.

    Cada bloco vem com `timestamp` em ms.
- **Outras chamadas:** `type=SAVED` (salvas, fora desta versão) e `/api/v1/interviews?...` (entrevistas agendadas pelo
  Indeed, vazia no teste). Uma entrevista agendada por ali também conta como `entrevista`.
- **Sessão:** persiste depois de fechar a janela (testado).
- **Proteção contra robôs:** login e páginas abriram normalmente na janela da ferramenta, sem página de verificação.
- **Tradução:** vale o status mais forte entre a empresa e a pessoa, nesta ordem: contratado > oferta > entrevista >
  recusa/sem interesse > aplicada.

  | Indeed | Etapa | Resultado |
  |---|---|---|
  | `REJECTED` (empresa ou pessoa) | encerrada | nao_aprovado |
  | `NOT_INTERESTED` | encerrada | desisti |
  | status com `INTERVIEW` ou entrevista agendada | entrevista | — |
  | status com `OFFER` | proposta | — |
  | `HIRED` | encerrada | contratado |
  | `APPLIED` | aplicada | — |
  | `withdrawn` verdadeiro | encerrada | desisti |

  - **Só informam:** `jobExpired` e `employerJobStatus` `CLOSED` ("Vaga fechada ou expirada no Indeed").
  - **Data da etapa:** o `timestamp` do status escolhido; para "aplicada", o `applyTime`.

## 5. LinkedIn (desativado)

- Não pesquisado com a pessoa logada, porque o portal fica desativado.
- O leitor parte do print (Rastreador de vagas: `linkedin.com/jobs-tracker/?stage=applied`, filtros, "Candidatou-se há
  1 sem", "Não aceita mais candidaturas"), lendo a tela, com testes em HTML fictício.
- Ao ativar, uma pesquisa como a desta seção procura a API da página.

## 6. Casamento com o banco (medido em 2026-10-18)

- **Gupy:** 1 das candidaturas casa pelo cargo + empresa; as demais foram feitas fora da ferramenta e entram como
  "novas".
- **Indeed:** 2 de 10 casam pelo `jk`.
- **Decision:**
  - novas **finalizadas** vêm **desmarcadas** por padrão, para não lotar o quadro com histórico;
  - novas **ativas** vêm marcadas;
  - o casamento por cargo + empresa olha o banco inteiro, não só as vagas recentes como na busca.

## 7. Dados de teste

As respostas fictícias em `tests/dados/contas/` reproduzem a estrutura dos JSON acima, com empresas, cargos e ids
inventados. Nenhum dado real da pessoa entra no repositório.
