"""As respostas que a pessoa já deu nos formulários (candidatura assistida, spec 027), para a ferramenta reaproveitar
nas próximas vagas sem perguntar de novo. São fatos que ela confirmou (constituição IV), nunca respostas da IA.

  chave(pergunta)            a pergunta normalizada (sem acento, numeração e pontuação)
  lembrar(campo, texto)      guarda a resposta da pessoa (salvo salário e relocação, que ela confirma a cada vaga)
  valor_para(campo)          a resposta guardada no formato do campo (texto, índice da opção, sim/não), ou None
  listar() / apagar(chave)   para a pessoa ver e corrigir

Fica em dash/dados/respostas_formulario.json (fora do Git), ao lado do banco das vagas.
"""
from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from datetime import date

import banco

NAO_LEMBRAR = {"pretensão salarial", "relocação"}  # mudam de vaga para vaga: a ferramenta pergunta sempre
# fatos estáveis de texto livre: reaproveitados também quando a pergunta vem com outra redação (spec 035)
FATOS = {"nome da mãe": re.compile(r"\b(mae|mother|materno|maiden)\b"),
         "nome do pai": re.compile(r"\b(pai|father|paterno)\b")}
MAX_RESPOSTAS, TAMANHO = 500, 2000
TRAVA = threading.Lock()


def arquivo():
    return banco.ARQUIVO.parent / "respostas_formulario.json"


def _sem_acento(s) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def chave(pergunta) -> str:
    t = _sem_acento(pergunta)
    t = re.sub(r"^\s*\d+\s*[.)\-:]\s*", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())[:300]


def _carregar() -> dict:
    try:
        d = json.loads(arquivo().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _gravar(d: dict) -> None:
    alvo = arquivo()
    alvo.parent.mkdir(parents=True, exist_ok=True)
    tmp = alvo.with_name(alvo.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, alvo)


def _categoria(campo: dict) -> str | None:
    import candidatura_ia
    return candidatura_ia.sensivel(campo.get("rotulo") or "") or candidatura_ia.sensivel(campo.get("nome") or "")


def fato(campo: dict) -> str | None:
    """O fato estável que a pergunta pede (remuneração atual, nome da mãe, nome do pai), para reaproveitar a resposta
    também com outra redação; None para as outras perguntas."""
    if campo.get("tipo") not in ("texto", "area"):
        return None
    if _categoria(campo) == "remuneração atual":
        return "remuneração atual"
    rotulo = _sem_acento(campo.get("rotulo"))
    if "nome" in rotulo or "name" in rotulo:
        return next((f for f, padrao in FATOS.items() if padrao.search(rotulo)), None)
    return None


def lembrar(campo: dict, texto: str) -> bool:
    """Guarda a resposta (o texto legível: o da opção, "sim"/"não" ou o digitado). Devolve se guardou."""
    categoria = _categoria(campo)
    k = chave(campo.get("rotulo"))
    texto = str(texto or "").strip()[:TAMANHO]
    if not k or not texto or categoria in NAO_LEMBRAR:
        return False
    with TRAVA:
        d = _carregar()
        if k not in d and len(d) >= MAX_RESPOSTAS:
            return False
        d[k] = {"pergunta": str(campo.get("rotulo") or "")[:500], "resposta": texto, "categoria": categoria,
                "fato": fato(campo), "em": date.today().isoformat()}
        _gravar(d)
    return True


def _norm(s) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", _sem_acento(s)).split())


def valor_para(campo: dict) -> str | None:
    """A resposta guardada para esta pergunta, no formato do campo. None se não há, ou se não cabe no campo
    (ex.: a opção guardada não existe nesta página)."""
    if _categoria(campo) in NAO_LEMBRAR:
        return None
    guardadas = _carregar()
    r = guardadas.get(chave(campo.get("rotulo")))
    alvo = fato(campo)
    if not r and alvo:  # outra redação do mesmo fato: a resposta mais recente dele (as antigas, sem "fato", pela pergunta)
        iguais = [x for x in guardadas.values()
                  if (x.get("fato") or fato({"rotulo": x.get("pergunta"), "tipo": "texto"})) == alvo]
        r = max(iguais, key=lambda x: x.get("em") or "") if iguais else None
    if not r:
        return None
    texto, tipo = r["resposta"], campo.get("tipo")
    if tipo in ("selecao", "unica", "lista", "multipla"):
        alvos = [_norm(x) for x in texto.split(";")] if tipo == "multipla" else [_norm(texto)]
        achados = [o["valor"] for o in campo.get("opcoes") or [] if not o.get("vazia") and _norm(o.get("texto")) in alvos]
        if not achados or (tipo != "multipla" and len(achados) != 1) or (tipo == "multipla" and len(achados) != len(alvos)):
            return None
        return ",".join(achados)
    if tipo == "caixa":
        return {"sim": "sim", "nao": "nao"}.get(_norm(texto))
    if tipo in ("texto", "area"):
        limite = int(campo.get("limite") or 0)
        return None if limite and len(texto) > limite else texto
    return None


def listar() -> list[dict]:
    return sorted(({"chave": k, **v} for k, v in _carregar().items()), key=lambda x: x.get("em") or "", reverse=True)


def apagar(k: str) -> bool:
    with TRAVA:
        d = _carregar()
        if k not in d:
            return False
        d.pop(k)
        _gravar(d)
    return True
