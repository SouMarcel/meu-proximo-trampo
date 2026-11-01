"""Fonte MyGreenhouse Jobs: a busca de vagas entre as empresas do Greenhouse (my.greenhouse.io/jobs/search), que só
aparece com login. É o primeiro portal da área "Portais com login" (spec 041; constituição, princípio VI, "Busca com
login"; regras comuns em fontes/_sessao.py).

Os termos do MyGreenhouse (User Agreement de 29/01/2025) proíbem acesso automatizado, e a Greenhouse pode suspender a
conta. A pessoa decidiu tê-lo na busca ("Termos contrários"), desligado por padrão: quem quiser liga no painel,
confirmando o aviso de risco, e conecta pela janela da ferramenta, com o login feito por ela.

A leitura roda só no botão Buscar da página, numa aba em segundo plano da janela da ferramenta:
- a página da busca é um app Inertia: a lista vem em JSON do mesmo endereço da busca, pedido de dentro da aba com os
  cabeçalhos do Inertia (a versão vem do data-page da primeira carga), como a própria página faz;
- cada cargo vai com o filtro remoto e, na área nacional, o local do país da pessoa (só o Brasil é conhecido); com a
  janela de até 5 dias, vai também "postadas nos últimos 5 dias". Até MAX_PAGINAS páginas de 12 vagas por cargo;
- a vaga tem o mesmo id das empresas acompanhadas (greenhouse-<empresa>-<id>), então não duplica; os dados da conta
  (vista, salva, candidatura) ficam de fora;
- a descrição vem da API pública do quadro da empresa (fontes/ats.py), sem a sessão.

Pausa sorteada de 3 a 7 segundos entre os pedidos (MYGREENHOUSE_PAUSA=N no .env muda para N a N+4, com N de 3 a 60).
No primeiro bloqueio (403, 429 ou 503), o portal sai da busca, sem nova tentativa, e das buscas das 24 horas
seguintes (a espera, gravada em .cache/). Captcha, login não feito, janela fechada ou página que a ferramenta não
reconhece param o portal só nesta busca, com aviso.
"""
from __future__ import annotations

import re
import sys
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from . import _comum, _sessao, ats

NOME = "mygreenhouse"
PLATAFORMA = "MyGreenhouse"
ROTULO = "MyGreenhouse Jobs"
AREAS = ("nacional", "internacional")
POR_PAIS = True  # a consulta remota no país…
GLOBAL = True  # …e a consulta internacional global (sem local)
COM_LOGIN = True
TERMOS = ("Busca do MyGreenhouse Jobs com o seu login, na janela da ferramenta. Os termos do MyGreenhouse proíbem "
          "acesso automatizado, e a Greenhouse pode suspender a conta. Entra por decisão registrada na spec 041 e vem "
          "desligado. Roda só pelo botão Buscar da página, com pausa entre os pedidos e 24 horas de espera se o portal "
          "limitar.")
AVISO_RISCO = ("Os termos do MyGreenhouse proíbem acesso automatizado (robôs e programas que leem o site). A Greenhouse "
               "pode limitar, suspender ou encerrar a sua conta do MyGreenhouse. A ferramenta só lê os resultados da "
               "busca quando você clica em Buscar na página, com pausa entre os pedidos, e para no primeiro bloqueio.")
AVISO_LOGIN = ("Entre na janela da ferramenta. O login por e-mail do MyGreenhouse é o mais indicado. O \"Entrar com "
               "LinkedIn\" também funciona, mas usa a sua conta do LinkedIn nesse acesso; a ferramenta não lê nem age "
               "nas páginas do LinkedIn.")

URL_LOGIN = "https://my.greenhouse.io/users/sign_in"
URL_BUSCA = "https://my.greenhouse.io/jobs/search"
DOMINIOS = ("my.greenhouse.io",)
ORIGENS = ("https://my.greenhouse.io",)
ORIGENS_SSO = ("https://www.linkedin.com", "https://linkedin.com")

# nome do jobspy -> parâmetros de local da busca (o local escolhido na página vira coordenadas)
PAISES = {"brazil": {"location": "Brazil", "lat": "-11.929178", "lon": "-49.542799", "location_type": "country",
                     "country_short_name": "BR"}}
POR_PAGINA = 12  # o portal devolve 12 vagas por página
MAX_PAGINAS = 3  # por cargo
MAX_DESCRICOES = 30  # descrições lidas por busca (pela API pública); as outras ficam pendentes
JANELA_5_DIAS = 120  # horas: até esse valor, a busca vai com "postadas nos últimos 5 dias"
PAUSA = (3.0, 7.0)  # padrão, sem MYGREENHOUSE_PAUSA
VAR_PAUSA = "MYGREENHOUSE_PAUSA"
PAUSA_MIN, PAUSA_FAIXA = 3.0, 4.0  # N de 3 a 60; a pausa é sorteada de N a N + 4
ESPERA = timedelta(hours=24)
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "mygreenhouse-espera.json"
BLOQUEIOS = (403, 429, 503)
PROPS = "browsing,page,moreResultsAvailable,jobPosts"  # nunca trackingData nem recentSearches
MODELOS = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial", "on-site": "presencial",
           "in_office": "presencial", "in-office": "presencial"}
BLOQUEIO = "o MyGreenhouse limitou as consultas"
MUDOU = "a página de busca do MyGreenhouse mudou; a leitura precisa de ajuste"
CAPTCHA = ("o MyGreenhouse pediu uma verificação (captcha): resolva na janela da ferramenta e busque de novo; o portal "
           "ficou de fora desta busca")
ID = re.compile(r"^greenhouse-(.+)-(\d+)$")

_estado = {"bloqueado": False, "fora": None, "ultimo": None, "pausa": None, "aba": None, "versao": None,
           "recarregou": False, "relogou": False, "avisou_espera": False, "avisou_fora": False}


def _esquecer() -> None:
    _estado.update(bloqueado=False, fora=None, pausa=None, aba=None, versao=None, recarregou=False, relogou=False,
                   avisou_espera=False, avisou_fora=False)


_comum.AO_ESQUECER.append(_esquecer)


def _eu():
    return sys.modules[__name__]


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def logado(url: str) -> bool:
    """A aba está no MyGreenhouse e fora das páginas de login (/users/…: entrar, senha, retorno do LinkedIn)."""
    p = urlsplit(str(url or ""))
    return (p.hostname or "").lower() in DOMINIOS and not p.path.startswith("/users/")


# ---------------------------------------------------------------- pausa, bloqueio e espera

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou MYGREENHOUSE_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN, faixa=PAUSA_FAIXA)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com MYGREENHOUSE_PAUSA definida: até MAX_PAGINAS pedidos por cargo, mais a carga da
    página."""
    return _comum.aviso_pausa(PLATAFORMA, "no MyGreenhouse", VAR_PAUSA, pausa(),
                              MAX_PAGINAS * consultas + 1 if consultas else 0)


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    _comum.pausar(_estado, _estado["pausa"])


def espera(agora: datetime | None = None) -> dict | None:
    """{"ate", "motivo"} nas ESPERA horas depois do último bloqueio; None fora delas ou sem arquivo legível."""
    return _comum.ler_espera(ARQ_ESPERA, ESPERA, agora)


def parada() -> bool:
    """Bloqueou nesta busca ou está em espera: a vaga sem texto fica pendente, sem pedido."""
    return _estado["bloqueado"] or espera() is not None


def _bloquear(motivo: str) -> _sessao.PortalComLoginErro:
    _estado.update(bloqueado=True, avisou_espera=True)
    ate = (_comum.gravar_espera(ARQ_ESPERA, motivo) + ESPERA).isoformat(timespec="minutes")
    return _sessao.PortalComLoginErro(f"{BLOQUEIO} ({motivo}); em espera até {_comum.ate_quando(ate)}", "bloqueio")


# ---------------------------------------------------------------- leitura

def _espacos(s) -> str:
    return " ".join(str(s or "").split())


def _canonico(token: str, jid: str) -> str:
    return f"https://job-boards.greenhouse.io/{token}/jobs/{jid}"


def endereco(cargo: str, consulta: dict, horas: int, pagina: int = 1) -> str:
    """O endereço da busca: o cargo (sem aspas), o filtro remoto, o local do país (consulta nacional), "postadas nos
    últimos 5 dias" (janela de até 120 horas) e a página (a partir da 2)."""
    params = [("query", str(cargo or "").strip().strip('"'))]
    if consulta.get("remoto", True):
        params.append(("work_type[]", "remote"))
    if not consulta.get("global"):
        params += list(PAISES[str(consulta.get("pais") or "").lower()].items())
    if int(horas or 0) <= JANELA_5_DIAS:
        params.append(("date_posted", "past_five_days"))
    if pagina > 1:
        params.append(("page", str(pagina)))
    return f"{URL_BUSCA}?{urlencode(params)}"


def _vaga(r) -> dict | None:
    """Uma vaga da lista no formato comum. Ficam de fora os dados da conta (viewed, appliedAt, saved) e o resto que
    a lista traz vazio ou que a ferramenta não usa."""
    if not isinstance(r, dict):
        return None
    token, jid, titulo = _espacos(r.get("urlToken")), _espacos(r.get("id")), _espacos(r.get("title"))
    if not token or not jid.isdigit() or not titulo:
        return None
    lugares = [_espacos(x if isinstance(x, str) else (x or {}).get("name")) for x in r.get("locations") or []]
    local = "; ".join(x for x in lugares if x)
    modelo = MODELOS.get(str(r.get("workType") or "").strip().lower())
    remoto = modelo == "remoto"
    url = str(r.get("publicUrl") or "").strip()
    v = {"id": _comum.ident("greenhouse", f"{token}-{jid}"), "plataforma": PLATAFORMA, "ats": "greenhouse",
         "titulo": titulo, "empresa": _espacos(r.get("companyName")) or token, "local": local or ("Remoto" if remoto else ""),
         "remoto": remoto, "publicada_em": _comum.data_iso(r.get("firstPublished")),
         "url": url if url.startswith("https://") else _canonico(token, jid), "url_candidatura": None,
         "salario": None, "tipo": None, "descricao": ""}
    if modelo:
        v["modelo_trabalho"] = modelo
    if remoto and local:
        v["restricao_local"] = _comum.curto(local)
    return v


def ler_resposta(dados) -> tuple[list[dict], bool]:
    """(vagas, há mais páginas) de uma resposta do Inertia; sem props.jobPosts, o portal mudou."""
    props = dados.get("props") if isinstance(dados, dict) else None
    posts = props.get("jobPosts") if isinstance(props, dict) else None
    if not isinstance(posts, list):
        raise _sessao.PortalComLoginErro(MUDOU, "mudou")
    vagas = [v for v in (_vaga(r) for r in posts) if v]
    return vagas, bool(props.get("moreResultsAvailable"))


def _preparar():
    """A aba da busca pronta: aberta (a carga da página conta como um pedido), logada, sem captcha e com a versão do
    app lida do data-page."""
    if _estado["versao"]:
        return _estado["aba"]
    eu = _eu()
    a = _estado["aba"]
    if a is None:
        _pausar()
        a = _estado["aba"] = _sessao.aba(eu)
    _sessao.garantir_login(eu, a)
    if _sessao.captcha_na_aba(eu, a):
        a.frente()
        raise _sessao.PortalComLoginErro(CAPTCHA, "captcha")
    pagina = _sessao.data_page(eu, a)
    if not pagina or not pagina.get("version"):
        raise _sessao.PortalComLoginErro(MUDOU, "mudou")
    _estado["versao"] = str(pagina["version"])
    return a


def _pedir(url: str):
    """Um pedido à lista, de dentro da aba, sem nova tentativa: 409 (versão nova do site) recarrega uma vez; sem
    login, espera a pessoa entrar uma vez; 403, 429 e 503 são bloqueio."""
    a = _preparar()
    cabecalhos = {"X-Inertia": "true", "X-Inertia-Version": _estado["versao"], "X-Inertia-Partial-Component": "jobs",
                  "X-Inertia-Partial-Data": PROPS, "X-Requested-With": "XMLHttpRequest",
                  "Accept": "text/html, application/xhtml+xml"}
    _pausar()
    status, dados, final = _sessao.pedir_json(_eu(), a, url, cabecalhos)
    if status in BLOQUEIOS:
        raise _bloquear(f"código {status}")
    if status == 409:
        if _estado["recarregou"]:
            raise _sessao.PortalComLoginErro(MUDOU, "mudou")
        _estado.update(recarregou=True, versao=None)
        _pausar()
        a.ir(URL_BUSCA)
        return _pedir(url)
    if status == 401 or (final and not logado(final)):
        if _estado["relogou"]:
            raise _sessao.PortalComLoginErro(f"{ROTULO}: a sessão caiu de novo; o portal ficou de fora desta busca",
                                             "login")
        _estado.update(relogou=True, versao=None)
        _pausar()
        a.ir(URL_BUSCA)
        return _pedir(url)
    if status == 0:
        raise _sessao.PortalComLoginErro(f"{ROTULO}: não consegui falar com o portal pela janela", "janela")
    if status != 200 or not isinstance(dados, dict):
        if _sessao.captcha_na_aba(_eu(), a):
            a.frente()
            raise _sessao.PortalComLoginErro(CAPTCHA, "captcha")
        raise _sessao.PortalComLoginErro(MUDOU if status == 200 else f"o MyGreenhouse respondeu {status}", "mudou")
    return dados


def _lista(cargo: str, consulta: dict, horas: int) -> list[dict]:
    vagas = []
    for pagina in range(1, MAX_PAGINAS + 1):
        lidas, mais = ler_resposta(_pedir(endereco(cargo, consulta, horas, pagina)))
        vagas += lidas
        if not mais or not lidas:
            break
    return vagas


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def _atende(v: dict, consulta: dict, limite: str) -> bool:
    import filtros  # aqui: o filtros.py importa as fontes sob demanda

    if not _comum.bate_cargo(v["titulo"], consulta["termo"]):
        return False
    if v.get("publicada_em") and v["publicada_em"] < limite:
        return False
    if consulta.get("global"):
        return bool(v["remoto"]) or not consulta.get("remoto")
    return bool(v["remoto"]) and filtros.aberta_ao_pais(v.get("restricao_local") or v.get("local"),
                                                        consulta.get("pais_nome") or "")


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if not _sessao.dentro_da_pagina():  # terminal ou chat: o portal fica de fora, sem abrir a janela
        if _estado["avisou_fora"]:
            return [], []
        _estado["avisou_fora"] = True
        return [], [_sessao.aviso_fora(_eu())]
    cargo = str(consulta.get("termo") or "").strip()
    if not cargo:
        return [], []
    if not consulta.get("global") and (consulta.get("grupo") != "remoto"
                                       or str(consulta.get("pais") or "").lower() not in PAISES):
        return [], []  # cidade, país sem filtro de remoto ou país desconhecido: sem pedido
    e = espera()
    if e:  # durante a espera, nenhum pedido; o aviso sai uma vez por busca
        if _estado["avisou_espera"]:
            return [], []
        _estado["avisou_espera"] = True
        return [], [f"{PLATAFORMA} em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); a busca seguiu sem ele"]
    if _estado["fora"]:
        return [], []  # parou antes nesta busca (o aviso já saiu)
    try:
        with _sessao.janela():
            vagas = _lista(cargo, consulta, horas)
    except _sessao.PortalComLoginErro as erro:
        _estado["fora"] = erro.tipo
        return [], [str(erro)]
    limite = _limite(horas)
    achadas = [v for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], []


def descrever(vaga: dict) -> str:
    """A descrição pela API pública do quadro da empresa (fontes/ats.py), sem a sessão. Depois de um bloqueio ou na
    espera, ou se a API não responder, devolve o que a vaga já tinha."""
    if parada():
        return vaga.get("descricao") or ""
    url = vaga.get("url") or ""
    if not ats.vaga_do_link(url):  # link no site da empresa: o quadro pelo id da vaga
        m = ID.match(str(vaga.get("id") or ""))
        url = _canonico(m.group(1), m.group(2)) if m else ""
    if not url:
        return vaga.get("descricao") or ""
    try:
        return ats.ler(url).get("descricao") or vaga.get("descricao") or ""
    except _comum.FonteErro:
        return vaga.get("descricao") or ""
