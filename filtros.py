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
        },
        "janela_horas": int(cfg.get("janela_horas") or 168),
        "tipos_emprego": [t for t in cfg.get("tipos_emprego") or [] if t in TIPOS_EMPREGO],
        "senioridades": [s for s in cfg.get("senioridades") or [] if s in SENIORIDADES],
        "moedas_aceitas": [m for m in cfg.get("moedas_aceitas") or [] if m in MOEDAS],
        "empresas_excluir": [str(e).strip() for e in cfg.get("empresas_excluir") or [] if str(e).strip()],
    }
    if not loc and cfg.get("local"):
        f["local_legado"] = str(cfg["local"])  # formato antigo: onde fazer a busca do país
    return f


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
    paises_int = []
    for p in inter.get("paises") or []:
        pp = pais_pt(p)
        if not pp:
            raise ValueError(f"país desconhecido: {p}")
        if pp != pais and pp not in paises_int:
            paises_int.append(pp)
    termos_int = _textos(inter.get("termos"), "cargos para o exterior", 10)
    ativo = bool(inter.get("ativo")) and m["remoto"]
    if ativo and not paises_int:
        raise ValueError("escolha pelo menos um país para a busca internacional")
    if ativo and not termos_int:
        raise ValueError("informe pelo menos um cargo para a busca internacional")
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
        "internacional": {"ativo": ativo, "paises": paises_int, "termos": termos_int},
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
            "janelas": JANELAS, "raios_km": RAIOS_KM}


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
    return crit


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
                          "remoto": not pais_sem_filtro})
    if cidade and (m["hibrido"] or m["presencial"]):
        for t in f["termos"]:
            lista.append({"grupo": "local", "termo": t, "pais": pais, "pais_nome": loc["pais"], "local": cidade,
                          "cidade": loc["cidade"], "estado": loc["estado"], "raio_km": loc["raio_km"],
                          "remoto": False})
    if m["remoto"] and inter["ativo"]:
        for p in inter["paises"]:
            for t in inter["termos"] or f["termos"]:
                lista.append({"grupo": f"internacional:{p}", "termo": t, "pais": PAISES[p], "pais_nome": p,
                              "local": None, "raio_km": None, "remoto": True})
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
    if m["remoto"] and f["internacional"]["ativo"]:
        partes.append(f"remoto no exterior: {', '.join(f['internacional']['paises'])}")
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
    if v.get("fora_dos_criterios"):
        motivos.append(str(v["fora_dos_criterios"]))
    return motivos
