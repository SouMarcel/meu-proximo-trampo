"""Contas conectadas (spec 018; constituição, princípio VI, "Conta conectada"): ler o andamento das candidaturas na
área logada de cada portal, na janela do navegador da ferramenta (navegador.py), com o login feito pela pessoa.

Contrato de cada módulo de portal:

  NOME, PLATAFORMA        "gupy" / "Gupy" (PLATAFORMA igual a banco.PLATAFORMAS)
  ATIVO                   só os ativos entram em CONTAS (painel e leitura); os outros ficam prontos no código
  ICONE                   SVG simples e genérico (sem logo da marca)
  URL_CANDIDATURAS        a página de candidaturas (leva ao login se a sessão acabou)
  HOST_LOGIN              trecho do endereço da página de login (para saber se ainda falta logar)
  ORIGENS                 origens do portal (para apagar a sessão dele ao desconectar)
  AVISO_LOGIN             frase curta sobre o login desse portal, para o painel
  ler(aba) -> [lida]      lê as candidaturas; levanta PortalErro(login=True) quando a sessão acabou
  logado(url) -> bool     a aba voltou logada ao portal (o login pode passar por outro site, ex.: LinkedIn)

Regras (constituição VI): só leitura. O código de um portal nunca clica em botões, nunca envia formulários e nunca
pede dados da conta (CPF, celular, perfil): só as rotas de candidaturas. Pede pela API que a própria página usa
(fetch com a sessão dela, de dentro da aba), então os cookies não saem do navegador.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / ".cache" / "contas"
ESTADO = PASTA / "estado.json"
ORDEM = {"salva": 0, "aplicada": 1, "entrevista": 2, "proposta": 3, "encerrada": 4}


class PortalErro(Exception):
    """Não deu para ler o portal; login=True quando a sessão acabou e a pessoa precisa logar na janela."""

    def __init__(self, motivo: str, login: bool = False):
        super().__init__(motivo)
        self.login = login


def lida(portal: str, plataforma: str, **campos) -> dict:
    """Uma candidatura lida de um portal (data-model.md), com os campos que faltarem preenchidos."""
    base = {"portal": portal, "plataforma": plataforma, "id": "", "titulo": "", "empresa": "", "local": "",
            "url": "", "status": "", "etapa": None, "resultado": None, "data": date.today().isoformat(),
            "nota": "", "avisos": [], "ativa": False}
    base.update(campos)
    base["titulo"] = " ".join(str(base["titulo"] or "").split())[:200]
    base["empresa"] = " ".join(str(base["empresa"] or "").split())[:120]
    base["local"] = " ".join(str(base["local"] or "").split())[:120]
    return base


def avancou(de: str | None, para: str | None) -> bool:
    """`para` está à frente de `de` no quadro (encerrada é final; sem etapa conta como antes de tudo)."""
    if not para or de == "encerrada":
        return False
    return ORDEM.get(para, -1) > ORDEM.get(de, -1) if de else True


JS_JSON = """(async () => {
  try {
    const r = await fetch(%s, {credentials: "include", headers: {"accept": "application/json"}});
    let d = null;
    try { d = await r.json(); } catch (e) {}
    return {status: r.status, dados: d, url: location.href};
  } catch (e) { return {status: 0, dados: null, url: location.href}; }
})()"""


def buscar_json(aba, url: str) -> tuple[int, object]:
    """(status HTTP, JSON) de um GET feito de dentro da página, com a sessão dela. Só leitura."""
    r = aba.avaliar(JS_JSON % json.dumps(url)) or {}
    return int(r.get("status") or 0), r.get("dados")


# ---------------------------------------------------------------- estado local (fora do Git)

def _ler_estado() -> dict:
    try:
        d = json.loads(ESTADO.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def conectados() -> list[str]:
    """Portais que a pessoa conectou (e que seguem ativos)."""
    return [p for p in _ler_estado().get("conectados", []) if p in CONTAS]


def marcar(portal: str, ligado: bool) -> None:
    d = _ler_estado()
    lista = [p for p in d.get("conectados", []) if p != portal] + ([portal] if ligado else [])
    d["conectados"] = lista
    PASTA.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


from . import gupy, indeed, linkedin  # noqa: E402  (os módulos usam as funções acima)

TODAS = {m.NOME: m for m in (gupy, indeed, linkedin)}
CONTAS = {n: m for n, m in TODAS.items() if m.ATIVO}
