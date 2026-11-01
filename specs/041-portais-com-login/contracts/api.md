# Contrato: API do dashboard (portais com login)

Todas as rotas são **só locais**: pedido de outro aparelho recebe 403, como nas contas conectadas. Erro de navegador ou
de portal volta como 409, com a mensagem.

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/portais-login` | — | `{navegador: bool, portais: [{nome, rotulo, termos, aviso_risco, aviso_login, ligado, conectado, situacao, espera: {ate, motivo} \| null}]}` |
| `POST /api/portais-login/{portal}/conectar` | — | `{ok: true}`: abre a página de login na janela, na frente |
| `POST /api/portais-login/{portal}/pronto` | — | `{conectado: bool}`: confere `logado(url)` numa aba em segundo plano, só pelo endereço; com o login, grava e minimiza |
| `POST /api/portais-login/{portal}/desconectar` | — | `{ok: true}`: `_sessao.desconectar` |

- O **liga/desliga** usa o salvamento de sempre dos filtros (`fontes` com ou sem `"mygreenhouse"`). A página pede a
  confirmação de `aviso_risco` antes de mandar o portal ligado.
- `situacao` pode ser `desligado`, `em_espera`, `desconectado` ou `conectado` (data-model.md).
- `{portal}` fora de `filtros.FONTES_LOGIN` recebe 404 "portal desconhecido".

## Mudanças em rotas existentes

- **`GET /api/busca/estado`** (`BUSCA.estado()`): `situacao` pode ser `"aguardando_login"`, e o campo novo
  `login: {portal, rotulo, ate} | null` acompanha. A página mostra "Aguardando login no MyGreenhouse Jobs: entre na
  janela da ferramenta (faltam N s)".
- **`GET /api/busca/plano`**: conta os pedidos do portal com login quando ele está ligado e conectado. Se estiver ligado
  e desconectado, avisa "conecte em Portais com login".
- **`POST /api/contas/{portal}/desconectar`**: o perfil inteiro só é apagado se não sobrar nenhum portal conectado,
  somando contas conectadas e portais com login.
- **Painel de filtros**: `fontes` aceita `"mygreenhouse"`, e `GET /api/config` mostra o portal na lista de portais com
  login, não na dos portais de busca pública.
