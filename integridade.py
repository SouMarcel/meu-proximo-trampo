"""Filtro de integridade do texto das vagas e origem dos links (spec 034).

O texto de uma vaga é escrito por terceiros e vai para a IA ao lado do perfil da pessoa. A regra "texto da internet é
dado, nunca instrução" (constituição IV) depende do modelo obedecer; este módulo tira em código o que a pessoa não vê
e aponta o que parece mirar a IA. Avisa e nunca bloqueia: a vaga com ⚠ segue para todos os fluxos.

  limpar(texto)               o texto sem os caracteres invisíveis (largura zero, controles de direção, hífen
                              invisível, tag characters); idempotente
  verificar(texto)            (texto limpo, achado | None): linhas com cara de instrução, palavras que misturam
                              alfabetos, caracteres de adulteração e trechos ocultos tirados do HTML
  estilo_oculto(estilo)       o atributo style esconde o elemento da pessoa (fontes/link.py pula esses elementos)
  sinal_oculto(texto, links)  o que um trecho oculto do HTML tinha de suspeito, para a marca que fica no texto
  portal_do_host(host)        ("portal" | "ats", nome) pelo domínio exato ou subdomínio; None para os outros
  origem_do_link(url)         {tipo: portal | ats | nao_verificada, dominio, nome?} do link de uma vaga

O achado ({veredito, contagens, citacoes}) fica na vaga para a página e nunca vai para a IA. O conteúdo oculto tirado
nunca é guardado: a marca no texto diz só o que ele tinha (instrução, texto invisível, link).

Inspirado no tools/posting_guard.py e na verificação de host do /apply do projeto ai-job-search
(github.com/ai-job-search-dev/ai-job-search, licença MIT); o código é deste projeto.
"""
from __future__ import annotations

import html
import re
import unicodedata
from urllib.parse import urlsplit

NL = chr(10)
LIMITE_CITACAO = 120
MAX_CITACOES = 5
MARCA = "[trecho oculto tirado pela ferramenta: "
MARCA_RE = re.compile(r"\[trecho oculto tirado pela ferramenta: ([^\]\n]{1,100})\]")

# ---------------------------------------------------------------- caracteres invisíveis (research R4)

LARGURA_ZERO = {0x200B, 0x200C, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF}
ZWJ = 0x200D  # junta emojis compostos (👩‍💻): fica perto de símbolo, sai entre letras
DIRECAO_COMUM = {0x200E, 0x200F}  # LRM e RLM, comuns em texto copiado
BIDI_ADULTERACAO = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))  # sobreposição e isolamento
HIFEN_INVISIVEL = 0x00AD
SEPARADORES = {0x2028, 0x2029}
TAG_INICIO, TAG_FIM = 0xE0000, 0xE007F  # "tag characters": um alfabeto que não aparece na tela e a IA lê
PLANO_14_FIM = 0xE01EF  # depois das tags, seletores de variação e códigos vazios: também invisíveis
BANDEIRA_PRETA = 0x1F3F4  # 🏴 + tags + U+E007F = bandeiras da Inglaterra, da Escócia e do País de Gales
BANDEIRAS = {"gbeng", "gbsct", "gbwls"}
ESPECIAIS = re.compile("[­​-‏ -‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e01ef]")
BANDEIRA = re.compile("\U0001f3f4([\U000e0061-\U000e007a]{5})\U000e007f")


def _varrer(texto: str) -> tuple[str, int, int]:
    """(texto sem os invisíveis, quantos saíram sem sinal, quantos indicam adulteração). Só olha as posições dos
    caracteres especiais; o resto do texto é copiado em pedaços."""
    if not ESPECIAIS.search(texto):
        return texto, 0, 0
    bandeiras = [(m.start(1), m.end()) for m in BANDEIRA.finditer(texto)
                 if "".join(chr(ord(x) - TAG_INICIO) for x in m.group(1)) in BANDEIRAS]
    saida: list[str] = []
    invisiveis = adulteracao = 0
    ultimo, n = 0, len(texto)
    for m in ESPECIAIS.finditer(texto):
        i = m.start()
        if i < ultimo:
            continue
        if any(a <= i < b for a, b in bandeiras):
            continue  # tag de uma bandeira: fica
        saida.append(texto[ultimo:i])
        ultimo = i + 1
        o = ord(texto[i])
        if TAG_INICIO <= o <= PLANO_14_FIM or o in BIDI_ADULTERACAO:
            adulteracao += 1
        elif o in SEPARADORES:
            saida.append(NL)
        elif o == ZWJ or o in LARGURA_ZERO:
            antes = next((s[-1] for s in reversed(saida) if s), "")
            depois = texto[i + 1] if i + 1 < n else ""
            entre_letras = antes.isalpha() and depois.isalpha()
            if o == ZWJ and not entre_letras and antes and not antes.isalnum() and not antes.isspace():
                saida.append(texto[i])  # emoji composto
            elif entre_letras:
                adulteracao += 1  # quebra a palavra e escapa de qualquer busca por padrão
            else:
                invisiveis += 1
        else:  # LRM/RLM e hífen invisível
            invisiveis += 1
    saida.append(texto[ultimo:])
    return "".join(saida), invisiveis, adulteracao


def limpar(texto) -> str:
    """O texto sem os caracteres invisíveis; o resto fica igual."""
    return _varrer(str(texto or ""))[0]


# ---------------------------------------------------------------- linhas com cara de instrução (research R5)

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(s.split())


_IA_EN = r"(?:ai|a\.i\.|llm|large language model|language model|ai (?:model|assistant|agent|screener|recruiter|system)|chatbot|bot|chatgpt|gpt|claude|gemini)"
_IA_PT = r"(?:ia|inteligencia artificial|modelo de linguagem|modelo de ia|assistente(?: de ia| virtual)?|robo|chatbot|llm)"
INSTRUCOES = [re.compile(p) for p in (  # sobre o texto sem acento e em minúsculas
    # ignorar as instruções anteriores
    r"\b(?:ignore|disregard|forget|override|bypass)\b (?:all |any )?(?:of )?(?:your |the |my )?"
    r"(?:previous|prior|above|earlier|preceding|former|original|system)\b.{0,20}\b"
    r"(?:instructions?|prompts?|rules|directions|guidelines|guidance)\b",
    r"\b(?:ignore|disregard)\b (?:all|any) (?:other |of the |the |your )?(?:instructions|prompts)\b",
    r"\b(?:ignore|ignorem|desconsidere|desconsiderem|esqueca|esquecam)\b (?:todas )?(?:as |os )?(?:suas )?"
    r"(?:instrucoes|instrucao|regras|orientacoes|comandos|prompts?)\b (?:anteriores|acima|previas|dadas|recebidas|do sistema)\b",
    r"\b(?:ignore|ignorem|desconsidere|desconsiderem|esqueca|esquecam)\b todas as (?:suas )?(?:instrucoes|regras|orientacoes)\b",
    # falar direto com a IA
    rf"\bif you(?: are|'re) an? {_IA_EN}(?:\s*[,.:;!]|\s*$| (?:reading|reviewing|evaluating|screening|parsing|processing|scoring|analy[sz]ing)\b| (?:and|who|that) )",
    rf"\bse voce (?:e|for|esta sendo) (?:uma? )?{_IA_PT}(?:\s*[,.:;!]|\s*$| (?:lendo|avaliando|analisando|processando)\b| que )",
    rf"\b(?:note|attention|message|instructions?|notice) (?:to|for) (?:the |any )?{_IA_EN}\s*:",
    rf"\b(?:atencao|aviso|nota|instrucao|instrucoes|mensagem)\s*,?\s*(?:(?:para|a|ao) )?(?:a |o )?{_IA_PT}\s*:",
    rf"^(?:attention|note|hey|dear)\s*,?\s*{_IA_EN}\s*:",
    r"\byou are now (?:an? )?(?:ai|assistant|language model|llm|chatbot|dan|in developer mode)\b",
    r"\bvoce (?:agora )?e (?:agora )?uma? (?:ia|inteligencia artificial|modelo de linguagem)\s*(?:[,.:;!]|$| e | que )",
    # mudar a nota
    r"\b(?:give|assign|award)\b.{0,30}\b(?:this|the)\b.{0,20}\b(?:job|posting|position|role|vacancy|candidate|applicant|application)\b"
    r".{0,30}\b(?:score|rating|grade|mark|fit score)\b.{0,15}\b(?:100|10/10|maximum|max|highest|perfect|full)\b",
    r"\b(?:rate|score|grade|rank)\b (?:this|the) (?:job|posting|position|role|vacancy|candidate|applicant|application) "
    r"(?:as |at |with )?(?:a |an )?(?:100|10/10|perfect|maximum|highest|excellent|strong fit|perfect fit|perfect match|top)\b",
    # papéis e marcações de conversa
    r"^(?:system|developer) (?:prompt|message|instructions?)\s*:",
    r"^assistant\s*:",
    r"\bprompt do sistema\s*:",
    r"\[/?inst\]|<\|(?:im_start|im_end|system|user|assistant|endoftext)\|>",
    # esconder as instruções
    r"\bdo not (?:mention|reveal|disclose|tell)\b.{0,20}\b(?:these|this|the) (?:instructions?|message|note|prompt)\b",
    r"\bnao (?:mencione|revele|conte|diga)\b.{0,20}\b(?:esta|estas|essa|essas) (?:instrucao|instrucoes|mensagem|orientacao)\b",
)]


COM_ACENTO = [re.compile(p) for p in (  # sobre o texto em minúsculas com acento: sem o acento, "dê" vira "de"
    r"\b(?:dê|dêem|atribua|atribuam|coloque|ponha|marque)\b.{0,30}\bnota\b.{0,15}(?:\bmáxima\b|\b100\b|\b10\b|\bdez\b|\bcem\b)",
    r"\b(?:dê|atribua|coloque)\b.{0,20}\b(?:aderência|pontuação)\b.{0,15}(?:\bmáxima\b|\b100\b|\btotal\b)",
)]


def _instrucao(linha: str) -> bool:
    n = _norm(linha)
    if not n:
        return False
    if any(p.search(n) for p in INSTRUCOES):
        return True
    baixa = " ".join(unicodedata.normalize("NFC", linha).lower().split())
    return any(p.search(baixa) for p in COM_ACENTO)


# ---------------------------------------------------------------- alfabetos misturados (research R6)

PALAVRA = re.compile(r"\w{4,}")


def _misturada(palavra: str) -> bool:
    latina = cirilica = grega = False
    for c in palavra:
        o = ord(c)
        if c.isalpha() and o < 0x250:
            latina = True
        elif 0x400 <= o <= 0x4FF:
            cirilica = True
        elif 0x370 <= o <= 0x3FF:
            grega = True
    return latina and (cirilica or grega)


# ---------------------------------------------------------------- HTML oculto (research R2/R3)

LINK = re.compile(r"https?://[^\s\"'<>)\]]+|\bwww\.[^\s\"'<>)\]]+", re.I)


def _zero(v: str | None) -> bool:
    return bool(v) and bool(re.fullmatch(r"[+-]?0*\.?0+(?:px|em|rem|pt|%|vw|vh|ex|ch)?", v))


def _longe(v: str | None) -> bool:
    m = re.fullmatch(r"-(\d+(?:\.\d+)?)(px|em|rem|pt|vw|vh|%)?", v or "")
    if not m:
        return False
    return float(m.group(1)) >= (999 if m.group(2) in (None, "px", "pt") else 50)


def estilo_oculto(estilo) -> bool:
    """O style esconde o elemento de quem olha a página (o navegador lê o style decodificado e sem comentários)."""
    s = re.sub(r"/\*.*?\*/", "", html.unescape(str(estilo or "")), flags=re.S).lower()
    d: dict[str, str] = {}
    for parte in s.split(";"):
        prop, _, valor = parte.partition(":")
        prop, valor = prop.strip(), " ".join(valor.replace("!important", "").split())
        if prop and valor:
            d[prop] = valor
    if d.get("display") == "none" or d.get("visibility") in ("hidden", "collapse"):
        return True
    if _zero(d.get("opacity")) or _zero(d.get("font-size")):
        return True
    cor = d.get("color", "").replace(" ", "")
    if cor == "transparent" or re.fullmatch(r"(?:rgba|hsla)\([^)]*,0*\.?0+\)", cor):
        return True
    clip = d.get("clip", "")
    if clip.startswith("rect(") and all(_zero(x) or x in ("1px", "1") for x in re.split(r"[,\s]+", clip[5:].rstrip(")")) if x):
        return True
    if re.fullmatch(r"inset\(\s*(?:50|[5-9]\d|100)%\s*\)", d.get("clip-path", "")):
        return True
    if any(_longe(d.get(k)) for k in ("left", "top", "text-indent", "margin-left", "margin-top")):
        return True
    escondendo = "hidden" in (d.get("overflow"), d.get("overflow-x"), d.get("overflow-y"))
    return escondendo and any(_zero(d.get(k)) for k in ("height", "width", "max-height", "max-width"))


def _host(url: str) -> str:
    try:
        h = urlsplit(url if "://" in url else "https://" + url).hostname or ""
    except ValueError:
        return ""
    return h.lower().removeprefix("www.")


def sinal_oculto(texto, links=(), com_links: bool = True) -> str | None:
    """O que o trecho oculto tinha de suspeito: "instrução para a IA", "texto invisível", "link para <host>" ou None.
    com_links=False para script e style, onde link é coisa da página (fontes, estatísticas), não da vaga."""
    texto = str(texto or "")
    limpo, _, adulteracao = _varrer(texto)
    if any(_instrucao(linha) for linha in limpo.split(NL)):
        return "instrução para a IA"
    if adulteracao:
        return "texto invisível"
    if not com_links:
        return None
    hosts = [h for h in (_host(u) for u in [*links, *LINK.findall(limpo)]) if h]
    if hosts:
        return "link para " + hosts[0][:60]
    return None


# ---------------------------------------------------------------- verificar

def verificar(texto) -> tuple[str, dict | None]:
    """(texto limpo, achado): o achado é {veredito, contagens, citacoes} (spec 034, data-model) ou None."""
    limpo, invisiveis, adulteracao = _varrer(str(texto or ""))
    cont = {"invisiveis": invisiveis, "adulteracao": adulteracao, "instrucoes": 0, "alfabetos": 0, "ocultos": 0,
            "links_ocultos": 0}
    citacoes: list[dict] = []

    def citar(tipo: str, trecho: str) -> None:
        if len(citacoes) < MAX_CITACOES and not any(c["trecho"] == trecho for c in citacoes):
            citacoes.append({"tipo": tipo, "trecho": trecho[:LIMITE_CITACAO]})

    if not limpo.strip() and not (invisiveis or adulteracao):
        return limpo, None
    for linha in limpo.split(NL):
        marcas = MARCA_RE.findall(linha)
        for o_que in marcas:
            if o_que.startswith("link"):
                cont["links_ocultos"] += 1
                citar("link_oculto", f"trecho oculto com {o_que} (tirado)")
            else:
                cont["ocultos"] += 1
                if o_que.startswith("instru"):
                    cont["instrucoes"] += 1
                else:
                    cont["adulteracao"] += 1
                citar("oculto", f"trecho oculto com {o_que} (tirado)")
        resto = MARCA_RE.sub("", linha) if marcas else linha
        if _instrucao(resto):
            cont["instrucoes"] += 1
            citar("instrucao", resto.strip())
        for palavra in PALAVRA.findall(resto):
            if _misturada(palavra):
                cont["alfabetos"] += 1
                citar("alfabetos", palavra)
    if adulteracao:
        citar("adulteracao", f"{adulteracao} caractere(s) invisível(is) de adulteração (tirados)")
    cont = {k: v for k, v in cont.items() if v}
    if not cont:
        return limpo, None
    atencao = cont.get("instrucoes") or cont.get("adulteracao") or cont.get("alfabetos")
    return limpo, {"veredito": "atencao" if atencao else "limpo", "contagens": cont, "citacoes": citacoes}


SO_NO_ORIGINAL = ("invisiveis", "adulteracao")  # caracteres que o texto limpo não tem mais para contar


def juntar(antigo: dict | None, novo: dict | None) -> dict | None:
    """O achado de um texto já limpo (novo) com o que só o texto original mostrava (antigo): os caracteres invisíveis
    e de adulteração tirados antes. Sem isso, rever uma vaga já limpa apagaria o ⚠ do texto invisível."""
    if not antigo:
        return novo
    cont = dict((novo or {}).get("contagens") or {})
    for k in SO_NO_ORIGINAL:
        n = max(cont.get(k, 0), (antigo.get("contagens") or {}).get(k, 0))
        if n:
            cont[k] = n
    if not cont:
        return None
    citacoes = list((novo or {}).get("citacoes") or [])
    for c in antigo.get("citacoes") or []:
        if c.get("tipo") == "adulteracao" and c not in citacoes and len(citacoes) < MAX_CITACOES:
            citacoes.append(c)
    atencao_ = cont.get("instrucoes") or cont.get("adulteracao") or cont.get("alfabetos")
    return {"veredito": "atencao" if atencao_ else "limpo", "contagens": cont, "citacoes": citacoes}


def atencao(texto, achado: dict | None = None) -> bool:
    """O texto tem sinal de que mirou a IA (o que vale um pedido de nota só para ele). achado: o que já foi gravado
    na vaga, que guarda o que o texto limpo não mostra mais (caracteres invisíveis tirados)."""
    if (achado or {}).get("veredito") == "atencao":
        return True
    novo = verificar(texto)[1]
    return bool(novo) and novo["veredito"] == "atencao"


# ---------------------------------------------------------------- domínios (research R8)

PORTAIS = {  # nome no dashboard -> domínios; o host casa pelo domínio exato ou por subdomínio
    "LinkedIn": ("linkedin.com", "lnkd.in"),
    "Gupy": ("gupy.io",),
    "InHire": ("inhire.app", "inhire.com.br"),
    "Catho": ("catho.com.br",),
    "Startup Jobs": ("startup.jobs",),
    "Nerdin": ("nerdin.com.br",),
    "InfoJobs": ("infojobs.com.br",),
    "Vagas.com": ("vagas.com.br",),
    "JobGether": ("jobgether.com",),
    "Remotive": ("remotive.com", "remotive.io"),
    "Himalayas": ("himalayas.app",),
    "RemoteOK": ("remoteok.com", "remoteok.io"),
    "Jobicy": ("jobicy.com",),
    "We Work Remotely": ("weworkremotely.com",),
    "Get on Board": ("getonbrd.com", "getonboard.com"),
}
INDEED = re.compile(r"(?:^|\.)indeed\.(?:com|[a-z]{2}|(?:com|co)\.[a-z]{2})$")
ATS = {  # sistemas de vaga oficiais das empresas
    "Greenhouse": ("greenhouse.io",),
    "Lever": ("lever.co",),
    "Ashby": ("ashbyhq.com",),
    "Workday": ("myworkdayjobs.com",),
    "SmartRecruiters": ("smartrecruiters.com",),
    "Workable": ("workable.com",),
}


def casa(host: str, dominio: str) -> bool:
    """O host é o domínio ou um subdomínio dele ("x.gupy.io" casa com "gupy.io"; "gupy.io.exemplo.com" não)."""
    host, dominio = (host or "").lower().rstrip("."), (dominio or "").lower()
    return bool(host) and (host == dominio or host.endswith("." + dominio))


def portal_do_host(host: str) -> tuple[str, str] | None:
    host = (host or "").lower().rstrip(".")
    if INDEED.search(host):
        return "portal", "Indeed"
    for tipo, tabela in (("portal", PORTAIS), ("ats", ATS)):
        for nome, dominios in tabela.items():
            if any(casa(host, d) for d in dominios):
                return tipo, nome
    return None


def origem_do_link(url) -> dict | None:
    """{tipo, dominio, nome?} do link; None se o link não tem host. O usuario@ antes do host nunca conta."""
    try:
        host = (urlsplit(str(url or "").strip()).hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if not host:
        return None
    dominio = host.removeprefix("www.")
    achado = portal_do_host(host)
    if not achado:
        return {"tipo": "nao_verificada", "dominio": dominio}
    return {"tipo": achado[0], "dominio": dominio, "nome": achado[1]}
