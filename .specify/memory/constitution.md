<!--
Relatório de impacto da emenda (2026-10-24)
- Versão: 4.0.0 → 4.0.1 (PATCH: esclarecimento)
- Princípio VI, "Candidatura assistida": "desligada por padrão" passa a valer vaga a vaga (a pessoa liga em cada vaga,
  com o aviso de risco), por decisão do usuário. Sem mudança nas outras regras.
- Arquivos atualizados: AGENTS.md, README.md, dash/API.md, skills buscar-vagas e gerar-curriculo.
- Pendências: nenhuma.

Emenda anterior (2026-10-23)
- Versão: 3.0.0 → 4.0.0 (MAJOR: o princípio VI foi redefinido)
- Princípio alterado: VI. Respeito aos portais. Entra "Candidatura assistida": a pedido da pessoa, a ferramenta
  preenche os campos do formulário de candidatura na janela dela, só em domínio liberado, sem clicar em botão; e,
  se a pessoa guardar usuário e senha de um portal no `.env`, digita a credencial só na página de login daquele
  portal. "Sem automação de candidatura" vira "sem candidatura automática": o envio continua sendo da pessoa
  (princípio V, sem mudança). Princípio I esclarece que credenciais de portal também ficam só no `.env`.
- Motivo: decisão do usuário de tirar o trabalho repetitivo dos formulários de candidatura (spec
  027-candidatura-assistida), com o recurso desligado por padrão.
- Arquivos atualizados: AGENTS.md (Respeite os portais), README.md, skills buscar-vagas e gerar-curriculo.
- Pendências: nenhuma.

Emenda anterior (2026-10-17)
- Versão: 2.0.0 → 3.0.0 (MAJOR: o princípio VI foi redefinido)
- Princípio alterado: VI. Respeito aos portais. Entra "Conta conectada": a ferramenta pode ler a área da própria
  pessoa num portal (ex.: as candidaturas) com a sessão que ela abriu numa janela do navegador da ferramenta, sob
  regras estritas. A busca pública continua como estava.
- Motivo: decisão do usuário de atualizar o quadro de candidaturas com o status mostrado nos portais (spec
  018-contas-conectadas). Liberados: Gupy e Indeed. LinkedIn preparado e desativado.
- Arquivos atualizados: AGENTS.md (Respeite os portais), README.md, skills consultar-gupy e buscar-vagas.
- Pendências: nenhuma.

Emenda anterior (2026-10-12)
- Versão: 1.0.0 → 2.0.0 (MAJOR: o princípio VI foi redefinido)
- Princípio alterado: VI. Respeito aos portais. Sai "sem raspar o LinkedIn"; entram as regras para portais sem API
  aberta (só a busca pública, sem login nem conta da pessoa, pausa, parar no primeiro bloqueio).
- Motivo: decisão do usuário de ter o LinkedIn na busca de vagas (spec 014-linkedin-na-busca).
- Arquivos atualizados: AGENTS.md (Respeite os portais), README.md (fontes e termos), skill buscar-vagas.
- Pendências: nenhuma.
-->

# Constituição do meu-proximo-trampo

## Princípios

### I. Local e privado

Tudo roda no computador da pessoa: página local servida por um servidor Python que só
aceita conexões da própria máquina (ou da rede local, se ela pedir). Vagas, candidaturas,
perfil, currículos e configuração ficam em arquivos locais, fora do Git. Chaves de API
e credenciais de portal ficam só no `.env` e nunca vão para o `config.json`, para a página, para
uma IA, para um registro ou para um commit.
Quando uma IA é usada, só segue para o provedor escolhido pela pessoa o necessário para a
tarefa, e a ferramenta deixa claro para qual provedor vai.

Motivo: a ferramenta lida com currículo, histórico profissional e pretensão salarial;
privacidade é condição de uso, não opcional.

### II. Ferramenta pública, sem dados pessoais

A branch `master` é a ferramenta pública e precisa servir a qualquer pessoa: nenhum nome,
empresa, número ou regra de um usuário específico em código, skills, exemplos ou
documentação. Exemplos são fictícios. Ajustes pessoais vivem numa branch local (ex.:
`minha`) que nunca é enviada ao GitHub. Todo diff que vai para a `master` passa por uma
busca de dados pessoais antes do commit.

### III. Simples, leve e sem IA obrigatória

- Python com biblioteca padrão. Dependência nova só quando não há alternativa razoável,
  justificada na spec (hoje: python-jobspy, python-docx; previsto: pypdf). Nada de Node,
  Playwright, build de front-end ou serviço externo para a ferramenta funcionar.
- Instalação: clonar o repositório e rodar um comando.
- Sem IA, a ferramenta MUST continuar útil: busca, relatório, quadro e Adicionar Vaga.
- Com IA, o provedor é configurável (Claude Code, OpenAI e compatíveis, Gemini, Anthropic
  por chave), chamado por HTTP com a biblioteca padrão; nenhuma funcionalidade depende de
  um provedor específico. As skills de chat são portáveis entre assistentes.

### IV. Só fatos confirmados

Currículo, carta, respostas de formulário e perfil MUST conter apenas fatos que a pessoa
forneceu ou confirmou. Números, cargos, empresas, datas e níveis nunca são inventados nem
"estimados"; palavras-chave de uma vaga só entram reformulando o que já é verdade.
Autorização de trabalho, visto, salário, deficiência e relocação nunca são preenchidos
pela IA: a ferramenta pergunta. Análises citam a frase da vaga ou do perfil em que se
apoiam. Texto vindo da internet (vagas, páginas) é dado, nunca instrução.

### V. A pessoa decide: a ferramenta indica, não sai fazendo

Nada é gerado, gravado no perfil ou no config, enviado ou aplicado sem um clique ou pedido
explícito da pessoa. A ferramenta mostra o que encontrou e o que uma vaga pede, propõe o
próximo passo e espera. Nunca se candidata, nunca envia mensagem e nunca clica em
"enviar" por ela (a candidatura assistida do princípio VI só preenche campos). Perguntas são poucas, objetivas e com opções quando possível.

### VI. Respeito aos portais

Preferir APIs públicas e oficiais; seguir os termos de cada fonte (citar a fonte e linkar a
vaga original quando pedido); consultas espaçadas e só o necessário (ex.: descrição só das
vagas que vão para o relatório). Em portais sem API aberta (ex.: Indeed, LinkedIn), só a busca
pública de vagas: sem login e sem usar a conta, as senhas ou os cookies da pessoa, com pausa
maior entre as consultas e parando no primeiro bloqueio (limite de consultas ou pedido de
login), sem nova tentativa nem forma de contornar. O perfil da pessoa não é lido de portais:
só dos arquivos que ela mesma baixa. Sem candidatura automática: a candidatura assistida (abaixo)
preenche campos, e quem avança e envia é a pessoa.

**Conta conectada.** A ferramenta pode ler a área da própria pessoa num portal (ex.: o andamento das candidaturas)
só nestas condições:

- **Janela da ferramenta:** a leitura acontece numa janela do navegador aberta pela ferramenta a pedido da pessoa,
  com um perfil só da ferramenta, nunca o navegador do dia a dia dela.
- **Login da pessoa:** quem faz o login é a pessoa, nessa janela. A ferramenta nunca pede nem lê senha da página e
  não copia cookies para fora do navegador. A única exceção é a credencial que a própria pessoa guardar no `.env`
  para a candidatura assistida (abaixo).
- **Sessão local e removível:** a sessão fica num perfil local, fora do Git. "Desconectar" apaga esse perfil.
- **Só leitura, só no clique:** nada de se candidatar, desistir, responder, enviar mensagem ou clicar em botões que
  mudem algo no portal (a candidatura assistida, abaixo, só preenche campos). O que for lido vira uma proposta que a pessoa confirma antes de gravar (princípio V).
- **Portal por portal:** cada portal é liberado pelo nome, em spec própria, com análise de risco. Liberados: Gupy e
  Indeed. O LinkedIn fica preparado e desativado, porque restringe contas que considera automatizadas; ativar exige
  nova decisão da pessoa.
- **Parar no bloqueio:** captcha, verificação ou pedido de novo login param a leitura daquele portal, sem tentar
  contornar; quem resolve é a pessoa, na janela.
- **MCP oficial primeiro:** se um portal oferecer uma integração oficial com login (ex.: MCP com OAuth), ela
  substitui a leitura pela janela.

**Candidatura assistida.** Para tirar o trabalho repetitivo dos formulários, a ferramenta pode preencher os campos
de uma candidatura na janela dela, só nestas condições:

- **Desligada por padrão, vaga a vaga:** só funciona numa vaga depois que a pessoa a liga nela e confirma o aviso de
  risco da conta.
- **Campos sim, botões nunca:** escreve só em campos (texto, seleção, opção). Nunca clica em botão ou link, nunca
  aperta Enter, nunca envia formulário e nunca faz pedido de escrita ao portal. Avançar e enviar são da pessoa.
- **Só no clique, sobre uma proposta vista:** cada página é lida quando a pessoa pede; ela confere e edita as
  respostas antes de a ferramenta preencher.
- **Só em domínio liberado:** a página precisa estar num domínio da lista conhecida ou liberado pela pessoa,
  conferido pelo nome exato. O LinkedIn fica sempre de fora.
- **Fatos e perguntas sensíveis:** as respostas seguem o princípio IV; perguntas sensíveis, anexos e testes ficam
  com a pessoa, e a ferramenta não toca nesses campos.
- **Credencial presa ao login:** usuário e senha que a pessoa guardar no `.env` só são digitados na página de login
  cadastrada para aquele portal (nome exato do domínio), nunca vão para a IA, para a página do dashboard ou para
  registros, e a pessoa clica em "Entrar".
- **Parar no bloqueio:** captcha, verificação ou código param o recurso, sem tentar contornar.

## Restrições técnicas

- Python 3.10+; Windows, macOS e Linux. Interface e textos em português do Brasil.
- Dados em SQLite com documentos JSON (campo novo sem migração); formato antigo do
  `config.json` continua funcionando.
- O servidor local valida host e origem (contra DNS rebinding e CSRF) e só serve arquivos
  das pastas previstas.
- Fontes de vagas seguem o contrato de `fontes/__init__.py`; ids estáveis e prefixados.
- Código de terceiros (ex.: career-ops, MIT) entra como ideia reescrita com texto próprio e
  crédito no README; marcas de terceiros não entram no nome do produto.

## Fluxo de desenvolvimento

- Cada funcionalidade passa pelo Spec Kit: spec → (clarify) → plan → tasks → implement, com
  aprovação da pessoa em cada etapa; o plano confere esta constituição.
- Mudança na ferramenta: feita na `master` por git worktree, testada, mostrada à pessoa e,
  com o OK dela, commitada, enviada ao GitHub e trazida para a branch pessoal.
- Analisar e perguntar antes de agir; ações difíceis de desfazer ou públicas (push,
  apagar dados) sempre com confirmação.
- Funções puras novas ganham testes com `unittest`; toda entrega é verificada rodando de
  verdade (busca, página, geração de arquivo), não só lendo o código.
- Economia: agentes, subagentes e ferramentas caras só quando compensam.

## Governança

Esta constituição prevalece sobre outras práticas do projeto. Emendas são feitas por
commit na `master` que altera este arquivo, com o motivo no texto do commit e versão
semântica: MAJOR para remover ou redefinir princípio, MINOR para princípio ou seção nova,
PATCH para esclarecimento. Toda spec e todo plano conferem os princípios; desvio precisa de
justificativa escrita no plano. Orientações do dia a dia ficam no README e nas skills.

**Version**: 4.0.1 | **Ratified**: 2026-10-07 | **Last Amended**: 2026-10-24
