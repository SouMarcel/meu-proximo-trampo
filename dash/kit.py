"""Kit de candidatura: o que a análise lê sobre a candidatura, o checklist "o que esta candidatura pede" e os
lembretes de follow-up do quadro.

O checklist e os lembretes saem só dos dados da vaga e do que a pessoa marcou, sem IA: itens de toda vaga
(currículo e candidatura), o que a análise apontou (`pede`), o que o anúncio diz com palavras conhecidas e os
itens que a pessoa acrescentou. Nada aqui gera texto nem envia nada; os botões só abrem o que a pessoa pediu.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

AUTORIZACAO = {"patrocina": "Patrocina visto", "nao_precisa": "Você não precisa de patrocínio",
               "omisso": "O anúncio não diz", "nao_patrocina": "Não patrocina visto"}
CONTRATACAO = {"contractor": "Contractor (você emite nota)", "eor": "Por EOR (Deel, Remote…)",
               "empregado_brasil": "Empregado no Brasil", "relocation": "Com relocation", "clt": "CLT", "pj": "PJ"}
INGLES = {"nao_pede": "Não pede", "basico": "Básico", "intermediario": "Intermediário", "fluente": "Fluente",
          "nativo": "Nativo"}
PEDE = {"curriculo_ingles": "Currículo em inglês", "carta": "Carta de apresentação", "formulario": "Respostas de formulário",
        "portfolio": "Portfólio", "teste": "Teste técnico", "video": "Vídeo de apresentação"}
RISCOS = {"remuneracao": "Remuneração pouco confiável", "remoto_hibrido": "“Remoto” que é híbrido"}
ESTADOS = {"a_fazer": "A fazer", "pronto": "Pronto", "nao_se_aplica": "Não se aplica"}
LEMBRETES = {"follow1": "Hora do follow-up", "follow2": "2º follow-up", "agradecimento": "Agradecer a entrevista"}
ESTADOS_LEMBRETE = ("feito", "dispensado")
ACOES = {"curriculo": "curriculo", "carta": "carta", "formulario": "respostas", "candidatura": "candidatar"}
TAMANHO_FRASE = 200
MAX_EXTRAS, TAMANHO_EXTRA = 10, 80
DIAS_FOLLOW = (("follow1", 7), ("follow2", 14))
# o que o anúncio pede, reconhecido sem IA (sem acento, minúsculas)
PALAVRAS = {
    "carta": ("cover letter", "carta de apresentacao", "motivation letter", "carta de motivacao", "letter of motivation"),
    "formulario": ("application form", "screening questions", "questionnaire", "questionario", "formulario de candidatura"),
    "portfolio": ("portfolio",),
    "teste": ("take-home", "take home", "coding challenge", "technical test", "technical assessment", "home assignment",
              "teste tecnico", "desafio tecnico", "case tecnico", "teste pratico", "prova tecnica"),
    "video": ("video introduction", "intro video", "short video", "record a video", "loom video", "video de apresentacao",
              "grave um video"),
}

# item que a pessoa acrescenta com o nome de um item conhecido vira esse item (com o botão de ajuda)
NOMES_ITENS = {
    "carta": ("carta", "carta de apresentacao", "cover letter", "carta de motivacao", "motivation letter"),
    "formulario": ("formulario", "respostas de formulario", "perguntas do formulario", "respostas", "application form",
                   "questionario"),
    "portfolio": ("portfolio",),
    "teste": ("teste", "teste tecnico", "desafio tecnico", "take-home", "take home"),
    "video": ("video", "video de apresentacao"),
}


def _sem_acento(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def _frase(v) -> str:
    return " ".join(str(v or "").split())[:TAMANHO_FRASE]


# ---------------------------------------------------------------- análise

def validar_analise(a: dict) -> dict:
    """Os campos da análise sobre a candidatura, limpos. Valor fora das opções faz o campo cair (a análise
    segue); a frase do anúncio vem junto de cada um."""
    limpos = {}

    def um(chave, campo, opcoes):
        x = a.get(chave)
        if isinstance(x, dict) and x.get(campo) in opcoes:
            limpos[chave] = {campo: x[campo], "frase": _frase(x.get("frase"))}

    def varios(chave, campo, opcoes, maximo):
        x = a.get(chave)
        if isinstance(x, list):
            itens, vistos = [], set()
            for i in x:
                if isinstance(i, dict) and i.get(campo) in opcoes and i[campo] not in vistos:
                    vistos.add(i[campo])
                    itens.append({campo: i[campo], "frase": _frase(i.get("frase"))})
            if itens:
                limpos[chave] = itens[:maximo]

    um("autorizacao", "valor", AUTORIZACAO)
    um("ingles", "nivel", INGLES)
    varios("contratacao", "valor", CONTRATACAO, 4)
    varios("pede", "item", PEDE, 6)
    varios("riscos", "tipo", RISCOS, 4)
    fuso = a.get("fuso")
    if isinstance(fuso, dict) and str(fuso.get("texto") or "").strip():
        limpos["fuso"] = {"texto": " ".join(str(fuso["texto"]).split())[:80], "frase": _frase(fuso.get("frase"))}
    sistema = " ".join(str(a.get("sistema_candidatura") or "").split())[:40]
    if sistema:
        limpos["sistema_candidatura"] = sistema
    return limpos


# ---------------------------------------------------------------- o que a pessoa marca

def _id_extra(texto: str) -> str:
    return "x:" + re.sub(r"[^a-z0-9]+", "-", _sem_acento(texto)).strip("-")[:40]


def validar_kit(d) -> dict:
    """Estado do checklist que a pessoa marcou: {estados: {item: estado}, extras: [texto], removidos: [item]}."""
    if not isinstance(d, dict):
        raise ValueError("kit inválido")
    estados = d.get("estados") or {}
    if not isinstance(estados, dict) or any(e not in ESTADOS for e in estados.values()):
        raise ValueError(f"estado do item deve ser um de {tuple(ESTADOS)}")
    extras, vistos = [], set()
    for x in d.get("extras") or []:
        x = " ".join(str(x).split())[:TAMANHO_EXTRA]
        if x and _id_extra(x) not in vistos:
            vistos.add(_id_extra(x))
            extras.append(x)
    if len(extras) > MAX_EXTRAS:
        raise ValueError(f"no máximo {MAX_EXTRAS} itens seus no checklist")
    removidos = [str(x)[:60] for x in d.get("removidos") or [] if str(x).strip()][:20]
    return {"estados": {str(k)[:60]: v for k, v in estados.items()}, "extras": extras, "removidos": removidos}


def validar_lembretes(d) -> dict:
    """Lembretes marcados: {base: "etapa:AAAA-MM-DD", follow1|follow2|agradecimento: feito|dispensado, parar}."""
    if not isinstance(d, dict):
        raise ValueError("lembretes inválidos")
    base = str(d.get("base") or "")
    if not re.fullmatch(r"(aplicada|entrevista):\d{4}-\d{2}-\d{2}", base):
        raise ValueError("lembretes: base inválida")
    limpos = {"base": base, "parar": bool(d.get("parar"))}
    for tipo in LEMBRETES:
        if d.get(tipo) is not None:
            if d[tipo] not in ESTADOS_LEMBRETE:
                raise ValueError(f"lembrete deve ser um de {ESTADOS_LEMBRETE}")
            limpos[tipo] = d[tipo]
    return limpos


# ---------------------------------------------------------------- checklist

def _no_anuncio(descricao) -> list[tuple[str, str]]:
    """Itens que o anúncio pede, reconhecidos por palavras conhecidas, com o trecho em volta."""
    texto = " ".join(str(descricao or "").split())
    base = _sem_acento(texto)
    achados = []
    for item, palavras in PALAVRAS.items():
        for p in palavras:
            m = re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", base)
            if m:
                inicio = max(0, m.start() - 60)
                achados.append((item, ("…" if inicio else "") + texto[inicio:m.end() + 60].strip() + "…"))
                break
    return achados


def checklist(v: dict) -> list[dict]:
    """O checklist da vaga: [{item, rotulo, origem (vaga|analise|anuncio|pessoa), estado, frase, acao}]."""
    marcado = v.get("kit") if isinstance(v.get("kit"), dict) else {}
    estados, removidos = marcado.get("estados") or {}, set(marcado.get("removidos") or [])
    itens: dict[str, dict] = {}

    def por(item, origem, rotulo, frase=""):
        if item not in itens:
            itens[item] = {"item": item, "rotulo": rotulo, "origem": origem, "frase": frase}

    pede = [p for p in v.get("pede") or [] if isinstance(p, dict)]
    ingles = next((p for p in pede if p.get("item") == "curriculo_ingles"), None)
    if ingles or v.get("idioma") == "en":
        por("curriculo", "analise" if ingles else "vaga", PEDE["curriculo_ingles"], (ingles or {}).get("frase", ""))
    else:
        por("curriculo", "vaga", "Currículo")
    for p in pede:
        if p.get("item") in PEDE and p["item"] != "curriculo_ingles":
            por(p["item"], "analise", PEDE[p["item"]], p.get("frase", ""))
    for item, frase in _no_anuncio(v.get("descricao")):
        por(item, "anuncio", PEDE[item], frase)
    for texto in marcado.get("extras") or []:
        conhecido = next((k for k, nomes in NOMES_ITENS.items() if _sem_acento(texto).strip(" .") in nomes), None)
        por(conhecido or _id_extra(texto), "pessoa", PEDE[conhecido] if conhecido else texto)
        if itens[conhecido or _id_extra(texto)]["origem"] == "pessoa":
            itens[conhecido or _id_extra(texto)].setdefault("extra", texto)  # para tirar, sai da lista da pessoa
    por("candidatura", "vaga", "Enviar a candidatura")
    saida = []
    for i in itens.values():
        if i["item"] in removidos:
            continue
        saida.append({**i, "estado": estados.get(i["item"], "a_fazer"), "acao": ACOES.get(i["item"])})
    return saida


# ---------------------------------------------------------------- lembretes

def _data(v) -> date | None:
    try:
        return date.fromisoformat(str(v or "")[:10])
    except ValueError:
        return None


def lembretes(v: dict, hoje: date | None = None) -> list[dict]:
    """O lembrete pendente da vaga no quadro (no máximo um): follow-up aos 7 e aos 14 dias em Aplicação Enviada
    (o 2º substitui o 1º; não há 3º) e agradecimento no dia seguinte à entrevista. Só lembra; a pessoa marca
    "feito", "dispensar" ou para os lembretes da vaga."""
    hoje = hoje or date.today()
    etapa, desde = v.get("etapa"), _data(v.get("etapa_em"))
    if etapa not in ("aplicada", "entrevista") or not desde:
        return []
    base = f"{etapa}:{desde.isoformat()}"
    marcado = v.get("lembretes") if isinstance(v.get("lembretes"), dict) else {}
    if marcado.get("base") != base:
        marcado = {}  # a vaga mudou de etapa: o que foi marcado antes não vale
    if marcado.get("parar"):
        return []
    if etapa == "aplicada":
        devidos = [(tipo, desde + timedelta(days=dias)) for tipo, dias in DIAS_FOLLOW if hoje >= desde + timedelta(days=dias)]
        if not devidos or marcado.get(devidos[-1][0]):
            return []  # o mais recente vale; resolvido o 2º, acabou
        tipo, quando = devidos[-1]
    else:
        quando = (_data(v.get("entrevista_em")) or desde) + timedelta(days=1)
        tipo = "agradecimento"
        if hoje < quando or marcado.get(tipo):
            return []
    return [{"tipo": tipo, "rotulo": LEMBRETES[tipo], "desde": quando.isoformat(), "base": base}]
