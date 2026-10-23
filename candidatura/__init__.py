"""Candidatura assistida (spec 027; constituição 4.0.0, princípio VI, "Candidatura assistida"): a ferramenta preenche
os campos do formulário de candidatura aberto na janela dela (navegador.py), com as respostas que a pessoa conferiu.

  dominios     onde o preenchimento é permitido (conhecidos, liberados pela pessoa, bloqueados)
  formulario   ler a página atual, classificar os campos e preencher só os confirmados
  login        usuário e senha guardados no .env, digitados só na página de login do portal

Regras: desligado por padrão; só campos, nunca botões, links, Enter ou envio; só no clique da pessoa, sobre uma
proposta que ela viu; só em domínio liberado; perguntas sensíveis, cadastro, consentimento, anexos e testes ficam
com a pessoa; para no captcha ou verificação. Quem avança e envia é sempre a pessoa.

O estado do recurso fica no config.json (fora do Git), na chave "candidatura":
  {"ligado": bool, "aviso_aceito": "AAAA-MM-DD", "dominios": [{"dominio": "host", "em": "AAAA-MM-DD"}]}
"""
from __future__ import annotations

import json
import os
import sys
import threading
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

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
    return {"ligado": bruto.get("ligado") is True, "aviso_aceito": bruto.get("aviso_aceito") or None, "dominios": dominios}


def _gravar_estado(novo: dict) -> dict:
    cfg = _config()
    cfg["candidatura"] = {"ligado": bool(novo.get("ligado")), "aviso_aceito": novo.get("aviso_aceito"),
                          "dominios": novo.get("dominios") or []}
    _gravar_config(cfg)
    return estado()


def ligar(ligado: bool, aceitar_aviso: bool = False) -> dict:
    """Liga ou desliga o recurso. A primeira vez que liga exige o aviso de risco aceito."""
    atual = estado()
    if ligado and not atual["aviso_aceito"]:
        if not aceitar_aviso:
            raise CandidaturaErro("para ligar, confirme o aviso de risco")
        atual["aviso_aceito"] = date.today().isoformat()
    atual["ligado"] = bool(ligado)
    return _gravar_estado(atual)


def exigir_ligado() -> None:
    if not estado()["ligado"]:
        raise CandidaturaErro("a candidatura assistida está desligada (ligue em Contas conectadas)")
