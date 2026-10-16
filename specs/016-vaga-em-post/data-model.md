# Data Model: Vaga publicada em post

Documentos JSON no SQLite de sempre (`dash/dados/candidaturas.db`). Os campos são novos e opcionais, e vagas antigas
seguem iguais (sem migração).

## Vaga (campos novos)

| Campo | Tipo | Regra | Onde nasce | Quem edita |
|---|---|---|---|---|
| `formato` | `"post"` ou ausente | só `"post"` é aceito | Adicionar Vaga por link de post ou por texto colado | ninguém depois |
| `email_candidatura` | texto ≤ 254 | `^[^@\s]+@[^@\s]+\.[^@\s]+$`; vazio apaga | formulário (extração ou à mão) | cartão expandido |
| `assunto_candidatura` | texto ≤ 200 | uma linha; vazio apaga | formulário | cartão expandido |

Id da vaga de link de post: `lip-<N>` (activity canônico) ou `lip-s<N>` / `lip-u<N>` (share/ugcPost sem canônico).
Combina com `banco.ID_VALIDO`. A vaga de texto colado usa o id `m-…` do Adicionar Vaga à mão.

`publicado_por` não é campo gravado: quando o autor é pessoa, entra como linha "Publicado por: [nome]" em
`anotacao`.

Os campos de hoje continuam:
- `url` é o link do post (ou o link achado no texto colado);
- `plataforma` é LinkedIn no link de post e a escolhida no texto colado;
- `descricao` é o texto inteiro, até 20.000 caracteres;
- `origem` é `"link"`, com etapa "relatorio" (vai para o Relatório de Vagas), ou `"manual"`, nas outras etapas.

## Post lido (resposta de `fontes/post.ler`, não gravado)

| Campo | Exemplo (fictício) |
|---|---|
| `id` | `lip-7000000000000000001` |
| `url` | link canônico `https://www.linkedin.com/feed/update/urn:li:activity:…` |
| `texto` | texto inteiro do post |
| `autor` | `Empresa Exemplo` |
| `autor_tipo` | `empresa`, `pessoa` ou `""` |

## Extração (resposta de `post_ia.extrair`, não gravada)

| Campo | Regra |
|---|---|
| `titulo` | ≤ 200; vazio se o texto não diz |
| `empresa` | ≤ 120 |
| `local` | ≤ 120 (cidade, "Remoto", "Híbrido SP"…) |
| `url` | http/https e presente literalmente no texto; senão vazio |
| `email_candidatura` | válido e presente literalmente no texto; senão vazio |
| `assunto_candidatura` | ≤ 200 |
| `parece_vaga` | booleano |
| `vagas` | inteiro 0–20 (quantas vagas o texto traz) |
| `provedor`, `modelo` | qual IA leu, para a tela |

## Transições

Post (link ou texto) → formulário preenchido (nada gravado) → clique em Adicionar → vaga gravada:
- com etapa "relatorio": vai para o Relatório de Vagas e a análise de aderência fica pendente (`analise_status`
  "pendente" se houver descrição);
- com outra etapa: vai direto para o quadro.
