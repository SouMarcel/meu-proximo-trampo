# Quickstart: validar a IA configurável

Windows, cópia limpa (como na spec 001), porta de teste 8799, banco e config temporários
(`TRAMPO_CONFIG`, `TRAMPO_BANCO`). Chaves reais só se o usuário quiser fornecer; sem elas, os
cenários com provedor real ficam para ele, e o fluxo é coberto pelo provedor `compativel` apontando
para um servidor falso local.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Sem config de IA, com o Claude Code instalado | escolha efetiva `claude_code`; vaga adicionada recebe nota como hoje (SC-006) |
| 2 | Config antiga com `analise_automatica: false` | efetiva `nenhum`; vaga fica sem nota |
| 3 | Painel → `compativel` com o servidor falso + chave de teste → testar → salvar | "Conexão funcionando"; `.env` com `IA_COMPATIVEL_API_KEY`; `config.json` com `"ia"` e sem chave; `GET /api/ia` mostra só `final` (FR-003, SC-001) |
| 4 | Com o 3, adicionar vaga com descrição | nota em até 2 min; detalhe mostra "compativel · <modelo>" (FR-007, SC-004) |
| 5 | Servidor falso devolvendo 401, 402, 429, 404 e fora do ar | teste e análise com o motivo certo; vaga esperando; aviso no Relatório; nada quebra (SC-007) |
| 6 | Servidor falso devolvendo texto que ecoa a chave | a chave aparece como `••••` na página e no terminal (FR-012) |
| 7 | "Sem IA" e adicionar vaga | vaga sem nota; servidor falso não recebe nenhum pedido (SC-005) |
| 8 | Página aberta por outro aparelho (`--rede`) tentando salvar | 403 com a mensagem; nada muda (FR-011) |
| 9 | `.env` com `MCP_STARTUP_JOBS` antes; salvar e remover a chave da IA | `MCP_STARTUP_JOBS` intacto (FR-003) |
| 10 | Procurar a chave de teste em todos os arquivos (fora do `.env`) e nas respostas da página | 0 ocorrências (SC-003) |
| 11 | Config sem `termos`, só com `"ia"` | aviso "Antes da primeira busca…" continua aparecendo; salvar filtros parte do exemplo e mantém `"ia"` |
| 12 | Provedor real (se o usuário fornecer chave): testar e analisar uma vaga | conexão e nota funcionando |

Testes automáticos: `python -m unittest discover -s tests`.

## Resultados (Windows 11, 2026-10-08)

Servidor da worktree com config e banco temporários, porta 8799, `--rede`, e provedor falso local
no formato da OpenAI (`validar_ia.py` no scratchpad da sessão).

| # | Resultado |
|---|---|
| 1 | ✅ sem `"ia"`, efetiva `claude_code` (Claude Code instalado) |
| 2 | ✅ coberto por teste (`analise_automatica: false` → `nenhum`) |
| 3 | ✅ testar → "Conexão funcionando (Outro compatível com OpenAI · modelo-falso)"; salvar → `chaves.compativel = {cadastrada, final "5678", origem "arquivo"}`; `config.json` só com `"ia"`, sem chave |
| 4 | ✅ vaga nova recebeu nota 72 com `analise_provedor: compativel`, `analise_modelo: modelo-falso` |
| 5 | ✅ 401 → `ia_erro` "chave recusada pelo provedor…"; vaga continua `pendente`; servidor segue no ar |
| 6 | ✅ resposta que ecoa a chave → motivo genérico; a chave não aparece nas respostas nem no log |
| 7 | ✅ "Sem IA": 0 pedidos ao provedor; vaga fica `pendente` |
| 8 | ✅ pela rede (IP da máquina): `GET /api/ia` com `pode_alterar: false`; `PUT` → 403 com a mensagem |
| 9 | ✅ `.env` com comentário e `MCP_STARTUP_JOBS` preservados ao gravar e ao remover a chave da IA |
| 10 | ✅ chave de teste: 0 ocorrências fora do `.env` (arquivos e respostas) |
| 11 | ✅ config só com `"ia"` → `existe: false` (aviso da spec 001 continua); salvar filtros parte do exemplo e preserva `"ia"` |
| 12 | ⏳ com provedor real: a fazer pelo usuário, se quiser (precisa da chave dele) |

Testes automáticos: 30 de 30 (`iniciar`, `ia`, `segredos`). JavaScript do `dashboard.html` sem erro
de sintaxe (`node --check`). ⏳ Conferir à vista o painel "IA" (avisos por provedor, campo de
chave, botão Remover) e o aviso de falha no Relatório.
