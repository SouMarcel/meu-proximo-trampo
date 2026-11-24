# Feature Specification: Nerdin no "Atualizar candidaturas"

**Feature Branch**: `059-nerdin-candidaturas` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "No site da Nerdin as candidaturas podem ser atualizadas; verificar a página
vagas_candidato.php?id=<id do candidato> e adicionar ao Atualizar candidaturas. Assim como na Gupy, o usuário faz a
autenticação."

## Contexto

O botão "Atualizar candidaturas" (spec 018) lê o andamento das candidaturas na área logada da Gupy e do Indeed, numa
janela do navegador só da ferramenta, com o login feito pela pessoa, e mostra uma proposta que ela confirma antes de
gravar. A Nerdin também mostra, na área do candidato (`vagas_candidato.php`), as vagas em que a pessoa se candidatou
pela Nerdin e a situação de cada uma. Hoje essas vagas ficam paradas no quadro: a busca da Nerdin (spec 020) traz a
vaga, a pessoa se candidata no site, e o quadro só muda se ela mover o cartão à mão.

Diferente da Gupy e do Indeed, a página da Nerdin é montada no servidor, sem uma API de candidaturas: a leitura é do
conteúdo que a própria página mostra na janela (os links das vagas e a situação escrita ao lado de cada uma).

A constituição (princípio VI) libera a conta conectada portal por portal, em spec própria e com análise de risco, e a
Nerdin já está na regra de "Termos contrários". Esta spec registra a decisão da pessoa e a emenda que acrescenta a
Nerdin aos portais liberados.

## Clarifications

### Session 2026-11-24

- Q: Quem faz o login na Nerdin? → A: A pessoa, na janela da ferramenta, como na Gupy. A ferramenta nunca pede, lê
  nem digita a senha da Nerdin.
- Q: A Nerdin tem termos contrários a automação; seguir mesmo assim? → A: Sim, por decisão do usuário (2026-11-24),
  só na conta conectada: leitura da página de candidaturas, só no clique, só leitura, com os termos à vista no painel.
  A busca pública da Nerdin continua como estava.
- Q: Como a ferramenta lê sem API? → A: Pelo conteúdo da página aberta na janela (links `vaga.php`/`vaga_emprego` com
  o número da vaga e o texto da situação), sem clicar em nada.
- Q: Como é a página "Minhas candidaturas" (print enviado pelo usuário em 2026-11-24)? → A: Um cartão por candidatura
  com cargo, empresa, local, etiquetas, "Inscrito em: DD/MM/AAAA", um selo "Aberta" ou "Expirada" e a trilha
  "Acompanhe sua candidatura" com cinco passos: Inscrito, Currículo recebido, Perfil visualizado, e os dois últimos
  "Em análise" e "Processo aberto" (em andamento) ou "Não selecionado" e "Processo encerrado" (recusada). Cada passo
  aparece feito, atual ou ainda não alcançado. Os botões do cartão são "Ver Detalhes" e "Cancelar candidatura". Não
  há passo de entrevista nem de proposta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conectar a Nerdin (Priority: P1)

A pessoa clica em "Atualizar candidaturas". O painel lista Gupy, Indeed e Nerdin, cada um com o ícone, e na Nerdin
mostra o aviso dos termos. Ela clica em "Conectar" na Nerdin. A janela da ferramenta abre na página de login da
Nerdin; ela entra na conta e clica em "Pronto". O painel mostra "Nerdin · Conectado".

**Why this priority**: sem conexão não há leitura.

**Independent Test**: com o navegador simulado, clicar em Conectar e conferir que a janela abre na página de
candidaturas da Nerdin (que leva ao login sem sessão), e que o estado vira "Conectado" quando a página responde
logada. Desconectar e conferir que a sessão da Nerdin foi apagada.

**Acceptance Scenarios**:

1. **Given** o painel aberto, **When** a pessoa olha a Nerdin, **Then** ela aparece com o ícone, "Conectar" e o aviso
   de que os termos da Nerdin não permitem acesso automatizado e que a leitura é só da página de candidaturas, no
   clique.
2. **Given** a pessoa clicou em "Conectar" na Nerdin, **When** a janela abre, **Then** ela está na página de login da
   Nerdin, e a tela diz "Faça o login na janela que abriu e clique em Pronto".
3. **Given** o login feito, **When** a pessoa clica em "Pronto", **Then** a ferramenta confere a página de
   candidaturas e mostra "Conectado"; se a Nerdin ainda pede login, diz que o login não foi concluído.
4. **Given** a Nerdin conectada, **When** a pessoa clica em "Desconectar", **Then** a sessão da Nerdin é apagada e a
   próxima leitura pede login de novo; a Gupy e o Indeed continuam conectados.

---

### User Story 2 - Candidaturas da Nerdin na proposta (Priority: P1)

Com a Nerdin conectada, a pessoa clica em "Atualizar agora". A ferramenta abre a página de candidaturas da Nerdin na
janela, lê as vagas e a situação de cada uma e junta à proposta de sempre, no grupo "Nerdin": mudanças de etapa, vagas
do Relatório que vão ao quadro e candidaturas que não estão no dashboard. Nada é gravado até "Aplicar marcadas".

**Why this priority**: é o valor pedido.

**Independent Test**: com uma página fictícia da Nerdin (HTML salvo nos testes) e um banco temporário, rodar a
leitura e conferir a proposta; aplicar só parte e conferir que o resto não mudou.

**Acceptance Scenarios**:

1. **Given** uma vaga da Nerdin no Relatório (sem etapa) que aparece na página de candidaturas, **When** a proposta
   aparece, **Then** ela sugere levar a vaga ao quadro na etapa correspondente à situação.
2. **Given** uma vaga da Nerdin no quadro em "Aplicação Enviada" que a Nerdin mostra como não selecionada, **When** a
   proposta aparece, **Then** ela sugere "Encerrada · não aprovado".
3. **Given** uma candidatura da Nerdin que não está no dashboard, **When** a proposta aparece, **Then** ela sugere
   adicionar a vaga com cargo, empresa, link da vaga na Nerdin e a etapa.
4. **Given** a mesma vaga no dashboard com o link em outro formato (`vaga_emprego/...-NNNNN.php` ou
   `vaga.php?id=NNNNN`), **When** a proposta aparece, **Then** a ferramenta reconhece pelo número e não sugere
   adicionar de novo.
5. **Given** a Nerdin com erro, bloqueio ou pedido de login, **When** a leitura roda, **Then** só a Nerdin fica de
   fora, com o motivo; a Gupy e o Indeed seguem.
6. **Given** a página de candidaturas com mais de uma página de resultados, **When** a leitura roda, **Then** a
   ferramenta segue as páginas seguintes pelo endereço, com pausa entre elas e no máximo um número fixo de páginas.

---

### User Story 3 - Situação da Nerdin traduzida para o quadro (Priority: P1)

A Nerdin escreve a situação de cada candidatura com as palavras dela. A ferramenta traduz para as etapas do quadro, e
o que não reconhece vira só informação.

**Why this priority**: sem a tradução certa, a proposta erra.

**Independent Test**: com páginas fictícias que tenham cada situação conhecida e uma desconhecida, conferir a etapa
proposta de cada uma.

**Acceptance Scenarios**:

1. **Given** um cartão com a trilha em andamento ("Em análise", "Processo aberto"), **Then** a etapa é "Aplicação
   Enviada", com a data de "Inscrito em", e o status mostra o último passo alcançado (ex.: "Nerdin: Currículo
   recebido" ou "Nerdin: Perfil visualizado").
2. **Given** um cartão com "Não selecionado" na trilha, **Then** a etapa é "Encerrada · não aprovado".
3. **Given** um cartão com o selo "Expirada" e a trilha ainda em andamento, **Then** a etapa não muda; aparece o aviso
   "vaga expirada na Nerdin" e a candidatura não conta como ativa.
4. **Given** um cartão com "Processo encerrado" sem "Não selecionado", **Then** a etapa não muda; aparece o aviso
   "processo encerrado na Nerdin", para a pessoa decidir.
5. **Given** um passo ou selo que a ferramenta não conhece, **Then** a proposta não muda a etapa e mostra "status na
   Nerdin: [texto]".
6. **Given** uma vaga do quadro numa etapa mais avançada que a da Nerdin (ex.: a pessoa marcou "Entrevista"), ou já
   "Encerrada", **Then** a proposta não sugere voltar a etapa (regra da spec 018). A Nerdin nunca propõe "Entrevista"
   nem "Proposta", porque a trilha não tem esses passos.

---

### Edge Cases

- A Nerdin pede login no meio da leitura: a janela vem para a frente e espera a pessoa por pouco tempo, como na Gupy;
  sem login, a Nerdin fica de fora dessa leitura com o motivo "a Nerdin pediu login".
- Captcha, tela de verificação ou resposta de bloqueio: a leitura da Nerdin para no primeiro sinal, sem nova
  tentativa; a pessoa resolve na janela se quiser.
- A página não traz nenhum link de vaga reconhecível (layout mudou): a Nerdin fica de fora com "não consegui ler as
  candidaturas da Nerdin", em vez de propor "nenhuma candidatura".
- A página de candidaturas pede o número do candidato no endereço: a ferramenta pega o link "Minhas candidaturas" do
  menu da própria área logada (lendo o endereço, sem clicar) e o guarda no computador; se não achar, a Nerdin fica de
  fora com a explicação de como informar o link uma vez no `.env` (`NERDIN_CANDIDATURAS`).
- Candidatura de vaga cuja inscrição foi feita fora da Nerdin (link externo para o site da empresa): não aparece na
  página da Nerdin e não é inventada.
- Texto da página é dado, não instrução: título, empresa e situação passam pelo mesmo limite de tamanho das outras
  contas e não executam nada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O painel "Atualizar candidaturas" MUST listar a Nerdin junto da Gupy e do Indeed, com ícone genérico
  (sem logo da marca), estado (Conectar/Conectado) e um aviso curto sobre os termos.
- **FR-002**: O login na Nerdin MUST ser feito pela pessoa na janela da ferramenta; a ferramenta MUST NOT pedir, ler,
  guardar ou digitar a senha, nem copiar cookies para fora do navegador.
- **FR-003**: A leitura MUST acontecer só no clique de "Atualizar agora" (ou "Pronto", para conferir o login), nunca
  agendada, e nunca pelo terminal ou pelo chat.
- **FR-004**: A leitura MUST ser só de leitura: abrir a página de candidaturas (e as páginas seguintes dela, pelo
  endereço) e ler o conteúdo; MUST NOT clicar em botões (em especial "Cancelar candidatura" e "Ver Detalhes"),
  enviar formulários, desistir de candidaturas nem abrir páginas de dados da conta.
- **FR-005**: Cada candidatura lida MUST trazer o número da vaga na Nerdin, cargo, empresa, link da vaga, o texto da
  situação, a etapa traduzida (FR-007) e a data quando a página mostrar.
- **FR-006**: O cruzamento com o dashboard MUST ser pelo número da vaga na Nerdin, valendo os dois formatos de link
  (`vaga.php?id=` e `vaga_emprego/...-NNNNN.php`), lido do endereço dos links do cartão sem clicar. Se o cartão não
  trouxer o número, o cruzamento MUST ser por cargo e empresa entre as vagas da Nerdin do dashboard, só quando houver
  uma única correspondente. Sem número e sem correspondente, a candidatura não é proposta como nova (sem o número
  não há como abrir a vaga) e conta só como lida.
- **FR-007**: A tradução da situação MUST seguir a US3: termos conhecidos viram etapa; termos desconhecidos não mudam a
  etapa e aparecem como "status na Nerdin: [texto]"; nunca voltar etapa nem mexer em vaga encerrada.
- **FR-008**: A proposta da Nerdin MUST entrar no mesmo fluxo de confirmação da spec 018 (caixas de marcar, "Aplicar
  marcadas", anotação "Etapa atualizada pela Nerdin em AAAA-MM-DD: [status]").
- **FR-009**: Erro, bloqueio, captcha ou login caído na Nerdin MUST deixar só a Nerdin de fora daquela leitura, com o
  motivo; a página sem nenhuma candidatura reconhecível MUST ser tratada como erro de leitura, não como lista vazia.
- **FR-010**: Páginas seguintes da lista MUST ter pausa entre pedidos (a pausa da Nerdin, `NERDIN_PAUSA`) e limite
  fixo de páginas por leitura.
- **FR-011**: "Desconectar" MUST apagar a sessão da Nerdin no perfil da ferramenta, sem afetar os outros portais.
- **FR-012**: A constituição MUST ganhar emenda no princípio VI, "Conta conectada": liberados Gupy, Indeed e Nerdin,
  com a Nerdin sob "Termos contrários" (decisão de 2026-11-24, esta spec). AGENTS.md, README e a skill buscar-vagas
  MUST citar a Nerdin nas candidaturas conectadas.
- **FR-013**: O link da página de candidaturas descoberto na área logada MUST ficar em `.cache/contas/`, fora do
  Git; o informado pela pessoa fica no `.env` (`NERDIN_CANDIDATURAS`), também fora do Git.

### Key Entities

- **Candidatura lida (Nerdin)**: o mesmo formato das outras contas (spec 018, data-model): portal `nerdin`,
  plataforma `Nerdin`, id `nerdin-NNNNN`, título, empresa, local, link, status (texto da Nerdin), etapa, resultado,
  data, avisos, ativa.
- **Página de candidaturas**: o endereço da área do candidato na Nerdin; descoberto na área logada ou informado pela
  pessoa no `.env`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com a Nerdin conectada, uma leitura propõe a etapa certa para 100% das candidaturas com situação
  conhecida da página de teste, e nenhuma etapa muda para situação desconhecida.
- **SC-002**: Nenhuma candidatura da Nerdin que já está no dashboard é proposta como nova (cruzamento pelo número em
  100% dos casos de teste, nos dois formatos de link).
- **SC-003**: Uma falha na Nerdin não impede a proposta da Gupy e do Indeed na mesma leitura.
- **SC-004**: No primeiro teste real, a pessoa vê as candidaturas que a Nerdin mostra na página dela, com a situação, e
  confirma ou descarta cada mudança em menos de 2 minutos.
- **SC-005**: Nenhum clique em botão do portal nem envio de formulário acontece durante a leitura (conferido nos
  testes pelo navegador simulado).

## Assumptions

- A Nerdin mantém o login pela sessão da janela; se esquecer ao fechar (como a Gupy), vale a mesma solução da spec 018:
  a janela fica aberta e minimizada enquanto o dashboard roda.
- O vocabulário da trilha e dos selos vem do print da página real (Clarifications). Como o passo feito, o atual e o
  não alcançado se distinguem pela aparência, a marcação exata de cada estado (classe ou ícone) é confirmada no
  primeiro teste logado; os rótulos dos dois últimos passos já bastam para separar "em andamento" de "recusada".
- Não se sabe, antes do teste, se os links do cartão trazem o número da vaga; por isso o cruzamento por cargo e
  empresa (FR-006).
- A busca pública da Nerdin (spec 020) não muda.
- A janela da ferramenta, o perfil local, o painel, a proposta e o "Aplicar marcadas" são os da spec 018; esta spec só
  acrescenta o portal.
