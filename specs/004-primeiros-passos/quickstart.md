# Quickstart: validar os primeiros passos

Servidor da worktree com config, banco e perfil temporários (porta 8799); materiais **fictícios**
gerados no teste (currículo .docx e PDF, ZIP no formato da exportação do LinkedIn); provedor de IA
falso local (como na spec 002) para o rascunho.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Sem perfil, abrir a página | os primeiros passos aparecem; fechar e reabrir pelo botão |
| 2 | Enviar currículo .docx, PDF e ZIP do LinkedIn | textos extraídos; ZIP com cargos, formação, competências, certificações e idiomas; avisos para o que faltar |
| 3 | PDF só com imagem, `.doc` antigo, arquivo acima de 10 MB | avisos claros; os outros materiais seguem |
| 4 | Currículo com CPF, RG e data de nascimento | não aparecem no pedido à IA (servidor falso registra o pedido) nem no perfil (SC-005) |
| 5 | Gerar rascunho com IA | rascunho em até 2 min; todo item com fonte; conflito de datas lado a lado (SC-002, SC-003) |
| 6 | Anamnese: responder, pular algumas, ativar o bloco do exterior | uma pergunta por vez; puladas no diagnóstico; conquista sem número fica qualitativa |
| 7 | Prévia: diagnóstico e Markdown editável | achados com pergunta; editar e gravar → `perfil.md` igual ao revisado |
| 8 | Fechar a página no meio e voltar | progresso retomado |
| 9 | Gravar com perfil existente | diferenças mostradas; versão anterior em `anexos/perfis-anteriores/` (SC-004) |
| 10 | Filtros propostos | cargos PT/EN, local, modelos, internacional só com interesse; mudanças em relação aos atuais; gravação pelo painel |
| 11 | Sem IA | rascunho vazio + campos do ZIP + texto ao lado; servidor falso sem nenhum pedido (SC-006) |
| 12 | Pela rede local (`--rede`) | ver sim; enviar e gravar → 403 |
| 13 | Skill de chat (Claude Code) | `PY primeiros_passos.py extrair` e `diagnostico` funcionando; skill listada |
| 14 | `python -m unittest discover -s tests` | todos passando |

## Resultados (09/10/2026, Windows 11)

- Cenários 1 a 13 por um roteiro (servidor da worktree na porta 8799 com `TRAMPO_CONFIG` e
  `TRAMPO_BANCO` temporários, provedor de IA falso local e materiais fictícios): **38/38**.
  ZIP do LinkedIn lido em 0,05 s; rascunho com o provedor falso em 0,03 s; o pedido à IA não
  levou CPF, RG nem data de nascimento; sem IA, nenhum pedido ao provedor; pela rede (`--rede`),
  leitura sim e envio e gravação com 403.
- Página: as 8 etapas renderizadas no Chrome sem janela (DOM depois do JS), sem erro e sem CPF
  na página; capturas conferidas de Materiais, Perguntas e Revisão.
- Cenário 14: **69 testes passando** (28 novos em `tests/test_primeiros_passos.py`).
- Fica para a pessoa: clicar no fluxo inteiro no navegador com materiais reais, com e sem IA.
