# Quickstart: validar a preparação para entrevista

Servidor no roteiro, config, banco e `entrevistas/` temporários, perfil e vagas fictícios, IA falsa local, Chrome sem
janela.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Vaga em Entrevista, sem IA: "Preparar entrevista" | dossiê com o que existe; perguntas da lista padrão com o porquê (SC-001) |
| 2 | Texto colado + resumo com IA falsa (um ponto com trecho inventado) | origem certa; o inventado vira dedução |
| 3 | Perguntas com IA falsa | somadas à lista, sem repetir |
| 4 | Histórias com IA falsa (uma com número fora do perfil) | rascunhos STAR com reflexão; o do número marcado (SC-002) |
| 5 | Confirmar uma história; não confirmar outra | só a confirmada no banco (SC-003); aparece em outra vaga |
| 6 | Simulação em inglês com IA falsa; pular; encerrar | retorno por resposta; "mais forte" conferida (SC-005); resumo |
| 7 | Salário com faixa na vaga e pretensão no perfil | só esses valores (SC-004) e os pontos de conversa |
| 8 | Anotar como foi | anotação com a vaga; perguntas que caíram entram nas prováveis |
| 9 | Página: botão no card de Entrevista e no detalhe; diálogo com as seções | renderiza e grava (capturas) |
| 10 | Chat: `entrevista.py preparar` e `historias` | mesmo resultado |
| 11 | `python -m unittest discover -s tests` | todos passando |

## Resultado (12/10/2026, Windows 11)

Roteiro com servidor na porta 8799, config, banco e `entrevistas/` temporários, perfil e vagas fictícios, IA falsa
local e Chrome sem janela: **25/25 verificações OK**, cobrindo os cenários 1 a 10.

- 1: sem IA, o dossiê mostra análise, lacunas, faixa e anotações; as perguntas vêm da lista padrão, dos requisitos e
  das lacunas, todas com o porquê; o resumo avisa que precisa de IA.
- 2: o resumo com a IA falsa dá a origem certa, e o ponto com trecho inventado vira dedução.
- 3: as perguntas da IA se somam à lista sem repetir.
- 4 e 5: os rascunhos STAR vêm com reflexão, o do "45%" vem marcado para conferir, nada é salvo antes da confirmação,
  e a história confirmada aparece em outra vaga e pode ser editada.
- 6: a simulação em inglês traz o retorno, e o "300" inventado na resposta mais forte vem marcado; o resumo mostra o
  que treinar; sem IA, só a resposta é gravada.
- 7: o salário mostra só a faixa da vaga e a pretensão do perfil.
- 8: a anotação é gravada, e a pergunta que caiu entra nas prováveis.
- 9: o botão está no card de Entrevista e no detalhe; as seis abas renderizam e gravam (capturas do dossiê, das
  histórias e da simulação).
- 10: `entrevista.py preparar` e `historias` dão o mesmo resultado.
- 11: `python -m unittest discover -s tests` → 199 testes OK.
