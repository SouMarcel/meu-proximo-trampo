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
import time
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
const ehOpcao = e => !!e && (e.type === "radio" || e.type === "checkbox");
// textos que não são pergunta: numeração, asterisco, contadores e avisos de tamanho
const AJUDA = /^(\*|\d+|[.)\-–:]|obrigat[oó]ri[oa]|opcional|optional|required|selecione|select)$|^(m[aá]x|m[ií]n|maximum|minimum|at[eé])\b.{0,25}caracter|^\d+\s*(\/|de|of)\s*\d+/i;
const deOpcao = n => { const l = n.parentElement && n.parentElement.closest("label");
  return !!(l && l.querySelector('input[type=radio],input[type=checkbox]')); };
// os textos visíveis entre o campo a (ou o começo da página) e o campo b, sem os rótulos das opções
const textosEntre = (a, b) => {
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const saida = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (a && !(a.compareDocumentPosition(n) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
    if (!(n.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING)) break;
    const p = n.parentElement;
    if (!p || p.closest("script,style,noscript,option,template,select,textarea,button")) continue;
    const t = limpo(n.textContent);
    if (!t || AJUDA.test(t) || deOpcao(n) || !visivel(p)) continue;
    saida.push({n, t});
  }
  return saida;
};
const anterior = el => { let ant = null; for (const e of todos()) { if (e === el) break; if (e.type !== "hidden") ant = e; } return ant; };
// a pergunta de um campo: o bloco do último texto com "?" entre o campo anterior e ele (ou os últimos textos)
const perguntaDe = el => {
  const segs = textosEntre(anterior(el), el);
  if (!segs.length) return "";
  let t = "";
  for (let k = segs.length - 1; k >= 0 && !t; k--) {
    if (segs[k].t.includes("?")) {
      const bloco = segs[k].n.parentElement.closest("h1,h2,h3,h4,h5,h6,legend,label,p,span,div") || segs[k].n.parentElement;
      t = textoDe(bloco);
      if (t.length > 400) t = segs[k].t;
    }
  }
  if (!t) t = segs.slice(-2).map(s => s.t).join(" ");
  return limpo(t.replace(/^\s*\d+\s*[.)\-–:]\s*/, "").replace(/\s*\*\s*$/, "")).slice(0, 500);
};
// grupos de opções: o mesmo name, ou names que só mudam no número do fim (ex.: Gupy, "checkbox-6405922-0" e "-1"),
// seguidos e sem pergunta entre eles. Caixas soltas (ex.: aceite de termos) nunca entram no grupo de outra pergunta.
const raiz = n => { const r = String(n || "").replace(/[-_]?\[?\d+\]?$/, ""); return r && r !== n ? r : null; };
const grupos = () => {
  const ops = todos().filter(e => ehOpcao(e) && !e.disabled && opcaoVisivel(e));
  const gs = [];
  let g = null;
  for (const e of ops) {
    const mesmaRaiz = g && raiz(e.name) && raiz(e.name) === g.raiz && !textosEntre(g.els[g.els.length - 1], e).length;
    const continua = g && e.type === g.tipo && ((e.name && e.name === g.nome) || mesmaRaiz);
    if (continua) { g.els.push(e); if (g.nome !== e.name) g.nome = null; }
    else { g = {tipo: e.type, nome: e.name || null, raiz: raiz(e.name), els: [e]}; gs.push(g); }
  }
  const lista = todos();
  return gs.map(x => ({els: x.els, tipo: x.tipo,
    chave: x.nome && x.els.length > 1 && document.getElementsByName(x.nome).length === x.els.length
      ? (x.tipo === "radio" ? "radio:" : "check:") + x.nome : "grp:" + lista.indexOf(x.els[0])}));
};
const grupoDe = chave => (grupos().find(g => g.chave === chave) || {els: []}).els;
const chaveDe = (el, i) => {
  if (el.id && unico('[id="' + CSS.escape(el.id) + '"]')) return "#" + el.id;
  if (el.name && unico('[name="' + CSS.escape(el.name) + '"]')) return "n:" + el.name;
  return "pos:" + i;
};
const achar = (chave) => {
  if (chave.startsWith("#")) return document.getElementById(chave.slice(1));
  if (chave.startsWith("n:")) return document.getElementsByName(chave.slice(2))[0] || null;
  if (chave.startsWith("pos:")) return todos()[Number(chave.slice(4))] || null;
  return null;
};
// campos escondidos de validação (ex.: o "required" do react-select): não são perguntas
const escondido = e => e.getAttribute("aria-hidden") === "true" || !!e.closest('[aria-hidden="true"]')
  || (e.tabIndex < 0 && getComputedStyle(e).opacity === "0");
// lista com busca (react-select e parecidos, ex.: Greenhouse): o input é um combobox e as opções só existem aberta
const ehLista = e => !!e && e.tagName === "INPUT" && (e.getAttribute("role") === "combobox" || e.getAttribute("aria-autocomplete") === "list");
const controleDe = e => e.closest('[class*="control"]') || e.parentElement;
const valorLista = e => {
  const c = controleDe(e);
  const v = c && c.querySelector('[class*="singleValue"],[class*="single-value"],[class*="-single-value"]');
  return v ? textoDe(v) : "";
};
const opcoesLista = e => {
  const ids = String(e.getAttribute("aria-controls") || e.getAttribute("aria-owns") || "").split(/\s+/).filter(Boolean);
  let box = ids.map(id => document.getElementById(id)).find(Boolean);
  if (!box) { const r = e.closest('[class*="container"]') || controleDe(e).parentElement; box = r && r.querySelector('[role="listbox"],[class*="menu"]'); }
  if (!box) return [];
  return Array.from(box.querySelectorAll('[role="option"],[class*="__option"],[class*="-option"]'))
    .filter(o => !o.querySelector('[role="option"],[class*="__option"]'));
};
const estadoLista = e => {
  const ativa = document.getElementById(e.getAttribute("aria-activedescendant") || "");
  const ops = opcoesLista(e);
  return {ativo: document.activeElement === e, valor: valorLista(e),
    opcoes: ops.map(o => ({t: textoDe(o), foco: o === ativa || /--is-focused|focused/.test(String(o.className)) || o.getAttribute("aria-selected") === "true"}))};
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
  if (AJUDA.test(t)) t = "";
  if (!t) t = perguntaDe(el);
  const nome = limpo(el.name);
  if (!t && /[a-zà-ú]{3,}\s+[a-zà-ú]{2,}/i.test(nome)) t = nome;  // ex.: Gupy, a pergunta no name do campo
  if (!t) t = limpo(el.placeholder);
  return t.slice(0, 500);
};
const lista = todos();
const campos = [], vistos = new Set();
const emGrupo = new Map();
grupos().forEach(g => g.els.forEach(e => emGrupo.set(e, g)));
let senhas = 0;
lista.forEach((el, i) => {
  const tag = el.tagName.toLowerCase();
  const tipoHtml = tag === "input" ? (el.type || "text").toLowerCase() : tag;
  if (["hidden", "submit", "button", "reset", "image"].includes(tipoHtml)) return;
  if (el.disabled || el.readOnly) return;
  if (tipoHtml === "radio" || tipoHtml === "checkbox") {
    const g = emGrupo.get(el);
    if (!g || vistos.has(g.chave)) return;
    vistos.add(g.chave);
    const textos = g.els.map(e => textoDe(rotuloFor(e)) || textoDe(e.closest("label")) || limpo(e.getAttribute("aria-label")) || limpo(e.value));
    const pergunta = perguntaDe(g.els[0]);
    const nome = limpo(g.els[0].name).slice(0, 100);
    if (g.els.length === 1 && g.tipo === "checkbox") {
      const rotulo = textos[0].length > 12 || !pergunta ? textos[0] : pergunta + " " + textos[0];
      campos.push({chave: g.chave, tipo: "caixa", tipo_html: "checkbox", rotulo: rotulo.slice(0, 500), obrigatorio: el.required,
        valor: el.checked ? "sim" : "nao", limite: 0, opcoes: [], nome});
      return;
    }
    campos.push({chave: g.chave, tipo: g.tipo === "radio" ? "unica" : "multipla", tipo_html: g.tipo, rotulo: pergunta, nome,
      obrigatorio: g.els.some(e => e.required), limite: 0,
      opcoes: textos.map((t, n) => ({valor: String(n), texto: t.slice(0, 200)})),
      valor: g.els.map((e, n) => e.checked ? String(n) : "").filter(Boolean).join(",")});
    return;
  }
  if (!visivel(el) || escondido(el)) return;
  const chave = chaveDe(el, i);
  if (vistos.has(chave)) return;
  vistos.add(chave);
  if (ehLista(el)) {  // as opções vêm depois, abrindo a lista (ler, em Python)
    campos.push({chave, tipo: "lista", tipo_html: "combobox", rotulo: rotuloDe(el), nome: limpo(el.name).slice(0, 100),
      obrigatorio: el.required || el.getAttribute("aria-required") === "true", limite: 0, opcoes: [], valor: valorLista(el),
      autocomplete: ""});
    return;
  }
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
return {url: location.href, titulos: limpo([document.title, ...Array.from(document.querySelectorAll("h1,h2")).slice(0, 8).map(textoDe)].join(" | ")).slice(0, 1500),
  texto: textoDe(document.body).slice(0, 4000), iframes: Array.from(document.querySelectorAll("iframe")).slice(0, 20).map(f => { const r = f.getBoundingClientRect();
    return {src: String(f.src || "").slice(0, 300), titulo: limpo(f.title).slice(0, 60), visivel: visivel(f), w: Math.round(r.width),
            h: Math.round(r.height), selo: !!f.closest(".grecaptcha-badge")}; }),
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
return {ok: a === el, tag: a ? a.tagName : "", tipo: a && a.type ? String(a.type).toLowerCase() : "", vazio: !(a && a.value),
        lista: ehLista(a)};
})(%s, %s)"""

JS_ESTADO_LISTA = "((chave) => {" + _COMUM + r"""
const el = achar(chave);
return el && ehLista(el) ? estadoLista(el) : null;
})(%s)"""

JS_SELECIONAR = "((chave, indice) => {" + _COMUM + r"""
const el = achar(chave);
if (!el || el.tagName !== "SELECT" || !el.options[indice]) return false;
Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(el, el.options[indice].value);
el.dispatchEvent(new Event("input", {bubbles: true}));
el.dispatchEvent(new Event("change", {bubbles: true}));
return el.selectedIndex === indice;
})(%s, %s)"""

JS_FOCAR_OPCAO = "((chave, indice) => {" + _COMUM + r"""
const el = grupoDe(chave)[indice];
if (!el || !["radio", "checkbox"].includes(el.type)) return {ok: false};
el.focus();
return {ok: document.activeElement === el, marcada: el.checked, tipo: el.type};
})(%s, %s)"""

JS_MARCADA = "((chave, indice) => {" + _COMUM + r"""
const el = grupoDe(chave)[indice];
return !!(el && el.checked);
})(%s, %s)"""

JS_SAIR = "(() => { const a = document.activeElement; if (a && a !== document.body && a.blur) a.blur(); return true; })()"

# ---------------------------------------------------------------- classificação (Python, testável sem navegador)

# "protegido por reCAPTCHA" no rodapé não é pedido de verificação: só frases de desafio e captcha visível contam
BLOQUEIO = re.compile(r"nao sou um robo|i'?m not a robot|(verifique|confirme) que voce e humano|verify(ing)? (that )?you are (a )?human|"
                      r"(resolva|complete|preencha) o captcha|(solve|complete) the captcha|"
                      r"codigo de verificacao|verification code|digite o codigo|enter the code|atividade (incomum|suspeita)|"
                      r"unusual activity|acesso bloqueado|access denied")
BLOQUEIO_IFRAME = re.compile(r"recaptcha|hcaptcha|turnstile|challenges\.cloudflare|captcha", re.I)
CAPTCHA_INVISIVEL = re.compile(r"[?&#]size=invisible", re.I)


def captcha_visivel(f) -> bool:
    """Um iframe de captcha que pede algo à pessoa: visível, fora do selo do reCAPTCHA invisível (canto da página) e sem
    size=invisible. Texto puro (formato antigo da leitura) conta como visível."""
    if isinstance(f, str):
        return bool(BLOQUEIO_IFRAME.search(f))
    if not isinstance(f, dict) or not BLOQUEIO_IFRAME.search(str(f.get("src") or "") + " " + str(f.get("titulo") or "")):
        return False
    if f.get("selo") or CAPTCHA_INVISIVEL.search(str(f.get("src") or "")):
        return False
    return bool(f.get("visivel")) and (f.get("w") or 0) >= 60 and (f.get("h") or 0) >= 40
TESTE = re.compile(r"teste (de perfil|comportamental|de logica|tecnico|de personalidade|de raciocinio|de ingles)|"
                   r"avaliacao (comportamental|tecnica|de perfil)|assessment|(gravar|gravacao de|envie um|enviar um) video|"
                   r"video (interview|recording)|tempo restante|time remaining|cronometro|desafio tecnico|coding challenge")
ACEITE = re.compile(r"\b(aceito|concordo|li e|i agree|i accept)\b")  # opção que é aceite de termos
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
    if tipo == "lista" and not c.get("opcoes"):
        return "outro", "lista que a ferramenta não conseguiu abrir: escolha você na janela"
    categoria = candidatura_ia.sensivel(c.get("rotulo") or "") or candidatura_ia.sensivel(c.get("nome") or "")
    if categoria:
        return "sensivel", f"{MOTIVOS['sensivel']} ({categoria})"
    if tipo == "caixa" and CONSENTIMENTO.search(rotulo):
        return "consentimento", MOTIVOS["consentimento"]
    if tipo in ("multipla", "unica") and any(ACEITE.search(_sem_acento(o.get("texto")))
                                            for o in c.get("opcoes") or []):
        return "consentimento", MOTIVOS["consentimento"]  # um aceite de termos nunca vai junto de outra resposta
    if tipo in ("texto", "selecao", "lista") and (
            c.get("tipo_html") in ("email", "tel", "url") or CADASTRO.search(rotulo)
            or AUTOCOMPLETE_CADASTRO.search(_sem_acento(c.get("autocomplete")))):
        return "cadastro", MOTIVOS["cadastro"]
    if tipo not in ("texto", "area", "selecao", "lista", "unica", "multipla", "caixa"):
        return "outro", MOTIVOS["outro"]
    if not rotulo.strip():
        return "outro", "campo sem pergunta legível: preencha você"
    return "comum", ""


def classificar_pagina(bruto: dict, campos: list[dict]) -> tuple[str, str]:
    """(etapa, aviso) da página."""
    texto, titulos = _sem_acento(bruto.get("texto")), _sem_acento(bruto.get("titulos"))
    if any(captcha_visivel(f) for f in bruto.get("iframes") or []) or BLOQUEIO.search(texto):
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
             "valor": str(c.get("valor") or "")[:300], "autocomplete": str(c.get("autocomplete") or "")[:60],
             "nome": str(c.get("nome") or "")[:100]}
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
    bruto = aba.avaliar(JS_LER)
    if isinstance(bruto, dict):  # listas com busca: as opções só aparecem com a lista aberta
        for c in [c for c in bruto.get("campos") or [] if isinstance(c, dict) and c.get("tipo") == "lista"][:20]:
            c["opcoes"] = [{"valor": str(i), "texto": t} for i, t in enumerate(_opcoes_lista(aba, c["chave"]))]
    return interpretar(bruto)


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


def _opcoes_lista(aba, chave: str) -> list[str]:
    """Abre a lista com busca (seta para baixo), lê as opções e fecha (Esc). Não escolhe nada."""
    foco = aba.avaliar(_js(JS_FOCAR, chave, False)) or {}
    if not foco.get("ok") or not foco.get("lista"):
        return []
    estado = None
    try:
        aba.tecla("ArrowDown")
        for _ in range(8):
            time.sleep(0.15)
            estado = aba.avaliar(_js(JS_ESTADO_LISTA, chave)) or {}
            if estado.get("opcoes"):
                break
    finally:
        aba.tecla("Escape")
        aba.avaliar(JS_SAIR)
    return [o["t"] for o in (estado or {}).get("opcoes") or [] if o.get("t")][:MAX_OPCOES]


def _escolher_na_lista(aba, chave: str, alvo: str) -> bool:
    """Escolhe a opção pelo texto: digita (a lista filtra), põe o destaque na opção exata (seta para baixo) e aperta Tab,
    que escolhe sem enviar nada. Confere que ficou escolhida; se não der, fecha (Esc) e devolve False."""
    foco = aba.avaliar(_js(JS_FOCAR, chave, False)) or {}
    if not foco.get("ok") or not foco.get("lista"):
        return False
    norm = lambda s: " ".join(_sem_acento(s).split())  # noqa: E731
    certo = norm(alvo)
    aba.digitar(alvo)
    for _ in range(40):
        time.sleep(0.15)
        estado = aba.avaliar(_js(JS_ESTADO_LISTA, chave)) or {}
        opcoes = estado.get("opcoes") or []
        if not estado.get("ativo") or not any(norm(o.get("t")) == certo for o in opcoes):
            break
        if any(o.get("foco") and norm(o.get("t")) == certo for o in opcoes):
            aba.tecla("Tab")
            time.sleep(0.25)
            return norm((aba.avaliar(_js(JS_ESTADO_LISTA, chave)) or {}).get("valor")) == certo
        aba.tecla("ArrowDown")
    aba.tecla("Escape")
    return False


def _escrever(aba, c: dict, valor, trocar: bool) -> bool:
    tipo = c["tipo"]
    if tipo in ("texto", "area"):
        valor = _cortar(valor, c["limite"])
        if c.get("tipo_html") == "number" and not re.fullmatch(r"-?\d+([.,]\d+)?", valor):
            return False
        return bool(valor) and _escrever_texto(aba, c, valor, trocar)
    if tipo == "lista":
        i = int(valor) if str(valor).isdigit() else -1
        return 0 <= i < len(c["opcoes"]) and _escolher_na_lista(aba, c["chave"], c["opcoes"][i]["texto"])
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


DA_PESSOA = {"comum", "sensivel", "cadastro"}  # o que a resposta da própria pessoa pode preencher


def preencher(aba, assinatura_lida: str, respostas: list, vaga: dict | None, da_pessoa: bool = False) -> dict:
    """Preenche os campos com as respostas ([{chave, valor, trocar}]). Confere o recurso ligado na vaga, o domínio e se a
    página ainda é a lida. Resposta da IA (da_pessoa=False) só vai em campo comum; a da pessoa (dada agora ou guardada)
    vai também em pergunta sensível e dado cadastral. Aceite de termos, arquivo, senha e o resto ficam na janela."""
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
        permitidas = DA_PESSOA if da_pessoa else {"comum"}
        preenchidos, ficaram, vistos = [], [], set()
        for r in respostas[:MAX_CAMPOS]:
            if not isinstance(r, dict) or r.get("chave") not in campos or r["chave"] in vistos:
                continue
            vistos.add(r["chave"])
            c = campos[r["chave"]]
            valor = r.get("valor")
            valor = ",".join(str(v) for v in valor) if isinstance(valor, list) else str(valor if valor is not None else "")
            item = {"chave": c["chave"], "rotulo": c["rotulo"], "marca": c["marca"], "tipo": c["tipo"], "nome": c.get("nome", "")}
            if c["marca"] not in permitidas:
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
            if c["chave"] not in vistos and c["marca"] not in permitidas:
                ficaram.append({"chave": c["chave"], "rotulo": c["rotulo"], "motivo": c["motivo"]})
        try:
            aba.avaliar(JS_SAIR)
        except Exception:  # noqa: BLE001  (tirar o foco é só cortesia)
            pass
        return {"preenchidos": preenchidos, "ficaram": ficaram,
                "aviso": "Confira na janela e clique você em Continuar ou Enviar."}
    finally:
        TRAVA.release()
