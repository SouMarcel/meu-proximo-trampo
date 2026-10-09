# Research: Skills portáveis

Fontes: documentação oficial de cada assistente (consultada em 2026-10-08 por um agente de
pesquisa) e o clone local do career-ops, que resolve o mesmo problema.

## 1. Onde cada assistente procura skills e instruções

| | Claude Code | Codex CLI | Gemini CLI | OpenCode |
|---|---|---|---|---|
| Skills do projeto | só `.claude/skills/` (sem configuração para outras pastas) | `.agents/skills/` | `.gemini/skills/` ou `.agents/skills/` | `.opencode/skills/`, `.claude/skills/` e `.agents/skills/` |
| Instruções da raiz | `CLAUDE.md` (lê `AGENTS.md` sozinho só sem `CLAUDE.md`/`CLAUDE.local.md`; senão, `@AGENTS.md` dentro do `CLAUDE.md`) | `AGENTS.md` (limite padrão 32 KiB) | `GEMINI.md`; para `AGENTS.md`, `.gemini/settings.json` → `context.fileName` | `AGENTS.md` |
| MCP do projeto | `.mcp.json` | `.codex/config.toml` (projeto confiável) | `.gemini/settings.json` → `mcpServers` | `opencode.json` → `mcp` |
| Pergunta com opções | `AskUserQuestion` | sem ferramenta geral documentada | `ask_user` | `question` |
| Ler URL | `WebFetch` | sem leitura de URL documentada | `web_fetch` | `webfetch` |

Antigravity CLI (substituto do Gemini CLI desde 18/06/2026, quando o Gemini CLI deixou de atender
o plano gratuito): lê `.agents/skills/` e `AGENTS.md`/`GEMINI.md`.

## 2. Fonte única e a cópia para o Claude Code

- **Decision**: fonte em `.agents/skills/<nome>/` (lida por Codex, Gemini CLI, OpenCode e
  Antigravity). Cópia **gerada e versionada** em `.claude/skills/<nome>/`, só para as três skills
  de usuário, por `sincronizar_skills.py` (biblioteca padrão), que copia a pasta inteira (inclui
  `gerar-curriculo/modelo.json`) e põe no `SKILL.md` da cópia, logo depois do frontmatter, o aviso
  `<!-- Cópia gerada de .agents/skills/<nome>/ por sincronizar_skills.py: edite lá. -->`.
  `python sincronizar_skills.py --conferir` (e um teste `unittest`) falha quando a cópia diverge.
- **Rationale**: o Claude Code não lê `.agents/` e não aceita outra pasta; links simbólicos viram
  arquivos de texto quebrados no Windows com `core.symlinks=false`; versionar a cópia faz o clone
  funcionar direto, sem passo extra.
- **Alternatives considered**: links simbólicos (quebram no Windows; o career-ops precisa de um
  "materializador"); plugin local do Claude Code apontando para `.agents/skills` (prefixa os nomes
  das skills, exige diálogo de confiança e não carrega em sessões na nuvem); fonte em
  `.claude/skills` com cópia em `.agents/skills` (tanto faz para a cópia, mas a pasta neutra como
  fonte deixa claro que não é do Claude).
- **Efeito no OpenCode**: ele lê `.claude/skills` e `.agents/skills`, então vê cada skill duas
  vezes, com conteúdo idêntico (avisa "duplicate skill name" e usa uma). O README cita
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` para quem quiser silenciar.

## 3. Instruções comuns

- **Decision**: `AGENTS.md` na raiz como fonte (abaixo de 32 KiB); `CLAUDE.md` versionado com só
  `@AGENTS.md`; `.gemini/settings.json` com `context.fileName: "AGENTS.md"` (em vez de `GEMINI.md`,
  para o Antigravity não carregar duas vezes).
- **Na branch pessoal**: hoje existe um `CLAUDE.md` local (seção do graphify), fora do Git pelo
  exclude local. Antes do merge, a seção do graphify vai para o `CLAUDE.local.md` (também lido pelo
  Claude Code) e o `CLAUDE.md` local e a linha do exclude saem, senão o merge falha.

## 4. Texto neutro nas skills

- **Decision**: trocar as quatro dependências exclusivas por instruções neutras:
  - perguntas com opções: "use a ferramenta de perguntas com opções do assistente (AskUserQuestion
    no Claude Code, ask_user no Gemini CLI, question no OpenCode); sem ela, pergunte em texto com as
    opções numeradas";
  - ler link: "use a ferramenta de leitura web do assistente (WebFetch, web_fetch, webfetch); sem
    ela (ex.: Codex), peça que a pessoa cole o texto da vaga";
  - Gupy: ferramentas MCP quando disponíveis; senão, o comando da ferramenta (§5);
  - referências entre skills: nome + caminho do arquivo em `.agents/skills/`.
- Frontmatter: manter `name` e `description` (padrão agentskills.io); `description` com até
  1024 caracteres.

## 5. Consulta à Gupy sem MCP

- **Decision**: `fontes/gupy.py` ganha uso por linha de comando (`main()`), chamado pelo script `consultar_gupy.py` na raiz:
  `PY consultar_gupy.py <ferramenta> chave=valor …` (ou um único JSON), com as mesmas ferramentas e
  argumentos do MCP (`search_jobs`, `get_job_by_id`, `list_companies`, `get_company_by_id`),
  reaproveitando `chamar()`; valores `true`/`false` viram booleanos e números inteiros viram int;
  imprime o JSON da resposta.
- **Rationale**: `chave=valor` evita o inferno de aspas de JSON no PowerShell e no cmd; é o mesmo
  serviço público que o MCP usa.
- MCP continua declarado onde é fácil: `.mcp.json` (Claude Code, já existe) e
  `.gemini/settings.json` (`httpUrl`). Codex e OpenCode usam o comando (o README mostra como
  declarar o MCP neles, para quem quiser).

## 6. Outros caminhos a ajustar

- `dash/analise.py` lê as regras de nota em `.claude/skills/buscar-vagas/SKILL.md` → passa a ler a
  fonte `.agents/skills/buscar-vagas/SKILL.md`.
- Menções a `.claude/skills/` em README, skills e `dash/README.md` passam a citar a fonte.

## 7. Verificação possível nesta máquina

- Claude Code 2.1.202 e Gemini CLI 0.60.0 instalados; Codex e OpenCode não. Gemini CLI exige chave
  paga da Gemini API desde 18/06/2026: o teste com ele depende de o usuário ter essa chave.
