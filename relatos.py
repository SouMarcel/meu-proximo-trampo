#!/usr/bin/env python3
"""Relatos da pessoa (spec 035): o que ela contou com as próprias palavras, na candidatura assistida, quando o perfil não
respondia a uma pergunta. O relato vale como fato confirmado (constituição IV): entra no texto do perfil usado pela IA
(respostas, currículo, carta, entrevista, nota e análises) e vai para o perfil.md só quando a pessoa pede.

  adicionar(pergunta, relato, resposta, vaga)   guarda (o mesmo relato para a mesma pergunta só é atualizado)
  listar() / editar(id, relato) / apagar(id)    para a pessoa ver e corrigir (Meu perfil → Seus relatos)
  bloco()                                       a seção "Relatos da pessoa" com os que ainda não estão no perfil.md
  com_relatos(perfil)                           o texto do perfil com essa seção, para os pedidos à IA
  levar_ao_perfil(id)                           acrescenta o relato ao perfil.md (a versão anterior fica guardada)

Fica em dash/dados/relatos.json (fora do Git). Documentos (CPF, RG) são mascarados antes de guardar.

  python relatos.py lista       os relatos guardados (para o assistente no chat)
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import threading
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
for _p in (str(RAIZ), str(RAIZ / "dash")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import banco  # noqa: E402  (dash/banco.py: a pasta dos dados)

MAX_RELATOS, TAMANHO_RELATO, TAMANHO_RESPOSTA, TAMANHO_PERGUNTA = 300, 4000, 2000, 500
SECAO_PERFIL = "## Relatos"
TITULO_BLOCO = "## Relatos da pessoa (fatos que ela contou com as próprias palavras; valem como confirmados)"
TRAVA = threading.Lock()


class RelatoErro(ValueError):
    """Relato inválido ou inexistente; a mensagem é para a pessoa (o servidor responde 400 com ela)."""


def arquivo() -> Path:
    return banco.ARQUIVO.parent / "relatos.json"


def _mascarar(texto: str) -> str:
    import primeiros_passos
    return primeiros_passos.mascarar_documentos(texto)


def _texto(v, maximo: int) -> str:
    return _mascarar(" ".join(str(v or "").split()) if maximo <= TAMANHO_PERGUNTA else str(v or "").strip())[:maximo]


def _carregar() -> list[dict]:
    try:
        d = json.loads(arquivo().read_text(encoding="utf-8"))
        return [x for x in d if isinstance(x, dict) and x.get("id")] if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _gravar(itens: list[dict]) -> None:
    alvo = arquivo()
    alvo.parent.mkdir(parents=True, exist_ok=True)
    tmp = alvo.with_name(alvo.name + ".tmp")
    tmp.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, alvo)


def _chave(s: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", str(s or "").lower()).split())


def adicionar(pergunta: str, relato: str, resposta: str = "", vaga: dict | None = None) -> dict | None:
    """Guarda o relato; devolve o registro, ou None se o relato está vazio."""
    relato = _texto(relato, TAMANHO_RELATO)
    if not relato:
        return None
    pergunta = _texto(pergunta, TAMANHO_PERGUNTA)
    registro = {"pergunta": pergunta, "relato": relato, "resposta": _texto(resposta, TAMANHO_RESPOSTA),
                "vaga": ({k: str(vaga.get(k) or "")[:200] for k in ("id", "titulo", "empresa")} if vaga else None),
                "em": datetime.now().isoformat(timespec="seconds")}
    with TRAVA:
        itens = _carregar()
        igual = next((x for x in itens if _chave(x.get("pergunta")) == _chave(pergunta)
                      and _chave(x.get("relato")) == _chave(relato)), None)
        if igual:
            igual.update({k: v for k, v in registro.items() if k != "vaga" or v})
            _gravar(itens)
            return igual
        registro.update(id="r-" + datetime.now().strftime("%y%m%d%H%M%S") + secrets.token_hex(2), no_perfil=False)
        itens.append(registro)
        while len(itens) > MAX_RELATOS:  # saem primeiro os que já estão no perfil, depois os mais antigos
            itens.remove(next((x for x in itens if x.get("no_perfil")), itens[0]))
        _gravar(itens)
    return registro


def listar() -> list[dict]:
    return sorted(_carregar(), key=lambda x: x.get("em") or "", reverse=True)


def _achar(itens: list[dict], rid: str) -> dict:
    achado = next((x for x in itens if x.get("id") == rid), None)
    if achado is None:
        raise RelatoErro("relato não encontrado")
    return achado


def editar(rid: str, relato: str) -> dict:
    relato = _texto(relato, TAMANHO_RELATO)
    if not relato:
        raise RelatoErro("o relato está vazio: para tirar, use Apagar")
    with TRAVA:
        itens = _carregar()
        r = _achar(itens, rid)
        r.update(relato=relato, em=datetime.now().isoformat(timespec="seconds"))
        _gravar(itens)
    return r


def apagar(rid: str) -> None:
    with TRAVA:
        itens = _carregar()
        itens.remove(_achar(itens, rid))
        _gravar(itens)


def bloco(itens: list[dict] | None = None) -> str:
    """A seção dos relatos que ainda não foram levados ao perfil.md (os levados já estão no texto do perfil)."""
    itens = [x for x in (listar() if itens is None else itens) if not x.get("no_perfil")]
    if not itens:
        return ""
    linhas = [TITULO_BLOCO]
    for x in sorted(itens, key=lambda x: x.get("em") or ""):
        linhas.append(f"- Pergunta: {x.get('pergunta') or '(sem pergunta)'}")
        linhas.append(f"  Relato ({(x.get('em') or '')[:10]}): {' '.join(str(x.get('relato') or '').split())}")
    return "\n".join(linhas)


def com_relatos(perfil: str) -> str:
    """O perfil com a seção dos relatos, para os pedidos à IA e a conferência sem IA."""
    extra = bloco()
    perfil = str(perfil or "")
    if not extra:
        return perfil
    return f"{perfil.rstrip()}\n\n{extra}\n" if perfil.strip() else extra + "\n"


def levar_ao_perfil(rid: str) -> dict:
    """Acrescenta o relato à seção "Relatos" do perfil.md (cria a seção se faltar) e o marca como levado."""
    import primeiros_passos
    with TRAVA:
        itens = _carregar()
        r = _achar(itens, rid)
        caminho = primeiros_passos.caminho_perfil()
        atual = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
        if not atual.strip():
            raise RelatoErro("ainda não há perfil: monte o perfil em Meu perfil antes de levar relatos para ele")
        item = f"- {r.get('pergunta') or 'Relato'} — {' '.join(str(r['relato']).split())} ({date.today().isoformat()})"
        linhas = atual.rstrip("\n").split("\n")
        if SECAO_PERFIL in (l.strip() for l in linhas):
            i = next(n for n, l in enumerate(linhas) if l.strip() == SECAO_PERFIL) + 1
            while i < len(linhas) and not linhas[i].startswith("## "):
                i += 1
            while i > 0 and not linhas[i - 1].strip():
                i -= 1
            linhas.insert(i, item)
            novo = "\n".join(linhas)
        else:
            novo = "\n".join(linhas) + f"\n\n{SECAO_PERFIL}\n\nFatos que você contou na candidatura assistida.\n\n{item}"
        _, anterior = primeiros_passos.gravar_perfil(novo)
        r["no_perfil"] = True
        _gravar(itens)
    return {"relato": r, "anterior": anterior.name if anterior else None}


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    args = sys.argv[1:] if argv is None else argv
    if args[:1] != ["lista"]:
        print(__doc__)
        return 1
    itens = listar()
    if not itens:
        print("Nenhum relato guardado.")
    for x in itens:
        onde = " (já no perfil.md)" if x.get("no_perfil") else ""
        print(f"- [{x['id']}] {(x.get('em') or '')[:10]}{onde} — {x.get('pergunta')}\n  {x.get('relato')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
