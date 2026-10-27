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

## Decisões técnicas (plano, 27/10/2026)

### D1. Onde a reserva mora
- **Decisão**: dentro de `ia.responder`, quando ele é chamado sem `escolha` explícita. Com `escolha` (Testar e
  qualquer uso de uma IA específica), é uma IA só, como hoje.
- **Motivo**: todo chamador já passa por `ia.responder`, e nenhum precisa mudar a chamada.
- **Alternativa**: cada chamador decidir a reserva. Repetiria a lógica em oito lugares.

### D2. Formato no `config.json`
- **Decisão**: `ia: {provedor, modelo, url_base, reservas: [{provedor, modelo, url_base}]}`, com até 3 reservas.
  - `validar_escolha` valida cada uma como a principal.
  - Não entra reserva repetida (mesmo provedor, modelo efetivo e endereço da principal ou de outra) nem "Sem IA".
  - Sem `reservas`, é o formato antigo.
- **Alternativa**: uma chave nova `ia_reservas`. Separaria o que é uma configuração só.

### D3. O que troca de IA
- Qualquer `IAErro` vindo do provedor: HTTP, tempo, conexão ou falta de chave.
- Erros de formato depois da resposta (`GeracaoErro`, JSON fora do esperado) são do chamador e não trocam de IA.
- Sem nova tentativa na mesma IA.

### D4. Mensagens
- **Uma IA só, falhando**: a mensagem de hoje, sem mudança.
- **Mais de uma, todas falhando**: "nenhuma IA respondeu: Gemini (Google): o provedor está com problema agora (erro
  503); OpenRouter: limite de uso atingido no provedor; tente de novo mais tarde".
- **A reserva respondeu**: `aviso_reserva()` → "Gemini (Google) fora: o provedor está com problema agora (erro 503).
  Respondeu o OpenRouter (openrouter/free)." Cada motivo passa por `mascarar`.

### D5. Quem respondeu (por thread)
- **Decisão**: `ia.responder` guarda num `threading.local` o resultado da última chamada:
  `{provedor, modelo, nome, falhas: [{nome, modelo, motivo}]}`.
  - `ia.ultima()` devolve esse resultado.
  - `ia.marca()` devolve `{provedor, modelo}` de quem respondeu e, se foi reserva, também `reserva: true` e `aviso`.
    Sem chamada na thread, vale a escolha efetiva, como hoje.
- **Motivo**: o servidor atende em várias threads, e a geração roda em thread própria. Assim a marca não mistura
  pedidos.

### D6. Situação de cada IA
- **Arquivo**: `.cache/ia-estado.json`, gravado a cada tentativa (sucesso ou falha), com hora e motivo, sem chave nem
  texto do pedido. Se não der para gravar, segue sem ele.
- `estado_para_pagina` traz:
  - `sequencia`: `[{provedor, nome, modelo, gratuito, chave_ok, situacao}]`;
  - `alerta`: a principal, quando a última tentativa com ela falhou.
- `/api/versao` traz `ia_alerta`, para o botão IA mostrar o alerta sem abrir o painel.
- Uma tentativa bem-sucedida da principal apaga o alerta.

### D7. Teste da sequência
- O front chama `POST /api/ia/testar` para cada IA da sequência, uma linha por vez. A chave digitada vai só para o
  teste daquela IA.
- O teste também grava a situação.
