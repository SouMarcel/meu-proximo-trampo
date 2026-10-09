# Research: IA configurável

Sem agentes de pesquisa: as decisões saem do código atual (`dash/analise.py`, `dash/servidor.py`,
`dash/banco.py`, `fontes/startupjobs.py`) e do formato público e estável de cada API.

## 1. Um módulo, três adaptadores

- **Decision**: novo `ia.py` na raiz (biblioteca padrão, `urllib`), com:
  - `claude_code`: o `claude -p --output-format json --tools "" --strict-mcp-config
    --disable-slash-commands --no-session-persistence` de hoje (`dash/analise.py:115-119`), mais
    `--model <modelo>` quando a pessoa informar um;
  - `anthropic`: `POST https://api.anthropic.com/v1/messages`, cabeçalhos `x-api-key`,
    `anthropic-version: 2023-06-01`, corpo `{model, max_tokens, system?, messages}`; texto em
    `content[].text`;
  - `openai_compat`: `POST {url_base}/chat/completions`, `Authorization: Bearer <chave>`, corpo
    `{model, messages}`; texto em `choices[0].message.content`. Serve OpenAI, OpenRouter, Groq,
    DeepSeek, Gemini (endereço compatível do Google) e "outro compatível".
- **Rationale**: dois formatos de API cobrem todos os provedores pedidos; `urllib` evita SDKs
  (princípio III).
- **Alternatives considered**: SDK de cada empresa (várias dependências); LiteLLM (dependência
  pesada, fora da proposta).

## 2. Catálogo de provedores

| id | Nome no painel | Adaptador | Endereço | Variável da chave | Cobrança |
|---|---|---|---|---|---|
| `claude_code` | Claude Code (assinatura) | claude_code | — | — | assinatura |
| `anthropic` | Anthropic (Claude) | anthropic | `https://api.anthropic.com/v1` | `ANTHROPIC_API_KEY` | por uso |
| `openai` | OpenAI | openai_compat | `https://api.openai.com/v1` | `OPENAI_API_KEY` | por uso |
| `openrouter` | OpenRouter | openai_compat | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | por uso |
| `groq` | Groq | openai_compat | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | por uso |
| `deepseek` | DeepSeek | openai_compat | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` | por uso |
| `gemini` | Gemini (Google) | openai_compat | `https://generativelanguage.googleapis.com/v1beta/openai` | `GEMINI_API_KEY` | por uso |
| `compativel` | Outro compatível com OpenAI | openai_compat | informado pela pessoa | `IA_COMPATIVEL_API_KEY` | por uso |
| `nenhum` | Sem IA | — | — | — | — |

- **Modelo padrão**: Anthropic → `claude-opus-5-5` (o mais capaz atual; o painel lembra que
  `claude-sonnet-5-5` e `claude-haiku-4-5-20251001` custam menos). Para os demais, o padrão é
  conferido na documentação de cada provedor na hora da implementação (os nomes mudam rápido) e
  fica numa tabela única em `ia.py`, fácil de atualizar. Claude Code → vazio (o padrão da conta).
- **Onde obter a chave**: cada item do catálogo leva o link da página de chaves do provedor, para o
  painel apontar (Assumption da spec).

## 3. Saída em JSON

- **Decision**: não usar os modos de "saída JSON" dos provedores. O pedido continua dizendo
  "Responda SOMENTE com um array JSON", e a extração atual (do primeiro `[` ao último `]`,
  `dash/analise.py:128-132`) + `banco.validar_analise` valem para todos.
- **Rationale**: o modo JSON da API da OpenAI exige objeto, não array (mudaria o pedido e a skill);
  nem todo provedor compatível suporta; a validação que já existe barra resposta torta.

## 4. Erros com motivo legível

- **Decision**: `IAErro(motivo)` com mensagens fixas em português, por situação:
  401/403 → "chave recusada pelo provedor"; 402 ou corpo com "insufficient_quota"/"credit" → "sem
  crédito no provedor"; 429 → "limite de uso atingido; tente mais tarde"; 404 ou
  "model_not_found" → "modelo '<nome>' não existe ou sua conta não tem acesso"; `URLError`/
  timeout → "sem conexão com o provedor"; Claude Code ausente → "Claude Code não está instalado
  neste computador"; resposta sem texto → "resposta vazia do provedor". O trecho bruto da resposta
  (até 300 caracteres) só entra depois de `mascarar()`.
- **mascarar(texto)**: troca por `••••` toda ocorrência das chaves conhecidas (as do arquivo e as
  do ambiente) e padrões típicos (`sk-…`, `AIza…`, `gsk_…`) antes de qualquer `print`, registro ou
  resposta à página (FR-012).

## 5. Onde ficam escolha e chaves

- **Decision**:
  - Escolha em `config.json` → `"ia": {"provedor", "modelo", "url_base"}` (sem chave).
  - Chaves no `.env` da raiz (já fora do Git), uma variável por provedor. Novo módulo
    `segredos.py` (biblioteca padrão): `ler(nome)` (variável de ambiente vence o arquivo, como já
    faz `fontes/startupjobs._chave`), `gravar(nome, valor)` e `remover(nome)` preservando as outras
    linhas e comentários, `final(nome)` (últimos 4) e `origem(nome)` (arquivo ou ambiente).
    `fontes/startupjobs.py` passa a usar `segredos.ler` (mesmo comportamento).
- **Compatibilidade (FR-014)**: sem bloco `"ia"`: `analise_automatica: false` → `nenhum`; senão,
  `claude_code` se o comando `claude` existir, senão `nenhum`.
- **Config inexistente**: gravar a escolha de IA cria `config.json` só com `{"ia": …}`. Para não
  apagar o aviso da spec 001, o `existe` de `GET /api/config` passa a significar "há cargos
  configurados" (`termos` não vazio); e `filtros.salvar`, quando o config ainda não tem `termos`,
  parte do `config.exemplo.json` e sobrepõe o que já existe (inclusive `"ia"`).

## 6. Análise automática

- **Decision**: `dash/analise.py` troca o `subprocess` por `ia.responder(pedido)`; `comando()` vira
  `ia.disponivel()`; em lotes de até 10 vagas por chamada (APIs têm limite de tamanho);
  `max_tokens` 16000 no Anthropic. Cada análise recebe `analise_provedor` e `analise_modelo` antes
  de `banco.aplicar_analises` (campos novos aceitos por `validar_analise`). O `Fila` guarda
  `ultimo_erro` e `ultimo_erro_em` (motivo já mascarado), expostos em `GET /api/versao`; a página
  mostra o aviso no Relatório. Salvar a escolha ou testar com sucesso chama `FILA.pedir()` para
  reprocessar as vagas que esperam.
- **Rationale**: a falha costuma ser da conta (chave, crédito, limite), não da vaga: um motivo
  geral basta (FR-013) e evita campo novo por vaga.

## 7. Segurança das rotas

- **Decision**: `PUT /api/ia`, `POST /api/ia/testar` e `DELETE /api/ia/chave/<provedor>` exigem,
  além das proteções atuais (host, origem, JSON), que o pedido venha do próprio computador
  (`client_address` 127.0.0.1 ou ::1); de outro aparelho (`--rede`) → 403 "só no computador onde a
  ferramenta roda" (FR-011). `GET /api/ia` nunca devolve chave, só `cadastrada`, `final` e
  `origem`.

## 8. Testar conexão

- **Decision**: chamada mínima ("Responda apenas: ok") com tempo limite de 15 s nos provedores por
  chave (SC-002) e 30 s no Claude Code (que demora a iniciar); a chave do formulário é usada no teste
  sem ser gravada; sem chave no formulário, usa a salva.

## 9. Testes

- **Decision**: `tests/test_ia.py` e `tests/test_segredos.py` (`unittest`): escolha efetiva e
  legado; montagem das requisições de cada adaptador (sem rede); extração de texto das respostas;
  classificação de erros; `mascarar`; `.env` preservando linhas; e um teste ponta a ponta com um
  servidor HTTP falso local imitando `/chat/completions` (provedor `compativel`).
