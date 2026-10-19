# Contrato: `fontes/nerdin.py`

Segue o contrato de `fontes/__init__.py`, sem mudá-lo.

## Atributos

```python
NOME = "nerdin"
PLATAFORMA = "Nerdin"
AREAS = ("nacional",)
TERMOS = ("Consulta não oficial à busca pública da Nerdin, portal só de vagas de tecnologia no Brasil, sem login. "
          "Há uma pausa de alguns segundos entre as consultas e, se a Nerdin limitar, a busca segue sem ela. "
          "A candidatura é sempre na própria Nerdin.")
MAX_DESCRICOES = 30
MAX_PAGINAS = 5
POR_PAGINA = 20
PAUSA = 3.0
```

## Funções

`buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]`
- `consulta["pais"] != "brazil"` → `([], [])`, sem pedido.
- Bloqueada nesta busca → `([], [])`, sem pedido (o aviso já saiu).
- Lê (ou reaproveita) a lista do cargo; filtra por título (`_comum.bate_cargo`), janela, grupo/modelos e
  cidade/UF (research R6); devolve até `max(1, por_termo)` vagas.
- Erro de leitura → as vagas já lidas e `["<mensagem>"]` (o mesmo erro sai uma vez por cargo).
- Página sem nenhum card reconhecível mas com conteúdo de lista → `["não consegui ler as vagas da Nerdin (a página
  pode ter mudado)"]`.

`descrever(vaga: dict) -> str`
- Bloqueada → `vaga.get("descricao") or ""`, sem pedido.
- Senão, a descrição do JSON-LD da página da vaga (até 12 000 caracteres). Erro → exceção (o `vagas.py` registra e
  segue).

`parada() -> bool` — bloqueada nesta busca.

`ler_lista(pagina: str) -> list[dict]` — as vagas de uma página de resultados, no formato comum (testável sem rede).

`id_do_link(url: str) -> str | None` — `nerdin-<n>` para `https://www.nerdin.com.br/vaga_emprego/vaga-<slug>-<n>.php`
(com ou sem `www`, com ou sem parâmetros); `None` para outros links.

## Pedidos

- `GET https://www.nerdin.com.br/vagas.php?busca=<cargo sem aspas>[&pagina=N]` (N a partir de 2).
- `GET <url da vaga>` em `descrever`.
- Cabeçalhos: `User-Agent: _comum.AGENTE`, `Accept-Language: pt-BR`. Sem cookies. Tempo limite 20 s; resposta
  acima de 3 MB → erro.
- Pausa mínima de `PAUSA` segundos entre dois pedidos à Nerdin.
- 403, 429, 503 → bloqueio: `FonteErro("a Nerdin limitou as consultas (código N); a busca seguiu sem ela")`, sem nova
  tentativa.

## Mudanças em outros módulos

| Módulo | Mudança |
|---|---|
| `fontes/__init__.py` | importa e registra `nerdin` em `FONTES` |
| `fontes/link.py` | `plataforma()` → `("nerdin.", "Nerdin")`; `ler()` → ramo Nerdin com `id_do_link` e `extrair_jobposting` |
| `filtros.py` | `FONTES_NAC` com `"nerdin": "Nerdin"` depois da Gupy; `FONTES_PADRAO = ["indeed", "gupy", "nerdin"]` |
| `vagas.py` | `fontes_da_busca`: `cfg.get("fontes", filtros.FONTES_PADRAO)` |
| `dash/banco.py` | `PLATAFORMAS` com `"Nerdin"` |
| `dash/dashboard.html` | `PLATAFORMAS`, par `["nerdin.", "Nerdin"]` em `plataformaDoLink`, `.plat[data-p="Nerdin"] i` |
| `config.exemplo.json` | `"fontes": ["indeed", "gupy", "nerdin"]` |
