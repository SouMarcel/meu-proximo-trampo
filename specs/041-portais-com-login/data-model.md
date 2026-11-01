# Modelo de dados: portais com login na busca

## Portal com login (módulo em `fontes/`)

Atributos de fonte comuns (`fontes/__init__.py`) mais os da área:

| Atributo | MyGreenhouse | Uso |
|---|---|---|
| `COM_LOGIN` | `True` | marca o portal da área; fora da página, `buscar` só avisa |
| `ROTULO` | `"MyGreenhouse Jobs"` | painel |
| `URL_LOGIN` | `https://my.greenhouse.io/users/sign_in` | Conectar |
| `URL_BUSCA` | `https://my.greenhouse.io/jobs/search` | carga da aba (versão do Inertia) e pedidos |
| `DOMINIOS` | `("my.greenhouse.io",)` | só nesses hosts a ferramenta lê a página |
| `ORIGENS` | `("https://my.greenhouse.io",)` | apagadas no Desconectar |
| `ORIGENS_SSO` | `("https://www.linkedin.com", "https://linkedin.com")` | apagadas no Desconectar (o login pelo LinkedIn) |
| `AVISO_RISCO` | os termos proíbem automação; a Greenhouse pode limitar, suspender ou encerrar a conta | confirmação ao ligar |
| `AVISO_LOGIN` | pode entrar pelo LinkedIn, e a ferramenta não lê as páginas dele; o login por e-mail do MyGreenhouse é preferível | painel |
| `logado(url)` | host em `DOMINIOS` e caminho fora de `/users/sign_in` | Pronto e espera de login, só pelo endereço |

## Conexão (`.cache/portais-login.json`)

```json
{"conectados": {"mygreenhouse": {"desde": "2026-11-01"}}}
```

- Pronto com `logado(url)` verdadeiro leva o portal a `conectados`. Desconectar o tira de lá.
- **Situação no painel**, nesta ordem:
  1. `desligado`: o portal não está em `fontes`;
  2. `em_espera`: há espera ativa (mostra o fim);
  3. `desconectado`: não está em `conectados`;
  4. `conectado`.

  A situação `aguardando_login` só existe durante a busca e vem do estado da busca.
- **Desconectar**: apaga `ORIGENS` e `ORIGENS_SSO` no perfil da janela. Se não sobrar nenhum portal conectado (contas
  conectadas e portais com login), fecha a janela e apaga o perfil.

## Espera (`.cache/mygreenhouse-espera.json`)

O formato é o de `_comum.gravar_espera`: `{"ate": ISO, "motivo": texto}`. Dura 24 h e começa no primeiro bloqueio
(403, 429, 503 ou desafio).

## Vaga (formato comum de `fontes/__init__.py`)

| Campo | Origem (`jobPosts[]`) |
|---|---|
| `id` | `_comum.ident("greenhouse", f"{urlToken}-{id}")`, igual ao das empresas acompanhadas |
| `plataforma` | `"MyGreenhouse"` |
| `ats` | `"greenhouse"` (ativa o "Acompanhar empresa") |
| `titulo` | `title` |
| `empresa` | `companyName` |
| `local` | `locations` juntos com "; " |
| `restricao_local` | o mesmo texto (entrada de `filtros.aberta_ao_pais`) |
| `remoto`, `modelo_trabalho` | `workType`: `remote` → `True`, `"remoto"`; `hybrid` → `"hibrido"`; `onsite`/`on-site` → `"presencial"` |
| `publicada_em` | `firstPublished[:10]` |
| `url` | `publicUrl` |
| `descricao` | vazia na lista; `descrever` lê a API pública (`ats.ler`) |
| descartados | `viewed`, `appliedAt`, `saved`, `departmentId`, `logoUrl`, `summary`, `description` (nulos), `payRanges` (enquanto nulo) |

## Estado da busca da página (`dash/buscador.py`)

Campos novos em `BUSCA.estado()`:
- `situacao`: além das atuais, `"aguardando_login"`.
- `login`: `{"portal": "mygreenhouse", "rotulo": "MyGreenhouse Jobs", "ate": ISO}` enquanto espera; `null` fora dela.

**Transições**:

```
consultando → aguardando_login   o portal pediu login
aguardando_login → consultando   logou, ou o tempo acabou e o portal foi pulado com aviso em "erros"
aguardando_login → cancelando    a pessoa cancelou; a espera termina no próximo passo de 3 s
```

## Config (`config.json`)

Sem formato novo. `fontes` aceita `"mygreenhouse"` (`filtros.FONTES_LOGIN`), que não entra em `FONTES_PADRAO`.
