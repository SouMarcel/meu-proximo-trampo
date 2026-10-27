# Research: Dados de contato na candidatura assistida, sem IA

**Data**: 2026-10-28. Leitura do código e dos testes reais de 27/10 (FullStack e JazzHR). Nenhuma consulta externa.

## R1. Como os dados de contato são preenchidos hoje

- **Classificação** (`candidatura/formulario.classificar_campo`): nome, sobrenome, e-mail, telefone, endereço, link
  etc. são marcados como `cadastro`. Os critérios são o tipo do campo (`email`, `tel`, `url`), o texto da pergunta
  (`CADASTRO`) ou o atributo `autocomplete` (`AUTOCOMPLETE_CADASTRO`). Esses campos **nunca vão à IA**.
- **Preenchimento** (`candidatura/auto.preencher_pagina`): um campo `cadastro` só recebe valor da **memória**
  (`dash/dados/respostas_formulario.json`), que guarda as respostas que a pessoa já deu. Sem memória, vira pergunta.
- **O casamento com a memória é pelo texto exato da pergunta**, normalizado (`memoria.chave`: sem acento, minúsculas,
  sem pontuação). "First Name*" serve para "First name", mas não para "Nome", "Given name" ou "Full name".
- **A leitura da página** (`formulario.ler`) já traz de cada campo `tipo_html`, `nome` (atributo `name`),
  `autocomplete` e `limite` (tamanho máximo).

## R2. O que a memória tem hoje (usuário, 27/10)

São 9 respostas, quase todas de contato, da candidatura de teste no JazzHR:
- First Name, Last Name, Email Address, Phone;
- Address, City, Postal;
- 2 sensíveis (veterano e deficiência).

## R3. De onde tirar os dados sem a pessoa digitar tudo

- **Currículo base**: `banco.curriculos_base()` aponta o arquivo base por idioma (ex.: o PDF em `anexos/`).
  - `primeiros_passos.extrair(caminho)` lê PDF (pypdf, já instalado pelo `iniciar.py`) e DOCX.
  - `primeiros_passos.reconhecer_contato(texto)` devolve `emails`, `telefones` e o `linkedin`.
  - CPF, RG e data de nascimento já saem mascarados (`mascarar_documentos`).
  - O nome costuma ser a primeira linha do currículo.
- **Memória** (R2): respostas como "First Name" e "Email Address" servem de proposta.
- **Filtros da busca**: `config.json` → `localidade` (`pais`, `estado`, `cidade`) é a cidade da pessoa. Serve de
  proposta para cidade, estado e país.

## R4. Como reconhecer o campo pelo sentido

- **`autocomplete` (padrão HTML)**:
  - `given-name`, `family-name`, `name`;
  - `email`, `tel`, `tel-national`;
  - `address-line1`, `address-level2` (cidade), `address-level1` (estado), `postal-code`;
  - `country` e `country-name`;
  - `url`.

  Muitos formulários de candidatura (Greenhouse, Lever, JazzHR) usam esses valores.
- **Tipo do campo**: `email`, `tel`; `url` com "linkedin" no texto ou no `name`.
- **Sinônimos** (sem acento, PT e EN):
  - "nome" / "primeiro nome" / "first name" / "given name";
  - "sobrenome" / "last name" / "family name" / "surname";
  - "nome completo" / "full name" / "your name" / "name";
  - "e-mail" / "email" / "email address";
  - "telefone" / "celular" / "whatsapp" / "phone" / "mobile";
  - "cidade" / "city", "estado" / "state" / "province", "país" / "country";
  - "cep" / "postal" / "zip", "endereço" / "address";
  - "linkedin", "portfólio" / "portfolio" / "site" / "website" / "github".
