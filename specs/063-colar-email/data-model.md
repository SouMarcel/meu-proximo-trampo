# Data model: Colar e-mail (spec 063)

Nada novo é gravado em disco. As estruturas abaixo existem só na memória do servidor, entre o Ler e o Aplicar.

## E-mail lido (interno)

| Campo | Tipo | Regra |
|---|---|---|
| `indice` | int | posição da caixa (1, 2, …) |
| `texto` | str | corpo limpo (sem cabeçalhos, endereços e links; filtro de integridade aplicado) |
| `tipo` | str \| null | `recebida`, `entrevista`, `proposta`, `negativa`, `cancelada`, `desistencia`, `contratacao`; null = não reconhecido |
| `trecho` | str | frase do e-mail em que o tipo se apoia (até 240 caracteres) |
| `alerta` | dict \| null | achado do filtro de integridade (`veredito`, `contagens`, `citacoes`) |
| `por_ia` | bool | o tipo/vaga veio da IA |

## Proposta de e-mail (resposta da leitura)

Mesmo formato do item das contas (dash/API.md 3.11), com campos a mais:

| Campo | Tipo | Regra |
|---|---|---|
| `chave` | str | `email:<indice>` |
| `portal` | str | `"email"` |
| `plataforma` | str | `"E-mail"` |
| `tipo` | str | `mudar`, `quadro`, `anotar` (etapa igual/anterior ou card encerrado), `escolher` (falta a vaga), `nao_reconhecido` (falta o tipo e a vaga) |
| `vaga_id` | str \| null | null em `escolher` e `nao_reconhecido` |
| `titulo`, `empresa` | str | da vaga (vazio sem vaga) |
| `de` | `{etapa, resultado}` \| null | o card agora |
| `para` | `{etapa, resultado}` \| null | a mudança; em `anotar`, igual a `de`; null sem tipo |
| `tipo_email` | str \| null | o tipo lido |
| `rotulo` | str | "negativa", "convite para entrevista ou teste", … |
| `trecho` | str | a frase de apoio |
| `opcoes` | `[{id, titulo, empresa, etapa}]` | em `escolher`, as vagas possíveis (vazio = buscar no quadro) |
| `alerta` | dict \| null | achado do filtro de integridade |
| `por_ia` | bool | |
| `status`, `nota`, `avisos`, `data`, `url` | | compatíveis com o item das contas (`status` = rótulo; `avisos` com o aviso ⚠ quando houver) |
| `marcado` | bool | true em `mudar`, `quadro` e `anotar`; false em `escolher` e `nao_reconhecido` |

## Escolha da pessoa (Aplicar)

`{chave, vaga_id?, tipo_email?}`: `vaga_id` obrigatório quando a proposta não tem vaga; `tipo_email` obrigatório quando
não tem tipo. Nas outras propostas, ignorados se iguais; se a pessoa trocou a vaga, vale a escolha.

## Transições

`tipo_email` → `{etapa, resultado}`: recebida → aplicada; entrevista → entrevista; proposta → proposta; negativa →
encerrada/nao_aprovado; cancelada → encerrada/cancelada; desistencia → encerrada/desisti; contratacao →
encerrada/contratado. Aplicar: `contas.avancou(atual, nova)` → muda a etapa (e o resultado se encerrada) e
`etapa_em` = hoje; senão só anota. Sempre: `banco.anotar(vid, "dd/mm/aaaa — e-mail de <rótulo>: \"<trecho>\"")`.
