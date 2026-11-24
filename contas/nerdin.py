"""Nerdin: a página "Minhas candidaturas" (vagas_candidato.php?id=<candidato>), que só abre logada e é montada no
servidor, sem API. O módulo pega o HTML da página aberta na janela (outerHTML) e lê os cartões em Python; nenhum
JavaScript da ferramenta mexe na página, e nada é clicado (em especial "Cancelar candidatura").

Como o HTML exato não é conhecido, o leitor é tolerante: o cartão é o menor elemento com "Acompanhe sua candidatura" e
"Inscrito em", e os campos saem de ícones, rótulos e textos, não de classes fixas. Os termos da Nerdin não permitem
acesso automatizado; a decisão está registrada na spec 059.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import date
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

import segredos

from . import PASTA, PortalErro, lida

NOME = "nerdin"
PLATAFORMA = "Nerdin"
ATIVO = True
ICONE = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="2" y="2" width="20" height="20" '
         'rx="6" fill="currentColor" opacity=".15"/><text x="12" y="16.5" text-anchor="middle" font-size="12" '
         'font-weight="700" fill="currentColor">N</text></svg>')
SITE = "https://www.nerdin.com.br"
URL_CANDIDATURAS = SITE + "/vagas_candidato.php"
HOST_LOGIN = "login.php"
ORIGENS = ("https://www.nerdin.com.br", "https://nerdin.com.br")
AVISO_LOGIN = ("Os termos da Nerdin não permitem acesso automatizado. A ferramenta só lê a sua página de "
               "candidaturas, no clique, sem clicar em nada; o login é seu, na janela.")
MAX_PAGINAS = 5
VAR_URL = "NERDIN_CANDIDATURAS"
GUARDADO = PASTA / "nerdin.json"

ENDERECO = re.compile(r"^https://(?:www\.)?nerdin\.com\.br/vagas_candidato\.php\?id=\d+$", re.I)
HREF_MENU = re.compile(r"""href\s*=\s*["']([^"']*vagas_candidato\.php\?id=(\d+)[^"']*)["']""", re.I)
HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
VAGA_PHP = re.compile(r"vaga\.php\?id=(\d+)", re.I)
VAGA_CURTA = re.compile(r"^https://(?:www\.)?nerdin\.com\.br/vaga/(\d+)\.php(?:[?#]|$)", re.I)  # "Ver Detalhes"
INSCRITO = re.compile(r"Inscrito em:?\s*(\d{1,2})/(\d{1,2})/(\d{4})", re.I)
VOID = {"br", "img", "input", "hr", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"}
ICONES_EMPRESA = ("building",)
ICONES_LOCAL = ("map-marker", "map-pin", "location")
FEITO = ("success", "done", "complet", "concluido", "check", "active", "ativo")
ROTULOS = ("Inscrito", "Currículo recebido", "Perfil visualizado", "Em análise", "Processo aberto",
           "Não selecionado", "Processo encerrado")
BOTOES = ("ver detalhes", "cancelar candidatura")
TRILHA = "acompanhe sua candidatura"
VAZIA = ("nenhuma candidatura", "nao se inscreveu")
BLOQUEIO = ("captcha", "acesso negado", "too many requests")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)).casefold()


def _limpo(texto: str) -> str:
    return " ".join(str(texto or "").split())


def logado(url: str) -> bool:
    p = urlsplit(url or "")
    return (p.hostname or "").lower() in ("nerdin.com.br", "www.nerdin.com.br") and "login" not in p.path.lower()


def endereco_valido(url: str) -> bool:
    return bool(ENDERECO.match(str(url or "").strip()))


# ---------------------------------------------------------------- árvore do HTML

class _No:
    __slots__ = ("tag", "attrs", "filhos", "pai")

    def __init__(self, tag: str, attrs: dict, pai: "_No | None"):
        self.tag, self.attrs, self.filhos, self.pai = tag, attrs, [], pai

    def classe(self) -> str:
        return (self.attrs.get("class") or "").lower()

    def pedacos(self) -> list[str]:
        out: list[str] = []
        for f in self.filhos:
            if isinstance(f, str):
                out.append(f)
            else:
                out.extend(f.pedacos())
        return out

    def texto(self) -> str:
        return _limpo(" ".join(self.pedacos()))

    def descendentes(self):
        for f in self.filhos:
            if isinstance(f, _No):
                yield f
                yield from f.descendentes()


class _Arvore(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = _No("raiz", {}, None)
        self.atual = self.raiz
        self.ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignorar += 1
            return
        no = _No(tag, {k: (v or "") for k, v in attrs}, self.atual)
        self.atual.filhos.append(no)
        if tag not in VOID:
            self.atual = no

    def handle_startendtag(self, tag, attrs):
        if tag in ("script", "style"):
            return
        self.atual.filhos.append(_No(tag, {k: (v or "") for k, v in attrs}, self.atual))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignorar = max(0, self.ignorar - 1)
            return
        n = self.atual
        while n is not self.raiz and n.tag != tag:
            n = n.pai
        if n is not self.raiz:
            self.atual = n.pai

    def handle_data(self, data):
        if not self.ignorar and _limpo(data):
            self.atual.filhos.append(_limpo(data))


def _arvore(html: str) -> _No:
    a = _Arvore()
    a.feed(html or "")
    a.close()
    return a.raiz


# ---------------------------------------------------------------- cartões

def _menor_com(no: _No, achar) -> list[_No]:
    """Os menores elementos cujo texto passa em `achar` (nenhum filho passa)."""
    if not achar(no.texto()):
        return []
    achados = [x for f in no.filhos if isinstance(f, _No) for x in _menor_com(f, achar)]
    return achados or [no]


def _cartao_ok(texto: str) -> bool:
    t = _sem_acento(texto)
    return TRILHA in t and "inscrito em" in t


def _tem_icone(no: _No, nomes: tuple[str, ...]) -> bool:
    return any(n in no.classe() for n in nomes)


def _ao_lado_do_icone(card: _No, nomes: tuple[str, ...]) -> str:
    outros = ICONES_EMPRESA + ICONES_LOCAL
    for ic in card.descendentes():
        if not _tem_icone(ic, nomes) or ic.pai is None:
            continue
        atual = ic
        for _ in range(3):
            pai = atual.pai
            if pai is None:
                break
            achados, depois = [], False
            for f in pai.filhos:
                if f is atual:
                    depois = True
                    continue
                if not depois:
                    continue
                if isinstance(f, _No) and any(_tem_icone(x, outros) for x in [f, *f.descendentes()]):
                    break
                achados.append(f if isinstance(f, str) else f.texto())
            texto = _limpo(" ".join(achados))
            if texto:
                return texto
            atual = pai
    return ""


def _marcado(no: _No) -> bool:
    return any(m in no.classe() for m in FEITO) or any(
        any(m in d.classe() for m in FEITO) for d in no.descendentes())


def _passos(card: _No) -> list[dict]:
    achados: dict[str, bool] = {}
    ordem: list[str] = []

    def visita(no: _No):
        for f in no.filhos:
            if isinstance(f, str):
                for rotulo in ROTULOS:
                    if _sem_acento(f) == _sem_acento(rotulo) and rotulo not in achados:
                        topo = no
                        while topo.pai is not None and topo.pai is not card and topo.pai.texto() == f:
                            topo = topo.pai
                        achados[rotulo] = _marcado(topo)
                        ordem.append(rotulo)
            else:
                visita(f)

    visita(card)
    return [{"rotulo": r, "feito": achados[r]} for r in ordem]


def _link_da_vaga(card: _No) -> tuple[str, str]:
    from fontes import nerdin as fonte

    for a in [card, *card.descendentes()]:
        href = a.attrs.get("href") if a.tag == "a" else None
        if not href:
            continue
        absoluto = urljoin(SITE + "/", unescape(href))
        ident = fonte.id_do_link(absoluto)
        if ident:
            return ident, absoluto
        m = VAGA_CURTA.match(absoluto)
        if m:
            return f"nerdin-{m.group(1)}", f"{SITE}/vaga/{m.group(1)}.php"
        m = VAGA_PHP.search(absoluto)
        if m:
            return f"nerdin-{m.group(1)}", f"{SITE}/vaga.php?id={m.group(1)}"
    return "", ""


def _cartao(card: _No) -> dict | None:
    titulo_no = next((d for d in card.descendentes() if d.tag in ("h1", "h2", "h3", "h4", "h5", "h6")
                      and d.texto() and _sem_acento(d.texto()) != TRILHA), None)
    if titulo_no is None:
        return None
    titulo = titulo_no.texto()
    pedacos = [_limpo(p) for p in card.pedacos() if _limpo(p)]
    selo = next((p for p in pedacos if _sem_acento(p) in ("aberta", "expirada")), "")
    m = INSCRITO.search(card.texto())
    inscrito = None
    if m:
        try:
            inscrito = date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            pass
    empresa = _ao_lado_do_icone(card, ICONES_EMPRESA)
    local = _ao_lado_do_icone(card, ICONES_LOCAL)

    # a trilha: o que vem depois de "Acompanhe sua candidatura", sem os botões
    antes, trilha, na_trilha = [], [], False
    for p in pedacos:
        if _sem_acento(p) == TRILHA:
            na_trilha = True
        elif na_trilha:
            if _sem_acento(p) not in BOTOES:
                trilha.append(p)
        else:
            antes.append(p)
    if not empresa or not local:
        depois = antes[antes.index(titulo) + 1:] if titulo in antes else antes
        sobras = [p for p in depois if p not in (selo, empresa, local) and not _sem_acento(p).startswith("inscrito")
                  and _sem_acento(p) not in BOTOES]
        empresa = empresa or (sobras.pop(0) if sobras else "")
        local = local or (sobras.pop(0) if sobras else "")
    ident, url = _link_da_vaga(card)
    return {"titulo": titulo, "empresa": empresa, "local": local, "selo": selo, "inscrito": inscrito,
            "passos": _passos(card), "trilha": trilha, "id": ident, "url": url}


def cartoes(html: str) -> list[dict]:
    raiz = _arvore(html)
    achados = _menor_com(raiz, _cartao_ok) if _cartao_ok(raiz.texto()) else []
    lidos = [c for c in (_cartao(n) for n in achados if n is not raiz) if c]
    return lidos


# ---------------------------------------------------------------- tradução

def traduzir(cartao: dict, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    passos = cartao.get("passos") or []
    rotulos = {_sem_acento(p["rotulo"]) for p in passos}
    expirada = _sem_acento(cartao.get("selo") or "") == "expirada"
    feitos = [p["rotulo"] for p in passos if p.get("feito")]
    avisos: list[str] = []
    etapa, resultado, ativa = None, None, False
    if "nao selecionado" in rotulos:
        status, etapa, resultado = "Não selecionado", "encerrada", "nao_aprovado"
    elif rotulos & {"em analise", "processo aberto"}:
        status = feitos[-1] if feitos else "Inscrito"
        etapa = "aplicada"
        if expirada:
            avisos.append("vaga expirada na Nerdin")
        ativa = not expirada
    elif "processo encerrado" in rotulos:
        status = "Processo encerrado"
        avisos.append("processo encerrado na Nerdin")
    else:
        status = _limpo(" · ".join(cartao.get("trilha") or [])) or (feitos[-1] if feitos else "Inscrito")
        avisos.append(f"status na Nerdin: {status}")
    return lida(NOME, PLATAFORMA, id=cartao.get("id") or "", titulo=cartao.get("titulo"),
                empresa=cartao.get("empresa"), local=cartao.get("local"), url=cartao.get("url") or "",
                status=status, etapa=etapa, resultado=resultado, data=cartao.get("inscrito") or hoje.isoformat(),
                avisos=avisos, ativa=ativa)


# ---------------------------------------------------------------- leitura

def link_do_menu(html: str) -> str | None:
    for m in HREF_MENU.finditer(html or ""):
        url = f"{SITE}/vagas_candidato.php?id={m.group(2)}"
        if endereco_valido(url):
            return url
    return None


def _endereco_conhecido() -> str:
    url = (segredos.ler(VAR_URL) or "").strip()
    if endereco_valido(url):
        return url
    try:
        guardado = str(json.loads(GUARDADO.read_text(encoding="utf-8")).get("url") or "")
    except (OSError, ValueError, AttributeError):
        guardado = ""
    return guardado if endereco_valido(guardado) else URL_CANDIDATURAS


def _guardar(url: str) -> None:
    try:
        GUARDADO.parent.mkdir(parents=True, exist_ok=True)
        GUARDADO.write_text(json.dumps({"url": url}), encoding="utf-8")
    except OSError:
        pass


PARAM_PAGINA = {"pagina", "page", "pag", "pg", "p"}


def _paginas(html: str, base: str, visitadas: set[str]) -> list[str]:
    """Links para as páginas seguintes da lista: o mesmo `id` e só um parâmetro de página numérico. Qualquer outro
    parâmetro fica de fora: um link como o de "Cancelar candidatura" pode agir só por ser aberto (constituição VI)."""
    alvo = parse_qs(urlsplit(base).query).get("id")
    achados: list[str] = []
    for m in HREF.finditer(html or ""):
        url = urljoin(base, unescape(m.group(1)))
        p = urlsplit(url)
        q = parse_qs(p.query, keep_blank_values=True)
        extras = set(q) - {"id"}
        if (f"{p.scheme}://{p.netloc}".lower() in ORIGENS and p.path.lower().endswith("/vagas_candidato.php")
                and q.get("id") == alvo and len(extras) == 1 and extras <= PARAM_PAGINA
                and all(len(q[k]) == 1 and q[k][0].isdigit() for k in extras)
                and url not in visitadas and url not in achados):
            achados.append(url)
    return achados


def _abrir(aba, url: str) -> str:
    aba.ir(url)
    if HOST_LOGIN in (aba.url() or ""):
        raise PortalErro("a Nerdin pediu login", login=True)
    return aba.avaliar("document.documentElement.outerHTML") or ""


def ler(aba) -> list[dict]:
    from fontes import nerdin as fonte

    endereco = _endereco_conhecido()
    html = _abrir(aba, endereco)
    lidos = cartoes(html)
    achou_link = False
    if not lidos:
        texto = _sem_acento(_arvore(html).texto())
        if any(b in texto for b in BLOQUEIO):
            raise PortalErro("a Nerdin bloqueou a leitura")
        menu = link_do_menu(html)
        achou_link = bool(menu)
        if menu and menu != endereco:
            endereco = menu
            html = _abrir(aba, endereco)
            _guardar(endereco)
            lidos = cartoes(html)
            texto = _sem_acento(_arvore(html).texto())
            if not lidos and any(b in texto for b in BLOQUEIO):
                raise PortalErro("a Nerdin bloqueou a leitura")
        if not lidos:
            if any(v in texto for v in VAZIA):
                return []
            motivo = "não consegui ler as candidaturas da Nerdin"
            if not achou_link:
                motivo += "; informe o link de Minhas candidaturas em NERDIN_CANDIDATURAS no .env"
            raise PortalErro(motivo)

    visitadas = {endereco}
    fila = _paginas(html, endereco, visitadas)
    pausa = fonte.pausa()["faixa"][0]
    while fila and len(visitadas) < MAX_PAGINAS:
        url = fila.pop(0)
        if url in visitadas:
            continue
        visitadas.add(url)
        time.sleep(pausa)
        pagina = _abrir(aba, url)
        lidos += cartoes(pagina)
        fila += [u for u in _paginas(pagina, endereco, visitadas) if u not in fila]
    vistos, unicos = set(), []
    for c in lidos:
        chave = (c["id"], c["titulo"], c["empresa"], c["inscrito"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(c)
    return [traduzir(c) for c in unicos]
