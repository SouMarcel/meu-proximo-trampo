"""Formulário de candidatura na página atual da janela da ferramenta (spec 027, research.md §2, §3 e §5).

  ler(aba)                                  a página: etapa, domínio, campos classificados e a assinatura
  classificar_pagina(bruto, campos)         login | perguntas | teste | bloqueio | desconhecida (sem navegador)
  classificar_campo(campo)                  comum | sensivel | cadastro | consentimento | arquivo | senha | outro
  preencher(aba, assinatura, respostas)     escreve só nos campos comuns confirmados; devolve o que fez e o que ficou

Escrita: texto pelo teclado (Input.insertText) no campo focado; seleção nativa pelo valor; opção e caixa pela tecla
espaço no input focado. Antes de digitar ou apertar espaço, confere que o elemento ativo é o campo certo. Nunca:
clique, envio de formulário, tecla Enter ou pedido de escrita ao portal (os testes procuram isso no JavaScript).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from . import TRAVA, CandidaturaErro, exigir_ligada
from . import dominios

MAX_CAMPOS, MAX_OPCOES, MAX_RESPOSTA = 80, 60, 5000

# ---------------------------------------------------------------- JavaScript (só lê, ou escreve em campos)

_COMUM = r"""
const limpo = s => String(s || "").replace(/\s+/g, " ").trim();
const todos = () => Array.from(document.querySelectorAll("input,select,textarea"));
const visivel = el => {
  if (!el || !el.isConnected) return false;
  const s = getComputedStyle(el);
  if (s.display === "none" || s.visibility === "hidden") return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};
const rotuloFor = el => el.id ? document.querySelector('label[for="' + CSS.escape(el.id) + '"]') : null;
const opcaoVisivel = el => visivel(el) || visivel(el.closest("label")) || visivel(rotuloFor(el));
const textoDe = el => el ? limpo(el.innerText || el.textContent) : "";
const unico = (sel) => document.querySelectorAll(sel).length === 1;
const chaveDe = (el, i) => {
  if (el.type === "radio" && el.name) return "radio:" + el.name;
  if (el.type === "checkbox" && el.name && document.getElementsByName(el.name).length > 1) return "check:" + el.name;
  if (el.id && unico('[id="' + CSS.escape(el.id) + '"]')) return "#" + el.id;
  if (el.name && unico('[name="' + CSS.escape(el.name) + '"]')) return "n:" + el.name;
  return "pos:" + i;
};
const grupo = (chave) => {
  const nome = chave.slice(chave.indexOf(":") + 1);
  const tipo = chave.startsWith("radio:") ? "radio" : "checkbox";
  return Array.from(document.getElementsByName(nome)).filter(e => e.type === tipo);
};
const achar = (chave) => {
  if (chave.startsWith("#")) return document.getElementById(chave.slice(1));
  if (chave.startsWith("n:")) return document.getElementsByName(chave.slice(2))[0] || null;
  if (chave.startsWith("pos:")) return todos()[Number(chave.slice(4))] || null;
  return null;
};
"""

JS_LER = "(() => {" + _COMUM + r"""
const rotuloDe = el => {
  let t = "";
  const ids = el.getAttribute("aria-labelledby");
  if (ids) t = limpo(ids.split(/\s+/).map(id => textoDe(document.getElementById(id))).join(" "));
  if (!t) t = textoDe(rotuloFor(el));
  if (!t) t = textoDe(el.closest("label"));
  if (!t) t = limpo(el.getAttribute("aria-label"));
  if (!t) {
    let p = el.parentElement;
    for (let n = 0; n < 4 && p && !t; n++, p = p.parentElement) {
      t = limpo(Array.from(p.childNodes).filter(x => x !== el && !(x.contains && x.contains(el)))
        .map(x => x.nodeType === 3 ? x.textContent : (x.matches && x.matches("input,select,textarea,button") ? "" : (x.innerText || "")))
        .join(" "));
    }
  }
  if (!t) t = limpo(el.placeholder);
  return t.slice(0, 500);
};
const perguntaDoGrupo = (els, textos) => {
  const fs = els[0].closest("fieldset");
  if (fs && fs.querySelector("legend")) return textoDe(fs.querySelector("legend")).slice(0, 500);
  const g = els[0].closest('[role="radiogroup"],[role="group"]');
  if (g && g.getAttribute("aria-label")) return limpo(g.getAttribute("aria-label")).slice(0, 500);
  let p = els[0].parentElement;
  while (p && !els.every(e => p.contains(e))) p = p.parentElement;
  for (let n = 0; n < 3 && p; n++, p = p.parentElement) {
    const tudo = textoDe(p);
    const primeira = textos.map(x => x && tudo.indexOf(x)).filter(x => x > 0);
    const antes = limpo(primeira.length ? tudo.slice(0, Math.min(...primeira)) : "");
    if (antes) return antes.slice(-500);
  }
  return "";
};
const lista = todos();
const campos = [], vistos = new Set();
let senhas = 0;
lista.forEach((el, i) => {
  const tag = el.tagName.toLowerCase();
  const tipoHtml = tag === "input" ? (el.type || "text").toLowerCase() : tag;
  if (["hidden", "submit", "button", "reset", "image"].includes(tipoHtml)) return;
  if (el.disabled || el.readOnly) return;
  const chave = chaveDe(el, i);
  if (vistos.has(chave)) return;
  if (tipoHtml === "radio" || tipoHtml === "checkbox") {
    const els = chave.startsWith("radio:") || chave.startsWith("check:") ? grupo(chave) : [el];
    if (!els.some(opcaoVisivel)) return;
    vistos.add(chave);
    const textos = els.map(e => textoDe(rotuloFor(e)) || textoDe(e.closest("label")) || limpo(e.getAttribute("aria-label")) || limpo(e.value));
    if (els.length === 1 && tipoHtml === "checkbox") {
      campos.push({chave, tipo: "caixa", tipo_html: tipoHtml, rotulo: rotuloDe(el), obrigatorio: el.required, valor: el.checked ? "sim" : "nao", limite: 0, opcoes: []});
      return;
    }
    campos.push({chave, tipo: tipoHtml === "radio" ? "unica" : "multipla", tipo_html: tipoHtml, rotulo: perguntaDoGrupo(els, textos),
      obrigatorio: els.some(e => e.required), limite: 0,
      opcoes: textos.map((t, n) => ({valor: String(n), texto: t.slice(0, 200)})),
      valor: tipoHtml === "radio" ? String(els.findIndex(e => e.checked)).replace("-1", "") : els.map((e, n) => e.checked ? String(n) : "").filter(Boolean).join(",")});
    return;
  }
  if (!visivel(el)) return;
  vistos.add(chave);
  if (tipoHtml === "password") senhas++;
  const base = {chave, tipo_html: tipoHtml, rotulo: rotuloDe(el), obrigatorio: el.required, nome: limpo(el.name).slice(0, 100),
    autocomplete: limpo(el.getAttribute("autocomplete")).slice(0, 60), limite: el.maxLength > 0 ? el.maxLength : 0};
  if (tag === "select") {
    campos.push({...base, tipo: "selecao", opcoes: Array.from(el.options).map((o, n) => ({valor: String(n), texto: limpo(o.text).slice(0, 200), vazia: !o.value})),
      valor: el.value ? String(el.selectedIndex) : ""});
  } else {
    const tipo = tag === "textarea" ? "area" : ({password: "senha", file: "arquivo", date: "data", "datetime-local": "data", month: "data", time: "data", range: "outro", color: "outro"})[tipoHtml] || "texto";
    campos.push({...base, tipo, opcoes: [], valor: tipo === "senha" || tipo === "arquivo" ? (el.value ? "*" : "") : String(el.value || "").slice(0, 300)});
  }
});
const outros = Array.from(document.querySelectorAll('[role="combobox"],[role="listbox"],[contenteditable="true"]'))
  .filter(e => !e.matches("input,select,textarea") && visivel(e)).length;
return {url: location.href, titulos: limpo([document.title, ...Array.from(document.querySelectorAll("h1,h2,h3")).slice(0, 12).map(textoDe)].join(" | ")).slice(0, 1500),
  texto: textoDe(document.body).slice(0, 4000), iframes: Array.from(document.querySelectorAll("iframe")).map(f => String(f.src || "").slice(0, 300)).slice(0, 20),
  campos: campos.slice(0, 80), senhas, outros};
})()"""

JS_FOCAR = "((chave, limpar) => {" + _COMUM + r"""
const el = achar(chave);
if (!el) return {ok: false};
if (limpar && "value" in el) {
  const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(el, "");
  el.dispatchEvent(new Event("input", {bubbles: true}));
}
el.focus();
const a = document.activeElement;
return {ok: a === el, tag: a ? a.tagName : "", tipo: a && a.type ? String(a.type).toLowerCase() : "", vazio: !(a && a.value)};
})(%s, %s)"""

JS_SELECIONAR = "((chave, indice) => {" + _COMUM + r"""
const el = achar(chave);
if (!el || el.tagName !== "SELECT" || !el.options[indice]) return false;
Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(el, el.options[indice].value);
el.dispatchEvent(new Event("input", {bubbles: true}));
el.dispatchEvent(new Event("change", {bubbles: true}));
return el.selectedIndex === indice;
})(%s, %s)"""

JS_FOCAR_OPCAO = "((chave, indice) => {" + _COMUM + r"""
const els = chave.startsWith("radio:") || chave.startsWith("check:") ? grupo(chave) : [achar(chave)].filter(Boolean);
const el = els[indice];
if (!el || !["radio", "checkbox"].includes(el.type)) return {ok: false};
el.focus();
return {ok: document.activeElement === el, marcada: el.checked, tipo: el.type};
})(%s, %s)"""

JS_MARCADA = "((chave, indice) => {" + _COMUM + r"""
const els = chave.startsWith("radio:") || chave.startsWith("check:") ? grupo(chave) : [achar(chave)].filter(Boolean);
return !!(els[indice] && els[indice].checked);
})(%s, %s)"""

JS_SAIR = "(() => { const a = document.activeElement; if (a && a !== document.body && a.blur) a.blur(); return true; })()"

# ---------------------------------------------------------------- classificação (Python, testável sem navegador)

BLOQUEIO = re.compile(r"captcha|nao sou um robo|i'?m not a robot|verifique que voce e humano|verify (that )?you are (a )?human|"
                      r"codigo de verificacao|verification code|digite o codigo|enter the code|atividade (incomum|suspeita)|"
                      r"unusual activity|acesso bloqueado|access denied")
BLOQUEIO_IFRAME = re.compile(r"recaptcha|hcaptcha|turnstile|challenges\.cloudflare|captcha", re.I)
TESTE = re.compile(r"teste (de perfil|comportamental|de logica|tecnico|de personalidade|de raciocinio|de ingles)|"
                   r"avaliacao (comportamental|tecnica|de perfil)|assessment|(gravar|gravacao de|envie um|enviar um) video|"
                   r"video (interview|recording)|tempo restante|time remaining|cronometro|desafio tecnico|coding challenge")
CONSENTIMENTO = re.compile(r"termos|aceito|concordo|\bli\b|privacidade|consent|\bagree\b|lgpd|autorizo|politica|\bterms\b|privacy")
CADASTRO = re.compile(r"\b(nome|name|sobrenome|first name|last name|full name|e-?mail|telefone|celular|phone|mobile|whatsapp|"
                      r"cpf|rg|documento|passaporte|passport|endereco|address|cep|zip|postal|cidade|city|bairro|estado|pais|"
                      r"country|nascimento|birth|idade|linkedin|github|portfolio|website|site|url)\b")
AUTOCOMPLETE_CADASTRO = re.compile(r"name|email|tel|address|postal|country|bday|street|locality|region|url|username")
MOTIVOS = {
    "sensivel": "responda você na página",
    "cadastro": "dado cadastral: confira ou preencha você",
    "consentimento": "aceite de termos: decida você",
    "arquivo": "anexo: envie você",
    "senha": "senha: use Preencher login",
    "outro": "campo que a ferramenta não preenche: escolha você",
}


def _sem_acento(s) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def classificar_campo(c: dict) -> tuple[str, str]:
    """(marca, motivo) de um campo lido."""
    import candidatura_ia
    tipo, rotulo = c.get("tipo"), _sem_acento(c.get("rotulo"))
    if tipo == "senha":
        return "senha", MOTIVOS["senha"]
    if tipo == "arquivo":
        return "arquivo", MOTIVOS["arquivo"]
    categoria = candidatura_ia.sensivel(c.get("rotulo") or "")
    if categoria:
        return "sensivel", f"{MOTIVOS['sensivel']} ({categoria})"
    if tipo == "caixa" and CONSENTIMENTO.search(rotulo):
        return "consentimento", MOTIVOS["consentimento"]
    if tipo in ("texto", "selecao") and (
            c.get("tipo_html") in ("email", "tel", "url") or CADASTRO.search(rotulo)
            or AUTOCOMPLETE_CADASTRO.search(_sem_acento(c.get("autocomplete")))):
        return "cadastro", MOTIVOS["cadastro"]
    if tipo not in ("texto", "area", "selecao", "unica", "multipla", "caixa"):
        return "outro", MOTIVOS["outro"]
    if not rotulo.strip():
        return "outro", "campo sem pergunta legível: preencha você"
    return "comum", ""


def classificar_pagina(bruto: dict, campos: list[dict]) -> tuple[str, str]:
    """(etapa, aviso) da página."""
    texto, titulos = _sem_acento(bruto.get("texto")), _sem_acento(bruto.get("titulos"))
    if any(BLOQUEIO_IFRAME.search(f or "") for f in bruto.get("iframes") or []) or BLOQUEIO.search(texto):
        return "bloqueio", "O portal pediu uma verificação (captcha ou código). Resolva na janela; a ferramenta parou aqui."
    if bruto.get("senhas"):
        return "login", "Tela de login: use Preencher login (se guardou a credencial) ou entre à mão, e clique você em Entrar."
    if TESTE.search(titulos):
        return "teste", "Esta etapa é um teste ou vídeo do portal: é com você. A ferramenta não preenche testes."
    if any(c["marca"] != "outro" for c in campos):
        return "perguntas", ""
    return "desconhecida", "Não reconheci perguntas nesta página. Avance no portal até o formulário e leia de novo."


def assinatura(campos: list[dict]) -> str:
    base = json.dumps([[c["chave"], c.get("rotulo") or "", c.get("tipo")] for c in campos], ensure_ascii=False)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def _limpar_campo(c: dict) -> dict | None:
    if not isinstance(c, dict) or not isinstance(c.get("chave"), str) or not c["chave"]:
        return None
    opcoes = [o for o in (c.get("opcoes") or [])[:MAX_OPCOES] if isinstance(o, dict)]
    campo = {"chave": c["chave"][:300], "tipo": str(c.get("tipo") or "outro"), "tipo_html": str(c.get("tipo_html") or "")[:30],
             "rotulo": " ".join(str(c.get("rotulo") or "").split())[:500], "obrigatorio": bool(c.get("obrigatorio")),
             "limite": int(c.get("limite") or 0) if str(c.get("limite") or "0").isdigit() else 0,
             "opcoes": [{"valor": str(o.get("valor")), "texto": " ".join(str(o.get("texto") or "").split())[:200],
                         "vazia": bool(o.get("vazia"))} for o in opcoes],
             "valor": str(c.get("valor") or "")[:300], "autocomplete": str(c.get("autocomplete") or "")[:60]}
    campo["marca"], campo["motivo"] = classificar_campo(campo)
    return campo


def interpretar(bruto) -> dict:
    """A leitura crua do JavaScript → página classificada (sem navegador)."""
    bruto = bruto if isinstance(bruto, dict) else {}
    campos = [c for c in (_limpar_campo(x) for x in (bruto.get("campos") or [])[:MAX_CAMPOS]) if c]
    etapa, aviso = classificar_pagina(bruto, campos)
    if etapa == "perguntas" and bruto.get("outros"):
        aviso = "Há campos que a ferramenta não preenche (listas próprias do portal): escolha você na janela."
    url = str(bruto.get("url") or "")
    return {"url": url, "dominio": dominios.situacao(url), "etapa": etapa, "aviso": aviso, "campos": campos,
            "assinatura": assinatura(campos)}


def ler(aba) -> dict:
    return interpretar(aba.avaliar(JS_LER))


# ---------------------------------------------------------------- escrita

def _js(modelo: str, *args) -> str:
    return modelo % tuple(json.dumps(a) for a in args)


def _cortar(texto: str, limite: int) -> str:
    texto = str(texto or "").strip()
    if limite and len(texto) > limite:
        corte = texto[:limite]
        espaco = corte.rfind(" ")
        texto = (corte[:espaco] if espaco > limite * 0.6 else corte).rstrip(" ,;:")
    return texto[:MAX_RESPOSTA]


def _escrever_texto(aba, c: dict, valor: str, trocar: bool) -> bool:
    foco = aba.avaliar(_js(JS_FOCAR, c["chave"], bool(trocar and c["valor"]))) or {}
    if not foco.get("ok") or foco.get("tag") not in ("INPUT", "TEXTAREA"):
        return False
    if foco.get("tipo") in ("password", "file", "submit", "button", "reset", "image", "hidden", "checkbox", "radio"):
        return False
    if not foco.get("vazio"):
        return False
    aba.digitar(valor)
    return True


def _marcar_opcao(aba, c: dict, indice: int) -> bool:
    foco = aba.avaliar(_js(JS_FOCAR_OPCAO, c["chave"], indice)) or {}
    if not foco.get("ok") or foco.get("tipo") not in ("radio", "checkbox"):
        return False
    if not foco.get("marcada"):
        aba.espaco()
    return bool(aba.avaliar(_js(JS_MARCADA, c["chave"], indice)))


def _escrever(aba, c: dict, valor, trocar: bool) -> bool:
    tipo = c["tipo"]
    if tipo in ("texto", "area"):
        valor = _cortar(valor, c["limite"])
        if c.get("tipo_html") == "number" and not re.fullmatch(r"-?\d+([.,]\d+)?", valor):
            return False
        return bool(valor) and _escrever_texto(aba, c, valor, trocar)
    indices = range(len(c["opcoes"]))
    if tipo == "selecao":
        i = int(valor) if str(valor).isdigit() else -1
        return i in indices and not c["opcoes"][i]["vazia"] and bool(aba.avaliar(_js(JS_SELECIONAR, c["chave"], i)))
    if tipo == "unica":
        i = int(valor) if str(valor).isdigit() else -1
        return i in indices and _marcar_opcao(aba, c, i)
    if tipo == "multipla":
        escolhidos = [int(v) for v in str(valor).split(",") if v.strip().isdigit() and int(v) in indices]
        return bool(escolhidos) and all([_marcar_opcao(aba, c, i) for i in escolhidos])
    if tipo == "caixa" and valor in ("sim", "nao"):
        if valor == c["valor"]:
            return True
        foco = aba.avaliar(_js(JS_FOCAR_OPCAO, c["chave"], 0)) or {}
        if not foco.get("ok") or foco.get("tipo") != "checkbox":
            return False
        aba.espaco()  # alterna a caixa focada
        return bool(aba.avaliar(_js(JS_MARCADA, c["chave"], 0))) == (valor == "sim")
    return False


def _tem_valor(c: dict) -> bool:
    if c["tipo"] == "caixa":
        return c["valor"] == "sim"
    if c["tipo"] == "selecao":
        return bool(c["valor"]) and c["valor"].isdigit() and int(c["valor"]) < len(c["opcoes"]) \
            and not c["opcoes"][int(c["valor"])]["vazia"]
    return bool(c["valor"])


def texto_do_valor(c: dict, valor: str) -> str:
    """O valor legível: o texto das opções escolhidas, "sim"/"não" na caixa, o texto digitado nos outros."""
    if c["opcoes"]:
        textos = {o["valor"]: o["texto"] for o in c["opcoes"]}
        return "; ".join(textos.get(v, v) for v in valor.split(","))
    if c["tipo"] == "caixa":
        return "sim" if valor == "sim" else "não"
    return _cortar(valor, c["limite"])


def preencher(aba, assinatura_lida: str, respostas: list, vaga: dict | None) -> dict:
    """Preenche os campos comuns com as respostas confirmadas ([{chave, valor, trocar}]). Confere o recurso ligado na vaga, o
    domínio e se a página ainda é a lida; nunca toca em campo sensível, cadastro, consentimento, arquivo ou senha."""
    exigir_ligada(vaga)
    if not isinstance(respostas, list):
        raise CandidaturaErro("respostas inválidas")
    if not TRAVA.acquire(blocking=False):
        raise CandidaturaErro("já há um preenchimento em andamento; espere terminar")
    try:
        pagina = ler(aba)
        dom = pagina["dominio"]
        if not dom["permitido"]:
            raise CandidaturaErro(dom["bloqueado"] or f"o endereço {dom['host']} não está liberado para preenchimento")
        if pagina["etapa"] == "bloqueio":
            raise CandidaturaErro(pagina["aviso"])
        if pagina["assinatura"] != assinatura_lida:
            raise CandidaturaErro("a página mudou desde a leitura: clique em Preencher esta página de novo")
        campos = {c["chave"]: c for c in pagina["campos"]}
        preenchidos, ficaram, vistos = [], [], set()
        for r in respostas[:MAX_CAMPOS]:
            if not isinstance(r, dict) or r.get("chave") not in campos or r["chave"] in vistos:
                continue
            vistos.add(r["chave"])
            c = campos[r["chave"]]
            valor = r.get("valor")
            valor = ",".join(str(v) for v in valor) if isinstance(valor, list) else str(valor if valor is not None else "")
            item = {"chave": c["chave"], "rotulo": c["rotulo"]}
            if c["marca"] != "comum":
                ficaram.append({**item, "motivo": c["motivo"]})
            elif not valor.strip():
                ficaram.append({**item, "motivo": "sem resposta"})
            elif _tem_valor(c) and not r.get("trocar"):
                ficaram.append({**item, "motivo": "já estava preenchido (mantido)"})
            elif _escrever(aba, c, valor.strip(), bool(r.get("trocar"))):
                preenchidos.append({**item, "valor": valor.strip(), "texto": texto_do_valor(c, valor.strip())})
            else:
                ficaram.append({**item, "motivo": "não consegui preencher este campo: preencha você"})
        for c in pagina["campos"]:
            if c["chave"] not in vistos and c["marca"] != "comum":
                ficaram.append({"chave": c["chave"], "rotulo": c["rotulo"], "motivo": c["motivo"]})
        try:
            aba.avaliar(JS_SAIR)
        except Exception:  # noqa: BLE001  (tirar o foco é só cortesia)
            pass
        return {"preenchidos": preenchidos, "ficaram": ficaram,
                "aviso": "Confira na janela e clique você em Continuar ou Enviar."}
    finally:
        TRAVA.release()
