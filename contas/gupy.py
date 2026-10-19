"""Gupy: as candidaturas da área logada (portal.gupy.io/my/applications), pela API que a própria página usa.

- A lista (todas as candidaturas de uma vez) vem de portal.gupy.io. Ela não traz o id da vaga.
- O detalhe de cada candidatura em andamento (id da vaga, etapa atual e categoria dela) só responde a partir da
  página da empresa (<subdominio>.gupy.io/candidates/applications/<id>); o id da vaga fica guardado em
  .cache/contas/gupy.json para não abrir a página de novo.
- A Gupy esquece o login quando a janela fecha: a janela fica aberta (minimizada) enquanto o dashboard roda; se a
  Gupy pedir login, a leitura traz a janela para a frente e espera a pessoa entrar (research §3).

Só leitura: nunca clica em "Desistir" nem em nada que mude a candidatura.
"""
from __future__ import annotations

import json
import re
from datetime import date
from urllib.parse import urlsplit

from . import PASTA, PortalErro, buscar_json, lida

NOME = "gupy"
PLATAFORMA = "Gupy"
ATIVO = True
ICONE = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="2" y="2" width="20" height="20" '
         'rx="6" fill="currentColor" opacity=".15"/><text x="12" y="16.5" text-anchor="middle" font-size="12" '
         'font-weight="700" fill="currentColor">G</text></svg>')
URL_CANDIDATURAS = "https://portal.gupy.io/my/applications"
HOST_LOGIN = "login.gupy.io"
ORIGENS = ("https://portal.gupy.io", "https://login.gupy.io", "https://private-api.gupy.io")
AVISO_LOGIN = ("A Gupy esquece o login quando a janela fecha: a janela fica aberta e minimizada enquanto o dashboard "
               "roda, e você entra de novo (ex.: com o LinkedIn) só quando o dashboard reinicia.")
API = "https://private-api.gupy.io/selection-process/candidate"
MAPA = PASTA / "gupy.json"
SUBDOMINIO = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
MODELO = {"remote": "Remoto", "hybrid": "Híbrido", "on-site": "Presencial"}
TALENTOS = "vacancy_type_talent_pool"


def logado(url: str) -> bool:
    """De volta à Gupy fora da página de login (o "Entrar com LinkedIn" passa pelo LinkedIn no meio do caminho)."""
    host = (urlsplit(url or "").hostname or "").lower()
    return host.endswith("gupy.io") and host != HOST_LOGIN


def _mapa() -> dict:
    try:
        d = json.loads(MAPA.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_mapa(m: dict) -> None:
    MAPA.parent.mkdir(parents=True, exist_ok=True)
    MAPA.write_text(json.dumps(m), encoding="utf-8")


def ativa(item: dict) -> bool:
    """Em andamento na tela da Gupy: em processo, vaga publicada (ou congelada), fora do banco de talentos."""
    return (item.get("applicationStatus") == "in_process" and item.get("jobStatus") in ("published", "frozen")
            and item.get("jobType") != TALENTOS)


def _etapa_atual(detalhe: dict | None) -> dict | None:
    if not detalhe:
        return None
    atual = detalhe.get("currentStepId")
    return next((s for s in (detalhe.get("job") or {}).get("jobSteps") or [] if s.get("id") == atual), None)


def traduzir(item: dict, detalhe: dict | None = None, job_id=None, hoje: date | None = None) -> dict:
    """Lida a partir de um item da lista e, nas ativas, do detalhe (research §3)."""
    hoje = hoje or date.today()
    app, sub = item.get("applicationId"), str(item.get("careerPageSubdomain") or "")
    job_id = job_id or ((detalhe or {}).get("job") or {}).get("id")
    sub_ok = SUBDOMINIO.match(sub)
    if job_id:
        vid, url = f"gupy-{job_id}", (f"https://{sub}.gupy.io/jobs/{job_id}" if sub_ok else "")
    else:
        vid, url = f"gupya-{app}", (f"https://{sub}.gupy.io/candidates/applications/{app}" if sub_ok else "")
    lugar = "/".join(x for x in (item.get("addressCity"), item.get("addressStateShortName")) if x)
    local = " · ".join(x for x in (MODELO.get(item.get("workplaceType") or ""), lugar) if x)
    st, vaga = item.get("applicationStatus"), item.get("jobStatus")
    etapa, resultado, nota = None, None, ""
    if st == "reproved":
        etapa, resultado = "encerrada", "nao_aprovado"
    elif item.get("jobType") == TALENTOS:
        etapa, nota = "aplicada", "candidatura ao banco de talentos da empresa"
    elif st == "in_process" and vaga == "canceled":
        etapa, resultado = "encerrada", "cancelada"
    elif st == "in_process" and vaga == "closed":
        etapa, nota = "encerrada", "vaga encerrada na Gupy sem resultado para você"
    elif ativa(item):
        passo = _etapa_atual(detalhe) or {}
        categoria, nome = passo.get("category"), " ".join(str(passo.get("name") or "").split())[:80]
        etapa = {"interview": "entrevista", "hiring": "proposta"}.get(categoria, "aplicada")
        k, n = item.get("jobStepCurrent"), item.get("jobStepCount")
        nota = f"Gupy: etapa {k} de {n}" + (f" ({nome})" if nome else "") if k is not None and n else nome
    return lida(NOME, PLATAFORMA, id=vid, titulo=item.get("jobName"), empresa=item.get("careerPageName"),
                local=local, url=url, status=f"{st} · vaga {vaga}", etapa=etapa, resultado=resultado,
                data=hoje.isoformat(), nota=nota, ativa=ativa(item))


def ler(aba) -> list[dict]:
    aba.ir(URL_CANDIDATURAS)
    if HOST_LOGIN in aba.url():
        raise PortalErro("a Gupy pediu login", login=True)
    status, dados = buscar_json(aba, f"{API}/applications")
    if status in (401, 403):
        raise PortalErro("a Gupy pediu login", login=True)
    if status != 200 or not isinstance(dados, dict) or not isinstance(dados.get("results"), list):
        raise PortalErro(f"não consegui ler as candidaturas da Gupy (resposta {status})")
    itens = [x for x in dados["results"] if isinstance(x, dict) and str(x.get("applicationId") or "").isdigit()]
    mapa, lidas = _mapa(), []
    for item in itens:
        detalhe = None
        sub = str(item.get("careerPageSubdomain") or "")
        if ativa(item) and SUBDOMINIO.match(sub):  # só as em andamento: a etapa atual muda
            aba.ir(f"https://{sub}.gupy.io/candidates/applications/{item['applicationId']}")
            st, d = buscar_json(aba, f"{API}/application/{item['applicationId']}/step")
            if st in (401, 403):
                raise PortalErro("a Gupy pediu login", login=True)
            if st == 200 and isinstance(d, dict):
                detalhe = d
                if (d.get("job") or {}).get("id"):
                    mapa[str(item["applicationId"])] = d["job"]["id"]
        lidas.append(traduzir(item, detalhe, mapa.get(str(item["applicationId"]))))
    _guardar_mapa(mapa)
    return lidas
