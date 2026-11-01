# Contrato: `fontes/_sessao.py` (área comum dos portais com login)

O módulo não faz pedido nenhum por conta própria. Ele só fala com a janela da ferramenta quando um portal com login
pede, e só dentro de `na_pagina`.

| Nome | Assinatura | Comportamento |
|---|---|---|
| `PortalComLoginErro` | `Exception(motivo, tipo)` | `tipo`: `"login"`, `"captcha"`, `"bloqueio"`, `"mudou"` ou `"janela"` |
| `na_pagina` | `contextmanager(esperar_login: Callable[[module, Aba], bool])` | Liga o contexto da busca da página, só durante o `with`. Aninhado ou em outra thread: erro de uso. |
| `dentro_da_pagina` | `() -> bool` | Diz se o contexto está ligado. |
| `aviso_fora` | `(modulo) -> str` | `"<ROTULO>: só pelo botão Buscar da página (portal com login)"` |
| `aviso_desconectado` | `(modulo) -> str` | `"<ROTULO>: ligado, mas sem conexão; conecte em Filtros da busca → Portais com login"` (o portal fica de fora da busca da página sem abrir a janela) |
| `janela` | `contextmanager()` | `NavegadorErro` (janela fechada, navegador ausente) vira `PortalComLoginErro(tipo="janela")` |
| `endereco` | `(aba) -> str` | `Aba.endereco()`: o endereço pelo histórico do navegador (`Page.getNavigationHistory`), sem rodar nada na página |
| `data_page` | `(modulo, aba) -> dict \| None` | `{component, version}` do app Inertia, só com `no_portal` |
| `conectados` | `() -> list[str]` | Lê `.cache/portais-login.json`; arquivo ausente ou inválido dá `[]`. |
| `marcar` | `(nome, conectado: bool) -> None` | Grava ou tira o portal, com a data. |
| `aba` | `(modulo) -> Aba` | Uma aba em segundo plano por busca e por portal (`navegador.abrir_para_leitura(URL_BUSCA)`), reaproveitada nos pedidos seguintes. `fechar_abas()` fecha no fim do `with`. |
| `no_portal` | `(modulo, aba) -> bool` | O host de `endereco(aba)` está em `modulo.DOMINIOS`. Toda leitura (`avaliar`) passa por aqui antes. |
| `pedir_json` | `(modulo, aba, url, cabecalhos) -> (status, dados \| None, endereço final)` | Faz `fetch(url, {credentials: "include", headers})` de dentro da aba, só se `no_portal` e só para um host de `DOMINIOS` (outro host: `ValueError`). Resposta que não é JSON dá `dados = None`; o endereço final mostra o redirecionamento ao login. |
| `garantir_login` | `(modulo, aba) -> None` | Se `modulo.logado(endereco(aba))` for falso: chama `esperar_login(modulo, aba)` do contexto. Com `True`, recarrega `URL_BUSCA`; com `False`, levanta `PortalComLoginErro(tipo="login")`. |
| `captcha_na_aba` | `(modulo, aba) -> bool` | Só com `no_portal`: iframe visível de captcha ou desafio (reCAPTCHA, hCaptcha, Cloudflare) ou texto de verificação. |
| `esperar` | `(modulo, aba, segundos=180, passo=3, cancelado=None, relogio=time.monotonic, dormir=time.sleep) -> bool` | Laço do callback padrão. Lê só `endereco(aba)` e `logado(url)`; para com `cancelado()` ou com a janela fechada. |
| `algum_conectado` | `() -> bool` | `conectados()` ou `contas.conectados()`. Decide se o Desconectar apaga o perfil inteiro. |
| `desconectar` | `(modulo) -> None` | `marcar(False)`. Se `algum_conectado()` ainda for verdadeiro, apaga `ORIGENS` e `ORIGENS_SSO` (`Storage.clearDataForOrigin`) numa aba própria (`abrir_para_leitura("about:blank")`, fechada no fim); se não, `navegador.desconectar()`. |

## Regras

- **Nunca** clicar, digitar, enviar formulário, ler senha ou copiar cookies. O único JavaScript que roda na aba é a
  leitura (`fetch` GET e consulta ao DOM), e só em host de `DOMINIOS`.
- Durante a espera de login, a ferramenta só olha o endereço da aba. Ela não lê nenhuma página do LinkedIn nem de outro
  serviço.
- A janela vem para a frente só para o login e o captcha. Depois, ela volta a ficar minimizada.
