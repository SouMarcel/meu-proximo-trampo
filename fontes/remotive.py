"""Fonte Remotive (remotive.com/api/remote-jobs): vagas remotas do mundo todo, API pública sem login.

A Remotive pede no máximo 4 consultas por dia e mostra as vagas com 24 horas de atraso: a lista recente
é baixada uma vez e guardada em disco por 6 horas (.cache/fontes, fora do Git), e cada cargo filtra essa
lista aqui. Termos da API: citar a Remotive e linkar a vaga original (o dashboard mostra a plataforma e o
link da vaga).
"""
from __future__ import annotations

from . import _comum

NOME = "remotive"
PLATAFORMA = "Remotive"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Cita a Remotive e linka a vaga original; no máximo 4 consultas por dia (a lista fica guardada 6 h)."
URL = "https://remotive.com/api/remote-jobs"
LIMITE = 300  # vagas mais recentes
HORAS_DISCO = 6
TIPOS = {"full_time": "Tempo integral", "part_time": "Meio período", "contract": "Contrato",
         "freelance": "Freelance", "internship": "Estágio"}


def _lista() -> list:
    dados = _comum.baixar_json(URL, {"limit": LIMITE})
    if not isinstance(dados, dict) or not isinstance(dados.get("jobs"), list):
        raise _comum.FonteErro("resposta inesperada da Remotive")
    return dados["jobs"]


def normalizar(r: dict) -> dict | None:
    if not r.get("id"):
        return None
    local = _comum.curto(r.get("candidate_required_location"))
    return {
        "id": _comum.ident(NOME, r["id"]),
        "plataforma": PLATAFORMA,
        "titulo": str(r.get("title") or "").strip(),
        "empresa": str(r.get("company_name") or "").strip() or "Empresa não informada",
        "local": f"Remoto ({local})" if local else "Remoto",
        "remoto": True,
        "publicada_em": _comum.data_iso(r.get("publication_date")),
        "url": r.get("url") or "",
        "url_candidatura": None,  # a candidatura sai da página da vaga na Remotive
        "salario": _comum.curto(r.get("salary"), 80),
        "tipo": TIPOS.get(r.get("job_type") or ""),
        "descricao": _comum.texto(r.get("description")),
        "restricao_local": local,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    return _comum.buscar_lista(NOME, _lista, normalizar, consulta, horas, por_termo, HORAS_DISCO)
