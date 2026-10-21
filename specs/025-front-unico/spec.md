# Feature Specification: Front único (a página nova vira a única página da ferramenta)

**Feature Branch**: `025-front-unico` (worktree saída da `master`; o código do front fica na branch `frontend-react`;
testada na branch pessoal antes da `master`)

**Created**: 2026-10-20

**Status**: Concluída (2026-10-21): a página nova em `/` e o dashboard antigo fora; a conferência visual no celular e nos dois temas (T069) fica com a pessoa

**Input**: User description: "Temos atualmente 2 páginas, a antiga e a /novo, e quero apenas uma delas: analise o que
precisamos para que a /novo integre e use as APIs corretamente e passe a ser a única página da nossa ferramenta. Por
hora não vamos ter novos commits vindos do Figma, assim temos que ajustar aqui o layout."

## Contexto

Hoje a ferramenta tem duas páginas:

- **`/`**: o dashboard atual (`dash/dashboard.html`), com todas as funções.
- **`/novo/`**: o front novo (spec 022), com o visual aprovado, montado a partir da branch `frontend-react`. Só o
  quadro e o Relatório usam dados reais: ler as vagas, seguir, não seguir, voltar para triagem, mover de etapa,
  anotar, remover e Forçar verificar. Busca, filtros, IA, perfil, contas conectadas e entrevista mostram dados de
  exemplo e "salvam" só na memória da tela. Currículo, kit da candidatura e análises do perfil não existem nele.

O Figma Make não vai mandar commits por enquanto. O front novo passa a ser ajustado aqui, tanto o layout quanto a
ligação com o servidor, direto na `frontend-react`, e segue chegando à `master` pela Action "Front: abrir PR".
O servidor e as rotas descritas em `dash/API.md` já existem e não mudam nesta spec, exceto na troca final da página.

## Clarifications

### Session 2026-10-20

- Q: Quem ajusta o front novo? → A: Nós, aqui, direto na `frontend-react`; o Figma Make não manda commits por ora.
- Q: Qual página fica? → A: A nova. A antiga sai quando a nova tiver todas as funções e a pessoa aprovar a troca.

## User Scenarios & Testing *(mandatory)*

As histórias seguem a ordem de entrega. Cada uma é testada sozinha em `/novo/`, enquanto `/` continua com o dashboard
atual, então a pessoa não perde função no meio do caminho.

### User Story 1 - Trazer vagas para a página nova (Priority: P1)

A pessoa usa só a página nova no dia a dia para trazer vagas: busca vagas, acompanha o andamento, cancela se quiser,
completa as descrições pendentes, tenta a nota de novo quando a IA falha e adiciona vagas por link, por post ou por
texto colado. A linha da última busca aparece no topo do Relatório.

**Why this priority**: é o uso diário da ferramenta; sem isso a pessoa ainda precisa voltar para a página antiga.

**Independent Test**: em `/novo/`, rodar uma busca de verdade, adicionar uma vaga por link e outra por texto colado,
e ver as três coisas também no dashboard antigo.

**Acceptance Scenarios**:

1. **Given** filtros e perfil prontos, **When** a pessoa clica em Buscar vagas, **Then** vê antes o que vai rodar
   (portais, cargos, janela, tempo estimado, qual IA e se a cobrança é por uso) e só então confirma.
2. **Given** uma busca há menos de 6 horas ou um portal em espera, **When** a pessoa tenta buscar, **Then** vê o
   aviso e só segue se confirmar; antes do horário mínimo, o botão fica desligado com o motivo.
3. **Given** uma busca rodando (da página, do terminal ou do chat), **When** a pessoa olha o Relatório, **Then** vê o
   andamento atualizado sozinho e pode cancelar a busca iniciada pela página.
4. **Given** um link de vaga, **When** a pessoa adiciona, **Then** a vaga entra no Relatório; se o link não puder ser
   lido, o formulário abre preenchido com o que deu para ler.
5. **Given** um post do LinkedIn ou um texto colado e uma IA escolhida, **When** a pessoa pede para preencher,
   **Then** a IA só preenche o formulário; nada é gravado até a pessoa conferir e clicar em adicionar.
6. **Given** vagas sem descrição, **When** a pessoa clica em Completar descrições, **Then** vê o andamento e quantas
   faltam, respeitando a espera dos portais.

---

### User Story 2 - Configurar a busca e a IA na página nova (Priority: P1)

A pessoa ajusta os filtros da busca nacional e da internacional e escolhe, testa e troca a IA na página nova, com as
opções reais da ferramenta.

**Why this priority**: a busca depende dos filtros, e a nota, o currículo e a entrevista dependem da IA.

**Independent Test**: mudar um filtro e a IA em `/novo/`, recarregar a página e ver a mudança mantida, também no
dashboard antigo.

**Acceptance Scenarios**:

1. **Given** a tela de filtros, **When** abre, **Then** mostra os filtros gravados e só as opções que a ferramenta
   aceita (países, modelos, janelas, fontes, idiomas, moedas e o resto).
2. **Given** um filtro inválido (sem cargo, híbrido sem cidade), **When** a pessoa salva, **Then** vê a mensagem do
   servidor e nada é gravado.
3. **Given** a tela da IA, **When** a pessoa escolhe um provedor, **Then** vê só os provedores que a ferramenta
   suporta, o que é enviado ao provedor e se a cobrança é por uso.
4. **Given** uma chave cadastrada, **When** a tela abre, **Then** mostra só os 4 últimos caracteres; a chave nunca
   aparece inteira nem fica guardada no navegador.
5. **Given** uma chave digitada, **When** a pessoa testa a conexão, **Then** vê o resultado sem gravar a chave.

---

### User Story 3 - Perfil e análises do perfil na página nova (Priority: P2)

A pessoa monta ou atualiza o perfil na página nova: envia currículo, PDF ou exportação do LinkedIn, gera o rascunho
com ou sem IA, resolve conflitos, responde a anamnese, vê o diagnóstico, revisa o que muda e grava. Também usa um
currículo que já tem, marca o "Seu currículo" de cada idioma e roda as análises: lacunas, prontidão internacional,
cargos-alvo e plano de estudo.

**Why this priority**: o perfil é a base da nota e do currículo, mas muda pouco depois do primeiro uso.

**Independent Test**: refazer o perfil do zero em `/novo/` com um currículo de exemplo, gravar e conferir o
`perfil.md`.

**Acceptance Scenarios**:

1. **Given** a página nova, **When** a pessoa abre Meu perfil, **Then** vê o perfil real e o passo em que parou,
   sem perfil de exemplo nem campos que a ferramenta não tem (pretensão salarial, anos de experiência).
2. **Given** um perfil existente, **When** a pessoa termina a revisão, **Then** vê o que muda antes de confirmar e
   gravar.
3. **Given** filtros propostos pelo perfil ou pelos cargos-alvo, **When** aparecem, **Then** são só proposta até a
   pessoa clicar em gravar.
4. **Given** uma análise que usa IA (cargos-alvo, plano de estudo), **When** a pessoa pede, **Then** vê antes qual
   IA vai rodar e o aviso de custo.

---

### User Story 4 - Currículo e kit da candidatura na página nova (Priority: P2)

No detalhe de uma vaga, a pessoa vê o que a candidatura pede (checklist), gera currículos para a vaga, baixa o PDF e
o DOCX, vê a conferência (fatos, ATS, requisitos), escreve carta ou mensagem e prepara respostas de formulário. Os
lembretes de follow-up aparecem e podem ser marcados como feitos, dispensados ou parados. Em Meu perfil, gera o
currículo base.

**Why this priority**: é o que leva da vaga à candidatura, e hoje não existe na página nova.

**Independent Test**: para uma vaga seguida, gerar um currículo, uma carta e respostas em `/novo/` e abrir os
arquivos gerados.

**Acceptance Scenarios**:

1. **Given** uma vaga seguida, **When** a pessoa abre Gerar currículo, **Then** vê as técnicas e as opções sugeridas
   para a vaga, qual IA vai rodar e o aviso de custo, e só gera ao confirmar.
2. **Given** uma geração em andamento, **When** a pessoa espera, **Then** vê a etapa atual; se falhar, pode tentar de
   novo.
3. **Given** perguntas de formulário com autorização de trabalho, visto, salário, deficiência, relocação ou
   diversidade, **When** as respostas voltam, **Then** essas perguntas vêm sem resposta da IA e com um campo para a
   pessoa escrever.
4. **Given** uma carta pronta, **When** a pessoa usa, **Then** pode copiar o texto; "Enviar por e-mail" só abre o
   programa de e-mail dela.

---

### User Story 5 - Preparar entrevista na página nova (Priority: P3)

A pessoa prepara a entrevista de uma vaga com dados reais: dossiê da vaga, texto da empresa colado por ela e resumo
com IA, perguntas prováveis, histórias (inclusive sugeridas pela IA), simulação em português ou inglês e anotação de
como foi.

**Why this priority**: usado só quando há entrevista marcada.

**Independent Test**: para uma vaga em Entrevista, salvar uma história e uma anotação em `/novo/` e vê-las no
dashboard antigo.

**Acceptance Scenarios**:

1. **Given** uma vaga, **When** a pessoa abre Preparar entrevista, **Then** vê os dados dessa vaga, sem conteúdo
   fixo de exemplo.
2. **Given** rascunhos de histórias da IA, **When** aparecem, **Then** não são gravados até "Salvar esta história".
3. **Given** uma história, **When** a pessoa remove, **Then** precisa confirmar com um segundo clique.

---

### User Story 6 - Atualizar candidaturas pelas contas conectadas na página nova (Priority: P3)

A pessoa conecta a Gupy e o Indeed na janela da ferramenta, lê o andamento das candidaturas e aplica só as mudanças
que marcou, ou importa o histórico.

**Why this priority**: opcional e menos frequente.

**Independent Test**: conectar um portal em `/novo/`, ler, desmarcar parte das mudanças, aplicar e conferir o quadro.

**Acceptance Scenarios**:

1. **Given** um portal desconectado, **When** a pessoa clica em Conectar, **Then** a janela da ferramenta abre no
   login do portal; a página nunca pede nem mostra senha.
2. **Given** uma leitura pronta, **When** a pessoa aplica, **Then** só os itens marcados são gravados.
3. **Given** um bloqueio ou pedido de login no portal, **When** acontece, **Then** a página mostra o aviso e para,
   sem tentar contornar.

---

### User Story 7 - A troca: uma página só (Priority: P3, depende das histórias 1 a 6)

Com as funções todas na página nova e o OK da pessoa, a página nova passa a abrir em `/`, o endereço `/novo/` leva
para `/` e o dashboard antigo sai da ferramenta. Comandos, atalhos, documentação, skills e testes passam a falar só
da página nova.

**Why this priority**: é o objetivo final, mas só pode acontecer depois da paridade.

**Independent Test**: abrir a ferramenta pelo `iniciar.py` e pelo atalho e cair na página nova; abrir `/novo/` e cair
em `/`; os testes passam.

**Acceptance Scenarios**:

1. **Given** a troca feita, **When** a pessoa abre `http://127.0.0.1:8765`, **Then** vê a página nova.
2. **Given** um favorito antigo para `/novo/`, **When** a pessoa abre, **Then** chega à página nova em `/`.
3. **Given** a lista de paridade (FR-020), **When** a troca é proposta, **Then** cada item foi conferido em uso real.

### Edge Cases

- Servidor fora do ar: a página entra em modo demonstração com o aviso fixo no topo; com o servidor no ar, nunca
  mostra nem grava dados de exemplo.
- Página aberta de outro aparelho da rede (só leitura): os botões que gravam ficam desligados com o motivo.
- Sem IA escolhida: os botões que precisam de IA levam à tela da IA em vez de chamar.
- Duas escritas seguidas na mesma vaga (ex.: arrastar e anotar): vão uma por vez, e a tela fica com a vaga que o
  servidor devolveu.
- Busca ou geração iniciada em outro lugar (terminal, chat, outra aba): a página mostra o andamento e não deixa
  começar outra.
- Erro do servidor: a mensagem dele aparece em português, sem ser escondida nem trocada por "erro desconhecido".
- Descrição, título, post ou mensagem com HTML ou script: aparece como texto; links só `http` e `https`, em nova aba.
- Arquivo de material grande demais ou de tipo não aceito no perfil: a página avisa antes de enviar.
- Página antiga e nova abertas ao mesmo tempo: as duas veem as mesmas vagas, porque leem do mesmo servidor.

## Requirements *(mandatory)*

### Functional Requirements

**Dados e regras gerais**

- **FR-001**: Todas as telas da página nova MUST usar só os dados e as ações do servidor local, conforme `dash/API.md`.
  Dados de exemplo só no modo demonstração (servidor fora do ar), com o aviso fixo e visível.
- **FR-002**: O navegador MUST guardar só preferências de tela (aba aberta, filtros visuais, ordem, tema); nunca vagas,
  perfil, filtros da busca, IA, chave ou candidaturas. Sai o exportar e importar de dados pelo navegador.
- **FR-003**: Campos que a ferramenta não tem MUST sair das telas (ex.: pretensão salarial e anos de experiência no
  perfil, provedores de IA que a ferramenta não suporta, análise automática nos filtros). Se uma tela precisar de algo
  que o servidor não oferece, isso fica anotado em vez de ser simulado.
- **FR-004**: As regras da seção 4 do `dash/API.md` MUST valer em todas as telas:
  - confirmar antes de gravar ou apagar;
  - IA só no clique, com o aviso de custo;
  - nada é enviado em nome da pessoa;
  - perguntas sensíveis ficam para a pessoa;
  - contas conectadas só leitura;
  - texto da internet aparece como texto;
  - respeito aos portais;
  - só leitura de outro aparelho.
- **FR-005**: Tarefas longas (busca, descrições, nota, geração de currículo, carta e respostas, leitura das contas)
  MUST mostrar o andamento atualizado sozinho, e as mensagens de erro do servidor MUST aparecer para a pessoa.
- **FR-006**: Telas novas MUST seguir o visual atual da página nova (paleta, temas claro e escuro, componentes), em
  português do Brasil, e funcionar na largura de um notebook e de um celular.

**Por área** (uma história cada)

- **FR-010**: Buscar vagas, Completar descrições, Tentar a nota de novo, a linha da última busca e Adicionar vaga
  (por link, post ou texto) MUST funcionar como no dashboard atual (História 1; `dash/API.md` 3.2 e 3.3).
- **FR-011**: Filtros da busca (nacional e internacional) e IA MUST ler e gravar a configuração real (História 2;
  `dash/API.md` 3.4 e 3.5).
- **FR-012**: Meu perfil e Primeiros passos, "Já tenho currículo", "Seu currículo" e as Análises do perfil MUST
  funcionar como no dashboard atual (História 3; `dash/API.md` 3.6 e 3.7).
- **FR-013**: Currículo por vaga e currículo base, checklist, carta, respostas e lembretes MUST existir na página nova
  (História 4; `dash/API.md` 3.1, 3.8, 3.9 e 3.12).
- **FR-014**: Preparar entrevista MUST usar os dados reais da vaga, com as abas Dossiê, Perguntas, Histórias, Simular,
  Salário e Depois (História 5; `dash/API.md` 3.10).
- **FR-015**: Contas conectadas e Atualizar candidaturas MUST funcionar como no dashboard atual (História 6;
  `dash/API.md` 3.11).
- **FR-016**: As telas que só existem na página nova (Métricas e Funil, Internacional, Preparador de Entrevistas como
  aba) MUST usar só dados reais; o que não tiver fonte real sai da tela.

**Entrega e troca**

- **FR-020**: Antes da troca, MUST haver uma lista de paridade com cada função do dashboard atual (botões e telas) e
  onde ela fica na página nova, conferida item por item em uso real.
- **FR-021**: Cada história MUST chegar à `master` pelo caminho de hoje (commit na `frontend-react` → Action "Front:
  abrir PR" → PR revisado e testado na branch pessoal → merge). Para testar antes, o front pode ser montado neste
  computador.
- **FR-022**: Na troca (História 7), a página nova MUST abrir em `/`, `/novo` e `/novo/` MUST levar a `/`, e o
  dashboard antigo MUST sair. Os comandos de abrir a ferramenta, os atalhos, a documentação (README, `dash/API.md`,
  `AGENTS.md`), as skills que citam a página e os testes MUST ser ajustados.
- **FR-023**: Até a troca, o dashboard atual em `/` MUST continuar funcionando sem mudança.
- **FR-024**: Quem usa a ferramenta MUST continuar sem precisar de Node: o front montado vai pronto no repositório.

### Key Entities

- **Página nova (front)**: a interface única da ferramenta depois da troca; lê e grava tudo pelo servidor local.
- **Lista de paridade**: cada função do dashboard atual, onde ela está na página nova e se foi conferida.
- **Modo demonstração**: o estado da página nova quando o servidor não responde; só nele aparecem dados de exemplo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Depois da troca, a ferramenta tem uma página só: abrir a ferramenta por qualquer caminho (comando,
  atalho, `/` ou `/novo/`) leva à página nova.
- **SC-002**: 100% dos itens da lista de paridade estão conferidos em uso real antes da troca.
- **SC-003**: Com o servidor no ar, nenhuma tela mostra dados de exemplo, e recarregar a página não perde nenhuma
  mudança que a pessoa tenha salvado.
- **SC-004**: Nenhuma chave de API, vaga, perfil ou candidatura fica guardada no navegador.
- **SC-005**: Uma semana de uso diário só na página nova (buscar, triar, seguir, gerar currículo) sem precisar abrir a
  página antiga, antes da troca.
- **SC-006**: Os testes da ferramenta continuam passando em cada entrega.
- **SC-007**: Quem usa a ferramenta continua sem instalar Node.

## Assumptions

- O servidor e as rotas de `dash/API.md` cobrem tudo o que a página nova precisa. Se faltar algo, a mudança no
  servidor entra no plano como item à parte, com justificativa.
- O visual atual da página nova (spec 022 e o que a spec 023 levou ao dashboard antigo) é a referência; não há
  redesenho.
- As entregas vão para a `master` por história, já que `/` segue com o dashboard antigo até a troca.
- Na troca, o dashboard antigo é apagado, sem ficar como reserva em outro endereço (a pessoa pediu uma página só).
- O modo demonstração continua depois da troca, para quem abrir a página sem o servidor.
- O Figma Make não grava na `frontend-react` enquanto esta spec estiver aberta. Se voltar, é preciso combinar antes
  para um lado não sobrescrever o outro.
- A página aberta pelo Live Server continua funcionando, porque usa o endereço completo do servidor.

## Fora do escopo

- Mudar as regras do servidor, da busca, da nota ou do currículo.
- Funções novas que não existem no dashboard atual nem na página nova.
- Integração com o Figma Make (prompts para o analista), enquanto ele estiver parado.
