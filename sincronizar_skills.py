#!/usr/bin/env python3
"""Gera e confere a cópia das skills de usuário para o Claude Code.

A fonte das skills é .agents/skills/ (lida por Codex, Gemini CLI, OpenCode e Antigravity). O
Claude Code só lê .claude/skills/, então este script copia cada skill de usuário para lá, com um
aviso no SKILL.md dizendo de onde a cópia vem. Edite sempre a fonte e rode de novo.

  python sincronizar_skills.py             recria as cópias
  python sincronizar_skills.py --conferir  só confere: sai com 1 se alguma cópia diverge da fonte

Só biblioteca padrão. As outras pastas de .claude/skills/ (ex.: speckit-*) não são tocadas.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FONTE = RAIZ / ".agents" / "skills"
DESTINO = RAIZ / ".claude" / "skills"
SKILLS = ("analisar-perfil", "buscar-vagas", "consultar-gupy", "gerar-curriculo")


def aviso(nome: str) -> str:
    return f"<!-- Cópia gerada de .agents/skills/{nome}/ por sincronizar_skills.py: edite lá. -->"


def com_aviso(texto: str, nome: str) -> str:
    """O SKILL.md com o aviso logo depois do frontmatter (--- … ---), que precisa continuar no topo."""
    texto = texto.replace("\r\n", "\n")
    if texto.startswith("---\n"):
        fim = texto.find("\n---\n", 4)
        if fim >= 0:
            corte = fim + len("\n---\n")
            return texto[:corte] + aviso(nome) + "\n" + texto[corte:]
    return aviso(nome) + "\n" + texto


def esperado(fonte: Path = FONTE, skills=SKILLS) -> dict[str, bytes]:
    """{caminho dentro de .claude/skills: conteúdo} que a cópia deve ter (fim de linha LF)."""
    saida = {}
    for nome in skills:
        base = fonte / nome
        for arq in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = (Path(nome) / arq.relative_to(base)).as_posix()
            if arq.name == "SKILL.md":
                saida[rel] = com_aviso(arq.read_text(encoding="utf-8"), nome).encode("utf-8")
            else:
                saida[rel] = arq.read_bytes().replace(b"\r\n", b"\n")
    return saida


def atual(destino: Path = DESTINO, skills=SKILLS) -> dict[str, bytes]:
    saida = {}
    for nome in skills:
        base = destino / nome
        if base.is_dir():
            for arq in base.rglob("*"):
                if arq.is_file():
                    saida[arq.relative_to(destino).as_posix()] = arq.read_bytes().replace(b"\r\n", b"\n")
    return saida


def diferencas(fonte: Path = FONTE, destino: Path = DESTINO, skills=SKILLS) -> list[str]:
    e, a = esperado(fonte, skills), atual(destino, skills)
    problemas = []
    for rel in sorted(set(e) | set(a)):
        if rel not in a:
            problemas.append(f"falta na cópia: .claude/skills/{rel}")
        elif rel not in e:
            problemas.append(f"sobrando na cópia: .claude/skills/{rel}")
        elif e[rel] != a[rel]:
            problemas.append(f"diferente da fonte: .claude/skills/{rel}")
    return problemas


def gerar(fonte: Path = FONTE, destino: Path = DESTINO, skills=SKILLS) -> list[str]:
    """Recria as cópias das skills de usuário. Devolve o que estava diferente antes."""
    mudou = diferencas(fonte, destino, skills)
    for nome in skills:
        if not (fonte / nome / "SKILL.md").is_file():
            raise FileNotFoundError(f"fonte não encontrada: .agents/skills/{nome}/SKILL.md")
    for nome in skills:
        if (destino / nome).exists():
            shutil.rmtree(destino / nome)
    for rel, dados in esperado(fonte, skills).items():
        caminho = destino / rel
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(dados)
    return mudou


def main(argv=None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conferir", action="store_true", help="só confere; sai com 1 se alguma cópia diverge")
    args = ap.parse_args(argv)
    if args.conferir:
        problemas = diferencas()
        for p in problemas:
            print(p)
        if problemas:
            print("Rode: python sincronizar_skills.py (e edite sempre em .agents/skills/)")
            return 1
        print(f"Cópias em dia: {', '.join(SKILLS)}.")
        return 0
    mudou = gerar()
    print(f"Cópias recriadas em .claude/skills/: {', '.join(SKILLS)}."
          + (f" Mudou: {len(mudou)} arquivo(s)." if mudou else " Nada mudou."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
