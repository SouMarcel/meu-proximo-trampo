"""Chaves de API locais: o arquivo .env da raiz (fora do Git) e as variáveis de ambiente.

  ler(nome)            valor da chave (a variável de ambiente vence o .env), ou ""
  origem(nome)         "ambiente", "arquivo" ou None
  final(nome)          últimos 4 caracteres, para a página mostrar sem revelar a chave
  gravar(nome, valor)  grava NOME=valor no .env, preservando as outras linhas e comentários
  remover(nome)        tira a linha do .env, preservando o resto

Só biblioteca padrão. Usado por ia.py e pelas fontes que aceitam chave (ex.: startup.jobs).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ENV = RAIZ / ".env"
LIMITE_VALOR = 400
NOME_VALIDO = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def _linhas() -> list[str]:
    try:
        return ENV.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return []


def _nome_da_linha(linha: str) -> str:
    nome, sep, _ = linha.partition("=")
    if not sep:
        return ""
    nome = nome.strip()
    if nome.startswith("export "):
        nome = nome[len("export "):].strip()
    return nome


def _do_arquivo(nome: str) -> str:
    valor = ""
    for linha in _linhas():
        if not linha.lstrip().startswith("#") and _nome_da_linha(linha) == nome:
            valor = linha.partition("=")[2].strip().strip("'\"")
    return valor


def ler(nome: str) -> str:
    return os.environ.get(nome, "").strip() or _do_arquivo(nome)


def origem(nome: str) -> str | None:
    if os.environ.get(nome, "").strip():
        return "ambiente"
    return "arquivo" if _do_arquivo(nome) else None


def final(nome: str) -> str:
    valor = ler(nome)
    return valor[-4:] if len(valor) >= 8 else ""


def _escrever(linhas: list[str]) -> None:
    tmp = ENV.with_name(ENV.name + ".tmp")
    tmp.write_text("".join(l + "\n" for l in linhas), encoding="utf-8")
    os.replace(tmp, ENV)


def gravar(nome: str, valor: str) -> None:
    """Grava a chave no .env (troca a linha existente ou acrescenta no fim)."""
    if not NOME_VALIDO.match(nome or ""):
        raise ValueError("nome de chave inválido")
    valor = str(valor or "").strip()
    if not valor:
        raise ValueError("a chave está vazia")
    if len(valor) > LIMITE_VALOR or any(c in valor for c in "\r\n\0"):
        raise ValueError("a chave tem um formato inválido (muito longa ou com quebra de linha)")
    linhas, trocou = [], False
    for linha in _linhas():
        if not linha.lstrip().startswith("#") and _nome_da_linha(linha) == nome:
            if not trocou:
                linhas.append(f"{nome}={valor}")
                trocou = True
            continue  # linhas repetidas do mesmo nome somem
        linhas.append(linha)
    if not trocou:
        linhas.append(f"{nome}={valor}")
    _escrever(linhas)


def remover(nome: str) -> bool:
    """Tira a chave do .env. Devolve True se havia alguma linha dela."""
    antes = _linhas()
    depois = [l for l in antes if l.lstrip().startswith("#") or _nome_da_linha(l) != nome]
    if len(depois) == len(antes):
        return False
    _escrever(depois)
    return True
