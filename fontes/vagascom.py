"""Fonte Vagas.com: a busca pública do portal brasileiro generalista de vagas (vagas.com.br), sem login e sem a conta,
as senhas ou os cookies da pessoa (spec 029).

A lista de cada cargo (vagas-de-<cargo>?ordenar_por=mais_recentes&pagina=N) é lida uma vez por busca, da vaga mais
nova para a mais antiga, até MAX_PAGINAS páginas ou a primeira vaga fora da janela, e serve às consultas do mesmo
cargo (remoto, país e cidade). A busca do site é ampla, então fica só a vaga cujo título bate com o cargo. A lista só
diz se a vaga é 100% home office; o modelo das outras fica para a análise. A descrição vem da página da vaga (os
dados estruturados JobPosting), só das vagas que vão para o relatório, no máximo MAX_DESCRICOES por busca.

Pausa sorteada de 3 a 7 segundos entre os pedidos (VAGASCOM_PAUSA=N no .env muda para N a N+4, com N de 3 a 60) e,
no primeiro bloqueio (recusa, limite de consultas ou pedido de login), o Vagas.com fica de fora pelo resto da busca,
sem nova tentativa, e das buscas das 24 horas seguintes (a espera, gravada em .cache/).
"""
from __future__ import annotations

import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin

from . import _comum, link

NOME = "vagascom"
PLATAFORMA = "Vagas.com"
AREAS = ("nacional",)  # só vagas do Brasil
TERMOS = ("Consulta não oficial à busca pública do Vagas.com, portal de vagas de todas as áreas no Brasil, sem login. "
          "Há uma pausa de alguns segundos entre as consultas e, se o Vagas.com limitar, a busca segue sem ele e ele "
          "fica 24 horas em espera. A candidatura é sempre no próprio Vagas.com.")

SITE = "https://www.vagas.com.br/"
POR_PAGINA = 40  # o que a lista mostra por página
MAX_PAGINAS = 3  # por cargo; a janela de tempo costuma parar antes
MAX_DESCRICOES = 30  # páginas de vaga lidas por busca; as outras ficam pendentes para a próxima
PAUSA = (3.0, 7.0)  # padrão, sem VAGASCOM_PAUSA
VAR_PAUSA = "VAGASCOM_PAUSA"  # no .env ou no ambiente: segundos de pausa mínima (spec 029)
PAUSA_MIN, PAUSA_FAIXA = 3.0, 4.0  # N de 3 a 60; a pausa é sorteada de N a N + 4
ESPERA = timedelta(hours=24)  # depois de um bloqueio, o Vagas.com fica de fora das buscas
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "vagascom-espera.json"
LIMITE_DESCRICAO = 12000
BLOQUEIO = "o Vagas.com limitou as consultas"
ILEGIVEL = "não consegui ler as vagas do Vagas.com (a página pode ter mudado)"
VAGA = re.compile(r"^(?:https?://(?:www\.)?vagas\.com\.br)?/vagas/v(\d+)(?:/[^?#]*)?(?:[?#].*)?$", re.I)
CAMPOS = {"emprVaga": "empresa", "nivelVaga": "nivel", "detalhes": "resumo", "vaga-local": "local",
          "data-publicacao": "data", "vaga-pne": "pcd"}

_estado = {"bloqueado": False, "ultimo": None, "listas": {}, "pausa": None, "avisou_espera": False}


def _esquecer() -> None:
    _estado.update(bloqueado=False, listas={}, pausa=None, avisou_espera=False)  # a pausa é lida de novo a cada busca


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- pausa, bloqueio e espera

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou VAGASCOM_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN, faixa=PAUSA_FAIXA)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com VAGASCOM_PAUSA definida (páginas de lista por cargo + descrições, no máximo)."""
    return _comum.aviso_pausa(PLATAFORMA, "no Vagas.com", VAR_PAUSA, pausa(),
                              consultas * MAX_PAGINAS + MAX_DESCRICOES if consultas else 0)


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    _comum.pausar(_estado, _estado["pausa"])


def espera(agora: datetime | None = None) -> dict | None:
    """{"ate", "motivo"} nas ESPERA horas depois do último bloqueio; None fora delas ou sem arquivo legível."""
    return _comum.ler_espera(ARQ_ESPERA, ESPERA, agora)


def parada() -> bool:
    """Bloqueou nesta busca ou está em espera: a vaga sem texto fica pendente."""
    return _estado["bloqueado"] or espera() is not None


def _bloquear(motivo: str) -> _comum.FonteErro:
    """Para o Vagas.com nesta busca e grava a espera para as próximas (o aviso do bloqueio já diz até quando)."""
    _estado.update(bloqueado=True, avisou_espera=True)
    ate = (_comum.gravar_espera(ARQ_ESPERA, motivo) + ESPERA).isoformat(timespec="minutes")
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); em espera até {_comum.ate_quando(ate)}")


def _baixar(url: str) -> str:
    return _comum.baixar_pagina(url, "o Vagas.com", _pausar, _bloquear, sinais_login=("login", "/auth"))


# ---------------------------------------------------------------- leitura dos cards

class _Cards(HTMLParser):
    """Os cards da lista: li.vaga; o link a.link-detalhes-vaga (data-id-vaga, href e o título inteiro no atributo
    title); empresa, nível, trecho do texto, local, data e o selo de PCD nas classes de CAMPOS. O balão de ajuda do
    local (div.tooltip-place) fica de fora."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.pilha: list[tuple[str, str | None, bool]] = []  # (tag, campo, ignorar o texto)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "li" and "vaga" in classes:
            self.cards.append({})
        if not self.cards:
            return
        card = self.cards[-1]
        if tag == "a" and "link-detalhes-vaga" in classes:
            card.update(href=a.get("href") or "", titulo=a.get("title") or "")
        if tag in link.VAZIOS:
            return
        campo = next((CAMPOS[c] for c in classes if c in CAMPOS), None)
        self.pilha.append((tag, campo, "tooltip-place" in classes))

    def handle_endtag(self, tag):
        if any(t == tag for t, _, _ in self.pilha):
            while self.pilha and self.pilha.pop()[0] != tag:
                pass

    def handle_data(self, data):
        if not self.cards or not data.strip():
            return
        for _, campo, ignorar in reversed(self.pilha):
            if ignorar:
                return
            if campo:
                card = self.cards[-1]
                card[campo] = (card.get(campo, "") + " " + data).strip()
                return


def _espacos(s) -> str:
    return " ".join(str(s or "").split())


def data_relativa(texto: str, hoje) -> str | None:
    """AAAA-MM-DD a partir de "Hoje", "Ontem", "Há 3 dias" ou "24/09/2026"; None se não reconhecer. O site também
    escreve em espanhol ("Hoy", "Ayer", "Hace 3 días") quando não reconhece o termo da busca."""
    t = _comum._norm(texto)
    if t in ("hoje", "hoy"):
        return hoje.isoformat()
    if t in ("ontem", "ayer"):
        return (hoje - timedelta(days=1)).isoformat()
    m = re.fullmatch(r"(?:ha|hace) (\d+) dias?", t)
    if m:
        return (hoje - timedelta(days=int(m.group(1)))).isoformat()
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(texto or ""))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def ler_lista(pagina: str) -> list[dict]:
    """As vagas de uma página de resultados, no formato comum (sem a descrição)."""
    p = _Cards()
    p.feed(pagina)
    p.close()
    hoje = _agora().astimezone().date()
    vagas, vistos = [], set()
    for c in p.cards:
        m = VAGA.match(str(c.get("href") or "").strip())
        titulo = _espacos(c.get("titulo"))
        if not m or m.group(1) in vistos or not titulo:
            continue
        vistos.add(m.group(1))
        local = _espacos(c.get("local"))
        local = "" if "nao informad" in _comum._norm(local) else local  # "Localização não informada"
        remoto = "home office" in _comum._norm(local)
        cidade, _, uf = local.rpartition(" / ")
        detalhes = [_espacos(c.get("nivel"))] + (["Exclusiva para PCD"] if c.get("pcd") else [])
        v = {
            "id": _comum.ident(NOME, m.group(1)), "plataforma": PLATAFORMA, "titulo": titulo,
            "empresa": _espacos(c.get("empresa")) or "Empresa não informada",
            "local": "Remoto" if remoto else f"{cidade.strip()}, {uf.strip()}" if cidade and uf else local,
            "remoto": remoto, "publicada_em": data_relativa(c.get("data"), hoje),
            "url": urljoin(SITE, c["href"].strip()),
            "url_candidatura": None, "salario": None, "tipo": " • ".join(d for d in detalhes if d) or None,
            "descricao": "",
        }
        if remoto:
            v["modelo_trabalho"] = "remoto"
        vagas.append(v)
    return vagas


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def url_lista(termo: str, pagina: int = 1) -> str:
    slug = "-".join(_comum._norm(termo).split())
    params = {"ordenar_por": "mais_recentes", **({"pagina": pagina, "q": termo} if pagina > 1 else {})}
    return f"{SITE}vagas-de-{slug}?{urlencode(params)}"


def _lista(termo: str, horas: int) -> tuple[list[dict], str | None]:
    """As vagas da busca do cargo (todas as páginas lidas), guardadas para as outras consultas do mesmo cargo."""
    if termo in _estado["listas"]:
        return _estado["listas"][termo]
    limite = _limite(horas)
    vagas: list[dict] = []
    erro = None
    for numero in range(1, MAX_PAGINAS + 1):
        try:
            pagina = _baixar(url_lista(termo, numero))
        except _comum.FonteErro as e:
            erro = str(e)
            break
        achadas = ler_lista(pagina)
        if not achadas:
            if numero == 1 and 'class="vaga ' in pagina:
                erro = ILEGIVEL
            break
        ids = {v["id"] for v in vagas}
        vagas += [v for v in achadas if v["id"] not in ids]
        datas = [v["publicada_em"] for v in achadas if v.get("publicada_em")]
        if len(achadas) < POR_PAGINA or (datas and min(datas) < limite) or f"pagina={numero + 1}" not in pagina:
            break
    _estado["listas"][termo] = (vagas, erro)
    return vagas, erro


def _atende(vaga: dict, consulta: dict, limite: str) -> bool:
    if not _comum.bate_cargo(vaga["titulo"], consulta["termo"]):
        return False
    if vaga.get("publicada_em") and vaga["publicada_em"] < limite:
        return False
    if consulta.get("remoto"):
        return vaga["remoto"]
    if consulta.get("cidade"):
        cidade, _, uf = str(vaga.get("local") or "").rpartition(", ")
        return not vaga["remoto"] and _comum.na_regiao(cidade, uf, consulta)
    modelos = consulta.get("modelos") or []
    return not (vaga["remoto"] and modelos and "remoto" not in modelos)


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if consulta.get("pais") != "brazil":
        return [], []  # o Vagas.com é só do Brasil
    e = espera()
    if e:  # durante a espera, nenhum pedido; o aviso sai uma vez por busca
        if _estado["avisou_espera"]:
            return [], []
        _estado["avisou_espera"] = True
        return [], [f"{PLATAFORMA} em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); a busca seguiu sem ele"]
    termo = " ".join(str(consulta.get("termo") or "").replace('"', " ").split())
    ja_lida = termo in _estado["listas"]
    if not termo or (_estado["bloqueado"] and not ja_lida):
        return [], []  # depois de um bloqueio, nenhum pedido a mais (a lista já lida continua valendo)
    vagas, erro = _lista(termo, horas)
    limite = _limite(horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []


def descrever(vaga: dict) -> str:
    """A descrição da página da vaga (dados estruturados JobPosting). Depois de um bloqueio ou na espera, devolve o
    que a vaga já tinha, sem pedido."""
    if parada():
        return vaga.get("descricao") or ""
    url = str(vaga.get("url") or "")
    if not VAGA.match(url):
        raise _comum.FonteErro("link de vaga do Vagas.com inesperado")
    lida = link.extrair_jobposting(_baixar(url), PLATAFORMA)
    return (lida.get("descricao") or vaga.get("descricao") or "")[:LIMITE_DESCRICAO]


def id_do_link(url: str) -> str | None:
    """O id da vaga ("vagascom-123") a partir do link da página da vaga; None para outros links."""
    m = VAGA.match(str(url or "").strip())
    return _comum.ident(NOME, m.group(1)) if m and str(url).lower().startswith(("http://", "https://")) else None
