"""Candidatura assistida (spec 027; constituição 4.0.0, princípio VI, "Candidatura assistida"): a ferramenta preenche
os campos do formulário de candidatura aberto na janela dela (navegador.py), com as respostas que a pessoa conferiu.

  dominios     onde o preenchimento é permitido (conhecidos, liberados pela pessoa, bloqueados)
  formulario   ler a página atual, classificar os campos e preencher só os confirmados
  login        usuário e senha guardados no .env, digitados só na página de login do portal

Regras: desligado por padrão, vaga a vaga (a pessoa liga em cada vaga, com o aviso de risco); só campos, nunca botões, links, Enter ou envio; só no clique da pessoa, sobre uma
proposta que ela viu; só em domínio liberado; perguntas sensíveis, cadastro, consentimento, anexos e testes ficam
com a pessoa; para no captcha ou verificação. Quem avança e envia é sempre a pessoa.

Cada vaga guarda a sua chave em "candidatura_assistida": {"ligada": bool, "em": "AAAA-MM-DD"} (banco local).
Os sites liberados pela pessoa ficam no config.json (fora do Git), em "candidatura": {"dominios": [{"dominio", "em"}]}.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "dash"), str(RAIZ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

AVISO = ("A candidatura assistida preenche os campos do formulário na janela da ferramenta; quem avança e envia é "
         "você. Os portais podem restringir contas que considerem automatizadas. Usuário e senha que você guardar "
         "ficam em texto no arquivo .env deste computador (fora do Git), legíveis por programas da sua conta.")
TRAVA = threading.Lock()  # um preenchimento por vez (FR: dois cliques não preenchem em dobro)


class CandidaturaErro(Exception):
    """Mensagem legível para a pessoa; nunca traz senha nem dados da página."""


def _config() -> dict:
    import filtros
    return filtros.ler_config()


def _gravar_config(cfg: dict) -> None:
    import filtros
    tmp = filtros.CONFIG.with_name(filtros.CONFIG.name + ".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, filtros.CONFIG)


def estado() -> dict:
    bruto = _config().get("candidatura")
    bruto = bruto if isinstance(bruto, dict) else {}
    dominios = [d for d in bruto.get("dominios") or [] if isinstance(d, dict) and d.get("dominio")]
    return {"dominios": dominios}


def _gravar_estado(novo: dict) -> dict:
    cfg = _config()
    cfg["candidatura"] = {"dominios": novo.get("dominios") or []}  # a antiga chave geral ("ligado") sai
    _gravar_config(cfg)
    return estado()


def ligada(vaga: dict | None) -> bool:
    return bool(vaga) and (vaga.get("candidatura_assistida") or {}).get("ligada") is True


def exigir_ligada(vaga: dict | None) -> None:
    if not ligada(vaga):
        raise CandidaturaErro("a candidatura assistida não está ligada nesta vaga (ligue no detalhe da vaga, aba Candidatura)")


def ligar_vaga(vid: str, ligar: bool, aceitar_aviso: bool = False) -> dict:
    """Liga ou desliga a candidatura assistida numa vaga. Ligar exige o aviso de risco aceito, a cada vaga."""
    import banco
    if ligar and not aceitar_aviso:
        raise CandidaturaErro("para ligar nesta vaga, confirme o aviso de risco")
    with banco.escrita() as con:
        doc = banco._ler(con, vid)
        if doc is None:
            raise KeyError(vid)
        doc["candidatura_assistida"] = {"ligada": bool(ligar), "em": date.today().isoformat()}
        doc["atualizada_em"] = banco.agora()
        banco._gravar(con, vid, doc)
    return doc
