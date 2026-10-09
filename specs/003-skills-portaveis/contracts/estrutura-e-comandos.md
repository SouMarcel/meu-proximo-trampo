# Contrato: estrutura das skills e comandos

## Estrutura

```text
AGENTS.md                         # fonte das instruções comuns (< 32 KiB)
CLAUDE.md                         # só "@AGENTS.md"
.gemini/settings.json             # {"context": {"fileName": "AGENTS.md"}, "mcpServers": {"gupy-candidato": {"httpUrl": "https://candidates.mcp.api.gupy.io/mcp"}}}
.mcp.json                         # já existe (Claude Code)
.agents/skills/                   # FONTE das skills de usuário
├── buscar-vagas/SKILL.md
├── consultar-gupy/SKILL.md
└── gerar-curriculo/{SKILL.md, modelo.json}
.claude/skills/                   # Claude Code
├── buscar-vagas/ consultar-gupy/ gerar-curriculo/   # CÓPIA GERADA (versionada)
└── speckit-*/                    # ferramentas de desenvolvimento (não geradas, não tocadas)
```

## `python sincronizar_skills.py [--conferir]`

- Sem opção: para cada skill de usuário (`buscar-vagas`, `consultar-gupy`, `gerar-curriculo`),
  recria `.claude/skills/<nome>/` a partir de `.agents/skills/<nome>/` (todos os arquivos), com o
  aviso de cópia logo depois do frontmatter do `SKILL.md`. Não mexe em outras pastas de
  `.claude/skills/`. Imprime o que mudou.
- `--conferir`: não escreve; sai com 0 se as cópias batem com a fonte e com 1 listando cada arquivo
  diferente, faltando ou sobrando.

## `PY consultar_gupy.py <ferramenta> [chave=valor …]`

- Ferramentas: `search_jobs`, `get_job_by_id`, `list_companies`, `get_company_by_id` (as mesmas do
  MCP `gupy-candidato`, com os mesmos argumentos).
- Argumentos `chave=valor`; `true`/`false` → booleano; inteiros → número; o resto, texto. Ou um único
  argumento JSON (`{"term": "analista"}`).
- Saída: o JSON da resposta (`data`) em UTF-8; erro → mensagem em português na saída de erro e
  código 1.

Exemplo: `.venv\Scripts\python consultar_gupy.py search_jobs term=analista pwd=true limit=10`
