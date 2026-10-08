# Feature Specification: Iniciar a ferramenta com um comando

**Feature Branch**: `001-iniciar-com-um-comando` (pasta da spec; o trabalho acontece na `master`
por worktree, conforme a constituição)

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "Fase 0 do plano: a pessoa clona o repositório e dá um comando para
iniciar a ferramenta, que é uma página local no PC. O comando prepara o que faltar e abre a
página."

## Clarifications

### Session 2026-10-07

- Q: Depois de iniciar, a ferramenta fica presa à janela do terminal ou roda em segundo plano?
  → A: Presa ao terminal: a janela mostra o endereço e como parar; fechar a janela ou
  interromper para a ferramenta. Sem modo em segundo plano nesta feature.
- Q: Quais sistemas esta feature cobre? → A: Só Windows, com foco na experiência web; macOS e
  Linux vão para a lista de desejos (`specs/lista-de-desejos.md`) e entram depois que tudo
  rodar sem problemas no Windows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Primeira vez: clonar e abrir com um comando (Priority: P1)

Uma pessoa que procura emprego, com os pré-requisitos instalados, clona o repositório e roda um
único comando. O comando confere o que falta, explica o que vai instalar, pede a confirmação dela,
prepara tudo dentro da pasta do projeto e abre a ferramenta no navegador.

**Why this priority**: hoje a instalação exige vários comandos diferentes por sistema (criar e
ativar ambiente, instalar dependências, copiar configuração). É a primeira barreira para quem não é
técnico, e todas as outras funcionalidades dependem de a pessoa conseguir abrir a ferramenta.

**Independent Test**: num clone limpo, rodar o comando, aceitar a instalação e ver a página aberta
no navegador, sem nenhum outro passo.

**Acceptance Scenarios**:

1. **Given** um clone recente, sem nada preparado, **When** a pessoa roda o comando e confirma a
   instalação, **Then** as dependências são instaladas só dentro da pasta do projeto e a página
   abre no navegador padrão.
2. **Given** um clone recente, **When** a pessoa recusa a instalação, **Then** nada é instalado e
   a mensagem explica o que falta e como instalar à mão.
3. **Given** a instalação concluída e nenhuma configuração criada ainda, **When** a página abre,
   **Then** ela funciona e indica o próximo passo (configurar a busca), e o comando não criou nem
   alterou nenhuma configuração ou dado da pessoa.

---

### User Story 2 - Uso do dia a dia: o mesmo comando abre em segundos (Priority: P1)

Com tudo preparado, a pessoa roda o mesmo comando sempre que quer usar a ferramenta. Ele abre a
página em segundos, sem perguntas. Se a ferramenta já estiver aberta, o comando só leva a pessoa
até ela, sem abrir uma segunda cópia.

**Why this priority**: é o uso que se repete todos os dias; se for lento ou fizer perguntas, a
pessoa volta a depender de passos manuais ou de alguém técnico.

**Independent Test**: com o ambiente pronto, rodar o comando duas vezes seguidas: a primeira abre
a ferramenta, a segunda só abre a página da que já está rodando.

**Acceptance Scenarios**:

1. **Given** o ambiente pronto, **When** a pessoa roda o comando, **Then** a página abre sem
   perguntas e sem acesso à internet.
2. **Given** a ferramenta já aberta, **When** a pessoa roda o comando de novo, **Then** a página
   da ferramenta aberta é exibida e nenhuma segunda cópia é iniciada.
3. **Given** uma atualização da ferramenta que exige uma dependência nova, **When** a pessoa roda
   o comando, **Then** ele avisa, pede confirmação e instala só o que falta.

---

### User Story 3 - Atalho de duplo clique (Priority: P3)

Quem prefere não usar o terminal encontra na pasta um atalho para Windows que faz o mesmo
que o comando, com a janela aberta o suficiente para ler mensagens de erro.

**Why this priority**: amplia o público, mas o comando já resolve o problema principal.

**Independent Test**: dar dois cliques no atalho e ver o mesmo resultado do comando.

**Acceptance Scenarios**:

1. **Given** o atalho para Windows, **When** a pessoa dá dois cliques, **Then** acontece o
   mesmo que ao rodar o comando, e qualquer erro fica visível na janela até ela fechá-la.

---

### Edge Cases

- Pré-requisito ausente ou com versão abaixo da mínima: mensagem com a versão exigida e onde
  baixar; nada mais é feito.
- Sem internet na primeira instalação: falha com mensagem clara, e a próxima execução completa o
  que ficou faltando, sem a pessoa limpar nada à mão.
- Instalação interrompida no meio (janela fechada, queda de energia): a próxima execução detecta
  o ambiente incompleto e oferece refazê-lo.
- Ambiente vindo de outra máquina ou sistema (pasta copiada): é detectado como inválido e a
  ferramenta oferece recriá-lo.
- Porta já ocupada por outro programa: mensagem dizendo isso e como usar outra porta.
- Caminho da pasta com espaços ou acentos (ex.: "Área de Trabalho"): funciona normalmente.
- Comando rodado a partir de outra pasta: funciona, porque se orienta pela pasta do projeto.
- Navegador não abre (ex.: máquina sem interface gráfica): o endereço da página fica visível
  para abrir à mão.
- Ambiente já preparado do jeito antigo, com os passos manuais: é reaproveitado, sem reinstalar.
- Janela do terminal fechada sem Ctrl+C: a ferramenta para junto, sem sobrar processo; na
  próxima execução ela inicia normalmente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta MUST poder ser iniciada no Windows por um único comando documentado,
  a partir da pasta clonada.
- **FR-002**: O comando MUST verificar os pré-requisitos (versão mínima) antes de qualquer outra
  ação e, se faltarem, dizer qual versão é exigida e onde obtê-la.
- **FR-003**: Se o ambiente do projeto não existir, estiver incompleto ou faltar alguma
  dependência, o comando MUST dizer o que será instalado e pedir confirmação antes de instalar.
- **FR-004**: Toda instalação MUST ficar dentro da pasta do projeto, fora do controle de versão,
  sem alterar nada do sistema da pessoa.
- **FR-005**: Durante a instalação, a pessoa MUST ver o andamento; em caso de falha, uma mensagem
  com a causa provável e como tentar de novo, sem rastreamento técnico bruto.
- **FR-006**: Com o ambiente pronto, o comando MUST iniciar a ferramenta, abrir a página no
  navegador padrão e mostrar o endereço da página.
- **FR-007**: Se a ferramenta já estiver em execução, o comando MUST abrir a página dela e
  terminar sem erro e sem iniciar outra cópia.
- **FR-008**: Execuções com o ambiente pronto MUST NOT fazer perguntas nem acessar a internet.
- **FR-009**: O comando MUST NOT criar nem alterar configuração, perfil, vagas ou qualquer dado
  da pessoa; a página MUST funcionar sem configuração e indicar o próximo passo.
- **FR-010**: As opções que a ferramenta já oferece ao iniciar MUST continuar disponíveis pelo
  comando: não abrir o navegador, aceitar acesso de outros aparelhos da rede local e usar outra
  porta.
- **FR-011**: O comando MUST oferecer uma opção explícita para aceitar a instalação sem perguntar,
  para quem automatiza a inicialização.
- **FR-012**: A ferramenta MUST ficar em execução na janela do terminal em que foi iniciada,
  mostrando o endereço da página e como parar; fechar a janela ou interromper (Ctrl+C) MUST
  pará-la por completo, sem deixar processo rodando, e os dados MUST continuar salvos.
- **FR-013**: MUST existir um atalho de duplo clique para Windows que faz o mesmo que o
  comando, numa janela que fica aberta enquanto a ferramenta roda e que continua visível quando
  há erro (por isso não minimizada; o atalho minimizado atual continua como alternativa).
- **FR-014**: A documentação de instalação MUST passar a ser "clonar e rodar o comando"; as formas
  atuais de iniciar (tarefa automática do editor, página aberta por outro servidor local, passos
  manuais) MUST continuar funcionando e documentadas como alternativas.
- **FR-015**: Todas as mensagens MUST estar em português do Brasil.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa com os pré-requisitos instalados vai do clone à página aberta em até
  5 minutos na primeira vez, digitando no máximo dois comandos (clonar e iniciar) e respondendo a
  uma confirmação.
- **SC-002**: Com o ambiente pronto, a página abre em até 10 segundos depois do comando.
- **SC-003**: Em 100% das vezes em que a ferramenta já está aberta, rodar o comando de novo exibe
  a página existente, sem erro e sem segunda cópia.
- **SC-004**: O fluxo da primeira vez e o do dia a dia funcionam num clone limpo no Windows 10 e
  no Windows 11.
- **SC-005**: Comparando a pasta antes e depois, o comando não cria nem modifica nenhum arquivo
  de configuração, perfil ou dados da pessoa (só o ambiente isolado do projeto).
- **SC-006**: Toda falha prevista nos casos-limite termina com uma mensagem que diz o que fazer,
  e a execução seguinte se recupera sem limpeza manual.

## Assumptions

- A pessoa já tem os pré-requisitos instalados (o interpretador na versão mínima exigida pela
  ferramenta e o Git para clonar); instalá-los está fora do escopo, o comando só orienta.
- Internet só é necessária na primeira instalação e quando uma atualização trouxer dependência
  nova.
- O ambiente isolado fica numa pasta do projeto que já está fora do controle de versão.
- A ferramenta continua sendo uma página local servida por um servidor no próprio computador
  (decisão de arquitetura do usuário); a única mudança na página é o aviso de próximo passo
  quando ainda não há configuração (hoje a página não indica nada nesse caso).
- Fora do escopo: macOS e Linux (comando e atalhos), na lista de desejos até o Windows rodar sem
  problemas; primeiros passos e anamnese (Fase 3), escolha do provedor de IA (Fase 1) e
  atualização da ferramenta em si (baixar a versão nova do repositório); esta feature só leva a
  pessoa até a página e detecta dependências novas.
- Sem configuração, a página já funciona hoje com os valores padrão, e a primeira gravação no
  painel de filtros cria a configuração; esse comportamento é mantido.
