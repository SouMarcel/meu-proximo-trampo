---
description: "Tarefas da spec 025 (front único)"
---

# Tasks: Front único

**Input**: `specs/025-front-unico/` (spec, plan, research, data-model, contracts/, quickstart)

**Tests**: a spec não pede testes automatizados novos para o front (research R3). Cada fase termina com os portões e o
roteiro do [quickstart](quickstart.md). Os testes Python só mudam na troca (US7).

## Caminhos

- `src/...`, `package.json`: na worktree da `frontend-react`
  (`scratchpad/wt-front`, branch `frontend-react`).
- Demais caminhos (`dash/`, `tests/`, `.github/`, docs): na worktree da spec (`scratchpad/wt-025`, branch
  `025-front-unico`, saída da `master`).
- Formatos de rotas e campos: sempre os do `dash/API.md`, nas seções citadas. Não inventar campo nem rota.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [x] T001 Criar a worktree da `frontend-react` em `scratchpad/wt-front` e instalar com
  `npx -y pnpm@10.34.3 install --frozen-lockfile` (feito no plano)
- [X] T002 Acrescentar o script `"typecheck": "tsc --noEmit"` em `package.json`
- [X] T003 Corrigir os 10 erros do `tsc`:
  - `src/App.tsx` (linhas 347, 364, 401);
  - `src/components/KanbanBoard.tsx` (109);
  - `src/components/modals/ConnectedAccountsModal.tsx` (311: `bg` e `text` → as chaves que existem no objeto);
  - `src/utils/formatters.ts` (271-282: importar `Vaga` e tipar `x`).
- [X] T004 [P] Em `.github/workflows/front.yml`, passo `pnpm exec tsc --noEmit` antes do `vite build`, com
  mensagem de erro clara na execução

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T005 Criar `src/types/api.ts` com os tipos do `dash/API.md`.
  - `Vaga` com todos os campos do §2, incluindo:
    - `id` "`^[A-Za-z0-9_.:-]{1,64}$`", `origem` `"busca"|"link"|"manual"`, `formato`, `nota_sem_descricao`;
    - `analise_status` `pendente|feita|sem_dados|sem_analise`;
    - `kit` `{estados: {item: "a_fazer"|"pronto"|"nao_se_aplica"}, extras: string[], removidos: string[]}`;
    - `lembretes` e os campos de análise `autorizacao`, `ingles`, `contratacao`, `fuso`, `riscos`, `pede`;
    - os calculados `checklist` e `lembretes_pendentes`.
  - `Versao` (§3.13) e `ErroApi` `{status, message, dados}`.
  - Os demais tipos listados em `data-model.md`, cada um acrescentado na fase que o usa.
- [X] T006 Reescrever `src/services/api.ts`:
  - manter `getApiBaseUrl()`;
  - função `pedir<T>(metodo, caminho, corpo?)`: escrita sempre com `Content-Type: application/json` e corpo `{}`
    quando vazio (também em DELETE); `cache: "no-store"`;
  - resposta não-ok vira `ErroApi` com `message` = `erro` do servidor;
  - falha de rede vira `ErroApi` com `status: 0` e "servidor fora do ar";
  - `urlArquivo(caminho)` = base + caminho, para os links `/arquivos/...`;
  - sai o objeto `ApiService`.
- [X] T007 [P] Criar `src/services/api/vagas.ts` (§3.1, §3.2): `versao()`, `listar()`, `ultimaBusca()`,
  `atualizar(id, campos)`, `remover(id)`, `analisar(id)`, `porLink(url)`, `extrair(texto, autor?, autor_tipo?)`,
  `criar(campos)`.
- [X] T008 [P] Criar `src/hooks/useConsulta.ts`: `useConsulta(fn, intervaloMs, ativo)`.
  - Não consulta com `document.hidden`; consulta de novo no `visibilitychange` ao voltar.
  - Para quando `ativo` vira `false`.
- [X] T009 [P] Criar `src/contexto/Ferramenta.tsx` (data-model "Contexto `Ferramenta`"):
  - campos `servidor` (`no_ar|fora|demo`), `podeAlterar`, `ia {disponivel, nome, modelo, cobranca}`, `perfilExiste`;
  - funções `registrarPodeAlterar(valor)`, `tratarErro(e)` (403 numa rota [local] → `podeAlterar = false`) e
    `exigirIA(abrirPainelIA)` (sem IA disponível, abre o painel IA e devolve `false`);
  - componente `<AvisoSoLeitura/>` com o motivo, para usar ao lado de botões desligados.
- [X] T010 [P] Criar `src/utils/filaVaga.ts`: `naFila(id, tarefa)`, que encadeia uma promessa por id para uma escrita
  por vez na mesma vaga.
- [X] T011 [P] Criar `src/components/TextoDaVaga.tsx` (research R8): markdown mínimo montado como elementos React.
  - Parágrafos, quebras, `**negrito**`, listas `-` e `*`.
  - Links só `http` e `https`, com `target="_blank" rel="noopener noreferrer"`.
  - Sem `dangerouslySetInnerHTML`.
- [X] T012 Em `src/utils/formatters.ts`, criar ou ajustar as funções do data-model "Estado derivado":
  - `situacaoNota(vaga, versao)`: `verificando` → `falha` → `analise_status`, mais o selo de nota provisória;
  - `areaDe(vaga)` (`area` ou dedução por `grupos`), `noQuadro(vaga)` e `noRelatorio(vaga)`;
  - `faixaNota(n)`: "≥80 forte, ≥65 boa, ≥50 parcial, abaixo baixa; sem número = sem nota".
- [X] T013 Reescrever o carregamento em `src/App.tsx`:
  - envolver a página no `FerramentaProvider`;
  - `useConsulta` de `versao()` a cada 4 s; quando `versao` muda ou o servidor volta, recarregar `listar()` e
    `ultimaBusca()`;
  - sem resposta na abertura → `demo` (dados do `mockData` e aviso fixo "Modo demonstração: dados de exemplo,
    servidor não encontrado");
  - queda depois de conectado → `fora` (faixa no topo e reconexão sozinha, sem trocar as vagas por exemplos);
  - todas as escritas de vaga por `naFila`, trocando a vaga local pela devolvida;
  - `vagasComStatus` deixa de reescrever `analise_status` e passa a usar `situacaoNota`.
- [X] T014 Trocar `Vaga` de `src/types/job.ts` pelo `Vaga` de `src/types/api.ts` em `KanbanBoard.tsx`,
  `TriageReport.tsx`, `JobCard.tsx`, `InternationalHub.tsx`, `FunnelAnalytics.tsx`, `modals/JobDetailModal.tsx` e
  `InterviewCoach.tsx` (em `src/components/`), corrigindo os campos que não existem. O `checklist` e as entrevistas
  ficam vazios até US4 e US5.
- [X] T015 Reescrever `src/services/mockData.ts` no formato de `src/types/api.ts`, com empresas e pessoas fictícias,
  usado só em `demo`. No `demo`, os botões que gravam ficam desligados com o aviso.
- [X] T016 Portões do quickstart (`tsc`, build, greps) e conferir em `/novo/` que quadro e Relatório continuam como
  antes, sem regressão

**Checkpoint**: base pronta; as histórias podem começar.

---

## Phase 3: User Story 1 - Trazer vagas para a página nova (P1) 🎯 MVP

**Goal**: buscar, completar descrições, tentar a nota de novo e adicionar vagas só pela página nova.

**Independent Test**: roteiro H1 do quickstart. Busca, vaga por link e vaga por texto aparecem também em `/`.

- [X] T017 [P] [US1] Criar `src/services/api/busca.ts` (§3.3): `plano()`,
  `iniciar({sem_nota?, confirmar_recente?, confirmar_espera?})`, `estado()`, `cancelar()`, `tentarNota()`,
  `pendentes()`, `completarPendentes()`.
- [X] T018 [US1] Reescrever `src/components/modals/SearchJobsModal.tsx` sobre `plano()`. Sai o `setTimeout`.
  - **Mostrar**: portais, cargos, `janela_horas`, `estimativa_min`, a IA (`nome`, `modelo`, "consome créditos"
    quando `cobranca == "uso"`), `aviso_cargos`, `aviso_pausa`, `espera` e `ultima`.
  - **Sem `filtros_ok` ou `perfil_ok`**: botões para Filtros e Meu perfil.
  - **Botão Buscar agora desligado**:
    - antes de `proxima_em`, mostrando o horário;
    - com `so_espera`;
    - com busca rodando.
  - **Com `recente` ou `espera`**: aviso e caixa de confirmação. O pedido repete com `confirmar_recente` e
    `confirmar_espera` só depois dela.
  - **409 com `precisa_confirmar`**: mostrar o `erro` e pedir a confirmação.
  - **Sem IA**: opção "buscar sem nota" (`sem_nota: true`).
  - **Só leitura**: respeitar `podeAlterar`.
- [X] T019 [US1] Criar `src/components/AndamentoBusca.tsx`, mostrado no topo do Relatório.
  - `useConsulta(estado, 2000)` enquanto `situacao` estiver em `consultando, descricoes, gravando, cancelando,
    externa` ou a análise rodar; para 20 s depois da última ação (§1).
  - **Mostrar**: `feitas/total`, `consulta {portal, cargo}`, `descricoes {lidas,total}`, `erros`, `mensagem` e, no
    fim, o `resumo` (brutas, novas, fora_criterios, ja_vistas, pendentes).
  - **Cancelar**: só com `origem == "pagina"` e `pode_alterar`.
  - **Com `situacao == "externa"`**: "busca rodando pelo terminal ou pelo chat".
  - **Com `analise.erro`**: botão "Tentar a nota de novo" (`tentarNota()`).
  - Também abre com o aviso `ia_erro` de `versao`.
- [X] T020 [P] [US1] Criar `src/components/UltimaBusca.tsx` (linha do topo do Relatório).
  - Mostrar data, termos, brutas, avaliadas, fora_criterios, fortes, boas, parciais e baixas, tolerando registro
    antigo sem campos.
  - Usar em `src/components/TriageReport.tsx`.
- [X] T021 [US1] Criar `src/components/CompletarDescricoes.tsx` no Relatório.
  - Botão com o número de `pendentes`, desligado com `espera` (mostrando até quando).
  - `completarPendentes()`; `useConsulta(pendentes, 2000)` enquanto `situacao == "lendo"`; no fim, recarregar as
    vagas e mostrar `completadas`, `restantes` e `erros`.
  - Tirar de `src/App.tsx` o `handleCompletarDescricao` simulado e a prop `onCompletarDescricao` de
    `modals/JobDetailModal.tsx`.
- [X] T022 [US1] Reescrever `src/components/modals/AddJobModal.tsx` (§3.2), sem `setTimeout`.
  - **Por link** (`porLink(url)`, URL até 1.000):
    - 201/200 → vaga gravada; avisar quando `nova: false`;
    - resposta com `post` → abrir o formulário com `parcial` e, se `ia.disponivel`, o botão "Preencher com IA";
    - 422 com `parcial` → formulário pré-preenchido com o `erro`;
    - 422 com `sugestao: "colar"` → caixa "colar texto";
    - 400 → mensagem.
  - **Colar texto**: "Preencher com IA" passa por `exigirIA`; `extrair()` só preenche o formulário; com
    `parece_vaga: false` ou `vagas > 1`, mostrar aviso; 409 → painel IA.
  - **Formulário**:
    - `titulo*` e `empresa*`;
    - `plataforma` da lista do §2;
    - `url` http/https; `local`; `descricao` "até 20.000";
    - `etapa` `"relatorio"` ou uma etapa (padrão `salva`);
    - `area` e `pais_vaga`;
    - `email_candidatura` e `assunto_candidatura`;
    - `formato`, `post_id` e `publicado_por` vindos do post.
  - **Adicionar**: `criar()`. Se a vaga voltar com `triagem: "fora"`, mostrar o `motivo_fora`.
- [X] T023 [US1] Ajustar `handleAddVaga` em `src/App.tsx` para receber a `Vaga` devolvida e acrescentar ou trocar
  pelo id.
- [X] T024 [US1] Em `src/components/TriageReport.tsx`, botão "Marcar todas como não seguidas" na sub-aba Para decidir.
  - Dois cliques: o segundo diz "Confirmar: marcar todas".
  - Uma vaga por vez via `naFila`, com `{triagem: "visitada", etapa: null, triada_em: hoje}`.
- [X] T025 [US1] Em `src/components/Header.tsx`:
  - tirar a prop `configIA` e mostrar a IA do contexto (nome e modelo; "sem IA" leva ao painel);
  - link "Apoie o projeto" com o mesmo endereço e texto do `dash/dashboard.html`;
  - Buscar vagas abre o `SearchJobsModal`.
- [X] T026 [US1] Em `src/components/modals/JobDetailModal.tsx`, a análise como o servidor manda:
  - descrição com `TextoDaVaga`;
  - análise com nota e faixa, "nota provisória" quando `nota_sem_descricao`, `resumo`, Encaixe, Lacunas, Atenção,
    `sinais`;
  - `autorizacao`, `ingles`, `contratacao`, `fuso` e `riscos` com a `frase` do anúncio;
  - `senioridade` com "sugerida" quando `senioridade_origem == "sugerida"`;
  - quem deu a nota (`analise_provedor` e `analise_modelo`).
- [X] T027 [US1] Em todo erro de API das telas desta fase, mostrar `ErroApi.message` (toast de erro) e passar por
  `tratarErro` (`src/App.tsx`, modais da fase)
- [X] T028 [US1] Portões do quickstart; build copiado para `dash/front/` na branch pessoal; roteiro H1 com a pessoa;
  marcar as linhas da História 1 em `contracts/paridade.md`. Com o OK: busca de dados pessoais, commit na
  `frontend-react` e o fluxo de entrega do quickstart.

**Checkpoint**: uso diário possível só pela página nova.

**Notas da implementação (H1, 2026-10-20)**:
- `UltimaBusca`, `CompletarDescricoes` e `AndamentoBusca` ficam no `App.tsx`, acima do `TriageReport`; o andamento
  também aparece na aba Internacional.
- Entraram também:
  - o botão de tema no cabeçalho (sistema → claro → escuro), que a lista de paridade dava como pronto e faltava;
  - "Voltar para triagem" em Não seguidas;
  - e-mail e assunto da candidatura no detalhe;
  - o título e o idioma da página (`.figma/make/site.json`).
- O detalhe da vaga deixou de chamar hooks antes do `return` (erro do React ao abrir) e lê a vaga direto da lista,
  então as mudanças aparecem na hora.
- No teste, a pessoa achou o perfil errado: era o perfil de exemplo do protótipo. Decisão dela: com o servidor no
  ar, as telas ainda não ligadas não mostram mais exemplo. Meu perfil, Filtros, IA, Contas e Entrevista mostram um
  aviso com o caminho para a mesma tela na página de sempre (`components/AindaNaPaginaAntiga.tsx`), e o exemplo
  fica só no modo demonstração. Cada história tira o aviso da sua tela.
- A sub-aba "Seguidas" do Relatório continua fora: o analista a tirou de propósito (commit `3a7bc44`); as vagas
  seguidas ficam no quadro.
- Conferido sem a pessoa:
  - `tsc` e build sem erros;
  - greps limpos (o `storage.ts` ainda usa o `mockData` no `JobStorageService`, que sai na H3);
  - 357 testes Python passando;
  - página montada aberta num navegador sem janela, com o servidor no ar (vagas, IA, última busca e pendentes
    reais) e com a API bloqueada (modo demonstração com os botões de gravar desligados).

---

## Phase 4: User Story 2 - Configurar a busca e a IA (P1)

**Goal**: filtros nacional e internacional e IA reais.

**Independent Test**: roteiro H2. As mudanças continuam depois de recarregar e aparecem em `/`.

- [X] T029 [P] [US2] Criar `src/services/api/config.ts` (`ler()` e `gravar(filtros)`, §3.4) e
  `src/services/api/ia.ts` (`estado()`, `salvar({provedor, modelo?, url_base?, chave?})`, `testar(...)` e
  `removerChave(provedor)`, §3.5), com os tipos `Config`, `Filtros`, `Opcoes`, `EstadoIA` e `Provedor` em
  `src/types/api.ts`
- [X] T030 [US2] Reescrever `src/components/modals/SearchFiltersModal.tsx` sobre `ler()`, com prop
  `modo: "nacional" | "internacional"`.
  - **Opções**: só as de `opcoes` (países, modelos, `tipos_emprego`, senioridades, moedas, `moeda_do_pais`, janelas
    "24","72","168","360","720", raios_km, idiomas, regiões, contratação, `fontes_nac` com `precisa`, `fontes_int`).
  - **Nacional**:
    - cargos (aspas = frase exata), localidade, modelos e senioridades;
    - tipos de emprego, `janela_horas`, `idiomas_aceitos`, `moedas_aceitas`, `empresas_excluir` e `fontes`.
  - **Internacional**:
    - `ativo`, `paises`, `termos`, `regioes`, `salario_min_anual_usd`, `fuso_horas`, `contratacao`;
    - `aceita_mudar`, `paises_mudanca`, `passaporte`, `autorizacao_trabalho`, `precisa_sponsor`, `fontes`;
    - `empresas` "`[{sistema, id, nome, url}]`", `frases_restricao` e `frases_positivas`.
  - **Salvar**: `gravar(filtros inteiro)`. Erro 400 mostra a regra do servidor ("informe pelo menos um cargo",
    "para híbrido ou presencial, informe a cidade"). Com `existe: false`, aviso de primeira vez.
- [X] T031 [US2] Reescrever `src/components/modals/AISettingsModal.tsx` sobre `estado()`. Sai o `setTimeout`.
  - **Provedores**: `provedores` do servidor, com nome, `cobranca`, `modelo_padrao`, `url_padrao`,
    `onde_obter_chave` (link http/https) e `dica`. Mostrar `claude_instalado` e `ultimo_erro`.
  - **Chave**: campo `type="password"` sempre vazio na abertura, mostrando "cadastrada, final XXXX" (`final`) e a
    `origem`. A chave nunca é guardada no estado global nem no navegador.
  - **Campos e ações**:
    - `url_base` obrigatória no provedor `compativel`;
    - Testar conexão → `{ok, mensagem}`, sem gravar;
    - Salvar;
    - Remover a chave com o `aviso` quando ela vem das variáveis do sistema.
  - **Antes de salvar**: o texto "o que é enviado ao provedor".
  - **Só leitura**: `pode_alterar` desliga tudo.
  - **Depois de salvar**: atualizar a `ia` do contexto.
- [X] T032 [US2] Em `src/App.tsx`, tirar os estados `filtros` e `configIA` simulados e os `handleSaveFilters` e
  `handleSaveConfigIA`. Em `src/components/InternationalHub.tsx`, "Filtros da busca internacional" abre o modal com
  `modo="internacional"`. Tirar `FiltrosBusca` e `ConfigIA` de `src/types/job.ts`.
**Notas da implementação (H2, 2026-10-20)**: `FiltrosBusca` fica em `types/job.ts` só para os primeiros passos de
exemplo (modo demonstração) e sai na H3. Gravar os filtros vale de outro aparelho (`PUT /api/config` não é só
local); a IA, não.

- [ ] T033 [US2] Portões, roteiro H2, linhas da História 2 em `contracts/paridade.md` e entrega com o OK

---

## Phase 5: User Story 3 - Perfil e análises do perfil (P2)

**Goal**: primeiros passos, "Já tenho currículo", "Seu currículo" e análises reais; some o perfil inventado.

**Independent Test**: roteiro H3. O `perfil.md` é gravado só depois de "Ver o que muda".

- [ ] T034 [P] [US3] Criar `src/services/api/perfil.ts` (todas as rotas do §3.6) e `src/services/api/analises.ts`
  (§3.7), com os tipos `EstadoPerfil`, `Material`, `Rascunho`, `Pergunta`, `Previa`, `FiltrosPropostos`,
  `CurriculosDaPasta`, `PropostaDoCurriculo`, `Analises`, `ItemLacuna`, `Prontidao`, `ItemPlano` e `Cargo` em
  `src/types/api.ts`
- [ ] T035 [US3] Reescrever `src/components/modals/CandidateOnboardingModal.tsx` como passos guiados pela `etapa` do
  servidor (`ia, materiais, rascunho, conflitos, anamnese, diagnostico, revisao, filtros, concluido`). Cada troca de
  passo grava com `PUT /api/perfil/progresso`.
  - **Materiais**: arquivo PDF, DOCX ou ZIP "até 10 MB" em base64 (aviso antes de enviar se passar), ou texto
    colado; remover material; avisos e trecho de cada um.
  - **Rascunho**: com IA (`exigirIA`, aviso de custo e "até minutos") ou "Montar sem IA".
  - **Conflitos**: escolher uma das `opcoes` com a fonte.
  - **Anamnese**: tipos `texto|lista|multi|opcoes|sim_nao`, respeitando `condicao`, mais contato e
    `contatos_achados`.
  - **Diagnóstico**: `previa()` com `falta|fraco|info` e o `ir` para a pergunta.
  - **Revisão**: markdown editável; com perfil existente, "Ver o que muda" antes de "Confirmar e gravar"
    (`PUT /api/perfil`).
  - **Filtros**: `mudancas` propostas, "Sugerir os cargos em inglês com a IA", "Confirmar e gravar nos filtros"
    (`PUT /api/config`) ou "Pular (manter os atuais)".
  - **Recomeçar**: pede confirmação antes do `DELETE` do progresso.
  - Apagar `src/services/onboardingData.ts`.
- [ ] T036 [US3] Reescrever `src/components/modals/ProfileModal.tsx`.
  - **Resumo**: `existe_perfil` e `perfil_do_curriculo`; "Atualizar o perfil" abre os primeiros passos.
  - **Já tenho currículo**:
    - `GET /api/perfil/curriculos`;
    - proposta pelo `do-curriculo` (não grava);
    - "Usar este currículo" com `manter_perfil` e `marcar_base`.
  - **Seu currículo** (pt e en): marcar e trocar com `PUT /api/curriculo-base`; link
    `/arquivos/curriculo-base/{pt|en}`.
  - **Sair**: exportar, importar, "restaurar padrões", `JobStorageService` (de `src/services/storage.ts`) e o tipo
    `PerfilUsuario`.
- [ ] T037 [US3] Criar `src/components/analises/Analises.tsx` sobre `GET /api/analises-perfil` (aba "Análises" do
  `ProfileModal`).
  - **Lacunas**: visão `todas|seguidas`, com termos, exemplo e peso.
  - **Prontidão internacional**.
  - **Cargos-alvo** (IA, com aviso de custo): itens `lateral|degrau|vizinho` com `evidencia`, `lacuna` e
    `conferir`. "Levar os marcados para os filtros" mostra `mudancas` antes de `confirmar: true`.
  - **Plano de estudo** (IA, com aviso de custo).
  - **Marca** "Meu LinkedIn tem a versão em inglês" (`PUT marcas`).
- [ ] T038 [US3] Em `src/components/InternationalHub.tsx`, painel de prontidão com os dados de
  `GET /api/analises-perfil`, mais o botão "Abrir o painel internacional" para a aba Análises
- [ ] T039 [US3] Em `src/App.tsx`, abrir os primeiros passos uma vez por sessão quando `existe_perfil` for falso.
  A marca da sessão vai em `sessionStorage` com `try/catch`. Tirar `perfil`/`MOCK_PERFIL` e `handleSavePerfil`.
- [ ] T040 [US3] Portões, roteiro H3, linhas da História 3 em `contracts/paridade.md` e entrega com o OK

---

## Phase 6: User Story 4 - Currículo e kit da candidatura (P2)

**Goal**: currículo (vaga e base), checklist, carta, respostas e lembretes na página nova.

**Independent Test**: roteiro H4. Os arquivos abrem, e a pergunta de salário volta sem resposta da IA.

- [ ] T041 [P] [US4] Criar `src/services/api/curriculo.ts` (§3.8: `catalogo(vagaId?)`, `gerar({vaga_id, tecnicas})`,
  `tentar()`, `estado()`, `lista({vaga}|{base: true})`) e `src/services/api/kit.ts` (§3.9: `lista(vagaId)`,
  `carta(...)`, `respostas(...)`, `salvarRespostas(nome, pessoa)`), com os tipos `Catalogo`, `EstadoGeracao`,
  `MetaCurriculo`, `DocumentoCarta` e `DocumentoRespostas`
- [ ] T042 [US4] Criar `src/components/curriculo/AndamentoGeracao.tsx`, montado no `App`, porque é uma geração por
  vez para currículo, carta e respostas.
  - `useConsulta(estado, 2000)` enquanto `situacao` estiver em `escrevendo, gerando, conferindo`.
  - Mostra `etapa_texto` e o alvo.
  - Em `falha`, mostra "Tentar de novo" (`tentar()`) quando `pode_tentar`.
  - Ao ficar `pronto`, avisa as telas abertas para recarregar a lista.
- [ ] T043 [US4] Criar `src/components/curriculo/GerarCurriculo.tsx` sobre `catalogo(vagaId)`.
  - **Técnicas**: `ats, foco, xyz, resultado_primeiro, competencias_primeiro`, com a explicação de cada uma.
  - **Escolhas**: `paginas` 1|2, `formato` br|us|eu e `estilo` padrao|compacto|executivo, com a `sugestao` e o
    `motivo`.
  - **Antes de gerar**: qual IA vai rodar e o aviso de custo; sem perfil (`perfil_ok`), leva a Meu perfil.
  - **Gerar**: `gerar()`; 409 mostra que há outra geração rodando.
- [ ] T044 [US4] Criar `src/components/curriculo/ListaCurriculos.tsx` (`lista`, mais recentes primeiro).
  - Links de PDF e DOCX por `urlArquivo("/arquivos/curriculos/" + nome)`.
  - Conferência: `veredito`, `fatos`, `ats`, `requisitos` e `cobertura`.
  - `paginas`, `acima_do_limite` e `sugestoes_corte`.
- [ ] T045 [US4] Criar `src/components/kit/Checklist.tsx` a partir de `vaga.checklist`
  (`{item, rotulo, origem, estado, frase, acao, extra?, base?, falta_base?}`).
  - **Estado**: alternar `a_fazer|pronto|nao_se_aplica`, gravando `{kit}`.
  - **Itens**: acrescentar ("até 10 extras") e remover.
  - **Ação de cada item**:
    - `curriculo` → `GerarCurriculo`;
    - `carta` e `respostas` → as abas do kit;
    - `candidatar` → só abre `url_candidatura` ou `url`.
  - **Currículo da pessoa**: link do `base`; aviso de `falta_base`.
- [ ] T046 [US4] Criar `src/components/kit/Carta.tsx`.
  - **Campos**: `formato` carta|mensagem, `tom` direto|caloroso|formal, `por_que*`.
  - **Só na carta**: `problema` e `primeiro_movimento`, obrigatórios.
  - **Só na mensagem**: `limite` "20-3000, padrão 400".
  - **Idioma**: pt, en, es, fr, de ou it.
  - **Gerar**: passa por `exigirIA`, com aviso de custo.
  - **Lista**: cartas e mensagens da vaga, com conferência, Copiar e o link do arquivo.
- [ ] T047 [US4] Criar `src/components/kit/Respostas.tsx`.
  - Perguntas "uma por linha, até 30" → `respostas()`, com aviso de custo.
  - Itens com `sensivel` aparecem sem resposta da IA, com o aviso de que são da pessoa e um campo "Escrever a minha".
  - `salvarRespostas(nome, {"<nº da pergunta, de 1>": texto})`.
  - Copiar tudo.
- [ ] T048 [US4] Criar `src/components/kit/Lembrete.tsx` para `vaga.lembretes_pendentes` (no máximo um).
  - Feito, Dispensar e Parar lembretes gravam `{lembretes}` (§2).
  - O texto lembra: "a mensagem é você quem escreve e envia".
  - Usar em `src/components/JobCard.tsx` e no detalhe.
- [ ] T049 [US4] Em `src/components/modals/JobDetailModal.tsx`:
  - a aba `kit` com `Checklist`, `Carta` e `Respostas`;
  - a seção "Currículos para esta vaga", com `GerarCurriculo` e `ListaCurriculos`;
  - "Candidatar no {plataforma}" só abre o portal;
  - "Enviar por e-mail" abre `mailto:` com o assunto;
  - tirar o checklist simulado.
- [ ] T050 [US4] Em `src/components/modals/ProfileModal.tsx`, a seção "Currículo base", com `GerarCurriculo` sem
  vaga e `ListaCurriculos` com `base: true`
- [ ] T051 [US4] Portões, roteiro H4, linhas da História 4 em `contracts/paridade.md` e entrega com o OK

---

## Phase 7: User Story 5 - Preparar entrevista (P3)

**Goal**: a tela de entrevista só com dados reais.

**Independent Test**: roteiro H5. A história e a anotação aparecem também em `/`.

- [ ] T052 [P] [US5] Criar `src/services/api/entrevista.ts` (§3.10: `ler(vid)`, `salvarEmpresa`, `resumir`,
  `maisPerguntas`, `sugerirHistorias`, `salvarHistoria`, `removerHistoria`, `simular`, `salvarRodada`), com os tipos
  `Entrevista`, `Historia`, `PerguntaProvavel`, `Rodada` e `RetornoSimulacao`
- [ ] T053 [US5] Reescrever `src/components/InterviewCoach.tsx` com seletor de vaga e as abas:
  - **Dossiê**: campos do `dossie`; texto da empresa colado "até 20.000" com Salvar o texto; Resumo com IA (aviso de
    custo), com `origem` e `trecho` de cada ponto.
  - **Perguntas**: tipo, porquê, `texto_en`; Mais perguntas com IA.
  - **Histórias**: editar e salvar; sugerir com IA (rascunhos marcados "não salvos" até "Salvar esta história");
    Remover com dois cliques.
  - **Simular**: idioma pt ou en, pergunta, resposta e retorno (null sem IA), mais `treinar`.
  - **Salário**: `faixa`, `moeda`, `pretensao` e `pontos`, só o que o servidor manda, sem valor inventado.
  - **Depois**: formulário da rodada e as anteriores.

  Tirar as dicas fixas.
- [ ] T054 [US5] Em `src/App.tsx`, "Preparar entrevista" do cartão em Entrevista (`JobCard.tsx`) e do detalhe abre
  a aba de entrevistas com a vaga escolhida. Tirar `perguntas_frequentes` e `historias_star` de todo `src/`.
- [ ] T055 [US5] Portões, roteiro H5, linhas da História 5 em `contracts/paridade.md` e entrega com o OK

---

## Phase 8: User Story 6 - Contas conectadas (P3)

**Goal**: atualizar candidaturas pela Gupy e pelo Indeed, só leitura e só o que foi marcado.

**Independent Test**: roteiro H6. Só os itens marcados mudam no quadro.

- [ ] T056 [P] [US6] Criar `src/services/api/contas.ts` (§3.11: `contas()`, `estado()`, `conectar(portal)`,
  `pronto(portal)`, `desconectar(portal)`, `ler()`, `aplicar({chaves}|{historico: true})`), com os tipos `Contas`,
  `Portal`, `EstadoCandidaturas` e `ItemCandidatura`
- [ ] T057 [US6] Reescrever `src/components/modals/ConnectedAccountsModal.tsx`.
  - **Portais**: os de `contas()`, só Gupy e Indeed. O ícone vira `<img src="data:image/svg+xml,...">`.
  - **Sem navegador**: aviso com `navegador: false`.
  - **Conexão**: Conectar abre a janela da ferramenta, Pronto (com `conectado: false` mostra "login ainda não
    concluído"), Desconectar.
  - **Leitura**: Atualizar agora e Ler de novo; `useConsulta` a 1,5 s, só com o diálogo aberto e `situacao` em
    `lendo|aguardando_login`.
  - **Resultado**:
    - itens `mudar|quadro|nova|historico` com de/para, status do portal e avisos;
    - caixas marcadas conforme `marcado`, `sem_mudanca` e `erros` por plataforma;
    - "Aplicar N mudanças" só com os marcados;
    - "Importar como histórico".
  - **Erros 409**: a mensagem aparece, sem nova tentativa sozinha.
  - **A página**: nenhum campo de senha.
- [ ] T058 [US6] Em `src/App.tsx`, tirar `portais`, `itensSync` e `historicoSync` simulados e os handlers de
  conectar, pronto, sincronizar e aplicar. Tirar `PortalConectado`, `ItemSincronizacao` e `HistoricoCandidatura` de
  `src/types/job.ts`.
- [ ] T059 [US6] Portões, roteiro H6, linhas da História 6 em `contracts/paridade.md` e entrega com o OK

---

## Phase 9: User Story 7 - A troca: uma página só (P3)

**Goal**: a página nova em `/`; sai o `dashboard.html`.

**Independent Test**: roteiro H7. `iniciar.py`, o atalho, `/`, `/novo/` e `/novo/assets/...` levam à página nova, e
os testes passam.

**Pré-condição**: `contracts/paridade.md` todo marcado e uma semana de uso só na página nova (SC-005), com o OK da
pessoa para a troca.

- [ ] T060 [US7] Em `dash/servidor.py`, conforme `contracts/servidor-troca.md`:
  - `/` e `/index.html` entregam `dash/front/index.html`;
  - os arquivos do front saem da raiz, com a mesma checagem de pasta e de `TIPOS_FRONT`;
  - `/novo`, `/novo/` e `/novo/<arquivo>` respondem 308 para o equivalente na raiz;
  - sem build, aviso em HTML;
  - tirar `PAGINA` e atualizar o docstring do topo e o texto de `SEM_FRONT`.
- [ ] T061 [US7] Atualizar `tests/test_front_estatico.py` conforme a seção "Testes" de `contracts/servidor-troca.md`
  (sai `test_dashboard_atual_continua_em_raiz`)
- [ ] T062 [P] [US7] Apagar `dash/dashboard.html`
- [ ] T063 [P] [US7] Atualizar a documentação:
  - `README.md` (linhas sobre o Live Server e o `dash/dashboard.html`);
  - `dash/README.md` (Live Server e a linha `dashboard.html` da tabela);
  - `dash/API.md` (§1 Endereço com a regra do `getApiBaseUrl`; "O front atual" passa a citar `src/services/api.ts`;
    §3.12 com as rotas novas de página);
  - `AGENTS.md` (o item do front novo em `/novo/` passa a dizer que a página da ferramenta é o front em `/`).
- [ ] T064 [P] [US7] Atualizar `.agents/skills/buscar-vagas/SKILL.md` (linha 38, `dashboard.html`) e rodar
  `python sincronizar_skills.py`, depois `python sincronizar_skills.py --conferir`
- [ ] T065 [P] [US7] Atualizar `.vscode/settings.json` (Live Server em `dash/front/index.html`) e o texto do PR em
  `.github/workflows/front.yml` (testar em `/`)
- [ ] T066 [US7] Rodar `python -m unittest discover -s tests`; roteiro H7 na branch pessoal; busca de dados pessoais;
  com o OK, merge na `master`, push e `git merge master` na branch pessoal

---

## Phase 10: Polish

- [ ] T067 Apagar `src/types/job.ts` e o que sobrar de `ApiService`, `JobStorageService`, `MOCK_*` fora do modo
  demonstração. O `grep` do quickstart fica limpo.
- [ ] T068 [P] Conferir `src/components/FunnelAnalytics.tsx` e `src/components/InternationalHub.tsx`: nenhum número ou
  texto fixo de exemplo, só valores calculados das vagas e das análises (FR-016)
- [ ] T069 [P] Conferir as telas novas na largura de notebook e de celular e nos temas claro e escuro (FR-006)
- [ ] T070 [P] Conferir o tamanho do JS montado (meta: abaixo de 700 kB) e que a página não faz nenhum pedido para
  fora de `127.0.0.1` (aba Rede do navegador)
- [ ] T071 Marcar a spec como Concluída em `specs/025-front-unico/spec.md`, rodar `graphify update .` e atualizar a
  memória do projeto

---

## Dependencies & Execution Order

- **Setup (T002–T004)** → **Foundational (T005–T016)** → histórias.
- **US1 e US2 (P1)**:
  - não dependem uma da outra, mas US1 vem primeiro (MVP);
  - o link "Filtros" do diálogo de busca (T018) só abre o modal antigo até a US2.
- **US3** depende da US2 no passo de filtros propostos (`PUT /api/config` e o tipo `Filtros`).
- **US4**:
  - não depende da US3;
  - a seção "Currículo base" (T050) mexe no `ProfileModal`, então vem depois de T036.
- **US5** e **US6** não dependem das outras histórias.
- **US7** depende de todas (paridade completa).
- **Polish** acompanha o fim; T067 só depois da US6.

Dentro de cada história: primeiro o arquivo `services/api/*.ts` [P], depois as telas, depois a fiação no `App.tsx`,
por último portões e roteiro.

## Parallel Example

```text
# Foundational, arquivos independentes:
T007 services/api/vagas.ts · T008 hooks/useConsulta.ts · T009 contexto/Ferramenta.tsx
T010 utils/filaVaga.ts · T011 components/TextoDaVaga.tsx

# US1: T017 (busca.ts) e T020 (UltimaBusca.tsx) juntos; T018, T019 e T021 depois de T017.
# US4: T041 primeiro; T045–T048 (kit/*) em paralelo com T043–T044 (curriculo/*).
# US7: T062–T065 em paralelo depois de T060.
```

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1, testados e entregues com o OK. A pessoa já busca e adiciona vagas só pela
   página nova.
2. **Incremental**: US2 → US3 → US4 → US5 → US6, cada uma com teste na branch pessoal, linhas marcadas na paridade e
   entrega pela Action.
3. **Troca**: US7 só com a paridade completa, uma semana de uso e o OK da pessoa.
