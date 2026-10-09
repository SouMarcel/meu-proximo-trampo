# Quickstart: validar fontes internacionais e elegibilidade

Respostas gravadas de cada fonte (uma consulta real por fonte no início da implementação), servidor
no roteiro, config e banco temporários.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Fontes novas desligadas | `vagas.py` igual à referência (SC-001) |
| 2 | Cada fonte com a resposta gravada | vagas normalizadas, filtradas pelo cargo, com restrição, moeda, salário e links |
| 3 | Fonte que falha (erro de rede simulado) | as outras seguem; erro no resumo (SC-004) |
| 4 | Link de carreiras Greenhouse, Lever, Ashby; link de outro sistema | reconhecidos; o outro recusado com explicação |
| 5 | Conjunto de anúncios de elegibilidade | cortes e passes esperados com o motivo certo; ambíguos passam (SC-002) |
| 6 | Anúncios com sponsor/relocation | sinal positivo na listagem e no detalhe (SC-003) |
| 7 | Frase própria de restrição e de sinal | corta citando a frase; sinal aparece |
| 8 | Adicionar Vaga com link de vaga do Lever (resposta gravada) | dados da fonte e elegibilidade aplicada |
| 9 | Painel internacional (Chrome sem janela) | fontes, empresas e frases; grava |
| 10 | (com OK) uma busca internacional real pequena com duas fontes | vagas na aba Internacional |
| 11 | `python -m unittest discover -s tests` | todos passando |

## Resultados (09/10/2026, Windows 11)

- Cenário 1 (SC-001): a saída do `vagas.py buscar --gravar` com a fonte falsa, em duas rodadas, saiu
  **igual** à de antes desta fase, com a busca internacional desligada e ligada.
- Cenários 2 a 9 por um roteiro (servidor no roteiro, config e banco temporários, respostas gravadas
  das fontes no lugar da rede, Chrome sem janela): **23/23**. Vagas de Remotive, Remote OK, Jobicy,
  We Work Remotely e Greenhouse normalizadas e gravadas com área, país, restrição e moeda; consultas
  globais rotuladas "exterior"; fonte fora do ar não trava as outras e o erro sai uma vez; empresas
  do Greenhouse, Lever e Ashby reconhecidas pelo link e link de outro sistema recusado com a
  explicação (no servidor e no painel); vagas só para Canadá/EUA em Fora dos critérios com o motivo;
  híbrida em Londres cortada para quem só aceita morar em Portugal; patrocínio e relocation como
  sinal verde na listagem, no card e no detalhe; frase própria cortando e frase positiva virando
  sinal; link do Lever lido pela API, com candidatura e elegibilidade, sem duplicar; painel com
  fontes, empresas e frases, gravando o que mudou (capturas conferidas).
- Cenário 5 também em `tests/test_elegibilidade.py`: 24 anúncios com o resultado esperado (SC-002 e
  SC-003).
- Cenário 11: **146 testes passando** (20 novos em `tests/test_fontes_int.py` e
  `tests/test_elegibilidade.py`).
- Cenário 10 (busca real pequena, com o OK do usuário): Remotive e Get on Board, cargo "data analyst",
  janela de 7 dias, config e banco temporários. As duas consultas responderam sem erro e não trouxeram
  vagas desse cargo: a API pública da Remotive devolveu só 17 vagas no total (11/09 a 07/10, nenhuma
  de analista), e o Get on Board, nenhuma na semana.
