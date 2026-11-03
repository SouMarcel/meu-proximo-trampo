# Data Model: O que as vagas pedem

## 1. Campo `requisitos` da vaga

Vai no documento da vaga, no banco SQLite com documentos JSON. É um campo novo, sem migração. Sem o campo, os
requisitos ainda não foram lidos.

```json
"requisitos": {
  "habilidades": [{"nome": "Gestão de projetos", "tipo": "tecnica", "exigida": true}],
  "certificacoes": [{"nome": "PMP", "tipo": "certificacao", "exigida": false}],
  "experiencia": {"anos": 5, "em": "gestão de projetos", "frase": "5+ anos de experiência em gestão de projetos"},
  "formacao": {"nivel": "graduacao", "areas": ["Administração", "Engenharia"], "frase": "Graduação em Administração ou Engenharia"},
  "idiomas": [{"idioma": "Espanhol", "nivel": "intermediario", "frase": "espanhol intermediário"}],
  "lido_em": "2026-11-03",
  "provedor": "gemini",
  "modelo": "gemini-2.5-flash"
}
```

| Campo | Regra de validação (`requisitos.validar`) |
|---|---|
| `habilidades` | lista, até 30 itens. Item: `nome` de 1 a 60 caracteres, depois de tirar espaços; `tipo` `tecnica` ou `comportamental` (outro valor vira `tecnica`); `exigida` booleano (ausente = `false`). Sai o item cujo nome começa por tempo ou experiência ("5 anos", "anos de", "experiência", "vivência", "conhecimento em", "years", "experience") ou que é nome de idioma (research D2). Itens com a mesma chave (D7) ficam uma vez, e vale `exigida` se algum for. |
| `certificacoes` | lista, até 15 itens. Item: `nome` de 1 a 80 caracteres; `tipo` `certificacao` ou `curso` (outro valor vira `curso`); `exigida` booleano. Os mesmos cortes das habilidades. |
| `experiencia` | objeto ou ausente. `anos`: inteiro de 0 a 40, ou `null` quando a vaga fala de experiência sem número; `em`: até 80 caracteres; `frase`: até 200. Sem `anos` e sem `frase`, o objeto sai. |
| `formacao` | objeto ou ausente. `nivel`: `tecnico`, `graduacao`, `pos`, `mestrado` ou `doutorado` (outro valor tira o objeto); `areas`: até 5 nomes de até 60 caracteres; `frase`: até 200. |
| `idiomas` | lista, até 6 itens. Item: `idioma`, nome em português de 1 a 30 caracteres; `nivel` `basico`, `intermediario`, `fluente` ou `nativo` ("avancado" vira `fluente`; outro valor tira o item); `frase` até 200. Um item por idioma, com o maior nível pedido. |
| `lido_em` | `AAAA-MM-DD`, posto na gravação. |
| `provedor`, `modelo` | qual IA leu: o mesmo formato de `analise_provedor` e `analise_modelo`. Vazio quando quem leu foi o assistente do chat. |

- **Gravação na análise** (`banco.validar_analise`): quando a análise traz `requisitos`, o campo é validado e gravado
  com a IA da análise e a data. Um campo inválido é cortado e não derruba a nota.
- **Gravação avulsa** (`banco.aplicar_requisitos(lista)`): cada item `{"id", "requisitos"}` troca só `requisitos` e
  `atualizada_em`, sem `aplicar_criterios`, sem mexer na nota, na triagem ou na etapa (FR-005). Devolve
  `(ids gravados, problemas)`.
- **Reanálise:** a análise nova troca o campo inteiro.

## 2. Seleção

| Campo | Valores | Padrão |
|---|---|---|
| `vagas` | `aplicacoes` (regra `noQuadro`, research D6) ou `todas` (`analise_status` "feita") | `aplicacoes` |
| `area` | `todas`, `nacional` ou `internacional` (regra `areaDe`, D6) | `todas` |

A página guarda a seleção em `localStorage`, na chave `mpt_pref_metricas_requisitos`, como `{"vagas", "area"}`. Um
valor que não está na tabela volta ao padrão.

## 3. Resumo (`requisitos.resumo`)

É o que `GET /api/requisitos` devolve e o que `PY dash/requisitos.py resumo --json` imprime. Os itens dizem `ids` (as
vagas que pedem), para a página abrir a lista (FR-019).

```json
{
  "selecao": {"vagas": "aplicacoes", "area": "todas"},
  "contagem": {"selecao": 40, "com_requisitos": 30, "a_ler": 2, "sem_texto": 7, "sem_analise": 1},
  "poucas": false,
  "habilidades": {
    "base": 30,
    "tecnicas": [{"nome": "SQL", "chave": "sql", "vagas": 12, "exigida": 9, "parte": 0.4,
                  "perfil": "habilidade", "ids": ["…"]}],
    "comportamentais": []
  },
  "certificacoes": {"base": 30, "itens": [{"nome": "PMP", "tipo": "certificacao", "vagas": 4, "exigida": 1,
                                           "parte": 0.133, "perfil": "nao", "ids": ["…"]}]},
  "experiencia": {"base": 30, "destaque": "4a5",
                  "faixas": [{"faixa": "ate1", "rotulo": "Até 1 ano", "vagas": 2, "ids": ["…"]}, "…",
                             {"faixa": "nao_diz", "rotulo": "Não diz", "vagas": 8, "ids": ["…"]}]},
  "formacao": {"base": 30, "niveis": [{"nivel": "graduacao", "rotulo": "Graduação", "vagas": 18, "ids": ["…"]}, "…"],
               "areas": [{"nome": "Administração", "vagas": 6, "ids": ["…"]}]},
  "idiomas": {"base": 31, "itens": [{"idioma": "Inglês", "vagas": 20, "ids": ["…"],
                                     "niveis": [{"nivel": "fluente", "rotulo": "Fluente", "vagas": 9, "ids": ["…"]}]}]},
  "senioridade": {"base": 35, "itens": [{"valor": "pleno", "rotulo": "Pleno", "vagas": 14, "ids": ["…"]}]},
  "modelo": {"base": 35, "itens": [{"valor": "remoto", "rotulo": "Remoto", "vagas": 20, "ids": ["…"]}]},
  "contratacao": {"base": 35, "itens": [{"valor": "clt", "rotulo": "CLT", "vagas": 10, "ids": ["…"]}]},
  "suas": {
    "existe_perfil": true, "tem_secao": true,
    "habilidades": [{"linha": "Jira", "nivel": "avançado", "vagas": 20, "destaque": true, "ids": ["…"]}],
    "certificacoes": [{"linha": "PSM I", "nivel": "em preparação", "vagas": 3, "destaque": true, "ids": ["…"]}],
    "aparecem": 8, "total": 14
  },
  "leitura": {"rodando": false, "lidas": 0, "total": 0, "parada": false, "erro": null},
  "ia": {"ligada": true, "nome": "Gemini · gemini-2.5-flash"}
}
```

| Campo | Regra |
|---|---|
| `contagem.selecao` | as vagas da seleção (D6). |
| `contagem.com_requisitos` | as vagas da seleção com `requisitos`. |
| `contagem.a_ler` | análise feita, texto, sem `descricao_pendente` e sem `requisitos`: o que o botão lê. |
| `contagem.sem_texto` | sem texto do anúncio ou com `descricao_pendente`. |
| `contagem.sem_analise` | com texto, mas ainda sem a análise feita: a análise automática traz os requisitos. |
| `poucas` | `com_requisitos` entre 1 e 4 (edge case "seleção com poucas vagas"). |
| `parte` | `vagas / base`, com 3 casas. |
| `perfil` | `habilidade` (ou `certificacao`, nas certificações), `citada` ou `nao` (D7). |
| ordem das listas | as que têm mais vagas primeiro, depois as mais exigidas, depois o nome. Cada lista mostra tudo, e a página exibe 15 e "Ver todas". |
| `experiencia.faixas` | `ate1` (0 e 1), `2a3`, `4a5`, `6a9`, `10mais` e `nao_diz`, nessa ordem. `destaque` é a maior fora de `nao_diz`; empatando, a menor faixa; `null` sem vagas. |
| `formacao.niveis` | `tecnico`, `graduacao`, `pos`, `mestrado`, `doutorado` e `nao_diz`, nessa ordem. |
| `idiomas.base` | vagas com `requisitos` ou com `ingles` (fora `nao_pede`). |
| `senioridade`, `modelo`, `contratacao` | `base` = as vagas da seleção com análise feita. Cada vaga conta uma vez por valor. `modelo` sem `nao_informado`. |
| `suas.habilidades` | as linhas das seções de habilidades (D8), na ordem das que mais vagas pedem; zeros no fim, na ordem do perfil. `destaque` = entre as 5 primeiras com `vagas` > 0. |
| `suas.aparecem`, `suas.total` | quantas linhas de habilidade têm `vagas` > 0, e quantas existem. |
| `suas.tem_secao` | `false` quando o perfil não tem seção de habilidades (FR-018). |

## 4. Estado da leitura (`Leitura.estado()`)

| Campo | Significado |
|---|---|
| `rodando` | há uma leitura em andamento. |
| `lidas`, `total` | as vagas gravadas nesta leitura, e quantas ela ia ler. |
| `parada` | a pessoa clicou em Parar, e a leitura terminou o lote e parou. |
| `erro` | `{motivo, em}` da falha que parou a leitura, sem chave; `null` quando não houve falha. |
| `selecao` | a seleção que a leitura está lendo. |
