# Contrato: `fontes/mygreenhouse.py`

Segue `fontes/__init__.py` e usa os atributos de portal com login (data-model.md). Constantes:

| Nome | Valor |
|---|---|
| `NOME`, `PLATAFORMA`, `ROTULO` | `"mygreenhouse"`, `"MyGreenhouse"`, `"MyGreenhouse Jobs"` |
| `AREAS`, `POR_PAIS`, `GLOBAL` | `("nacional", "internacional")`, `True`, `True` |
| `COM_LOGIN` | `True` |
| `TERMOS` | Busca do MyGreenhouse Jobs com o login da pessoa, na janela da ferramenta. Os termos do MyGreenhouse proíbem acesso automatizado, e a Greenhouse pode suspender a conta. Entra por decisão registrada na spec 041 e vem desligado. Roda só pelo botão Buscar da página, com pausa e 24 horas de espera se limitar. |
| `PAISES` | `{"brazil": {"location": "Brazil", "lat": "-11.929178", "lon": "-49.542799", "location_type": "country", "country_short_name": "BR"}}` |
| `POR_PAGINA`, `MAX_PAGINAS`, `MAX_DESCRICOES` | 12, 3, 30 |
| `JANELA_5_DIAS` | 120 (horas): até esse valor, vai `date_posted=past_five_days` |
| `PAUSA`, `VAR_PAUSA`, `PAUSA_MIN`, `PAUSA_FAIXA` | `(3.0, 7.0)`, `"MYGREENHOUSE_PAUSA"`, 3.0, 4.0 |
| `ESPERA`, `ARQ_ESPERA` | 24 horas, `.cache/mygreenhouse-espera.json` |
| `BLOQUEIOS` | 403, 429, 503 |
| `PROPS` | `"browsing,page,moreResultsAvailable,jobPosts"` (nunca `trackingData` nem `recentSearches`) |

## Funções

- `logado(url) -> bool`: host `my.greenhouse.io` e caminho fora de `/users/sign_in`.
- `endereco(cargo, consulta, horas, pagina) -> str`: monta `URL_BUSCA` com `query` (sem aspas), `work_type[]=remote`,
  o local do país (consulta nacional), `date_posted` (janela de até 120 h) e `page` (a partir de 2).
- `ler_resposta(dados) -> (vagas, mais: bool)`: `props.jobPosts` no formato comum (data-model.md), com os campos da conta
  descartados. Sem `props.jobPosts`, levanta `_sessao.PortalComLoginErro(tipo="mudou")`.
- `buscar(consulta, horas, por_termo) -> (vagas, erros)`:
  - **fora da página**: `([], [aviso_fora])` uma vez por busca, sem abrir a janela;
  - **em espera**: aviso uma vez;
  - **nacional**: só o grupo remoto com país em `PAISES`; os outros grupos e países, `([], [])`. **Internacional**: só
    a consulta global, sem local;
  - pede até `MAX_PAGINAS` (para com `mais = False`) e filtra pelo cargo (`_comum`), pela janela
    (`publicada_em`) e, no grupo remoto nacional, por `filtros.aberta_ao_pais`.
  - Parada no primeiro problema, sem nova tentativa:

    | Problema | O que acontece |
    |---|---|
    | 409 | recarrega a aba uma vez por busca; se repetir, "mudou" |
    | 401, ou redirecionamento ao login | `_sessao.garantir_login` |
    | `BLOQUEIOS` ou desafio | `_comum.gravar_espera`, `parada()` e aviso com o fim da espera |
    | captcha | aviso "resolva na janela e busque de novo" e a janela na frente |
    | "mudou" ou "janela" | aviso, e o portal fica fora do resto da busca |
- `descrever(vaga) -> str`: `ats.ler(vaga["url"])["descricao"]`, pela API pública e sem a sessão. Em erro, devolve o
  que a vaga já tinha.
- `pausa()`, `aviso_pausa(consultas)`, `espera()` e `parada()`: como na FullStack. `aviso_pausa` conta
  `MAX_PAGINAS × cargos + 1`.
