"""Lê uma vaga a partir do link (botão Adicionar Vaga do dashboard).

- Indeed: a página bloqueia leitura automática, então usa a API do app do Indeed pelo
  código da vaga (jk), com os cabeçalhos do python-jobspy.
- LinkedIn: a API pública de visitante (sem login), pelo número da vaga.
- Gupy: o MCP público de candidatos da Gupy (fontes/gupy.py), pelo número da vaga; se
  ele falhar, os dados estruturados da página, como nos outros sites.
- startup.jobs: o MCP público do site (fontes/startupjobs.py), pelo número da vaga; se
  ele falhar, os dados estruturados da página.
- Greenhouse, Lever e Ashby: a API pública de vagas da empresa (fontes/ats.py), pelo
  número da vaga, com o link de candidatura e a restrição de local; se ela falhar, os
  dados estruturados da página.
- Outros sites (InHire, Remotive, Himalayas, Remote OK, Jobicy, We Work Remotely, Get on
  Board, páginas de empresa): os dados estruturados de vaga da página (schema.org
  JobPosting, o formato que o Google usa).

Se não der para ler, levanta LinkErro com o que conseguiu (o dashboard abre o
formulário para o usuário completar). Só abre endereços públicos da internet.
"""
from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from . import _comum, ats, gupy, startupjobs

NL = chr(10)
LIMITE_BYTES = 3_000_000
TEMPO = 20
NAVEGADOR = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
VAZIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCOS = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article"}


class LinkErro(Exception):
    """Não deu para ler a vaga; `parcial` traz o que deu, para pré-preencher o formulário."""

    def __init__(self, motivo: str, parcial: dict | None = None):
        super().__init__(motivo)
        self.parcial = parcial or {}


def plataforma(host: str) -> str:
    host = (host or "").lower()
    for chave, nome in (("indeed.", "Indeed"), ("linkedin.", "LinkedIn"), ("gupy.io", "Gupy"),
                        ("inhire", "InHire"), ("catho.", "Catho"), ("startup.jobs", "Startup Jobs"),
                        ("remotive.", "Remotive"), ("himalayas.app", "Himalayas"), ("remoteok.", "RemoteOK"),
                        ("jobicy.", "Jobicy"), ("weworkremotely.", "We Work Remotely"), ("getonbrd.", "Get on Board"),
                        ("getonboard.", "Get on Board"), ("greenhouse.io", "Greenhouse"), ("lever.co", "Lever"),
                        ("ashbyhq.com", "Ashby")):
        if chave in host:
            return nome
    return "Outra"


# ---------------------------------------------------------------- rede

def _host_publico(host: str) -> bool:
    """Evita que o link aponte para a rede local ou para o próprio computador."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return bool(infos)


class _SoPublico(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        partes = urlsplit(newurl)
        if partes.scheme not in ("http", "https") or not _host_publico(partes.hostname or ""):
            raise LinkErro("o link redireciona para um endereço que não é público")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _baixar(url: str, dados: bytes | None = None, cabecalhos: dict | None = None) -> str:
    partes = urlsplit(url)
    if partes.scheme not in ("http", "https") or not partes.hostname or not _host_publico(partes.hostname):
        raise LinkErro("link inválido ou de um endereço que não é público")
    req = urllib.request.Request(url, data=dados, headers={
        "User-Agent": NAVEGADOR, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8", **(cabecalhos or {})})
    try:
        with urllib.request.build_opener(_SoPublico).open(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            charset = r.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        raise LinkErro(f"o site respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LinkErro(f"não consegui abrir o link ({getattr(e, 'reason', e)})") from None
    if len(corpo) > LIMITE_BYTES:
        raise LinkErro("página grande demais")
    return corpo.decode(charset, errors="replace")


# ---------------------------------------------------------------- HTML

class _Texto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.partes.append(NL + "- ")
        elif tag == "br" or tag in BLOCOS:
            self.partes.append(NL)

    def handle_endtag(self, tag):
        if tag in BLOCOS and tag != "li":  # o próximo <li> já começa linha nova
            self.partes.append(NL)

    def handle_data(self, data):
        self.partes.append(data)


def texto_de_html(trecho: str) -> str:
    """Texto legível de um trecho HTML: uma linha por bloco, '- ' nos itens de lista."""
    if "&lt;" in (trecho or "") and "<" not in trecho:
        trecho = html.unescape(trecho)  # HTML que veio escapado dentro do JSON
    p = _Texto()
    p.feed(trecho or "")
    p.close()
    saida, vazia = [], True
    for linha in "".join(p.partes).split(NL):
        linha = " ".join(linha.split())
        if linha in ("", "-"):
            if not vazia:
                saida.append("")
            vazia = True
        else:
            saida.append(linha)
            vazia = False
    return NL.join(saida).strip()


class _Classes(HTMLParser):
    """HTML interno dos elementos que têm certas classes CSS."""

    def __init__(self, classes):
        super().__init__(convert_charrefs=True)
        self.achados = {c: [] for c in classes}
        self._classes, self._pilha, self._prof = classes, [], 0

    def handle_starttag(self, tag, attrs):
        for _, _, partes in self._pilha:
            partes.append(self.get_starttag_text() or "")
        if tag in VAZIOS:
            return
        self._prof += 1
        minhas = (dict(attrs).get("class") or "").split()
        for c in self._classes:
            if c in minhas:
                self._pilha.append((c, self._prof, []))

    def handle_endtag(self, tag):
        if tag in VAZIOS:
            return
        for _, _, partes in self._pilha:
            partes.append(f"</{tag}>")
        for item in [p for p in self._pilha if p[1] == self._prof]:
            self._pilha.remove(item)
            self.achados[item[0]].append("".join(item[2]))
        self._prof -= 1

    def handle_data(self, data):
        for _, _, partes in self._pilha:
            partes.append(html.escape(data, quote=False))


class _Dados(HTMLParser):
    """Blocos <script type="application/ld+json"> e metas og: da página."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.jsonld: list[str] = []
        self.meta: dict[str, str] = {}
        self._dentro = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._dentro = True
            self.jsonld.append("")
        elif tag == "meta" and (a.get("property") or a.get("name")):
            self.meta[(a.get("property") or a.get("name")).lower()] = a.get("content") or ""

    def handle_endtag(self, tag):
        if tag == "script":
            self._dentro = False

    def handle_data(self, data):
        if self._dentro:
            self.jsonld[-1] += data


def _data(v) -> str | None:
    try:
        return datetime.fromisoformat(str(v)[:10]).date().isoformat()
    except ValueError:
        return None


# ---------------------------------------------------------------- portais

def _ler_indeed(partes) -> dict:
    q = parse_qs(partes.query)
    jk = (q.get("jk") or q.get("vjk") or [""])[0].lower()
    if not jk or any(c not in "0123456789abcdef" for c in jk):
        raise LinkErro("não achei o código da vaga (jk=…) no link do Indeed")
    sub = (partes.hostname or "").lower().split(".")[0]
    pais = {"www": "US", "indeed": "US", "uk": "GB"}.get(sub, sub.upper())
    try:
        from jobspy.indeed.constant import api_headers
    except ImportError:
        raise LinkErro("falta a biblioteca python-jobspy para ler links do Indeed") from None
    consulta = ('{ jobData(jobKeys: ["%s"]) { results { job { key title datePublished description { html } '
                'location { formatted { long } } employer { name } attributes { key label } } } } }') % jk
    resposta = _baixar("https://apis.indeed.com/graphql", json.dumps({"query": consulta}).encode("utf-8"),
                       {**api_headers, "indeed-co": pais, "content-type": "application/json"})
    try:
        job = json.loads(resposta)["data"]["jobData"]["results"][0]["job"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise LinkErro("o Indeed não devolveu essa vaga (ela pode ter saído do ar)") from None
    local = ((job.get("location") or {}).get("formatted") or {}).get("long") or ""
    attrs = job.get("attributes") or []
    remoto = "remot" in local.lower() or any(
        a.get("key") == "DSQF7" or "remot" in (a.get("label") or "").lower() for a in attrs)
    pub = job.get("datePublished")
    return {
        "id": jk, "plataforma": "Indeed", "titulo": job.get("title") or "",
        "empresa": (job.get("employer") or {}).get("name") or "Empresa não informada",
        "local": local, "remoto": remoto,
        "publicada_em": datetime.fromtimestamp(pub / 1000, timezone.utc).date().isoformat()
        if isinstance(pub, (int, float)) else None,
        "url": f"https://{partes.hostname}/viewjob?jk={jk}", "tipo": None,
        "descricao": texto_de_html((job.get("description") or {}).get("html") or ""),
    }


def _ler_linkedin(partes) -> dict:
    q = parse_qs(partes.query)
    vid = (q.get("currentJobId") or [""])[0] or partes.path.rstrip("/").split("/")[-1].split("-")[-1]
    if not vid.isdigit():
        raise LinkErro("não achei o número da vaga no link do LinkedIn")
    pagina = _baixar(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{vid}")
    classes = ("top-card-layout__title", "topcard__org-name-link", "topcard__flavor--bullet",
               "show-more-less-html__markup", "description__job-criteria-subheader", "description__job-criteria-text")
    p = _Classes(classes)
    p.feed(pagina)
    p.close()
    t = {c: [texto_de_html(x) for x in p.achados[c]] for c in classes}
    primeiro = lambda c: t[c][0] if t[c] else ""
    criterios = [f"{a}: {b}" for a, b in zip(t["description__job-criteria-subheader"], t["description__job-criteria-text"])]
    descricao = primeiro("show-more-less-html__markup")
    if criterios:
        descricao = (descricao + NL + NL + NL.join(criterios)).strip()
    local = primeiro("topcard__flavor--bullet")
    tipo = next((b for a, b in zip(t["description__job-criteria-subheader"], t["description__job-criteria-text"])
                 if "emprego" in a.lower() or "employment" in a.lower()), None)
    return {
        "id": f"li-{vid}", "plataforma": "LinkedIn", "titulo": primeiro("top-card-layout__title"),
        "empresa": primeiro("topcard__org-name-link"), "local": local, "remoto": "remot" in local.lower(),
        "publicada_em": None, "url": f"https://www.linkedin.com/jobs/view/{vid}/", "tipo": tipo, "descricao": descricao,
    }


def _ler_gupy(url: str, vid: str) -> dict:
    try:
        vaga = gupy.ler(vid)
    except gupy.GupyErro:
        vaga = extrair_jobposting(_baixar(url), "Gupy")
    return {**vaga, "id": vid, "url": url}


def _ler_startupjobs(url: str, vid: str) -> dict:
    try:
        vaga = startupjobs.ler(vid)
    except startupjobs.StartupJobsErro:
        vaga = extrair_jobposting(_baixar(url), "Startup Jobs")
    return {**vaga, "id": vid, "url": url}


def _ler_ats(url: str, plat: str) -> dict:
    try:
        vaga = ats.ler(url)
    except _comum.FonteErro:
        vaga = extrair_jobposting(_baixar(url), plat)
        empresa, vid = ats.vaga_do_link(url)
        vaga.update(id=_comum.ident(empresa["sistema"], f"{empresa['id']}-{vid}"), ats=empresa["sistema"])
    return {**vaga, "url": url}


def _achar_vaga(obj):
    if isinstance(obj, list):
        for x in obj:
            achada = _achar_vaga(x)
            if achada:
                return achada
    elif isinstance(obj, dict):
        tipo = obj.get("@type")
        if tipo == "JobPosting" or (isinstance(tipo, list) and "JobPosting" in tipo):
            return obj
        for k in ("@graph", "mainEntity", "itemListElement"):
            if k in obj:
                achada = _achar_vaga(obj[k])
                if achada:
                    return achada
    return None


def extrair_jobposting(pagina: str, plat: str) -> dict:
    """Vaga a partir dos dados estruturados (JobPosting) de uma página HTML."""
    p = _Dados()
    p.feed(pagina)
    p.close()
    vaga = None
    for bloco in p.jsonld:
        try:
            vaga = _achar_vaga(json.loads(bloco.strip()))
        except ValueError:
            continue
        if vaga:
            break
    if not vaga:
        raise LinkErro("a página não traz os dados da vaga num formato que eu consiga ler",
                       {"titulo": p.meta.get("og:title", ""), "descricao": p.meta.get("og:description", "")})
    org = vaga.get("hiringOrganization")
    empresa = org.get("name") if isinstance(org, dict) else org if isinstance(org, str) else ""
    locais = vaga.get("jobLocation")
    locais = locais if isinstance(locais, list) else [locais] if locais else []
    partes = []
    for loc in locais:
        end = loc.get("address") if isinstance(loc, dict) else None
        if isinstance(end, dict):
            pais = end.get("addressCountry")
            pais = pais.get("name") if isinstance(pais, dict) else pais
            partes.append(", ".join(str(x) for x in (end.get("addressLocality"), end.get("addressRegion"), pais) if x))
    remoto = "TELECOMMUTE" in str(vaga.get("jobLocationType") or "").upper()
    tipo = vaga.get("employmentType")
    return {
        "plataforma": plat, "titulo": html.unescape(str(vaga.get("title") or "")).strip(),
        "empresa": html.unescape(str(empresa or "")).strip(),
        "local": "; ".join(x for x in partes if x) or ("Remoto" if remoto else ""), "remoto": remoto,
        "publicada_em": _data(vaga.get("datePosted")),
        "tipo": ", ".join(map(str, tipo)) if isinstance(tipo, list) else (str(tipo) if tipo else None),
        "descricao": texto_de_html(str(vaga.get("description") or "")),
    }


def ler(url: str) -> dict:
    """Dados da vaga no formato do banco (id, plataforma, titulo, empresa, local, remoto,
    publicada_em, url, tipo, descricao). Levanta LinkErro se não conseguir."""
    url = (url or "").strip()
    partes = urlsplit(url)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        raise LinkErro("o link precisa começar com http:// ou https://")
    plat = plataforma(partes.hostname)
    if plat == "Indeed":
        vaga = _ler_indeed(partes)
    elif plat == "LinkedIn":
        vaga = _ler_linkedin(partes)
    elif plat == "Gupy" and gupy.id_do_link(url):
        vaga = _ler_gupy(url, gupy.id_do_link(url))
    elif plat == "Startup Jobs" and startupjobs.id_do_link(url):
        vaga = _ler_startupjobs(url, startupjobs.id_do_link(url))
    elif plat in ("Greenhouse", "Lever", "Ashby") and ats.vaga_do_link(url):
        vaga = _ler_ats(url, plat)
    else:
        vaga = extrair_jobposting(_baixar(url), plat)
        vaga["id"] = "web-" + hashlib.sha1((partes.netloc + partes.path).lower().encode("utf-8")).hexdigest()[:16]
        vaga["url"] = url
    if not vaga.get("titulo") or not vaga.get("empresa"):
        raise LinkErro("não consegui ler o cargo e a empresa da vaga", vaga)
    return vaga
