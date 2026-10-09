"""Fonte startup.jobs, pelo servidor MCP público do site (https://startup.jobs/mcp).

Vagas de startups, a maior parte de fora do Brasil e muitas remotas. O servidor é
aberto, sem login, e só lê vagas; aqui ele é chamado direto por HTTP, no protocolo do
MCP (JSON-RPC), como na Gupy. Sem conta, ele só traz as vagas dos últimos 14 dias e
aceita 20 consultas por minuto, por isso as consultas saem espaçadas. A chave de API é
opcional (identifica o uso; o acesso total o site libera por e-mail): fica na variável
de ambiente MCP_STARTUP_JOBS ou numa linha MCP_STARTUP_JOBS=… do arquivo .env da raiz,
que está fora do Git.

Diferenças para os outros portais: a palavra-chave é procurada como frase no título e
no nome da empresa (aspas zeram o resultado e saem), o local é só o país (a busca na
cidade traz as vagas híbridas e presenciais do país e fica com as da cidade, sem raio),
e a lista não traz a descrição: ela vem por descrever(), uma consulta por vaga, que o
vagas.py só pede para as vagas que vão para o relatório.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import segredos  # segredos.py, na raiz: chaves do .env

NOME = "startupjobs"
PLATAFORMA = "Startup Jobs"
URL_MCP = "https://api.startup.jobs/mcp"
VAR_CHAVE = "MCP_STARTUP_JOBS"
LIMITE_DESCRICAO = 12000
POR_PAGINA = 50  # máximo do servidor
MAX_PAGINAS = 5  # a busca na cidade filtra aqui, página a página
INTERVALO = 3.2  # segundos entre consultas (20 por minuto sem acesso total)
TEMPO = 30
# Código ISO de cada país de filtros.PAISES (o servidor filtra pelo código)
CODIGOS = {
    "África do Sul": "ZA", "Alemanha": "DE", "Arábia Saudita": "SA", "Argentina": "AR", "Austrália": "AU",
    "Áustria": "AT", "Bahrein": "BH", "Bangladesh": "BD", "Bélgica": "BE", "Brasil": "BR", "Bulgária": "BG",
    "Canadá": "CA", "Catar": "QA", "Chile": "CL", "China": "CN", "Chipre": "CY", "Colômbia": "CO",
    "Coreia do Sul": "KR", "Costa Rica": "CR", "Croácia": "HR", "Dinamarca": "DK", "Egito": "EG",
    "Emirados Árabes Unidos": "AE", "Equador": "EC", "Eslováquia": "SK", "Eslovênia": "SI", "Espanha": "ES",
    "Estados Unidos": "US", "Estônia": "EE", "Filipinas": "PH", "Finlândia": "FI", "França": "FR",
    "Grécia": "GR", "Holanda": "NL", "Hong Kong": "HK", "Hungria": "HU", "Índia": "IN", "Indonésia": "ID",
    "Irlanda": "IE", "Israel": "IL", "Itália": "IT", "Japão": "JP", "Kuwait": "KW", "Letônia": "LV",
    "Lituânia": "LT", "Luxemburgo": "LU", "Malásia": "MY", "Malta": "MT", "Marrocos": "MA", "México": "MX",
    "Nigéria": "NG", "Noruega": "NO", "Nova Zelândia": "NZ", "Omã": "OM", "Panamá": "PA", "Paquistão": "PK",
    "Peru": "PE", "Polônia": "PL", "Portugal": "PT", "Reino Unido": "GB", "República Tcheca": "CZ",
    "Romênia": "RO", "Singapura": "SG", "Suécia": "SE", "Suíça": "CH", "Tailândia": "TH", "Taiwan": "TW",
    "Turquia": "TR", "Ucrânia": "UA", "Uruguai": "UY", "Venezuela": "VE", "Vietnã": "VN",
}
PAISES = {codigo: nome for nome, codigo in CODIGOS.items()}
MODALIDADES = {"remote": "remoto", "hybrid": "híbrido", "on-site": "presencial"}
TIPOS = {"full-time": "Tempo integral", "part-time": "Meio período", "internship": "Estágio",
         "contractor": "Contrato (PJ)"}
PERIODOS = {"per year": "/ano", "per month": "/mês", "per week": "/semana", "per day": "/dia", "per hour": "/hora"}
EMPRESAS_SEM_NOME = {"pagina de carreira externa", "external career page"}  # anúncio copiado sem o nome da empresa

_ultima = 0.0  # time.monotonic() da última consulta
_sem_chave = False  # o servidor recusou a chave: as próximas consultas vão sem ela
_aviso = ""  # sai uma vez, nos erros da busca


class StartupJobsErro(Exception):
    pass


def _sem_acento(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def _chave() -> str:
    """Chave de API opcional: a variável de ambiente ou a linha dela no .env da raiz."""
    return segredos.ler(VAR_CHAVE)


def _avisos() -> list[str]:
    global _aviso
    aviso, _aviso = _aviso, ""
    return [aviso] if aviso else []


def _segundos(retry_after) -> float:
    try:
        return min(max(float(retry_after), 5.0), 60.0)
    except (TypeError, ValueError):
        return 20.0


def chamar(ferramenta: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do MCP do startup.jobs e devolve o JSON da resposta. Espaça as consultas e, se o
    servidor pedir para esperar (429), espera e tenta de novo. Chave recusada não impede a consulta: ela só
    identifica o uso, então a consulta segue sem ela (e a busca avisa)."""
    global _ultima, _sem_chave, _aviso
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": ferramenta, "arguments": argumentos}}).encode("utf-8")
    cabecalhos = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                  "MCP-Protocol-Version": "2025-06-18", "User-Agent": "meu-proximo-trampo"}
    chave = "" if _sem_chave else _chave()
    if chave:
        cabecalhos["Authorization"] = f"Bearer {chave}"
    texto = ""
    for tentativa in range(3):
        espera = _ultima + INTERVALO - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        _ultima = time.monotonic()
        try:
            with urllib.request.urlopen(urllib.request.Request(URL_MCP, data=corpo, headers=cabecalhos),
                                        timeout=TEMPO) as r:
                texto = r.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and cabecalhos.pop("Authorization", None):
                _sem_chave = True
                _aviso = f"o startup.jobs recusou a chave de API ({e.code}) e a busca seguiu sem ela; confira {VAR_CHAVE}"
                continue
            if e.code == 429 and tentativa < 2:
                time.sleep(_segundos(e.headers.get("Retry-After")))
                continue
            raise StartupJobsErro(f"o servidor do startup.jobs respondeu {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise StartupJobsErro(f"não consegui falar com o startup.jobs ({getattr(e, 'reason', e)})") from None
    resposta = None
    for bloco in [x[5:].strip() for x in texto.splitlines() if x.startswith("data:")] or [texto]:  # SSE ou JSON puro
        try:
            msg = json.loads(bloco, strict=False)
        except ValueError:
            continue
        if isinstance(msg, dict) and msg.get("id") == 1:
            resposta = msg
    if resposta is None:
        raise StartupJobsErro("resposta inesperada do servidor do startup.jobs")
    if "error" in resposta:
        raise StartupJobsErro(f"o startup.jobs recusou a consulta ({(resposta['error'] or {}).get('message')})")
    resultado = resposta.get("result") or {}
    conteudo = "".join(c.get("text", "") for c in resultado.get("content") or [] if c.get("type") == "text")
    if resultado.get("isError"):
        raise StartupJobsErro(f"o startup.jobs recusou a consulta ({conteudo[:300]})")
    try:
        dados = json.loads(conteudo, strict=False)
    except ValueError:
        raise StartupJobsErro("resposta inesperada do servidor do startup.jobs") from None
    if not isinstance(dados, dict):
        raise StartupJobsErro("resposta inesperada do servidor do startup.jobs")
    return dados


def _empresa(c: dict) -> str:
    nome = re.sub(r"\s+-\s+LinkedIn$", "", str(c.get("name") or "").strip(), flags=re.I)  # "Empresa - LinkedIn"
    if _sem_acento(nome) in EMPRESAS_SEM_NOME:  # fica o site da empresa, quando há
        nome = (urlsplit(str(c.get("website_url") or "")).hostname or "").removeprefix("www.")
    return nome or "Empresa não informada"


def _local(r: dict) -> str:
    loc = r.get("location") if isinstance(r.get("location"), dict) else {}
    pais = PAISES.get(loc.get("country_code") or "") or loc.get("country") or ""
    if r.get("workplace_type") == "remote":
        return f"Remoto ({pais})" if pais else "Remoto"
    return ", ".join(x for x in (loc.get("city"), pais) if x)


def _salario(s) -> str | None:
    if not isinstance(s, str) or not s.strip():
        return None
    for en, pt in PERIODOS.items():
        s = s.replace(" " + en, pt)
    return s.strip()


def _normalizar(r: dict) -> dict | None:
    if not r.get("id"):
        return None
    modalidade = r.get("workplace_type") or ""
    tipo = TIPOS.get(r.get("employment_type") or "")
    descricao = (r.get("description") or "").split("Originally posted on startup.jobs")[0].strip()[:LIMITE_DESCRICAO]
    # o que o startup.jobs informa em campos próprios vai no fim da descrição, para a análise e para o dashboard
    extras = [f"modelo {MODALIDADES[modalidade]}" if modalidade in MODALIDADES else "", tipo.lower() if tipo else ""]
    if any(extras):
        descricao = (descricao + "\n\nNo startup.jobs: " + " · ".join(x for x in extras if x)).strip()
    publicada = str(r.get("published_at") or "")[:10]
    return {
        "id": f"{NOME}-{r['id']}",
        "plataforma": PLATAFORMA,
        "titulo": (r.get("title") or "").strip(),
        "empresa": _empresa(r.get("company") if isinstance(r.get("company"), dict) else {}),
        "local": _local(r),
        "remoto": modalidade == "remote",
        "publicada_em": publicada if re.fullmatch(r"\d{4}-\d{2}-\d{2}", publicada) else None,
        "url": r.get("url") or "",
        "url_candidatura": None,  # a candidatura sai da página da vaga
        "salario": _salario(r.get("salary")),
        "tipo": tipo,
        "descricao": descricao,
    }


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    pais = CODIGOS.get(consulta.get("pais_nome") or "")
    if not pais:
        return [], [f"o startup.jobs não filtra pelo país {consulta.get('pais_nome')}"]
    termo = " ".join(consulta["termo"].replace('"', " ").split())  # a busca já é por frase; aspas zeram o resultado
    desde = (datetime.now(timezone.utc) - timedelta(hours=horas)).strftime("%Y-%m-%dT%H:%M:%SZ")
    args = {"q": termo, "country": pais, "posted_after": desde}
    cidade = "" if consulta["remoto"] else _sem_acento(consulta.get("cidade"))
    if consulta["remoto"]:
        args["workplace_type"] = "remote"
    vagas: list[dict] = []
    cursor = None
    for _ in range(MAX_PAGINAS):
        pagina = {**args, "limit": POR_PAGINA if cidade else min(POR_PAGINA, por_termo)}
        if cursor:
            pagina["cursor"] = cursor
        try:
            dados = chamar("search_jobs", pagina)
        except StartupJobsErro as e:
            return vagas, [str(e), *_avisos()]
        for r in dados.get("jobs") or []:
            loc = r.get("location") if isinstance(r.get("location"), dict) else {}
            if cidade and (r.get("workplace_type") == "remote" or _sem_acento(loc.get("city")) != cidade):
                continue  # o servidor não filtra cidade: ficam as vagas híbridas e presenciais da cidade do usuário
            vaga = _normalizar(r)
            if vaga:
                vagas.append(vaga)
        cursor = dados.get("next_cursor")
        if len(vagas) >= por_termo or not cursor or not dados.get("has_more"):
            break
    return vagas[:por_termo], _avisos()


def ler(vid: str) -> dict:
    """Uma vaga pelo id ("startupjobs-123"), com a descrição, no formato comum. Levanta StartupJobsErro se não
    conseguir."""
    numero = str(vid).removeprefix(f"{NOME}-")
    if not numero.isdigit():
        raise StartupJobsErro("id de vaga do startup.jobs inválido")
    job = chamar("get_job", {"id": int(numero)}).get("job")
    vaga = _normalizar(job) if isinstance(job, dict) else None
    if not vaga or not vaga["titulo"]:
        raise StartupJobsErro("o startup.jobs não devolveu essa vaga (ela pode ter saído do ar)")
    return vaga


def descrever(vaga: dict) -> str:
    """Descrição completa de uma vaga da busca (a lista não traz). Levanta StartupJobsErro se não conseguir."""
    return ler(vaga["id"])["descricao"]


def id_do_link(url: str) -> str | None:
    """Id da vaga ("startupjobs-123") num link do startup.jobs: …startup.jobs/<cargo>-<empresa>-123."""
    partes = urlsplit(str(url or ""))
    host = (partes.hostname or "").lower()
    if host != "startup.jobs" and not host.endswith(".startup.jobs"):
        return None
    segmentos = [s for s in partes.path.split("/") if s]
    m = re.search(r"-(\d+)$", segmentos[0]) if len(segmentos) == 1 else None
    return f"{NOME}-{m.group(1)}" if m else None
