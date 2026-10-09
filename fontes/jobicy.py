"""Fonte Jobicy (jobicy.com/api/v2/remote-jobs): vagas remotas, API pública sem login.

Busca por cargo (parâmetro `tag`), uma consulta por cargo, e confere o título aqui. `jobGeo` diz onde a
pessoa precisa estar e vira a restrição de local. Termos da API: creditar o Jobicy com link para a vaga e
mandar a candidatura sempre para o link original da vaga.
"""
from __future__ import annotations

from . import _comum

NOME = "jobicy"
PLATAFORMA = "Jobicy"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Credita o Jobicy com link para a vaga; a candidatura sai sempre do link original."
URL = "https://jobicy.com/api/v2/remote-jobs"
QUANTAS = 50  # máximo da API


def normalizar(r: dict) -> dict | None:
    if not r.get("id"):
        return None
    geo = _comum.curto(", ".join(x.strip() for x in str(r.get("jobGeo") or "").split(",") if x.strip()))
    tipo = r.get("jobType")
    return {
        "id": _comum.ident(NOME, r["id"]),
        "plataforma": PLATAFORMA,
        "titulo": str(r.get("jobTitle") or "").strip(),
        "empresa": str(r.get("companyName") or "").strip() or "Empresa não informada",
        "local": f"Remoto ({geo})" if geo else "Remoto",
        "remoto": True,
        "publicada_em": _comum.data_iso(r.get("pubDate")),
        "url": str(r.get("url") or ""),
        "url_candidatura": None,
        "salario": _comum.salario(r.get("salaryMin") or r.get("annualSalaryMin"),
                                  r.get("salaryMax") or r.get("annualSalaryMax"),
                                  r.get("salaryCurrency"), r.get("salaryPeriod") or "year"),
        "moeda": _comum.moeda(r.get("salaryCurrency")),
        "tipo": ", ".join(map(str, tipo)) if isinstance(tipo, list) and tipo else None,
        "descricao": _comum.texto(r.get("jobDescription")),
        "restricao_local": geo,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    termo = " ".join(consulta["termo"].replace('"', " ").split())

    def lista():
        dados = _comum.baixar_json(URL, {"count": QUANTAS, "tag": termo})
        if not isinstance(dados, dict):
            raise _comum.FonteErro("resposta inesperada do Jobicy")
        return dados.get("jobs") or []

    return _comum.buscar_lista(f"{NOME}:{termo.lower()}", lista, normalizar, consulta, horas, por_termo)
