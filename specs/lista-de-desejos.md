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

## Faixa salarial (spec 028)

- **Novo CAGED** (dado oficial: salário de admissão por ocupação e estado): os microdados são arquivos mensais
  grandes em 7z, o que exige uma dependência (py7zr) e uma tabela de cargo → CBO. Fica como spec própria.
- **Glassdoor**: em 2026-10-23 o site recusou acesso automatizado (403) e a API pública de parceiros não está
  disponível. Se houver uma integração oficial, ela pode entrar como fonte.

## Divulgação

- **Site do projeto no GitHub Pages** (`soumarcel.github.io/meu-proximo-trampo`, pasta `docs/` na master): página de
  apresentação, instalação e "Apoie o projeto", e talvez o dashboard em modo demonstração com vagas fictícias. A
  ferramenta em si não roda no Pages (precisa de Python e guarda dados pessoais no computador).
