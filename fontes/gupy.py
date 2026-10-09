"""Fonte Gupy, pelo servidor MCP público de candidatos da Gupy ("Gupy MCP - Candidato").

O servidor (URL_MCP) é aberto, sem login, e só lê vagas públicas. Aqui ele é chamado
direto por HTTP, no protocolo do MCP (JSON-RPC), então a busca funciona também sem o
Claude Code. A skill consultar-gupy usa o mesmo servidor pelas ferramentas do MCP
(registrado em .mcp.json), para perguntas na conversa.

Sem a integração MCP no assistente (Codex, OpenCode…), as mesmas ferramentas saem pela linha de
comando: python consultar_gupy.py search_jobs term=analista pwd=true limit=10 (veja main()).

Diferenças para o Indeed: não há filtro de data (a busca ordena pela publicação e para
quando as vagas saem da janela), aspas não fazem frase exata, a cidade não tem raio e
só funciona junto com o estado por extenso, e a resposta não traz a cidade da vaga.
"""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

NOME = "gupy"
PLATAFORMA = "Gupy"
URL_MCP = "https://candidates.mcp.api.gupy.io/mcp"
LIMITE_DESCRICAO = 12000
POR_PAGINA = 100  # máximo do servidor
TEMPO = 30
UFS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}
TIPOS = {
    "vacancy_type_effective": "Efetivo (CLT)", "vacancy_legal_entity": "PJ", "vacancy_type_internship": "Estágio",
    "vacancy_type_apprentice": "Jovem aprendiz", "vacancy_type_trainee": "Trainee",
    "vacancy_type_temporary": "Temporário", "vacancy_type_freelancer": "Freelancer",
    "vacancy_type_outsource": "Terceirizado", "vacancy_type_intermittent": "Intermitente",
    "vacancy_type_summer": "Summer job", "vacancy_type_volunteer": "Voluntário", "vacancy_type_associate": "Associado",
    "vacancy_type_talent_pool": "Banco de talentos",
}
MODALIDADES = {"remote": "remoto", "hybrid": "híbrido", "on-site": "presencial"}


class GupyErro(Exception):
    pass


def chamar(ferramenta: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do MCP da Gupy e devolve o campo "data" da resposta."""
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": ferramenta, "arguments": argumentos}}).encode("utf-8")
    req = urllib.request.Request(URL_MCP, data=corpo, headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18", "User-Agent": "meu-proximo-trampo"})
    try:
        with urllib.request.urlopen(req, timeout=TEMPO) as r:
            texto = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise GupyErro(f"o servidor da Gupy respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise GupyErro(f"não consegui falar com a Gupy ({getattr(e, 'reason', e)})") from None
    resposta = None
    for bloco in [x[5:].strip() for x in texto.splitlines() if x.startswith("data:")] or [texto]:  # SSE ou JSON puro
        try:
            msg = json.loads(bloco, strict=False)
        except ValueError:
            continue
        if isinstance(msg, dict) and msg.get("id") == 1:
            resposta = msg
    if resposta is None:
        raise GupyErro("resposta inesperada do servidor da Gupy")
    if "error" in resposta:
        raise GupyErro(f"a Gupy recusou a consulta ({(resposta['error'] or {}).get('message')})")
    resultado = resposta.get("result") or {}
    conteudo = "".join(c.get("text", "") for c in resultado.get("content") or [] if c.get("type") == "text")
    if resultado.get("isError"):
        raise GupyErro(f"a Gupy recusou a consulta ({conteudo[:300]})")
    try:
        return json.loads(conteudo, strict=False)["data"]
    except (ValueError, KeyError, TypeError):
        raise GupyErro("resposta inesperada do servidor da Gupy") from None


def _publicada(r: dict) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(r.get("publishedDate") or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _normalizar(r: dict, consulta: dict | None = None) -> dict | None:
    if not r.get("id"):
        return None
    modalidade = r.get("workplaceType") or ""
    remoto = modalidade == "remote"
    if remoto:
        local = f"Remoto ({r['country']})" if r.get("country") else "Remoto"
    elif consulta and consulta.get("cidade"):  # a Gupy não devolve a cidade; esta veio da busca na cidade
        local = ", ".join(x for x in (consulta["cidade"], consulta.get("estado")) if x)
    else:
        local = r.get("country") or ""
    tipo = TIPOS.get(r.get("type") or "")
    prazo = str(r.get("applicationDeadline") or "")[:10]
    # o que a Gupy informa em campos próprios vai no fim da descrição, para a análise e para o dashboard
    extras = [f"modelo {MODALIDADES[modalidade]}" if modalidade in MODALIDADES else "", tipo or "",
              f"inscrições até {prazo}" if prazo else "", "aberta a PCD" if r.get("disabilities") else ""]
    descricao = (r.get("description") or "").strip()[:LIMITE_DESCRICAO]
    if any(extras):
        descricao = (descricao + "\n\nNa Gupy: " + " · ".join(x for x in extras if x)).strip()
    empresa = "Empresa confidencial" if r.get("isConfidentialCareerPage") else (r.get("careerPageName") or "").strip()
    salario = r.get("salary") if isinstance(r.get("salary"), dict) else {}
    publicada = _publicada(r)
    return {
        "id": f"gupy-{r['id']}",
        "plataforma": PLATAFORMA,
        "titulo": (r.get("name") or "").strip(),
        "empresa": empresa or "Empresa não informada",
        "local": local,
        "remoto": remoto,
        "publicada_em": publicada.astimezone().date().isoformat() if publicada else None,
        "url": r.get("jobUrl") or "",
        "url_candidatura": None,  # o link da vaga já é a página de candidatura
        "salario": salario.get("label") if salario.get("status") not in (None, "not_disclosed") else None,
        "tipo": tipo,
        "descricao": descricao,
    }


def _argumentos(consulta: dict) -> dict:
    termo = " ".join(consulta["termo"].replace('"', " ").split())  # a Gupy não tem busca por frase exata
    args = {"term": termo, "sortBy": "publishedDate", "sortOrder": "desc"}
    pais = consulta.get("pais_nome")
    if pais:
        args["country"] = pais
    if consulta["remoto"]:
        args["workplaceTypes"] = "remote"
    elif consulta.get("cidade"):
        args["city"] = consulta["cidade"]
        estado = consulta.get("estado") or ""
        if pais == "Brasil":
            estado = UFS.get(estado.upper(), estado)
        if estado:
            args["state"] = estado  # sem o estado, o filtro de cidade da Gupy quase não acha nada
        args["workplaceTypes"] = "hybrid,on-site"
    return args


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    args = _argumentos(consulta)
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    vagas: list[dict] = []
    offset = 0
    while len(vagas) < por_termo:
        tamanho = min(POR_PAGINA, por_termo - len(vagas))
        try:
            dados = chamar("search_jobs", {**args, "limit": tamanho, "offset": offset})
        except GupyErro as e:
            return vagas, [str(e)]
        pagina = dados.get("data") or []
        for r in pagina:
            publicada = _publicada(r)
            if publicada and publicada < limite:  # ordenada pela publicação: daqui em diante é tudo mais antigo
                return vagas, []
            vaga = _normalizar(r, consulta)
            if vaga:
                vagas.append(vaga)
        offset += len(pagina)
        if len(pagina) < tamanho or offset >= ((dados.get("pagination") or {}).get("total") or 0):
            break
    return vagas[:por_termo], []


def ler(vid: str) -> dict:
    """Uma vaga pelo id ("gupy-12345"), no formato comum. Levanta GupyErro se não conseguir."""
    numero = str(vid).removeprefix("gupy-")
    if not numero.isdigit():
        raise GupyErro("id de vaga da Gupy inválido")
    dados = chamar("get_job_by_id", {"id": int(numero)})
    vaga = _normalizar(dados) if isinstance(dados, dict) else None
    if not vaga or not vaga["titulo"]:
        raise GupyErro("a Gupy não devolveu essa vaga (ela pode ter saído do ar)")
    return vaga


def id_do_link(url: str) -> str | None:
    """Id da vaga ("gupy-12345") num link da Gupy: …gupy.io/jobs/12345 ou …gupy.io/job/<base64 de {"jobId": 12345}>."""
    partes = urlsplit(str(url or ""))
    host = (partes.hostname or "").lower()
    if host != "gupy.io" and not host.endswith(".gupy.io"):
        return None
    segmentos = [s for s in partes.path.split("/") if s]
    for anterior, seg in zip(segmentos, segmentos[1:]):
        if anterior == "jobs" and seg.isdigit():
            return f"gupy-{seg}"
        if anterior == "job":
            try:
                dados = json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
            except ValueError:
                continue
            if isinstance(dados, dict) and str(dados.get("jobId") or "").isdigit():
                return f"gupy-{dados['jobId']}"
    return None


# ---------------------------------------------------------------- linha de comando

FERRAMENTAS = ("search_jobs", "get_job_by_id", "list_companies", "get_company_by_id")
USO = ("uso: python consultar_gupy.py <ferramenta> [chave=valor …]  (ou um único JSON)\n"
       "ferramentas: " + ", ".join(FERRAMENTAS) + "\n"
       "ex.: python consultar_gupy.py search_jobs term=analista pwd=true limit=10\n"
       "     python consultar_gupy.py get_job_by_id id=12345")


def argumentos_da_linha(itens: list[str]) -> dict:
    """Argumentos das ferramentas a partir da linha de comando: chave=valor (true/false → booleano,
    inteiro → número, o resto texto) ou um único objeto JSON."""
    if len(itens) == 1 and itens[0].lstrip().startswith("{"):
        dados = json.loads(itens[0])
        if not isinstance(dados, dict):
            raise ValueError("o JSON precisa ser um objeto")
        return dados
    args = {}
    for item in itens:
        chave, sep, valor = item.partition("=")
        chave = chave.strip()
        if not sep or not chave:
            raise ValueError(f"argumento inválido: {item!r} (use chave=valor)")
        baixo = valor.strip().lower()
        if baixo in ("true", "false"):
            args[chave] = baixo == "true"
        elif re.fullmatch(r"-?\d+", valor.strip()):
            args[chave] = int(valor)
        else:
            args[chave] = valor
    return args


def main(argv: list[str] | None = None) -> int:
    """Consulta a Gupy sem a integração MCP do assistente e imprime o JSON da resposta."""
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(USO)
        return 0 if argv else 2
    if argv[0] not in FERRAMENTAS:
        print(f"ferramenta desconhecida: {argv[0]} (use: {', '.join(FERRAMENTAS)})", file=sys.stderr)
        return 2
    try:
        dados = chamar(argv[0], argumentos_da_linha(argv[1:]))
    except (ValueError, GupyErro) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps(dados, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
