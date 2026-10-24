# Lista de desejos

O que ficou para depois, com o motivo. Cada item vira uma spec (`/speckit-specify`) quando for
priorizado.

## Plataformas

- **macOS e Linux para o comando `iniciar`** (de `001-iniciar-com-um-comando`): atalhos
  `iniciar.command` (macOS) e `iniciar.sh` (Linux), com permissão de execução e fim de linha LF,
  e verificação do fluxo da primeira vez e do dia a dia nos dois sistemas. Entra depois que o
  Windows rodar sem problemas. Decisão do usuário em 2026-10-08: foco na experiência web no
  Windows.

## Fontes de vagas

- **Mais portais do Brasil** (pedido do usuário em 2026-10-13): ampliar a busca nacional com outros portais
  brasileiros (ex.: InHire, Catho, Vagas.com, InfoJobs, Glassdoor). Para cada um, levantar antes se há API pública
  ou oficial, os termos de uso e o risco de bloqueio, e seguir o princípio VI (só a busca pública, sem login, pausa,
  parar no primeiro bloqueio). Entra como portal na seção Portais do painel, desligado por padrão.

## Contas conectadas (spec 018)

- **MCP oficial com login**: se a Gupy (ou outro portal) lançar uma integração oficial com login (ex.: MCP com
  OAuth) que traga as candidaturas, ela substitui a leitura pela janela da ferramenta (constituição VI). Conferido em
  2026-10-17: o MCP de candidatos da Gupy não tem login nem as candidaturas.
- **Ativar o LinkedIn**: `contas/linkedin.py` está pronto e desativado. Ativar pede decisão da pessoa e uma pesquisa
  como a da Gupy e do Indeed (a API da página do Rastreador de vagas), por causa do risco de restrição da conta.
- **Mais portais na conta conectada** (ex.: InHire, Catho, Vagas.com): um módulo em `contas/` por portal, em spec
  própria, com análise de risco.
- **Gupy sem login a cada reinício do dashboard**: a Gupy esquece o login quando a janela fecha, então a janela fica
  aberta enquanto o dashboard roda (decisão de 2026-10-18). Se a Gupy um dia lembrar a sessão, voltar a fechar a
  janela depois de cada leitura.

## Candidatura assistida (spec 027)

- **Senha no Gerenciador de Credenciais do Windows** em vez do `.env` (texto puro): exige `ctypes` com a API do
  Windows (CredRead/CredWrite) ou uma dependência; manter o `.env` como alternativa no macOS e no Linux.
- **Termos de candidato da Gupy**: em 2026-10-23 as páginas de termos deram 404; conferir o "Aviso de Privacidade …
  para Pessoas Candidatas" e o suporte de candidatos. Se proibirem automação, a Gupy vai para os bloqueados.
- **Seletores próprios dos portais** (listas feitas com `div`, `role=combobox`): hoje ficam com a pessoa. Ajustar por
  portal depois da prova real.
- **Formulário dentro de iframe** (ex.: Greenhouse embutido no site da empresa): hoje só a página principal é lida;
  a pessoa pode abrir o endereço do iframe direto na janela.
- **"Atualizar candidaturas" no meio de uma candidatura** navega a aba da janela para a área do portal: abrir a
  leitura numa aba própria.

## Divulgação

- **Site do projeto no GitHub Pages** (`soumarcel.github.io/meu-proximo-trampo`, pasta `docs/` na master): página de
  apresentação, instalação e "Apoie o projeto", e talvez o dashboard em modo demonstração com vagas fictícias. A
  ferramenta em si não roda no Pages (precisa de Python e guarda dados pessoais no computador).
