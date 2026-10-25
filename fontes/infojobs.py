"""Fonte InfoJobs: a busca pública do portal brasileiro generalista de vagas (infojobs.com.br), sem login e sem a
conta, as senhas ou os cookies da pessoa (spec 026).

Os termos do InfoJobs não autorizam robôs; a pessoa decidiu tê-lo na busca mesmo assim, como o LinkedIn, e a
ferramenta lê o mínimo. Cada consulta lê uma lista do site, já filtrada pela data (Antiguedad):
- a remota, a lista de home office (vagas-de-emprego-<cargo>-trabalho-home-office.aspx), cujas vagas são todas
  remotas;
- a da cidade, a lista da cidade (vagas-de-emprego-<cargo>-em-<cidade>.aspx), que traz também as vizinhas;
- a do país inteiro, empregos.aspx?palabra=<cargo>.
Fora da remota, vai também o filtro de modelo do site (idw: 1 presencial, 2 home office, 3 híbrido, juntos com
vírgula) com os modelos que a pessoa marcou.
Uma página só por lista: a seguinte não tem endereço próprio. A busca do site é ampla, então fica só a vaga cujo
título bate com o cargo. "Todo Brasil" no local é vaga remota. A descrição vem da página da vaga (os dados
estruturados JobPosting ou, quando a página não os traz, o texto da própria página), só das vagas que vão para o
relatório, no máximo MAX_DESCRICOES por busca.

Pausa sorteada de 3 a 7 segundos entre os pedidos (INFOJOBS_PAUSA=N no .env muda para N a N+4, com N de 3 a 60) e,
no primeiro bloqueio (recusa, limite de consultas ou pedido de login), o InfoJobs fica de fora pelo resto da busca,
sem nova tentativa, e das buscas das 24 horas seguintes (a espera, gravada em .cache/).
"""
from __future__ import annotations

import re
import time  # a pausa (_comum.pausar); os testes trocam o relógio por este módulo
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin

from . import _comum, link

NOME = "infojobs"
PLATAFORMA = "InfoJobs"
AREAS = ("nacional",)  # só vagas do Brasil
TERMOS = ("Consulta não oficial à busca pública do InfoJobs, portal de vagas de todas as áreas no Brasil, sem login. "
          "Os termos do InfoJobs não autorizam robôs: a ferramenta lê o mínimo, com uma pausa de alguns segundos entre "
          "as consultas e, se o InfoJobs limitar, a busca segue sem ele e ele fica 24 horas em espera. "
          "A candidatura é sempre no próprio InfoJobs.")

SITE = "https://www.infojobs.com.br/"
LISTA = SITE + "empregos.aspx"
POR_PAGINA = 20  # o que a lista mostra; a página seguinte não tem endereço próprio
MAX_DESCRICOES = 30  # páginas de vaga lidas por busca; as outras ficam pendentes para a próxima
PAUSA = (3.0, 7.0)  # padrão, sem INFOJOBS_PAUSA
VAR_PAUSA = "INFOJOBS_PAUSA"  # no .env ou no ambiente: segundos de pausa mínima (spec 026)
PAUSA_MIN, PAUSA_FAIXA = 3.0, 4.0  # N de 3 a 60; a pausa é sorteada de N a N + 4
ESPERA = timedelta(hours=24)  # depois de um bloqueio, o InfoJobs fica de fora das buscas
ARQ_ESPERA = Path(__file__).resolve().parent.parent / ".cache" / "infojobs-espera.json"
LIMITE_DESCRICAO = 12000
BLOQUEIO = "o InfoJobs limitou as consultas"
ILEGIVEL = "não consegui ler as vagas do InfoJobs (a página pode ter mudado)"
VAGA = re.compile(r"^(?:https?://(?:www\.)?infojobs\.com\.br)?/vaga-de-[^/?#]*?__(\d+)\.aspx(?:[?#].*)?$", re.I)
# horas da janela -> filtro de data do site (Antiguedad): 2 = 3 dias, 3 = semana, 4 = 15 dias; acima, 5 = mês
ANTIGUIDADE = ((72, 2), (168, 3), (360, 4))
HOME_OFFICE = "trabalho-home-office"  # sufixo da lista de home office do site (vagas-de-emprego-<cargo>-<sufixo>.aspx)
TODO_BRASIL = "todo brasil"  # o local das vagas remotas
IDW = (("presencial", "1"), ("remoto", "2"), ("hibrido", "3"))  # filtro de modelo do site (idw=1,3 junta dois)
MODELOS = (("home office", "remoto"), ("remoto", "remoto"), ("hibrido", "hibrido"), ("presencial", "presencial"))
ICONES = {"money": "salario", "buildings": "modelo", "house-and-building": "modelo", "suitcase": "experiencia",
          "graduate-hat": "escolaridade"}

_estado = {"bloqueado": False, "ultimo": None, "listas": {}, "pausa": None, "avisou_espera": False}


def _esquecer() -> None:
    _estado.update(bloqueado=False, listas={}, pausa=None, avisou_espera=False)  # a pausa é lida de novo a cada busca


_comum.AO_ESQUECER.append(_esquecer)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- pausa, bloqueio e espera

def pausa() -> dict:
    """A pausa entre os pedidos: PAUSA, ou INFOJOBS_PAUSA do .env (ver _comum.pausa_do_env)."""
    return _comum.pausa_do_env(VAR_PAUSA, PAUSA, PAUSA_MIN, faixa=PAUSA_FAIXA)


def aviso_pausa(consultas: int) -> str | None:
    """Aviso do começo da busca com INFOJOBS_PAUSA definida (uma lista por consulta + descrições, no máximo)."""
    return _comum.aviso_pausa(PLATAFORMA, "no InfoJobs", VAR_PAUSA, pausa(),
                              consultas + MAX_DESCRICOES if consultas else 0)


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
    """Para o InfoJobs nesta busca e grava a espera para as próximas (o aviso do bloqueio já diz até quando)."""
    _estado.update(bloqueado=True, avisou_espera=True)
    ate = (_comum.gravar_espera(ARQ_ESPERA, motivo) + ESPERA).isoformat(timespec="minutes")
    return _comum.FonteErro(f"{BLOQUEIO} ({motivo}); em espera até {_comum.ate_quando(ate)}")


def _baixar(url: str) -> str:
    return _comum.baixar_pagina(url, "o InfoJobs", _pausar, _bloquear)


# ---------------------------------------------------------------- leitura dos cards

class _Cards(HTMLParser):
    """Os cards da lista: div.js_vacancyLoad com data-id e data-href; a data em div.js_date (data-value); o título em
    h2.js_vacancyTitle; a empresa no primeiro div.text-body; o local em div.mb-8; salário, modelo, experiência e
    escolaridade nos itens marcados pelo ícone; o trecho do texto em div.text-medium. Texto oculto (hidden) fica de
    fora."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.pilha: list[list] = []  # [tag, campo, ignorar o texto]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "div" and "js_vacancyLoad" in classes:
            self.cards.append({"id": a.get("data-id") or "", "href": a.get("data-href") or ""})
        if not self.cards:
            return
        card = self.cards[-1]
        if "js_date" in classes and a.get("data-value"):
            card["data"] = a["data-value"]
        if tag == "use":
            icone = ICONES.get(str(a.get("xlink:href") or a.get("href") or "").lstrip("#"))
            item = next((e for e in reversed(self.pilha) if e[0] == "div"), None)
            if icone and item is not None and not item[1]:
                item[1] = icone
            return
        if tag in link.VAZIOS:
            return
        campo = None
        if tag == "h2" and "js_vacancyTitle" in classes:
            campo = "titulo"
        elif tag == "div" and classes == ["text-body"] and "empresa" not in card:
            campo = "empresa"
        elif tag == "div" and classes == ["mb-8"] and "local" not in card:
            campo = "local"
        elif tag == "div" and classes == ["text-medium"]:
            campo = "resumo"
        self.pilha.append([tag, campo, "hidden" in a])

    def handle_endtag(self, tag):
        if any(e[0] == tag for e in self.pilha):
            while self.pilha and self.pilha.pop()[0] != tag:
                pass

    def handle_data(self, data):
        if not self.cards or not data.strip():
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


def _local(texto: str) -> tuple[str, str]:
    """("São Paulo", "SP") a partir de "São Paulo - SP"; ("", "") sem local."""
    partes = [p.strip() for p in _espacos(texto).rsplit(" - ", 1)]
    if len(partes) == 2 and re.fullmatch(r"[A-Za-z]{2}", partes[1]):
        return partes[0], partes[1].upper()
    return _espacos(texto), ""


def ler_lista(pagina: str, home_office: bool = False) -> list[dict]:
    """As vagas de uma página de resultados, no formato comum (sem a descrição). home_office: a página é a lista de
    home office do site, cujos cards não mostram o modelo; todas as vagas dela são remotas. "Todo Brasil" no local
    também é vaga remota."""
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
        cidade, uf = _local(c.get("local"))
        texto_modelo = _comum._norm(c.get("modelo"))
        modelo = next((m_ for k, m_ in MODELOS if k in texto_modelo), None)
        if _comum._norm(cidade) == TODO_BRASIL:
            cidade, modelo = "", "remoto"
        elif home_office:
            modelo = "remoto"
        empresa = _espacos(c.get("empresa"))
        if _comum._norm(empresa) in ("empresa confidencial", "confidencial"):
            empresa = "Confidencial"
        data = str(c.get("data") or "")[:10].replace("/", "-")
        salario = _espacos(c.get("salario"))
        detalhes = [_espacos(c.get(k)) for k in ("experiencia", "escolaridade") if c.get(k)]
        v = {
            "id": _comum.ident(NOME, m.group(1)), "plataforma": PLATAFORMA, "titulo": titulo,
            "empresa": empresa or "Empresa não informada",
            "local": f"{cidade}, {uf}" if cidade and uf else cidade or ("Remoto" if modelo == "remoto" else ""),
            "remoto": modelo == "remoto",
            "publicada_em": data if re.fullmatch(r"\d{4}-\d{2}-\d{2}", data) else None,
            "url": urljoin(SITE, c["href"].strip()), "url_candidatura": None,
            "salario": salario if salario and "combinar" not in _comum._norm(salario) else None,
            "tipo": " • ".join(detalhes) or None, "descricao": "",
        }
        if modelo:
            v["modelo_trabalho"] = modelo
        vagas.append(v)
    return vagas


# ---------------------------------------------------------------- busca

def _limite(horas: int) -> str:
    """A data mais antiga da janela (em dias inteiros, como nas outras fontes)."""
    return (_agora() - timedelta(days=max(1, -(-int(horas or 24) // 24)))).date().isoformat()


def antiguidade(horas: int) -> int:
    """O filtro de data do site que cobre a janela (o recorte fino é feito aqui, pela data de cada vaga)."""
    return next((codigo for teto, codigo in ANTIGUIDADE if int(horas or 24) <= teto), 5)


def _slug(texto: str, junta: str) -> str:
    return junta.join(_comum._norm(texto).split())


def url_lista(termo: str, horas: int, cidade: str | None = None, remoto: bool = False,
              modelos: list[str] | None = None) -> str:
    """A lista do cargo: a de home office (consulta remota), a da cidade (que traz também as vizinhas) ou a do país
    inteiro, sempre com o filtro de data do site e, fora da remota, o de modelo (idw) dos modelos marcados."""
    filtro = urlencode({"Antiguedad": antiguidade(horas)})
    cargo = quote(_slug(termo, "+"), safe="+")
    if remoto:
        return f"{SITE}vagas-de-emprego-{cargo}-{HOME_OFFICE}.aspx?{filtro}"
    codigos = [c for m, c in IDW if m in (modelos or [])]
    if codigos and len(codigos) < len(IDW):  # todos os modelos (ou nenhum) = sem filtro
        filtro += "&idw=" + ",".join(codigos)  # vírgula sem escape, como o site monta
    if cidade:
        return f"{SITE}vagas-de-emprego-{cargo}-em-{_slug(cidade, '-')}.aspx?{filtro}"
    return f"{LISTA}?{urlencode({'palabra': termo})}&{filtro}"


def _lista(url: str) -> tuple[list[dict], str | None]:
    """As vagas de uma lista (uma página), guardadas para as outras consultas da mesma lista."""
    if url in _estado["listas"]:
        return _estado["listas"][url]
    vagas, erro = [], None
    try:
        pagina = _baixar(url)
    except _comum.FonteErro as e:
        erro = str(e)
    else:
        vagas = ler_lista(pagina, home_office=f"-{HOME_OFFICE}.aspx" in url or url.endswith("&idw=2"))
        if not vagas and "js_vacancyLoad" in pagina:
            erro = ILEGIVEL
    _estado["listas"][url] = (vagas, erro)
    return vagas, erro


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
        cidade, _, uf = str(vaga.get("local") or "").rpartition(", ")
        return not vaga["remoto"] and _comum.na_regiao(cidade, uf, consulta)
    return True


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    if consulta.get("pais") != "brazil":
        return [], []  # o InfoJobs é só do Brasil
    e = espera()
    if e:  # durante a espera, nenhum pedido; o aviso sai uma vez por busca
        if _estado["avisou_espera"]:
            return [], []
        _estado["avisou_espera"] = True
        return [], [f"{PLATAFORMA} em espera até {_comum.ate_quando(e['ate'])} ({e['motivo']}); a busca seguiu sem ele"]
    termo = " ".join(str(consulta.get("termo") or "").replace('"', " ").split())
    if not termo:
        return [], []
    url = url_lista(termo, horas, consulta.get("cidade"), bool(consulta.get("remoto")), consulta.get("modelos"))
    ja_lida = url in _estado["listas"]
    if _estado["bloqueado"] and not ja_lida:
        return [], []  # depois de um bloqueio, nenhum pedido a mais (a lista já lida continua valendo)
    vagas, erro = _lista(url)
    limite = _limite(horas)
    achadas = [dict(v) for v in vagas if _atende(v, consulta, limite)]
    return achadas[:max(1, por_termo)], [erro] if erro and not ja_lida else []


class _Pagina(HTMLParser):
    """A página da vaga quando ela não traz o JobPosting: título em h2.js_vacancyHeaderTitle, empresa no link de
    div.h4, local e salário em div.text-medium.mb-4, modelo em div.text-medium.small e a descrição em
    p.white-space-pre-line."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.campos: dict[str, list[str]] = {}
        self.pilha: list[list] = []  # [tag, campo]

    def handle_starttag(self, tag, attrs):
        if tag in link.VAZIOS:
            return
        classes = (dict(attrs).get("class") or "").split()
        campo = None
        if tag == "h2" and "js_vacancyHeaderTitle" in classes:
            campo = "titulo"
        elif tag == "div" and "h4" in classes and "empresa" not in self.campos:
            campo = "empresa"
        elif tag == "div" and "text-medium" in classes and "mb-4" in classes:
            campo = "modelo" if "small" in classes else "linha"
        elif tag == "p" and "white-space-pre-line" in classes:
            campo = "descricao"
        if campo:
            self.campos.setdefault(campo, []).append("")
        self.pilha.append([tag, campo])

    def handle_endtag(self, tag):
        if any(e[0] == tag for e in self.pilha):
            while self.pilha and self.pilha.pop()[0] != tag:
                pass

    def handle_data(self, data):
        campo = next((e[1] for e in reversed(self.pilha) if e[1]), None)
        if campo:
            self.campos[campo][-1] += data


def ler_pagina(pagina: str) -> dict:
    """A vaga a partir do HTML da página, para quando ela não traz o JobPosting (ex.: vagas "Todo Brasil"): titulo,
    empresa, local, remoto, salario e descricao (vazios quando a página não diz)."""
    p = _Pagina()
    p.feed(pagina)
    p.close()
    um = lambda k: _espacos((p.campos.get(k) or [""])[0])
    linhas = [_espacos(x) for x in p.campos.get("linha", []) if _espacos(x)]
    local = next((x for x in linhas if "salario" not in _comum._norm(x) and not x.startswith("R$")), "")
    salario = next((x for x in linhas if x.startswith("R$")), None)
    remoto = any(k in _comum._norm(um("modelo")) for k in ("home office", "remoto")) or \
        _comum._norm(local) == TODO_BRASIL
    cidade, uf = _local(local)
    descricao = "\n\n".join(x.strip() for x in p.campos.get("descricao", []) if x.strip())
    empresa = um("empresa")
    return {"plataforma": PLATAFORMA, "titulo": um("titulo"),
            "empresa": "Confidencial" if _comum._norm(empresa) in ("empresa confidencial", "confidencial") else empresa,
            "local": "Remoto" if _comum._norm(local) == TODO_BRASIL else f"{cidade}, {uf}" if uf else cidade,
            "remoto": remoto, "salario": salario, "descricao": descricao[:LIMITE_DESCRICAO]}


def descrever(vaga: dict) -> str:
    """A descrição da página da vaga: os dados estruturados JobPosting ou, quando a página não os traz, o texto da
    própria página (ler_pagina). Depois de um bloqueio ou na espera, devolve o que a vaga já tinha, sem pedido."""
    if parada():
        return vaga.get("descricao") or ""
    url = str(vaga.get("url") or "")
    if not VAGA.match(url):
        raise _comum.FonteErro("link de vaga do InfoJobs inesperado")
    pagina = _baixar(url)
    try:
        texto = link.extrair_jobposting(pagina, PLATAFORMA).get("descricao")
    except link.LinkErro:
        texto = ler_pagina(pagina)["descricao"]
    return (texto or vaga.get("descricao") or "")[:LIMITE_DESCRICAO]


def id_do_link(url: str) -> str | None:
    """O id da vaga ("infojobs-123") a partir do link da página da vaga; None para outros links."""
    m = VAGA.match(str(url or "").strip())
    return _comum.ident(NOME, m.group(1)) if m and str(url).lower().startswith(("http://", "https://")) else None
