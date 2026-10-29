"""Preencher esta página (spec 027, decisão de 2026-10-24): a ferramenta preenche o que sabe e pergunta o resto.

  preencher_pagina(aba, vaga)      lê a página; preenche os campos de contato com os dados que a pessoa salvou (spec
                                   033, sem IA), depois com as respostas que ela já deu (memória) e, nos campos comuns,
                                   com as propostas da IA tiradas do perfil; devolve o que preencheu (com a fonte), as
                                   perguntas que precisam da pessoa e o que fica com ela na janela
  responder(aba, vaga, ...)        preenche as respostas que a pessoa deu no painel e as guarda na memória (se ela quiser);
                                   na pergunta comum de texto, a resposta é um relato: a IA o transforma na resposta e
                                   ele fica guardado no que a ferramenta sabe da pessoa (spec 035)

Nunca clica nem envia: quem confere na janela e clica em Continuar ou Enviar é a pessoa. Pergunta sensível e dado
cadastral só recebem a resposta da própria pessoa, literal (dada agora ou guardada); a pretensão salarial e a relocação
ela responde a cada vaga.
"""
from __future__ import annotations

from . import contato, exigir_ligada, memoria
from .formulario import _tem_valor, ler, preencher

NA_JANELA = {"consentimento", "arquivo", "senha", "outro"}
FONTE_RELATO, FONTE_RELATO_LITERAL, FONTE_PESSOA = "seu relato (adaptado pela IA)", "seu relato", "sua resposta"


def aceita_relato(c: dict) -> bool:
    """Pergunta comum de texto: a resposta da pessoa é um relato que a IA transforma na resposta (spec 035)."""
    import candidatura_ia
    return (c.get("marca") == "comum" and c.get("tipo") in ("texto", "area") and c.get("tipo_html") != "number"
            and not candidatura_ia.sensivel(c.get("rotulo") or ""))


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
        relato = aceita_relato(c)
        motivo = motivo_falha.get(c["chave"]) or {
            "sensivel": c["motivo"].replace("responda você na página", "pergunta sensível: só você responde, e vai como você "
                                                                       "escrever"),
            "cadastro": "dado seu que a ferramenta ainda não tem: vai como você escrever",
        }.get(c["marca"], "a ferramenta não sabe isso de você: conte com suas palavras, e ela transforma o relato na "
                          "resposta" if relato else "o seu perfil não responde")
        saida["perguntas"].append({**c, "proposta": "", "motivo": motivo, "relato": relato,
                                   "lembrar": memoria._categoria(c) not in memoria.NAO_LEMBRAR})
    saida["preenchidos"] = [{k: p[k] for k in ("chave", "rotulo", "texto", "fonte", "conferir")} for p in preenchidos]
    return saida


def responder(aba, vaga: dict, assinatura: str, respostas: list, lembrar: bool = True, guardar_relatos: bool = True,
              adaptar=None) -> dict:
    """As respostas que a pessoa deu no painel. Na pergunta comum de texto, a resposta é um relato: a IA o transforma na
    resposta (adaptar = candidatura_ia.adaptar_relatos) e o relato fica guardado (relatos.py), se ela quiser. Pergunta
    sensível e dado cadastral vão literais. Guarda na memória, se ela quiser, salvo a pretensão salarial e a relocação."""
    exigir_ligada(vaga)
    lista = respostas if isinstance(respostas, list) else []  # o que não é lista o preencher recusa com o motivo
    pagina = ler(aba)
    # página mudou ou fora dos domínios liberados: nada vai à IA, e o preencher abaixo explica o motivo
    ok = pagina["assinatura"] == assinatura and pagina["dominio"]["permitido"]
    campos = {c["chave"]: c for c in pagina["campos"]} if ok else {}
    relatos_da_pagina = {r["chave"]: str(r.get("valor") or "") for r in lista
                         if isinstance(r, dict) and r.get("chave") in campos and aceita_relato(campos[r["chave"]])
                         and str(r.get("valor") or "").strip()}
    adaptado = {"respostas": {}, "pela_ia": set(), "aviso": None, "ia": None}
    if relatos_da_pagina:
        if adaptar is None:
            import candidatura_ia
            adaptar = candidatura_ia.adaptar_relatos
        adaptado = adaptar(vaga, [(campos[k], v) for k, v in relatos_da_pagina.items()])
    finais = [{**x, "valor": adaptado["respostas"].get(x.get("chave"), x.get("valor"))} if isinstance(x, dict) else x
              for x in lista] if isinstance(respostas, list) else respostas
    r = preencher(aba, assinatura, finais, vaga, da_pessoa=True)
    guardadas = relatados = 0
    for p in r["preenchidos"]:
        if p["chave"] in relatos_da_pagina:
            p["fonte"] = FONTE_RELATO if p["chave"] in adaptado["pela_ia"] else FONTE_RELATO_LITERAL
            if guardar_relatos:
                import relatos
                relatados += bool(relatos.adicionar(p["rotulo"], relatos_da_pagina[p["chave"]], p["texto"], vaga))
        else:
            p["fonte"] = FONTE_PESSOA
        if lembrar:
            guardadas += memoria.lembrar({"rotulo": p["rotulo"], "nome": p.get("nome", ""), "tipo": p.get("tipo")}, p["texto"])
    r.update(lembradas=guardadas, relatos=relatados, aviso_ia=adaptado.get("aviso"), ia=adaptado.get("ia"))
    r["preenchidos"] = [{k: p[k] for k in ("chave", "rotulo", "valor", "texto", "fonte")} for p in r["preenchidos"]]
    return r
