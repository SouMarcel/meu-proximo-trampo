"""Fonte We Work Remotely (RSS público em weworkremotely.com/remote-jobs.rss): vagas remotas, sem login.

Um RSS com as vagas recentes de todas as categorias, lido uma vez por busca (os cargos são filtrados
aqui). O título vem como "Empresa: Cargo"; `region` diz onde a pessoa precisa estar e vira a restrição de
local. O dashboard cita o We Work Remotely e linka a vaga original.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from . import _comum

NOME = "weworkremotely"
PLATAFORMA = "We Work Remotely"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Cita o We Work Remotely e linka a vaga original; um RSS por busca."
URL = "https://weworkremotely.com/remote-jobs.rss"


def _lista() -> list:
    try:
        raiz = ET.fromstring(_comum.baixar_texto(URL).encode("utf-8"))
    except ET.ParseError:
        raise _comum.FonteErro("resposta inesperada do We Work Remotely") from None
    itens = []
    for item in raiz.iter("item"):
        itens.append({filho.tag: (filho.text or "").strip() for filho in item if "}" not in filho.tag})
    return itens


def normalizar(r: dict) -> dict | None:
    link = r.get("link") or r.get("guid") or ""
    slug = link.rstrip("/").rsplit("/", 1)[-1]
    if not slug:
        return None
    empresa, _, cargo = str(r.get("title") or "").partition(": ")
    if not cargo:
        empresa, cargo = "", empresa
    regiao = _comum.curto(r.get("region"))
    return {
        "id": _comum.ident(NOME, slug),
        "plataforma": PLATAFORMA,
        "titulo": cargo.strip(),
        "empresa": empresa.strip() or "Empresa não informada",
        "local": f"Remoto ({regiao})" if regiao else "Remoto",
        "remoto": True,
        "publicada_em": _comum.data_iso(r.get("pubDate")),
        "url": link,
        "url_candidatura": None,
        "salario": None,
        "tipo": _comum.curto(r.get("type"), 40),
        "descricao": _comum.texto(r.get("description")),
        "restricao_local": regiao,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    return _comum.buscar_lista(NOME, _lista, normalizar, consulta, horas, por_termo)
