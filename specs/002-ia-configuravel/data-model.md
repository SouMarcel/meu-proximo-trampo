# Data Model: IA configurável

## Escolha de IA (`config.json` → `"ia"`)

| Campo | Tipo | Regra |
|---|---|---|
| `provedor` | texto | um dos ids do catálogo ([research.md §2](research.md)): `claude_code`, `anthropic`, `openai`, `openrouter`, `groq`, `deepseek`, `gemini`, `compativel`, `nenhum` |
| `modelo` | texto | até 120 caracteres; vazio = padrão do provedor |
| `url_base` | texto | só para `compativel`; obrigatório nele; precisa começar com `https://` (ou `http://127.0.0.1`/`http://localhost`, para serviços locais compatíveis) |

Nunca contém chave. **Escolha efetiva** (o que a ferramenta usa de fato):

```text
sem "ia" e analise_automatica == false  → nenhum
sem "ia" e comando `claude` existe      → claude_code
sem "ia"                                → nenhum
com "ia"                                → a escolha gravada
```

## Chave do provedor (`.env`, fora do Git)

| Campo | Regra |
|---|---|
| variável | uma por provedor (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, `IA_COMPATIVEL_API_KEY`) |
| valor | até 400 caracteres, sem quebra de linha; gravado como `NOME=valor` |
| origem | `ambiente` (variável do sistema, vence) ou `arquivo` (`.env`) |

Gravar ou remover preserva todas as outras linhas (ex.: `MCP_STARTUP_JOBS`) e comentários. Para a
página, só sai `{cadastrada, final (últimos 4), origem}`.

## Registro da análise (na vaga, campos novos de `banco.validar_analise`)

| Campo | Regra |
|---|---|
| `analise_provedor` | id do catálogo (ex.: `gemini`) |
| `analise_modelo` | texto até 120; vazio para o padrão do Claude Code |

Os demais campos da análise não mudam.

## Estado da análise automática (em memória, `Fila`)

| Campo | Regra |
|---|---|
| `rodando` | já existe |
| `ultimo_erro` | motivo legível e mascarado da última rodada que falhou; limpo na próxima rodada com sucesso |
| `ultimo_erro_em` | data e hora da falha |
