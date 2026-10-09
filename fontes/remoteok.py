"""Fonte Remote OK (remoteok.com/api): vagas remotas, API pública sem login.

A API devolve uma lista das vagas recentes; o primeiro item é o aviso legal, não uma vaga. Termos da API:
citar o Remote OK e linkar a vaga original (o dashboard mostra a plataforma e o link), sem usar o logotipo.
A lista é baixada uma vez por busca e os cargos são filtrados aqui.
"""
from __future__ import annotations

from . import _comum

NOME = "remoteok"
PLATAFORMA = "RemoteOK"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Cita o Remote OK e linka a vaga original (sem o logotipo); uma consulta por busca."
URL = "https://remoteok.com/api"


def _lista() -> list:
    dados = _comum.baixar_json(URL)
    if not isinstance(dados, list):
        raise _comum.FonteErro("resposta inesperada do Remote OK")
    return [x for x in dados if isinstance(x, dict) and x.get("id")]  # pula o aviso legal


def normalizar(r: dict) -> dict | None:
    if not r.get("id"):
        return None
    local = _comum.curto(_comum.consertar(r.get("location")))
    tem_salario = any(isinstance(x, (int, float)) and x > 0 for x in (r.get("salary_min"), r.get("salary_max")))
    return {
        "id": _comum.ident(NOME, r["id"]),
        "plataforma": PLATAFORMA,
        "titulo": _comum.consertar(r.get("position")).strip(),
        "empresa": _comum.consertar(r.get("company")).strip() or "Empresa não informada",
        "local": f"Remoto ({local})" if local else "Remoto",
        "remoto": True,
        "publicada_em": _comum.data_iso(r.get("date") or r.get("epoch")),
        "url": str(r.get("url") or ""),
        "url_candidatura": None,  # o apply_url leva para a mesma página da vaga
        "salario": _comum.salario(r.get("salary_min"), r.get("salary_max"), "USD", "year") if tem_salario else None,
        "moeda": "USD" if tem_salario else None,
        "tipo": None,
        "descricao": _comum.texto(_comum.consertar(r.get("description"))),
        "restricao_local": local,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    return _comum.buscar_lista(NOME, _lista, normalizar, consulta, horas, por_termo)
