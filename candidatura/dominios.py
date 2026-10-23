"""Onde a candidatura assistida pode preencher (spec 027, research.md §1).

  CONHECIDOS        portal → domínios de candidatura e hosts de login (só portais sem termos contrários)
  BLOQUEADOS        domínio → motivo; nunca preenche, nem com liberação da pessoa
  host_de(url)      o host da URL, em minúsculas, só para https
  situacao(url)     {"host", "permitido", "portal", "origem": conhecido|liberado|None, "bloqueado": motivo|None,
                     "pode_liberar"}
  liberar(host)     a pessoa libera um host fora da lista (gravado no config.json)
  revogar(host)     tira o host da lista dela

A comparação é pelo host exato ou por subdomínio ("x.gupy.io" casa com "gupy.io"; "gupy.io.exemplo.com" não).
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlsplit

from . import CandidaturaErro, _gravar_estado, estado

CONHECIDOS = {
    "gupy": {"rotulo": "Gupy", "dominios": ("gupy.io",), "login": ("login.gupy.io",), "credencial": "GUPY"},
    "greenhouse": {"rotulo": "Greenhouse", "dominios": ("greenhouse.io",), "login": ("my.greenhouse.io",),
                   "credencial": "GREENHOUSE"},
    "lever": {"rotulo": "Lever", "dominios": ("jobs.lever.co",), "login": (), "credencial": None},
    "workday": {"rotulo": "Workday", "dominios": ("myworkdayjobs.com",), "login": (), "credencial": None},
}
BLOQUEADOS = {
    "linkedin.com": "o LinkedIn fica fora da ferramenta (restringe contas que considera automatizadas)",
    "lnkd.in": "o LinkedIn fica fora da ferramenta (restringe contas que considera automatizadas)",
    "indeed.com": "os termos do Indeed proíbem automação na candidatura",
    "indeed.com.br": "os termos do Indeed proíbem automação na candidatura",
    "nerdin.com.br": "os termos do Nerdin proíbem robôs e automações",
}
HOST_VALIDO = re.compile(r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
MAX_LIBERADOS = 200


def casa(host: str, dominio: str) -> bool:
    host, dominio = (host or "").lower().rstrip("."), (dominio or "").lower()
    return bool(host) and (host == dominio or host.endswith("." + dominio))


def host_de(url: str) -> str:
    p = urlsplit(str(url or ""))
    if p.scheme != "https" or not p.hostname:
        return ""
    return p.hostname.lower().rstrip(".")


def bloqueio(host: str) -> str | None:
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    for dominio, motivo in BLOQUEADOS.items():
        if casa(host, dominio):
            return motivo
    if re.search(r"(^|\.)indeed\.[a-z.]+$", host) or re.search(r"(^|\.)linkedin\.[a-z.]+$", host):
        return BLOQUEADOS["indeed.com"] if "indeed" in host else BLOQUEADOS["linkedin.com"]
    return None


def portal_conhecido(host: str) -> str | None:
    for nome, p in CONHECIDOS.items():
        if any(casa(host, d) for d in p["dominios"]):
            return nome
    return None


def situacao(url: str) -> dict:
    host = host_de(url)
    base = {"host": host, "permitido": False, "portal": None, "origem": None, "bloqueado": None, "pode_liberar": False}
    if not host:
        return {**base, "bloqueado": "a página não é um endereço seguro (https) de um site"}
    motivo = bloqueio(host)
    if motivo:
        return {**base, "bloqueado": motivo}
    portal = portal_conhecido(host)
    if portal:
        return {**base, "permitido": True, "portal": portal, "origem": "conhecido"}
    if any(casa(host, d["dominio"]) for d in estado()["dominios"]):
        return {**base, "permitido": True, "origem": "liberado"}
    return {**base, "pode_liberar": True}


def _validar_host(host: str) -> str:
    host = str(host or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not HOST_VALIDO.match(host):
        raise CandidaturaErro("endereço inválido: use só o nome do site, como carreiras.empresa.com.br")
    return host


def liberar(host: str) -> dict:
    host = _validar_host(host)
    motivo = bloqueio(host)
    if motivo:
        raise CandidaturaErro(f"não dá para liberar {host}: {motivo}")
    atual = estado()
    if portal_conhecido(host) or any(d["dominio"] == host for d in atual["dominios"]):
        return atual
    if len(atual["dominios"]) >= MAX_LIBERADOS:
        raise CandidaturaErro("lista de endereços liberados cheia; revogue algum antes")
    atual["dominios"] = atual["dominios"] + [{"dominio": host, "em": date.today().isoformat()}]
    return _gravar_estado(atual)


def revogar(host: str) -> dict:
    host = _validar_host(host)
    atual = estado()
    atual["dominios"] = [d for d in atual["dominios"] if d["dominio"] != host]
    return _gravar_estado(atual)


def para_pagina() -> dict:
    return {"conhecidos": [{"portal": n, "rotulo": p["rotulo"], "dominios": list(p["dominios"]),
                            "tem_login": bool(p["login"] and p["credencial"])} for n, p in CONHECIDOS.items()],
            "bloqueados": [{"dominio": d, "motivo": m} for d, m in BLOQUEADOS.items() if d != "lnkd.in"],
            "liberados": estado()["dominios"]}
