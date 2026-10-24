"""Fonte Nerdin: a busca pública do portal brasileiro de vagas de tecnologia (nerdin.com.br), sem login e sem a
conta, as senhas ou os cookies da pessoa.

A lista de cada cargo (vagas.php?busca=<cargo>) é lida uma vez por busca, da vaga mais nova para a mais antiga, até
MAX_PAGINAS páginas ou a primeira vaga fora da janela, e serve às consultas do mesmo cargo (remoto, país e cidade),
que filtram pelo título, pelo modelo de trabalho e pela cidade ou estado. A busca do site é ampla (traz vagas que só
citam o cargo no texto), então fica só a vaga cujo título bate com o cargo. A descrição vem da página da vaga (os
dados estruturados JobPosting), só das vagas que vão para o relatório, no máximo MAX_DESCRICOES por busca. Pausa de
PAUSA segundos entre os pedidos (NERDIN_PAUSA=N no .env muda para N, com N de 3 a 60; spec 026) e, no primeiro
bloqueio, a Nerdin fica de fora pelo resto da busca, sem nova tentativa (constituição, princípio VI).
"""
from __future__ import annotations

import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin

from . import _comum, link

NOME = "nerdin"
PLATAFORMA = "Nerdin"
AREAS = ("nacional",)  # só vagas do Brasil
TERMOS = ("Consulta não oficial à busca pública da Nerdin, portal só de vagas de tecnologia no Brasil, sem login. "
          "Há uma pausa de alguns segundos entre as consultas e, se a Nerdin limitar, a busca segue sem ela. "
          "A candidatura é sempre na própria Nerdin.")

SITE = "https://www.nerdin.com.br/"
LISTA = SITE + "vagas.php"
POR_PAGINA = 20  # o que a lista mostra por página
MAX_PAGINAS = 5  # por cargo; a janela de tempo costuma parar antes
MAX_DESCRICOES = 30  # páginas de vaga lidas por busca; as outras ficam pendentes para a próxima
PAUSA = 3.0  # segundos entre os pedidos à Nerdin, sem NERDIN_PAUSA
VAR_PAUSA = "NERDIN_PAUSA"  # no .env ou no ambiente: segundos de pausa (spec 026)
PAUSA_MIN = 3.0
TEMPO = 20
LIMITE_BYTES = 3_000_000
LIMITE_DESCRICAO = 12000
BLOQUEIOS = (403, 429, 503)
BLOQUEIO = "a Nerdin limitou as consultas"
ILEGIVEL = "não consegui ler as vagas da Nerdin (a página pode ter mudado)"
VAGA = re.compile(r"^(?:https?://(?:www\.)?nerdin\.com\.br/)?vaga_emprego/vaga-[^/?#]*?-(\d+)\.php(?:[?#].*)?$", re.I)
MODELOS = (("home office", "remoto"), ("remoto", "remoto"), ("hibrido", "hibrido"), ("presencial", "presencial"))
TIPOS = (("clt", "tempo_integral"), ("pj", "pj"), ("freelancer", "pj"), ("estagio", "estagio"),
         ("temporario", "temporario"))
UFS = _comum.UFS

_estado = {"bloqueado": False, "ultimo": None, "listas": {}, "pausa": None}


def _esquecer() -> None:
    _estado.update(bloqueado=False, listas={}, pausa=None)  # a pausa é lida de novo a cada busca


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def pausa() -> dict:
    """A pausa entre os pedidos à Nerdin: PAUSA, ou NERDIN_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, (PAUSA, PAUSA), PAUSA_MIN)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com NERDIN_PAUSA definida (páginas de lista por cargo + descrições, no máximo)."""
    pedidos = consultas * MAX_PAGINAS + MAX_DESCRICOES if consultas else 0
    return _comum.aviso_pausa(PLATAFORMA, "na Nerdin", VAR_PAUSA, pausa(), pedidos)


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    _comum.pausar(_estado, _estado["pausa"])


def parada() -> bool:
    """Bloqueou nesta busca: a vaga sem texto fica pendente."""
    return _estado["bloqueado"]


def _bloquear(motivo: str) -> _comum.FonteErro:
    _estado["bloqueado"] = True
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); a busca seguiu sem ela")


def _baixar(url: str) -> str:
    """Um pedido à Nerdin: sem cookies e sem nova tentativa; recusa, limite ou pedido de login param a fonte."""
    _pausar()
    req = urllib.request.Request(url, headers={"User-Agent": _comum.AGENTE, "Accept": "text/html",
                                               "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            charset = r.headers.get_content_charset() or "utf-8"
            final = r.geturl() or url
    except urllib.error.HTTPError as e:
        if e.code in BLOQUEIOS:
            raise _bloquear(f"código {e.code}") from None
        raise _comum.FonteErro(f"a Nerdin respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise _comum.FonteErro(f"não consegui falar com a Nerdin ({getattr(e, 'reason', e)})") from None
    if "login" in final.lower():
        raise _bloquear("pediu login")
    if len(corpo) > LIMITE_BYTES:
        raise _comum.FonteErro("resposta grande demais da Nerdin")
    return corpo.decode(charset, errors="replace")


# ---------------------------------------------------------------- leitura dos cards

class _Cards(HTMLParser):
    CAMPOS = {"vaga-titulo": "titulo", "vaga-resumo-linha": "resumo", "vaga-salario-destaque": "salario",
              "vaga-empresa-nome": "empresa", "vaga-local-linha": "local", "vaga-nova-badge": None}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.pilha: list[tuple[str, str | None, bool]] = []  # (tag, campo, ignorar o texto)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "div" and "vaga-card" in classes:
            self.cards.append({"href": a.get("data-href") or ""})
        if not self.cards:
            return
        card = self.cards[-1]
        if tag == "time" and a.get("datetime"):
            card["data"] = a["datetime"]
        if tag in link.VAZIOS:
            return
        achada = next((c for c in classes if c in self.CAMPOS), None)
        self.pilha.append((tag, self.CAMPOS.get(achada), achada == "vaga-nova-badge"))

    def handle_endtag(self, tag):
        if any(t == tag for t, _, _ in self.pilha):
            while self.pilha and self.pilha.pop()[0] != tag:
                pass

    def handle_data(self, data):
        if not self.cards:
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


def _partes(s: str) -> list[str]:
    return [p.strip() for p in s.split("•") if p.strip()]


def ler_lista(pagina: str) -> list[dict]:
    """As vagas de uma página de resultados, no formato comum (sem a descrição)."""
    p = _Cards()
    p.feed(pagina)
    p.close()
    vagas, vistos = [], set()
    for c in p.cards:
        m = VAGA.match(c["href"].strip())
        titulo = _espacos(c.get("titulo"))
        if not m or m.group(1) in vistos or not titulo:
            continue
        vistos.add(m.group(1))
        resumo = _espacos(c.get("resumo"))
        chaves = {_comum._norm(x) for x in _partes(resumo)}
        local = _espacos(c.get("local"))
        home_office = _comum._norm(local) == "home office"
        modelo = next((m_ for k, m_ in MODELOS if k in chaves), "remoto" if home_office else None)
        tipos = []
        for chave, tipo in TIPOS:
            if chave in chaves and tipo not in tipos:
                tipos.append(tipo)
        salario = _espacos(c.get("salario"))
        data = str(c.get("data") or "")[:10]
        v = {
            "id": _comum.ident(NOME, m.group(1)), "plataforma": PLATAFORMA, "titulo": titulo,
            "empresa": _espacos(c.get("empresa")) or "Empresa não informada",
            "local": "Remoto" if home_office else ", ".join(_partes(local)), "remoto": modelo == "remoto",
            "publicada_em": data if re.fullmatch(r"\d{4}-\d{2}-\d{2}", data) else None,
            "url": urljoin(SITE, c["href"].strip()), "url_candidatura": None,
            "salario": salario if salario and "combinar" not in _comum._norm(salario) else None,
            "tipo": resumo or None, "descricao": "",
        }
        if modelo:
            v["modelo_trabalho"] = modelo
        if tipos:
            v["tipo_emprego"] = tipos
        vagas.append(v)
    return vagas


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def _lista(termo: str, horas: int) -> tuple[list[dict], str | None]:
    """As vagas da busca do cargo (todas as páginas lidas), guardadas para as outras consultas do mesmo cargo."""
    if termo in _estado["listas"]:
        return _estado["listas"][termo]
    limite = _limite(horas)
    vagas: list[dict] = []
    erro = None
    for numero in range(1, MAX_PAGINAS + 1):
        params = {"busca": termo, **({"pagina": numero} if numero > 1 else {})}
        try:
            pagina = _baixar(f"{LISTA}?{urlencode(params)}")
        except _comum.FonteErro as e:
            erro = str(e)
            break
        achadas = ler_lista(pagina)
        if not achadas:
            if numero == 1 and "vaga-card" in pagina:
                erro = ILEGIVEL
            break
        ids = {v["id"] for v in vagas}
        vagas += [v for v in achadas if v["id"] not in ids]
        datas = [v["publicada_em"] for v in achadas if v.get("publicada_em")]
        if len(achadas) < POR_PAGINA or (datas and min(datas) < limite):
            break
    _estado["listas"][termo] = (vagas, erro)
    return vagas, erro


def _na_regiao(vaga: dict, consulta: dict) -> bool:
    """A vaga é da cidade ou do estado da pessoa ("Cidade, UF")."""
    partes = [p.strip() for p in str(vaga.get("local") or "").split(",") if p.strip()]
    if len(partes) < 2:
        return False
    cidade, uf = _comum._norm(partes[0]), partes[-1].upper()
    if consulta.get("cidade") and cidade == _comum._norm(consulta["cidade"]):
        return True
    estado = _comum._norm(consulta.get("estado"))
    return bool(estado) and (estado.upper() == uf if len(estado) == 2 else UFS.get(uf) == estado)


def _atende(vaga: dict, consulta: dict, limite: str) -> bool:
    if not _comum.bate_cargo(vaga["titulo"], consulta["termo"]):
        return False
    if vaga.get("publicada_em") and vaga["publicada_em"] < limite:
        return False
    if consulta.get("remoto"):
        return vaga["remoto"]
    modelos = consulta.get("modelos") or []
    if vaga.get("modelo_trabalho") and modelos and vaga["modelo_trabalho"] not in modelos:
        return False
    if consulta.get("cidade"):
        return not vaga["remoto"] and _na_regiao(vaga, consulta)
    return True


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if consulta.get("pais") != "brazil":
        return [], []  # a Nerdin é só do Brasil
    termo = " ".join(str(consulta.get("termo") or "").replace('"', " ").split())
    ja_lida = termo in _estado["listas"]
    if not termo or (_estado["bloqueado"] and not ja_lida):
        return [], []  # depois de um bloqueio, nenhum pedido a mais (a lista já lida continua valendo)
    vagas, erro = _lista(termo, horas)
    limite = _limite(horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []


def descrever(vaga: dict) -> str:
    """A descrição da página da vaga (dados estruturados JobPosting). Depois de um bloqueio, devolve o que a vaga já
    tinha, sem pedido."""
    if parada():
        return vaga.get("descricao") or ""
    url = str(vaga.get("url") or "")
    if not VAGA.match(url):
        raise _comum.FonteErro("link de vaga da Nerdin inesperado")
    lida = link.extrair_jobposting(_baixar(url), PLATAFORMA)
    return (lida.get("descricao") or vaga.get("descricao") or "")[:LIMITE_DESCRICAO]


def id_do_link(url: str) -> str | None:
    """O id da vaga ("nerdin-123") a partir do link da página da vaga; None para outros links."""
    m = VAGA.match(str(url or "").strip())
    return _comum.ident(NOME, m.group(1)) if m and str(url).lower().startswith(("http://", "https://")) else None
