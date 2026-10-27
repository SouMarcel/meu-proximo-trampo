"""Usuário e senha de um portal, guardados pela pessoa no .env e digitados só na página de login dele (spec 027,
research.md §4; constituição I e VI).

  nomes(portal)               ("LOGIN_GUPY_USUARIO", "LOGIN_GUPY_SENHA")
  credencial(portal)          (usuario, senha) ou None
  gravar(portal, u, s) / apagar(portal)
  para_pagina()               por portal: usuário e os 4 últimos caracteres da senha (nunca a senha)
  preencher_login(aba)        digita a credencial se a página está em https, num host exato de login de um portal
                              conhecido e com um único campo de senha; quem clica em Entrar é a pessoa

A senha nunca vai para a IA, para a página do dashboard, para registros ou mensagens de erro. No .env, um valor que
começa ou termina com aspas ou espaço é gravado como "b64:..." para não ser cortado na leitura (isso não é
criptografia: o .env continua legível por programas da conta da pessoa). Quem prefere pode escrever o valor
direto no .env, sem o prefixo.
"""
from __future__ import annotations

import base64
import binascii
import json

import segredos

from . import TRAVA, CandidaturaErro, exigir_ligada
from .dominios import CONHECIDOS, host_de

PREFIXO_B64 = "b64:"
MAX_USUARIO, MAX_SENHA = 200, 200

JS_CAMPOS_LOGIN = r"""(() => {
const visivel = el => { if (!el || !el.isConnected) return false; const s = getComputedStyle(el);
  if (s.display === "none" || s.visibility === "hidden") return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
const todos = Array.from(document.querySelectorAll("input"));
const vis = todos.filter(e => visivel(e) && !e.disabled && !e.readOnly);
const senhas = vis.filter(e => (e.type || "").toLowerCase() === "password");
const tiposUsuario = ["text", "email", "tel", ""];
const antes = vis.filter(e => tiposUsuario.includes((e.type || "").toLowerCase()) &&
  (!senhas.length || (e.compareDocumentPosition(senhas[0]) & Node.DOCUMENT_POSITION_FOLLOWING)));
const pareceUsuario = e => /user|mail|login|cpf|conta|account/i.test([e.name, e.id, e.getAttribute("autocomplete"), e.type].join(" "));
const usuario = antes.filter(pareceUsuario).pop() || (antes.length === 1 || senhas.length ? antes.pop() : null);
return {senhas: senhas.length, usuario: usuario ? todos.indexOf(usuario) : -1, senha: senhas.length === 1 ? todos.indexOf(senhas[0]) : -1};
})()"""

JS_FOCAR_LOGIN = r"""((indice, esperado) => {
const el = Array.from(document.querySelectorAll("input"))[indice];
if (!el) return {ok: false};
const tipo = (el.type || "").toLowerCase();
if ((esperado === "senha") !== (tipo === "password")) return {ok: false};
if (el.value) { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, ""); el.dispatchEvent(new Event("input", {bubbles: true})); }
el.focus();
return {ok: document.activeElement === el && !el.value, tipo};
})(%s, %s)"""

JS_SAIR = "(() => { const a = document.activeElement; if (a && a !== document.body && a.blur) a.blur(); return true; })()"


def _portal(portal: str) -> dict:
    p = CONHECIDOS.get(str(portal or ""))
    if not p or not p["credencial"] or not p["login"]:
        raise CandidaturaErro("este portal não tem login guardável na ferramenta")
    return p


def nomes(portal: str) -> tuple[str, str]:
    c = _portal(portal)["credencial"]
    return f"LOGIN_{c}_USUARIO", f"LOGIN_{c}_SENHA"


def _decodificar(valor: str) -> str:
    if valor.startswith(PREFIXO_B64):
        try:
            return base64.b64decode(valor[len(PREFIXO_B64):], validate=True).decode("utf-8")
        except (binascii.Error, ValueError):
            return ""
    return valor


def _codificar(valor: str) -> str:
    if valor != valor.strip() or valor[:1] in "'\"" or valor[-1:] in "'\"" or valor.startswith(PREFIXO_B64):
        return PREFIXO_B64 + base64.b64encode(valor.encode("utf-8")).decode("ascii")
    return valor


def credencial(portal: str) -> tuple[str, str] | None:
    nu, ns = nomes(portal)
    usuario, senha = _decodificar(segredos.ler(nu)), _decodificar(segredos.ler(ns))
    return (usuario, senha) if usuario and senha else None


def gravar(portal: str, usuario, senha) -> None:
    nu, ns = nomes(portal)
    usuario, senha = str(usuario or "").strip(), str(senha or "")
    if not usuario or not senha:
        raise CandidaturaErro("informe o usuário e a senha")
    if len(usuario) > MAX_USUARIO or len(senha) > MAX_SENHA or any(ch in usuario + senha for ch in "\r\n\0"):
        raise CandidaturaErro("usuário ou senha em formato inválido (muito longo ou com quebra de linha)")
    try:
        segredos.gravar(nu, _codificar(usuario))
        segredos.gravar(ns, _codificar(senha))
    except ValueError:
        raise CandidaturaErro("não deu para guardar a credencial no .env") from None


def apagar(portal: str) -> None:
    for nome in nomes(portal):
        segredos.remover(nome)


def para_pagina() -> list[dict]:
    saida = []
    for nome, p in CONHECIDOS.items():
        if not (p["credencial"] and p["login"]):
            continue
        cred = credencial(nome)
        _, ns = nomes(nome)
        saida.append({"portal": nome, "rotulo": p["rotulo"], "login": list(p["login"]), "guardada": bool(cred),
                      "usuario": cred[0] if cred else "", "final": cred[1][-4:] if cred and len(cred[1]) >= 8 else "",
                      "no_ambiente": segredos.origem(ns) == "ambiente"})
    return saida


def portal_do_login(url: str) -> str | None:
    host = host_de(url)
    return next((n for n, p in CONHECIDOS.items() if host and p["credencial"] and host in p["login"]), None)


def preencher_login(aba, vaga: dict | None) -> dict:
    """Digita usuário e/ou senha guardados na tela de login aberta. Nunca clica em Entrar."""
    exigir_ligada(vaga)
    portal = portal_do_login(aba.url())
    if not portal:
        raise CandidaturaErro("esta página não é a tela de login de um portal com credencial guardável "
                              "(Gupy ou Greenhouse); faça o login à mão")
    cred = credencial(portal)
    if not cred:
        raise CandidaturaErro(f"nenhuma credencial guardada para {CONHECIDOS[portal]['rotulo']}; faça o login à mão")
    if not TRAVA.acquire(blocking=False):
        raise CandidaturaErro("já há um preenchimento em andamento; espere terminar")
    try:
        campos = aba.avaliar(JS_CAMPOS_LOGIN) or {}
        if int(campos.get("senhas") or 0) > 1:
            raise CandidaturaErro("a página tem mais de um campo de senha; faça o login à mão")
        feitos = []
        for papel, indice, valor in (("usuario", campos.get("usuario"), cred[0]), ("senha", campos.get("senha"), cred[1])):
            if not isinstance(indice, int) or indice < 0:
                continue
            if portal_do_login(aba.url()) != portal:  # a página mudou no meio: não digita
                raise CandidaturaErro("a página saiu da tela de login; nada mais foi digitado")
            foco = aba.avaliar(JS_FOCAR_LOGIN % (json.dumps(indice), json.dumps(papel))) or {}
            if not foco.get("ok"):
                continue
            aba.digitar(valor)
            feitos.append(papel)
        try:
            aba.avaliar(JS_SAIR)
        except Exception:  # noqa: BLE001
            pass
    except CandidaturaErro:
        raise
    except Exception:  # noqa: BLE001  (nenhum detalhe, para a senha nunca aparecer numa mensagem)
        raise CandidaturaErro("não deu para preencher o login; faça à mão na janela") from None
    finally:
        TRAVA.release()
    if not feitos:
        raise CandidaturaErro("não achei os campos de login nesta página; faça à mão na janela")
    rotulo = CONHECIDOS[portal]["rotulo"]
    texto = {("usuario", "senha"): "usuário e senha", ("usuario",): "usuário", ("senha",): "senha"}[tuple(feitos)]
    return {"portal": portal, "rotulo": rotulo, "preenchidos": feitos,
            "aviso": f"{rotulo}: {texto} preenchido(s). Confira e clique você em Entrar (ou Continuar)."}
