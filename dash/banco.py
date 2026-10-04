#!/usr/bin/env python3
"""Banco local do dashboard de candidaturas (SQLite, só biblioteca padrão).

Usado pelo servidor (dash/servidor.py), por vagas.py e pela skill buscar-vagas. Também tem
comandos para consultar e analisar vagas sem abrir o navegador:

  python dash/banco.py quadro [--etapa entrevista]   resumo do quadro
  python dash/banco.py pendentes                      vagas esperando análise (JSON)
  python dash/banco.py analisar ARQUIVO.json          grava análises dessas vagas

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
from contextlib import closing, contextmanager
from datetime import date, datetime
from pathlib import Path

DASH = Path(__file__).resolve().parent
ARQUIVO = Path(os.environ.get("TRAMPO_BANCO") or DASH / "dados" / "candidaturas.db")
DADOS = ARQUIVO.parent
BACKUPS = DADOS / "backup"
MANTER_BACKUPS = 10

ETAPAS = ("salva", "aplicada", "entrevista", "proposta", "encerrada")
TRIAGENS = ("pendente", "seguir", "visitada")
RESULTADOS = ("nao_aprovado", "desisti", "cancelada", "contratado")
PLATAFORMAS = ("Indeed", "LinkedIn", "Gupy", "InHire", "Catho", "Outra")
MODELOS = ("remoto", "hibrido", "presencial", "nao_informado")
SENIORIDADES = ("junior", "pleno", "senior")
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


def ultima_busca() -> dict | None:
    with closing(conectar()) as con:
        linha = con.execute("SELECT id, dados FROM buscas ORDER BY id DESC LIMIT 1").fetchone()
    if not linha:
        return None
    doc = json.loads(linha[1])
    doc["id"] = linha[0]
    return doc


def ids_vistos() -> set[str]:
    """Todos os IDs do Indeed já registrados (inclusive anúncios repetidos e vagas manuais com link do Indeed)."""
    vistos: set[str] = set()
    for doc in listar_vagas():
        vistos.add(doc["id"])
        if doc.get("jk"):
            vistos.add(str(doc["jk"]))
        vistos.update(str(x) for x in doc.get("ids_relacionados") or [])
        m = re.search(r"[?&]jk=([0-9a-f]{16})", str(doc.get("url") or ""))
        if m:
            vistos.add(m.group(1))
    return vistos


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
    return limpos


# ---------------------------------------------------------------- escrita

def criar_manual(campos: dict) -> dict:
    """Vaga trazida pelo usuário pelo botão Adicionar Vaga."""
    titulo = _texto(campos.get("titulo"), 200)
    empresa = _texto(campos.get("empresa"), 120)
    if not titulo or not empresa:
        raise ValueError("cargo e empresa são obrigatórios")
    plataforma = campos.get("plataforma") if campos.get("plataforma") in PLATAFORMAS else "Outra"
    etapa = campos.get("etapa") if campos.get("etapa") in ETAPAS else "salva"
    url = _texto(campos.get("url"), 1000)
    if url and not re.match(r"^https?://", url, re.I):
        raise ValueError("o link precisa começar com http:// ou https://")
    descricao = _texto(campos.get("descricao"), 20000)
    m = re.search(r"[?&]jk=([0-9a-f]{16})", url, re.I)
    vid = "m-" + datetime.now().strftime("%y%m%d%H%M%S") + secrets.token_hex(2)
    doc = {
        "origem": "manual", "plataforma": plataforma, "titulo": titulo, "empresa": empresa,
        "local": _texto(campos.get("local"), 120), "url": url, "jk": m.group(1).lower() if m else None,
        "descricao": descricao, "triagem": "seguir", "etapa": etapa, "etapa_em": hoje(),
        "encontrada_em": hoje(), "resultado": None, "anotacao": "",
        "analise_status": "pendente" if (descricao or url) else "sem_dados",
        "criada_em": agora(), "atualizada_em": agora(),
    }
    with escrita() as con:
        _gravar(con, vid, doc)
    doc["id"] = vid
    return doc


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
    """Grava análises do Claude; não toca em etapa, triagem, resultado nem anotações."""
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
    pend = sum(1 for v in listar_vagas() if v.get("origem") != "manual" and v.get("triagem") == "pendente")
    print(f"Relatório de Vagas: {pend} vaga(s) esperando decisão.")
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
            print(f"- {v.get('titulo')} | {v.get('empresa')} | {v.get('plataforma')} | desde {v.get('etapa_em') or '?'}"
                  + (f" | {', '.join(extra)}" if extra else "") + (f" | nota: {nota[:120]}" if nota else ""))
    return 0


def precisa_analise(v: dict) -> bool:
    """Adicionada à mão esperando análise, ou trazida pela busca sem nota e ainda não descartada."""
    if v.get("analise_status") == "pendente":
        return True
    return v.get("analise_status") == "sem_analise" and v.get("triagem") != "visitada"


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
    args = ap.parse_args()
    return {"quadro": _cmd_quadro, "pendentes": _cmd_pendentes, "analisar": _cmd_analisar}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
