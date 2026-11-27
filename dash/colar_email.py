"""Leitura e classificação de e-mails de candidaturas colados pela pessoa (spec 063).

Reconhece o tipo do e-mail (recebida, entrevista, proposta, negativa, cancelada, desistencia,
contratacao), casa com as candidaturas no quadro e monta a proposta de mudança de etapa,
sem IA e sem tocar no banco de dados.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(1, str(RAIZ))
if str(RAIZ / "dash") not in sys.path:
    sys.path.insert(1, str(RAIZ / "dash"))

import banco  # noqa: E402
import contas  # noqa: E402
import integridade  # noqa: E402

TIPOS = ("recebida", "entrevista", "proposta", "negativa", "cancelada", "desistencia", "contratacao")

ROTULOS = {
    "recebida": "candidatura recebida",
    "entrevista": "convite para entrevista ou teste",
    "proposta": "proposta",
    "negativa": "negativa",
    "cancelada": "vaga cancelada",
    "desistencia": "desistência",
    "contratacao": "contratação",
}

MUDANCA = {
    "recebida": {"etapa": "aplicada", "resultado": None},
    "entrevista": {"etapa": "entrevista", "resultado": None},
    "proposta": {"etapa": "proposta", "resultado": None},
    "negativa": {"etapa": "encerrada", "resultado": "nao_aprovado"},
    "cancelada": {"etapa": "encerrada", "resultado": "cancelada"},
    "desistencia": {"etapa": "encerrada", "resultado": "desisti"},
    "contratacao": {"etapa": "encerrada", "resultado": "contratado"},
}

MAX_EMAILS = 20
MAX_CARACTERES = 20000
MAX_TRECHO = 240

CABECALHO_RE = re.compile(
    r"^\s*(?:de|from|para|to|cc|cco|bcc|assunto|subject|data|date|enviado|enviada em|sent|responder a|reply-to)\s*:",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
EMAIL_RE = re.compile(r"<?\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b>?", re.IGNORECASE)

RE_NAO_PROPOSTA = re.compile(
    r"\b(?:nao|not|no)\s+(?:temos|ha|tem|have|tenemos)\s+(?:uma\s+|an?\s+|una\s+)?(?:proposta|offer|oferta)\b"
)

PADROES: list[tuple[str, re.Pattern]] = [
    (
        "contratacao",
        re.compile(
            r"\b(?:seja bem[- ]vinda?|bem[- ]vinda? ao time|bem[- ]vinda? a equipe|"
            r"parabens pela contratacao|welcome aboard|you have been hired|"
            r"you(?:'re| are) hired|welcome to the team|bienvenid[oa] al equipo|"
            r"felicitaciones por tu contratacion|has sido contratad[oa]|"
            r"te damos la bienvenida)\b"
        ),
    ),
    (
        "proposta",
        re.compile(
            r"\b(?:proposta de (?:trabalho|emprego|contratacao)|carta (?:proposta|oferta)|"
            r"temos o prazer de (?:lhe )?(?:oferecer|fazer uma proposta)|"
            r"fazer uma proposta de (?:trabalho|emprego|contratacao)|"
            r"job offer|offer letter|pleased to offer|delighted to offer|"
            r"oferta (?:de empleo|laboral)|carta de oferta)\b"
        ),
    ),
    (
        "negativa",
        re.compile(
            r"\b(?:infelizmente|segui(?:r|mos) com outros? candidat|"
            r"nao (?:foi|fomos) (?:selecionad|aprovad)|nao (?:vamos|iremos|podemos) avancar|"
            r"nao avancar|optamos por (?:seguir|prosseguir) com|"
            r"decidimos (?:seguir|prosseguir|avancar) com outr|"
            r"unfortunately|not (?:be )?moving forward|"
            r"will not (?:be )?(?:moving|proceeding) forward|"
            r"decided to (?:move|proceed) (?:forward )?with other|"
            r"other candidates|pursuing other candidates|not selected|unsuccessful|"
            r"lamentablemente|no continuar|no vamos a continuar|no continuaremos|"
            r"decidido (?:avanzar|seguir) con otr|otros candidatos|"
            r"nao foi dessa vez|nao seguiremos com|nao has sido seleccionad)\b"
        ),
    ),
    (
        "cancelada",
        re.compile(
            r"\b(?:vaga|posicao|processo seletivo|processo)\b[^\n.!?]{0,80}\b(?:foi )?(?:cancelad[oa]|encerrad[oa]|congelad[oa]|suspens[oa])\b|"
            r"\b(?:position|role|job)\b[^\n.!?]{0,80}\b(?:has been |is |was )?(?:cancelled|canceled|closed|put on hold|suspended)\b|"
            r"\brole (?:is )?no longer available|"
            r"\b(?:vacante|posicion|proceso de seleccion|proceso)\b[^\n.!?]{0,80}\b(?:ha sido )?(?:cancelad[oa]|cerrad[oa]|suspendid[oa])\b"
        ),
    ),
    (
        "desistencia",
        re.compile(
            r"\b(?:(?:sua|a) desistencia|retirou (?:sua|a) candidatura|"
            r"cancelou (?:sua|a) candidatura|desistencia (?:confirmada|registrada)|"
            r"you (?:have )?withdrawn|withdrew your application|"
            r"application (?:has been )?withdrawn|"
            r"retiraste tu (?:candidatura|postulacion)|"
            r"has retirado tu (?:candidatura|postulacion))\b"
        ),
    ),
    (
        "entrevista",
        re.compile(
            r"\b(?:entrevista|teste tecnico|desafio tecnico|case tecnico|"
            r"(?<!\bin )(?<!\bany )(?<!\bthis )case|"
            r"proxima (?:fase|etapa|rodada)|agendar (?:uma )?(?:conversa|entrevista|reuniao|call)|"
            r"bate[- ]papo com|interview|technical (?:test|assessment|challenge)|"
            r"next (?:step|stage|round)|schedule (?:an? )?(?:interview|call)|"
            r"prueba tecnica|siguiente etapa)\b"
        ),
    ),
    (
        "recebida",
        re.compile(
            r"\b(?:recebemos (?:a sua|sua|a) candidatura|"
            r"candidatura (?:foi )?(?:recebida|enviada|registrada|confirmada|submetida)|"
            r"obrigad[oa] por se candidatar|obrigad[oa] pelo interesse|em analise|"
            r"application (?:was |has been )?(?:received|submitted)|"
            r"thank you for (?:applying|your application)|"
            r"we (?:have )?received your application|"
            r"hemos recibido tu (?:candidatura|postulacion)|"
            r"gracias por (?:postularte|tu postulacion|tu candidatura)|"
            r"postulacion recibida|en analisis)\b"
        ),
    ),
]

# Confirmação de candidatura que só fala da entrevista como possibilidade ("caso seu perfil avance, entraremos em
# contato para uma entrevista"): não é convite.
CONDICIONAL_RE = re.compile(
    r"\b(?:caso|se (?:o |a )?(?:seu|sua|voce)|if|should|once|eventua\w*|possive\w*|futur\w*|podera|poderemos|"
    r"em breve|si (?:tu|su)|en caso)\b"
)


def _so_possibilidade(regex: re.Pattern, frases_sem: list[str]) -> bool:
    """Toda frase em que o padrão casa fala dele como possibilidade (CONDICIONAL_RE)."""
    casadas = [f for f in frases_sem if regex.search(f)]
    return bool(casadas) and all(CONDICIONAL_RE.search(f) for f in casadas)


def limpar(texto: str) -> tuple[str, dict | None]:
    """Corta o texto em MAX_CARACTERES, tira cabeçalhos, endereços e links,
    junta espaços, remove linhas vazias repetidas e roda integridade.verificar."""
    if not texto:
        return "", None
    texto = texto[:MAX_CARACTERES]
    linhas_limpas: list[str] = []
    for linha in texto.splitlines():
        if CABECALHO_RE.match(linha):
            continue
        linha = URL_RE.sub("", linha)
        linha = EMAIL_RE.sub("", linha)
        linha = " ".join(linha.split())
        if linha:
            linhas_limpas.append(linha)
        elif linhas_limpas and linhas_limpas[-1]:
            linhas_limpas.append("")

    while linhas_limpas and not linhas_limpas[-1]:
        linhas_limpas.pop()

    texto_limpo = "\n".join(linhas_limpas)
    texto_limpo, achado = integridade.verificar(texto_limpo)
    return texto_limpo, achado


def classificar(texto: str) -> tuple[str | None, str]:
    """(tipo, trecho). Padrões regex sem acento e caixa, em PT/EN/ES, testados na ordem:
    contratacao, proposta, negativa, cancelada, desistencia, entrevista, recebida.
    Trecho é a frase do texto original limpo onde o padrão casou, cortada em MAX_TRECHO."""
    if not texto:
        return None, ""
    texto_sem = banco._sem_acento(texto).lower()
    frases = [f.strip() for f in re.split(r"[.!?\n]+", texto) if f.strip()]
    frases_sem = [banco._sem_acento(f).lower() for f in frases]

    for tipo, regex in PADROES:
        if tipo == "proposta" and RE_NAO_PROPOSTA.search(texto_sem):
            continue
        if tipo == "entrevista" and _so_possibilidade(regex, frases_sem):
            continue  # "caso seu perfil avance, chamaremos para entrevista": é a confirmação de recebida
        m = regex.search(texto_sem)
        if m:
            for f_orig, f_sem in zip(frases, frases_sem):
                if regex.search(f_sem):
                    return tipo, f_orig[:MAX_TRECHO]
            start = max(0, m.start() - 20)
            end = min(len(texto), m.end() + 100)
            return tipo, texto[start:end].strip()[:MAX_TRECHO]
    return None, ""


def candidatas(vagas: list[dict]) -> list[dict]:
    """Vagas com etapa definida e sem juntada_a."""
    return [v for v in vagas if v.get("etapa") and not v.get("juntada_a")]


def achar(texto: str, vagas: list[dict]) -> tuple[dict | None, list[dict]]:
    """(vaga escolhida, opções) entre as candidatas(vagas)."""
    cands = candidatas(vagas)
    if not cands or not texto:
        return None, []

    texto_sem = banco._sem_acento(texto).lower()
    texto_alnum = re.sub(r"[^a-z0-9]", "", texto_sem)
    palavras_texto = set(re.findall(r"[a-z0-9]+", texto_sem))

    empresa_citada: dict[str, bool] = {}
    proporcao: dict[str, float] = {}

    for v in cands:
        vid = v["id"]
        eb = banco.empresa_base(v.get("empresa") or "").lower()
        empresa_citada[vid] = bool(eb and len(eb) >= 4 and eb in texto_alnum)

        titulo_sem = banco._sem_acento(v.get("titulo") or "").lower()
        palavras_titulo = [p for p in re.findall(r"[a-z0-9]+", titulo_sem) if len(p) >= 3]
        total = len(palavras_titulo)
        iguais = sum(1 for p in palavras_titulo if p in palavras_texto)
        proporcao[vid] = (iguais / total) if total > 0 else 0.0

    com_empresa = [v for v in cands if empresa_citada[v["id"]]]

    if len(com_empresa) == 1:
        return com_empresa[0], []
    elif len(com_empresa) > 1:
        ordenadas = sorted(com_empresa, key=lambda v: proporcao[v["id"]], reverse=True)
        p1 = proporcao[ordenadas[0]["id"]]
        p2 = proporcao[ordenadas[1]["id"]]
        if p1 >= 0.6 and (p1 - p2) >= 0.2:
            return ordenadas[0], []
        opcoes = sorted(com_empresa, key=lambda v: (v.get("titulo") or "").lower())
        return None, opcoes
    else:
        prop_1 = [v for v in cands if proporcao[v["id"]] == 1.0]
        if len(prop_1) == 1:
            return prop_1[0], []
        return None, []


def _resumo(v: dict) -> dict:
    return {
        "id": v.get("id"),
        "titulo": v.get("titulo") or "",
        "empresa": v.get("empresa") or "",
        "etapa": v.get("etapa"),
    }


def propor(emails: list[str], vagas: list[dict]) -> list[dict]:
    """Gera uma lista de propostas para os e-mails colados, sem gravar nada."""
    itens: list[dict] = []
    for pos, raw in enumerate(emails[:MAX_EMAILS]):
        if not raw or not raw.strip():
            continue
        texto_limpo, alerta = limpar(raw)
        if not texto_limpo.strip():
            continue

        indice = pos + 1
        tipo_email, trecho = classificar(texto_limpo)
        vaga, opcoes_achar = achar(texto_limpo, vagas)

        rotulo = ROTULOS.get(tipo_email, "não reconhecido") if tipo_email else "não reconhecido"
        status = rotulo
        nota = trecho
        avisos = (
            ["⚠ o e-mail tem sinal de texto dirigido à IA; tratado como dado"]
            if alerta and alerta.get("veredito") == "atencao"
            else []
        )
        data = date.today().isoformat()
        url = ""

        if tipo_email is None:
            tipo_prop = "nao_reconhecido"
            vaga_id = None
            titulo = ""
            empresa = ""
            de = None
            para = None
            marcado = False
            opcoes = [_resumo(vaga)] if vaga else []
        elif vaga is None:
            tipo_prop = "escolher"
            vaga_id = None
            titulo = ""
            empresa = ""
            de = None
            para = MUDANCA[tipo_email]
            marcado = False
            opcoes = [_resumo(o) for o in opcoes_achar]
        else:
            vaga_id = vaga.get("id")
            titulo = vaga.get("titulo") or ""
            empresa = vaga.get("empresa") or ""
            de = {"etapa": vaga.get("etapa"), "resultado": vaga.get("resultado")}
            etapa_atual = vaga.get("etapa")
            etapa_nova = MUDANCA[tipo_email]["etapa"]
            if contas.avancou(etapa_atual, etapa_nova):
                tipo_prop = "mudar"
                para = MUDANCA[tipo_email]
            else:
                tipo_prop = "anotar"
                para = de
            marcado = True
            opcoes = []

        item = {
            "chave": f"email:{indice}",
            "portal": "email",
            "plataforma": "E-mail",
            "tipo": tipo_prop,
            "vaga_id": vaga_id,
            "titulo": titulo,
            "empresa": empresa,
            "de": de,
            "para": para,
            "tipo_email": tipo_email,
            "rotulo": rotulo,
            "trecho": trecho,
            "opcoes": opcoes,
            "alerta": alerta,
            "por_ia": False,
            "status": status,
            "nota": nota,
            "avisos": avisos,
            "data": data,
            "url": url,
            "marcado": marcado,
            "texto": texto_limpo,
        }
        itens.append(item)
        if len(itens) >= MAX_EMAILS:
            break
    return itens
