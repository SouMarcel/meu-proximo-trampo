"""LinkedIn: o Rastreador de vagas (linkedin.com/jobs-tracker). Pronto, mas DESATIVADO (ATIVO = False): o LinkedIn
restringe contas que considera automatizadas, e ativar exige nova decisão da pessoa (constituição VI).

Lê a tela (cada linha com link /jobs/view/N): cargo, "empresa · local (modelo)" e "Candidatou-se há 1 sem", que vira
uma data aproximada. Ao ativar, uma pesquisa como a da Gupy e do Indeed (research §5) deve procurar a API da página.

Só leitura: nunca clica em "Recebeu resposta? Sim/Não", "Adicionar nota" nem em nada que mude a candidatura.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from urllib.parse import urlsplit

from . import PortalErro, lida

NOME = "linkedin"
PLATAFORMA = "LinkedIn"
ATIVO = False
ICONE = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="2" y="2" width="20" height="20" '
         'rx="6" fill="currentColor" opacity=".15"/><text x="12" y="16.5" text-anchor="middle" font-size="11" '
         'font-weight="700" fill="currentColor">in</text></svg>')
FILTROS = {"applied": "aplicada", "interview": "entrevista"}
URL_CANDIDATURAS = "https://www.linkedin.com/jobs-tracker/?stage=applied"
HOST_LOGIN = "linkedin.com/login"
ORIGENS = ("https://www.linkedin.com",)
AVISO_LOGIN = "O LinkedIn fica desativado: ele restringe contas que considera automatizadas."
DIAS = {"min": 0, "h": 0, "d": 1, "dia": 1, "dias": 1, "sem": 7, "m": 30, "mês": 30, "meses": 30, "a": 365, "ano": 365,
        "anos": 365}
JS_LINHAS = """(() => [...document.querySelectorAll('a[href*="/jobs/view/"]')].map(a => {
  const linha = a.closest('li, tr, [data-view-name]') || a.parentElement;
  return {href: a.href, texto: linha ? linha.innerText : a.innerText};
}))()"""


def logado(url: str) -> bool:
    host = (urlsplit(url or "").hostname or "").lower()
    return host.endswith("linkedin.com") and not any(x in (url or "") for x in ("/login", "/checkpoint", "/uas/", "/authwall"))


def data_aproximada(texto: str, hoje: date | None = None) -> tuple[str, bool]:
    """("AAAA-MM-DD", aproximada) a partir de "Candidatou-se há 1 sem" / "há 3 d" / "hoje"."""
    hoje = hoje or date.today()
    m = re.search(r"há\s+(\d+)\s*([a-zà-ú]+)", texto or "", re.I)
    if m:
        dias = DIAS.get(m.group(2).lower().rstrip("."), 0) * int(m.group(1))
        return (hoje - timedelta(days=dias)).isoformat(), True
    return hoje.isoformat(), "hoje" not in (texto or "").lower()


def traduzir(href: str, texto: str, filtro: str = "applied", hoje: date | None = None) -> dict | None:
    m = re.search(r"/jobs/view/(\d+)", href or "")
    linhas = [" ".join(x.split()) for x in str(texto or "").splitlines() if x.strip()]
    if not m or not linhas:
        return None
    empresa_local = next((x for x in linhas[1:] if " · " in x), "")
    empresa, _, local = empresa_local.partition(" · ")
    quando = next((x for x in linhas if x.lower().startswith("candidatou-se")), "")
    data, aproximada = data_aproximada(quando, hoje)
    avisos = ["não aceita mais candidaturas"] if "não aceita mais candidaturas" in " ".join(linhas).lower() else []
    etapa = FILTROS.get(filtro)
    return lida(NOME, PLATAFORMA, id=f"li-{m.group(1)}", titulo=linhas[0], empresa=empresa, local=local,
                url=f"https://www.linkedin.com/jobs/view/{m.group(1)}/", status=filtro, etapa=etapa, data=data,
                nota="data aproximada (o LinkedIn mostra só há quanto tempo)" if aproximada else "", avisos=avisos,
                ativa=etapa is not None and not avisos)


def ler(aba) -> list[dict]:
    lidas = []
    for filtro in FILTROS:
        aba.ir(f"https://www.linkedin.com/jobs-tracker/?stage={filtro}")
        if HOST_LOGIN in aba.url() or "/checkpoint/" in aba.url():
            raise PortalErro("o LinkedIn pediu login ou verificação", login=True)
        for linha in aba.avaliar(JS_LINHAS) or []:
            x = traduzir((linha or {}).get("href"), (linha or {}).get("texto"), filtro)
            if x:
                lidas.append(x)
    return lidas
