"""IA da ferramenta: a porta única das chamadas diretas (pedido → resposta, sem conversa).

  escolha_efetiva(cfg=None)   {"provedor", "modelo", "url_base"} que a ferramenta usa de fato
  disponivel(cfg=None)        há IA ligada e pronta (chave cadastrada; no Claude Code, o comando)
  responder(pedido, ...)      texto da resposta; levanta IAErro com motivo legível e sem chave
  testar(escolha, chave)      (ok, mensagem) com uma chamada mínima
  validar_escolha(dados)      confere provedor, modelo e endereço
  salvar_escolha(dados)       grava "ia" no config.json (nunca a chave)
  mascarar(texto)             esconde chaves em mensagens
  estado_para_pagina(...)     o que o painel "IA" da página mostra (sem chave)

Adaptadores: Claude Code (linha de comando, assinatura), Messages API da Anthropic e o formato
Chat Completions da OpenAI (OpenAI, OpenRouter, Groq, DeepSeek, Gemini e "outro compatível").
Só biblioteca padrão. As chaves vêm de segredos.py (.env ou variável de ambiente).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import segredos

RAIZ = Path(__file__).resolve().parent
TEMPO_TESTE = 15
TEMPO_TESTE_CLAUDE = 30
MAX_TOKENS_ANTHROPIC = 16000
LIMITE_MODELO = 120
PEDIDO_TESTE = "Responda apenas: ok"


class IAErro(Exception):
    """Falha ao falar com a IA. A mensagem já é legível, em português e sem chave."""


# Catálogo (research.md §2). "modelo" é o padrão sugerido: atual, de uso geral e de custo moderado.
# Conferido na documentação oficial de cada provedor em 2026-10-08; os nomes mudam rápido, revisar ao atualizar.
PROVEDORES = {
    "claude_code": {"nome": "Claude Code (assinatura)", "adaptador": "claude_code", "url": "", "variavel": "",
                    "cobranca": "assinatura", "chave_em": "https://claude.com/claude-code", "modelo": ""},
    "anthropic": {"nome": "Anthropic (Claude)", "adaptador": "anthropic", "url": "https://api.anthropic.com/v1",
                  "variavel": "ANTHROPIC_API_KEY", "cobranca": "uso",
                  "chave_em": "https://platform.claude.com/settings/keys", "modelo": "claude-opus-5-5"},
    "openai": {"nome": "OpenAI", "adaptador": "openai", "url": "https://api.openai.com/v1",
               "variavel": "OPENAI_API_KEY", "cobranca": "uso",
               "chave_em": "https://platform.openai.com/settings/organization/api-keys", "modelo": "gpt-6-luna"},
    "openrouter": {"nome": "OpenRouter", "adaptador": "openai", "url": "https://openrouter.ai/api/v1",
                   "variavel": "OPENROUTER_API_KEY", "cobranca": "uso",
                   "chave_em": "https://openrouter.ai/settings/keys", "modelo": "google/gemini-3.8-flash"},
    "groq": {"nome": "Groq", "adaptador": "openai", "url": "https://api.groq.com/openai/v1",
             "variavel": "GROQ_API_KEY", "cobranca": "uso", "chave_em": "https://console.groq.com/keys", "modelo": "openai/gpt-oss-120b"},
    "deepseek": {"nome": "DeepSeek", "adaptador": "openai", "url": "https://api.deepseek.com/v1",
                 "variavel": "DEEPSEEK_API_KEY", "cobranca": "uso",
                 "chave_em": "https://platform.deepseek.com/api_keys", "modelo": "deepseek-flash"},
    "gemini": {"nome": "Gemini (Google)", "adaptador": "openai",
               "url": "https://generativelanguage.googleapis.com/v1beta/openai",
               "variavel": "GEMINI_API_KEY", "cobranca": "uso",
               "chave_em": "https://aistudio.google.com/apikey", "modelo": "gemini-3.8-flash"},
    "compativel": {"nome": "Outro compatível com OpenAI", "adaptador": "openai", "url": "",
                   "variavel": "IA_COMPATIVEL_API_KEY", "cobranca": "uso", "chave_em": "", "modelo": ""},
    "nenhum": {"nome": "Sem IA", "adaptador": "", "url": "", "variavel": "", "cobranca": "", "chave_em": "",
               "modelo": ""},
}
DICA_ANTHROPIC = "claude-sonnet-5-5 e claude-haiku-4-5-20251001 custam menos que o Opus."
PADROES_CHAVE = re.compile(r"(sk-ant-[A-Za-z0-9_\-]{8,}|sk-[A-Za-z0-9_\-]{8,}|AIza[0-9A-Za-z_\-]{20,}"
                           r"|gsk_[A-Za-z0-9]{10,}|sj_[A-Za-z0-9]{10,})")
URL_VALIDA = re.compile(r"^(https://[^\s/]+|http://(127\.0\.0\.1|localhost)(:\d+)?)(/\S*)?$")


# ---------------------------------------------------------------- escolha

def _ler_config() -> dict:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    import filtros
    try:
        return filtros.ler_config()
    except (OSError, ValueError):
        return {}


def escolha_efetiva(cfg: dict | None = None) -> dict:
    """A escolha gravada; sem ela, o comportamento antigo: Claude Code se instalado e não desligado."""
    cfg = _ler_config() if cfg is None else cfg
    ia = cfg.get("ia") if isinstance(cfg.get("ia"), dict) else None
    if ia and ia.get("provedor") in PROVEDORES:
        return {"provedor": ia["provedor"], "modelo": str(ia.get("modelo") or "").strip(),
                "url_base": str(ia.get("url_base") or "").strip()}
    if cfg.get("analise_automatica") is False or not shutil.which("claude"):
        return {"provedor": "nenhum", "modelo": "", "url_base": ""}
    return {"provedor": "claude_code", "modelo": "", "url_base": ""}


def modelo_efetivo(escolha: dict) -> str:
    return escolha.get("modelo") or PROVEDORES.get(escolha.get("provedor"), {}).get("modelo", "")


def disponivel(cfg: dict | None = None) -> bool:
    escolha = escolha_efetiva(cfg)
    prov = PROVEDORES[escolha["provedor"]]
    if escolha["provedor"] == "nenhum":
        return False
    if prov["adaptador"] == "claude_code":
        return shutil.which("claude") is not None
    return escolha["provedor"] == "compativel" or bool(segredos.ler(prov["variavel"]))


def validar_escolha(dados) -> dict:
    if not isinstance(dados, dict):
        raise ValueError("dados inválidos")
    provedor = str(dados.get("provedor") or "")
    if provedor not in PROVEDORES:
        raise ValueError("escolha um provedor da lista")
    modelo = str(dados.get("modelo") or "").strip()
    if len(modelo) > LIMITE_MODELO or any(c in modelo for c in "\r\n\0"):
        raise ValueError("nome de modelo inválido")
    url = str(dados.get("url_base") or "").strip().rstrip("/")
    if provedor == "compativel":
        if not URL_VALIDA.match(url):
            raise ValueError("informe o endereço do serviço (começando com https://)")
        if not modelo:
            raise ValueError("informe o nome do modelo do serviço")
    else:
        url = ""
    return {"provedor": provedor, "modelo": modelo, "url_base": url}


def salvar_escolha(dados) -> dict:
    """Grava a escolha em config.json → "ia", preservando as outras chaves. Nunca grava chave."""
    escolha = validar_escolha(dados)
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    import filtros
    cfg = filtros.ler_config()
    cfg["ia"] = escolha
    tmp = filtros.CONFIG.with_name(filtros.CONFIG.name + ".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, filtros.CONFIG)
    return escolha


# ---------------------------------------------------------------- erros e chaves

def mascarar(texto, *extras) -> str:
    """Troca por •••• as chaves conhecidas (do .env, do ambiente e as passadas) e padrões típicos."""
    texto = str(texto or "")
    valores = [segredos.ler(p["variavel"]) for p in PROVEDORES.values() if p["variavel"]]
    for valor in [*valores, *extras]:
        if valor and len(str(valor)) >= 8:
            texto = texto.replace(str(valor), "••••")
    return PADROES_CHAVE.sub("••••", texto)


def motivo_http(status: int, corpo: str = "", modelo: str = "") -> str:
    baixo = (corpo or "").lower()
    if status in (401, 403) or "invalid_api_key" in baixo or "api key not valid" in baixo:
        return "chave recusada pelo provedor (confira se a chave está certa e ativa)"
    if status == 402 or "insufficient_quota" in baixo or "credit" in baixo or "billing" in baixo:
        return "sem crédito no provedor (confira o saldo ou o plano da sua conta)"
    if status == 429:
        return "limite de uso atingido no provedor; tente de novo mais tarde"
    if status == 404 or "model_not_found" in baixo or ("model" in baixo and "not found" in baixo):
        return f"o modelo '{modelo}' não existe ou a sua conta não tem acesso a ele"
    if status >= 500:
        return f"o provedor está com problema agora (erro {status}); tente mais tarde"
    return f"o provedor recusou o pedido (erro {status})"


# ---------------------------------------------------------------- adaptadores

def _pedido_anthropic(url, modelo, chave, pedido, sistema=None, max_tokens=MAX_TOKENS_ANTHROPIC):
    corpo = {"model": modelo, "max_tokens": max_tokens, "messages": [{"role": "user", "content": pedido}]}
    if sistema:
        corpo["system"] = sistema
    cabecalhos = {"x-api-key": chave, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    return url.rstrip("/") + "/messages", cabecalhos, corpo


def _pedido_openai(url, modelo, chave, pedido, sistema=None):
    mensagens = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": pedido}]
    cabecalhos = {"Content-Type": "application/json"}
    if chave:
        cabecalhos["Authorization"] = "Bearer " + chave
    return url.rstrip("/") + "/chat/completions", cabecalhos, {"model": modelo, "messages": mensagens}


def _texto(adaptador: str, resposta) -> str:
    partes = []
    if isinstance(resposta, dict) and adaptador == "anthropic":
        partes = [b.get("text", "") for b in resposta.get("content") or []
                  if isinstance(b, dict) and b.get("type") == "text"]
    elif isinstance(resposta, dict):
        escolhas = resposta.get("choices") or []
        mensagem = (escolhas[0] or {}).get("message") or {} if escolhas else {}
        conteudo = mensagem.get("content")
        if isinstance(conteudo, str):
            partes = [conteudo]
        elif isinstance(conteudo, list):
            partes = [c.get("text", "") for c in conteudo if isinstance(c, dict)]
    texto = "".join(p for p in partes if isinstance(p, str)).strip()
    if not texto:
        raise IAErro("resposta vazia do provedor")
    return texto


def _postar(url, cabecalhos, corpo, tempo, modelo=""):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode("utf-8"), method="POST",
                                 headers={**cabecalhos, "User-Agent": "meu-proximo-trampo"})
    try:
        with urllib.request.urlopen(req, timeout=tempo) as r:
            bruto = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise IAErro(motivo_http(e.code, e.read().decode("utf-8", "replace")[:2000], modelo)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if isinstance(e, TimeoutError) or "timed out" in str(e):
            raise IAErro("o provedor demorou demais para responder; tente de novo") from None
        raise IAErro("sem conexão com o provedor (confira a internet e o endereço)") from None
    try:
        return json.loads(bruto)
    except ValueError:
        raise IAErro("resposta inesperada do provedor") from None


def _claude_code(pedido, sistema, modelo, tempo):
    exe = shutil.which("claude")
    if not exe:
        raise IAErro("Claude Code não está instalado neste computador")
    args = [exe, "-p", "--output-format", "json", "--tools", "", "--strict-mcp-config",
            "--disable-slash-commands", "--no-session-persistence"]
    if modelo:
        args += ["--model", modelo]
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    try:
        r = subprocess.run(args, input=(sistema + "\n\n" + pedido) if sistema else pedido, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", cwd=RAIZ, timeout=tempo, **extra)
    except subprocess.TimeoutExpired:
        raise IAErro("o Claude Code demorou demais para responder") from None
    except OSError as e:
        raise IAErro(f"não deu para rodar o Claude Code ({e})") from None
    try:
        saida = json.loads(r.stdout)
    except ValueError:
        raise IAErro(f"o Claude Code não respondeu como esperado (código {r.returncode}): "
                     f"{(r.stderr or r.stdout).strip()[-300:]}") from None
    texto = str(saida.get("result") or "") if isinstance(saida, dict) else ""
    if r.returncode != 0 or (isinstance(saida, dict) and saida.get("is_error")):
        raise IAErro(f"o Claude Code falhou: {(texto or r.stderr).strip()[-300:]}")
    if not texto.strip():
        raise IAErro("resposta vazia do Claude Code")
    return texto


def responder(pedido: str, sistema: str | None = None, tempo: float = 600, escolha: dict | None = None,
              chave: str | None = None) -> str:
    """Texto da resposta da IA escolhida. Levanta IAErro (mensagem legível e mascarada)."""
    escolha = escolha or escolha_efetiva()
    prov = PROVEDORES.get(escolha.get("provedor"))
    if not prov or escolha["provedor"] == "nenhum":
        raise IAErro("a IA está desligada (Sem IA)")
    modelo = modelo_efetivo(escolha)
    try:
        if prov["adaptador"] == "claude_code":
            return _claude_code(pedido, sistema, modelo, tempo)
        chave = chave or segredos.ler(prov["variavel"])
        if not chave and escolha["provedor"] != "compativel":
            raise IAErro(f"falta a chave do provedor {prov['nome']} (cadastre no painel IA)")
        url = escolha.get("url_base") or prov["url"]
        if prov["adaptador"] == "anthropic":
            pedido_http = _pedido_anthropic(url, modelo, chave, pedido, sistema)
        else:
            pedido_http = _pedido_openai(url, modelo, chave, pedido, sistema)
        return _texto(prov["adaptador"], _postar(*pedido_http, tempo=tempo, modelo=modelo))
    except IAErro as erro:
        raise IAErro(mascarar(str(erro), chave or "")) from None


def testar(escolha, chave: str | None = None) -> tuple[bool, str]:
    """Chamada mínima para conferir provedor, modelo e chave. A chave passada não é gravada."""
    try:
        escolha = validar_escolha(escolha)
    except ValueError as erro:
        return False, str(erro)
    if escolha["provedor"] == "nenhum":
        return True, "Sem IA: nada é enviado a provedores."
    tempo = TEMPO_TESTE_CLAUDE if escolha["provedor"] == "claude_code" else TEMPO_TESTE
    try:
        responder(PEDIDO_TESTE, tempo=tempo, escolha=escolha, chave=chave)
    except IAErro as erro:
        return False, str(erro)
    nome = PROVEDORES[escolha["provedor"]]["nome"]
    return True, f"Conexão funcionando ({nome} · {modelo_efetivo(escolha) or 'modelo padrão da conta'})."


# ---------------------------------------------------------------- página

def estado_para_pagina(pode_alterar: bool, ultimo_erro=None) -> dict:
    """O que o painel "IA" mostra. Nunca inclui chave: só se existe, os últimos 4 e a origem."""
    cfg = _ler_config()
    efetiva = escolha_efetiva(cfg)
    gravada = cfg.get("ia") if isinstance(cfg.get("ia"), dict) else None
    provedores = [{"id": pid, "nome": p["nome"], "precisa_chave": bool(p["variavel"]) and pid != "compativel",
                   "aceita_chave": bool(p["variavel"]), "cobranca": p["cobranca"], "modelo_padrao": p["modelo"],
                   "url_padrao": p["url"], "onde_obter_chave": p["chave_em"],
                   "dica": DICA_ANTHROPIC if pid == "anthropic" else ""} for pid, p in PROVEDORES.items()]
    chaves = {pid: {"cadastrada": bool(segredos.ler(p["variavel"])), "final": segredos.final(p["variavel"]),
                    "origem": segredos.origem(p["variavel"])}
              for pid, p in PROVEDORES.items() if p["variavel"]}
    return {"escolha": gravada, "efetiva": efetiva["provedor"], "modelo_efetivo": modelo_efetivo(efetiva),
            "url_efetiva": efetiva.get("url_base", ""), "provedores": provedores, "chaves": chaves,
            "claude_instalado": shutil.which("claude") is not None, "pode_alterar": bool(pode_alterar),
            "disponivel": disponivel(cfg), "ultimo_erro": ultimo_erro}
