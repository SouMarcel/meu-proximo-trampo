"""Fonte Himalayas (himalayas.app/jobs/api): vagas remotas, API pública sem login.

A API devolve as vagas mais recentes em páginas de 20, com cursor; a busca lê poucas páginas, uma vez por
busca, e filtra os cargos aqui. Cada vaga traz os países onde a pessoa precisa morar
(`locationRestrictions`), que viram a restrição de local. O dashboard cita a Himalayas e linka a vaga.
"""
from __future__ import annotations

from . import _comum

NOME = "himalayas"
PLATAFORMA = "Himalayas"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Cita a Himalayas e linka a vaga original; lê poucas páginas da lista recente por busca."
URL = "https://himalayas.app/jobs/api"
POR_PAGINA = 20  # máximo da API
PAGINAS = 3


def _lista() -> list:
    vagas, cursor = [], None
    for _ in range(PAGINAS):
        dados = _comum.baixar_json(URL, {"limit": POR_PAGINA, **({"cursor": cursor} if cursor else {})})
        if not isinstance(dados, dict) or not isinstance(dados.get("jobs"), list):
            raise _comum.FonteErro("resposta inesperada da Himalayas")
        vagas += dados["jobs"]
        cursor = dados.get("nextCursor")
        if not cursor or not dados["jobs"]:
            break
    return vagas


def normalizar(r: dict) -> dict | None:
    link = str(r.get("guid") or r.get("applicationLink") or "")
    slug = link.rstrip("/").rsplit("/", 1)[-1]
    if not slug:
        return None
    paises = [str(p).strip() for p in r.get("locationRestrictions") or [] if str(p).strip()]
    restricao = _comum.curto(", ".join(paises))
    return {
        "id": _comum.ident(NOME, slug),
        "plataforma": PLATAFORMA,
        "titulo": str(r.get("title") or "").strip(),
        "empresa": str(r.get("companyName") or "").strip() or "Empresa não informada",
        "local": f"Remoto ({restricao})" if restricao else "Remoto",
        "remoto": True,
        "publicada_em": _comum.data_iso(r.get("pubDate")),
        "url": str(r.get("applicationLink") or link),
        "url_candidatura": None,
        "salario": _comum.salario(r.get("minSalary"), r.get("maxSalary"), r.get("currency"), r.get("salaryPeriod")),
        "moeda": _comum.moeda(r.get("currency")),
        "tipo": _comum.curto(r.get("employmentType"), 40),
        "descricao": _comum.texto(r.get("description")),
        "restricao_local": restricao,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    return _comum.buscar_lista(NOME, _lista, normalizar, consulta, horas, por_termo)
