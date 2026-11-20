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
  automatizado (403) em 2026-10-23, na pesquisa da faixa salarial. O bloco "Próximos a mapear" do painel (spec 043)
  mostra esta lista, pela constante `filtros.PORTAIS_A_MAPEAR`: atualize as duas juntas.

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

## Currículo com resultado (spec 053)

- **Caça de números**: para cada item que a conferência marca como só de tarefa, a página faz uma pergunta curta e
  específica ("quantas pessoas?", "o que mudou depois?", "qual medida mostra isso?"). A resposta vira relato (spec
  035) e vai ao perfil pela revisão item a item (spec 050). Sem sugerir métrica nem reescrever o item com verbo mais
  forte: só pergunta o que a pessoa pode contar.
- **Marcar como visto** (pedido do usuário em 2026-11-20): na conferência do currículo, um ponto "conferir" que a
  pessoa já leu e aceitou pode ser marcado como visto e sai da lista daquele currículo. Só vale para "conferir";
  "não pronto" continua bloqueando até a correção.

## Faixa salarial (spec 028)

- **Novo CAGED** (dado oficial: salário de admissão por ocupação e estado): os microdados são arquivos mensais
  grandes em 7z, o que exige uma dependência (py7zr) e uma tabela de cargo → CBO. Fica como spec própria.
- **Glassdoor**: em 2026-10-23 o site recusou acesso automatizado (403) e a API pública de parceiros não está
  disponível. Se houver uma integração oficial, ela pode entrar como fonte.

## Busca nacional e internacional

- **Busca única, com a área da vaga pela moeda, pelo país e pelo idioma** (pedido do usuário em 2026-10-31; análise
  feita, sem spec): um clique em "Buscar vagas" procura em todos os portais, e cada vaga é separada em nacional ou
  internacional pelo que importa para a pessoa. Decisões já tomadas:
  - **área**: moeda > país > idioma. Uma vaga que paga numa moeda que não é a da pessoa é internacional. Senão, uma vaga
    com local fora do país dela também é internacional. Com local no país dela, a vaga é nacional mesmo em outro
    idioma e ganha a etiqueta "em inglês". Sem moeda nem local, o idioma decide. A moeda e o idioma da pessoa saem de
    `localidade.pais`;
  - **busca**: tudo, sempre. Sai o interruptor `internacional.ativo`, e as duas listas de portais viram uma só. O
    Indeed continua só nos países escolhidos, porque exige um país por consulta;
  - **elegibilidade**: etiquetar e avisar com "Aceita <país ou região>", "Só residentes de X" ou "⚠ Não diz". A vaga
    "Só residentes de X" vai para Fora dos critérios, como hoje;
  - **origem do portal no lugar do domínio**: o portal brasileiro (atributo `PAIS` na fonte) conta como local no
    país. O `.com.br` vale só como palpite no Adicionar Vaga por link, porque o domínio engana: a Gupy é gupy.io, e
    FullStack e Get on Board são .com e contratam na América Latina;
  - **etiqueta de país em toda vaga**: "<país da pessoa> → <país da vaga>", com "País não informado" quando ninguém
    diz o país.

  Antes da spec, rever as decisões contra as specs 044 (Vagas Internacionais) e 047 (o catálogo de regiões e a regra
  por sobreposição) e prever um comando que mostre quais vagas gravadas mudariam de área. Esse comando só grava com o
  OK da pessoa.

## Divulgação

- **Site do projeto no GitHub Pages** (`soumarcel.github.io/meu-proximo-trampo`, pasta `docs/` na master): página de
  apresentação, instalação e "Apoie o projeto", e talvez o dashboard em modo demonstração com vagas fictícias. A
  ferramenta em si não roda no Pages (precisa de Python e guarda dados pessoais no computador).
