"""Indeed: as candidaturas da área logada (myjobs.indeed.com/applied), pela API que a própria página usa
(appStatusJobs?type=POST_APPLY). Cada item traz o jobKey, que é o jk que o dashboard já usa nas vagas do Indeed.

O status vem de dois lados (research §4): o que a empresa marcou (candidateStatus) e o que a pessoa marcou em
"Atualizar status" (selfReportedStatus). Vale o mais recente. "Vaga fechada ou expirada" só informa.

Só leitura: nunca clica em "Atualizar status" nem em nada que mude a candidatura.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from urllib.parse import urlsplit

from . import PortalErro, buscar_json, lida

NOME = "indeed"
PLATAFORMA = "Indeed"
ATIVO = True
ICONE = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="2" y="2" width="20" height="20" '
         'rx="6" fill="currentColor" opacity=".15"/><text x="12" y="16.5" text-anchor="middle" font-size="12" '
         'font-weight="700" fill="currentColor">i</text></svg>')
PAIS = "BR"
URL_CANDIDATURAS = f"https://myjobs.indeed.com/applied?co={PAIS}"
HOST_LOGIN = "secure.indeed.com"
ORIGENS = ("https://myjobs.indeed.com", "https://secure.indeed.com", "https://br.indeed.com", "https://www.indeed.com")
AVISO_LOGIN = "O Indeed mantém o login entre as leituras."
JK = re.compile(r"^[0-9a-f]{16}$")


def logado(url: str) -> bool:
    host = (urlsplit(url or "").hostname or "").lower()
    return host.endswith("indeed.com") and host != HOST_LOGIN


def _quando(ms) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _etapa(status: str) -> tuple[str | None, str | None]:
    s = str(status or "").upper()
    if "HIRED" in s:
        return "encerrada", "contratado"
    if "OFFER" in s:
        return "proposta", None
    if "INTERVIEW" in s:
        return "entrevista", None
    if "REJECT" in s:
        return "encerrada", "nao_aprovado"
    if "NOT_INTERESTED" in s or "WITHDRAW" in s:
        return "encerrada", "desisti"
    if s == "APPLIED":
        return "aplicada", None
    return None, None


def traduzir(item: dict, entrevistas: set[str] | None = None, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    jk = str(item.get("jobKey") or "").lower()
    st = item.get("statuses") or {}
    candidatos = [x for x in (st.get("candidateStatus"), st.get("selfReportedStatus")) if isinstance(x, dict)
                  and x.get("status")]
    escolhido = max(candidatos, key=lambda x: int(x.get("timestamp") or 0)) if candidatos else {}
    texto = str(escolhido.get("status") or "")
    etapa, resultado = _etapa(texto)
    data = _quando(escolhido.get("timestamp")) or _quando(item.get("applyTime")) or hoje.isoformat()
    if item.get("withdrawn"):
        etapa, resultado, texto = "encerrada", "desisti", "WITHDRAWN"
    elif jk in (entrevistas or set()) and etapa in (None, "aplicada"):
        etapa, texto = "entrevista", "INTERVIEW"
    if etapa == "aplicada":
        data = _quando(item.get("applyTime")) or data
    vaga = (st.get("employerJobStatus") or {}).get("status") if isinstance(st.get("employerJobStatus"), dict) else None
    avisos = ["vaga fechada ou expirada no Indeed"] if item.get("jobExpired") or vaga == "CLOSED" else []
    url = item.get("jobUrl") if str(item.get("jobUrl") or "").startswith("http") else ""
    return lida(NOME, PLATAFORMA, id=jk if JK.match(jk) else "", titulo=item.get("jobTitle"),
                empresa=(item.get("company") or {}).get("name"), local=item.get("location"),
                url=url or (f"https://br.indeed.com/viewjob?jk={jk}" if JK.match(jk) else ""), status=texto,
                etapa=etapa, resultado=resultado, data=data, avisos=avisos,
                ativa=etapa in ("aplicada", "entrevista", "proposta") and not avisos)


def ler(aba) -> list[dict]:
    aba.ir(URL_CANDIDATURAS)
    if HOST_LOGIN in aba.url():
        raise PortalErro("o Indeed pediu login", login=True)
    status, dados = buscar_json(aba, f"/api/v1/appStatusJobs?type=POST_APPLY&co={PAIS}")
    if status in (401, 403):
        raise PortalErro("o Indeed pediu login", login=True)
    corpo = (dados or {}).get("body") if isinstance(dados, dict) else None
    if status != 200 or not isinstance(corpo, dict) or not isinstance(corpo.get("appStatusJobs"), list):
        raise PortalErro(f"não consegui ler as candidaturas do Indeed (resposta {status})")
    entrevistas = set()
    st, d = buscar_json(aba, "/api/v1/interviews")  # entrevista marcada pelo Indeed; se falhar, segue sem
    if st == 200 and isinstance(d, dict):
        for e in ((d.get("body") or {}).get("interviews") or []):
            jk = str((e or {}).get("jobKey") or "").lower()
            if JK.match(jk):
                entrevistas.add(jk)
    return [traduzir(x, entrevistas) for x in corpo["appStatusJobs"] if isinstance(x, dict) and x.get("jobKey")]
