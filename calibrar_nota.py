#!/usr/bin/env python3
"""Comando de desenvolvimento para calibração da nota de aderência (spec 062).

Refaz a nota de uma amostra de vagas já analisadas e compara, sem gravar nada no banco. Com `--antes REF`, cada lote
vai à mesma IA com as regras da versão REF do Git (ex.: origin/master) e com as atuais, e a comparação é entre as duas
respostas: só as regras mudam. Sem `--antes`, a comparação é com a nota gravada, que só vale quando a IA de hoje é a
mesma que deu as notas (o comando avisa quando não é).

Uso:
  python calibrar_nota.py --medir [ID]            tamanho do pedido de 1 vaga, por parte; sem IA
  python calibrar_nota.py --antes origin/master   regras antigas x atuais, na mesma IA (o dobro de pedidos)
  python calibrar_nota.py [--amostra 30] [--semente N]
  python calibrar_nota.py --ids ID1,ID2,...       as mesmas vagas de uma calibração anterior
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import tempfile
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent
for _p in (str(RAIZ), str(RAIZ / "dash")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CACHE = RAIZ / ".cache"

import analise  # noqa: E402
import banco  # noqa: E402
import ia  # noqa: E402


def partes_do_pedido(pedido: str) -> dict[str, int]:
    """Divide o pedido de nota em caracteres por partes: regras, perfil, filtros e vaga."""
    t_perfil = "## Perfil do usuário"
    t_filtros = "## Filtros da busca do usuário"
    t_vagas = "## Vagas"

    i_perfil = pedido.find(t_perfil)
    i_filtros = pedido.find(t_filtros, i_perfil if i_perfil >= 0 else 0)
    i_vagas = pedido.find(t_vagas, i_filtros if i_filtros >= 0 else 0)

    if i_perfil >= 0 and i_filtros >= i_perfil and i_vagas >= i_filtros:
        regras = pedido[:i_perfil]
        perfil = pedido[i_perfil:i_filtros]
        filtros = pedido[i_filtros:i_vagas]
        vaga = pedido[i_vagas:]
    else:
        regras = pedido[:i_perfil] if i_perfil >= 0 else ""
        perfil = pedido[i_perfil:i_filtros] if i_perfil >= 0 and i_filtros >= 0 else ""
        filtros = pedido[i_filtros:i_vagas] if i_filtros >= 0 and i_vagas >= 0 else ""
        vaga = pedido[i_vagas:] if i_vagas >= 0 else ""

    return {
        "total": len(pedido),
        "regras": len(regras),
        "perfil": len(perfil),
        "filtros": len(filtros),
        "vaga": len(vaga),
    }


def escolher_amostra(
    vagas: list[dict],
    n: int = 30,
    modelo: str | None = None,
    semente: int = 0,
    area: Any = lambda v: "nacional",
) -> list[dict]:
    """Seleciona uma amostra representativa de vagas já analisadas para calibração."""
    if n <= 0:
        return []

    def elegivel(v: dict) -> bool:
        if v.get("analise_status") != "feita":
            return False
        nota = v.get("aderencia")
        if not isinstance(nota, (int, float)) or isinstance(nota, bool):
            return False
        desc = v.get("descricao")
        if not desc or not str(desc).strip():
            return False
        if v.get("nota_sem_descricao"):
            return False
        return True

    def faixa(nota: float) -> int:
        if nota >= 80:
            return 0
        if nota >= 65:
            return 1
        if nota >= 50:
            return 2
        return 3

    def area_cat(v: dict) -> str:
        try:
            a = area(v)
        except Exception:
            a = "nacional"
        return "internacional" if str(a or "").startswith("internacional") else "nacional"

    chaves_grupos = [(f, a) for f in (0, 1, 2, 3) for a in ("nacional", "internacional")]
    baldes: dict[tuple[int, str], list[dict]] = {k: [] for k in chaves_grupos}

    for v in vagas:
        if elegivel(v):
            nota = float(v["aderencia"])
            k = (faixa(nota), area_cat(v))
            baldes[k].append(v)

    rng = random.Random(semente)
    for k in chaves_grupos:
        itens = baldes[k]
        rng.shuffle(itens)
        if modelo:
            itens.sort(key=lambda v: 0 if v.get("analise_modelo") == modelo else 1)

    resultado: list[dict] = []
    vistos: set[Any] = set()
    while len(resultado) < n:
        pegou = False
        for k in chaves_grupos:
            while baldes[k]:
                v = baldes[k].pop(0)
                vid = v.get("id")
                if vid not in vistos:
                    vistos.add(vid)
                    resultado.append(v)
                    pegou = True
                    break
            if len(resultado) >= n:
                break
        if not pegou:
            break

    return resultado


def comparar(vaga: dict, resposta: dict | None, erro: str | None = None) -> dict:
    """Compara os dados antes e depois da calibração de uma vaga."""
    nota_antes = vaga.get("aderencia")
    nota_depois = None
    if resposta and "aderencia" in resposta:
        val = resposta["aderencia"]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            nota_depois = val

    diferenca = None
    if nota_depois is not None and isinstance(nota_antes, (int, float)) and not isinstance(nota_antes, bool):
        diferenca = nota_depois - nota_antes

    fora_antes = bool(vaga.get("fora_dos_criterios"))
    fora_depois = bool(resposta.get("fora_dos_criterios")) if resposta else False

    motivo_erro = erro if erro is not None else (resposta.get("erro") if resposta else None)

    return {
        "id": vaga["id"],
        "nota_antes": nota_antes,
        "nota_depois": nota_depois,
        "diferenca": diferenca,
        "fora_antes": fora_antes,
        "fora_depois": fora_depois,
        "modelo_antes": vaga.get("analise_modelo"),
        "erro": motivo_erro,
    }


def resumir(linhas: list[dict]) -> dict:
    """Gera o resumo das comparações de calibração."""
    respondidas = sum(1 for l in linhas if l.get("nota_depois") is not None)
    if respondidas > 0:
        dentro_count = sum(
            1 for l in linhas
            if l.get("nota_depois") is not None and l.get("diferenca") is not None and abs(l["diferenca"]) <= 10
        )
        dentro_de_10 = round(dentro_count / respondidas, 4)
        trocas_fora = sum(
            1 for l in linhas
            if l.get("nota_depois") is not None and l.get("fora_antes") != l.get("fora_depois")
        )
        passa = bool(dentro_de_10 >= 0.9 and trocas_fora == 0)
    else:
        dentro_de_10 = 0.0
        trocas_fora = 0
        passa = False

    return {
        "respondidas": respondidas,
        "dentro_de_10": dentro_de_10,
        "trocas_fora": trocas_fora,
        "passa": passa,
    }


def _git_show(ref_caminho: str) -> str | None:
    r = subprocess.run(["git", "show", ref_caminho], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def montador_antigo(ref: str):
    """O montar_pedido da versão `ref` do Git, com as regras daquela versão (a skill e, se já existia, o
    regras-da-nota.md). None se a versão não tem o dash/analise.py."""
    codigo = _git_show(f"{ref}:dash/analise.py")
    if codigo is None:
        return None
    pasta = Path(tempfile.mkdtemp(prefix="calibrar-"))
    for nome in ("SKILL.md", "regras-da-nota.md"):
        texto = _git_show(f"{ref}:.agents/skills/buscar-vagas/{nome}")
        if texto is not None:
            (pasta / nome).write_text(texto, encoding="utf-8")
    modulo = types.ModuleType("analise_antes")
    modulo.__file__ = str(RAIZ / "dash" / "analise.py")
    exec(compile(codigo, f"{ref}:dash/analise.py", "exec"), modulo.__dict__)
    modulo.SKILL = pasta / "SKILL.md"
    if hasattr(modulo, "REGRAS"):
        modulo.REGRAS = pasta / "regras-da-nota.md"
    return modulo.montar_pedido


def base_antes(vaga: dict, resposta: dict, ref: str) -> dict:
    """A vaga com a nota e o fora dos critérios da resposta às regras antigas, para comparar com as atuais."""
    return {**vaga, "aderencia": resposta.get("aderencia"), "fora_dos_criterios": resposta.get("fora_dos_criterios"),
            "analise_modelo": f"regras de {ref}"}


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):  # o console do Windows não é UTF-8 por padrão (setas, acentos)
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    parser = argparse.ArgumentParser(description="Calibração da nota de aderência")
    parser.add_argument("--antes", default=None, help="versão do Git com as regras antigas (ex.: origin/master)")
    parser.add_argument("--medir", nargs="?", const="", default=None, help="tamanho do pedido de 1 vaga, por parte; sem IA")
    parser.add_argument("--amostra", type=int, default=30, help="tamanho da amostra (padrão 30)")
    parser.add_argument("--semente", type=int, default=0, help="semente aleatória (padrão 0)")
    parser.add_argument("--ids", type=str, default=None, help="lista de IDs separados por vírgula")

    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    if args.medir is not None:
        vid = args.medir.strip()
        if vid:
            vaga = banco.obter(vid)
            if not vaga:
                print(f"Vaga {vid} não encontrada no banco.", file=sys.stderr)
                return 2
        else:
            todas = banco.listar_vagas()
            com_desc = [v for v in todas if v.get("descricao") and str(v["descricao"]).strip()]
            if not com_desc:
                print("Nenhuma vaga com descrição encontrada no banco.", file=sys.stderr)
                return 2
            com_desc.sort(key=lambda v: str(v.get("encontrada_em") or ""), reverse=True)
            recentes = com_desc[:20]
            vaga = max(recentes, key=lambda v: len(str(v.get("descricao") or "")))

        pedido = analise.montar_pedido([vaga])
        CACHE.mkdir(parents=True, exist_ok=True)
        caminho_pedido = CACHE / f"pedido-{vaga['id']}.txt"
        caminho_pedido.write_text(pedido, encoding="utf-8")

        partes = partes_do_pedido(pedido)
        print(f"Pedido de 1 vaga ({vaga['id']}):")
        print(f"  Total:    {partes['total']} caracteres")
        print(f"  Regras:   {partes['regras']} caracteres")
        print(f"  Perfil:   {partes['perfil']} caracteres")
        print(f"  Filtros:  {partes['filtros']} caracteres")
        print(f"  Vaga:     {partes['vaga']} caracteres")

        passa = partes["total"] <= 20000
        print(f"SC-001: {'PASSA' if passa else 'NÃO PASSA'}")
        return 0 if passa else 1

    if not ia.disponivel():
        print("Sem IA disponível para calibração.", file=sys.stderr)
        return 2

    seq = ia.sequencia()
    ia_principal = seq[0] if seq else {}
    modelo_principal = ia.modelo_efetivo(ia_principal) if ia_principal else None
    provedor_principal = ia_principal.get("provedor", "")

    f = analise._filtros()
    cfg = f.ler_config()
    efet = f.efetivos(cfg)
    area_func = lambda v: analise._area(f, v, efet)

    if args.ids:
        candidatos_ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        amostra = []
        for vid in candidatos_ids:
            v = banco.obter(vid)
            if v:
                amostra.append(v)
    else:
        todas = banco.listar_vagas()
        amostra = escolher_amostra(
            todas,
            n=args.amostra,
            modelo=modelo_principal,
            semente=args.semente,
            area=area_func,
        )

    if len(amostra) < 1:
        print("Nenhuma vaga para a amostra.", file=sys.stderr)
        return 2

    montar_antigo = None
    if args.antes:
        montar_antigo = montador_antigo(args.antes)
        if montar_antigo is None:
            print(f"Não achei dash/analise.py na versão {args.antes} do Git.", file=sys.stderr)
            return 2
        print(f"Comparando as regras de {args.antes} com as atuais, na mesma IA ({len(amostra)} vagas).")
    else:
        outras = sum(1 for v in amostra if v.get("analise_modelo") != modelo_principal)
        if outras:
            print(f"Aviso: {outras} de {len(amostra)} notas gravadas vieram de outra IA; a diferença mistura a troca "
                  "de IA com a das regras. Para medir só as regras: --antes origin/master.")

    lotes_vagas = analise.lotes(amostra, 3)
    recusas = 0
    parar_tudo = False
    ultimo_erro = None
    resultados_por_id = {}
    primeiro_pedido = True

    for lote in lotes_vagas:
        if parar_tudo:
            break
        tentativa_mesmo_lote = False
        while True:
            if not primeiro_pedido and not tentativa_mesmo_lote:
                time.sleep(analise.pausa_lote())
            primeiro_pedido = False
            tentativa_mesmo_lote = False
            try:
                antes = {}
                if montar_antigo is not None:
                    texto_antes = ia.responder(montar_antigo(lote), tempo=analise.TEMPO_MAXIMO)
                    antes = {str(x.get("id")): x for x in analise.lista_json(texto_antes) or []
                             if isinstance(x, dict)}
                pedido = analise.montar_pedido(lote)
                texto = ia.responder(pedido, tempo=analise.TEMPO_MAXIMO)
                recusas = 0
                lista = analise.lista_json(texto)
                if montar_antigo is not None:  # a base da comparação é a resposta às regras antigas
                    sem_antes = [v for v in lote if str(v["id"]) not in antes]
                    for v in sem_antes:
                        resultados_por_id[v["id"]] = comparar(v, None, erro="a IA não devolveu esta vaga (regras "
                                                                            "antigas)")
                    lote = [base_antes(v, antes[str(v["id"])], args.antes) for v in lote if v not in sem_antes]
                if lista is None:
                    for v in lote:
                        resultados_por_id[v["id"]] = comparar(
                            v, None, erro="a resposta da IA não trouxe o JSON das análises"
                        )
                else:
                    resp_map = {
                        str(item.get("id")): item
                        for item in lista
                        if isinstance(item, dict) and "id" in item
                    }
                    for v in lote:
                        vid = str(v["id"])
                        if vid in resp_map:
                            resultados_por_id[vid] = comparar(v, resp_map[vid])
                        else:
                            resultados_por_id[vid] = comparar(
                                v, None, erro="a IA não devolveu esta vaga"
                            )
                break
            except ia.IAErro as e:
                if e.limite:
                    recusas += 1
                    ultimo_erro = str(e) or "limite de pedidos da IA"
                    if recusas >= 3:
                        for v in lote:
                            resultados_por_id[v["id"]] = comparar(v, None, erro=ultimo_erro)
                        parar_tudo = True
                        break
                    else:
                        espera = min(e.espera or 60, 300)
                        time.sleep(espera)
                        tentativa_mesmo_lote = True
                        continue
                else:
                    ultimo_erro = str(e)
                    for v in lote:
                        resultados_por_id[v["id"]] = comparar(v, None, erro=ultimo_erro)
                    break

    if parar_tudo:
        for v in amostra:
            if v["id"] not in resultados_por_id:
                resultados_por_id[v["id"]] = comparar(v, None, erro=ultimo_erro)

    linhas = [resultados_por_id[v["id"]] for v in amostra]

    for linha in linhas:
        if linha.get("erro"):
            print(f"  {linha['id']}: erro: {linha['erro']}")
        else:
            dif = linha["diferenca"]
            dif_str = f"+{dif}" if dif is not None and dif > 0 else str(dif)
            fora_str = ""
            if linha["fora_antes"] != linha["fora_depois"]:
                de = "fora" if linha["fora_antes"] else "dentro"
                para = "fora" if linha["fora_depois"] else "dentro"
                fora_str = f" [critérios: {de} → {para}]"
            elif linha["fora_antes"]:
                fora_str = " [fora dos critérios]"
            modelo_str = f" ({linha['modelo_antes'] or 'sem modelo'})"
            print(f"  {linha['id']}: {linha['nota_antes']} → {linha['nota_depois']} ({dif_str}){fora_str}{modelo_str}")

    resumo = resumir(linhas)
    trocas = [
        l for l in linhas
        if l.get("nota_depois") is not None and l.get("fora_antes") != l.get("fora_depois")
    ]
    if trocas:
        print("\nTrocas de fora dos critérios:")
        for t in trocas:
            de = "fora" if t["fora_antes"] else "dentro"
            para = "fora" if t["fora_depois"] else "dentro"
            print(f"  {t['id']}: {de} → {para}")

    pct = resumo["dentro_de_10"] * 100
    print(
        f"\nResumo: {resumo['respondidas']}/{len(linhas)} respondidas, "
        f"{pct:.1f}% dentro de 10 pts, {resumo['trocas_fora']} trocas fora/dentro"
    )
    print(f"SC-002: {'PASSA' if resumo['passa'] else 'NÃO PASSA'}")

    CACHE.mkdir(parents=True, exist_ok=True)
    agora = datetime.now()
    pedido_1 = analise.montar_pedido([amostra[0]])
    partes_1 = partes_do_pedido(pedido_1)
    relatorio = {
        "em": agora.isoformat(timespec="seconds"),
        "ia": {"provedor": provedor_principal, "modelo": modelo_principal or ""},
        "pedido_1_vaga": partes_1,
        "vagas": linhas,
        "resumo": resumo,
    }
    nome_arquivo = f"calibracao-{agora.strftime('%Y%m%d-%H%M')}.json"
    (CACHE / nome_arquivo).write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return 0 if resumo["passa"] else 1


if __name__ == "__main__":
    sys.exit(main())
