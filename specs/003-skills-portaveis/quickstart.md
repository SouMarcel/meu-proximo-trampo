# Quickstart: validar as skills portáveis

| # | Cenário | Esperado |
|---|---|---|
| 1 | `python sincronizar_skills.py --conferir` logo depois da geração | código 0 (SC-003) |
| 2 | Editar uma frase numa cópia em `.claude/skills/` e conferir | código 1 apontando o arquivo; nova geração restaura |
| 3 | Busca textual nas skills de usuário por `AskUserQuestion`, `WebFetch`, `mcp__` sem alternativa ao lado | 0 ocorrências sem alternativa (SC-002) |
| 4 | `PY consultar_gupy.py search_jobs term=analista limit=3` | JSON com vagas, em até 30 s (SC-005) |
| 5 | Claude Code numa sessão nova na pasta: listar skills e pedir "busca vagas novas pra mim" (só até ele escolher a skill) | as três skills de usuário listadas e a buscar-vagas escolhida (SC-004) |
| 6 | Gemini CLI na pasta (se houver chave paga): `/skills` e o pedido de busca | skills de `.agents/skills` listadas; AGENTS.md carregado |
| 7 | Clone novo (cópia limpa) no Windows | `.agents/skills` e `.claude/skills` completos, sem arquivo de texto no lugar de pasta (SC-006) |
| 8 | Codex e OpenCode | ⏳ não instalados nesta máquina: verificação pendente para quem tiver |
| 9 | `dash/analise.py` montando o pedido | regras de nota recortadas da fonte `.agents/skills/buscar-vagas/SKILL.md` |
| 10 | `python -m unittest discover -s tests` | todos passando (inclui a conferência das cópias) |

## Resultados (Windows 11, 2026-10-08)

| # | Resultado |
|---|---|
| 1 | ✅ `--conferir` → "Cópias em dia" depois da geração |
| 2 | ✅ coberto por `tests/test_skills.py` (cópia editada, apagada e sobrando são acusadas; a geração restaura) |
| 3 | ✅ as menções a AskUserQuestion, WebFetch e `mcp__` nas skills de usuário vêm com a alternativa ao lado |
| 4 | ✅ `consultar_gupy.py search_jobs term=analista limit=3` → 3 vagas (total 7612) em ~1 s |
| 5 | ✅ sessão nova do Claude Code (2.1.202) na worktree: vê buscar-vagas, consultar-gupy e gerar-curriculo, escolhe a buscar-vagas para "busca vagas novas pra mim" e carregou o AGENTS.md |
| 6 | ✅ Gemini CLI 0.60.0 (`gemini skills list`, pasta marcada como confiável): lista as três skills de `.agents/skills`; as `speckit-*` não aparecem. Sem marcar a pasta como confiável, ele ignora as skills do projeto (anotado no README). Conversa completa não testada (exige chave paga) |
| 7 | ✅ nenhum link simbólico no índice do Git; as pastas são arquivos comuns |
| 8 | ⏳ Codex e OpenCode não instalados nesta máquina |
| 9 | ✅ o pedido da análise automática traz "Como dar a nota" e os campos, lidos de `.agents/skills/buscar-vagas/SKILL.md` |
| 10 | ✅ 41 de 41 testes |
