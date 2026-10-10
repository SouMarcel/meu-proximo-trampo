#!/usr/bin/env python3
"""Banco local do dashboard de candidaturas (SQLite, só biblioteca padrão).

Usado pelo servidor (dash/servidor.py), por vagas.py e pela skill buscar-vagas. Também tem
comandos para consultar e analisar vagas sem abrir o navegador:

  python dash/banco.py quadro [--etapa entrevista]   resumo do quadro
  python dash/banco.py pendentes                      vagas esperando análise (JSON)
  python dash/banco.py analisar ARQUIVO.json          grava análises dessas vagas
  python dash/banco.py vaga "acme product owner"      dados completos de uma vaga (ID ou trecho do cargo/empresa)
  python dash/banco.py anotar ID "texto"              acrescenta uma linha às anotações da vaga
  python dash/banco.py kit ID                         o que a candidatura pede (checklist) e o lembrete da vaga
  python dash/banco.py lembretes                      lembretes de follow-up pendentes no quadro

O arquivo do banco é dash/dados/candidaturas.db (ou o caminho em TRAMPO_BANCO).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sqlite3
import sys
import unicodedata
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

DASH = Path(__file__).resolve().parent
if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))
import kit  # noqa: E402  (dash/kit.py: checklist e lembretes)

ARQUIVO = Path(os.environ.get("TRAMPO_BANCO") or DASH / "dados" / "candidaturas.db")
DADOS = ARQUIVO.parent
BACKUPS = DADOS / "backup"
MANTER_BACKUPS = 10

ETAPAS = ("salva", "aplicada", "entrevista", "proposta", "encerrada")
TRIAGENS = ("pendente", "seguir", "visitada", "fora")  # fora = furou os filtros da busca
RESULTADOS = ("nao_aprovado", "desisti", "cancelada", "contratado")
PLATAFORMAS = ("Indeed", "LinkedIn", "Gupy", "InHire", "Catho", "Startup Jobs", "Remotive", "Himalayas", "RemoteOK",
               "Jobicy", "We Work Remotely", "Get on Board", "Greenhouse", "Lever", "Ashby", "Outra")
SISTEMAS_ATS = ("greenhouse", "lever", "ashby")
MODELOS = ("remoto", "hibrido", "presencial", "nao_informado")
SENIORIDADES = ("junior", "pleno", "senior")
ORIGENS_SENIORIDADE = ("declarada", "sugerida")
TIPOS_EMPREGO = ("tempo_integral", "pj", "meio_periodo", "estagio", "temporario")  # as chaves de filtros.TIPOS_EMPREGO
ID_VALIDO = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
DATA_VALIDA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def hoje() -> str:
    return date.today().isoformat()


def conectar() -> sqlite3.Connection:
    DADOS.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ARQUIVO, timeout=15)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS vagas  (id TEXT PRIMARY KEY, dados TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS buscas (id TEXT PRIMARY KEY, dados TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS meta   (chave TEXT PRIMARY KEY, valor INTEGER NOT NULL);
        INSERT OR IGNORE INTO meta VALUES ('versao', 0);
        """
    )
    return con


@contextmanager
def escrita():
    """Transação de escrita; incrementa a versão para o dashboard recarregar."""
    with closing(conectar()) as con:
        with con:
            yield con
            con.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")


def _ler(con, vid: str) -> dict | None:
    linha = con.execute("SELECT dados FROM vagas WHERE id = ?", (vid,)).fetchone()
    if not linha:
        return None
    doc = json.loads(linha[0])
    doc["id"] = vid
    return doc


def _gravar(con, vid: str, doc: dict) -> None:
    corpo = {k: v for k, v in doc.items() if k != "id"}
    con.execute("INSERT OR REPLACE INTO vagas (id, dados) VALUES (?, ?)", (vid, json.dumps(corpo, ensure_ascii=False)))


# ---------------------------------------------------------------- leitura

def versao() -> int:
    with closing(conectar()) as con:
        return con.execute("SELECT valor FROM meta WHERE chave = 'versao'").fetchone()[0]


def listar_vagas() -> list[dict]:
    with closing(conectar()) as con:
        saida = []
        for vid, dados in con.execute("SELECT id, dados FROM vagas"):
            doc = json.loads(dados)
            doc["id"] = vid
            saida.append(doc)
        return saida


def obter(vid: str) -> dict | None:
    with closing(conectar()) as con:
        return _ler(con, vid)


def _sem_acento(s) -> str:
    return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()


def procurar(texto: str) -> list[dict]:
    """Vaga pelo ID exato ou pelas palavras do texto no cargo/empresa (sem diferenciar acento e caixa)."""
    vagas = listar_vagas()
    exata = [v for v in vagas if v["id"] == texto.strip()]
    if exata:
        return exata
    palavras = _sem_acento(texto).split()
    return [v for v in vagas if palavras and all(p in _sem_acento(f"{v.get('titulo')} {v.get('empresa')}") for p in palavras)]


def ultima_busca() -> dict | None:
    with closing(conectar()) as con:
        linha = con.execute("SELECT id, dados FROM buscas ORDER BY id DESC LIMIT 1").fetchone()
    if not linha:
        return None
    doc = json.loads(linha[1])
    doc["id"] = linha[0]
    return doc


# ---------------------------------------------------------------- vaga repetida

REPETIDA_DIAS = 60  # cargo + empresa iguais só contam como a mesma vaga se ela foi encontrada há até tantos dias
EMPRESAS_GENERICAS = {"", "empresa nao informada", "empresa confidencial", "confidencial"}


def _id_gupy():
    """fontes.gupy.id_do_link, carregado sob demanda (fontes/ fica na raiz do projeto)."""
    try:
        raiz = str(DASH.parent)
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        from fontes.gupy import id_do_link
        return id_do_link
    except ImportError:
        return lambda url: None


def ids_da_vaga(doc: dict, id_gupy=None) -> set[str]:
    """IDs pelos quais a vaga pode voltar: o dela, os dos anúncios repetidos e os que saem dos links, inclusive
    o de candidatura (o jk do Indeed, o número da vaga da Gupy). Assim a vaga do Indeed que manda para a Gupy
    é reconhecida quando aparece de novo pela Gupy."""
    id_gupy = id_gupy or _id_gupy()
    ids = {str(doc["id"])} if doc.get("id") else set()
    if doc.get("jk"):
        ids.add(str(doc["jk"]))
    ids.update(str(x) for x in doc.get("ids_relacionados") or [])
    for url in (doc.get("url"), doc.get("url_candidatura")):
        m = re.search(r"[?&]jk=([0-9a-f]{16})", str(url or ""))
        if m:
            ids.add(m.group(1))
        g = id_gupy(url)
        if g:
            ids.add(g)
    return ids


def chave_vaga(titulo, empresa) -> str | None:
    """Cargo + empresa sem acento, caixa e espaços extras: o mesmo anúncio em outro portal tem a mesma chave.
    Sem empresa conhecida não há chave (dois "Analista" de empresas confidenciais não são a mesma vaga)."""
    empresa = " ".join(_sem_acento(empresa).split())
    titulo = " ".join(_sem_acento(titulo).split())
    if not titulo or empresa in EMPRESAS_GENERICAS:
        return None
    return f"{titulo}|{empresa}"


def _recente(doc: dict) -> bool:
    data = str(doc.get("encontrada_em") or doc.get("criada_em") or "")[:10]
    return data >= (date.today() - timedelta(days=REPETIDA_DIAS)).isoformat()


class IndiceVistas:
    """Acha a vaga já registrada que é a mesma que uma vaga nova: por um id em comum (ids_da_vaga, inclusive pelos
    links) ou pelo mesmo cargo + empresa encontrado nos últimos REPETIDA_DIAS dias (depois disso, a mesma vaga
    reaberta pela empresa conta como nova)."""

    def __init__(self):
        self._id_gupy = _id_gupy()
        self.por_id: dict[str, str] = {}
        self.por_chave: dict[str, str] = {}
        for doc in listar_vagas():
            for i in ids_da_vaga(doc, self._id_gupy):
                self.por_id.setdefault(i, doc["id"])
            chave = chave_vaga(doc.get("titulo"), doc.get("empresa")) if _recente(doc) else None
            if chave:
                self.por_chave.setdefault(chave, doc["id"])

    def achar(self, doc: dict) -> str | None:
        """ID da vaga registrada que é a mesma que `doc`, ou None."""
        for i in ids_da_vaga(doc, self._id_gupy):
            if i in self.por_id:
                return self.por_id[i]
        return self.por_chave.get(chave_vaga(doc.get("titulo"), doc.get("empresa")) or "")


def ids_vistos() -> set[str]:
    """Todos os IDs de vaga já registrados (ids_da_vaga de cada uma)."""
    return set(IndiceVistas().por_id)


def achar_repetida(doc: dict) -> dict | None:
    """Vaga já registrada que é a mesma que `doc` (veja IndiceVistas)."""
    vid = IndiceVistas().achar(doc)
    return obter(vid) if vid else None


def registrar_outros_portais(vid: str, plataformas: list[str], ids: list[str]) -> dict | None:
    """A mesma vaga apareceu em outro portal: as plataformas de lá viram etiquetas a mais (outras_plataformas) e os
    ids de lá passam a contar como dela (ids_relacionados). Não mexe em nada do usuário nem da análise."""
    doc = obter(vid)
    if doc is None:
        return None
    extras = list(doc.get("outras_plataformas") or [])
    relacionados = list(doc.get("ids_relacionados") or [])
    for p in plataformas:
        if p in PLATAFORMAS and p != "Outra" and p != doc.get("plataforma") and p not in extras:
            extras.append(p)
    for i in map(str, ids):
        if i and i != vid and i not in relacionados:
            relacionados.append(i)
    if extras == (doc.get("outras_plataformas") or []) and relacionados == (doc.get("ids_relacionados") or []):
        return doc
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            return None
        doc.update(outras_plataformas=extras, ids_relacionados=relacionados, atualizada_em=agora())
        _gravar(con, vid, doc)
    return doc


# ---------------------------------------------------------------- validação

def _texto(v, maximo: int) -> str:
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError("esperava texto")
    return v.strip()[:maximo]


def _data_ou_nulo(v):
    if v in (None, ""):
        return None
    if not isinstance(v, str) or not DATA_VALIDA.match(v):
        raise ValueError("data deve ser AAAA-MM-DD")
    return v


def _lista(v, maximo: int = 6) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        raise ValueError("esperava lista de textos")
    return [str(x).strip()[:300] for x in v if str(x).strip()][:maximo]


def _validar_usuario(campos: dict) -> dict:
    """Campos que o dashboard pode alterar."""
    limpos = {}
    for k, v in campos.items():
        if k == "triagem":
            if v not in TRIAGENS:
                raise ValueError("triagem inválida")
        elif k == "etapa":
            if v is not None and v not in ETAPAS:
                raise ValueError("etapa inválida")
        elif k == "resultado":
            if v is not None and v not in RESULTADOS:
                raise ValueError("resultado inválido")
        elif k in ("etapa_em", "triada_em"):
            v = _data_ou_nulo(v)
        elif k == "anotacao":
            v = _texto(v, 5000)
        elif k == "kit":
            v = kit.validar_kit(v)
        elif k == "lembretes":
            v = kit.validar_lembretes(v)
        elif k == "entrevista_em":
            v = _data_ou_nulo(v)
        else:
            raise ValueError(f"campo não editável: {k}")
        limpos[k] = v
    return limpos


def validar_analise(a: dict) -> dict:
    status = a.get("analise_status", "feita")
    if status not in ("feita", "sem_dados"):
        raise ValueError("analise_status deve ser 'feita' ou 'sem_dados'")
    limpos = {
        "analise_status": status,
        "analisada_em": hoje(),
        "resumo": _texto(a.get("resumo"), 400),
        "encaixe": _lista(a.get("encaixe")),
        "lacunas": _lista(a.get("lacunas")),
        "alertas": _lista(a.get("alertas")),
    }
    if status == "feita":
        try:
            limpos["aderencia"] = max(0, min(100, int(round(float(a["aderencia"])))))
        except (KeyError, TypeError, ValueError):
            raise ValueError("'aderencia' ausente ou inválida") from None
    modelo = a.get("modelo_trabalho")
    if modelo is not None:
        if modelo not in MODELOS:
            raise ValueError(f"modelo_trabalho deve ser um de {MODELOS}")
        limpos["modelo_trabalho"] = modelo
    niveis = a.get("senioridade")
    if niveis is not None:
        niveis = _lista(niveis)
        if any(n not in SENIORIDADES for n in niveis):
            raise ValueError(f"senioridade deve ser uma lista com {SENIORIDADES}")
        limpos["senioridade"] = [n for n in SENIORIDADES if n in niveis]
        if limpos["senioridade"]:
            origem = a.get("senioridade_origem")
            if origem not in ORIGENS_SENIORIDADE:
                raise ValueError(f"senioridade_origem deve ser um de {ORIGENS_SENIORIDADE}")
            limpos["senioridade_origem"] = origem
    tipos = a.get("tipo_emprego")
    if tipos is not None:
        tipos = _lista(tipos)
        if any(t not in TIPOS_EMPREGO for t in tipos):
            raise ValueError(f"tipo_emprego deve ser uma lista com {TIPOS_EMPREGO}")
        limpos["tipo_emprego"] = [t for t in TIPOS_EMPREGO if t in tipos]
    idioma = str(a.get("idioma") or "").strip().lower()
    if idioma:
        if not re.fullmatch(r"[a-z]{2}", idioma):
            raise ValueError("idioma deve ser um código de 2 letras (pt, en, es…)")
        limpos["idioma"] = idioma
    moeda = str(a.get("moeda") or "").strip().upper()
    if moeda:
        if len(moeda) != 3 or not moeda.isalpha():
            raise ValueError("moeda deve ser um código de 3 letras (BRL, USD, EUR…)")
        limpos["moeda"] = moeda
    limpos.update(kit.validar_analise(a))  # o que a candidatura pede e o que pode impedir
    if a.get("fora_dos_criterios"):
        limpos["fora_dos_criterios"] = _texto(a["fora_dos_criterios"], 200)
    provedor = str(a.get("analise_provedor") or "").strip()
    if provedor:  # qual IA deu a nota (ia.PROVEDORES); vazio nas análises feitas pelo chat
        if not re.match(r"^[a-z_]{1,32}$", provedor):
            raise ValueError("analise_provedor inválido")
        limpos["analise_provedor"] = provedor
        limpos["analise_modelo"] = _texto(a.get("analise_modelo"), 120)
    return limpos


# ---------------------------------------------------------------- escrita

def aplicar_criterios(doc: dict) -> None:
    """Vaga do relatório que fura os filtros da busca vai para Fora dos critérios, como as da busca. Também
    grava os sinais positivos (patrocínio de visto, relocation, frases da pessoa), em qualquer vaga."""
    try:
        raiz = str(DASH.parent)
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        import filtros  # filtros.py, na raiz do projeto
        f = filtros.efetivos(filtros.ler_config())
        sinais = filtros.sinais(doc, f)
        if sinais:
            doc["sinais"] = sinais
        else:
            doc.pop("sinais", None)
        if doc.get("origem") == "manual" or doc.get("triagem") != "pendente":
            return
        motivos = filtros.criterios(doc, f)
    except Exception:  # config ausente ou com erro não impede gravar a vaga
        return
    if motivos:
        doc.update(triagem="fora", triada_em=hoje(), motivo_fora=motivos)


def definir_area(doc: dict, campos: dict | None = None) -> None:
    """Área (nacional ou internacional) e país da vaga: o que a pessoa escolheu, senão o palpite pelo local."""
    campos = campos or {}
    try:
        raiz = str(DASH.parent)
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        import filtros
        f = filtros.efetivos(filtros.ler_config())
    except Exception:
        return
    if campos.get("area") in filtros.AREAS:
        doc["area"] = campos["area"]
        pais = _texto(campos.get("pais_vaga"), 60)
        doc["pais_vaga"] = (filtros.pais_pt(pais) or pais or filtros.pais_do_local(doc.get("local"))) if doc["area"] == "internacional" else None
    else:
        doc["area"], doc["pais_vaga"] = filtros.area_da_vaga({**doc, "area": None}, f)
    if not doc.get("idioma"):  # como nas vagas da busca: o checklist pede o currículo no idioma da vaga
        idioma = filtros.idioma_da_vaga(doc)
        if idioma:
            doc["idioma"] = idioma


def _da_fonte(doc: dict, dados: dict) -> None:
    """O que a leitura do link trouxe além do básico: restrição de local, sistema de candidatura, link de
    candidatura, salário, moeda e idioma."""
    extras = {
        "restricao_local": _texto(dados.get("restricao_local"), 200),
        "ats": dados.get("ats") if dados.get("ats") in SISTEMAS_ATS else None,
        "url_candidatura": _texto(dados.get("url_candidatura"), 1000),
        "salario": _texto(dados.get("salario"), 80),
        "moeda": _texto(dados.get("moeda"), 3).upper(),
        "idioma": _texto(dados.get("idioma"), 2).lower(),
        "modelo_trabalho": dados.get("modelo_trabalho") if dados.get("modelo_trabalho") in ("remoto", "hibrido", "presencial") else "",
    }
    if not re.match(r"^https?://", extras["url_candidatura"], re.I):
        extras["url_candidatura"] = ""
    if not re.fullmatch(r"[A-Z]{3}", extras["moeda"]):
        extras["moeda"] = ""
    if not re.fullmatch(r"[a-z]{2}", extras["idioma"]):
        extras["idioma"] = ""
    doc.update({k: v for k, v in extras.items() if v})


def criar_manual(campos: dict) -> dict:
    """Vaga trazida pelo usuário pelo botão Adicionar Vaga (preenchida à mão).

    Com etapa "relatorio", vai para o Relatório de Vagas como as da busca (origem "link");
    nas outras etapas, direto para o quadro.
    """
    titulo = _texto(campos.get("titulo"), 200)
    empresa = _texto(campos.get("empresa"), 120)
    if not titulo or not empresa:
        raise ValueError("cargo e empresa são obrigatórios")
    plataforma = campos.get("plataforma") if campos.get("plataforma") in PLATAFORMAS else "Outra"
    no_relatorio = campos.get("etapa") == "relatorio"
    etapa = campos.get("etapa") if campos.get("etapa") in ETAPAS else "salva"
    url = _texto(campos.get("url"), 1000)
    if url and not re.match(r"^https?://", url, re.I):
        raise ValueError("o link precisa começar com http:// ou https://")
    descricao = _texto(campos.get("descricao"), 20000)
    m = re.search(r"[?&]jk=([0-9a-f]{16})", url, re.I)
    vid = "m-" + datetime.now().strftime("%y%m%d%H%M%S") + secrets.token_hex(2)
    doc = {
        "origem": "link" if no_relatorio else "manual", "plataforma": plataforma, "titulo": titulo, "empresa": empresa,
        "local": _texto(campos.get("local"), 120), "url": url, "jk": m.group(1).lower() if m else None,
        "descricao": descricao, "triagem": "pendente" if no_relatorio else "seguir",
        "etapa": None if no_relatorio else etapa, "etapa_em": None if no_relatorio else hoje(),
        "encontrada_em": hoje(), "resultado": None, "anotacao": "",
        "analise_status": "pendente" if descricao or (url and not no_relatorio) else "sem_dados",
        "criada_em": agora(), "atualizada_em": agora(),
    }
    definir_area(doc, campos)
    if no_relatorio:
        doc["termos"] = []
    aplicar_criterios(doc)
    with escrita() as con:
        _gravar(con, vid, doc)
    doc["id"] = vid
    return doc


def criar_de_link(dados: dict) -> tuple[dict, bool]:
    """Vaga lida pelo link (fontes/link.py): vai para o Relatório de Vagas, como as da busca.

    Devolve (vaga, nova). Se a vaga já está no banco (a busca já tinha trazido, ou é a
    mesma de outro portal: link de candidatura ou cargo + empresa iguais), devolve a que
    existe, sem mudar nada.
    """
    vid = str(dados.get("id") or "")
    if not ID_VALIDO.match(vid):
        raise ValueError("id de vaga inválido")
    descricao = _texto(dados.get("descricao"), 20000)
    doc = {
        "origem": "link", "plataforma": dados.get("plataforma") if dados.get("plataforma") in PLATAFORMAS else "Outra",
        "titulo": _texto(dados.get("titulo"), 200), "empresa": _texto(dados.get("empresa"), 120),
        "local": _texto(dados.get("local"), 120), "remoto": bool(dados.get("remoto")),
        "publicada_em": _data_ou_nulo(dados.get("publicada_em")), "url": _texto(dados.get("url"), 1000),
        "tipo": _texto(dados.get("tipo"), 80) or None, "descricao": descricao, "termos": [],
        "analise_status": "pendente" if descricao else "sem_dados",
        "triagem": "pendente", "triada_em": None, "etapa": None, "etapa_em": None, "resultado": None, "anotacao": "",
        "encontrada_em": hoje(), "criada_em": agora(), "atualizada_em": agora(),
    }
    if not doc["titulo"] or not doc["empresa"]:
        raise ValueError("cargo e empresa são obrigatórios")
    _da_fonte(doc, dados)
    definir_area(doc, dados)
    repetida = achar_repetida({**doc, "id": vid})
    if repetida is not None:  # a plataforma do link vira mais uma etiqueta da vaga que já existe
        return registrar_outros_portais(repetida["id"], [doc["plataforma"]], [vid]) or repetida, False
    aplicar_criterios(doc)
    with escrita() as con:
        atual = _ler(con, vid)
        if atual is not None:
            atual["id"] = vid
            return atual, False
        _gravar(con, vid, doc)
    doc["id"] = vid
    return doc, True


def atualizar_usuario(vid: str, campos: dict) -> dict:
    limpos = _validar_usuario(campos)
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        doc.update(limpos)
        doc["atualizada_em"] = agora()
        _gravar(con, vid, doc)
    return doc


def anotar(vid: str, texto: str) -> dict:
    """Acrescenta uma linha às anotações da vaga, sem apagar o que já está lá."""
    texto = _texto(texto, 500)
    if not texto:
        raise ValueError("texto vazio")
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        atual = (doc.get("anotacao") or "").rstrip()
        doc["anotacao"] = _texto(f"{atual}\n{texto}" if atual else texto, 5000)
        doc["atualizada_em"] = agora()
        _gravar(con, vid, doc)
    return doc


def registrar_curriculo(vid: str, nome: str) -> dict:
    """Liga à vaga um currículo gerado pela página (nome dos arquivos em curriculos/)."""
    if not re.fullmatch(r"[a-z0-9-]{1,90}", str(nome or "")):
        raise ValueError("nome de currículo inválido")
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        doc["curriculos"] = [*[c for c in doc.get("curriculos") or [] if c != nome], nome]
        doc["atualizada_em"] = agora()
        _gravar(con, vid, doc)
    return doc


def registrar_documento(vid: str, tipo: str, nome: str) -> dict:
    """Liga à vaga uma carta ou um conjunto de respostas gerado pela página (nome dos arquivos em curriculos/)."""
    if tipo not in ("carta", "respostas") or not re.fullmatch(r"[a-z0-9-]{1,90}", str(nome or "")):
        raise ValueError("documento inválido")
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        doc["documentos"] = [*[d for d in doc.get("documentos") or [] if d.get("nome") != nome],
                             {"tipo": tipo, "nome": nome, "criado_em": agora()}]
        doc["atualizada_em"] = agora()
        _gravar(con, vid, doc)
    return doc


def curriculos_base() -> dict:
    """O currículo da própria pessoa de cada idioma ({pt, en}: {nome, url} ou None), para o checklist das vagas."""
    try:
        raiz = str(DASH.parent)
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        import curriculo_base  # curriculo_base.py, na raiz do projeto
        marcados = curriculo_base.marcados()
    except Exception:  # config ausente ou com erro não impede listar as vagas
        return {}
    return {k: {"nome": Path(v).name, "url": f"/arquivos/curriculo-base/{k}"} if v else None for k, v in marcados.items()}


def com_kit(v: dict, base: dict | None = None) -> dict:
    """A vaga com o checklist e o lembrete calculados (o que a página e a skill mostram)."""
    base = curriculos_base() if base is None else base
    return {**v, "checklist": kit.checklist(v, base), "lembretes_pendentes": kit.lembretes(v)}


def remover(vid: str) -> None:
    """Vaga manual é apagada; vaga do Indeed só sai do quadro (continua como visitada)."""
    with escrita() as con:
        doc = _ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        if doc.get("origem") == "manual":
            con.execute("DELETE FROM vagas WHERE id = ?", (vid,))
        else:
            doc.update({"triagem": "visitada", "etapa": None, "resultado": None, "triada_em": hoje(),
                        "atualizada_em": agora()})
            _gravar(con, vid, doc)


def inserir_vagas(docs: list[dict]) -> tuple[list[str], list[str]]:
    """Insere vagas novas sem nunca sobrescrever uma existente. Devolve (inseridas, já existentes)."""
    novas, existentes = [], []
    with escrita() as con:
        for doc in docs:
            vid = doc["id"]
            if con.execute("SELECT 1 FROM vagas WHERE id = ?", (vid,)).fetchone():
                existentes.append(vid)
                continue
            _gravar(con, vid, doc)
            novas.append(vid)
    return novas, existentes


def registrar_busca(bid: str, dados: dict) -> None:
    with escrita() as con:
        con.execute("INSERT OR REPLACE INTO buscas (id, dados) VALUES (?, ?)", (bid, json.dumps(dados, ensure_ascii=False)))


def aplicar_analises(analises: list[dict]) -> tuple[list[str], list[str]]:
    """Grava análises do Claude. Não toca em etapa, resultado nem anotações; vaga do relatório
    ainda sem decisão que furar os filtros da busca vai para Fora dos critérios."""
    ok, problemas = [], []
    with escrita() as con:
        for a in analises:
            vid = str(a.get("id", ""))
            doc = _ler(con, vid)
            if doc is None:
                problemas.append(f"{vid!r}: vaga não encontrada")
                continue
            try:
                doc.update(validar_analise(a))
            except ValueError as e:
                problemas.append(f"{vid}: {e}")
                continue
            aplicar_criterios(doc)
            doc["atualizada_em"] = agora()
            _gravar(con, vid, doc)
            ok.append(vid)
    return ok, problemas


def backup_diario() -> Path | None:
    """Uma cópia por dia em dash/dados/backup, mantendo as mais recentes."""
    if not ARQUIVO.exists():
        return None
    BACKUPS.mkdir(parents=True, exist_ok=True)
    destino = BACKUPS / f"candidaturas-{hoje()}.db"
    if not destino.exists():
        with closing(conectar()) as origem, closing(sqlite3.connect(destino)) as copia:
            origem.backup(copia)
    for velho in sorted(BACKUPS.glob("candidaturas-*.db"))[:-MANTER_BACKUPS]:
        velho.unlink()
    return destino


# ---------------------------------------------------------------- linha de comando

def _cmd_quadro(args) -> int:
    vagas = [v for v in listar_vagas() if v.get("etapa") and (v.get("origem") == "manual" or v.get("triagem") == "seguir")]
    if args.etapa:
        vagas = [v for v in vagas if v["etapa"] == args.etapa]
    todas = listar_vagas()
    pend = sum(1 for v in todas if v.get("origem") != "manual" and v.get("triagem") == "pendente")
    fora = sum(1 for v in todas if v.get("triagem") == "fora")
    print(f"Relatório de Vagas: {pend} vaga(s) esperando decisão; {fora} fora dos critérios.")
    for etapa in ETAPAS:
        grupo = sorted((v for v in vagas if v["etapa"] == etapa), key=lambda v: v.get("etapa_em") or "", reverse=True)
        if not grupo and args.etapa:
            continue
        print(f"\n## {etapa} ({len(grupo)})")
        for v in grupo:
            extra = []
            if v.get("resultado"):
                extra.append(v["resultado"])
            if isinstance(v.get("aderencia"), int):
                extra.append(f"aderência {v['aderencia']}")
            if v.get("analise_status") == "pendente":
                extra.append("aguardando análise")
            nota = (v.get("anotacao") or "").replace("\n", " ")
            print(f"- {v.get('titulo')} | {v.get('empresa')} | {_plataformas(v)} | desde {v.get('etapa_em') or '?'}"
                  + (f" | {', '.join(extra)}" if extra else "") + (f" | nota: {nota[:120]}" if nota else ""))
    return 0


def precisa_analise(v: dict) -> bool:
    """Adicionada à mão esperando análise, ou trazida pela busca sem nota e ainda não descartada."""
    if v.get("analise_status") == "pendente":
        return True
    return v.get("analise_status") == "sem_analise" and v.get("triagem") not in ("visitada", "fora")


def _plataformas(v: dict) -> str:
    return " + ".join([v.get("plataforma") or "Outra", *(v.get("outras_plataformas") or [])])


def _cmd_pendentes(args) -> int:
    pend = [v for v in listar_vagas() if precisa_analise(v)]
    campos = ("id", "origem", "titulo", "empresa", "plataforma", "local", "url", "descricao")
    print(json.dumps([{k: v.get(k) for k in campos} for v in pend], ensure_ascii=False, indent=1))
    print(f"\n{len(pend)} vaga(s) aguardando análise.", file=sys.stderr)
    return 0


def _cmd_analisar(args) -> int:
    bruto = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
    analises = bruto.get("analises", []) if isinstance(bruto, dict) else bruto
    ok, problemas = aplicar_analises(analises)
    print(f"{len(ok)} análise(s) gravada(s): {', '.join(ok) or '-'}")
    for p in problemas:
        print(f"  problema: {p}")
    return 1 if problemas and not ok else 0


def _cmd_vaga(args) -> int:
    achadas = procurar(args.texto)
    if not achadas:
        print(f"Nenhuma vaga com {args.texto!r}.", file=sys.stderr)
        return 1
    if len(achadas) > 1:
        print(f"{len(achadas)} vagas com {args.texto!r}; use o ID ou um trecho mais específico:")
        for v in achadas:
            onde = v.get("etapa") or f"relatório ({v.get('triagem')})"
            print(f"- {v['id']} | {v.get('titulo')} | {v.get('empresa')} | {onde}")
        return 1
    v = achadas[0]
    print(f"## {v.get('titulo')} — {v.get('empresa')} ({v['id']})")
    linha = [_plataformas(v), v.get("local") or "local não informado", f"publicada {v.get('publicada_em') or '?'}"]
    if v.get("salario"):
        linha.append(f"salário: {v['salario']}")
    print(" · ".join(linha))
    print(f"Link: {v.get('url') or '-'}")
    print(f"Etapa: {v.get('etapa') or '-'} · triagem: {v.get('triagem') or '-'}")
    if v.get("termos"):
        print(f"Encontrada pelos termos: {', '.join(v['termos'])}")
    if v.get("motivo_fora"):
        print(f"Fora dos critérios: {'; '.join(v['motivo_fora'])}")
    if v.get("senioridade"):
        print(f"Senioridade: {'/'.join(v['senioridade'])} ({v.get('senioridade_origem') or 'pelo título'})")
    if isinstance(v.get("aderencia"), int):
        print(f"\nAderência {v['aderencia']}: {v.get('resumo') or ''}")
        for rotulo, campo in (("Encaixe", "encaixe"), ("Lacunas", "lacunas"), ("Alertas", "alertas")):
            if v.get(campo):
                print(f"{rotulo}: " + "; ".join(v[campo]))
    if v.get("anotacao"):
        print(f"\nAnotações:\n{v['anotacao']}")
    print(f"\n{v.get('descricao') or '(sem descrição)'}")
    return 0


def _cmd_anotar(args) -> int:
    try:
        v = anotar(args.id, args.texto)
    except KeyError:
        print(f"Vaga {args.id} não existe.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"Anotado em {v.get('titulo')} — {v.get('empresa')}.")
    return 0


def _cmd_kit(args) -> int:
    achadas = procurar(args.texto)
    if len(achadas) != 1:
        return _cmd_vaga(args)  # nenhuma ou várias: a mesma mensagem do comando vaga
    v = com_kit(achadas[0])
    print(f"## {v.get('titulo')} — {v.get('empresa')} ({v['id']})")
    for rotulo, campo, opcoes, chave in (("Autorização", "autorizacao", kit.AUTORIZACAO, "valor"),
                                         ("Inglês", "ingles", kit.INGLES, "nivel")):
        if v.get(campo):
            print(f"{rotulo}: {opcoes[v[campo][chave]]} (“{v[campo]['frase']}”)")
    for c in v.get("contratacao") or []:
        print(f"Contratação: {kit.CONTRATACAO[c['valor']]} (“{c['frase']}”)")
    if v.get("fuso"):
        print(f"Fuso: {v['fuso']['texto']} (“{v['fuso']['frase']}”)")
    for r in v.get("riscos") or []:
        print(f"Atenção: {kit.RISCOS[r['tipo']]} (“{r['frase']}”)")
    print("\nO que esta candidatura pede:")
    for i in v["checklist"]:
        print(f"- [{kit.ESTADOS[i['estado']]}] {i['rotulo']}" + (f" (“{i['frase']}”)" if i.get("frase") else ""))
    for lem in v["lembretes_pendentes"]:
        print(f"\nLembrete: {lem['rotulo']} (desde {lem['desde']})")
    return 0


def _cmd_lembretes(args) -> int:
    pendentes = [(v, lem) for v in listar_vagas() for lem in kit.lembretes(v)]
    if not pendentes:
        print("Nenhum lembrete pendente no quadro.")
    for v, lem in sorted(pendentes, key=lambda x: x[1]["desde"]):
        print(f"- {lem['rotulo']} (desde {lem['desde']}): {v.get('titulo')} — {v.get('empresa')} ({v['id']})")
    return 0


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quadro", help="resumo do quadro de candidaturas")
    q.add_argument("--etapa", choices=ETAPAS)
    sub.add_parser("pendentes", help="vagas adicionadas à mão aguardando análise (JSON)")
    a = sub.add_parser("analisar", help="grava análises de um arquivo JSON")
    a.add_argument("arquivo")
    v = sub.add_parser("vaga", help="dados completos de uma vaga (ID ou trecho do cargo/empresa)")
    v.add_argument("texto")
    n = sub.add_parser("anotar", help="acrescenta uma linha às anotações da vaga")
    n.add_argument("id")
    n.add_argument("texto")
    k = sub.add_parser("kit", help="o que a candidatura pede (checklist) e o lembrete da vaga")
    k.add_argument("texto")
    sub.add_parser("lembretes", help="lembretes de follow-up pendentes no quadro")
    args = ap.parse_args()
    return {"quadro": _cmd_quadro, "pendentes": _cmd_pendentes, "analisar": _cmd_analisar,
            "vaga": _cmd_vaga, "anotar": _cmd_anotar, "kit": _cmd_kit, "lembretes": _cmd_lembretes}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
