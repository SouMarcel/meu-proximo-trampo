"""Fonte de vagas falsa para os testes e a validação (contrato de fontes/__init__.py). Nada sai da máquina.

Os parâmetros de módulo mudam o comportamento: PAUSA (segundos por consulta), ERRO (mensagem devolvida
em toda consulta, sem vagas), POR_TERMO (vagas por consulta) e COM_DESCRICAO (False: a descrição vem
por descrever(), como na Gupy). CHAMADAS e DESCRITAS contam o uso.
"""
from __future__ import annotations

import re
import time
from datetime import date

NOME = "falsa"
PLATAFORMA = "Falsa"
PAUSA = 0.0
ERRO = ""
POR_TERMO = 3
COM_DESCRICAO = True
CHAMADAS: list[dict] = []
DESCRITAS: list[str] = []


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
    CHAMADAS.append(dict(consulta))
    if PAUSA:
        time.sleep(PAUSA)
    if ERRO:
        return [], [ERRO]
    termo = consulta["termo"].strip('"')
    vagas = []
    for i in range(min(POR_TERMO, por_termo)):
        # a vaga 0 é a mesma para todos os termos (aparece repetida entre consultas)
        chave = "comum" if i == 0 else f"{_slug(termo)}-{consulta['grupo'].replace(':', '-')}-{i}"
        vagas.append({
            "id": f"falsa-{_slug(chave)}", "titulo": "Analista Comum" if i == 0 else f"{termo.title()} {i}",
            "empresa": "Empresa Comum" if i == 0 else f"Empresa {i}", "local": consulta.get("local") or "Remoto",
            "remoto": bool(consulta.get("remoto")), "publicada_em": date.today().isoformat(),
            "url": f"https://exemplo.invalid/vaga/{_slug(chave)}", "url_candidatura": None, "salario": None,
            "tipo": None, "descricao": f"Descrição da vaga {chave}." if COM_DESCRICAO else "", "plataforma": PLATAFORMA,
        })
    return vagas, []


def descrever(vaga: dict) -> str:
    DESCRITAS.append(vaga["id"])
    return vaga.get("descricao") or f"Descrição lida à parte da vaga {vaga['id']}."
