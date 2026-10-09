"""Fonte Get on Board (getonbrd.com/api/v0/search/jobs): vagas de tecnologia da América Latina, API pública.

Busca por cargo (`query`), uma consulta por cargo, e confere o título aqui. A vaga diz se é remota e de que
jeito (`remote_modality`: remoto de qualquer lugar, remoto só no país, híbrido, presencial), os países e o
idioma do anúncio. O salário vem por mês, em dólar. O dashboard cita o Get on Board e linka a vaga.
"""
from __future__ import annotations

from . import _comum

NOME = "getonboard"
PLATAFORMA = "Get on Board"
AREAS = ("internacional",)
POR_PAIS = False
TERMOS = "Cita o Get on Board e linka a vaga original; uma consulta por cargo."
URL = "https://www.getonbrd.com/api/v0/search/jobs"
QUANTAS = 50
IDIOMAS = {"spanish": "es", "english": "en", "portuguese": "pt", "es": "es", "en": "en", "pt": "pt"}
MODELOS = {"hybrid": "hibrido", "no_remote": "presencial", "remote_local": "remoto", "fully_remote": "remoto",
           "temporarily_remote": "remoto"}
MODALIDADES = {"hybrid": "híbrido", "no_remote": "presencial", "remote_local": "remoto no país",
               "fully_remote": "remoto", "temporarily_remote": "remoto por um tempo"}


def normalizar(r: dict) -> dict | None:
    a = r.get("attributes") if isinstance(r.get("attributes"), dict) else {}
    if not r.get("id") or not a:
        return None
    empresa = ((a.get("company") or {}).get("data") or {}).get("attributes") or {}
    paises = [str(p).strip() for p in a.get("countries") or [] if str(p).strip() and str(p).strip() != "Remote"]
    remoto = bool(a.get("remote"))
    modalidade = a.get("remote_modality") or ""
    if modalidade == "fully_remote":
        restricao = _comum.curto(a.get("remote_zone"))
    else:  # remoto só no país, híbrido e presencial: os países da vaga (ou o da empresa)
        restricao = _comum.curto(", ".join(paises) or empresa.get("country") or a.get("remote_zone"))
    partes = [a.get("functions"), a.get("description"), a.get("desirable"), a.get("benefits")]
    descricao = _comum.texto("\n".join(str(p) for p in partes if p))
    if modalidade in MODALIDADES:
        descricao = (descricao + "\n\nNo Get on Board: modelo " + MODALIDADES[modalidade]).strip()
    links = r.get("links") if isinstance(r.get("links"), dict) else {}
    lugar = ", ".join(paises) or empresa.get("country") or ""
    return {
        "id": _comum.ident(NOME, r["id"]),
        "plataforma": PLATAFORMA,
        "titulo": str(a.get("title") or "").strip(),
        "empresa": str(empresa.get("name") or "").strip() or "Empresa não informada",
        "local": (f"Remoto ({lugar})" if lugar else "Remoto") if remoto else lugar,
        "remoto": remoto,
        "modelo_trabalho": MODELOS.get(modalidade),
        "publicada_em": _comum.data_iso(a.get("published_at")),
        "url": str(links.get("public_url") or ""),
        "url_candidatura": None,
        "salario": _comum.salario(a.get("min_salary"), a.get("max_salary"), "USD", "month"),
        "moeda": "USD" if a.get("min_salary") or a.get("max_salary") else None,
        "tipo": None,
        "descricao": descricao,
        "restricao_local": restricao,
        "idioma": IDIOMAS.get(str(a.get("lang") or "").lower()),
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    termo = " ".join(consulta["termo"].replace('"', " ").split())

    def lista():
        dados = _comum.baixar_json(URL, {"query": termo, "per_page": QUANTAS, "expand": '["company"]'})
        if not isinstance(dados, dict) or not isinstance(dados.get("data"), list):
            raise _comum.FonteErro("resposta inesperada do Get on Board")
        return dados["data"]

    return _comum.buscar_lista(f"{NOME}:{termo.lower()}", lista, normalizar, consulta, horas, por_termo)
