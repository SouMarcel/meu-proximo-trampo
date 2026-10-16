# Research: Vaga publicada em post

## 1. Como ler um post público do LinkedIn sem login

- **Decision**: pedir a versão de incorporação do post, `https://www.linkedin.com/embed/feed/update/<urn>`, onde
  `<urn>` é `urn:li:activity:N`, `urn:li:share:N` ou `urn:li:ugcPost:N`. Um pedido só, sem cookies e sem seguir
  redirecionamento.
- **Rationale**: é a página que o LinkedIn oferece para incorporar um post em outros sites, feita para ser vista sem
  conta. No teste de 2026-10-16 (um pedido), um post público de página de empresa respondeu 200 com 25 KB, trazendo:
  - o texto inteiro no elemento de classe `attributed-text-segment-list__content`;
  - quem publicou num link com `data-tracking-control-name="public_post_embed_feed-actor-name"`, cujo endereço tem
    `/company/` (página de empresa) ou `/in/` (pessoa) e cujo texto é o nome;
  - `og:url` com o endereço canônico `feed/update/urn:li:activity:N`;
  - nenhum JSON-LD de vaga, por isso o leitor de hoje não serve.
- **Alternatives considered**:
  - a página `feed/update/...` direto: exige login;
  - a página `/posts/<slug>` (versão pública "SEO"): abre às vezes sem login, mas é maior, muda mais e redireciona
    para login com facilidade;
  - a API oficial de posts: exige app aprovado e login da pessoa, o que é contra o princípio VI.

## 2. Formatos de link e identificação do post

- **Decision**: `fontes/post.py` reconhece:
  - `linkedin.com/feed/update/urn:li:activity:N` (também com `?updateEntityUrn=…`);
  - `linkedin.com/posts/<slug>-activity-N-<sufixo>`;
  - `urn:li:share:N` e `urn:li:ugcPost:N` em qualquer parte do link (ex.: `feed/update/urn:li:share:N`,
    `embed/feed/update/urn:li:ugcPost:N`).

  O id da vaga é `lip-<N>` do `urn:li:activity` canônico (o `og:url` da resposta). Quando a resposta não traz o
  canônico, vale o número do link, com prefixo do tipo (`lip-s<N>`, `lip-u<N>`).
- **Rationale**: o mesmo post tem número de `activity` diferente do de `share`/`ugcPost`, e só a resposta diz o
  canônico. Antes do pedido, um id `lip-<N>` já gravado evita o pedido (link repetido). Depois do pedido, o canônico
  pega o mesmo post colado em outro formato.
- **Alternatives considered**: hash do link inteiro (não junta formatos diferentes do mesmo post).
- **Pendente na verificação**: conferir com um link real em formato `share` ou `ugcPost`, com o OK da pessoa (um
  pedido). Só o formato `activity` foi testado.

## 3. Bloqueio e espera

- **Decision**: o pedido do post usa a mesma classificação de bloqueio do LinkedIn (`fontes/linkedin._motivo`: 429
  excesso de pedidos, 999 recusa automática da rede, 3xx pediu login, 401/403 acesso negado). Ele **não** chama
  `_bloquear` (que grava a espera) e **não** consulta `espera()`. 404 e 410 viram "o post não existe mais ou não é
  público". Nada de nova tentativa.
- **Rationale**: decisão da pessoa na clarificação. É um pedido pontual, como o link de vaga do LinkedIn na spec 015.
  A espera foi feita para a busca, que faz muitos pedidos seguidos.
- **Alternatives considered**: gravar a espera (descartado pela pessoa).

## 4. Extração com IA

- **Decision**: o módulo novo `post_ia.py` monta um pedido curto para `ia.responder`. O texto vai como dado,
  delimitado, com a instrução de não seguir ordens contidas nele. A resposta é um JSON fixo (ver
  [contracts/extracao-ia.md](contracts/extracao-ia.md)), lido pelo mesmo jeito de `candidatura_ia._json`. A resposta é
  limpa no servidor:
  - tamanhos máximos dos campos do formulário;
  - e-mail e link só valem se aparecerem **literalmente** no texto (defesa contra invenção);
  - `parece_vaga` vira booleano, e `vagas` vira inteiro de 0 a 20.
- **Rationale**: a IA só preenche o formulário e a pessoa confere tudo (princípio V). A checagem literal impede que um
  e-mail ou link inventado vá para a candidatura (princípio IV).
- **Alternatives considered**:
  - regras simples (regex) para o cargo: descartadas pela pessoa;
  - mandar o perfil junto: desnecessário, porque a extração não avalia aderência e o perfil não deve sair do
    computador sem motivo (princípio I).
- **Tempo**: 120 s de limite. Passou disso, vale o caminho de reserva (item 5).

## 5. Fluxo na página: com IA, aguardar; sem IA, direto ao formulário

- **Decision** (pedido da pessoa em 2026-10-16): são duas chamadas.
  1. `POST /api/vagas/link` (a de hoje) reconhece o post, lê a página pública e responde **sem criar vaga**:
     `{"post": {...}, "parcial": {...}, "ia": {...}}`.
  2. A segunda chamada depende de haver IA:
     - **com IA** (disponível e pedido deste computador): a página mostra "Em análise pela IA (provedor · modelo),
       aguarde…" e chama `POST /api/vagas/extrair`. O formulário só abre quando a resposta chega, já preenchido;
     - **sem IA**: o formulário abre direto, com descrição, link e empresa (se o autor for página de empresa).
  3. Se a IA der erro ou passar do tempo, o formulário abre como no caso sem IA, com o motivo.

  Durante a espera, Cancelar fecha o Adicionar Vaga, como hoje. "Colar texto de post ou mensagem" abre uma caixa de
  texto; "Continuar" segue o passo 2 com o texto colado.
- **Rationale**: a pessoa prefere ver o formulário uma vez só, já completo, em vez de ver campos mudando enquanto
  digita. Sem IA não há o que esperar. A detecção de post fica num lugar só, em Python, e não é duplicada em
  JavaScript.
- **Alternatives considered**:
  - abrir o formulário na hora e deixar a IA preencher depois os campos intocados: descartado pela pessoa;
  - extrair em segundo plano e gravar: violaria "nunca grava sem o clique".

## 6. Quem pode usar a IA na extração

- **Decision**: `POST /api/vagas/extrair` vale só deste computador, como as outras rotas que chamam a IA (currículo,
  análises, entrevista). De outro aparelho da rede (`--rede`), a página não chama a extração e abre o formulário com
  o aviso "a leitura com IA só funciona no computador onde a ferramenta roda".
- **Rationale**: a IA usa a chave e a cota da pessoa. As rotas com IA já são só locais (`SO_LOCAL_PERFIL`).

## 7. E-mail de candidatura no banco e na página

- **Decision**: campos novos na vaga, sem migração:
  - `email_candidatura` (até 254 caracteres, validado com uma regex simples `nome@dominio.tld`, sem espaços);
  - `assunto_candidatura` (até 200).

  Os dois são editáveis por `PATCH /api/vagas/<id>` (`banco._validar_usuario`). No cartão expandido ficam dois
  campos acima das Anotações. O botão do rodapé passa a "Salvar" (anotações, e-mail e assunto). Com e-mail válido,
  aparece o botão "Enviar por e-mail", um link `mailto:` com `subject` codificado. O kit mostra "Candidatura por
  e-mail" e, no item "Enviar a candidatura", o mesmo link `mailto:`.
- **Rationale**: o `mailto:` só abre o programa de e-mail da pessoa; quem envia é ela (princípio V).
- **Alternatives considered**: guardar o e-mail em `url_candidatura` como `mailto:` (o campo hoje só aceita
  http/https e serve para outro fim).

## 8. Etiqueta Post e quem publicou

- **Decision**:
  - a vaga ganha `formato: "post"`, e a página mostra a etiqueta "Post" ao lado das plataformas (como `intTag`);
  - "Publicado por: [nome]" vai para `anotacao` quando o autor é pessoa;
  - a vaga de link de post entra pelo `banco.criar_manual`, que passa a aceitar `formato`, `post_id`,
    `email_candidatura`, `assunto_candidatura` e `publicado_por`. Com `post_id`, o id é `lip-…` e um id já gravado
    devolve a vaga que existe ("já estava"), como em `criar_de_link`. As regras de repetida (`achar_repetida`)
    também valem.
- **Rationale**: o formulário é o mesmo do Adicionar Vaga à mão, então a gravação usa o mesmo caminho, com os campos
  novos.

## 9. Dados de teste

- **Decision**: `tests/dados/linkedin/post.html` com a estrutura da página real (as mesmas classes e atributos), mas
  com texto, empresa, nomes e e-mail fictícios. Há também uma variante com autor pessoa.
- **Rationale**: princípio II.
