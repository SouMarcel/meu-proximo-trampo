# Contrato: buscar vagas pela página

Rotas de escrita só do próprio computador (`403` com "Só dá para fazer isso no computador onde a
ferramenta roda."), com as proteções atuais do servidor (host, origem, JSON). Erros de validação →
`400 {"erro"}`; busca já rodando ou fora do intervalo → `409 {"erro", "estado"}`.

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/busca/plano` | — | `{filtros_ok, perfil_ok, consultas, portais: [nome], cargos: [texto], janela_horas, estimativa_min, ia: {ligada, nome, modelo, cobranca}, ultima: {fim, origem, situacao} ou null, proxima_em: ISO ou null, recente: bool}` |
| `GET /api/busca` | — | estado da busca (data-model.md) + `analise: {rodando, faltam, erro}` + `pode_alterar` |
| `POST /api/busca` | `{sem_nota?: bool, confirmar_recente?: bool}` | `202` estado; `400` sem cargos; `409` busca em andamento (página ou terminal), antes do intervalo mínimo, ou recente sem `confirmar_recente` |
| `DELETE /api/busca` | — | estado (`cancelando` ou o atual se não há busca da página) |
| `POST /api/busca/analisar` | `{}` | `{analise}`: pede de novo a nota das vagas que esperam |
| (existente) `GET /api/versao` | — | ganha `busca: {situacao, origem}` |

## Linha de comando (sem mudança de uso)

```text
PY vagas.py buscar [--gravar]   # recusa com código 4 se há busca rodando pela página
PY vagas.py gravar [...]        # igual
```
