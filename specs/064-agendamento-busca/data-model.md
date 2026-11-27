# Data Model: Busca agendada e retomada depois da espera

## Agendamento (`config.json` → `agendamento`)

| Campo | Tipo | Regra |
|---|---|---|
| `ligado` | bool | padrão `false` |
| `horario` | texto `HH:MM` | 00:00 a 23:59; padrão `"08:00"`; inválido no arquivo vira o padrão, inválido na entrada é erro |
| `continuar` | bool | "Continuar de onde parou"; padrão `false`; independe de `ligado` |

Mudar o horário depois da busca do dia já ter rodado (ou sido pulada) não roda outra no mesmo dia: a data de hoje já
consta em `agendamento.json`. Desmarcar `continuar` apaga as retomadas.

## Retomada (`.cache/retomadas.json` → `{"<nome do portal>": Retomada}`)

| Campo | Tipo | Regra |
|---|---|---|
| `portal` | texto | rótulo (`PLATAFORMA`), para a página |
| `origem_busca` | texto | origem da busca que criou (`pagina`, `terminal`, `chat`, `agendada`) |
| `criada_em` | ISO | quando nasceu; mantido nas tentativas seguintes (teto de 24 h sem agendada) |
| `proxima` | ISO | próxima tentativa: o bloqueio + 6 h; avança de 6 em 6 h quando perdida ou pulada |
| `faltaram` | lista de consultas | as consultas do portal que não rodaram (dicionários de `filtros.consultas`); pode ser vazia |
| `tentativas` | int | retomadas já feitas |
| `ultimo_motivo` | texto | o bloqueio mais recente (ex.: "excesso de pedidos") |

As descrições pendentes são contadas na hora pelo banco (`banco.pendentes_de_descricao(portal)`), não guardadas aqui.

Transições:

```text
(bloqueio numa busca, continuar ligado) → pendente
pendente --hora devida, portal livre, nada rodando--> rodando
rodando --sem bloqueio, sem pendente--> apagada (sucesso)
rodando --sem bloqueio, pendentes pelo limite por busca--> pendente (faltaram vazio, +6 h)
rodando --bloqueou de novo--> pendente (faltaram atualizado, +6 h, tentativas+1)
pendente --hora devida, portal em espera--> pendente (+6 h, "pulada")
pendente --servidor desligado na hora (passou 15 min)--> pendente (+6 h até o futuro, "perdida")
pendente --busca agendada rodou / busca manual incluiu o portal--> apagada (substituída) [ou recriada se ela bloquear]
pendente --24 h desde criada_em sem agendamento ligado / caixa desmarcada / Cancelar--> apagada
```

## Execução do relógio (`.cache/agendamento.json`)

```json
{
  "dia": "2026-11-28",              // data da última busca agendada devida (rodada, pulada ou perdida)
  "historico": [                    // últimos 30 eventos, do mais novo para o mais antigo
    {"tipo": "agendada|retomada", "situacao": "rodou|pulada|perdida|falha",
     "portal": "LinkedIn",          // só na retomada
     "em": "2026-11-28T08:00:12", "motivo": "busca manual às 07:30",
     "resumo": {"novas": 4, "completadas": 12, "bloqueados": ["LinkedIn"]}}
  ]
}
```

## Histórico de buscas (`.cache/buscas-historico.json`)

Lista das últimas 20 buscas, gravada pela `TravaBusca` ao sair: `{origem, inicio, fim, situacao}` (as mesmas chaves
do `.cache/busca.json`). Base do pulo de 4 horas (R3).

## Espera do portal (`.env`)

| Variável | Unidade | Faixa | Padrão |
|---|---|---|---|
| `LINKEDIN_ESPERA`, `INFOJOBS_ESPERA`, `VAGASCOM_ESPERA`, `JOBGETHER_ESPERA`, `FULLSTACK_ESPERA`, `MYGREENHOUSE_ESPERA` | minutos | 60 a 2880 | 360 |

O arquivo `.cache/<portal>-espera.json` segue igual (`desde`, `motivo`); o fim é `desde + duração atual`.

## Resultado do `executar` (acréscimo)

`"faltaram": {"linkedin": [consulta, …]}`: só os portais com espera que bloquearam nesta busca.
`executar(..., so_consultas={"linkedin": [...]})`: com o parâmetro, só os portais da chave rodam, e só essas consultas.
