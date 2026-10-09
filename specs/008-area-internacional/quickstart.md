# Quickstart: validar a área internacional

Servidor da worktree no roteiro (porta 8799), config e banco temporários, fonte falsa (com `AREAS`
configurável e vagas com local de vários países e idiomas). Nenhum portal real.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Internacional desligada, sem idiomas: `vagas.py buscar --gravar` com a fonte falsa | saída e vagas iguais à referência da spec 005 (SC-002) |
| 2 | Ligar a internacional sem países ou cargos | `400` com o que falta |
| 3 | Ligar com Portugal + "data analyst", remoto nacional desmarcado | consultas internacionais existem; vagas de fora com `area: internacional`, `pais_vaga: Portugal` |
| 4 | Aceito morar fora com Portugal | consulta `mudanca:Portugal` sem filtro de remoto |
| 5 | Fonte só nacional | não consultada nas consultas internacionais (SC-004) |
| 6 | Idiomas PT e EN; vaga em espanhol | Fora dos critérios com "Vaga em espanhol; você aceita português e inglês"; vagas PT e EN passam; vaga curta passa |
| 7 | Moeda não aceita e salário anual abaixo do mínimo | Fora dos critérios com o motivo; sem salário, passa |
| 8 | Análise com IA falsa devolvendo `idioma` | vale mais que a detecção; critério reaplicado |
| 9 | Página (Chrome sem janela) | abas; Relatório só nacional; aba Internacional com as de fora; etiqueta "Internacional · Portugal" na listagem, card, lista do quadro e detalhe; filtro de área no quadro; painel internacional abre e grava |
| 10 | Adicionar Vaga com local "Remote - United States" | área sugerida internacional, país Estados Unidos |
| 11 | `python -m unittest discover -s tests` | todos passando |

## Resultados (09/10/2026, Windows 11)

- Cenário 1 (SC-002): a saída do `vagas.py buscar --gravar` com a fonte falsa, em duas rodadas, saiu
  **igual** à de antes desta fase, tanto com a busca internacional desligada quanto ligada (os
  campos novos `area`, `pais_vaga` e `idioma` não entram na comparação).
- Cenários 2 a 10 por um roteiro (servidor no roteiro, config e banco temporários, fonte falsa,
  vagas fictícias em PT, EN e ES, Chrome sem janela): **15/15**, duas rodadas seguidas. Painel recusa
  ligar sem país ou cargo; liga com o remoto nacional desmarcado; "aceito morar fora" gera a consulta
  presencial/híbrida; fonte só nacional não é consultada para o exterior; vagas de fora gravadas como
  internacionais com o país; espanhol cortado com o motivo e PT/EN aceitos; salário em USD abaixo do
  mínimo cortado e sem salário aceito; o idioma da análise vale mais; local nos Estados Unidos vira
  internacional; Relatório de Vagas só com as nacionais e a aba Internacional com as de fora;
  etiqueta na listagem, no card, na lista do quadro e no detalhe; filtro de área no quadro; painel
  internacional com todos os campos (capturas conferidas).
- Cenário 11: **126 testes passando** (10 novos em `tests/test_internacional.py`).

