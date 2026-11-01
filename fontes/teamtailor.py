"""Empresas acompanhadas no Teamtailor (spec 042): a lista pública de vagas que o próprio site de carreiras oferece
(feed RSS em https://<site>/jobs.rss, anunciado na página de vagas e liberado pelo robots.txt), sem login.

O feed traz, por vaga, o título, a descrição em HTML, a data, o link (/jobs/<número>-<slug>), o modelo de trabalho
(remoteStatus) e os locais (cidade e país). Ele mostra até 100 vagas, as mais recentes; empresa com mais vagas abertas
tem as mais antigas fora, o que basta para a janela de dias da busca. Uma leitura por empresa por busca
(fontes/ats.py chama lista() pela memória da busca).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from . import _comum

TT = "{https://teamtailor.com/locations}"
ID = re.compile(r"/jobs/(\d+)")
LIMITE_BYTES = 5_000_000
# remoteStatus do Teamtailor -> modelo de trabalho; "none" é sem modelo informado
MODELOS = {"fully": "remoto", "remote": "remoto", "temporary": "remoto", "hybrid": "hibrido", "onsite": "presencial"}
FORMATO = "a lista de vagas do Teamtailor veio num formato inesperado"


def feed(host: str) -> str:
    return f"https://{host}/jobs.rss"


def _texto(el, caminho: str) -> str:
    achado = el.find(caminho)
    return " ".join((achado.text or "").split()) if achado is not None else ""


def nome_bonito(nome: str) -> str:
    """O nome do feed sem gritar ("LOJAS EXEMPLO BR" -> "Lojas Exemplo BR")."""
    if nome.isupper():
        return " ".join(p if len(p) <= 2 else p.capitalize() for p in nome.split())
    return nome


def ler_feed(xml: str, empresa: dict) -> list[dict]:
    """As vagas do feed no formato comum, com o id teamtailor-<site>-<número>."""
    try:
        canal = ET.fromstring(xml).find("channel")
    except ET.ParseError:
        raise _comum.FonteErro(FORMATO) from None
    if canal is None:
        raise _comum.FonteErro(FORMATO)
    host = str(empresa.get("id") or "")
    nome = str(empresa.get("nome") or "").strip() or nome_bonito(_texto(canal, "title")) or host
    vagas = []
    for item in canal.findall("item"):
        titulo, url = _texto(item, "title"), _texto(item, "link")
        m = ID.search(urlsplit(url).path)
        if not titulo or not m or not url.startswith("https://"):
            continue
        modelo = MODELOS.get(_texto(item, "remoteStatus").lower())
        remoto = modelo == "remoto"
        lugares, paises = [], []
        for loc in item.findall(f"{TT}locations/{TT}location"):
            cidade, pais = _texto(loc, f"{TT}city"), _texto(loc, f"{TT}country")
            lugar = ", ".join(x for x in (cidade or _texto(loc, f"{TT}name"), pais) if x)
            if lugar and lugar not in lugares:
                lugares.append(lugar)
            if pais and pais not in paises:
                paises.append(pais)
        local = "; ".join(lugares)
        v = {"id": _comum.ident("teamtailor", f"{host}-{m.group(1)}"), "plataforma": "Teamtailor", "ats": "teamtailor",
             "titulo": titulo, "empresa": nome, "local": local or ("Remoto" if remoto else ""), "remoto": remoto,
             "publicada_em": _comum.data_iso(_texto(item, "pubDate")), "url": url, "url_candidatura": None,
             "salario": None, "tipo": _comum.curto(_texto(item, f"{TT}department"), 80),
             "descricao": _comum.texto(item.findtext("description") or "")}
        if modelo:
            v["modelo_trabalho"] = modelo
        if remoto and paises:
            v["restricao_local"] = _comum.curto(", ".join(paises))
        vagas.append(v)
    return vagas


def lista(empresa: dict) -> list[dict]:
    """O feed da empresa (um pedido, sem nova tentativa) no formato comum."""
    corpo = _comum.baixar(feed(str(empresa["id"])), aceitar="application/rss+xml, application/xml, text/xml",
                          nova_tentativa=False)
    return ler_feed(corpo.decode("utf-8", errors="replace"), empresa)
