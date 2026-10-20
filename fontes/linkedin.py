"""Fonte LinkedIn: a busca pública de vagas (a mesma que aparece para quem não entrou na conta), sem login e sem a
conta, as senhas ou os cookies da pessoa.

Os cargos de um grupo de filtros.consultas vão numa consulta só, ligados por OR (até 3 páginas), com o local (país,
cidade com raio ou "Worldwide") e o modelo de trabalho do grupo; a janela de tempo e os tipos de emprego vão como
filtro do próprio LinkedIn. A descrição vem da página pública da vaga, só das vagas que vão para o relatório,
no máximo MAX_DESCRICOES por busca; as outras ficam pendentes para a próxima. Pausa de 3 a 7 segundos entre os
pedidos (LINKEDIN_PAUSA=N no .env aumenta para N a N+4, com N de 3 a 60) e, no primeiro bloqueio (limite de consultas ou pedido de login), o LinkedIn fica de fora pelo resto da busca,
sem nova tentativa (constituição, princípio VI), e também das buscas das 6 horas seguintes (a espera, gravada em
.cache/). O aviso traz o motivo provável.

Cada pedido ao LinkedIn (busca, descrição, link e post colados) entra no registro .cache/linkedin-pedidos.json
(spec 024): quando, de onde, o quê, a resposta e os segundos desde o pedido anterior, sem cargos nem endereços.
`vagas.py pedidos-linkedin` resume o registro e mostra o que veio antes de cada bloqueio.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

import segredos  # segredos.py, na raiz: o .env (LINKEDIN_PAUSA)

from . import _comum, link

NOME = "linkedin"
PLATAFORMA = "LinkedIn"
AREAS = ("nacional", "internacional")
POR_PAIS = True
GLOBAL = True  # também na consulta "mundo todo" (Worldwide)
TERMOS = ("Consulta não oficial à busca pública do LinkedIn, sem login e sem a sua conta. Há uma pausa de alguns "
          "segundos entre as consultas e, se o LinkedIn limitar, a busca segue sem ele e ele fica 6 horas em espera. "
          "A candidatura é sempre no próprio LinkedIn.")

BUSCA = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
VAGA = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
PAUSA = (3.0, 7.0)  # padrão, sem LINKEDIN_PAUSA
VAR_PAUSA = "LINKEDIN_PAUSA"  # no .env ou no ambiente: segundos de pausa mínima (spec 017)
PAUSA_MIN, PAUSA_MAX, PAUSA_FAIXA = 3.0, 60.0, 4.0  # N fica entre 3 e 60; a pausa é sorteada de N a N + 4
POR_PAGINA = 10  # o que a busca pública devolve por página
MAX_PAGINAS = 1  # uma página por consulta: poucas consultas, menos risco de bloqueio
MAX_PAGINAS_AGRUPADA = 3  # a consulta com os cargos juntos (AGRUPAR) lê até 3 páginas
AGRUPAR = True  # os cargos de um grupo numa consulta só, ligados por OR
MAX_DESCRICOES = 20  # descrições lidas por busca; as outras ficam pendentes para a próxima
ESPERA = timedelta(hours=6)  # depois de um bloqueio, o LinkedIn fica de fora das buscas
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "linkedin-espera.json"
ARQ_PEDIDOS = ARQ_ESPERA.with_name("linkedin-pedidos.json")  # o registro dos pedidos (spec 024)
MAX_PEDIDOS = 300  # o registro guarda os últimos N pedidos
NOVA_RODADA = timedelta(minutes=30)  # no resumo, um intervalo maior que este começa outra rodada de pedidos
TEMPO = 20
LIMITE_BYTES = 3_000_000
LIMITE_DESCRICAO = 12000
BLOQUEIO = "o LinkedIn limitou as consultas"
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

_estado = {"bloqueado": False, "ultimo": None, "avisou_espera": False, "pausa": None}
MOTIVOS = {429: "excesso de pedidos",
           999: "recusa automática, costuma ser a rede: VPN, Wi-Fi corporativo ou internet compartilhada"}


def _esquecer() -> None:
    _estado.update(bloqueado=False, avisou_espera=False, pausa=None)  # a pausa é lida de novo a cada busca


_comum.AO_ESQUECER.append(_esquecer)


def _num(n: float) -> str:
    return f"{n:g}".replace(".", ",")


def pausa() -> dict:
    """{"faixa": (mín, máx) em segundos, "definida": LINKEDIN_PAUSA está no .env ou no ambiente, "ajuste": motivo
    quando o valor foi trocado pelo limite ou ignorado, ou ""}. Sem a variável, vale PAUSA."""
    bruto = segredos.ler(VAR_PAUSA)
    if not bruto:
        return {"faixa": PAUSA, "definida": False, "ajuste": ""}
    try:
        n = float(bruto.replace(",", "."))
        if not math.isfinite(n):
            raise ValueError
    except ValueError:
        return {"faixa": PAUSA, "definida": True,
                "ajuste": f"o valor de {VAR_PAUSA} ({bruto[:20]}) não é um número e foi ignorado"}
    ajuste = ""
    if n < PAUSA_MIN:
        n, ajuste = PAUSA_MIN, f"{VAR_PAUSA} abaixo do mínimo de {_num(PAUSA_MIN)} segundos; vale o mínimo"
    elif n > PAUSA_MAX:
        n, ajuste = PAUSA_MAX, f"{VAR_PAUSA} acima do máximo de {_num(PAUSA_MAX)} segundos; vale o máximo"
    return {"faixa": (n, n + PAUSA_FAIXA), "definida": True, "ajuste": ajuste}


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca quando LINKEDIN_PAUSA está definida: a pausa em uso e o tempo de pausa estimado
    (consultas do LinkedIn × páginas + descrições, no máximo)."""
    p = pausa()
    if not p["definida"] or not consultas:
        return None
    mn, mx = p["faixa"]
    pedidos = consultas * (MAX_PAGINAS_AGRUPADA if AGRUPAR else MAX_PAGINAS) + MAX_DESCRICOES
    minutos = max(1, round(pedidos * (mn + mx) / 2 / 60))
    texto = (f"LinkedIn: pausa de {_num(mn)} a {_num(mx)} s entre os pedidos ({VAR_PAUSA}), "
             f"até cerca de {minutos} min só de pausa no LinkedIn.")
    return f"{texto} Atenção: {p['ajuste']}." if p["ajuste"] else texto


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Redirecionamento (para login, cadastro, verificação) não é seguido: vira erro e conta como bloqueio."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _pausar() -> None:
    if _estado["pausa"] is None:
        _estado["pausa"] = pausa()["faixa"]
    if _estado["ultimo"] is not None:
        espera = _estado["ultimo"] + random.uniform(*_estado["pausa"]) - time.monotonic()
        if espera > 0:
            time.sleep(espera)
    _estado["ultimo"] = time.monotonic()


def _hora(iso: str) -> str:
    return str(iso)[11:16]


def _motivo(codigo: int) -> str:
    if codigo in MOTIVOS:
        return MOTIVOS[codigo]
    if 300 <= codigo < 400:
        return "pediu login"
    return f"acesso negado (código {codigo})"


def _bloquear(motivo: str) -> _comum.FonteErro:
    """Para o LinkedIn nesta busca e grava a espera para as próximas (se não der para gravar, segue sem ela)."""
    _estado["bloqueado"] = True
    agora = datetime.now()
    try:
        ARQ_ESPERA.parent.mkdir(parents=True, exist_ok=True)
        ARQ_ESPERA.write_text(json.dumps({"desde": agora.isoformat(timespec="seconds"), "motivo": motivo},
                                         ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    ate = (agora + ESPERA).isoformat(timespec="minutes")
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); em espera até {_hora(ate)}")


def espera(agora: datetime | None = None) -> dict | None:
    """{"ate", "motivo"} nas ESPERA horas depois do último bloqueio; None fora delas ou sem arquivo legível."""
    agora = agora or datetime.now()
    try:
        dados = json.loads(ARQ_ESPERA.read_text(encoding="utf-8"))
        desde = datetime.fromisoformat(str(dados["desde"]))
    except (OSError, ValueError, TypeError, KeyError):
        return None
    ate = min(desde, agora) + ESPERA  # hora gravada no futuro (relógio mudou) vale como agora
    if agora >= ate:
        return None
    return {"ate": ate.isoformat(timespec="minutes"), "motivo": str(dados.get("motivo") or "bloqueio")}


def parada() -> bool:
    """Bloqueou nesta busca ou está em espera: a vaga sem texto fica pendente."""
    return _estado["bloqueado"] or espera() is not None


# ---------------------------------------------------------------- registro dos pedidos (spec 024)

_TRAVA_PEDIDOS = threading.Lock()
_origem = threading.local()  # a origem vale por thread: no servidor, a busca e o Forçar verificar rodam em paralelo


@contextmanager
def origem(nome: str):
    """Marca no registro os pedidos ao LinkedIn feitos nesta thread dentro do bloco (busca, completar, forcar)."""
    anterior = getattr(_origem, "nome", None)
    _origem.nome = nome
    try:
        yield
    finally:
        _origem.nome = anterior


def _ler_pedidos() -> list[dict]:
    try:
        dados = json.loads(ARQ_PEDIDOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [d for d in dados if isinstance(d, dict)] if isinstance(dados, list) else []


def registrar_pedido(tipo: str, resposta: int | str, de: str | None = None) -> None:
    """Uma linha no registro: quando, de onde (`de` ou a origem da thread), o quê (pagina, descricao, link, post), a
    resposta (código HTTP ou "rede") e os segundos desde o pedido anterior. Sem cargos nem endereços. Se não der
    para gravar, segue sem o registro: ele só ajuda a entender os bloqueios."""
    agora = datetime.now()
    with _TRAVA_PEDIDOS:
        lista = _ler_pedidos()
        desde = None
        if lista:
            try:
                desde = round((agora - datetime.fromisoformat(lista[-1]["em"])).total_seconds(), 1)
            except (KeyError, TypeError, ValueError):
                pass
        lista.append({"em": agora.isoformat(timespec="seconds"), "origem": de or getattr(_origem, "nome", None) or "outro",
                      "tipo": tipo, "resposta": resposta, "desde_anterior_s": desde})
        try:
            ARQ_PEDIDOS.parent.mkdir(parents=True, exist_ok=True)
            tmp = ARQ_PEDIDOS.with_name(ARQ_PEDIDOS.name + ".tmp")
            tmp.write_text(json.dumps(lista[-MAX_PEDIDOS:], ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, ARQ_PEDIDOS)
        except OSError:
            pass


def _e_bloqueio(resposta) -> bool:
    return isinstance(resposta, int) and (resposta in (429, 999, 401, 403) or 300 <= resposta < 400)


def resumo_pedidos(horas: int = 48, agora: datetime | None = None) -> str:
    """O registro das últimas `horas`, em rodadas (pedidos separados por menos de NOVA_RODADA): quantos pedidos de
    cada tipo, as respostas e, em cada bloqueio, em que pedido ele veio, quanto tempo depois do anterior e quantos
    pedidos houve nas 24 horas antes dele."""
    agora = agora or datetime.now()
    todos = []
    for p in _ler_pedidos():
        try:
            todos.append({**p, "_em": datetime.fromisoformat(p["em"])})
        except (KeyError, TypeError, ValueError):
            continue
    janela = [p for p in todos if p["_em"] >= agora - timedelta(hours=horas)]
    if not janela:
        return (f"Nenhum pedido ao LinkedIn registrado nas últimas {horas} horas "
                f"(o registro começa a valer depois desta atualização).")
    rodadas: list[list[dict]] = []
    for p in janela:
        if rodadas and p["_em"] - rodadas[-1][-1]["_em"] <= NOVA_RODADA:
            rodadas[-1].append(p)
        else:
            rodadas.append([p])
    linhas = [f"Pedidos ao LinkedIn nas últimas {horas} horas: {len(janela)}, em {len(rodadas)} rodada(s)."]
    for r in rodadas:
        tipos: dict[str, int] = {}
        for p in r:
            tipos[p["tipo"]] = tipos.get(p["tipo"], 0) + 1
        origens = ", ".join(dict.fromkeys(p["origem"] for p in r))
        respostas = ", ".join(f"{k}: {v}" for k, v in _contar(str(p["resposta"]) for p in r).items())
        linhas.append(f"- {r[0]['_em']:%d/%m %H:%M}–{r[-1]['_em']:%H:%M} ({origens}): "
                      + ", ".join(f"{v} {k}" for k, v in tipos.items()) + f"; respostas {respostas}")
        for i, p in enumerate(r, 1):
            if not _e_bloqueio(p["resposta"]):
                continue
            antes = sum(1 for q in todos if p["_em"] - timedelta(hours=24) <= q["_em"] < p["_em"])
            intervalo = p.get("desde_anterior_s")
            linhas.append(f"  bloqueio {p['resposta']} ({_motivo(p['resposta'])}) no {i}º pedido da rodada "
                          f"({p['tipo']}, {p['origem']})"
                          + (f", {intervalo:g} s depois do anterior" if isinstance(intervalo, (int, float)) else "")
                          + f"; {antes} pedido(s) ao LinkedIn nas 24 h antes")
    return "\n".join(linhas)


def _contar(itens) -> dict[str, int]:
    saida: dict[str, int] = {}
    for i in itens:
        saida[i] = saida.get(i, 0) + 1
    return saida


def _baixar(url: str) -> str:
    """Um pedido ao LinkedIn: sem cookies, sem seguir redirecionamento e sem nova tentativa. Entra no registro."""
    _pausar()
    tipo = "pagina" if url.startswith(BUSCA) else "descricao"
    req = urllib.request.Request(url, headers={"User-Agent": link.NAVEGADOR, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    try:
        with urllib.request.build_opener(_SemRedirecionar).open(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            charset = r.headers.get_content_charset() or "utf-8"
            status = getattr(r, "status", None)
        registrar_pedido(tipo, status if isinstance(status, int) else 200)
    except urllib.error.HTTPError as e:
        registrar_pedido(tipo, e.code)
        if e.code in (429, 999, 401, 403) or 300 <= e.code < 400:
            raise _bloquear(_motivo(e.code)) from None
        raise _comum.FonteErro(f"o LinkedIn respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        registrar_pedido(tipo, "rede")
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
    termo = str(consulta["termo"])  # a combinada mantém as aspas de cada cargo; um cargo só, como sempre
    p = {"keywords": termo if consulta.get("agrupada") else termo.strip('"'), "location": local}
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
    esp = espera()
    if esp:  # bloqueio recente: nenhum pedido; o aviso sai uma vez por busca
        if _estado["avisou_espera"]:
            return [], []
        _estado["avisou_espera"] = True
        return [], [f"LinkedIn em espera até {_hora(esp['ate'])} ({esp['motivo']}); ficou de fora desta busca"]
    params = parametros(consulta, horas)
    modelos = consulta.get("modelos") or []
    vagas: list[dict] = []
    inicio = 0
    for _ in range(MAX_PAGINAS_AGRUPADA if consulta.get("agrupada") else MAX_PAGINAS):
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
    vaga["tipo_emprego"]. Depois de um bloqueio ou na espera, devolve o que a vaga já tinha, sem pedido."""
    if parada():
        return vaga.get("descricao") or ""
    numero = str(vaga["id"]).removeprefix("li-")
    lida = link.vaga_linkedin(numero, _baixar(VAGA.format(numero)))
    tipos = tipo_emprego(lida.get("tipo") or "")
    if tipos:
        vaga["tipo_emprego"] = tipos
    return (lida.get("descricao") or vaga.get("descricao") or "")[:LIMITE_DESCRICAO]
