#!/usr/bin/env python3
"""Faixa salarial de uma vaga (spec 028): só números com fonte, nunca estimados (constituição IV).

  ler_valor(texto)          "R$ 5.000 a R$ 7.000 por mês" → {min, max, moeda, periodo, mensal_min, mensal_max}, ou None
  parecidas(vaga, vagas)    vagas do banco com cargo parecido que informam salário, mais parecidas primeiro
  links(vaga)               pesquisas para abrir no navegador da pessoa (Glassdoor, Indeed); a ferramenta não lê
                            essas páginas (o Glassdoor bloqueia acesso automatizado; constituição VI)
  faixa(vid)                tudo junto: o que a vaga informa, as parecidas, o resumo, as pesquisas da pessoa e os links
  anotar(vid, texto, fonte) guarda na vaga a faixa que a pessoa viu (ex.: no Glassdoor), com a fonte e a data
  remover(vid, indice)      apaga uma anotação

  python salarios.py <ID ou trecho do cargo/empresa>

Os valores são convertidos para o mês só para comparar (ano ÷ 12, hora × 220, dia × 22, semana × 52 ÷ 12) e a
conversão aparece junto. Nada aqui chama a IA nem a internet.
"""
from __future__ import annotations

import re
import statistics
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote, quote_plus

RAIZ = Path(__file__).resolve().parent
for p in (str(RAIZ / "dash"), str(RAIZ)):
    if p not in sys.path:
        sys.path.insert(0, p)
import banco  # noqa: E402

MOEDAS = (("BRL", r"r\$|brl|reais"), ("USD", r"us\$|usd|u\$s|dolar|dollars?"), ("EUR", r"€|eur|euros?"),
          ("GBP", r"£|gbp|libras?"), ("USD", r"(?<![a-z])\$"))
PERIODOS = (("hora", r"/\s*h(ora)?\b|por hora|\bhora\b|hourly|per hour|/hr\b|\bhr\b"),
            ("dia", r"/\s*dia\b|por dia|\bdiaria|daily|per day|/day"),
            ("semana", r"semana|weekly|per week|/wk"),
            ("ano", r"/\s*ano\b|por ano|\banual|annual|yearly|per year|/yr|/year|\ba\.a\.|\bano\b"),
            ("mes", r"/\s*m[eê]s|por m[eê]s|mensa|monthly|per month|/mo\b|\bmes\b"))
FATOR_MES = {"mes": 1, "ano": 1 / 12, "hora": 220, "dia": 22, "semana": 52 / 12}
BENEFICIO = re.compile(r"\bvale\b|refeic|alimentac|\bvr\b|\bva\b|beneficio|auxilio|ticket|swile|flash|alelo|plano de saude")
NUMERO = re.compile(r"(\d[\d.,\s]*\d|\d)\s*(mil|k)?(?![a-z])", re.I)
PARADAS = {"de", "da", "do", "das", "dos", "e", "em", "para", "com", "a", "o", "as", "os", "the", "of", "and", "for", "in",
           "to", "at", "jr", "junior", "pl", "pleno", "sr", "senior", "i", "ii", "iii", "iv", "remoto", "remote", "hibrido",
           "hybrid", "presencial", "vaga", "pcd", "pessoa", "profissional", "home", "office", "temporario", "efetivo",
           "clt", "pj", "br", "brasil", "100", "lead", "especialista"}
SEMELHANCA_MINIMA = 0.5
MAX_PARECIDAS = 20
MAX_ANOTACOES, TAMANHO_TEXTO, TAMANHO_FONTE = 20, 300, 120


class SalarioErro(ValueError):
    """Mensagem legível para a pessoa."""


def _sem_acento(s) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _numero(bruto: str, mil: str | None) -> float | None:
    s = re.sub(r"\s+", "", bruto)
    if "," in s and "." in s:  # o último separador é o decimal
        decimal = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if decimal == "," else ",", "").replace(decimal, ".")
    elif "," in s:
        partes = s.split(",")
        s = s.replace(",", ".") if len(partes) == 2 and len(partes[1]) <= 2 else s.replace(",", "")
    elif "." in s:
        partes = s.split(".")
        s = s.replace(".", "") if all(len(p) == 3 for p in partes[1:]) else s
    try:
        valor = float(s)
    except ValueError:
        return None
    return valor * 1000 if mil else valor


def ler_valor(texto, moeda_padrao: str | None = None) -> dict | None:
    """O valor de um texto de salário, ou None se não há número ou se é benefício (VR, VA, auxílio)."""
    t = _sem_acento(texto).replace(" ", " ")
    if not t.strip() or BENEFICIO.search(t):
        return None
    numeros = [n for n in (_numero(m.group(1), m.group(2)) for m in NUMERO.finditer(t)) if n and n >= 1]
    if not numeros:
        return None
    com_simbolos = str(texto).lower() + " " + t  # sem acento, o € e o £ somem
    moeda = next((m for m, p in MOEDAS if re.search(p, com_simbolos)), None) or (moeda_padrao or "").upper() or None
    periodo = next((nome for nome, p in PERIODOS if re.search(p, t)), None)
    lo, hi = min(numeros[:2]), max(numeros[:2])
    if periodo is None:  # sem período escrito: Brasil costuma informar o mês; fora, valores altos são anuais
        periodo = "ano" if moeda not in (None, "BRL") and lo >= 15000 else "mes"
    fator = FATOR_MES[periodo]
    return {"min": lo, "max": hi, "moeda": moeda, "periodo": periodo,
            "mensal_min": round(lo * fator, 2), "mensal_max": round(hi * fator, 2)}


def _tokens(titulo) -> set[str]:
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", _sem_acento(titulo))
    return {x for x in re.findall(r"[a-z0-9+#]+", t) if x not in PARADAS and len(x) > 1}


def semelhanca(a, b) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return round(len(ta & tb) / len(ta | tb), 2) if ta and tb else 0.0


def _moeda_da_vaga(v: dict) -> str:
    propria = ler_valor(v.get("salario"), v.get("moeda"))
    if propria and propria["moeda"]:
        return propria["moeda"]
    return str(v.get("moeda") or ("BRL" if (v.get("area") or "nacional") == "nacional" else "")).upper()


def parecidas(v: dict, vagas: list[dict]) -> list[dict]:
    moeda = _moeda_da_vaga(v)
    niveis = set(v.get("senioridade") or [])
    saida = []
    for x in vagas:
        if x.get("id") == v.get("id") or not x.get("salario"):
            continue
        valor = ler_valor(x["salario"], x.get("moeda"))
        if not valor or (moeda and valor["moeda"] and valor["moeda"] != moeda):
            continue
        outros = set(x.get("senioridade") or [])
        if niveis and outros and not niveis & outros:
            continue
        s = semelhanca(v.get("titulo"), x.get("titulo"))
        if s < SEMELHANCA_MINIMA:
            continue
        saida.append({"id": x["id"], "titulo": x.get("titulo") or "", "empresa": x.get("empresa") or "",
                      "plataforma": x.get("plataforma") or "", "salario": x["salario"], "url": x.get("url") or "",
                      "semelhanca": s, **valor})
    saida.sort(key=lambda p: (-p["semelhanca"], -p["mensal_max"]))
    return saida[:MAX_PARECIDAS]


def resumo(itens: list[dict]) -> dict | None:
    """Menor, maior e mediana (do meio de cada faixa, por mês). A mediana só aparece com 3 vagas ou mais."""
    if not itens:
        return None
    meios = [(i["mensal_min"] + i["mensal_max"]) / 2 for i in itens]
    return {"n": len(itens), "moeda": itens[0]["moeda"], "minimo": min(i["mensal_min"] for i in itens),
            "maximo": max(i["mensal_max"] for i in itens),
            "mediana": round(statistics.median(meios), 2) if len(itens) >= 3 else None}


def _cargo(titulo) -> str:
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", str(titulo or ""))
    t = re.split(r"\s[|–—-]\s|\s/\s", t)[0]
    t = re.sub(r"(?i)\b(vaga|pcd|remoto|remote|h[ií]brido|hybrid|presencial|home office)\b", " ", t)
    return " ".join(t.split())[:80]


def _empresa(v: dict) -> str:
    e = " ".join(str(v.get("empresa") or "").split())[:80]
    return "" if re.search(r"(?i)confidencial|sigilos|não informad|nao informad", e) else e


def links(v: dict) -> list[dict]:
    """Pesquisas para a pessoa abrir no navegador dela. A ferramenta não lê essas páginas."""
    br = _moeda_da_vaga(v) in ("BRL", "") and (v.get("pais_vaga") in (None, "", "Brasil"))
    gd, indeed, palavra = ("glassdoor.com.br", "br.indeed.com", "salário") if br else ("glassdoor.com", "indeed.com", "salary")
    cargo, empresa = _cargo(v.get("titulo")), _empresa(v)
    google = lambda q: "https://www.google.com/search?q=" + quote_plus(q)
    saida = []
    if cargo and empresa:
        saida.append({"rotulo": f"{cargo} na {empresa} (Glassdoor)", "url": google(f'site:{gd} {palavra} "{cargo}" "{empresa}"')})
    if cargo:
        saida.append({"rotulo": f"{cargo} no mercado (Glassdoor)", "url": google(f'site:{gd} {palavra} "{cargo}"')})
    if empresa:
        saida.append({"rotulo": f"{empresa} no Glassdoor", "url": f"https://www.{gd}/Search/results.htm?keyword={quote(empresa)}"})
    if cargo:
        saida.append({"rotulo": f"{cargo} (salários do Indeed)", "url": google(f"site:{indeed}/career {palavra} \"{cargo}\"")})
    return saida


def _vaga(vid: str) -> dict:
    v = banco.obter(vid)
    if v is None:
        raise KeyError(vid)
    return v


def faixa(vid: str) -> dict:
    v = _vaga(vid)
    lista = parecidas(v, banco.listar_vagas())
    return {"vaga": {"id": v["id"], "titulo": v.get("titulo") or "", "empresa": v.get("empresa") or "",
                     "salario": v.get("salario") or "", "valor": ler_valor(v.get("salario"), v.get("moeda"))},
            "moeda": _moeda_da_vaga(v) or None, "parecidas": lista, "resumo": resumo(lista),
            "pesquisas": v.get("salario_pesquisa") or [], "links": links(v),
            "conversao": "valores por mês para comparar: ano ÷ 12, hora × 220, dia × 22"}


def anotar(vid: str, texto, fonte) -> list[dict]:
    """Guarda a faixa que a pessoa viu, como ela escreveu, com a fonte e a data."""
    texto = " ".join(str(texto or "").split())[:TAMANHO_TEXTO]
    fonte = " ".join(str(fonte or "").split())[:TAMANHO_FONTE]
    if not texto:
        raise SalarioErro("escreva a faixa que você viu")
    if not fonte:
        raise SalarioErro("diga de onde é a faixa (ex.: Glassdoor, recrutador)")
    with banco.escrita() as con:
        doc = banco._ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        lista = list(doc.get("salario_pesquisa") or [])
        if len(lista) >= MAX_ANOTACOES:
            raise SalarioErro(f"no máximo {MAX_ANOTACOES} anotações de salário por vaga; apague alguma")
        lista.append({"texto": texto, "fonte": fonte, "em": date.today().isoformat()})
        doc["salario_pesquisa"] = lista
        doc["atualizada_em"] = banco.agora()
        banco._gravar(con, vid, doc)
    return lista


def remover(vid: str, indice: int) -> list[dict]:
    with banco.escrita() as con:
        doc = banco._ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        lista = list(doc.get("salario_pesquisa") or [])
        if not 0 <= indice < len(lista):
            raise SalarioErro("anotação não encontrada")
        lista.pop(indice)
        doc["salario_pesquisa"] = lista
        doc["atualizada_em"] = banco.agora()
        banco._gravar(con, vid, doc)
    return lista


def _dinheiro(valor: float, moeda: str | None) -> str:
    simbolo = {"BRL": "R$", "USD": "US$", "EUR": "€", "GBP": "£"}.get(moeda or "", moeda or "")
    return f"{simbolo} {valor:,.0f}".replace(",", ".").strip()


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    alvo = argv[0]
    vagas = banco.listar_vagas()
    achadas = [v for v in vagas if v["id"] == alvo] or [
        v for v in vagas if _sem_acento(alvo) in _sem_acento(f"{v.get('titulo')} {v.get('empresa')}")]
    if len(achadas) != 1:
        print(f"{len(achadas)} vagas com {alvo!r}; use o ID.", file=sys.stderr)
        return 2
    r = faixa(achadas[0]["id"])
    print(f"## {r['vaga']['titulo']} — {r['vaga']['empresa']}")
    print(f"A vaga informa: {r['vaga']['salario'] or 'não informa'}")
    if r["resumo"]:
        s = r["resumo"]
        print(f"Vagas parecidas no seu banco ({s['n']}): de {_dinheiro(s['minimo'], s['moeda'])} a "
              f"{_dinheiro(s['maximo'], s['moeda'])} por mês"
              + (f", mediana {_dinheiro(s['mediana'], s['moeda'])}" if s["mediana"] else ""))
        for p in r["parecidas"]:
            print(f"  - {p['titulo']} — {p['empresa']} ({p['plataforma']}): {p['salario']}  {p['url']}")
    else:
        print("Vagas parecidas no seu banco: nenhuma informa salário.")
    for a in r["pesquisas"]:
        print(f"Sua anotação ({a['fonte']}, {a['em']}): {a['texto']}")
    print("Pesquisar (abra no navegador):")
    for link in r["links"]:
        print(f"  - {link['rotulo']}: {link['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
