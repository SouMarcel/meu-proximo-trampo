# Quickstart: validar o kit de candidatura

Servidor no roteiro, config e banco temporários, IA falsa local (compatível com OpenAI), perfil e vagas
fictícios, Chrome sem janela.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Análise com frases conhecidas (sponsor, B2B, fluent English, overlap, hybrid) | campos novos com a opção certa e a frase (SC-001); valor fora das opções cai |
| 2 | Vaga sem IA | detalhe com sistema, sinais e restrição; checklist por palavras do anúncio |
| 3 | Checklist: marcar, tirar, acrescentar; refazer a análise | estado preservado (SC-006); item novo entra |
| 4 | Botão de candidatura | só um link `target=_blank`, nenhuma chamada ao servidor (SC-004) |
| 5 | Carta sem uma das quatro respostas | `400` dizendo qual falta |
| 6 | Carta com IA falsa: fato inventado / correta / genérica / curta | bloquear / ok / conferir / conferir (SC-003) |
| 7 | Respostas: 5 perguntas, 2 sensíveis, IA falsa que responde tudo | sensíveis com a pessoa, sem resposta da IA (SC-002); resposta da pessoa gravada igual |
| 8 | Lembretes com datas simuladas (8, 15 e 22 dias; entrevista ontem; mudança de etapa; parar) | aparecem e somem nos dias certos (SC-005) |
| 9 | Página: detalhe com análise, checklist e documentos; card com lembrete | renderiza e grava (capturas) |
| 10 | Skill: `PY conferir.py --carta`, `PY candidatura_ia.py sensiveis`, `PY dash/banco.py kit` | mesma regra da página |
| 11 | `python -m unittest discover -s tests` | todos passando |
| 12 | (com OK) uma carta com a IA configurada pela pessoa | carta conferida |

## Resultados (09/10/2026, Windows 11)

- Referências do `vagas.py` (specs 005, 008 e 009) iguais às de antes desta fase.
- Cenários 1 a 10 por um roteiro (servidor no roteiro, config e banco temporários, IA falsa local
  compatível com OpenAI, perfil e vagas fictícios, Chrome sem janela): **23/23**. Campos novos da
  análise com a opção certa e a frase; checklist sem IA pelas palavras do anúncio; estado da pessoa
  preservado com a análise refeita e item novo acrescentado; botão de candidatura só como link;
  carta sem uma das quatro respostas recusada dizendo qual; carta correta ok e com fato inventado
  bloqueada, as duas guardadas (.docx e .txt); perguntas sensíveis sem resposta da IA e a resposta da
  pessoa gravada como ela escreveu; lembretes aos 7 e 14 dias e de agradecimento, sumindo ao marcar ou
  ao mudar de etapa; comandos da skill com a mesma regra; detalhe, card, contagem no quadro e
  diálogos na página (capturas conferidas).
- Ajustes achados na validação: condição de corrida entre duas mudanças seguidas no checklist
  (corrigida), cartas listadas também entre os currículos (corrigido) e rótulo de item tirado.
- Correção de quebra: `conferir.datas` perdia o ano depois de uma palavra que parece mês ("since
  2015"); agora o ano conta.
- Cenário 11: **161 testes passando** (15 novos em `tests/test_kit.py` e `tests/test_candidatura.py`).
- Cenário 12 (carta com a IA real): pendente, com o OK do usuário.
