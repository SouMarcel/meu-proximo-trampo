# Contratos: JobGether na busca de vagas

## 1. Módulo `fontes/jobgether.py` (contrato de `fontes/__init__.py`)

| Nome | Valor ou assinatura |
|---|---|
| `NOME` | `"jobgether"` (em `config.json` → `fontes`) |
| `PLATAFORMA` | `"JobGether"` |
| `AREAS` | `("nacional", "internacional")` |
| `POR_PAIS`, `GLOBAL` | `True`, `True` |
| `TERMOS` | resumo para o painel: API oficial para assistentes, termos que proíbem acesso automatizado, decisão registrada na spec 030, vagas sem descrição, espera de 24 h no bloqueio |
| `buscar(consulta, horas, por_termo)` | `(vagas, erros)`; consulta da cidade ou de mudança devolve `([], [])` sem pedido |
| `pausa()` | `_comum.pausa_do_env("JOBGETHER_PAUSA", (2.0, 2.0), 2.0)` |
| `aviso_pausa(consultas)` | aviso com até `consultas × MAX_PAGINAS` pedidos |
| `espera()` | `{"ate", "motivo"}` nas 24 h depois do bloqueio, ou `None` |
| `parada()` | bloqueou nesta busca ou está em espera |
| `id_do_link(url)` | `"jobgether-<24 hex>"` para `https://jobgether.com/offer/<24 hex>-…` (com ou sem `www.`); `None` para outro link |

O módulo não tem `descrever()` nem `MAX_DESCRICOES`: não há de onde tirar a descrição.

## 2. Pedido à API

```
POST https://jobgether.com/api/v1/jobs
User-Agent: meu-proximo-trampo (ferramenta local de busca de vagas)
Content-Type: application/json
Accept: application/json

{"keyword": "<cargo sem aspas>", "locations": ["<slug>"], "sort": "date", "limit": 25, "page": <1..3>,
 "includeHybrid": true}          # includeHybrid só na consulta do país quando a pessoa aceita híbrido
```

| Resposta | Efeito |
|---|---|
| 200 `{"jobs": [...], "pagination": {"hasMore": bool}}` | vagas normalizadas; próxima página se `hasMore` e ainda dentro da janela |
| 403, 429 | bloqueio: `FonteErro("o JobGether limitou as consultas (código N); em espera até HH:MM")`, espera gravada, nenhum pedido a mais |
| 400 `field = "locations"` | aviso "o JobGether não reconhece o local <slug>", uma vez por busca |
| outro 4xx/5xx, rede | `FonteErro` só daquela consulta, sem nova tentativa |
| corpo fora do formato | `FonteErro("não consegui ler as vagas do JobGether (a API pode ter mudado)")` |

## 3. Dashboard (`dash/API.md`)

- `plataforma`: soma `JobGether` à lista de valores.
- `fontes`, nos filtros da busca: soma `jobgether`, com o rótulo "JobGether" e o `termos` do módulo.
- `POST /api/vagas/link` com link do JobGether responde 422
  `{erro: "o JobGether não deixa a ferramenta ler a página da vaga; complete cargo, empresa e descrição", parcial: {url, plataforma: "JobGether", area, pais_vaga}}`,
  e o formulário abre pré-preenchido.
- O `POST` de vaga manual com `url` do JobGether grava com id `jobgether-<id>`. Se a vaga já existe, devolve a que
  existe.

## 4. `.env`

```ini
# JOBGETHER_PAUSA=2   # padrão 2 s; mínimo 2 s (API oficial, Crawl-delay do site)
```

## 5. Candidatura assistida

`candidatura/dominios.BLOQUEADOS["jobgether.com"] = "os termos do JobGether proíbem acesso automatizado"`
