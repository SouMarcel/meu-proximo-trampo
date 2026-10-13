"""Fonte LinkedIn: a busca pública de vagas (a mesma que aparece para quem não entrou na conta), sem login e sem a
conta, as senhas ou os cookies da pessoa.

Cada consulta de filtros.consultas vira uma busca com o local (país, cidade com raio ou "Worldwide") e o modelo de
trabalho do grupo; a janela de tempo e os tipos de emprego vão como filtro do próprio LinkedIn. A descrição vem da
página pública da vaga, só para as vagas que vão para o relatório. Pausa de 3 a 7 segundos entre os pedidos e, no
primeiro bloqueio (limite de consultas ou pedido de login), o LinkedIn fica de fora pelo resto da busca, sem nova
tentativa (constituição, princípio VI).
"""
from __future__ import annotations

import random
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlencode

from . import _comum, link

NOME = "linkedin"
PLATAFORMA = "LinkedIn"
AREAS = ("nacional", "internacional")
POR_PAIS = True
GLOBAL = True  # também na consulta "mundo todo" (Worldwide)
TERMOS = ("Consulta não oficial à busca pública do LinkedIn, sem login e sem a sua conta. Há uma pausa de alguns "
          "segundos entre as consultas e, se o LinkedIn limitar, a busca segue sem ele (tente mais tarde). "
          "A candidatura é sempre no próprio LinkedIn.")

BUSCA = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
VAGA = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
PAUSA = (3.0, 7.0)
POR_PAGINA = 10  # o que a busca pública devolve por página
MAX_PAGINAS = 1  # uma página por consulta: poucas consultas, menos risco de bloqueio
TEMPO = 20
LIMITE_BYTES = 3_000_000
LIMITE_DESCRICAO = 12000
BLOQUEIO = "o LinkedIn limitou as consultas; tente mais tarde"
ILEGIVEL = "não consegui ler as vagas do LinkedIn (a página pode ter mudado)"
WT = {"presencial": "1", "remoto": "2", "hibrido": "3"}
JT = {"tempo_integral": "F", "pj": "C", "meio_periodo": "P", "estagio": "I", "temporario": "T"}
# nome do país no LinkedIn quando o do jobspy (filtros.PAISES) não serve com a primeira letra maiúscula
PAIS_EN = {"usa": "United States", "uk": "United Kingdom", "türkiye": "Turkey", "czech republic": "Czechia",
           "uae": "United Arab Emirates", "united arab emirates": "United Arab Emirates", "hong kong": "Hong Kong SAR"}
TIPOS = [("tempo_integral", ("full-time", "full time", "tempo integral")),
         ("pj", ("contract", "contrato", "freelance", "autônomo", "autonomo")),
         ("meio_periodo", ("part-time", "part time", "meio período", "meio periodo")),
         ("estagio", ("internship", "estágio", "estagio")),
         ("temporario", ("temporary", "temporário", "temporario"))]

_estado = {"bloqueado": False, "ultimo": None}


def _esquecer() -> None:
    _estado.update(bloqueado=False)


_comum.AO_ESQUECER.append(_esquecer)


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Redirecionamento (para login, cadastro, verificação) não é seguido: vira erro e conta como bloqueio."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _pausar() -> None:
    if _estado["ultimo"] is not None:
        espera = _estado["ultimo"] + random.uniform(*PAUSA) - time.monotonic()
        if espera > 0:
            time.sleep(espera)
    _estado["ultimo"] = time.monotonic()


def _bloquear() -> _comum.FonteErro:
    _estado["bloqueado"] = True
    return _comum.FonteErro(BLOQUEIO)


def _baixar(url: str) -> str:
    """Um pedido ao LinkedIn: sem cookies, sem seguir redirecionamento e sem nova tentativa."""
    _pausar()
    req = urllib.request.Request(url, headers={"User-Agent": link.NAVEGADOR, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    try:
        with urllib.request.build_opener(_SemRedirecionar).open(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            charset = r.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        if e.code in (429, 999, 401, 403) or 300 <= e.code < 400:
            raise _bloquear() from None
        raise _comum.FonteErro(f"o LinkedIn respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise _comum.FonteErro(f"não consegui falar com o LinkedIn ({getattr(e, 'reason', e)})") from None
    if len(corpo) > LIMITE_BYTES:
        raise _comum.FonteErro("resposta grande demais do LinkedIn")
    return corpo.decode(charset, errors="replace")


# ---------------------------------------------------------------- consulta

def _pais(consulta: dict) -> str:
    p = str(consulta.get("pais") or "")
    return PAIS_EN.get(p, " ".join(w.capitalize() for w in p.split()))


def parametros(consulta: dict, horas: int | None) -> dict:
    """Os filtros da busca do LinkedIn para uma consulta de filtros.consultas."""
    if consulta.get("global"):
        local = "Worldwide"
    elif consulta.get("local"):
        local = f"{consulta['local']}, {_pais(consulta)}".strip(", ")
    else:
        local = _pais(consulta)
    modelos = consulta.get("modelos") or (["remoto"] if consulta.get("remoto") else [])
    p = {"keywords": str(consulta["termo"]).strip('"'), "location": local}
    if consulta.get("local") and consulta.get("raio_km"):
        p["distance"] = max(1, round(consulta["raio_km"] / 1.609))  # o LinkedIn mede o raio em milhas
    if modelos:
        p["f_WT"] = ",".join(WT[m] for m in ("presencial", "remoto", "hibrido") if m in modelos)
    tipos = [JT[t] for t in JT if t in (consulta.get("tipos_emprego") or [])]
    if tipos:
        p["f_JT"] = ",".join(tipos)
    if horas:
        p["f_TPR"] = f"r{int(horas) * 3600}"
    return p


def tipo_emprego(texto: str) -> list[str]:
    """O "Employment type" do LinkedIn (em inglês ou português) nos códigos de filtros.TIPOS_EMPREGO."""
    t = str(texto or "").lower()
    return [codigo for codigo, nomes in TIPOS if any(n in t for n in nomes)]


# ---------------------------------------------------------------- leitura dos cards

class _Cards(HTMLParser):
    CAMPOS = {"base-search-card__title": "titulo", "base-search-card__subtitle": "empresa",
              "job-search-card__location": "local"}
    VAZIOS = link.VAZIOS

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.pilha: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        urn = a.get("data-entity-urn") or ""
        if "jobPosting" in urn or "base-search-card" in classes:  # começo de um card
            m = re.search(r"jobPosting:(\d+)", urn)
            numero = m.group(1) if m else None
            ultimo = self.cards[-1] if self.cards else None
            if ultimo is not None and not ultimo.get("titulo") and (numero is None or ultimo.get("numero") in (None, numero)):
                ultimo["numero"] = ultimo.get("numero") or numero  # o mesmo card (urn e classe em elementos aninhados)
            else:
                self.cards.append({"numero": numero})
        if not self.cards:
            return
        card = self.cards[-1]
        if tag == "a" and not card.get("numero"):  # card sem o urn: o número vem do link da vaga
            m = re.search(r"/jobs/view/(?:[^/?]*-)?(\d+)", a.get("href") or "")
            if m:
                card["numero"] = m.group(1)
        if tag == "time" and a.get("datetime"):
            card["publicada_em"] = a["datetime"][:10]
        if tag in self.VAZIOS:
            return
        campo = next((self.CAMPOS[c] for c in classes if c in self.CAMPOS), None)
        self.pilha.append((tag, campo))

    def handle_endtag(self, tag):
        if any(t == tag for t, _ in self.pilha):
            while self.pilha and self.pilha.pop()[0] != tag:
                pass

    def handle_data(self, data):
        if not self.cards:
            return
        for _, campo in self.pilha:
            if campo:
                card = self.cards[-1]
                card[campo] = (card.get(campo, "") + " " + data).strip()


def ler_lista(pagina: str) -> list[dict]:
    """As vagas de uma página de resultados (o trecho de HTML que a busca pública devolve)."""
    p = _Cards()
    p.feed(pagina)
    p.close()
    vagas, vistos = [], set()
    for c in p.cards:
        n = c.get("numero")
        if not n or n in vistos or not c.get("titulo"):
            continue
        vistos.add(n)
        local = " ".join((c.get("local") or "").split())
        vagas.append({
            "id": f"li-{n}", "plataforma": PLATAFORMA, "titulo": " ".join(c["titulo"].split()),
            "empresa": " ".join((c.get("empresa") or "").split()) or "Empresa não informada", "local": local,
            "remoto": bool(re.search(r"remot", local, re.I)), "publicada_em": c.get("publicada_em"),
            "url": f"https://www.linkedin.com/jobs/view/{n}/", "url_candidatura": None, "salario": None, "tipo": None,
            "descricao": "",
        })
    return vagas


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if _estado["bloqueado"]:
        return [], []  # o aviso já saiu nesta busca; nenhum pedido a mais
    params = parametros(consulta, horas)
    modelos = consulta.get("modelos") or []
    vagas: list[dict] = []
    inicio = 0
    for _ in range(MAX_PAGINAS):
        if len(vagas) >= max(1, por_termo):
            break
        try:
            pagina = _baixar(f"{BUSCA}?{urlencode({**params, 'start': inicio})}")
        except _comum.FonteErro as e:
            return vagas, [str(e)]
        achadas = ler_lista(pagina)
        if not achadas:
            if pagina.strip() and inicio == 0 and "<li" in pagina:
                return vagas, [ILEGIVEL]
            break
        vagas += [v for v in achadas if v["id"] not in {x["id"] for x in vagas}]
        if len(achadas) < POR_PAGINA:
            break
        inicio += len(achadas)
    for v in vagas:
        if len(modelos) == 1:  # a consulta pediu um modelo só: o LinkedIn já filtrou
            v["modelo_trabalho"] = modelos[0]
            v["remoto"] = modelos[0] == "remoto"
    return vagas[:max(1, por_termo)], []


def descrever(vaga: dict) -> str:
    """A descrição da página pública da vaga (com os critérios: tipo de emprego, nível). Também preenche
    vaga["tipo_emprego"]. Depois de um bloqueio, devolve o que a vaga já tinha, sem pedido."""
    if _estado["bloqueado"]:
        return vaga.get("descricao") or ""
    numero = str(vaga["id"]).removeprefix("li-")
    lida = link.vaga_linkedin(numero, _baixar(VAGA.format(numero)))
    tipos = tipo_emprego(lida.get("tipo") or "")
    if tipos:
        vaga["tipo_emprego"] = tipos
    return (lida.get("descricao") or vaga.get("descricao") or "")[:LIMITE_DESCRICAO]
