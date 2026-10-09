# Data Model: Buscar vagas pela página

Tudo local e fora do Git.

## Busca em andamento (memória do servidor; `dash/buscador.py`)

| Campo | Regra |
|---|---|
| `situacao` | `ociosa`, `consultando`, `descricoes`, `gravando`, `concluida`, `cancelando`, `cancelada`, `falha`, `interrompida`, `externa` (busca do terminal ou do chat em andamento, vista pela trava) |
| `origem` | `pagina` (a busca deste servidor) ou `terminal` (vista pela trava) |
| `inicio`, `fim` | data e hora ISO |
| `consulta` | `{portal, cargo, grupo}` da consulta em andamento |
| `feitas`, `total` | consultas concluídas e previstas |
| `encontradas` | vagas distintas até agora |
| `descricoes` | `{lidas, total}` quando o portal lê a descrição à parte |
| `com_nota` | se as vagas novas vão para a IA |
| `resumo` | no fim: `{brutas, novas, fora_criterios, ja_vistas, excluidas_titulo, fora_da_janela, busca_id}` |
| `erros` | mensagens dos portais (até 20) |
| `mensagem` | texto para a pessoa em `falha` (ex.: falta biblioteca, todos os portais falharam) |

Transições: `ociosa → consultando → descricoes → gravando → concluida`; de `consultando` ou
`descricoes` → `cancelando → cancelada` (nada gravado); qualquer etapa → `falha` (nada gravado,
exceto quando a falha é só na análise, que não muda a busca); servidor fechado → `interrompida`
(visto no próximo início pelo `busca.json`).

## Registro da última busca (`.cache/busca.json`)

`{origem, inicio, situacao, fim, pid}`, escrito por quem segura a trava (página ou terminal) ao
começar (`rodando`) e ao terminar (`concluida`, `falha` quando nenhum portal respondeu, `cancelada`, `erro` quando
faltou biblioteca ou deu erro inesperado). `rodando` com a trava livre = `interrompida`. Base do
intervalo mínimo (só `concluida` e `falha` contam).

## Trava (`.cache/busca.trava`)

Arquivo travado pelo sistema operacional enquanto alguém consulta os portais. Sem conteúdo útil.

## Candidatas da página (`.cache/pagina/candidatas.json`, `candidatas.md`)

Mesmo formato do `.cache/candidatas.json` do terminal, em pasta própria.

## Registro de busca no banco (tabela `buscas`, já existe)

Ganha `origem` (`pagina` ou `terminal`) e `situacao` (`concluida`). Só buscas gravadas entram no
banco; cancelada, interrompida e falha ficam só no `busca.json` e na página.

## Vaga (já existe)

Sem campo novo. Busca da página com nota: `analise_status: "pendente"` (a análise automática dá a
nota); sem nota: `sem_analise`, como o `--gravar` de hoje.
