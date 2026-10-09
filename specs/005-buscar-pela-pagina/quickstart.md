# Quickstart: validar a busca pela página

Servidor da worktree subido dentro do roteiro de validação (porta 8799), com `TRAMPO_CONFIG` e
`TRAMPO_BANCO` temporários, uma **fonte falsa** no lugar dos portais (devolve vagas fictícias, com
pausa curta e um erro opcional) e o provedor de IA falso local (como nas specs 002 e 004). Nenhum
portal de verdade é consultado.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Sem cargos nos filtros, `GET /api/busca/plano` e `POST /api/busca` | `filtros_ok: false`; `400`; na página, o botão abre Filtros da busca |
| 2 | Com filtros, sem perfil | plano com `perfil_ok: false`; página oferece Meu perfil ou buscar sem nota |
| 3 | Plano com filtros e perfil | consultas, portais, cargos, janela, estimativa e IA corretos; nada consultado ainda |
| 4 | Buscar sem IA | andamento a cada consulta (≤ 5 s); no fim, vagas no relatório `sem_analise`, resumo certo; IA falsa sem pedido (SC-006) |
| 5 | Buscar com IA | vagas novas `pendente` → nota pela análise automática; andamento "faltam N"; fora dos critérios sem IA |
| 6 | IA falha (servidor falso devolve erro) | vagas gravadas sem nota, motivo visível, `POST /api/busca/analisar` tenta de novo |
| 7 | Cancelar no meio | nenhuma consulta nova depois do pedido; nada gravado; situação `cancelada`; não conta para o intervalo |
| 8 | Buscar de novo logo depois de uma concluída | `409` com `proxima_em` (30 min); depois do mínimo e antes de 6 h, `409` sem `confirmar_recente` e `202` com ele |
| 9 | Busca da página rodando + `vagas.py buscar` | terminal recusa com código 4 e a mensagem; o inverso: `POST /api/busca` → `409` dizendo que há busca no terminal |
| 10 | Candidatas do chat em `.cache/candidatas.json` + busca pela página | o arquivo do chat continua igual |
| 11 | Mesma fonte falsa pelo terminal e pela página | mesmas vagas e mesmo resumo (SC-005) |
| 12 | Servidor fechado no meio | ao subir de novo, `GET /api/busca` mostra `interrompida`; nada gravado |
| 13 | Pela rede (`--rede`) | ver o estado sim; iniciar e cancelar → 403 |
| 14 | Página no Chrome sem janela | botão, diálogo de confirmação, andamento e resumo renderizados sem erro |
| 15 | `python -m unittest discover -s tests` | todos passando |
| 16 | (opcional, com o OK da pessoa) uma busca real pequena: um cargo, um portal | grava como o terminal |

## Resultados (09/10/2026, Windows 11)

- Antes de tudo, a saída do `vagas.py buscar --gravar` com a fonte falsa (duas rodadas: vagas novas
  e já vistas) foi guardada e comparada depois da refatoração: **idêntica** (texto, `candidatas.json`,
  vagas no banco e registro da busca).
- Cenários 1 a 13 por um roteiro (servidor no próprio roteiro, porta 8799, config e banco
  temporários, fonte falsa, IA falsa): **31/31**. Andamento lido 17 vezes numa busca de 4 consultas
  (todas as etapas vistas); com IA, notas gravadas pela análise automática; IA fora do ar → vagas sem
  nota com o motivo, e "tentar de novo" deu as notas; cancelar parou depois de 1 consulta sem gravar
  nada; terminal recusou com código 4 durante a busca da página e a página recusou com busca no
  terminal; mesmas vagas e mesmo resumo pela página e pelo terminal; pela rede, 403 para iniciar e
  cancelar.
- Cenário 14 (Chrome sem janela): **5/5** — diálogo com o plano, andamento com Cancelar, resumo da
  busca concluída com o botão indisponível até o horário, busca externa e a opção "Buscar sem nota"
  sem perfil; capturas conferidas.
- Cenário 15: **83 testes passando** (14 novos em `tests/test_busca.py`).
- Cenário 16 (busca real pequena, com o OK da pessoa): um cargo na Gupy, config e banco temporários:
  concluída em 0,6 s, 3 vagas novas com descrição, gravadas sem nota, registro com origem `pagina`.
