"""Fonte das empresas que a pessoa acompanha, pelas páginas de vagas no Greenhouse, no Lever e no Ashby.

A pessoa cola no painel o link da página de vagas da empresa; reconhecer() descobre o sistema e o
identificador da empresa. Na busca internacional, cada empresa é consultada uma vez pela API pública do
sistema (sem login) e as vagas são filtradas aqui pelos cargos em inglês. ler() traz uma vaga pelo link
(Adicionar Vaga).
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from . import _comum

NOME = "ats"
PLATAFORMA = "Empresas acompanhadas"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "APIs públicas de vagas das próprias empresas; uma consulta por empresa por busca."
SISTEMAS = {"greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby"}
EXEMPLOS = "job-boards.greenhouse.io/empresa, jobs.lever.co/empresa ou jobs.ashbyhq.com/empresa"
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
MODELOS = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial", "on-site": "presencial"}


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
    slug = (query.get("for") or [""])[0] if segs[:2] == ["embed", "job_board"] else (segs[0] if segs else "")
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
        dados = _comum.baixar_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", {"content": "true"})
        itens = dados.get("jobs") if isinstance(dados, dict) else None
    elif sistema == "lever":
        itens = _comum.baixar_json(f"{_api_lever(e)}/v0/postings/{slug}", {"mode": "json"})
    elif sistema == "ashby":
        dados = _comum.baixar_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                                   {"includeCompensation": "true"})
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
        local = str((r.get("location") or {}).get("name") or "").strip()
        remoto = "remote" in local.lower()
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


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    vagas, erros = [], []
    for e in consulta.get("empresas") or []:
        rotulo = f"{e.get('nome') or e.get('id')} ({SISTEMAS.get(e.get('sistema'), e.get('sistema'))})"
        achadas, errs = _comum.buscar_lista(f"{NOME}:{e.get('sistema')}:{e.get('id')}", lambda e=e: _lista(e),
                                            lambda r, e=e: normalizar(r, e), consulta, horas, por_termo)
        vagas += achadas
        erros += [f"{rotulo}: {m}" for m in errs]
    return vagas, erros


def ler(url: str) -> dict:
    """Uma vaga pelo link (Greenhouse, Lever ou Ashby), no formato comum. Levanta FonteErro se não conseguir."""
    achado = vaga_do_link(url)
    if not achado:
        raise _comum.FonteErro("link de vaga do Greenhouse, Lever ou Ashby não reconhecido")
    e, vid = achado
    if e["sistema"] == "greenhouse":
        r = _comum.baixar_json(f"https://boards-api.greenhouse.io/v1/boards/{e['id']}/jobs/{vid}")
    elif e["sistema"] == "lever":
        r = _comum.baixar_json(f"{_api_lever(e)}/v0/postings/{e['id']}/{vid}", {"mode": "json"})
    else:
        r = next((x for x in _lista(e) if str(x.get("id")) == vid), None)
    vaga = normalizar(r, e) if isinstance(r, dict) else None
    if not vaga or not vaga["titulo"]:
        raise _comum.FonteErro("o sistema não devolveu essa vaga (ela pode ter saído do ar)")
    return vaga
