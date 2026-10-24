"""Apoio às fontes internacionais: baixar JSON e RSS com pausa e limites, filtrar pelo cargo, HTML → texto,
datas e salário no formato do dashboard.

As listas dessas fontes não buscam por cargo (ou buscam mal), então cada fonte baixa a lista recente uma
vez por busca, guarda com lembrar() e filtra aqui pelos cargos (bate_cargo), como os filtros de título.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
import unicodedata
import urllib.error
import urllib.request
import math
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import segredos  # segredos.py, na raiz: o .env (<NOME>_PAUSA)

from .link import texto_de_html

AGENTE = "meu-proximo-trampo (ferramenta local de busca de vagas)"
TEMPO = 30
LIMITE_BYTES = 20_000_000  # listas completas com descrição (RemoteOK, Greenhouse) passam de alguns MB
LIMITE_DESCRICAO = 12000  # o trecho de elegibilidade costuma estar no fim do anúncio
INTERVALO = 2.0  # segundos entre consultas ao mesmo site
VALIDADE = 15 * 60  # a memória de uma lista vale para a busca em curso
PASTA = Path(__file__).resolve().parent.parent / ".cache" / "fontes"  # listas guardadas em disco (fora do Git)
PALAVRAS_VAZIAS = {"a", "an", "and", "the", "of", "for", "to", "in", "at", "with", "e", "de", "da", "do", "das",
                   "dos", "em", "para"}
SIMBOLOS = {"BRL": "R$", "USD": "US$", "EUR": "€"}
PERIODOS = (("hour", "/hora"), ("day", "/dia"), ("daily", "/dia"), ("week", "/semana"), ("month", "/mês"),
            ("year", "/ano"), ("annual", "/ano"))  # "per-year-salary", "1 YEAR", "monthly"…

_ultima: dict[str, float] = {}  # site -> time.monotonic() da última consulta
_memoria: dict[str, tuple[float, object]] = {}


class FonteErro(Exception):
    def __init__(self, motivo: str, repetido: bool = False):
        super().__init__(motivo)
        self.repetido = repetido  # o mesmo erro já saiu nesta busca


# ---------------------------------------------------------------- rede

def baixar(url: str, params: dict | None = None, aceitar: str = "application/json") -> bytes:
    """Corpo da resposta, com pausa entre consultas ao mesmo site e uma nova tentativa se ele pedir para
    esperar (429). Levanta FonteErro com uma explicação legível."""
    if params:
        url += ("&" if "?" in url else "?") + urlencode(params)
    site = urlsplit(url).hostname or ""
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": aceitar})
    for tentativa in range(2):
        espera = _ultima.get(site, -INTERVALO) + INTERVALO - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        _ultima[site] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=TEMPO) as r:
                corpo = r.read(LIMITE_BYTES + 1)
        except urllib.error.HTTPError as e:
            if e.code == 429 and tentativa == 0:
                time.sleep(_segundos(e.headers.get("Retry-After")))
                continue
            raise FonteErro(f"{site} respondeu {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise FonteErro(f"não consegui falar com {site} ({getattr(e, 'reason', e)})") from None
        if len(corpo) > LIMITE_BYTES:
            raise FonteErro(f"resposta grande demais de {site}")
        return corpo
    raise FonteErro(f"{site} pediu para esperar; tente mais tarde")


def _segundos(retry_after) -> float:
    try:
        return min(max(float(retry_after), 5.0), 60.0)
    except (TypeError, ValueError):
        return 20.0


def baixar_json(url: str, params: dict | None = None):
    corpo = baixar(url, params)
    try:
        return json.loads(corpo.decode("utf-8", errors="replace"), strict=False)
    except ValueError:
        raise FonteErro(f"resposta inesperada de {urlsplit(url).hostname}") from None


def baixar_texto(url: str, params: dict | None = None) -> str:
    return baixar(url, params, aceitar="application/rss+xml, application/xml, text/xml, */*").decode(
        "utf-8", errors="replace")


def lembrar(chave: str, fn, horas_disco: float = 0):
    """O resultado de fn() (uma lista baixada), guardado para a busca em curso: o segundo cargo da mesma
    fonte não consulta de novo. Um erro também fica guardado, para não insistir num site fora do ar (e sai
    uma vez só). horas_disco: guarda também em disco por esse tempo (fontes que pedem poucas consultas por dia)."""
    agora = time.monotonic()
    guardado = _memoria.get(chave)
    if guardado and agora - guardado[0] < VALIDADE:
        valor = guardado[1]
        if isinstance(valor, FonteErro):
            raise FonteErro(str(valor), repetido=True)
        return valor
    try:
        valor = _do_disco(chave, horas_disco, fn) if horas_disco else fn()
    except FonteErro as e:
        valor = e
    _memoria[chave] = (agora, valor)
    if isinstance(valor, FonteErro):
        raise valor
    return valor


def _do_disco(chave: str, horas: float, fn):
    arq = PASTA / f"{re.sub(r'[^a-z0-9_-]+', '-', chave.lower())}.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        if 0 <= time.time() - float(dados["em"]) < horas * 3600:
            return dados["itens"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    itens = fn()
    try:
        PASTA.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({"em": time.time(), "itens": itens}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # sem disco, só não guarda
    return itens


AO_ESQUECER: list = []  # fontes com estado próprio da busca (ex.: o bloqueio do LinkedIn) se registram aqui


def esquecer() -> None:
    _memoria.clear()
    for fn in AO_ESQUECER:
        fn()


# ---------------------------------------------------------------- portais que leem páginas (spec 026)
# Pausa ajustável por <NOME>_PAUSA no .env, pedido de página com parada no bloqueio e espera depois dele. Cada fonte
# chama estas funções com os próprios atributos (VAR_PAUSA, PAUSA, ARQ_ESPERA, ESPERA…).

PAUSA_MAX = 60.0  # o teto de qualquer <NOME>_PAUSA
BLOQUEIOS = (403, 429, 503)


def num(n: float) -> str:
    return f"{n:g}".replace(".", ",")


def pausa_do_env(var: str, padrao: tuple[float, float], minimo: float, maximo: float = PAUSA_MAX,
                 faixa: float = 0.0) -> dict:
    """{"faixa": (mín, máx) em segundos, "definida": a variável está no .env ou no ambiente, "ajuste": motivo quando o
    valor foi trocado pelo limite ou ignorado, ou ""}. Sem a variável, vale o padrão do portal; com ela (N, entre
    `minimo` e `maximo`), a pausa vai de N a N + `faixa`."""
    bruto = segredos.ler(var)
    if not bruto:
        return {"faixa": padrao, "definida": False, "ajuste": ""}
    try:
        n = float(bruto.replace(",", "."))
        if not math.isfinite(n):
            raise ValueError
    except ValueError:
        return {"faixa": padrao, "definida": True,
                "ajuste": f"o valor de {var} ({bruto[:20]}) não é um número e foi ignorado"}
    ajuste = ""
    if n < minimo:
        n, ajuste = minimo, f"{var} abaixo do mínimo de {num(minimo)} segundos; vale o mínimo"
    elif n > maximo:
        n, ajuste = maximo, f"{var} acima do máximo de {num(maximo)} segundos; vale o máximo"
    return {"faixa": (n, n + faixa), "definida": True, "ajuste": ajuste}


def aviso_pausa(portal: str, no_portal: str, var: str, p: dict, pedidos: int) -> str | None:
    """Aviso do começo da busca quando a variável de pausa do portal está definida: a pausa em uso e o tempo de pausa
    estimado para `pedidos` pedidos, no máximo. `no_portal`: "no LinkedIn", "na Nerdin"…"""
    if not p["definida"] or not pedidos:
        return None
    mn, mx = p["faixa"]
    minutos = max(1, round(pedidos * (mn + mx) / 2 / 60))
    faixa = f"{num(mn)} s" if mn == mx else f"{num(mn)} a {num(mx)} s"
    texto = f"{portal}: pausa de {faixa} entre os pedidos ({var}), até cerca de {minutos} min só de pausa {no_portal}."
    return f"{texto} Atenção: {p['ajuste']}." if p["ajuste"] else texto


def pausar(estado: dict, faixa: tuple[float, float]) -> None:
    """Espera um intervalo sorteado em `faixa` desde o último pedido ao portal (estado["ultimo"])."""
    if estado["ultimo"] is not None:
        espera = estado["ultimo"] + random.uniform(*faixa) - time.monotonic()
        if espera > 0:
            time.sleep(espera)
    estado["ultimo"] = time.monotonic()


def gravar_espera(arq: Path, motivo: str, agora: datetime | None = None) -> datetime:
    """Grava o começo da espera do portal (fora do Git, em .cache/); se não der para gravar, segue sem ela."""
    agora = agora or datetime.now()
    try:
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({"desde": agora.isoformat(timespec="seconds"), "motivo": motivo},
                                  ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return agora


def ler_espera(arq: Path, duracao: timedelta, agora: datetime | None = None) -> dict | None:
    """{"ate", "motivo"} durante `duracao` depois do último bloqueio gravado; None fora dela ou sem arquivo legível."""
    agora = agora or datetime.now()
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        desde = datetime.fromisoformat(str(dados["desde"]))
    except (OSError, ValueError, TypeError, KeyError):
        return None
    ate = min(desde, agora) + duracao  # hora gravada no futuro (relógio mudou) vale como agora
    if agora >= ate:
        return None
    return {"ate": ate.isoformat(timespec="minutes"), "motivo": str(dados.get("motivo") or "bloqueio")}


def ate_quando(iso, hoje=None) -> str:
    """O fim da espera para os avisos: "17:00" hoje (ou já passado), "24/10 17:00" num dia seguinte."""
    s = str(iso or "")
    hoje = hoje or datetime.now().date()
    try:
        dia = datetime.fromisoformat(s[:16]).date()
    except ValueError:
        return s[11:16]
    return f"{dia:%d/%m} {s[11:16]}" if dia > hoje else s[11:16]


def baixar_pagina(url: str, o_portal: str, antes, bloquear, sinais_login: tuple[str, ...] = ("login",),
                  tempo: int = 20, limite: int = 3_000_000) -> str:
    """Um pedido HTML ao portal, sem cookies e sem nova tentativa. antes() faz a pausa; bloquear(motivo) devolve o
    FonteErro do bloqueio (recusa, limite de consultas ou redirecionamento para o login). `o_portal`: "o InfoJobs"…"""
    antes()
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html",
                                               "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=tempo) as r:
            corpo = r.read(limite + 1)
            charset = r.headers.get_content_charset() or "utf-8"
            final = r.geturl() or url
    except urllib.error.HTTPError as e:
        if e.code in BLOQUEIOS:
            raise bloquear(f"código {e.code}") from None
        raise FonteErro(f"{o_portal} respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FonteErro(f"não consegui falar com {o_portal} ({getattr(e, 'reason', e)})") from None
    if any(s in urlsplit(final).path.lower() for s in sinais_login):
        raise bloquear("pediu login")
    if len(corpo) > limite:
        raise FonteErro(f"resposta grande demais d{o_portal}")
    return corpo.decode(charset, errors="replace")


UFS = {"AC": "acre", "AL": "alagoas", "AP": "amapa", "AM": "amazonas", "BA": "bahia", "CE": "ceara",
       "DF": "distrito federal", "ES": "espirito santo", "GO": "goias", "MA": "maranhao", "MT": "mato grosso",
       "MS": "mato grosso do sul", "MG": "minas gerais", "PA": "para", "PB": "paraiba", "PR": "parana",
       "PE": "pernambuco", "PI": "piaui", "RJ": "rio de janeiro", "RN": "rio grande do norte",
       "RS": "rio grande do sul", "RO": "rondonia", "RR": "roraima", "SC": "santa catarina", "SP": "sao paulo",
       "SE": "sergipe", "TO": "tocantins"}


def na_regiao(cidade: str, uf: str, consulta: dict) -> bool:
    """A vaga (cidade e sigla do estado) é da cidade ou do estado da consulta (sigla ou nome do estado)."""
    if consulta.get("cidade") and cidade and _norm(cidade) == _norm(consulta["cidade"]):
        return True
    estado, uf = _norm(consulta.get("estado")), str(uf or "").strip().upper()
    return bool(estado and uf) and (estado.upper() == uf if len(estado) == 2 else UFS.get(uf) == estado)


def buscar_lista(chave: str, baixar_lista, normalizar, consulta: dict, horas: int, por_termo: int,
                 horas_disco: float = 0) -> tuple[list[dict], list[str]]:
    """O buscar() das fontes que baixam uma lista: a lista uma vez por busca, filtrada aqui."""
    try:
        itens = lembrar(chave, baixar_lista, horas_disco)
    except FonteErro as e:
        return [], [] if e.repetido else [str(e)]
    return filtrar(itens, consulta, horas, por_termo, normalizar), []


def filtrar(itens, consulta: dict, horas: int, por_termo: int, normalizar) -> list[dict]:
    """Normaliza e fica com as vagas do cargo, da janela de publicação e, na busca só remota, as remotas."""
    limite = (datetime.now(timezone.utc) - timedelta(days=math.ceil(horas / 24))).date().isoformat()
    saida, ids = [], set()
    for item in itens or []:
        try:
            v = normalizar(item)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            v = None  # item fora do formato esperado: fica de fora
        if not v or v["id"] in ids or not v.get("titulo") or not bate_cargo(v["titulo"], consulta["termo"]):
            continue
        if v.get("publicada_em") and v["publicada_em"] < limite:
            continue
        if consulta.get("remoto") and not v.get("remoto"):
            continue
        ids.add(v["id"])
        saida.append(v)
    return saida[:por_termo]


# ---------------------------------------------------------------- texto

def consertar(s) -> str:
    """Texto UTF-8 que chegou lido como Latin-1 ("fÃ¼r" -> "für"); o resto fica como está."""
    s = str(s or "")
    if re.search("[ÂÃ][-¿]", s):
        try:
            return s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return s


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9+#]+", " ", s).split())


def bate_cargo(titulo: str, termo: str) -> bool:
    """O título atende ao cargo: frase exata se o cargo vier entre aspas; senão, todas as palavras
    significativas do cargo aparecem no título (em qualquer ordem)."""
    t = f" {_norm(titulo)} "
    termo = str(termo or "").strip()
    if len(termo) > 1 and termo[0] == termo[-1] == '"':
        frase = _norm(termo)
        return bool(frase) and f" {frase} " in t
    palavras = [p for p in _norm(termo).split() if p not in PALAVRAS_VAZIAS]
    return bool(palavras) and all(f" {p} " in t for p in palavras)


def texto(trecho) -> str:
    """Descrição legível (HTML ou texto), até LIMITE_DESCRICAO caracteres."""
    trecho = str(trecho or "")
    if "<" in trecho or "&lt;" in trecho:
        trecho = texto_de_html(trecho)
    return trecho.strip()[:LIMITE_DESCRICAO]


def data_iso(valor) -> str | None:
    """AAAA-MM-DD a partir de segundos ou milissegundos desde 1970, ISO 8601 ou a data de um RSS."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)) or re.fullmatch(r"\d{9,13}", str(valor).strip()):
        n = float(valor)
        if n > 1e11:  # milissegundos
            n /= 1000
        return datetime.fromtimestamp(n, tz=timezone.utc).date().isoformat()
    s = str(valor).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return None


def salario(minimo, maximo, moeda=None, periodo=None) -> str | None:
    """Faixa no formato das outras fontes ("US$ 100.000–150.000/ano"); None sem valor."""
    def numero(x):
        try:
            n = float(x)
        except (TypeError, ValueError):
            return None
        return n if n > 0 else None
    lo, hi = numero(minimo), numero(maximo)
    if lo is None and hi is None:
        return None
    moeda = str(moeda or "").strip().upper()
    fmt = lambda x: f"{x:,.0f}".replace(",", ".")
    faixa = fmt(lo or hi) if lo is None or hi is None or lo == hi else f"{fmt(lo)}–{fmt(hi)}"
    p = next((pt for en, pt in PERIODOS if en in str(periodo or "").lower()), "")
    return f"{SIMBOLOS.get(moeda, moeda)} {faixa}{p}".strip()


def moeda(codigo) -> str | None:
    codigo = str(codigo or "").strip().upper()
    return codigo if re.fullmatch(r"[A-Z]{3}", codigo) else None


def ident(nome: str, chave) -> str:
    """Id estável da vaga ("remotive-123"); se passaria de 64 caracteres (o limite do banco), o fim do slug
    vira um resumo dele."""
    chave = re.sub(r"[^a-z0-9_.-]+", "-", str(chave).lower()).strip("-")
    vid = f"{nome}-{chave}"
    return vid if len(vid) <= 64 else f"{vid[:55]}-{hashlib.sha1(chave.encode()).hexdigest()[:8]}"


def curto(s, limite: int = 200) -> str | None:
    s = " ".join(str(s or "").split())
    return s[:limite] or None
