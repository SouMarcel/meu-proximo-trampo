# Research: Informações básicas e idiomas com nível

## R1. A pergunta de idiomas continua `tipo: "lista"`

- **Decision**: a pergunta continua `tipo: "lista"` e ganha três campos opcionais:
  - `idiomas`: as opções de idioma;
  - `niveis`: `[{valor, rotulo, descricao}]`;
  - `linhas`: as respostas já dadas, convertidas.

  A página nova reconhece a pergunta pelos campos `niveis` e `idiomas`.
- **Rationale**:
  - O backend chega à `master` antes do PR do front, que é aberto pela Action. Nesse intervalo, a página antiga mostra
    a mesma caixa de texto de hoje e grava a lista de textos.
  - O formato gravado continua uma lista de textos, o mesmo que a montagem do perfil, o diagnóstico e a skill de chat
    já usam.
- **Alternatives considered**:
  - **`tipo: "idiomas"` novo**: na página antiga, a pergunta ficaria sem campo nenhum.
  - **Gravar objetos `{idioma, nivel}`**: mudaria a montagem do perfil e o progresso já salvo, sem ganho para a
    pessoa.

## R2. As listas e a conversão ficam no Python

- **Decision**:
  - `IDIOMAS_PERFIL`, `NIVEIS_IDIOMA` e `ler_idioma(s)` ficam em `primeiros_passos.py`;
  - `perguntas_para` põe na pergunta as `linhas` já convertidas;
  - a página só desenha as linhas, confere e monta o texto `"{idioma} — {rotulo do nível}"`. O `rotulo` vem pronto
    do backend, ex.: `B2 (Intermediário superior)` ou `Nativo`.
- **Rationale**:
  - O front não tem testes automáticos, e a constituição pede `unittest` para função pura nova.
  - O formato do texto fica num lugar só: o rótulo vem do backend, e a conversão de volta é testada no Python.
- **Alternatives considered**:
  - **Conversão em TypeScript**: ficaria sem teste e com a regra em dois lugares.

## R3. Conversão das respostas antigas sem estimar nível

- **Decision**:
  - **Idioma**: o texto antes do primeiro separador (`—`, `–`, ` - `, `:`, `(`, `,`) é comparado sem acento e sem
    maiúsculas com sinônimos:
    - ingles/english;
    - portugues/portuguese/portugues brasileiro;
    - frances/french/francais;
    - alemao/german/deutsch;
    - espanhol/spanish/castelhano/espanol.

    "Português" com "Portugal" ou "europeu" vira Outro, para não virar BR à força. Sem sinônimo, a linha vira Outro,
    com o nome como a pessoa escreveu.
  - **Nível**: a sigla `A1`…`C2` como palavra solta vira o nível; `nativo`, `nativa`, `native` ou `língua materna`
    viram Nativo. Qualquer outra palavra (fluente, avançado, Professional Working, Elementary) deixa o nível em branco
    e guarda o texto original em `original`, que a página mostra ("você tinha escrito: …").
- **Rationale**: constituição IV (níveis nunca estimados). Uma escala como "Professional Working" ou "fluente" não tem
  equivalência exata no CEFR; quem escolhe é a pessoa.
- **Alternatives considered**:
  - **Usar `NIVEL_INGLES` de `analise_perfil`**: a tabela daria um nível para "fluente". Ela serve para classificar a
    prontidão, não para escrever no perfil em nome da pessoa.

## R4. A resposta antiga "Qual o seu nível de inglês?"

- **Decision**: a pergunta sai de `PERGUNTAS`, e `"ingles"` fica em `IDS` como id antigo, aceito pela validação. Na
  montagem do perfil, a linha "Inglês (nível declarado)" só entra quando nenhuma linha da lista é inglês com nível do
  formato novo (sigla CEFR ou Nativo).
- **Rationale**:
  - Quem não refez a pergunta não perde o nível declarado.
  - Quem refez fica com o inglês uma vez só.
  - `analise_perfil._nivel_ingles` lê todas as linhas, e o formato novo já é reconhecido: B1 é intermediário, B2 é
    avançado, C1 e C2 são fluente e Nativo é nativo.
- **Alternatives considered**:
  - **Apagar `respostas.ingles` do progresso**: mexe em dado da pessoa sem clique.
  - **Sumir sempre que houver "Inglês" na lista**: tiraria o nível de quem escreveu só "Inglês", sem nível.

## R5. Validação da lista na página

- **Decision**: a página impede a Próxima, com um aviso que nomeia a linha, quando:
  - há idioma sem nível;
  - "Outro" está sem nome;
  - o mesmo idioma se repete. A comparação é sem acento e sem maiúsculas, e "Outro: português" conta igual a
    Português (BR).

  Linhas totalmente vazias são ignoradas. Lista vazia equivale a Pular. O backend não valida o formato: aceita
  qualquer texto, como hoje, porque a skill de chat e a página antiga continuam gravando texto livre.
- **Rationale**: o erro aparece onde a pessoa pode corrigir, sem quebrar os outros caminhos.

## R6. Onde fica cada bloco

- **Decision**:
  - **Informações básicas**: dados de contato, respostas guardadas e sites. Fica no `MeuPerfil` como tela `basicas`,
    com o botão sempre visível depois dos passos e antes de "Currículo base". A tela não salva o progresso do perfil
    (como `analises` e `curriculos`) e não mostra Recomeçar.
  - **"Atualizar candidaturas"**: portais, login guardado e leitura. A linha "Seus dados de contato, respostas
    guardadas e sites da candidatura assistida ficam em Meu perfil → Informações básicas" ganha o botão "Abrir", que
    fecha o diálogo e abre o Meu perfil nessa tela (`App`: `perfilAberto = {tela: "basicas"}`).
  - Os dois blocos leem `GET /api/candidatura`, que já devolve tudo. Não há rota nova.
- **Rationale**: o pedido do usuário, com as decisões 1 e 2 da spec. Um clique leva de um lugar ao outro.

## R7. Fora de outro aparelho

- **Decision**: com `so` (só leitura) no Meu perfil, a aba mostra "Só dá para ver e mudar estes dados no computador
  onde a ferramenta roda." e não chama a rota. Sem `so`, um 403 da rota mostra o mesmo texto.
- **Rationale**: a rota já responde 403 fora deste computador (`SO_LOCAL_PERFIL`). A aba só traduz a resposta.
