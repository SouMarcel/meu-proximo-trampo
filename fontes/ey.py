"""Fonte EY: a busca pública do site de vagas da EY (careers.ey.com, no SAP SuccessFactors), sem login e sem a
conta, as senhas ou os cookies da pessoa (spec 039).

A lista de cada cargo (search/?q=<cargo>&locationsearch=<país>, das mais recentes para as mais antigas) é lida uma
vez por busca, até MAX_PAGINAS páginas, e serve às consultas do mesmo cargo (remoto, país e cidade). A busca do site é
ampla, então fica só a vaga cujo título bate com o cargo. A lista não traz data nem modelo de trabalho: a busca abre a
página de cada vaga que bateu (os microdados schema.org trazem data, locais e descrição), no máximo MAX_VAGAS páginas
por busca, e para na primeira vaga mais antiga que a janela. As vagas já lidas ficam numa memória de datas
(.cache/ey-datas.json: número, data e locais, sem nada da pessoa), para a página não ser aberta de novo nas próximas
buscas; as que ficarem além do limite entram numa busca seguinte. O RSS do site fica numa área bloqueada pelo
robots.txt e não é usado.

Pausa sorteada de 3 a 7 segundos entre os pedidos (EY_PAUSA=N no .env muda para N a N+4, com N de 3 a 60) e, no
primeiro bloqueio (recusa, limite de consultas ou pedido de login), a EY fica de fora pelo resto da busca, sem nova
tentativa (sem espera entre buscas, como a Nerdin).
"""
from __future__ import annotations

import html
import json
import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin

from . import _comum, link

NOME = "ey"
PLATAFORMA = "EY"
AREAS = ("nacional",)
TERMOS = ("Consulta não oficial à busca pública do site de vagas da EY, sem login. A ferramenta abre a página de cada "
          "vaga que bate com o cargo, para ler a data e a descrição. Há uma pausa de alguns segundos entre as "
          "consultas e, se a EY limitar, a busca segue sem ela. A candidatura é sempre no próprio site da EY.")

SITE = "https://careers.ey.com/ey/"
POR_PAGINA = 25  # o que a lista mostra por página
MAX_PAGINAS = 2  # por cargo
MAX_VAGAS = 20  # páginas de vaga abertas por busca (busca e descrever); as outras ficam para a próxima
ORDEM_POR_DATA = True  # a lista vem da mais nova para a mais antiga: a primeira vaga fora da janela encerra a leitura
PAUSA = (3.0, 7.0)  # padrão, sem EY_PAUSA
VAR_PAUSA = "EY_PAUSA"  # no .env ou no ambiente: segundos de pausa mínima (spec 039)
PAUSA_MIN, PAUSA_FAIXA = 3.0, 4.0  # N de 3 a 60; a pausa é sorteada de N a N + 4
ARQ_DATAS = Path(__file__).resolve().parent.parent / ".cache" / "ey-datas.json"
VALIDADE_DATAS = timedelta(days=60)  # entradas lidas há mais tempo saem da memória
LIMITE_DESCRICAO = 12000
BLOQUEIO = "a EY limitou as consultas"
ILEGIVEL = "não consegui ler as vagas da EY (a página pode ter mudado)"
VAGA = re.compile(r"^(?:https?://careers\.ey\.com)?/[A-Za-z0-9_-]+/job/[^/?#]+/(\d+)/?(?:[?#].*)?$", re.I)
PAISES = {"brazil": "Brazil", "usa": "United States", "uk": "United Kingdom"}  # o resto: inicial maiúscula
MESES = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                     "dec"), 1)}
REMOTO = re.compile(r"\b(?:remoto|remota|remote|home office|teletrabalho)\b")

_estado = {"bloqueado": False, "ultimo": None, "listas": {}, "pausa": None, "lidas": 0, "datas": None,
           "locais": {}}


def _esquecer() -> None:
    _estado.update(bloqueado=False, listas={}, pausa=None, lidas=0, datas=None, locais={})


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- pausa e bloqueio

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou EY_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN, faixa=PAUSA_FAIXA)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com EY_PAUSA definida (páginas de lista por cargo + páginas de vaga, no máximo)."""
    return _comum.aviso_pausa(PLATAFORMA, "na EY", VAR_PAUSA, pausa(),
                              consultas * MAX_PAGINAS + MAX_VAGAS if consultas else 0)


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    _comum.pausar(_estado, _estado["pausa"])


def parada() -> bool:
    """Bloqueou nesta busca (a EY não tem espera entre buscas)."""
    return _estado["bloqueado"]


def _bloquear(motivo: str) -> _comum.FonteErro:
    _estado["bloqueado"] = True
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); a busca seguiu sem ela")


def _baixar(url: str) -> str:
    return _comum.baixar_pagina(url, "a EY", _pausar, _bloquear)


# ---------------------------------------------------------------- memória de datas

def _datas() -> dict:
    """{número: {"data", "locais", "lida_em"}} das vagas já lidas; arquivo ausente ou ilegível vale como vazio."""
    if _estado["datas"] is None:
        try:
            dados = json.loads(ARQ_DATAS.read_text(encoding="utf-8"))
            _estado["datas"] = dados if isinstance(dados, dict) else {}
        except (OSError, ValueError):
            _estado["datas"] = {}
    return _estado["datas"]


def _gravar_datas() -> None:
    """Grava a memória sem as entradas lidas há mais de VALIDADE_DATAS; se não der para gravar, segue sem ela."""
    corte = (_agora() - VALIDADE_DATAS).date().isoformat()
    datas = {k: v for k, v in _datas().items() if isinstance(v, dict) and str(v.get("lida_em") or "") >= corte}
    _estado["datas"] = datas
    try:
        ARQ_DATAS.parent.mkdir(parents=True, exist_ok=True)
        ARQ_DATAS.write_text(json.dumps(datas, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- leitura das páginas

class _Linhas(HTMLParser):
    """As linhas da lista (tr.data-row): o primeiro a.jobTitle-link (link e título) e o span.jobLocation (o local
    principal; o "+N more" fica no small, fora do texto)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.linhas: list[dict] = []
        self.campo: str | None = None
        self.fechar: str | None = None
        self.no_small = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "tr" and "data-row" in classes:
            self.linhas.append({"href": "", "titulo": "", "local": "", "mais": False})
        if not self.linhas:
            return
        linha = self.linhas[-1]
        if tag == "a" and "jobTitle-link" in classes and not linha["href"]:
            linha["href"] = a.get("href") or ""
            self.campo, self.fechar = "titulo", "a"
        elif tag == "span" and "jobLocation" in classes:
            self.campo, self.fechar = "local", "span"
        elif tag == "small" and self.campo == "local":
            self.no_small, linha["mais"] = True, True

    def handle_endtag(self, tag):
        if tag == "small":
            self.no_small = False
        elif tag == self.fechar:
            self.campo = self.fechar = None

    def handle_data(self, data):
        if self.campo and self.linhas and not self.no_small:
            linha = self.linhas[-1]
            linha[self.campo] = (linha[self.campo] + " " + data).strip()


def _espacos(s) -> str:
    return " ".join(str(s or "").split())


def _local(cidade: str, uf: str, pais: str) -> str:
    """ "Cidade, UF" no Brasil; "Cidade, País" fora dele."""
    cidade, uf, pais = _espacos(cidade), _espacos(uf), _espacos(pais)
    fim = uf if pais.upper() in ("BR", "BRAZIL", "BRASIL", "") else pais
    return ", ".join(x for x in (cidade, fim) if x)


def _remoto(*textos) -> bool:
    return any(REMOTO.search(_comum._norm(t)) for t in textos)


def _tipo(titulo: str) -> str | None:
    t = _comum._norm(titulo)
    tipos = ["Banco de talentos"] if "banco de talentos" in t else []
    if re.search(r"\bpcd\b", t):
        tipos.append("Exclusiva para PCD" if "exclusiv" in t else "Vaga para PCD")
    return " • ".join(tipos) or None


def numero(url: str) -> str | None:
    m = VAGA.match(str(url or "").strip())
    return m.group(1) if m else None


def ler_lista(pagina: str) -> list[dict]:
    """As vagas de uma página de resultados, no formato comum, sem data e sem descrição. O local é o principal
    ("São Paulo JK, SP, BR, 04543-011" -> "São Paulo JK, SP")."""
    p = _Linhas()
    p.feed(pagina)
    p.close()
    vagas, vistos = [], set()
    for linha in p.linhas:
        n = numero(linha["href"])
        titulo = _espacos(linha["titulo"])
        if not n or n in vistos or not titulo:
            continue
        vistos.add(n)
        partes = [x.strip() for x in _espacos(linha["local"]).split(",")]
        local = _local(partes[0], partes[1] if len(partes) > 1 else "", partes[2] if len(partes) > 2 else "")
        remoto = _remoto(titulo, local)
        v = {
            "id": _comum.ident(NOME, n), "plataforma": PLATAFORMA, "titulo": titulo, "empresa": "EY",
            "local": "Remoto" if remoto and not local else local, "remoto": remoto, "publicada_em": None,
            "url": urljoin(SITE, linha["href"].strip()), "url_candidatura": None, "salario": None,
            "tipo": _tipo(titulo), "descricao": "",
        }
        if remoto:
            v["modelo_trabalho"] = "remoto"
        vagas.append(v)
    return vagas


def _data_postada(valor: str) -> str | None:
    """ "Thu Oct 22 00:00:00 UTC 2026" -> "2026-10-22" (sem depender do idioma do sistema); ISO também vale."""
    m = re.search(r"\b([A-Za-z]{3})[a-z]*\.? (\d{1,2})\b.*?\b(\d{4})\b", str(valor or ""))
    if m and m.group(1).lower() in MESES:
        try:
            return date(int(m.group(3)), MESES[m.group(1).lower()], int(m.group(2))).isoformat()
        except ValueError:
            return None
    return _comum.data_iso(valor)


def _interno(pagina: str, inicio: re.Match) -> str:
    """O HTML dentro do elemento aberto em `inicio` (até a marca que fecha a mesma tag, contando as aninhadas)."""
    tag, pos, nivel = inicio.group(1).lower(), inicio.end(), 1
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", pagina[pos:], re.I):
        nivel += -1 if m.group(1) else 1
        if nivel == 0:
            return pagina[pos:pos + m.start()]
    return pagina[pos:]


def _meta(trecho: str, prop: str) -> str:
    m = re.search(rf'<meta\b[^>]*\bitemprop="{prop}"[^>]*\bcontent="([^"]*)"', trecho, re.I)
    return html.unescape(m.group(1)).strip() if m else ""


def ler_pagina(pagina: str) -> dict:
    """A vaga pelos microdados schema.org da página: título, data, locais, descrição e tipo. Levanta link.LinkErro sem
    título."""
    m = re.search(r'<(\w+)\b[^>]*\bitemprop="title"[^>]*>', pagina, re.I)
    titulo = _espacos(link.texto_de_html(_interno(pagina, m))) if m else ""
    if not titulo:
        raise link.LinkErro("a página não traz os dados da vaga num formato que eu consiga ler")
    locais = []
    for end in re.findall(r'itemtype="https?://schema\.org/PostalAddress"[^>]*>(.*?)</span>', pagina, re.I | re.S):
        cidade, uf, pais = (_meta(end, p) for p in ("addressLocality", "addressRegion", "addressCountry"))
        if cidade and [cidade, uf] not in [x[:2] for x in locais]:
            locais.append([cidade, uf, pais])
    m = re.search(r'<(\w+)\b[^>]*\bdata-careersite-propertyid="city"[^>]*>', pagina, re.I)
    principal = _comum._norm(link.texto_de_html(_interno(pagina, m))) if m else ""
    locais.sort(key=lambda x: _comum._norm(x[0]) != principal)  # a "Localização primária" primeiro
    m = re.search(r'<(\w+)\b[^>]*\bitemprop="description"[^>]*>', pagina, re.I)
    descricao = link.texto_de_html(_interno(pagina, m)) if m else ""
    local = _local(*locais[0]) if locais else ""
    remoto = _remoto(titulo, local)
    vaga = {
        "plataforma": PLATAFORMA, "titulo": titulo, "empresa": _meta(pagina, "hiringOrganization") or "EY",
        "local": local or ("Remoto" if remoto else ""), "remoto": remoto,
        "publicada_em": _data_postada(_meta(pagina, "datePosted")), "tipo": _tipo(titulo),
        "descricao": descricao[:LIMITE_DESCRICAO], "locais": [x[:2] for x in locais],
    }
    if remoto:
        vaga["modelo_trabalho"] = "remoto"
    return vaga


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def _pais(pais) -> str | None:
    pais = str(pais or "").strip().lower()
    return PAISES.get(pais) or (pais.replace("-", " ").title() if pais else None)


def url_lista(termo: str, pais: str, inicio: int = 0) -> str:
    params = {"q": termo, "locationsearch": pais, "sortColumn": "referencedate", "sortDirection": "desc",
              **({"startrow": inicio} if inicio else {})}
    return f"{SITE}search/?{urlencode(params)}"


def _linhas(busca: str, pais: str) -> tuple[list[dict], str | None]:
    """As vagas das páginas da lista (sem data), sem repetir."""
    vagas: list[dict] = []
    for n in range(MAX_PAGINAS):
        inicio = n * POR_PAGINA
        try:
            pagina = _baixar(url_lista(busca, pais, inicio))
        except _comum.FonteErro as e:
            return vagas, str(e)
        achadas = ler_lista(pagina)
        if not achadas:
            return vagas, ILEGIVEL if n == 0 and "data-row" in pagina else None
        ids = {v["id"] for v in vagas}
        vagas += [v for v in achadas if v["id"] not in ids]
        if len(achadas) < POR_PAGINA or f"startrow={inicio + POR_PAGINA}" not in pagina:
            break
    return vagas, None


def _completar(v: dict) -> bool | None:
    """Data, locais e descrição da vaga, pela memória ou pela página. True: completa; None: ficou sem página (limite
    da busca ou bloqueio anterior); False: erro só desta vaga. O bloqueio nesta página sobe como FonteErro."""
    n = numero(v["url"])
    lembrada = _datas().get(n)
    if isinstance(lembrada, dict):
        v["publicada_em"] = lembrada.get("data")
        _estado["locais"][v["id"]] = [list(x)[:2] for x in lembrada.get("locais") or []]
        return True
    if _estado["bloqueado"] or _estado["lidas"] >= MAX_VAGAS:
        return None
    _estado["lidas"] += 1
    try:
        lida = ler_pagina(_baixar(v["url"]))
    except link.LinkErro:
        return False
    except _comum.FonteErro:
        if _estado["bloqueado"]:
            raise
        return False
    v.update(publicada_em=lida["publicada_em"], descricao=lida["descricao"])
    if lida["local"]:
        v["local"] = lida["local"] if not v["local"] or v["local"] == "Remoto" else v["local"]
    _estado["locais"][v["id"]] = lida["locais"]
    _datas()[n] = {"data": lida["publicada_em"], "locais": lida["locais"], "lida_em": _agora().date().isoformat()}
    return True


def _lista(termo: str, pais: str, horas: int) -> tuple[list[dict], str | None]:
    """As vagas do cargo que batem com o título, com data e locais, guardadas para as outras consultas do cargo."""
    chave = (termo, pais)
    if chave in _estado["listas"]:
        return _estado["listas"][chave]
    busca = " ".join(termo.replace('"', " ").split())
    linhas, erro = _linhas(busca, pais)
    limite = _limite(horas)
    vagas, mudou = [], False
    for v in linhas:
        if not _comum.bate_cargo(v["titulo"], termo):
            continue
        lida_agora = numero(v["url"]) not in _datas()
        try:
            feito = _completar(v)
        except _comum.FonteErro as e:  # bloqueio: as vagas já completas seguem
            erro = erro or str(e)
            break
        mudou = mudou or bool(feito and lida_agora)
        if feito is None:
            break  # sem a página, não dá para saber a data; a vaga fica para uma busca seguinte
        if not feito:
            continue  # a página da vaga deu erro (ex.: vaga encerrada)
        if v.get("publicada_em") and v["publicada_em"] < limite:
            if ORDEM_POR_DATA:
                break  # as seguintes são mais antigas
            continue
        vagas.append(v)
    if mudou:
        _gravar_datas()
    _estado["listas"][chave] = (vagas, erro)
    return vagas, erro


def _atende(vaga: dict, consulta: dict) -> bool:
    if consulta.get("remoto"):
        return vaga["remoto"]
    if consulta.get("cidade"):
        locais = _estado["locais"].get(vaga["id"]) or [str(vaga.get("local") or "").rsplit(", ", 1)]
        return not vaga["remoto"] and any(_comum.na_regiao(c[0], c[1] if len(c) > 1 else "", consulta)
                                          for c in locais if c)
    modelos = consulta.get("modelos") or []
    return not (vaga["remoto"] and modelos and "remoto" not in modelos)


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    pais = _pais(consulta.get("pais"))
    termo = " ".join(str(consulta.get("termo") or "").split())
    if not pais or not termo.replace('"', "").strip():
        return [], []
    ja_lida = (termo, pais) in _estado["listas"]
    if _estado["bloqueado"] and not ja_lida:
        return [], []  # depois de um bloqueio, nenhum pedido a mais (a lista já lida continua valendo)
    vagas, erro = _lista(termo, pais, horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []


def descrever(vaga: dict) -> str:
    """A descrição lida na busca, sem pedido; sem ela, a página da vaga (conta em MAX_VAGAS). Depois de um bloqueio
    ou no limite, devolve o que a vaga já tinha."""
    if vaga.get("descricao"):
        return vaga["descricao"]
    if parada() or _estado["lidas"] >= MAX_VAGAS:
        return ""
    if not numero(vaga.get("url")):
        raise _comum.FonteErro("link de vaga da EY inesperado")
    _estado["lidas"] += 1
    return ler_pagina(_baixar(str(vaga["url"])))["descricao"]


def id_do_link(url: str) -> str | None:
    """O id da vaga ("ey-1234567") a partir do link da página da vaga; None para outros links."""
    url = str(url or "").strip()
    n = numero(url)
    return _comum.ident(NOME, n) if n and url.lower().startswith(("http://", "https://")) else None
