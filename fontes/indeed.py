"""Fonte Indeed, via python-jobspy (usa a API do app do Indeed; não precisa de login nem de chave)."""
from __future__ import annotations

import logging
import math
import re
from datetime import date, datetime

NOME = "indeed"
PLATAFORMA = "Indeed"
AREAS = ("nacional", "internacional")  # o Indeed tem site em cada país
LIMITE_DESCRICAO = 12000


def _valor(v):
    """Converte células do pandas/numpy em tipos JSON simples."""
    if v is None:
        return None
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        try:
            v = v.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()[:10]
    if isinstance(v, str) and v.strip() in ("", "nan", "NaT", "None"):
        return None
    if type(v).__name__ == "NaTType":
        return None
    return v


def _salario(r: dict) -> str | None:
    lo, hi = r.get("min_amount"), r.get("max_amount")
    if lo is None and hi is None:
        return None
    simbolo = {"BRL": "R$", "USD": "US$", "EUR": "€"}.get(r.get("currency") or "", r.get("currency") or "")
    fmt = lambda x: f"{x:,.0f}".replace(",", ".")
    if lo is None or hi is None or lo == hi:
        faixa = fmt(lo if lo is not None else hi)
    else:
        faixa = f"{fmt(lo)}–{fmt(hi)}"
    periodo = {"yearly": "/ano", "monthly": "/mês", "weekly": "/semana", "daily": "/dia", "hourly": "/hora"}.get(
        r.get("interval") or "", "")
    return f"{simbolo} {faixa}{periodo}".strip()


def _normalizar(r: dict) -> dict | None:
    url = r.get("job_url") or ""
    m = re.search(r"[?&]jk=([0-9a-f]+)", url)
    jid = m.group(1) if m else str(r.get("id") or "").removeprefix("in-")
    if not jid:
        return None
    desc = (r.get("description") or "").strip()
    return {
        "id": jid,
        "plataforma": PLATAFORMA,
        "titulo": (r.get("title") or "").strip(),
        "empresa": (r.get("company") or "").strip() or "Empresa não informada",
        "local": r.get("location") or "",
        "remoto": bool(r.get("is_remote")),
        "publicada_em": r.get("date_posted"),
        "url": url,
        "url_candidatura": r.get("job_url_direct"),
        "salario": _salario(r),
        "tipo": r.get("job_type"),
        "descricao": desc[:LIMITE_DESCRICAO],
    }


class _ColetorErros(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.mensagens: list[str] = []

    def emit(self, record):
        self.mensagens.append(record.getMessage())


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    from jobspy import scrape_jobs  # ImportError é tratado por quem chama

    coletor = _ColetorErros()
    logger = logging.getLogger("JobSpy:Indeed")
    logger.addHandler(coletor)
    raio = consulta.get("raio_km")
    try:
        df = scrape_jobs(
            site_name=["indeed"], search_term=consulta["termo"], location=consulta.get("local") or None,
            distance=max(1, round(raio / 1.609)) if raio else 50,  # o Indeed mede o raio em milhas
            results_wanted=por_termo, hours_old=horas, country_indeed=consulta["pais"],
            is_remote=consulta["remoto"], description_format="markdown", verbose=0,
        )
    except Exception as e:  # a biblioteca levanta tipos variados
        return [], [str(e)]
    finally:
        logger.removeHandler(coletor)
    vagas = []
    for linha in df.to_dict("records"):
        vaga = _normalizar({k: _valor(v) for k, v in linha.items()})
        if vaga:
            vagas.append(vaga)
    return vagas, coletor.mensagens
