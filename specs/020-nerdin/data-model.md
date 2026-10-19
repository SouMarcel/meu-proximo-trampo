# Data Model: Nerdin na busca de vagas

Nenhuma tabela nova nem campo novo. A Nerdin usa o formato comum das fontes (`fontes/__init__.py`).

## Vaga da Nerdin (formato comum)

| Campo | Origem | Regra |
|---|---|---|
| `id` | número no fim do link | `nerdin-<número>` (`_comum.ident`); igual na busca e no Adicionar Vaga |
| `plataforma` | fixo | `"Nerdin"` (entra em `banco.PLATAFORMAS`) |
| `titulo` | `h3.vaga-titulo` | sem o selo "Nova" e o ícone de urgente; espaços normalizados |
| `empresa` | `span.vaga-empresa-nome` | vazio → "Empresa não informada" |
| `local` | `div.vaga-local-linha span` | "São Paulo • SP" → "São Paulo, SP"; "Home Office" → "Remoto"; ausente → "" |
| `remoto` | linha de resumo ou local | `True` com "Home Office" |
| `modelo_trabalho` | linha de resumo | `remoto`, `hibrido`, `presencial`; ausente quando o card não diz |
| `tipo_emprego` | linha de resumo | lista com `tempo_integral` (CLT), `pj` (PJ, Freelancer), `estagio`, `temporario`; vazia quando não diz |
| `tipo` | linha de resumo | o texto como veio (ex.: "PJ • Senior • Home Office") |
| `salario` | `div.vaga-salario-destaque span` | `None` se ausente ou "a combinar" |
| `publicada_em` | `time[datetime]` | AAAA-MM-DD |
| `url` | `data-href` | `https://www.nerdin.com.br/vaga_emprego/vaga-<slug>-<n>.php` |
| `url_candidatura` | — | `None` (a candidatura é na própria página da vaga) |
| `descricao` | página da vaga (JSON-LD) | vazia na busca; preenchida por `descrever()` para as candidatas |

## Lista do cargo (memória da busca)

`_estado["listas"][termo] = (vagas, erro)`: as vagas lidas das páginas do cargo (sem filtro de consulta) e o erro
da leitura, se houve. Zerada a cada busca por `_comum.esquecer()`.

## Estado da fonte na busca

`_estado = {"bloqueado": bool, "ultimo": monotonic | None, "listas": {...}}`. `bloqueado` vira `True` no primeiro
403/429/503 e faz `buscar` devolver `([], [])` e `descrever` devolver o texto que a vaga já tinha. Zerado por
`_comum.esquecer()` (exceto `ultimo`, que mantém a pausa entre buscas seguidas).

## Configuração

`config.json` → `fontes`: sem mudança de formato. Sem a chave, vale `filtros.FONTES_PADRAO` = `["indeed", "gupy",
"nerdin"]`.
