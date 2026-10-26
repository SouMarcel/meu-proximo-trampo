# Contratos: Empresas acompanhadas na busca nacional

## 1. Configuração (`GET`/`PUT /api/config`)

- `filtros.empresas`: `[{sistema, id, nome, url}]`, no máximo 50, no nível de cima de `filtros`. Sai de
  `filtros.internacional`.
- `PUT`:
  - aceita `empresas` no nível de cima (front novo);
  - sem essa chave, aceita `internacional.empresas` (front antigo);
  - grava sempre em cima;
  - o item pode ser o link (texto) ou `{url}`; o servidor reconhece o sistema e o nome.
- Erro 400:
  - "empresas: no máximo 50";
  - "<link>: não é uma página de vagas do Greenhouse, do Lever nem do Ashby (ex.: …)";
  - a regra da internacional ligada continua: "escolha pelo menos um país, uma fonte do exterior ou uma empresa para
    a busca internacional", agora contando a lista de cima.
- `consultas`: soma as consultas nacionais das empresas no mesmo número que já conta os cargos. A lista é baixada uma
  vez por empresa, sem consulta a mais por cargo.

## 2. Acompanhar

**`GET /api/empresas`** responde `{empresas: Empresa[], maximo: 50}`.

**`POST /api/empresas`** recebe `{url*: string}` (até 1.000 caracteres): o link da página de vagas ou de uma vaga do
Greenhouse, do Lever ou do Ashby.

| Resposta | Corpo |
|---|---|
| 201 (nova) | `{empresa: Empresa, nova: true, empresas: Empresa[]}` |
| 200 (já estava) | `{empresa: Empresa, nova: false, empresas: Empresa[]}` |
| 400 | link não reconhecido, ou "a lista de empresas está cheia (50); remova uma no painel Filtros da busca" |

Não faz pedido ao sistema da empresa e grava só a chave `empresas` do `config.json`.

## 3. Adicionar Vaga (`POST /api/vagas/link`)

Quando o link é de vaga do Greenhouse, do Lever ou do Ashby, a resposta 201/200 ganha
`empresa: {sistema, id, nome, url, acompanhada: bool}`. Nos outros links, a chave não vem.

## 4. Fonte `fontes/ats.py`

| Nome | Valor |
|---|---|
| `AREAS` | `("nacional", "internacional")` |
| `POR_PAIS`, `GLOBAL` | `True`, `True` |
| `buscar(consulta, horas, por_termo)` | `remoto`, `pais`, `local` e global atendidas; `internacional:<p>` e `mudanca:<p>` → `([], [])` sem pedido |
| `ler(url)` | como hoje, sem nova tentativa no 429 |

| Resposta da API do sistema | Efeito |
|---|---|
| 200 | vagas da empresa, filtradas pela consulta |
| 403, 429 | o sistema para até o fim da busca, com um aviso só e sem nova tentativa; as empresas dele não fazem pedido |
| 404 | aviso da empresa: página de vagas não existe mais; remover ou trocar o link |
| outro erro, rede | aviso da empresa; as outras seguem |

## 5. `fontes/_comum.py`

- `baixar(url, params=None, aceitar=..., nova_tentativa=True)` e `baixar_json(url, params=None, nova_tentativa=True)`:
  com `False`, o 429 vira `FonteErro` na hora.
- `FonteErro(motivo, repetido=False, codigo=None)`: `codigo` é o status HTTP quando houver.

## 6. `filtros.py`

- `aberta_ao_pais(texto, pais) -> bool`: o local cita o país, uma região que o inclui ou "mundo todo".
- `acompanhar(url) -> (empresa, nova, empresas)`: levanta `ValueError` com a mensagem do 400.
