"""Fonte das empresas que a pessoa acompanha, pelas páginas de vagas no Greenhouse, no Lever e no Ashby.

A pessoa cola no painel o link da página de vagas da empresa (ou acompanha a empresa a partir de uma vaga);
reconhecer() descobre o sistema e o identificador da empresa. Cada empresa é consultada no máximo uma vez por busca
pela API pública do sistema (sem login), e a mesma lista serve às duas áreas (spec 031):
- na busca nacional, as vagas remotas abertas a quem mora no país da pessoa (o local cita o país, uma região que o
  inclui ou o mundo todo) e, na consulta da cidade, as presenciais e híbridas na cidade ou no estado dela;
- na busca internacional, a consulta global com os cargos em inglês, como antes.
No primeiro 403 ou 429 de um sistema, sem nova tentativa, as empresas dele ficam sem pedido até o fim da busca. ler()
traz uma vaga pelo link (Adicionar Vaga).
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from . import _comum

NOME = "ats"
PLATAFORMA = "Empresas acompanhadas"
AREAS = ("nacional", "internacional")
POR_PAIS = True  # atende as consultas nacionais (remota, do país e da cidade)…
GLOBAL = True  # …e a consulta internacional global; as por país e as de mudança não fazem pedido
TERMOS = "APIs públicas de vagas das próprias empresas; uma consulta por empresa por busca."
SISTEMAS = {"greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby"}
EXEMPLOS = "job-boards.greenhouse.io/empresa, jobs.lever.co/empresa ou jobs.ashbyhq.com/empresa"
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
MODELOS = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial", "on-site": "presencial"}
NACIONAIS = ("remoto", "pais", "local")  # grupos das consultas nacionais (filtros.consultas)
BLOQUEIOS = (403, 429)

_estado = {"bloqueados": set()}  # sistemas que recusaram ou limitaram nesta busca


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
    return None


def reconhecer(url: str) -> dict:
    """{sistema, id, nome, url} da empresa pelo link da página de vagas (ou de uma vaga dela). Levanta
    ValueError explicando quando o link não é do Greenhouse, do Lever nem do Ashby."""
    host, esquema, segs, query = _partes(url)
    sistema = _sistema(host)
    if not sistema or esquema not in ("http", "https"):
        raise ValueError(f"não é uma página de vagas do Greenhouse, do Lever nem do Ashby (ex.: {EXEMPLOS})")
    # embed/job_board?for=… e embed/job_app?for=… (formulário embutido no site da empresa) trazem a empresa no for
    slug = (query.get("for") or [""])[0] if segs[:1] == ["embed"] else (segs[0] if segs else "")
    if not SLUG.fullmatch(slug or ""):
        raise ValueError(f"o link não traz o nome da empresa no {SISTEMAS[sistema]} (ex.: {EXEMPLOS})")
    base = {"greenhouse": "https://job-boards.greenhouse.io", "ashby": "https://jobs.ashbyhq.com",
            "lever": f"https://{host}"}[sistema]
    nome = " ".join(p.capitalize() for p in re.split(r"[-_.]+", slug) if p)
    return {"sistema": sistema, "id": slug, "nome": nome or slug, "url": f"{base}/{slug}"}


def vaga_do_link(url: str) -> tuple[dict, str] | None:
    """(empresa, id da vaga) num link de vaga do Greenhouse, Lever ou Ashby; None se não for."""
    host, _, segs, query = _partes(url)
    sistema = _sistema(host)
    if not sistema:
        return None
    try:
        empresa = reconhecer(url)
    except ValueError:
        return None
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
    aberta = bool(v.get("remoto")) and filtros.aberta_ao_pais(v.get("restricao_local") or v.get("local"), pais)
    if grupo == "remoto":
        return aberta
    if grupo == "pais":
        return aberta or (not v.get("remoto") and filtros.pais_do_local(v.get("local")) == pais)
    return not v.get("remoto") and _na_cidade(v.get("local"), consulta)


def _aviso(erro: _comum.FonteErro, e: dict) -> str | None:
    """O aviso do erro de uma empresa; 403 e 429 param o sistema dela até o fim da busca."""
    sistema = SISTEMAS.get(e.get("sistema"), e.get("sistema"))
    if erro.codigo in BLOQUEIOS:
        _estado["bloqueados"].add(e.get("sistema"))
        return (f"o {sistema} limitou as consultas (código {erro.codigo}); as outras empresas dele ficam para a "
                "próxima busca")
    if erro.repetido:
        return None  # o mesmo erro já saiu nesta busca
    nome = e.get("nome") or e.get("id")
    if erro.codigo == 404:
        return (f"a página de vagas de {nome} no {sistema} não existe mais (a empresa pode ter mudado de sistema ou de "
                "nome); remova ou troque o link")
    return f"{nome} ({sistema}): {erro}"


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if not consulta.get("global") and consulta.get("grupo") not in NACIONAIS:
        return [], []  # por país e mudança: as empresas rodam nas consultas nacionais e na global
    vagas, erros = [], []
    for e in consulta.get("empresas") or []:
        if e.get("sistema") in _estado["bloqueados"]:
            continue  # o sistema recusou ou limitou nesta busca: nenhum pedido a mais
        try:  # a mesma lista para todos os cargos e as duas áreas
            itens = _comum.lembrar(f"{NOME}:{e.get('sistema')}:{e.get('id')}", lambda e=e: _lista(e))
        except _comum.FonteErro as erro:
            aviso = _aviso(erro, e)
            if aviso:
                erros.append(aviso)
            continue
        achadas = _comum.filtrar(itens, {**consulta, "remoto": False}, horas, len(itens) + 1,
                                 lambda r, e=e: normalizar(r, e))  # cargo e janela; a área vem abaixo
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
