"""Fonte das empresas que a pessoa acompanha, pela página de vagas de cada uma (specs 031 e 042).

A pessoa cola no painel o link da página de vagas da empresa (ou acompanha a empresa a partir de uma vaga). Sistemas
reconhecidos: Greenhouse, Lever e Ashby (APIs públicas), Teamtailor (o feed público, fontes/teamtailor.py) e o site de
vagas da EY (fontes/ey.py); outra página é "página própria", lida pela IA (fontes/pagina_empresa.py). reconhecer()
não faz pedido (domínios conhecidos); descobrir() abre a página uma vez quando o domínio é desconhecido. Link de
portal de vagas é recusado: portal se liga em Portais. Cada empresa é consultada no máximo uma vez por busca, sem
login, e a mesma lista serve às duas áreas (spec 031):
- na busca nacional, as vagas remotas abertas a quem mora no país da pessoa (o local cita o país, uma região que o
  inclui ou o mundo todo) e, na consulta da cidade, as presenciais e híbridas na cidade ou no estado dela;
- na busca internacional, a consulta global com os cargos em inglês, como antes.
No primeiro 403 ou 429 de um sistema (Greenhouse, Lever, Ashby) ou de um site (Teamtailor e página própria, também
503), sem nova tentativa, as empresas dele ficam sem pedido até o fim da busca. A EY segue as regras dela. ler() traz
uma vaga pelo link (Adicionar Vaga).
"""
from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, urlsplit

from . import _comum, ey, pagina_empresa, teamtailor

NOME = "ats"
PLATAFORMA = "Empresas acompanhadas"
AREAS = ("nacional", "internacional")
POR_PAIS = True  # atende as consultas nacionais (remota, do país e da cidade)…
GLOBAL = True  # …e a consulta internacional global; as por país e as de mudança não fazem pedido
TERMOS = "Páginas e APIs públicas de vagas das próprias empresas; uma consulta por empresa por busca."
# sistema -> nome da plataforma nas vagas
SISTEMAS = {"greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby", "teamtailor": "Teamtailor", "ey": "EY",
            "pagina": "Site da empresa"}
ROTULOS = {**SISTEMAS, "ey": "Site de vagas da EY", "pagina": "Página própria (lida pela IA)"}
EXEMPLOS = "careers.ey.com, carreiras.empresa.com.br/jobs ou jobs.lever.co/empresa"
EY = {"sistema": "ey", "id": "ey", "nome": "EY", "url": "https://careers.ey.com/ey/"}
POR_HOST = ("teamtailor", "pagina")  # bloqueio por site (cada empresa num domínio)
BLOQUEIOS_HOST = (403, 429, 503)
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
MODELOS = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial", "on-site": "presencial"}
NACIONAIS = ("remoto", "pais", "local")  # grupos das consultas nacionais (filtros.consultas)
BLOQUEIOS = (403, 429)

_estado = {"bloqueados": set()}  # sistemas (e sites) que recusaram ou limitaram nesta busca


def _esquecer() -> None:
    _estado["bloqueados"] = set()


_comum.AO_ESQUECER.append(_esquecer)


def _partes(url: str) -> tuple[str, str, list[str], dict]:
    url = str(url or "").strip()
    if url and "://" not in url:
        url = "https://" + url
    p = urlsplit(url)
    return (p.hostname or "").lower(), p.scheme, [s for s in p.path.split("/") if s], parse_qs(p.query)


def _sistema(host: str) -> str | None:
    if host in ("boards.greenhouse.io", "job-boards.greenhouse.io", "job-boards.eu.greenhouse.io",
                "boards.eu.greenhouse.io"):
        return "greenhouse"
    if host in ("jobs.lever.co", "jobs.eu.lever.co"):
        return "lever"
    if host == "jobs.ashbyhq.com":
        return "ashby"
    if host.endswith(".teamtailor.com") and host.count(".") >= 2:
        return "teamtailor"
    if host == "careers.ey.com":
        return "ey"
    return None


class Desconhecido(ValueError):
    """Domínio que reconhecer() não conhece: descobrir() precisa abrir a página uma vez."""


def _portal(host: str) -> str | None:
    """O nome do portal de vagas do domínio (LinkedIn, Indeed, Gupy…), menos a EY, que é uma empresa."""
    import integridade  # na raiz; aqui para o módulo não depender dela ao ser importado

    achado = integridade.portal_do_host(host)
    return achado[1] if achado and achado[0] == "portal" and achado[1] != "EY" else None


def _id_pagina(host: str, segs: list[str]) -> str:
    return "/".join([host.removeprefix("www."), *segs])[:200]


def _nome_do_host(host: str) -> str:
    """Um nome para a empresa a partir do domínio ("carreiras.empresa.com.br" -> "Empresa")."""
    base = host.removeprefix("www.").split(".")
    parte = base[1] if base[0] in ("carreiras", "careers", "jobs", "vagas", "trabalhe") and len(base) > 2 else base[0]
    return " ".join(p.capitalize() for p in re.split(r"[-_]+", parte) if p) or host


def reconhecer(url: str) -> dict:
    """{sistema, id, nome, url} da empresa pelo link da página de vagas (ou de uma vaga dela), sem pedido. Levanta
    ValueError com a explicação (link inválido, portal de vagas) e Desconhecido quando o domínio não é conhecido."""
    host, esquema, segs, query = _partes(url)
    if esquema not in ("http", "https") or not host:
        raise ValueError(f"o link não é de uma página da internet (ex.: {EXEMPLOS})")
    sistema = _sistema(host)
    if sistema == "ey":
        return dict(EY)
    if sistema == "teamtailor":
        return {"sistema": "teamtailor", "id": host, "nome": _nome_do_host(host), "url": f"https://{host}/jobs"}
    if not sistema:
        portal = _portal(host)
        if portal:
            raise ValueError(f"{portal} é um portal de vagas, não a página de uma empresa: ligue-o em Filtros da busca "
                             "→ Portais")
        raise Desconhecido("não reconheci o sistema dessa página: adicione pelo botão Adicionar do painel, que abre a "
                           "página uma vez para descobrir")
    # embed/job_board?for=… e embed/job_app?for=… (formulário embutido no site da empresa) trazem a empresa no for
    slug = (query.get("for") or [""])[0] if segs[:1] == ["embed"] else (segs[0] if segs else "")
    if not SLUG.fullmatch(slug or ""):
        raise ValueError(f"o link não traz o nome da empresa no {SISTEMAS[sistema]} (ex.: {EXEMPLOS})")
    base = {"greenhouse": "https://job-boards.greenhouse.io", "ashby": "https://jobs.ashbyhq.com",
            "lever": f"https://{host}"}[sistema]
    nome = " ".join(p.capitalize() for p in re.split(r"[-_.]+", slug) if p)
    return {"sistema": sistema, "id": slug, "nome": nome or slug, "url": f"{base}/{slug}"}


def descobrir(url: str) -> dict:
    """reconhecer(); com domínio desconhecido, um pedido à página: o feed do Teamtailor anunciado faz dela Teamtailor,
    senão é página própria (lida pela IA). O nome vem de og:site_name ou do título. ValueError com o motivo."""
    try:
        return reconhecer(url)
    except Desconhecido:
        pass
    url = str(url or "").strip()
    url = url if "://" in url else "https://" + url
    host, _, segs, _ = _partes(url)
    try:
        pagina = _comum.baixar(url.split("#", 1)[0], aceitar="text/html,application/xhtml+xml",
                               nova_tentativa=False).decode("utf-8", errors="replace")
    except _comum.FonteErro as e:
        if e.codigo == 404:
            raise ValueError("a página não existe (404): confira o link") from None
        raise ValueError(f"não consegui abrir a página ({e})") from None
    nome = ""
    m = re.search(r"""<meta[^>]+property=["']og:site_name["'][^>]+content=["']([^"']{1,120})""", pagina, re.I)
    if m:
        nome = m.group(1)
    else:
        m = re.search(r"<title[^>]*>([^<]{1,200})</title>", pagina, re.I)
        if m:  # "Vagas - Empresa" ou "Carreira | Empresa": a parte mais curta costuma ser o nome
            partes = [p.strip() for p in re.split(r"\s[-|–—]\s", m.group(1)) if p.strip()]
            nome = min(partes, key=len) if partes else ""
    nome = teamtailor.nome_bonito(" ".join(html.unescape(nome).split())[:80]) or _nome_do_host(host)
    rss = re.search(r"""<link[^>]+application/rss\+xml[^>]*href=["'](https://[^"']+/jobs\.rss)["']""", pagina, re.I)
    if rss and "teamtailor" in pagina.lower():
        alvo = (urlsplit(rss.group(1)).hostname or host).lower()
        return {"sistema": "teamtailor", "id": alvo, "nome": nome, "url": f"https://{alvo}/jobs"}
    return {"sistema": "pagina", "id": _id_pagina(host, segs), "nome": nome, "url": url}


def conferir(e: dict) -> dict:
    """A empresa já reconhecida (do painel), conferida sem pedido: sistema conhecido e link coerente."""
    sistema, url = str(e.get("sistema") or ""), str(e.get("url") or "").strip()
    url = url if "://" in url or not url else "https://" + url
    host, esquema, segs, _ = _partes(url)
    if esquema not in ("http", "https") or not host:
        raise ValueError("o link da empresa não é de uma página da internet")
    if sistema in ("greenhouse", "lever", "ashby", "ey"):
        r = reconhecer(url)
        if r["sistema"] != sistema:
            raise ValueError("o link não é do sistema informado")
    elif sistema == "teamtailor":
        r = {"sistema": sistema, "id": host, "nome": "", "url": f"https://{host}/jobs"}
    elif sistema == "pagina":
        portal = _portal(host)
        if portal:
            raise ValueError(f"{portal} é um portal de vagas, não a página de uma empresa")
        r = {"sistema": sistema, "id": _id_pagina(host, segs), "nome": "", "url": url}
    else:
        raise ValueError(f"sistema desconhecido: {sistema}")
    r["nome"] = str(e.get("nome") or "").strip()[:80] or r.get("nome") or r["id"]
    return r


def vaga_do_link(url: str) -> tuple[dict, str] | None:
    """(empresa, id da vaga) num link de vaga do Greenhouse, Lever, Ashby, Teamtailor (*.teamtailor.com) ou EY; None
    se não for."""
    host, _, segs, query = _partes(url)
    sistema = _sistema(host)
    if not sistema:
        return None
    try:
        empresa = reconhecer(url)
    except ValueError:
        return None
    if sistema == "ey":
        n = ey.numero(url)
        return (empresa, n) if n else None
    if sistema == "teamtailor":
        m = re.fullmatch(r"(\d+)(?:-.*)?", segs[1]) if len(segs) >= 2 and segs[0] == "jobs" else None
        return (empresa, m.group(1)) if m else None
    if sistema == "greenhouse":
        vid = segs[2] if len(segs) >= 3 and segs[1] == "jobs" else (query.get("gh_jid") or [""])[0]
        vid = vid if vid.isdigit() else ""
    else:
        vid = segs[1] if len(segs) >= 2 and re.fullmatch(r"[0-9a-fA-F-]{8,}", segs[1]) else ""
    return (empresa, vid) if vid else None


# ---------------------------------------------------------------- APIs

def _api_lever(e: dict) -> str:
    return "https://api.eu.lever.co" if ".eu." in str(e.get("url") or "") else "https://api.lever.co"


def _lista(e: dict) -> list:
    sistema, slug = e["sistema"], e["id"]
    if sistema == "teamtailor":
        return teamtailor.lista(e)
    if sistema == "pagina":
        return pagina_empresa.lista(e)
    if not SLUG.fullmatch(slug):
        raise _comum.FonteErro("identificador de empresa inválido")
    if sistema == "greenhouse":
        dados = _comum.baixar_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", {"content": "true"},
                                   nova_tentativa=False)
        itens = dados.get("jobs") if isinstance(dados, dict) else None
    elif sistema == "lever":
        itens = _comum.baixar_json(f"{_api_lever(e)}/v0/postings/{slug}", {"mode": "json"}, nova_tentativa=False)
    elif sistema == "ashby":
        dados = _comum.baixar_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                                   {"includeCompensation": "true"}, nova_tentativa=False)
        itens = dados.get("jobs") if isinstance(dados, dict) else None
    else:
        raise _comum.FonteErro(f"sistema desconhecido: {sistema}")
    if not isinstance(itens, list):
        raise _comum.FonteErro(f"resposta inesperada do {SISTEMAS[sistema]}")
    return itens


def _remoto_restricao(remoto: bool, *lugares) -> str | None:
    """Na vaga remota, o lugar informado é onde a pessoa precisa estar; na presencial, é só o local."""
    return _comum.curto(", ".join(x for x in lugares if x)) if remoto else None


def normalizar(r: dict, e: dict) -> dict | None:
    sistema, slug = e["sistema"], e["id"]
    if not r.get("id"):
        return None
    base = {"id": _comum.ident(sistema, f"{slug}-{r['id']}"), "plataforma": SISTEMAS[sistema], "ats": sistema,
            "empresa": e.get("nome") or slug}
    if sistema == "greenhouse":
        import filtros  # aqui: o filtros.py importa este módulo sob demanda

        local = str((r.get("location") or {}).get("name") or "").strip()
        # "Remote, Brazil", ou só regiões e o mundo todo ("Latin America", "Anywhere")
        remoto = "remote" in local.lower() or filtros.so_regioes(local)
        return {**base, "titulo": str(r.get("title") or "").strip(),
                "empresa": str(r.get("company_name") or "").strip() or base["empresa"],
                "local": local, "remoto": remoto,
                "publicada_em": _comum.data_iso(r.get("first_published") or r.get("updated_at")),
                "url": str(r.get("absolute_url") or ""), "url_candidatura": None, "salario": None, "tipo": None,
                "descricao": _comum.texto(r.get("content")), "restricao_local": _remoto_restricao(remoto, local),
                "idioma": str(r.get("language") or "")[:2].lower() or None}
    if sistema == "lever":
        cat = r.get("categories") if isinstance(r.get("categories"), dict) else {}
        locais = [str(x) for x in cat.get("allLocations") or [] if x] or [str(cat.get("location") or "")]
        local = "; ".join(x for x in locais if x)
        remoto = str(r.get("workplaceType") or "").lower() == "remote"
        partes = [r.get("descriptionPlain") or ""]
        for lista in r.get("lists") or []:
            partes.append(f"{lista.get('text') or ''}\n{_comum.texto(lista.get('content'))}")
        partes.append(r.get("additionalPlain") or "")
        faixa = r.get("salaryRange") if isinstance(r.get("salaryRange"), dict) else {}
        return {**base, "titulo": str(r.get("text") or "").strip(), "local": local, "remoto": remoto,
                "modelo_trabalho": MODELOS.get(str(r.get("workplaceType") or "").lower()),
                "publicada_em": _comum.data_iso(r.get("createdAt")),
                "url": str(r.get("hostedUrl") or ""), "url_candidatura": r.get("applyUrl") or None,
                "salario": _comum.salario(faixa.get("min"), faixa.get("max"), faixa.get("currency"), faixa.get("interval")),
                "moeda": _comum.moeda(faixa.get("currency")), "tipo": _comum.curto(cat.get("commitment"), 40),
                "descricao": _comum.texto("\n\n".join(p.strip() for p in partes if p and p.strip())),
                "restricao_local": _remoto_restricao(remoto, local, r.get("country"))}
    if sistema == "ashby":
        def lugar(x):
            end = ((x or {}).get("address") or {}).get("postalAddress") or {}
            return ", ".join(str(v) for v in (x.get("location"), end.get("addressCountry")) if v)
        locais = [lugar(r)] + [lugar(x) for x in r.get("secondaryLocations") or [] if isinstance(x, dict)]
        local = "; ".join(x for x in locais if x)
        remoto = bool(r.get("isRemote")) or str(r.get("workplaceType") or "").lower() == "remote"
        comp = r.get("compensation") if isinstance(r.get("compensation"), dict) else {}
        sal = next((c for c in comp.get("summaryComponents") or []
                    if isinstance(c, dict) and c.get("compensationType") == "Salary"), {})
        return {**base, "titulo": str(r.get("title") or "").strip(), "local": local, "remoto": remoto,
                "modelo_trabalho": "remoto" if remoto else MODELOS.get(str(r.get("workplaceType") or "").lower()),
                "publicada_em": _comum.data_iso(r.get("publishedAt")),
                "url": str(r.get("jobUrl") or ""), "url_candidatura": r.get("applyUrl") or None,
                "salario": _comum.salario(sal.get("minValue"), sal.get("maxValue"), sal.get("currencyCode"),
                                          sal.get("interval")),
                "moeda": _comum.moeda(sal.get("currencyCode")) if sal.get("minValue") or sal.get("maxValue") else None,
                "tipo": _comum.curto(r.get("employmentType"), 40),
                "descricao": _comum.texto(r.get("descriptionPlain") or r.get("descriptionHtml")),
                "restricao_local": _remoto_restricao(remoto, local)}
    return None


def _na_cidade(local, consulta: dict) -> bool:
    """O local cita a cidade da pessoa ou o nome do estado dela, e nenhum outro país."""
    import filtros  # aqui: o filtros.py importa este módulo sob demanda

    t = f" {_comum._norm(local)} "
    cidade = _comum._norm(consulta.get("cidade"))
    estado = _comum.UFS.get(str(consulta.get("estado") or "").strip().upper(), "")
    if not any(nome and f" {nome} " in t for nome in (cidade, estado)):
        return False
    return filtros.pais_do_local(local) in (None, consulta.get("pais_nome"))


def _na_area(v: dict, consulta: dict) -> bool:
    """Na consulta global, como antes (só remotas, a não ser que a pessoa aceite morar fora). Nas nacionais (spec 031):
    remota aberta ao país; na do país, também as não remotas no país; na da cidade, as não remotas na cidade."""
    import filtros

    if consulta.get("global"):
        return bool(v.get("remoto")) or not consulta.get("remoto")
    pais, grupo = consulta.get("pais_nome") or "", consulta.get("grupo")
    if v.get("plataforma") == SISTEMAS["pagina"]:
        # página própria (spec 042): a remota sem outro país ("Home Office") é da empresa que a pessoa escolheu
        aberta = bool(v.get("remoto")) and filtros.pais_do_local(v.get("local")) in (None, pais)
    else:
        aberta = bool(v.get("remoto")) and filtros.aberta_ao_pais(v.get("restricao_local") or v.get("local"), pais)
    if grupo == "remoto":
        return aberta
    if grupo == "pais":
        return aberta or (not v.get("remoto") and filtros.pais_do_local(v.get("local")) == pais)
    return not v.get("remoto") and _na_cidade(v.get("local"), consulta)


def _chave(e: dict) -> str:
    """O que um bloqueio para: o sistema (Greenhouse, Lever, Ashby) ou o site (Teamtailor e página própria)."""
    if e.get("sistema") in POR_HOST:
        return "site:" + (_partes(str(e.get("url") or ""))[0] or str(e.get("id")))
    return str(e.get("sistema"))


def _aviso(erro: _comum.FonteErro, e: dict) -> str | None:
    """O aviso do erro de uma empresa; 403 e 429 (e 503, num site) param o sistema ou o site dela até o fim da busca."""
    sistema = SISTEMAS.get(e.get("sistema"), e.get("sistema"))
    nome = e.get("nome") or e.get("id")
    por_host = e.get("sistema") in POR_HOST
    if erro.codigo in (BLOQUEIOS_HOST if por_host else BLOQUEIOS):
        _estado["bloqueados"].add(_chave(e))
        if por_host:
            return (f"o site de vagas de {nome} limitou as consultas (código {erro.codigo}); fica para a próxima "
                    "busca")
        return (f"o {sistema} limitou as consultas (código {erro.codigo}); as outras empresas dele ficam para a "
                "próxima busca")
    if erro.repetido:
        return None  # o mesmo erro já saiu nesta busca
    if por_host:
        if erro.codigo == 404:
            return f"a página de vagas de {nome} não existe mais; remova ou troque o link"
        return f"{nome}: {erro}" if erro.codigo != 0 else str(erro)  # 0: aviso sem erro (ex.: nenhuma vaga na página)
    if erro.codigo == 404:
        return (f"a página de vagas de {nome} no {sistema} não existe mais (a empresa pode ter mudado de sistema ou de "
                "nome); remova ou troque o link")
    return f"{nome} ({sistema}): {erro}"


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if not consulta.get("global") and consulta.get("grupo") not in NACIONAIS:
        return [], []  # por país e mudança: as empresas rodam nas consultas nacionais e na global
    vagas, erros = [], []
    for e in consulta.get("empresas") or []:
        if e.get("sistema") == "ey":  # a busca do site da EY, com as regras dela (spec 039), só na área nacional
            achadas, errs = ey.buscar(consulta, horas, por_termo)
            vagas += achadas
            erros += errs
            continue
        if _chave(e) in _estado["bloqueados"]:
            continue  # o sistema ou o site recusou ou limitou nesta busca: nenhum pedido a mais
        try:  # a mesma lista para todos os cargos e as duas áreas
            itens = _comum.lembrar(f"{NOME}:{e.get('sistema')}:{e.get('id')}", lambda e=e: _lista(e))
        except _comum.FonteErro as erro:
            aviso = _aviso(erro, e)
            if aviso:
                erros.append(aviso)
            continue
        if e.get("sistema") in POR_HOST:
            normal = dict  # Teamtailor e página própria já vêm no formato comum
        else:
            normal = lambda r, e=e: normalizar(r, e)  # noqa: E731
        achadas = _comum.filtrar(itens, {**consulta, "remoto": False}, horas, len(itens) + 1,
                                 normal)  # cargo e janela; a área vem abaixo
        vagas += [v for v in achadas if _na_area(v, consulta)][:max(1, por_termo)]
    return vagas, erros


def ler(url: str) -> dict:
    """Uma vaga pelo link (Greenhouse, Lever ou Ashby), no formato comum. Levanta FonteErro se não conseguir."""
    achado = vaga_do_link(url)
    if not achado:
        raise _comum.FonteErro("link de vaga do Greenhouse, Lever ou Ashby não reconhecido")
    e, vid = achado
    if e["sistema"] == "greenhouse":
        r = _comum.baixar_json(f"https://boards-api.greenhouse.io/v1/boards/{e['id']}/jobs/{vid}",
                               nova_tentativa=False)
    elif e["sistema"] == "lever":
        r = _comum.baixar_json(f"{_api_lever(e)}/v0/postings/{e['id']}/{vid}", {"mode": "json"}, nova_tentativa=False)
    else:
        r = next((x for x in _lista(e) if str(x.get("id")) == vid), None)
    vaga = normalizar(r, e) if isinstance(r, dict) else None
    if not vaga or not vaga["titulo"]:
        raise _comum.FonteErro("o sistema não devolveu essa vaga (ela pode ter saído do ar)")
    return vaga
