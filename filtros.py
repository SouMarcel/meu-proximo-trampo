#!/usr/bin/env python3
"""Filtros da busca: o que buscar nos portais e o que fica fora dos critérios.

Lê e grava os filtros no config.json (o painel "Filtros da busca" do dashboard grava
por salvar()), monta as consultas de cada busca e diz por que uma vaga fura os
critérios do usuário. Só biblioteca padrão: é usado por vagas.py e por dash/servidor.py.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("TRAMPO_CONFIG") or RAIZ / "config.json")
EXEMPLO = RAIZ / "config.exemplo.json"

# Países com site do Indeed: nome em português -> nome usado pelo python-jobspy
PAISES = {
    "África do Sul": "south africa", "Alemanha": "germany", "Arábia Saudita": "saudi arabia",
    "Argentina": "argentina", "Austrália": "australia", "Áustria": "austria", "Bahrein": "bahrain",
    "Bangladesh": "bangladesh", "Bélgica": "belgium", "Brasil": "brazil", "Bulgária": "bulgaria",
    "Canadá": "canada", "Catar": "qatar", "Chile": "chile", "China": "china", "Chipre": "cyprus",
    "Colômbia": "colombia", "Coreia do Sul": "south korea", "Costa Rica": "costa rica", "Croácia": "croatia",
    "Dinamarca": "denmark", "Egito": "egypt", "Emirados Árabes Unidos": "united arab emirates",
    "Equador": "ecuador", "Eslováquia": "slovakia", "Eslovênia": "slovenia", "Espanha": "spain",
    "Estados Unidos": "usa", "Estônia": "estonia", "Filipinas": "philippines", "Finlândia": "finland",
    "França": "france", "Grécia": "greece", "Holanda": "netherlands", "Hong Kong": "hong kong",
    "Hungria": "hungary", "Índia": "india", "Indonésia": "indonesia", "Irlanda": "ireland", "Israel": "israel",
    "Itália": "italy", "Japão": "japan", "Kuwait": "kuwait", "Letônia": "latvia", "Lituânia": "lithuania",
    "Luxemburgo": "luxembourg", "Malásia": "malaysia", "Malta": "malta", "Marrocos": "morocco",
    "México": "mexico", "Nigéria": "nigeria", "Noruega": "norway", "Nova Zelândia": "new zealand",
    "Omã": "oman", "Panamá": "panama", "Paquistão": "pakistan", "Peru": "peru", "Polônia": "poland",
    "Portugal": "portugal", "Reino Unido": "uk", "República Tcheca": "czech republic", "Romênia": "romania",
    "Singapura": "singapore", "Suécia": "sweden", "Suíça": "switzerland", "Tailândia": "thailand",
    "Taiwan": "taiwan", "Turquia": "türkiye", "Ucrânia": "ukraine", "Uruguai": "uruguay",
    "Venezuela": "venezuela", "Vietnã": "vietnam",
}
MODELOS = {"remoto": "Remoto", "hibrido": "Híbrido", "presencial": "Presencial"}
TIPOS_EMPREGO = {"tempo_integral": "Tempo integral (CLT)", "pj": "PJ / contrato", "meio_periodo": "Meio período",
                 "estagio": "Estágio", "temporario": "Temporário"}
SENIORIDADES = {"junior": "Jr", "pleno": "Pl", "senior": "Sr"}
# Moedas que o usuário pode aceitar para vagas fora do país dele (a moeda do país dele sempre vale)
MOEDAS = {"USD": "Dólar (USD)", "EUR": "Euro (EUR)", "GBP": "Libra (GBP)", "CAD": "Dólar canadense (CAD)",
          "CHF": "Franco suíço (CHF)"}
# Moeda de cada país de PAISES, para reconhecer a moeda do país do usuário
MOEDA_DO_PAIS = {
    "África do Sul": "ZAR", "Alemanha": "EUR", "Arábia Saudita": "SAR", "Argentina": "ARS", "Austrália": "AUD",
    "Áustria": "EUR", "Bahrein": "BHD", "Bangladesh": "BDT", "Bélgica": "EUR", "Brasil": "BRL", "Bulgária": "EUR",
    "Canadá": "CAD", "Catar": "QAR", "Chile": "CLP", "China": "CNY", "Chipre": "EUR", "Colômbia": "COP",
    "Coreia do Sul": "KRW", "Costa Rica": "CRC", "Croácia": "EUR", "Dinamarca": "DKK", "Egito": "EGP",
    "Emirados Árabes Unidos": "AED", "Equador": "USD", "Eslováquia": "EUR", "Eslovênia": "EUR", "Espanha": "EUR",
    "Estados Unidos": "USD", "Estônia": "EUR", "Filipinas": "PHP", "Finlândia": "EUR", "França": "EUR",
    "Grécia": "EUR", "Holanda": "EUR", "Hong Kong": "HKD", "Hungria": "HUF", "Índia": "INR", "Indonésia": "IDR",
    "Irlanda": "EUR", "Israel": "ILS", "Itália": "EUR", "Japão": "JPY", "Kuwait": "KWD", "Letônia": "EUR",
    "Lituânia": "EUR", "Luxemburgo": "EUR", "Malásia": "MYR", "Malta": "EUR", "Marrocos": "MAD", "México": "MXN",
    "Nigéria": "NGN", "Noruega": "NOK", "Nova Zelândia": "NZD", "Omã": "OMR", "Panamá": "USD", "Paquistão": "PKR",
    "Peru": "PEN", "Polônia": "PLN", "Portugal": "EUR", "Reino Unido": "GBP", "República Tcheca": "CZK",
    "Romênia": "RON", "Singapura": "SGD", "Suécia": "SEK", "Suíça": "CHF", "Tailândia": "THB", "Taiwan": "TWD",
    "Turquia": "TRY", "Ucrânia": "UAH", "Uruguai": "UYU", "Venezuela": "VES", "Vietnã": "VND",
}
JANELAS = {24: "Últimas 24 horas", 72: "Últimos 3 dias", 168: "Última semana", 720: "Último mês"}
RAIOS_KM = (10, 25, 50, 80)
LEGADOS = ("local", "pais_indeed", "somente_remoto")  # formato antigo do config.json

# ---------------------------------------------------------------- área internacional e idioma

IDIOMAS = {"pt": "português", "en": "inglês", "es": "espanhol", "fr": "francês", "de": "alemão", "it": "italiano"}
REGIOES = {"brasil": "Brasil", "latam": "América Latina", "americas": "Américas", "mundo": "Mundo todo"}
CONTRATACOES = {"contractor": "Contractor (você emite nota)", "eor": "Empregado por EOR (Deel, Remote…)",
                "pj": "PJ no Brasil", "clt": "CLT de empresa com operação no Brasil"}
AREAS = ("nacional", "internacional")
GRUPOS_FORA = ("internacional:", "mudanca:")
# palavras comuns que distinguem cada idioma (sem acento); o que aparece em mais de um idioma ficou de fora
PALAVRAS_IDIOMA = {
    "pt": set("nao voce sua seu dos das uma ao mais com na no em vaga empresa conhecimento atividades requisitos "
              "beneficios trabalho nossa nosso sera voces tambem ou pelo pela e um os ter boa bom pessoa nossos nossas "
              "seus suas sao precisa alem incluem vale ser pode ate ja dados vendas saude familia".split()),
    "en": set("the and to of for with you your our we will is are be on this that team experience work skills role "
              "company about have who what".split()),
    "es": set("el los las y con del al sus una trabajo equipo conocimiento puesto buscamos somos tu usted nuestro "
              "nuestra tambien muy".split()),
    "fr": set("le les et des pour avec vous nous dans est sur aux du votre notre poste entreprise travail une".split()),
    "de": set("der die das und mit fur sie wir ist auf ein eine zu im den dem bei als oder unser ihre erfahrung".split()),
    "it": set("il di per che della nel sono nostro nostra esperienza lavoro azienda squadra ruolo gli".split()),
}
MIN_PALAVRAS_IDIOMA = 25
LUGARES = {  # cidades, siglas e regiões que aparecem no local das vagas (sem acento) -> país ou região
    "us": "Estados Unidos", "usa": "Estados Unidos", "u.s.": "Estados Unidos", "united states": "Estados Unidos",
    "eua": "Estados Unidos", "new york": "Estados Unidos", "san francisco": "Estados Unidos",
    "california": "Estados Unidos", "texas": "Estados Unidos", "seattle": "Estados Unidos", "boston": "Estados Unidos",
    "chicago": "Estados Unidos", "austin": "Estados Unidos", "miami": "Estados Unidos", "uk": "Reino Unido",
    "united kingdom": "Reino Unido", "england": "Reino Unido", "london": "Reino Unido", "londres": "Reino Unido",
    "berlin": "Alemanha", "berlim": "Alemanha", "munich": "Alemanha", "paris": "França", "lisbon": "Portugal",
    "lisboa": "Portugal", "amsterdam": "Holanda", "dublin": "Irlanda", "madrid": "Espanha", "barcelona": "Espanha",
    "toronto": "Canadá", "vancouver": "Canadá", "montreal": "Canadá", "buenos aires": "Argentina",
    "santiago": "Chile", "bogota": "Colômbia", "ciudad de mexico": "México", "mexico city": "México",
    "worldwide": "mundo todo", "anywhere": "mundo todo", "global": "mundo todo", "mundo": "mundo todo",
    "europe": "Europa", "europa": "Europa", "emea": "Europa", "latam": "América Latina",
    "latin america": "América Latina", "america latina": "América Latina", "south america": "América Latina",
    "americas": "Américas", "brazil": "Brasil", "brasil": "Brasil",
}


def pais_do_local(texto) -> str | None:
    """País (em português) ou região que o local da vaga indica; None quando não dá para saber."""
    t = " " + re.sub(r"[^a-z0-9.]+", " ", sem_acento(texto)) + " "
    if not t.strip():
        return None
    nomes = dict(LUGARES)
    for pt, en in PAISES.items():
        nomes.setdefault(sem_acento(pt), pt)
        nomes.setdefault(en, pt)
    achados = []
    for nome, pais in nomes.items():
        m = re.search(r"(?<![a-z0-9])" + re.escape(nome) + r"(?![a-z0-9])", t)
        if m:
            achados.append((m.start(), -len(nome), pais))
    return min(achados)[2] if achados else None


def area_da_vaga(v: dict, f: dict) -> tuple[str, str | None]:
    """(nacional | internacional, país ou região). A área gravada vale; senão, a consulta que achou a vaga
    (internacional só se nenhuma consulta nacional a achou); senão, o local."""
    if v.get("area") in AREAS:
        return v["area"], v.get("pais_vaga")
    grupos = v.get("grupos") or []
    fora = [g.split(":", 1)[1] for g in grupos if g.startswith(GRUPOS_FORA)]
    if fora and len(fora) == len(grupos):
        return "internacional", fora[0]
    if fora:
        return "nacional", None
    pais = pais_do_local(v.get("local"))
    if pais and pais != f["localidade"]["pais"]:
        return "internacional", pais
    return "nacional", None


def idioma_texto(texto) -> str | None:
    """Idioma do texto pelas palavras comuns; None quando o texto é curto ou misturado demais."""
    palavras = re.findall(r"[a-z]+", sem_acento(texto))
    conta = {k: sum(p in lista for p in palavras) for k, lista in PALAVRAS_IDIOMA.items()}
    ordem = sorted(conta.items(), key=lambda x: -x[1])
    (primeiro, n1), (_, n2) = ordem[0], ordem[1]
    if sum(conta.values()) < MIN_PALAVRAS_IDIOMA or n1 < 1.5 * max(n2, 1):
        return None
    return primeiro


def idioma_da_vaga(v: dict) -> str | None:
    """O idioma do portal ou da análise, se houver; senão, o do título e da descrição."""
    for chave in ("idioma", "lang", "language"):
        valor = str(v.get(chave) or "").strip().lower()[:2]
        if re.fullmatch(r"[a-z]{2}", valor):
            return valor
    return idioma_texto(f"{v.get('titulo') or ''} {v.get('descricao') or ''}")


def salario_anual_usd(v: dict) -> float | None:
    """O maior valor anual em dólar que o texto de salário da vaga informa; None quando não dá para saber."""
    texto = sem_acento(v.get("salario"))
    moeda = str(v.get("moeda") or "").upper()
    if not texto or "r$" in texto or (moeda and moeda != "USD") or not (moeda == "USD" or "usd" in texto or "$" in texto):
        return None
    valores = []
    for m in re.finditer(r"(\d[\d.,]*)\s*(k\b)?", texto):
        bruto = m.group(1).rstrip(".,")
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", bruto):
            n = float(re.sub(r"[.,]", "", bruto))
        else:
            try:
                n = float(bruto.replace(",", "."))
            except ValueError:
                continue
        valores.append(n * (1000 if m.group(2) else 1))
    if not valores:
        return None
    maior = max(valores)
    if re.search(r"\b(hour|hr|hora|hourly)\b", texto):
        return maior * 2080
    if re.search(r"\b(month|mo|mes|mensal|monthly)\b", texto):
        return maior * 12
    if re.search(r"\b(year|yr|ano|anual|annual|yearly)\b", texto) or maior >= 20000:
        return maior
    return None



def sem_acento(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def pais_pt(nome) -> str | None:
    """Nome do país em português, aceitando também o nome do jobspy (o config antigo usa "Brazil")."""
    alvo = sem_acento(nome)
    for pt, en in PAISES.items():
        if alvo and alvo in (sem_acento(pt), en):
            return pt
    return None


# ---------------------------------------------------------------- config

def ler_config() -> dict:
    if not CONFIG.exists():
        return {}
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def efetivos(cfg: dict) -> dict:
    """Filtros completos a partir do config.json, aceitando o formato antigo (local, pais_indeed, somente_remoto)."""
    loc = cfg.get("localidade") if isinstance(cfg.get("localidade"), dict) else {}
    pais = pais_pt(loc.get("pais") or cfg.get("pais_indeed") or "Brasil") or "Brasil"
    modelos = cfg.get("modelos")
    if not isinstance(modelos, dict):
        so_remoto = cfg.get("somente_remoto", True)
        modelos = {"remoto": True, "hibrido": not so_remoto, "presencial": not so_remoto}
    inter = cfg.get("internacional") if isinstance(cfg.get("internacional"), dict) else {}
    f = {
        "termos": [str(t) for t in cfg.get("termos") or []],
        "localidade": {"pais": pais, "estado": str(loc.get("estado") or ""), "cidade": str(loc.get("cidade") or ""),
                       "raio_km": int(loc.get("raio_km") or 25)},
        "modelos": {k: bool(modelos.get(k)) for k in MODELOS},
        "internacional": {
            "ativo": bool(inter.get("ativo")),
            "paises": [p for p in map(pais_pt, inter.get("paises") or []) if p and p != pais],
            "termos": [str(t) for t in inter.get("termos") or []],
            "regioes": [r for r in inter.get("regioes") or [] if r in REGIOES],
            "salario_min_anual_usd": _numero(inter.get("salario_min_anual_usd")),
            "fuso_horas": int(_numero(inter.get("fuso_horas"))),
            "contratacao": [c for c in inter.get("contratacao") or [] if c in CONTRATACOES],
            "aceita_mudar": bool(inter.get("aceita_mudar")),
            "paises_mudanca": [p for p in map(pais_pt, inter.get("paises_mudanca") or []) if p and p != pais],
            "passaporte": bool(inter.get("passaporte")),
            "autorizacao_trabalho": [p for p in map(pais_pt, inter.get("autorizacao_trabalho") or []) if p],
            "precisa_sponsor": bool(inter.get("precisa_sponsor")),
        },
        "idiomas_aceitos": [i for i in cfg.get("idiomas_aceitos") or [] if i in IDIOMAS],
        "janela_horas": int(cfg.get("janela_horas") or 168),
        "tipos_emprego": [t for t in cfg.get("tipos_emprego") or [] if t in TIPOS_EMPREGO],
        "senioridades": [s for s in cfg.get("senioridades") or [] if s in SENIORIDADES],
        "moedas_aceitas": [m for m in cfg.get("moedas_aceitas") or [] if m in MOEDAS],
        "empresas_excluir": [str(e).strip() for e in cfg.get("empresas_excluir") or [] if str(e).strip()],
    }
    if not loc and cfg.get("local"):
        f["local_legado"] = str(cfg["local"])  # formato antigo: onde fazer a busca do país
    return f


def _numero(v) -> float:
    try:
        return max(0.0, float(v or 0))
    except (TypeError, ValueError):
        return 0.0


def _paises(v, nome: str, excluir: str | None = None) -> list[str]:
    saida = []
    for p in v or []:
        pp = pais_pt(p)
        if not pp:
            raise ValueError(f"{nome}: país desconhecido: {p}")
        if pp != excluir and pp not in saida:
            saida.append(pp)
    return saida


def _codigos(v, nome: str, validos: dict) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list) or any(x not in validos for x in v):
        raise ValueError(f"{nome} inválido")
    return [k for k in validos if k in v]


def _textos(v, nome: str, maximo: int, tamanho: int = 80) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list):
        raise ValueError(f"{nome}: esperava uma lista")
    saida, vistos = [], set()
    for x in v:
        x = str(x).strip()[:tamanho]
        if x and sem_acento(x) not in vistos:
            vistos.add(sem_acento(x))
            saida.append(x)
    if len(saida) > maximo:
        raise ValueError(f"{nome}: no máximo {maximo}")
    return saida


def _inteiro(v, nome: str, minimo: int, maximo: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ValueError(f"{nome} inválido") from None
    if not minimo <= n <= maximo:
        raise ValueError(f"{nome} deve ficar entre {minimo} e {maximo}")
    return n


def validar(e: dict) -> dict:
    """Valida o que vem do painel do dashboard. Devolve os filtros no formato do config.json."""
    if not isinstance(e, dict):
        raise ValueError("filtros inválidos")
    termos = _textos(e.get("termos"), "cargos", 30)
    if not termos:
        raise ValueError("informe pelo menos um cargo")
    loc = e.get("localidade") if isinstance(e.get("localidade"), dict) else {}
    pais = pais_pt(loc.get("pais"))
    if not pais:
        raise ValueError("escolha um país da lista")
    cidade = str(loc.get("cidade") or "").strip()[:80]
    estado = str(loc.get("estado") or "").strip()[:40]
    raio = _inteiro(loc.get("raio_km") or 25, "raio", 1, 200)
    modelos = e.get("modelos") if isinstance(e.get("modelos"), dict) else {}
    m = {k: bool(modelos.get(k)) for k in MODELOS}
    if not any(m.values()):
        raise ValueError("marque pelo menos um modelo de trabalho")
    if (m["hibrido"] or m["presencial"]) and not cidade:
        raise ValueError("para híbrido ou presencial, informe a cidade")
    inter = e.get("internacional") if isinstance(e.get("internacional"), dict) else {}
    paises_int = _paises(inter.get("paises"), "países de interesse", pais)
    termos_int = _textos(inter.get("termos"), "cargos para o exterior", 10)
    ativo = bool(inter.get("ativo"))  # não depende mais do remoto no país
    if ativo and not paises_int:
        raise ValueError("escolha pelo menos um país para a busca internacional")
    if ativo and not termos_int:
        raise ValueError("informe pelo menos um cargo em inglês para a busca internacional")
    salario = inter.get("salario_min_anual_usd") or 0
    if not isinstance(salario, (int, float)) or isinstance(salario, bool) or not 0 <= salario <= 10_000_000:
        raise ValueError("salário mínimo anual inválido")
    fuso = inter.get("fuso_horas") or 0
    if not isinstance(fuso, int) or isinstance(fuso, bool) or not 0 <= fuso <= 12:
        raise ValueError("as horas de sobreposição de fuso devem ficar entre 0 e 12")
    internacional = {
        "ativo": ativo, "paises": paises_int, "termos": termos_int,
        "regioes": _codigos(inter.get("regioes"), "região", REGIOES),
        "salario_min_anual_usd": salario, "fuso_horas": fuso,
        "contratacao": _codigos(inter.get("contratacao"), "forma de contratação", CONTRATACOES),
        "aceita_mudar": bool(inter.get("aceita_mudar")),
        "paises_mudanca": _paises(inter.get("paises_mudanca"), "países para morar", pais),
        "passaporte": bool(inter.get("passaporte")),
        "autorizacao_trabalho": _paises(inter.get("autorizacao_trabalho"), "autorização de trabalho"),
        "precisa_sponsor": bool(inter.get("precisa_sponsor")),
    }
    tipos = e.get("tipos_emprego") or []
    sen = e.get("senioridades") or []
    if not isinstance(tipos, list) or any(t not in TIPOS_EMPREGO for t in tipos):
        raise ValueError("tipo de emprego inválido")
    if not isinstance(sen, list) or any(s not in SENIORIDADES for s in sen):
        raise ValueError("senioridade inválida")
    moedas = e.get("moedas_aceitas") or []
    if not isinstance(moedas, list) or any(m not in MOEDAS for m in moedas):
        raise ValueError("moeda inválida")
    return {
        "termos": termos,
        "localidade": {"pais": pais, "estado": estado, "cidade": cidade, "raio_km": raio},
        "modelos": m,
        "internacional": internacional,
        "idiomas_aceitos": _codigos(e.get("idiomas_aceitos"), "idioma", IDIOMAS),
        "janela_horas": _inteiro(e.get("janela_horas") or 168, "período de publicação", 1, 720),
        "tipos_emprego": [t for t in TIPOS_EMPREGO if t in tipos],
        "senioridades": [s for s in SENIORIDADES if s in sen],
        "moedas_aceitas": [m for m in MOEDAS if m in moedas],
        "empresas_excluir": _textos(e.get("empresas_excluir"), "empresas a excluir", 100),
    }


def salvar(entrada: dict) -> dict:
    """Grava os filtros no config.json, mantendo as outras chaves (perfil, fontes, titulo_excluir…)."""
    novos = validar(entrada)
    cfg = ler_config()
    if not cfg.get("termos") and EXEMPLO.exists():  # ainda sem filtros (talvez só com "ia"): parte do exemplo
        cfg = {**json.loads(EXEMPLO.read_text(encoding="utf-8")), **cfg}
    for k in LEGADOS:
        cfg.pop(k, None)
    cfg.update(novos)
    tmp = CONFIG.with_name(CONFIG.name + ".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    os.replace(tmp, CONFIG)
    return efetivos(cfg)


def opcoes() -> dict:
    """Listas que o painel do dashboard mostra."""
    return {"paises": sorted(PAISES, key=sem_acento), "modelos": MODELOS, "tipos_emprego": TIPOS_EMPREGO,
            "senioridades": SENIORIDADES, "moedas": MOEDAS, "moeda_do_pais": MOEDA_DO_PAIS,
            "janelas": JANELAS, "raios_km": RAIOS_KM, "idiomas": IDIOMAS, "regioes": REGIOES,
            "contratacao": CONTRATACOES}


def criterios_extra(f: dict) -> list[str]:
    """Critérios além de local e modelo, em texto, para o digest da busca e para a análise automática."""
    crit = []
    if f["senioridades"]:
        crit.append("senioridade " + "/".join(SENIORIDADES[s] for s in f["senioridades"]))
    if f["tipos_emprego"]:
        crit.append("tipo de emprego " + ", ".join(TIPOS_EMPREGO[t] for t in f["tipos_emprego"]))
    if f["moedas_aceitas"]:
        local = MOEDA_DO_PAIS.get(f["localidade"]["pais"])
        crit.append(f"fora do país ({local or 'moeda local'} sempre vale), salário só em " + ", ".join(f["moedas_aceitas"]))
    if f["idiomas_aceitos"]:
        crit.append("vaga só em " + _lista_e([IDIOMAS[i] for i in f["idiomas_aceitos"]]))
    inter = f["internacional"]
    if inter["ativo"]:
        partes = []
        if inter["regioes"]:
            partes.append("regiões aceitas: " + ", ".join(REGIOES[r] for r in inter["regioes"]))
        if inter["contratacao"]:
            partes.append("contratação aceita: " + ", ".join(CONTRATACOES[c] for c in inter["contratacao"]))
        if inter["fuso_horas"]:
            partes.append(f"pelo menos {inter['fuso_horas']} h de sobreposição de fuso com o Brasil")
        if inter["salario_min_anual_usd"]:
            partes.append(f"salário mínimo de US$ {inter['salario_min_anual_usd']:,.0f} por ano")
        partes.append("passaporte válido: " + ("sim" if inter["passaporte"] else "não"))
        partes.append("autorização de trabalho em: " + (", ".join(inter["autorizacao_trabalho"]) or "nenhum país"))
        partes.append("precisa de patrocínio de visto: " + ("sim" if inter["precisa_sponsor"] else "não"))
        if inter["aceita_mudar"]:
            partes.append("aceita morar fora" + (" (" + ", ".join(inter["paises_mudanca"]) + ")" if inter["paises_mudanca"] else ""))
        crit.append("vagas internacionais: " + "; ".join(partes))
    return crit


def _lista_e(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


# ---------------------------------------------------------------- consultas

def cidade_rotulo(f: dict) -> str:
    loc = f["localidade"]
    return ", ".join(x for x in (loc["cidade"], loc["estado"]) if x)


def consultas(f: dict, incluir_presencial: bool = False) -> list[dict]:
    """Uma consulta por termo em cada grupo: remoto no país, cidade (híbrido/presencial) e cada país do exterior."""
    m, loc, inter = f["modelos"], f["localidade"], f["internacional"]
    pais = PAISES[loc["pais"]]
    cidade = cidade_rotulo(f) if loc["cidade"] else ""
    # sem cidade, híbrido/presencial só dá para buscar no país inteiro, sem o filtro de remoto (como no formato antigo)
    pais_sem_filtro = incluir_presencial or ((m["hibrido"] or m["presencial"]) and not cidade)
    lista = []
    if m["remoto"] or pais_sem_filtro:
        for t in f["termos"]:
            lista.append({"grupo": "pais" if pais_sem_filtro else "remoto", "termo": t, "pais": pais,
                          "pais_nome": loc["pais"], "local": f.get("local_legado"), "raio_km": None,
                          "remoto": not pais_sem_filtro, "area": "nacional"})
    if cidade and (m["hibrido"] or m["presencial"]):
        for t in f["termos"]:
            lista.append({"grupo": "local", "termo": t, "pais": pais, "pais_nome": loc["pais"], "local": cidade,
                          "cidade": loc["cidade"], "estado": loc["estado"], "raio_km": loc["raio_km"],
                          "remoto": False, "area": "nacional"})
    if inter["ativo"]:  # não depende do remoto no país
        for p in inter["paises"]:
            for t in inter["termos"] or f["termos"]:
                lista.append({"grupo": f"internacional:{p}", "termo": t, "pais": PAISES[p], "pais_nome": p,
                              "local": None, "raio_km": None, "remoto": True, "area": "internacional"})
        if inter.get("aceita_mudar"):  # presencial e híbrido nos países para onde aceita se mudar
            for p in inter.get("paises_mudanca") or inter["paises"]:
                for t in inter["termos"] or f["termos"]:
                    lista.append({"grupo": f"mudanca:{p}", "termo": t, "pais": PAISES[p], "pais_nome": p,
                                  "local": None, "raio_km": None, "remoto": False, "area": "internacional"})
    return lista


def resumo(f: dict) -> str:
    m, loc = f["modelos"], f["localidade"]
    partes = []
    if m["remoto"]:
        partes.append(f"remoto ({loc['pais']})")
    locais = [MODELOS[k].lower() for k in ("hibrido", "presencial") if m[k]]
    if locais:
        onde = f"em {cidade_rotulo(f)} ({loc['raio_km']} km)" if loc["cidade"] else f"em {loc['pais']}"
        partes.append(f"{' e '.join(locais)} {onde}")
    inter = f["internacional"]
    if inter["ativo"]:
        partes.append(f"remoto no exterior: {', '.join(inter['paises'])}")
        if inter.get("aceita_mudar"):
            partes.append(f"presencial ou híbrido em: {', '.join(inter.get('paises_mudanca') or inter['paises'])}")
    return "; ".join(partes)


# ---------------------------------------------------------------- critérios

def senioridade_titulo(titulo) -> list[str]:
    """Níveis que o título declara (mesma regra do dashboard): Jr, Pl, Sr, Snr, Mid-level, Semi Senior…"""
    t = " " + " ".join(re.sub("[^a-z0-9]+", " ", sem_acento(titulo)).split()) + " "
    t = re.sub(" semi ?(senior|sr) ", " ssr ", t)  # "Semi Senior" (espanhol) é pleno
    niveis = []
    if re.search(" (jr|junior|entry level) ", t):
        niveis.append("junior")
    if re.search(" (pl(?! sql )|pleno|mid|intermediate|intermediario|intermediaria|ssr|ii) ", t):
        niveis.append("pleno")
    if re.search(" (sr|snr|senior|iii|principal) ", t):
        niveis.append("senior")
    return niveis


def na_cidade(v: dict, f: dict) -> bool:
    cidade = sem_acento(f["localidade"]["cidade"])
    if not cidade:
        return True  # sem cidade configurada, vale em qualquer lugar (formato antigo)
    return "local" in (v.get("grupos") or []) or cidade in sem_acento(v.get("local"))


def criterios(v: dict, f: dict) -> list[str]:
    """Motivos pelos quais a vaga fura os filtros do usuário (lista vazia = passa).

    Usa o que já se sabe da vaga: antes da IA, empresa e senioridade do título; depois,
    também modelo de trabalho, senioridade e tipo de emprego lidos na descrição.
    """
    motivos = []
    empresa = sem_acento(v.get("empresa"))
    for e in f["empresas_excluir"]:
        if sem_acento(e) and sem_acento(e) in empresa:
            motivos.append(f"Empresa na sua lista de exclusão ({e})")
            break
    modelo, m = v.get("modelo_trabalho"), f["modelos"]
    if modelo in MODELOS:
        nome = MODELOS[modelo]
        onde = f" em {v['local']}" if v.get("local") and modelo != "remoto" else ""
        if not m[modelo]:
            motivos.append(f"{nome}{onde}; você não aceita {nome.lower()}")
        elif modelo != "remoto" and not na_cidade(v, f):
            motivos.append(f"{nome}{onde}; você aceita {nome.lower()} só em {cidade_rotulo(f)}")
    niveis = v["senioridade"] if isinstance(v.get("senioridade"), list) else senioridade_titulo(v.get("titulo"))
    if f["senioridades"] and niveis and not set(niveis) & set(f["senioridades"]):
        motivos.append(f"Senioridade {'/'.join(SENIORIDADES[n] for n in niveis)}; você busca "
                       + "/".join(SENIORIDADES[n] for n in f["senioridades"]))
    tipos = [t for t in v.get("tipo_emprego") or [] if t in TIPOS_EMPREGO]
    if f["tipos_emprego"] and tipos and not set(tipos) & set(f["tipos_emprego"]):
        motivos.append(f"{', '.join(TIPOS_EMPREGO[t] for t in tipos)}; você busca "
                       + ", ".join(TIPOS_EMPREGO[t] for t in f["tipos_emprego"]))
    moeda = str(v.get("moeda") or "").upper()
    moeda_local = MOEDA_DO_PAIS.get(f["localidade"]["pais"])
    if f["moedas_aceitas"] and moeda and moeda != moeda_local and moeda not in f["moedas_aceitas"]:
        motivos.append(f"Paga em {moeda}; fora do seu país você aceita {', '.join(f['moedas_aceitas'])}")
    if f["idiomas_aceitos"]:
        idioma = idioma_da_vaga(v)
        if idioma and idioma not in f["idiomas_aceitos"]:
            motivos.append(f"Vaga em {IDIOMAS.get(idioma, idioma)}; você aceita "
                           + _lista_e([IDIOMAS[i] for i in f["idiomas_aceitos"]]))
    minimo = f["internacional"]["salario_min_anual_usd"]
    if minimo and area_da_vaga(v, f)[0] == "internacional":
        anual = salario_anual_usd(v)
        if anual and anual < minimo:
            motivos.append(f"Paga até US$ {anual:,.0f} por ano; seu mínimo é US$ {minimo:,.0f}")
    if v.get("fora_dos_criterios"):
        motivos.append(str(v["fora_dos_criterios"]))
    return motivos
