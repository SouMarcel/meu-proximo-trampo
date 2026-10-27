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

## Decisões técnicas (plano, 28/10/2026)

### D1. Onde fica
- **Decisão**: `candidatura/contato.py` e `dash/dados/contato.json`, ao lado de `memoria.py` e
  `respostas_formulario.json`.
- **Motivo**: a memória guarda a resposta de uma pergunta específica; os dados de contato servem a qualquer pergunta
  com o mesmo sentido.
- **Alternativa**: guardar no `perfil.md`. Ele vai para a IA, e estes dados não podem ir.

### D2. Reconhecimento (conservador)
A ordem é:
1. **`autocomplete`**:
   - `given-name` → nome; `family-name` → sobrenome; `name` → nome completo;
   - `email`; `tel`/`tel-national` → telefone;
   - `address-level2` → cidade; `address-level1` → estado; `country`/`country-name` → país;
   - `postal-code` → CEP; `address-line1`/`street-address` → endereço;
   - `url` → portfólio, ou LinkedIn se a pergunta falar de LinkedIn.
2. **Tipo do campo**: `email` → e-mail; `tel` → telefone; `url` → LinkedIn ou portfólio, pela pergunta.
3. **Sinônimos**: a pergunta inteira, normalizada e sem "obrigatório", "required", "optional" e `*`, precisa bater com
   um sinônimo (R4). "Nome da empresa anterior" não vira nome. O atributo `name` do campo (ex.: `first_name`) também
   conta.
- **Campo `sensivel`** (cidadania, país de residência legal etc.) nunca é preenchido com dado de contato.

### D3. Proposta
- **Do currículo base** (`curriculo_base.marcados()`, pt e depois en), lido por `primeiros_passos.extrair`:
  - e-mail, telefone e LinkedIn por `reconhecer_contato`;
  - nome pela primeira linha que tenha de 2 a 6 palavras, só letras, até 60 caracteres e sem "@". O primeiro nome vai
    para nome, e o resto para sobrenome.
- **Da memória**, pelas chaves conhecidas (`first name`, `last name`, `email address`, `phone`, `city`, `postal`,
  `address` e os sinônimos em português), quando o currículo não trouxe.
- **Dos filtros da busca** (`localidade`): cidade, estado e país.
- A resposta diz a fonte de cada valor ("currículo", "respostas anteriores", "filtros da busca") e não grava nada.

### D4. Validação ao salvar
- Textos de até 200 caracteres.
- E-mail no formato `a@b.c`.
- LinkedIn com `linkedin.com/`.
- Portfólio começando com `http(s)://` ou parecendo um domínio.
- Valor que pareça CPF, RG ou data de nascimento (as mesmas expressões de `primeiros_passos`) é recusado.
- Campo vazio não é gravado.

### D5. Formato no preenchimento
- **Texto**: o valor salvo. Nome completo é `nome + " " + sobrenome`.
- **Lista de país ou estado**: a opção cujo texto normalizado bate com o valor ou com o nome em inglês do país
  (`filtros.PAISES`), ou, no estado, com a sigla ou o nome (`_comum.UFS`). Sem opção que bata, o campo fica com a
  pessoa.

### D6. Ordem em `preencher_pagina`
- Dados de contato → memória → IA.
- O passo novo usa `formulario.preencher(..., da_pessoa=True)`, que já é o caminho das respostas da pessoa (pode
  preencher `cadastro`).
- Os campos preenchidos saem dos passos seguintes.
