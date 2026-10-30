"""Fonte FullStack: as vagas públicas do portal da FullStack (talent.fullstack.com, "FullStack Connect"), vagas remotas
para a América Latina, sem login e sem a conta, as senhas ou os cookies da pessoa (spec 040).

Os termos de uso da FullStack proíbem acesso automatizado ("any robot, spider, or other automatic device"), e não há
API oficial. A pessoa decidiu tê-la na busca (constituição, princípio VI, "Termos contrários"), desligada por padrão:
quem quiser liga no painel. A página do portal é um app em JavaScript que lê as vagas de uma API interna, sem login; a
ferramenta faz os mesmos pedidos públicos que a página:
- a lista (api-v1.fullstack.com/api/job-postings/public), filtrada pelo país da pessoa (só o Brasil, o único
  identificador de país conhecido), lida uma vez por busca para todos os cargos, até MAX_PAGINAS páginas. A API não
  ordena por data, então a janela de tempo é filtrada aqui;
- o detalhe de cada publicação (job-postings/<id>), só para a descrição das vagas que vão para o relatório, no máximo
  MAX_DESCRICOES por busca.
A FullStack publica a mesma vaga em várias cidades: as publicações viram uma vaga só, pelo id da vaga (jobId). O e-mail
do recrutador e os ids internos que a API devolve não são guardados. Só as consultas remota e do país; a da cidade não
faz pedido (as vagas são remotas).

Pausa sorteada de 3 a 7 segundos entre os pedidos (FULLSTACK_PAUSA=N no .env muda para N a N+4, com N de 3 a 60) e, no
primeiro bloqueio (401, 403, 429 ou 503), a FullStack fica de fora pelo resto da busca, sem nova tentativa, e das
buscas das 24 horas seguintes (a espera, gravada em .cache/).
"""
from __future__ import annotations

import json
import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from . import _comum, link

NOME = "fullstack"
PLATAFORMA = "FullStack"
AREAS = ("nacional",)
TERMOS = ("Consulta não oficial às vagas públicas da FullStack (vagas remotas para a América Latina), sem login. Os "
          "termos de uso da FullStack proíbem acesso automatizado e não há API oficial: a ferramenta faz os mesmos "
          "pedidos públicos que a página do portal, por decisão registrada na spec 040, e vem desligada; ligue aqui "
          "se concordar. Há uma pausa de alguns segundos entre as consultas e, se a FullStack limitar, a busca segue "
          "sem ela e ela fica 24 horas em espera. A candidatura é no próprio portal da FullStack.")

API = "https://api-v1.fullstack.com/api/"
SITE = "https://talent.fullstack.com/jobs/"
POR_PAGINA = 30  # o único tamanho de página que a API aceita (5, 10, 50 e 100 dão 400)
MAX_PAGINAS = 10  # a lista do Brasil tinha 9 em 30/10/2026; a API não ordena por data
MAX_DESCRICOES = 30  # detalhes lidos por busca; as outras vagas ficam pendentes para a próxima
PAISES = {"brazil": "1ae07c37-d911-413f-9160-8cd2a5d93257"}  # nome do jobspy -> countryId da FullStack
PAUSA = (3.0, 7.0)  # padrão, sem FULLSTACK_PAUSA
VAR_PAUSA = "FULLSTACK_PAUSA"  # no .env ou no ambiente: segundos de pausa mínima (spec 040)
PAUSA_MIN, PAUSA_FAIXA = 3.0, 4.0  # N de 3 a 60; a pausa é sorteada de N a N + 4
ESPERA = timedelta(hours=24)  # depois de um bloqueio, a FullStack fica de fora das buscas
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "fullstack-espera.json"
BLOQUEIOS = (401, 403, 429, 503)
TEMPO = 30
LIMITE_BYTES = 5_000_000
LIMITE_DESCRICAO = 12000
BLOQUEIO = "a FullStack limitou as consultas"
ILEGIVEL = "não consegui ler as vagas da FullStack (a API pode ter mudado)"
VAGA = re.compile(r"^https?://talent\.fullstack\.com/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
                  r"(?:/apply)?/?(?:[?#].*)?$", re.I)
MODELOS = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial", "onsite": "presencial"}
# linkedInJobType da API -> (tipo, código de filtros.TIPOS_EMPREGO); tempo integral no exterior não é CLT, fica sem código
CONTRATOS = {"FULL_TIME": ("Tempo integral", None), "PART_TIME": ("Meio período", "meio_periodo"),
             "CONTRACT": ("Contrato", "pj"), "TEMPORARY": ("Temporário", "temporario"),
             "INTERNSHIP": ("Estágio", "estagio")}

_estado = {"bloqueado": False, "ultimo": None, "pausa": None, "listas": {}, "avisou_espera": False}


def _esquecer() -> None:
    _estado.update(bloqueado=False, pausa=None, listas={}, avisou_espera=False)


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- pausa, bloqueio e espera

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou FULLSTACK_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN, faixa=PAUSA_FAIXA)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com FULLSTACK_PAUSA definida (a lista é uma por busca, mais as descrições)."""
    return _comum.aviso_pausa(PLATAFORMA, "na FullStack", VAR_PAUSA, pausa(),
                              MAX_PAGINAS + MAX_DESCRICOES if consultas else 0)


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
    """Para a FullStack nesta busca e grava a espera para as próximas (o aviso do bloqueio já diz até quando)."""
    _estado.update(bloqueado=True, avisou_espera=True)
    ate = (_comum.gravar_espera(ARQ_ESPERA, motivo) + ESPERA).isoformat(timespec="minutes")
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); em espera até {_comum.ate_quando(ate)}")


def _baixar(caminho: str, params: dict | None = None):
    """Um GET à API, com a pausa, sem cookies e sem nova tentativa: 401, 403, 429 e 503 são bloqueio; outro erro vale
    só para este pedido."""
    _pausar()
    url = API + caminho + (f"?{urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": _comum.AGENTE, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
    except urllib.error.HTTPError as e:
        if e.code in BLOQUEIOS:
            raise _bloquear(f"código {e.code}") from None
        raise _comum.FonteErro(f"a FullStack respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise _comum.FonteErro(f"não consegui falar com a FullStack ({getattr(e, 'reason', e)})") from None
    if len(corpo) > LIMITE_BYTES:
        raise _comum.FonteErro("resposta grande demais da FullStack")
    try:
        return json.loads(corpo.decode("utf-8", errors="replace"))
    except ValueError:
        raise _comum.FonteErro(ILEGIVEL) from None


# ---------------------------------------------------------------- leitura

def _espacos(s) -> str:
    return " ".join(str(s or "").split())


def ler_lista(itens) -> list[dict]:
    """As publicações da API no formato comum, uma vaga por jobId (a primeira publicação vale para o link). Ficam de
    fora o e-mail do recrutador e os ids internos."""
    vagas, vistos = [], set()
    for it in itens if isinstance(itens, list) else []:
        if not isinstance(it, dict):
            continue
        job, pub, titulo = str(it.get("jobId") or ""), str(it.get("id") or ""), _espacos(it.get("jobTitle"))
        if not job or not pub or not titulo or job in vistos:
            continue
        vistos.add(job)
        modelo = MODELOS.get(str(it.get("linkedInWorkplaceType") or "").strip().lower())
        remoto = modelo == "remoto"
        regiao = "América Latina" if str(it.get("regionGroup") or "").lower() == "latam" else _espacos(it.get("region"))
        tipo, codigo = CONTRATOS.get(str(it.get("linkedInJobType") or "").upper(), (None, None))
        v = {
            "id": _comum.ident(NOME, job), "plataforma": PLATAFORMA, "titulo": titulo, "empresa": "FullStack",
            "local": "Remoto" if remoto else ", ".join(x for x in (_espacos(it.get("city")), _espacos(it.get("state")),
                                                                    _espacos(it.get("region"))) if x),
            "remoto": remoto, "publicada_em": _comum.data_iso(it.get("createdAt")), "url": SITE + pub,
            "url_candidatura": None, "salario": None,
            "tipo": " • ".join(x for x in (_espacos(it.get("linkedInSeniority")), tipo) if x) or None,
            "tipo_emprego": [codigo] if codigo else [], "idioma": "en", "descricao": "",
        }
        if modelo:
            v["modelo_trabalho"] = modelo
        if remoto and regiao:
            v["restricao_local"] = regiao
        vagas.append(v)
    return vagas


def _descricao(detalhe: dict) -> str:
    """As seções do detalhe (título e texto) e as habilidades, até LIMITE_DESCRICAO caracteres."""
    partes = []
    for s in detalhe.get("sections") or []:
        if isinstance(s, dict):
            corpo = link.texto_de_html(str(s.get("body") or ""))
            partes.append("\n\n".join(x for x in (_espacos(s.get("title")), corpo) if x))
    habilidades = [_espacos(h) for h in detalhe.get("skillsNames") or [] if _espacos(h)]
    if habilidades:
        partes.append("Habilidades: " + ", ".join(habilidades))
    return "\n\n".join(p for p in partes if p)[:LIMITE_DESCRICAO]


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def _lista(pais: str) -> tuple[list[dict], str | None]:
    """As vagas publicadas no país (todas as páginas lidas), guardadas para as outras consultas da busca."""
    if pais in _estado["listas"]:
        return _estado["listas"][pais]
    itens, erro = [], None
    for numero in range(1, MAX_PAGINAS + 1):
        try:
            dados = _baixar("job-postings/public", {"page": numero, "take": POR_PAGINA,
                                                    "filter": f"countryId={PAISES[pais]}"})
        except _comum.FonteErro as e:
            erro = str(e)
            break
        meta = dados.get("meta") if isinstance(dados, dict) else None
        if not isinstance(meta, dict) or not isinstance(dados.get("data"), list):
            erro = ILEGIVEL
            break
        itens += dados["data"]
        if not meta.get("hasNextPage"):
            break
    _estado["listas"][pais] = (ler_lista(itens), erro)
    return _estado["listas"][pais]


def _atende(vaga: dict, consulta: dict, limite: str) -> bool:
    if not _comum.bate_cargo(vaga["titulo"], consulta["termo"]):
        return False
    if vaga.get("publicada_em") and vaga["publicada_em"] < limite:
        return False
    if consulta.get("remoto"):
        return vaga["remoto"]
    modelos = consulta.get("modelos") or []
    return not modelos or vaga.get("modelo_trabalho", "remoto") in modelos


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    pais = str(consulta.get("pais") or "").lower()
    if pais not in PAISES or consulta.get("cidade") or not str(consulta.get("termo") or "").strip():
        return [], []  # outro país (identificador desconhecido) ou consulta da cidade: sem pedido
    e = espera()
    if e:  # durante a espera, nenhum pedido; o aviso sai uma vez por busca
        if _estado["avisou_espera"]:
            return [], []
        _estado["avisou_espera"] = True
        return [], [f"{PLATAFORMA} em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); a busca seguiu sem ela"]
    ja_lida = pais in _estado["listas"]
    if _estado["bloqueado"] and not ja_lida:
        return [], []
    vagas, erro = _lista(pais)
    limite = _limite(horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []


def _publicacao(url: str) -> str | None:
    m = VAGA.match(str(url or "").strip())
    return m.group(1).lower() if m else None


def descrever(vaga: dict) -> str:
    """A descrição pelo detalhe da publicação. Depois de um bloqueio ou na espera, devolve o que a vaga já tinha, sem
    pedido."""
    if parada():
        return vaga.get("descricao") or ""
    pub = _publicacao(vaga.get("url"))
    if not pub:
        raise _comum.FonteErro("link de vaga da FullStack inesperado")
    detalhe = _baixar(f"job-postings/{pub}")
    if not isinstance(detalhe, dict):
        raise _comum.FonteErro(ILEGIVEL)
    return _descricao(detalhe) or vaga.get("descricao") or ""


def ler(url: str) -> dict:
    """A vaga pelo link (Adicionar Vaga), com o mesmo id da busca: um pedido ao detalhe da publicação. Na espera,
    nenhum pedido: link.LinkErro com a plataforma, para a pessoa completar à mão."""
    pub = _publicacao(url)
    if not pub:
        raise link.LinkErro("não reconheci o link da vaga da FullStack (talent.fullstack.com/jobs/<id>)")
    e = espera()
    if e:
        raise link.LinkErro(f"a FullStack está em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); "
                            "tente depois ou preencha os dados à mão", {"plataforma": PLATAFORMA, "url": url})
    try:
        detalhe = _baixar(f"job-postings/{pub}")
    except _comum.FonteErro as erro:
        raise link.LinkErro(str(erro), {"plataforma": PLATAFORMA, "url": url}) from None
    vagas = ler_lista([detalhe])
    if not vagas:
        raise link.LinkErro("não consegui ler a vaga da FullStack", {"plataforma": PLATAFORMA, "url": url})
    return {**vagas[0], "descricao": _descricao(detalhe), "url": SITE + pub}


def id_do_link(url: str) -> str | None:
    """None: o id da busca (fullstack-<jobId>) não está no link, que traz o id da publicação; ler() resolve com um
    pedido."""
    return None
