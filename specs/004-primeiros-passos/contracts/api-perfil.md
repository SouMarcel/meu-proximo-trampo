# Contrato: primeiros passos

Rotas de escrita só do próprio computador (`403` com "Só dá para fazer isso no computador onde a
ferramenta roda."), com as proteções atuais do servidor. Erros de validação → `400 {"erro"}`.

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/perfil/estado` | — | `{existe_perfil, etapa, materiais: [{id, tipo, nome, avisos, trecho, tem_texto}], rascunho, respostas, contato, contatos_achados, perguntas, ia_disponivel, pode_alterar}` |
| `POST /api/perfil/material` | `{nome, base64}` ou `{texto, nome?}` (até 15 MB) | `{material, estado}`: o material criado (sem o texto inteiro: `trecho` de 600 caracteres) e o estado |
| `DELETE /api/perfil/material/<id>` | — | estado |
| `POST /api/perfil/rascunho` | `{sem_ia?}` | estado com `rascunho` (`origem` `ia` ou `sem_ia`; com IA: pedido ao provedor, até 2 min; sem IA ou `sem_ia`: a partir do ZIP) |
| `PUT /api/perfil/progresso` | `{etapa?, respostas?, escolhas?: {indice_conflito: indice_opcao}, contato?}` | estado |
| `POST /api/perfil/previa` | `{markdown?}` | `{markdown, diagnostico: [{tipo, mensagem, pergunta, ir}], textos: [{nome, texto}], diferencas: [{tipo: +/-, texto}] ou null, conflitos_pendentes}`; sem `markdown`, monta do rascunho e das respostas (sem IA e com perfil existente, parte do perfil atual) |
| `PUT /api/perfil` | `{markdown}` | `{gravado: caminho, anterior: caminho ou null}` |
| `GET /api/perfil/filtros-propostos` | — | `{filtros, mudancas, avisos, sugestao_en}` |
| `POST /api/perfil/filtros-propostos` | `{sugerir_en: true}` | o mesmo, com os cargos em inglês sugeridos pela IA (marcados em `sugestao_en`) |
| (existente) `PUT /api/config` | filtros | gravação dos filtros (sem mudança) |
| `DELETE /api/perfil/progresso` | — | recomeçar (apaga o progresso; os arquivos em anexos ficam) |

## Comandos (para a skill de chat e testes)

```text
PY primeiros_passos.py extrair <arquivo>       # texto mascarado + campos (ZIP do LinkedIn), em JSON
PY primeiros_passos.py diagnostico [perfil.md]  # achados do diagnóstico, em texto
PY primeiros_passos.py gravar <rascunho.md>     # grava o perfil revisado (versão anterior guardada)
```
