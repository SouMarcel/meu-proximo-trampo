"""Preencher esta página (spec 027, decisão de 2026-10-24): a ferramenta preenche o que sabe e pergunta o resto.

  preencher_pagina(aba, vaga)      lê a página; preenche os campos de contato com os dados que a pessoa salvou (spec
                                   033, sem IA), depois com as respostas que ela já deu (memória) e, nos campos comuns,
                                   com as propostas da IA tiradas do perfil; devolve o que preencheu (com a fonte), as
                                   perguntas que precisam da pessoa e o que fica com ela na janela
  responder(aba, vaga, ...)        preenche as respostas que a pessoa deu no painel e as guarda na memória (se ela quiser)

Nunca clica nem envia: quem confere na janela e clica em Continuar ou Enviar é a pessoa. Pergunta sensível só recebe
resposta da própria pessoa (dada agora ou guardada); salário e relocação ela responde a cada vaga.
"""
from __future__ import annotations

from . import contato, exigir_ligada, memoria
from .formulario import _tem_valor, ler, preencher

NA_JANELA = {"consentimento", "arquivo", "senha", "outro"}


def _vazio(pagina: dict) -> dict:
    return {"pagina": {k: pagina[k] for k in ("url", "dominio", "etapa", "aviso", "assinatura")},
            "preenchidos": [], "perguntas": [], "na_janela": [], "aviso_ia": None, "ia": None,
            "aviso": "Confira na janela e clique você em Continuar ou Enviar."}


def preencher_pagina(aba, vaga: dict, propor=None) -> dict:
    """propor(vaga, campos) -> {"itens": [campo + proposta, conferir], "aviso", "ia"} (candidatura_ia.propor_respostas)."""
    exigir_ligada(vaga)
    pagina = ler(aba)
    saida = _vazio(pagina)
    if pagina["etapa"] != "perguntas" or not pagina["dominio"]["permitido"]:
        return saida
    dados_contato = contato.ler()
    do_contato, da_memoria, abertos = [], [], []
    for c in pagina["campos"]:
        if c["marca"] in NA_JANELA:
            saida["na_janela"].append({"chave": c["chave"], "rotulo": c["rotulo"], "motivo": c["motivo"]})
            continue
        if _tem_valor(c):
            continue  # já preenchido na página (ex.: dados da conta do portal)
        if c["marca"] in ("cadastro", "comum"):
            v_contato = contato.valor_para(c, dados_contato) if dados_contato else None
            if v_contato:
                do_contato.append({"chave": c["chave"], "valor": v_contato})
                continue
        valor = memoria.valor_para(c)
        if valor:
            da_memoria.append({"chave": c["chave"], "valor": valor})
        elif c["marca"] == "comum":
            abertos.append(c)

    preenchidos, falhas = [], []
    if do_contato:  # os dados de contato que a pessoa salvou: sem IA (spec 033)
        r = preencher(aba, pagina["assinatura"], do_contato, vaga, da_pessoa=True)
        preenchidos += [{**p, "fonte": contato.FONTE, "conferir": []} for p in r["preenchidos"]]
        falhas += [f for f in r["ficaram"] if f["chave"] in {x["chave"] for x in do_contato}]
    if da_memoria:
        r = preencher(aba, pagina["assinatura"], da_memoria, vaga, da_pessoa=True)
        preenchidos += [{**p, "fonte": "sua resposta anterior", "conferir": []} for p in r["preenchidos"]]
        falhas += [f for f in r["ficaram"] if f["chave"] in {x["chave"] for x in da_memoria}]

    propostas = {}
    if abertos:
        if propor is None:
            import candidatura_ia
            propor = candidatura_ia.propor_respostas
        resultado = propor(vaga, abertos)
        saida["aviso_ia"], saida["ia"] = resultado.get("aviso"), resultado.get("ia")
        propostas = {i["chave"]: i for i in resultado.get("itens") or [] if i.get("proposta")}
    if propostas:
        r = preencher(aba, pagina["assinatura"], [{"chave": k, "valor": i["proposta"]} for k, i in propostas.items()], vaga)
        preenchidos += [{**p, "fonte": "seu perfil", "conferir": propostas[p["chave"]].get("conferir") or []} for p in r["preenchidos"]]
        falhas += [f for f in r["ficaram"] if f["chave"] in propostas]

    feitos = {p["chave"] for p in preenchidos}
    motivo_falha = {f["chave"]: f["motivo"] for f in falhas}
    for c in pagina["campos"]:
        if c["chave"] in feitos or c["marca"] in NA_JANELA or _tem_valor(c):
            continue
        motivo = motivo_falha.get(c["chave"]) or {
            "sensivel": c["motivo"].replace("responda você na página", "pergunta sensível: só você responde"),
            "cadastro": "dado seu que não está no perfil",
        }.get(c["marca"], "o seu perfil não responde")
        saida["perguntas"].append({**c, "proposta": "", "motivo": motivo,
                                   "lembrar": memoria._categoria(c) not in memoria.NAO_LEMBRAR})
    saida["preenchidos"] = [{k: p[k] for k in ("chave", "rotulo", "texto", "fonte", "conferir")} for p in preenchidos]
    return saida


def responder(aba, vaga: dict, assinatura: str, respostas: list, lembrar: bool = True) -> dict:
    """As respostas que a pessoa deu no painel: preenche (inclusive pergunta sensível e dado cadastral) e guarda na
    memória, se ela quiser, salvo salário e relocação."""
    r = preencher(aba, assinatura, respostas, vaga, da_pessoa=True)
    guardadas = 0
    if lembrar:
        for p in r["preenchidos"]:
            guardadas += memoria.lembrar({"rotulo": p["rotulo"], "nome": p.get("nome", ""), "tipo": p.get("tipo")}, p["texto"])
    r["lembradas"] = guardadas
    r["preenchidos"] = [{k: p[k] for k in ("chave", "rotulo", "valor", "texto")} for p in r["preenchidos"]]
    return r
