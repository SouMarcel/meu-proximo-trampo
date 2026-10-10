# Quickstart: validar as análises do perfil

Servidor no roteiro, config e banco temporários, perfil e vagas fictícios, IA falsa local, Chrome sem janela.

| # | Cenário | Esperado |
|---|---|---|
| 1 | 8 vagas analisadas com lacunas conhecidas (variações de "Power BI") | ranking com a mais frequente nas de maior aderência no topo, variações juntas, níveis e exemplos (SC-001) |
| 2 | Visão "seguidas" com 3 vagas | aviso de quantas faltam, sem ranking (SC-002) |
| 3 | Plano de estudo com IA falsa; sem IA | plano para as lacunas do topo; sem IA, explicação |
| 4 | Cargos-alvo com IA falsa (um com evidência inventada) | 5–10 cargos com tipo, evidência e termos; o inventado marcado (SC-003) |
| 5 | Levar 2 cargos para os filtros | proposta com o que muda; nada gravado até confirmar; resto igual (SC-004) |
| 6 | Prontidão com perfil e filtros de teste | situação certa em cada item; marcar LinkedIn salva (SC-005) |
| 7 | Análises salvas | reabrir mostra a última com a data |
| 8 | Página: passo "Análises" em Meu perfil | três seções, botões e resultados (capturas) |
| 9 | Chat: `analise_perfil.py lacunas/prontidao/cargos/plano` | mesmo resultado |
| 10 | `python -m unittest discover -s tests` | todos passando |

## Resultados (10/10/2026, Windows 11)

- Referências do `vagas.py` iguais às de antes desta fase.
- Cenários 1 a 9 por um roteiro (servidor no roteiro, config e banco temporários, IA falsa local, perfil e 8 vagas
  fictícios, Chrome sem janela): **11/11**. Ranking com as variações de "Tableau" juntas no topo (crítica), AWS, inglês
  e dbt como média; visão "seguidas" com 3 vagas mostra quantas faltam; plano de estudo com a IA; 5 cargos com tipo,
  evidência e termos, o de evidência inventada marcado "conferir"; levar cargos para os filtros sem gravar até
  confirmar, e o resto dos filtros igual; prontidão com a situação certa em cada item e a marcação do LinkedIn salva;
  análises salvas com a data; comandos do chat com o mesmo resultado; passo "Análises" na página (captura conferida).
- Achado nos testes: requisito do anúncio coberto por ferramenta da mesma família no perfil (Tableau × Power BI)
  conta como "sustentado" pela conferência de requisitos e não vira lacuna; lacuna de uma vaga só, de peso baixo,
  fica abaixo de 10% e fora do ranking (como a spec pede).
- Cenário 10: **181 testes passando** (8 novos em `tests/test_analise_perfil.py`).
