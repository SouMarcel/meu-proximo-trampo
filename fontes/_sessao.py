"""Área comum dos portais com login (spec 041; constituição, princípio VI, "Busca com login"): portais que só mostram a
busca de vagas depois do login, lidos na janela da ferramenta (navegador.py), com o login feito pela pessoa.

Atributos de um portal com login, além do contrato de fontes/__init__.py:

  COM_LOGIN = True        marca o portal da área
  ROTULO                  nome no painel (ex.: "MyGreenhouse Jobs")
  URL_LOGIN, URL_BUSCA    a página de login (Conectar) e a da busca (carga da aba)
  DOMINIOS                hosts do portal: só neles a ferramenta lê a página
  ORIGENS, ORIGENS_SSO    origens do portal e do login por outro serviço (ex.: LinkedIn), apagadas no Desconectar
  AVISO_RISCO             o risco da conta, confirmado pela pessoa ao ligar
  AVISO_LOGIN             frase sobre o login, para o painel
  logado(url) -> bool     a aba está logada no portal (só pelo endereço)

Regras:
- Só na busca da página: o buscador do dashboard abre na_pagina() em volta de vagas.executar. Fora dele (terminal,
  chat), o portal fica de fora com o aviso "só pelo botão Buscar da página", sem abrir a janela.
- Nunca clicar, digitar, enviar formulário, ler senha ou copiar cookies. O único JavaScript que roda na aba é a
  leitura (fetch GET de dentro da página, com a sessão dela, e consulta ao DOM), e só num host de DOMINIOS.
- Na espera do login, só o endereço da aba é olhado (pelo histórico do navegador): a página pode ser de outro serviço,
  como o LinkedIn, e não é lida.
- A janela vem para a frente só para o login e o captcha; depois volta a ficar minimizada.
- A conexão de cada portal fica em .cache/portais-login.json, fora do Git.
"""
from __future__ import annotations

import contextlib
import json
import threading
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = RAIZ / ".cache" / "portais-login.json"
ESPERA_LOGIN = 180  # segundos que a busca espera a pessoa entrar de novo, com a janela na frente
PASSO_LOGIN = 3


class PortalComLoginErro(Exception):
    """O portal saiu desta busca; tipo: "login", "captcha", "bloqueio", "mudou" ou "janela"."""

    def __init__(self, motivo: str, tipo: str):
        super().__init__(motivo)
        self.tipo = tipo


def _nav():
    import navegador  # na raiz; aqui para o módulo não abrir nada ao ser importado
    return navegador


# ---------------------------------------------------------------- o contexto da busca da página

_trava = threading.Lock()
_ctx: dict = {"thread": None, "esperar_login": None, "abas": {}}


@contextlib.contextmanager
def na_pagina(esperar_login):
    """Liga a busca da página só durante o `with`, na thread que o abriu. esperar_login(modulo, aba) -> bool traz a
    janela para a frente e espera a pessoa entrar (dash/buscador.py)."""
    with _trava:
        if _ctx["thread"] is not None:
            raise RuntimeError("a busca da página já está ligada (aninhada ou em outra thread)")
        _ctx.update(thread=threading.get_ident(), esperar_login=esperar_login, abas={})
    try:
        yield
    finally:
        fechar_abas()
        with _trava:
            _ctx.update(thread=None, esperar_login=None, abas={})


def dentro_da_pagina() -> bool:
    return _ctx["thread"] is not None and _ctx["thread"] == threading.get_ident()


def aviso_fora(modulo) -> str:
    return f"{modulo.ROTULO}: só pelo botão Buscar da página (portal com login)"


def aviso_desconectado(modulo) -> str:
    return f"{modulo.ROTULO}: ligado, mas sem conexão; conecte em Filtros da busca → Portais com login"


# ---------------------------------------------------------------- conexão (fora do Git)

def _ler() -> dict:
    try:
        d = json.loads(ESTADO.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def conectados() -> list[str]:
    c = _ler().get("conectados")
    return [str(n) for n in c] if isinstance(c, dict) else []


def marcar(nome: str, conectado: bool) -> None:
    d = _ler()
    c = d.get("conectados") if isinstance(d.get("conectados"), dict) else {}
    if conectado:
        c[nome] = {"desde": date.today().isoformat()}
    else:
        c.pop(nome, None)
    d["conectados"] = c
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def algum_conectado() -> bool:
    """Sobra alguma sessão na janela: um portal com login ou uma conta conectada (spec 018)."""
    if conectados():
        return True
    import contas  # na raiz
    return bool(contas.conectados())


def desconectar(modulo) -> None:
    """Tira o portal da conexão. Com outra sessão na janela, apaga só as origens do portal e as do login por outro
    serviço; sem nenhuma, fecha a janela e apaga o perfil inteiro, como na conta conectada."""
    marcar(modulo.NOME, False)
    nav = _nav()
    if not algum_conectado():
        nav.desconectar()
        return
    aba = nav.abrir_para_leitura("about:blank")  # aba própria: não tira a pessoa de outra página
    try:
        for origem in (*modulo.ORIGENS, *getattr(modulo, "ORIGENS_SSO", ())):
            aba.sessao.pedir("Storage.clearDataForOrigin", origin=origem, storageTypes="all")
        aba.minimizar()
    finally:
        aba.fechar_aba()


# ---------------------------------------------------------------- a aba e a leitura

@contextlib.contextmanager
def janela():
    """Erro do navegador (janela fechada no meio, navegador ausente) vira PortalComLoginErro(tipo="janela")."""
    nav = _nav()
    try:
        yield
    except nav.NavegadorErro as e:
        raise PortalComLoginErro(f"a janela da ferramenta não respondeu ({e})", "janela") from None


def aba(modulo):
    """Uma aba em segundo plano por portal e por busca, aberta na URL_BUSCA e reaproveitada nos pedidos seguintes."""
    if not dentro_da_pagina():
        raise PortalComLoginErro(aviso_fora(modulo), "janela")
    a = _ctx["abas"].get(modulo.NOME)
    if a is None:
        with janela():
            a = _nav().abrir_para_leitura(modulo.URL_BUSCA)
        _ctx["abas"][modulo.NOME] = a
    return a


def fechar_abas() -> None:
    for a in list(_ctx["abas"].values()):
        try:
            a.fechar_aba()
        except Exception:  # a janela pode ter sido fechada pela pessoa
            pass
    _ctx["abas"].clear()


def endereco(a) -> str:
    return a.endereco()


def no_portal(modulo, a) -> bool:
    return (urlsplit(endereco(a)).hostname or "").lower() in modulo.DOMINIOS


JS_PAGINA = """(() => {
  const el = document.querySelector("[data-page]");
  if (!el) return null;
  try { const d = JSON.parse(el.getAttribute("data-page")); return {component: d.component, version: d.version}; }
  catch (e) { return null; }
})()"""

JS_CAPTCHA = """(() => {
  const visivel = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 30 && r.height > 30 && s.visibility !== "hidden" && s.display !== "none"; };
  const quadro = [...document.querySelectorAll("iframe")].some(i =>
    /recaptcha|hcaptcha|turnstile|challenges\\.cloudflare/i.test(i.src || "") && visivel(i));
  const texto = (document.body && document.body.innerText || "").slice(0, 5000);
  return quadro || /verify you are human|are you a robot|unusual activity|verifique que voc[eê] [eé] humano|atividade incomum/i.test(texto);
})()"""

JS_PEDIDO = """(async () => {
  try {
    const r = await fetch(%s, {credentials: "include", headers: %s});
    const t = await r.text();
    let d = null;
    try { d = JSON.parse(t); } catch (e) {}
    return {status: r.status, dados: d, url: r.url};
  } catch (e) { return {status: 0, dados: null, url: ""}; }
})()"""


def data_page(modulo, a) -> dict | None:
    """{component, version} do app da página (Inertia), só com a aba no portal."""
    if not no_portal(modulo, a):
        return None
    d = a.avaliar(JS_PAGINA)
    return d if isinstance(d, dict) else None


def captcha_na_aba(modulo, a) -> bool:
    """Captcha ou verificação visível na página do portal (reCAPTCHA, hCaptcha, Cloudflare ou o texto)."""
    return no_portal(modulo, a) and bool(a.avaliar(JS_CAPTCHA))


def pedir_json(modulo, a, url: str, cabecalhos: dict) -> tuple[int, object, str]:
    """(status, JSON ou None, endereço final) de um GET feito de dentro da aba, com a sessão dela: os cookies não saem
    do navegador. Só com a aba e o pedido no portal."""
    if (urlsplit(url).hostname or "").lower() not in modulo.DOMINIOS:
        raise ValueError("pedido fora do portal")
    if not no_portal(modulo, a):
        raise PortalComLoginErro(f"{modulo.ROTULO}: a aba saiu do portal (login?)", "login")
    r = a.avaliar(JS_PEDIDO % (json.dumps(url), json.dumps(cabecalhos))) or {}
    return int(r.get("status") or 0), r.get("dados"), str(r.get("url") or "")


# ---------------------------------------------------------------- login

def esperar(modulo, a, segundos: float = ESPERA_LOGIN, passo: float = PASSO_LOGIN, cancelado=None,
            relogio=time.monotonic, dormir=time.sleep) -> bool:
    """Espera a aba voltar logada ao portal, olhando só o endereço. Para com cancelado() ou com a janela fechada."""
    nav = _nav()
    limite = relogio() + segundos
    while relogio() < limite:
        if cancelado and cancelado():
            return False
        dormir(passo)
        try:
            if modulo.logado(endereco(a)):
                dormir(passo)  # deixa o portal terminar de gravar a sessão antes de ler
                return True
        except nav.NavegadorErro:
            return False
    return False


def garantir_login(modulo, a) -> None:
    """Com a aba fora do login, chama a espera da busca da página (janela na frente, até 3 minutos). Logou: recarrega
    a busca. Não logou: PortalComLoginErro(tipo="login")."""
    if modulo.logado(endereco(a)):
        return
    esperar_login = _ctx["esperar_login"] if dentro_da_pagina() else None
    if esperar_login is None or not esperar_login(modulo, a):
        raise PortalComLoginErro(f"{modulo.ROTULO}: o login não foi feito na janela da ferramenta; o portal ficou de "
                                 "fora desta busca", "login")
    a.ir(modulo.URL_BUSCA)
    if not modulo.logado(endereco(a)):
        raise PortalComLoginErro(f"{modulo.ROTULO}: o login não foi reconhecido; o portal ficou de fora desta busca",
                                 "login")
