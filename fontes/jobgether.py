"""Fonte JobGether: vagas remotas de empresas do mundo todo pela API oficial que o portal oferece a assistentes de IA
(jobgether.com/api/v1/jobs), sem chave, sem login e sem cookies (spec 030).

Os termos de uso do JobGether proíbem acesso automatizado (seções 4.5 e 9). A pessoa decidiu tê-lo na busca pela API
para assistentes, desligado por padrão (constituição, princípio VI, "Termos contrários"). Cada consulta pede as vagas
mais recentes do cargo num local:
- na busca nacional (consultas remota e do país), o país da pessoa;
- na internacional, o país da consulta, ou "anywhere" na consulta global ("mundo todo").
A consulta da cidade e as de mudança ficam de fora: o JobGether só tem vagas remotas (e híbridas, quando pedidas) e
não filtra por cidade. O pedido é um POST com corpo JSON, porque o robots.txt bloqueia endereços com query string. Até
MAX_PAGINAS páginas de POR_PAGINA vagas, parando ao chegar a vagas mais antigas que a janela. A busca da API é ampla,
então fica só a vaga cujo título bate com o cargo.

A lista não traz a descrição, e a página da vaga recusa a ferramenta (403): as vagas entram sem descrição, e a nota da
IA fica provisória (spec 021). O id vem do endereço da vaga (/offer/<id>-<slug>), porque o id da API muda quando a vaga
é republicada.

Pausa de 2 segundos entre os pedidos (o Crawl-delay do site; JOBGETHER_PAUSA=N no .env, com N de 2 a 60) e, no
primeiro bloqueio (403 ou 429), o JobGether fica de fora pelo resto da busca, sem nova tentativa, e das buscas das 24
horas seguintes (a espera, gravada em .cache/).
"""
from __future__ import annotations

import json
import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import _comum

NOME = "jobgether"
PLATAFORMA = "JobGether"
AREAS = ("nacional", "internacional")
POR_PAIS = True
GLOBAL = True  # também na consulta "mundo todo" (anywhere)
TERMOS = ("API oficial do JobGether para assistentes de IA, sem chave e sem login: vagas remotas de empresas do mundo "
          "todo, em inglês. Os termos de uso do JobGether proíbem acesso automatizado; a ferramenta usa a API que o "
          "portal oferece a assistentes, por decisão registrada na spec 030, e vem desligada. As vagas chegam sem "
          "descrição (a nota da IA fica provisória). Se o JobGether limitar, a busca segue sem ele e ele fica 24 horas "
          "em espera. A candidatura é no site da empresa.")

URL = "https://jobgether.com/api/v1/jobs"
POR_PAGINA = 25  # o máximo da API
MAX_PAGINAS = 3  # por consulta (a API vai até 10)
PAUSA = (2.0, 2.0)  # padrão, sem JOBGETHER_PAUSA: o Crawl-delay do robots.txt
VAR_PAUSA = "JOBGETHER_PAUSA"  # no .env ou no ambiente: segundos de pausa (spec 030)
PAUSA_MIN = 2.0  # API oficial: o mínimo é o Crawl-delay, e não os 3 s dos portais que leem páginas
ESPERA = timedelta(hours=24)  # depois de um bloqueio, o JobGether fica de fora das buscas
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "jobgether-espera.json"
TEMPO = 30
LIMITE_BYTES = 5_000_000
BLOQUEIO = "o JobGether limitou as consultas"
ILEGIVEL = "não consegui ler as vagas do JobGether (a API pode ter mudado)"
# nomes de país do jobspy (filtros.PAISES) que o JobGether escreve de outro jeito; os outros levam hífen no lugar do
# espaço ("south africa" -> "south-africa"), e um nome que a API recusar vira aviso
SLUGS = {"usa": "united-states", "uk": "united-kingdom"}
GLOBAL_SLUG = "anywhere"
VAGA = re.compile(r"^https?://(?:www\.)?jobgether\.com/offer/([0-9a-f]{24})(?:-[^/?#]*)?/?(?:[?#].*)?$", re.I)
SALARIO = re.compile(r"\s*([\d.,]+)\s*(?:-\s*([\d.,]+)\s*)?([A-Za-z]{3})\s*")
# contractType da API -> (tipo, código de filtros.TIPOS_EMPREGO); tempo integral no exterior não é CLT, fica sem código
CONTRATOS = (("full time", "Tempo integral", None), ("part time", "Meio período", "meio_periodo"),
             ("fixed term", "Temporário", "temporario"), ("freelance", "Freelance", "pj"),
             ("internship", "Estágio", "estagio"))

_estado = {"bloqueado": False, "ultimo": None, "listas": {}, "pausa": None, "avisos": set(), "locais_recusados": set()}


def _esquecer() -> None:
    _estado.update(bloqueado=False, listas={}, pausa=None, avisos=set(), locais_recusados=set())


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class _LocalRecusado(_comum.FonteErro):
    """A API não conhece o local pedido (400 em "locations")."""


# ---------------------------------------------------------------- pausa, bloqueio e espera

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou JOBGETHER_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com JOBGETHER_PAUSA definida (até MAX_PAGINAS pedidos por consulta)."""
    return _comum.aviso_pausa(PLATAFORMA, "no JobGether", VAR_PAUSA, pausa(), consultas * MAX_PAGINAS)


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    _comum.pausar(_estado, _estado["pausa"])


def espera(agora: datetime | None = None) -> dict | None:
    """{"ate", "motivo"} nas ESPERA horas depois do último bloqueio; None fora delas ou sem arquivo legível."""
    return _comum.ler_espera(ARQ_ESPERA, ESPERA, agora)


def parada() -> bool:
    """Bloqueou nesta busca ou está em espera."""
    return _estado["bloqueado"] or espera() is not None


def _bloquear(motivo: str) -> _comum.FonteErro:
    """Para o JobGether nesta busca e grava a espera para as próximas (o aviso do bloqueio já diz até quando)."""
    _estado["bloqueado"] = True
    _estado["avisos"].add("espera")
    ate = (_comum.gravar_espera(ARQ_ESPERA, motivo) + ESPERA).isoformat(timespec="minutes")
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); em espera até {_comum.ate_quando(ate)}")


def _campo_recusado(e: urllib.error.HTTPError) -> str:
    """O parâmetro que a API recusou, no corpo do 400 (application/problem+json); "" se não der para ler."""
    try:
        return str(json.loads(e.read().decode("utf-8", errors="replace")).get("field") or "")
    except Exception:  # corpo ausente ou fora do formato
        return ""


def _baixar(corpo: dict) -> dict:
    """Um POST à API, com a pausa, sem cookies e sem nova tentativa. 403 e 429 são bloqueio; um local que o JobGether
    não conhece levanta _LocalRecusado; outro erro vale só para esta consulta."""
    _pausar()
    req = urllib.request.Request(URL, data=json.dumps(corpo).encode("utf-8"), method="POST",
                                 headers={"User-Agent": _comum.AGENTE, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TEMPO) as r:
            bruto = r.read(LIMITE_BYTES + 1)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise _bloquear(f"código {e.code}") from None
        if e.code == 400 and _campo_recusado(e) == "locations":
            raise _LocalRecusado(f"o JobGether não reconhece o local {', '.join(corpo.get('locations') or [])}; "
                                 "a busca seguiu sem ele") from None
        raise _comum.FonteErro(f"o JobGether respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise _comum.FonteErro(f"não consegui falar com o JobGether ({getattr(e, 'reason', e)})") from None
    if len(bruto) > LIMITE_BYTES:
        raise _comum.FonteErro(ILEGIVEL)
    try:
        dados = json.loads(bruto.decode("utf-8", errors="replace"), strict=False)
    except ValueError:
        raise _comum.FonteErro(ILEGIVEL) from None
    if not isinstance(dados, dict) or not isinstance(dados.get("jobs"), list):
        raise _comum.FonteErro(ILEGIVEL)
    return dados


# ---------------------------------------------------------------- vagas

def id_do_link(url: str) -> str | None:
    """"jobgether-<id>" num link de vaga (jobgether.com/offer/<id de 24 hex>-<slug>); None para outro link."""
    m = VAGA.match(str(url or "").strip())
    return _comum.ident(NOME, m.group(1).lower()) if m else None


def _contrato(valor) -> tuple[str | None, str | None]:
    texto = " ".join(str(valor or "").lower().replace("-", " ").split())
    return next(((tipo, codigo) for chave, tipo, codigo in CONTRATOS if texto.startswith(chave)), (None, None))


def normalizar(r: dict) -> dict | None:
    titulo = " ".join(str(r.get("title") or "").split())
    url = str(r.get("url") or "").strip()
    vid = id_do_link(url) or (_comum.ident(NOME, r["id"]) if r.get("id") else None)
    if not titulo or not vid:
        return None
    lugares = _comum.curto(r.get("location"))
    hibrido = "hybrid" in str(r.get("remote") or "").lower()
    rotulo = "Híbrido" if hibrido else "Remoto"
    m = SALARIO.fullmatch(str(r.get("salaryRange") or ""))
    numero = lambda s: s.replace(",", "") if s else None
    tipo, codigo = _contrato(r.get("contractType"))
    vaga = {
        "id": vid,
        "plataforma": PLATAFORMA,
        "titulo": titulo,
        "empresa": " ".join(str(r.get("company") or "").split()) or "Empresa não informada",
        "local": f"{rotulo} ({lugares})" if lugares else rotulo,
        "remoto": not hibrido,
        "modelo_trabalho": "hibrido" if hibrido else "remoto",
        "publicada_em": _comum.data_iso(r.get("postedAt")),
        "url": url if re.match(r"^https?://", url) else "",
        "url_candidatura": None,  # a candidatura sai da página da vaga no JobGether, para o site da empresa
        "salario": _comum.salario(numero(m.group(1)), numero(m.group(2)), m.group(3)) if m else None,
        "moeda": _comum.moeda(m.group(3)) if m else None,
        "tipo": tipo,
        "descricao": "",  # a lista não traz, e a página recusa a ferramenta
        "restricao_local": lugares,
    }
    if codigo:
        vaga["tipo_emprego"] = [codigo]
    return vaga


def _local(consulta: dict) -> str | None:
    """O local da consulta no JobGether: "anywhere" na global; senão o país, pelo nome do jobspy."""
    if consulta.get("global"):
        return GLOBAL_SLUG
    pais = " ".join(str(consulta.get("pais") or "").lower().split())
    return SLUGS.get(pais, pais.replace(" ", "-")) if pais else None


def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def _ler(termo: str, local: str, hibrido: bool, horas: int) -> tuple[list[dict], str | None]:
    """As vagas do cargo no local, das mais recentes para as mais antigas: até MAX_PAGINAS páginas, parando ao chegar a
    vagas mais antigas que a janela ou quando a API diz que não há mais. Devolve (vagas, erro); as vagas lidas antes de
    um erro seguem valendo."""
    limite = _limite(horas)
    vagas, ids = [], set()
    for pagina in range(1, MAX_PAGINAS + 1):
        corpo = {"keyword": termo, "locations": [local], "sort": "date", "limit": POR_PAGINA, "page": pagina}
        if hibrido:
            corpo["includeHybrid"] = True
        try:
            dados = _baixar(corpo)
        except _LocalRecusado as e:
            _estado["locais_recusados"].add(local)
            return vagas, str(e)
        except _comum.FonteErro as e:
            return vagas, str(e)
        datas = []
        for item in dados["jobs"]:
            try:
                v = normalizar(item) if isinstance(item, dict) else None
            except (KeyError, TypeError, ValueError, AttributeError, IndexError):
                v = None  # item fora do formato esperado: fica de fora
            if not v:
                continue
            if v.get("publicada_em"):
                datas.append(v["publicada_em"])
            if v["id"] not in ids:
                ids.add(v["id"])
                vagas.append(v)
        mais = bool((dados.get("pagination") or {}).get("hasMore"))
        if not dados["jobs"] or not mais or (datas and min(datas) < limite):
            break
    return vagas, None


def _atende(vaga: dict, consulta: dict, limite: str) -> bool:
    if not _comum.bate_cargo(vaga["titulo"], consulta["termo"]):
        return False
    if vaga.get("publicada_em") and vaga["publicada_em"] < limite:
        return False
    return vaga["remoto"] or not consulta.get("remoto")


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    grupo = str(consulta.get("grupo") or "")
    if grupo == "local" or grupo.startswith("mudanca:"):
        return [], []  # o JobGether não filtra por cidade e não tem vagas presenciais
    e = espera()
    if e:  # durante a espera, nenhum pedido; o aviso sai uma vez por busca
        if "espera" in _estado["avisos"]:
            return [], []
        _estado["avisos"].add("espera")
        return [], [f"{PLATAFORMA} em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); a busca seguiu sem ele"]
    termo = " ".join(str(consulta.get("termo") or "").replace('"', " ").split())
    local = _local(consulta)
    if not termo or not local or local in _estado["locais_recusados"]:
        return [], []
    hibrido = (not consulta.get("remoto") and not consulta.get("global")
               and "hibrido" in (consulta.get("modelos") or []))
    chave = (termo.lower(), local, hibrido)
    ja_lida = chave in _estado["listas"]
    if not ja_lida:
        if _estado["bloqueado"]:
            return [], []  # depois de um bloqueio, nenhum pedido a mais (a lista já lida continua valendo)
        _estado["listas"][chave] = _ler(termo, local, hibrido, horas)
    vagas, erro = _estado["listas"][chave]
    limite = _limite(horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []
