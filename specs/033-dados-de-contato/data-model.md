# Data Model: Dados de contato na candidatura assistida, sem IA

## Dados de contato (`dash/dados/contato.json`, fora do Git)

| Campo | Regra |
|---|---|
| `nome` | texto, até 200 |
| `sobrenome` | texto, até 200 |
| `email` | formato `a@b.c` |
| `telefone` | texto, até 40, como a pessoa digitou |
| `cidade`, `estado`, `pais` | texto; `pais` em português (ex.: "Brasil") |
| `linkedin` | contém `linkedin.com/` |
| `portfolio` | `http(s)://…` ou um domínio |
| `endereco`, `cep` | opcionais |

**Regras**:
- campo vazio não é gravado;
- valor com cara de CPF, RG ou data de nascimento é recusado, com a mensagem de qual campo;
- o arquivo só é escrito quando a pessoa salva; "Apagar" remove o arquivo.

**Valor derivado (não gravado)**: `nome_completo` = `nome` + " " + `sobrenome`.

## Proposta (memória, não gravada)

```json
{"dados": {"nome": "…", "sobrenome": "…", "email": "…", "telefone": "…", "linkedin": "…",
           "cidade": "…", "estado": "…", "pais": "…"},
 "fontes": {"nome": "currículo", "email": "currículo", "cidade": "filtros da busca", "telefone": "respostas anteriores"},
 "avisos": ["o currículo traz 2 e-mails; ficou o primeiro"]}
```

## Reconhecimento de um campo (resultado de `contato.reconhecer`)

Um dos nomes `nome`, `sobrenome`, `nome_completo`, `email`, `telefone`, `cidade`, `estado`, `pais`, `cep`,
`endereco`, `linkedin`, `portfolio`, ou `None` quando não reconhece ou quando o campo é `sensivel`.

## Item preenchido (em `preencher_pagina`)

`{chave, rotulo, texto, fonte: "seus dados de contato", conferir: []}`, no mesmo formato dos itens da memória
("sua resposta anterior") e da IA ("seu perfil").
