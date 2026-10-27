# Research: IA com reserva e aviso de indisponibilidade

**Data**: 2026-10-27. Leitura do código (`ia.py`, `dash/servidor.py`, `dash/analise.py` e quem chama a IA). Nenhuma
consulta externa.

**Motivo**: na primeira candidatura assistida fora da Gupy, o Gemini respondeu 503 (sobrecarga do Google) e a ferramenta
não preencheu nada que dependesse da IA. A única saída era esperar ou trocar de provedor à mão.

## R1. Como a IA é escolhida hoje

- **Escolha única**: `config.json` → `ia: {provedor, modelo, url_base}`, gravada pelo painel IA (`ia.salvar_escolha`).
  Sem ela, vale o comportamento antigo: Claude Code se estiver instalado.
- **Chaves**: uma variável por provedor no `.env` (`GEMINI_API_KEY`, `OPENROUTER_API_KEY` etc.), lidas por
  `segredos.py`. A página nunca vê a chave, só se existe e os 4 últimos caracteres.
- **Provedores** (`ia.PROVEDORES`):
  - Claude Code (assinatura);
  - Anthropic, OpenAI, OpenRouter, Groq, DeepSeek e Gemini;
  - "outro compatível" (endereço próprio, inclusive local);
  - Sem IA.
- **Modelo gratuito do OpenRouter**: `openrouter/free` (o roteador gratuito, padrão desde 21/10) ou um modelo com
  `:free` (`ia.gratuito`).

## R2. Como a falha aparece hoje

- `ia.responder` levanta `IAErro` com o motivo em português, sem chave (`motivo_http`):
  - 401/403: chave recusada;
  - 402: sem crédito;
  - 429: limite de uso;
  - 404: modelo inexistente;
  - 5xx: "o provedor está com problema agora (erro N)";
  - tempo esgotado e sem conexão.
- **Cada chamador trata o erro do seu jeito**: currículo, carta, respostas de formulário, candidatura assistida,
  análise automática do relatório, análise do perfil, leitura do currículo base, Adicionar Vaga por post.
  - Quase todos repassam o motivo e pedem para a pessoa "tentar mais tarde" ou "escrever as respostas aqui".
  - A análise automática guarda o último erro (`analise.FILA.ultimo_erro`), que o painel IA mostra
    (`estado_para_pagina(..., ultimo_erro)`).
- **Não há nova tentativa nem outro provedor.** Com o principal fora, toda função com IA para.

## R3. Quem registra qual IA respondeu

`curriculo_ia`, `candidatura_ia` e `analise_perfil` gravam no documento a "marca" da IA (`_marca_ia`). A marca vem de
`ia.escolha_efetiva()`, a escolha configurada, e não de quem respondeu de fato. Com reserva, ela precisa vir do
provedor que respondeu.

## R4. Teste de 2026-10-27

- `ia.testar` com o Gemini (`gemini-3.8-flash`): "o provedor está com problema agora (erro 503); tente mais tarde".
- No `.env` do usuário, as duas chaves que ele quer usar já estão cadastradas: Gemini e OpenRouter.
