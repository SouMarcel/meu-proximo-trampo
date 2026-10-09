# Contrato: configuração e rotas da área internacional

Sem rota nova: os filtros continuam pelo `GET/PUT /api/config` (escrita com as proteções atuais).

| Rota | Mudança |
|---|---|
| `GET /api/config` | `filtros` traz `idiomas_aceitos` e o `internacional` completo (data-model.md); `opcoes` ganha `idiomas`, `regioes`, `contratacao` |
| `PUT /api/config` | aceita os campos novos; `400` com mensagem para valores inválidos ou internacional ligada sem países/cargos |
| `GET /api/vagas` | cada vaga traz `area`, `pais_vaga`, `idioma` quando houver |
| `POST /api/vagas` e `/api/vagas/link` | aceitam `area` e `pais_vaga`; o link devolve o palpite em `parcial` e na vaga |

Linha de comando: sem mudança de uso (`vagas.py buscar` respeita a área de cada fonte).
