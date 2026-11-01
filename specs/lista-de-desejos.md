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
  brasileiros (ex.: InHire, Catho, Glassdoor; InfoJobs e Vagas.com já entraram, specs 026 e 029). Cada um segue o
  roteiro `docs/novo-portal.md`: a pesquisa (API oficial, robots.txt, termos de uso, login, formato da lista) e as
  decisões na spec, inclusive se entra ligado ou desligado por padrão (princípio VI). O Glassdoor recusou acesso
  automatizado (403) em 2026-10-23, na pesquisa da faixa salarial.

- **Greenhouse como portal, com busca por cargo** (pesquisa de 2026-10-25, specs 030 e 031): **feito na spec 041**
  (2026-11-01), como portal com login: a pessoa conecta o MyGreenhouse Jobs na janela da ferramenta, e a busca da
  página o lê, com a emenda 5.3.0 da constituição ("Busca com login"). O registro original segue abaixo. A única busca
  do Greenhouse entre empresas, o MyGreenhouse Jobs, exige login (sem sessão, `my.greenhouse.io/jobs` leva a
  `/users/sign_in`), não tem API documentada e só mostra as empresas que aderiram. A API pública de vagas responde
  empresa por empresa, e isso já é usado nas empresas acompanhadas (que a spec 031 levou também para a busca nacional).
  Ler essa busca pela janela da ferramenta, com o login feito pela pessoa, ou com a credencial do `.env`, exigiria
  emenda da constituição (a conta conectada cobre só a área da própria pessoa) e leria uma busca interna que pode mudar
  sem aviso. Rever se a Greenhouse publicar uma busca pública ou uma API de busca.

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
- **Seletores próprios dos portais**: as listas com busca do tipo react-select (`role=combobox`, ex.: Greenhouse) são
  preenchidas desde 2026-10-24. Outros seletores feitos com `div`, sem `role=combobox`, ainda ficam com a pessoa:
  ajustar por portal quando aparecerem.
- **Formulário dentro de iframe** (ex.: Greenhouse embutido no site da empresa): hoje só a página principal é lida;
  a pessoa pode abrir o endereço do iframe direto na janela.

## Materiais do perfil (spec 037)

- **OCR fora do Windows**: hoje só o Windows lê PDF que é só imagem (OCR do sistema, pelo PowerShell).
  - **macOS**: pelo Vision, que já vem no sistema.
  - **Linux**: com o Tesseract, se a pessoa tiver instalado.

  Nos dois, sem dependência obrigatória e com a mesma saída de `ocr.ler_pdf`.
- **Imagem solta** (JPG, PNG) como material: a mesma leitura do OCR, sem precisar converter em PDF.

## Faixa salarial (spec 028)

- **Novo CAGED** (dado oficial: salário de admissão por ocupação e estado): os microdados são arquivos mensais
  grandes em 7z, o que exige uma dependência (py7zr) e uma tabela de cargo → CBO. Fica como spec própria.
- **Glassdoor**: em 2026-10-23 o site recusou acesso automatizado (403) e a API pública de parceiros não está
  disponível. Se houver uma integração oficial, ela pode entrar como fonte.

## Divulgação

- **Site do projeto no GitHub Pages** (`soumarcel.github.io/meu-proximo-trampo`, pasta `docs/` na master): página de
  apresentação, instalação e "Apoie o projeto", e talvez o dashboard em modo demonstração com vagas fictícias. A
  ferramenta em si não roda no Pages (precisa de Python e guarda dados pessoais no computador).
