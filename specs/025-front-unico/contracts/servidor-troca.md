# Contrato do servidor depois da troca (História 7)

Só as rotas de página mudam; as rotas `/api/...` e `/arquivos/...` ficam como estão no `dash/API.md`.

| Pedido | Antes | Depois |
|---|---|---|
| `GET /` e `GET /index.html` | `dash/dashboard.html` | `dash/front/index.html` |
| `GET /assets/<arquivo>`, `/favicon.svg` | 404 | arquivo de `dash/front/` (só os tipos de `TIPOS_FRONT`, dentro da pasta) |
| `GET /robots.txt` | 404 | 404 (`.txt` continua fora de `TIPOS_FRONT`; a página é local) |
| `GET /novo` | 308 → `/novo/` | 308 → `/` |
| `GET /novo/` e `/novo/index.html` | front novo | 308 → `/` |
| `GET /novo/<arquivo>` | arquivo de `dash/front/` | 308 → `/<arquivo>` (favoritos e abas abertas continuam funcionando) |
| `GET /` sem `dash/front/index.html` | — | 404 com aviso em HTML: "front não montado" e o que fazer |
| `GET /dashboard.html` | (Live Server só) | 404 |
| `GET /favicon.ico` | 204 | 204 |

Regras que continuam:
- caminho resolvido dentro de `dash/front/`;
- recusa de `..`, `%2e%2e` e barra invertida;
- só os tipos `.html .js .css .svg .png .woff2`;
- os mesmos cabeçalhos de segurança de `_enviar`.

Arquivos que saem: `dash/dashboard.html`. Constante que sai: `PAGINA`.

## Testes (`tests/test_front_estatico.py`)

- `/` entrega o `index.html` do front, e `/assets/x.js` entrega o arquivo com o tipo certo.
- `/novo`, `/novo/` e `/novo/assets/x.js` respondem 308 para o endereço equivalente na raiz.
- Pedidos para fora da pasta e de tipo desconhecido continuam 404.
- Sem build, `/` mostra o aviso.
- Sai o `test_dashboard_atual_continua_em_raiz`.
