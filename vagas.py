#!/usr/bin/env python3
"""meu-proximo-trampo: busca vagas e manda para o dashboard local.

  python vagas.py buscar --gravar   busca e grava tudo no dashboard, sem nota (uso sem IA)
  python vagas.py buscar            busca e deixa as candidatas em .cache/ para avaliação
  python vagas.py ver ID [ID…]      descrição completa de candidatas
  python vagas.py gravar            grava as candidatas avaliadas (.cache/avaliacoes.json)
  python vagas.py gravar --sem-avaliacao   grava as candidatas da última busca sem nota

Configuração em config.json (copie de config.exemplo.json). Dashboard: python dash/servidor.py
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CACHE = RAIZ / ".cache"
URL_DASHBOARD = "http://127.0.0.1:8765/"

sys.path.insert(0, str(RAIZ / "dash"))
import banco  # noqa: E402  (dash/banco.py)
import filtros  # noqa: E402
from fontes import FONTES  # noqa: E402


def carregar_config() -> dict:
    if not filtros.CONFIG.exists():
        sys.exit("Falta o config.json. Copie config.exemplo.json para config.json (ou use o painel Filtros da busca "
                 "do dashboard) e ajuste os cargos.")
    return filtros.ler_config()


def normalizar(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt.lower()).strip()


def bate_algum(titulo_norm: str, termos: list[str]) -> str | None:
    """Devolve o primeiro termo que aparece como palavra inteira no título."""
    for termo in termos:
        t = normalizar(termo).strip('"')
        if t and re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", titulo_norm):
            return termo
    return None


# ---------------------------------------------------------------- buscar

def rotulo_grupo(grupo: str, f: dict) -> str:
    if grupo.startswith("internacional:"):
        return grupo.split(":", 1)[1]
    return {"remoto": "remoto", "pais": "país todo", "local": filtros.cidade_rotulo(f)}.get(grupo, grupo)


def cmd_buscar(args) -> int:
    cfg = carregar_config()
    f = filtros.efetivos(cfg)
    if args.termos:
        f["termos"] = args.termos
    if args.janela_horas:
        f["janela_horas"] = args.janela_horas
    if args.local:
        f["local_legado"] = args.local
    if not f["termos"]:
        print("Nenhum cargo para buscar: informe os termos no painel Filtros da busca ou no config.json.", file=sys.stderr)
        return 2
    termos = f["termos"]
    horas = f["janela_horas"]
    por_termo = args.resultados or cfg.get("resultados_por_termo", 40)
    plano = filtros.consultas(f, incluir_presencial=args.incluir_presencial)
    nomes_fontes = args.fontes or cfg.get("fontes", ["indeed", "gupy"])
    desconhecidas = [n for n in nomes_fontes if n not in FONTES]
    if desconhecidas:
        print(f"Fonte(s) desconhecida(s): {', '.join(desconhecidas)}. Disponíveis: {', '.join(FONTES)}", file=sys.stderr)
        return 2

    brutas: dict[str, dict] = {}
    por_busca: dict[str, int] = {}
    erros: list[str] = []
    primeira = True
    for nome in nomes_fontes:
        fonte = FONTES[nome]
        for c in plano:
            if not primeira:
                time.sleep(args.pausa)
            primeira = False
            try:
                vagas, errs = fonte.buscar(c, horas, por_termo)
            except ImportError as e:
                print(f"ERRO: dependência ausente ({e}). Rode: pip install -r requirements.txt", file=sys.stderr)
                return 2
            rotulo = f"{nome}: {c['termo']}" + ("" if c["grupo"] == "remoto" else f" [{rotulo_grupo(c['grupo'], f)}]")
            erros += [f"{rotulo}: {m}" for m in errs]
            por_busca[rotulo] = len(vagas)
            for v in vagas:
                atual = brutas.setdefault(v["id"], {**v, "termos": [], "grupos": []})
                if c["termo"] not in atual["termos"]:
                    atual["termos"].append(c["termo"])
                if c["grupo"] not in atual["grupos"]:
                    atual["grupos"].append(c["grupo"])

    excluir = cfg.get("titulo_excluir", [])
    incluir = cfg.get("titulo_incluir", [])
    vistas = banco.IndiceVistas()  # pelos ids e links, e por cargo + empresa (a mesma vaga em outro portal tem outro id)
    # o filtro de data dos portais às vezes deixa passar republicações antigas
    limite_data = (date.today() - timedelta(days=math.ceil(horas / 24) + 1)).isoformat()
    grupos: dict[tuple[str, str], dict] = {}
    excluidas: list[str] = []
    antigas = 0
    for v in brutas.values():
        if v.get("publicada_em") and v["publicada_em"] < limite_data:
            antigas += 1
            continue
        tn = normalizar(v["titulo"])
        motivo = bate_algum(tn, excluir)
        if not motivo and incluir and not bate_algum(tn, incluir):
            motivo = "fora de titulo_incluir"
        if motivo:
            excluidas.append(f'{v["titulo"]} | {v["empresa"]}  ("{motivo}")')
            continue
        chave = (tn, normalizar(v["empresa"]))  # mesmo anúncio publicado várias vezes
        if chave in grupos:
            g = grupos[chave]
            g["ids_relacionados"].append(v["id"])
            g["termos"] += [t for t in v["termos"] if t not in g["termos"]]
            g["grupos"] += [x for x in v["grupos"] if x not in g["grupos"]]
            if v["plataforma"] != g["plataforma"] and v["plataforma"] not in g["outras_plataformas"]:
                g["outras_plataformas"].append(v["plataforma"])  # o mesmo anúncio em outro portal
            continue
        v["ids_relacionados"] = []
        v["outras_plataformas"] = []
        grupos[chave] = v

    candidatas, fora, ja_vistas = [], [], 0
    outros_portais: dict[str, dict] = {}  # vaga já no dashboard -> plataformas e ids com que ela apareceu agora
    for v in grupos.values():
        existente = vistas.achar(v)
        if existente:
            ja_vistas += 1
            reg = outros_portais.setdefault(existente, {"plataformas": [], "ids": []})
            reg["plataformas"] += [p for p in [v["plataforma"], *v["outras_plataformas"]] if p not in reg["plataformas"]]
            reg["ids"] += [i for i in [v["id"], *v["ids_relacionados"]] if i not in reg["ids"]]
            continue
        motivos = filtros.criterios(v, f)  # antes da IA: empresa excluída e senioridade do título
        if motivos:
            v["motivo_fora"] = motivos
            fora.append(v)
        else:
            candidatas.append(v)
    candidatas.sort(key=lambda r: r.get("publicada_em") or "", reverse=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    resultado = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "parametros": {"fontes": nomes_fontes, "termos": termos, "janela_horas": horas, "consultas": len(plano),
                       "resumo": filtros.resumo(f), "filtros": f, "resultados_por_termo": por_termo},
        "por_busca": por_busca,
        "brutas": len(brutas),
        "fora_da_janela": antigas,
        "excluidas_titulo": len(excluidas),
        "ja_vistas": ja_vistas,
        "outros_portais": outros_portais,
        "erros": erros,
        "candidatas": candidatas,
        "fora": fora,
    }
    (CACHE / "candidatas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_digest(resultado, args.trecho)

    print(f"Consultas: {len(plano)} ({filtros.resumo(f)})")
    print(f"Vagas encontradas: {len(brutas)}  ({', '.join(f'{k}: {n}' for k, n in por_busca.items())})")
    print(f"Publicadas antes da janela (descartadas): {antigas}")
    print(f"Cortadas pelo título: {len(excluidas)}")
    print(f"Já vistas (já estão no dashboard): {ja_vistas}")
    print(f"Fora dos critérios (vão para a aba Fora dos critérios, sem avaliação): {len(fora)}")
    for v in fora:
        print(f"  - {v['titulo'][:55]} | {v['empresa'][:28]}: {'; '.join(v['motivo_fora'])}")
    print(f"CANDIDATAS: {len(candidatas)}")
    if erros:
        print("\nErros reportados pelos portais:")
        for e in erros[:10]:
            print(f"  - {e}")
    if excluidas:
        print("\nCortadas pelo título (confira se o filtro não está agressivo demais):")
        for e in excluidas[:25]:
            print(f"  - {e}")
        if len(excluidas) > 25:
            print(f"  … e mais {len(excluidas) - 25}")
    if candidatas:
        print("\nCandidatas:")
        for c in candidatas:
            print(f"  {c['id']}  {c['publicada_em'] or '?':10}  {c['titulo'][:60]} | {c['empresa'][:30]}")

    if not brutas and erros:
        print("\nO portal não devolveu nada e houve erros: provável bloqueio temporário. Espere antes de tentar de novo.")
        return 3
    if args.gravar:
        print()
        return gravar(sem_avaliacao=True)
    print(f"\nPróximo passo: avaliar as candidatas ({(CACHE / 'candidatas.md').as_posix()}) e rodar `vagas.py gravar`,")
    print("ou gravar sem nota com `vagas.py gravar --sem-avaliacao`.")
    return 0


def escrever_digest(resultado: dict, trecho: int) -> None:
    p = resultado["parametros"]
    f = p["filtros"]
    cand = resultado["candidatas"]
    crit = [p["resumo"], *filtros.criterios_extra(f)]
    linhas = [
        f"# Candidatas — {resultado['gerado_em'][:16].replace('T', ' ')}",
        f"Fontes: {', '.join(p['fontes'])} · termos: {', '.join(p['termos'])} · janela {p['janela_horas']}h",
        f"Critérios do usuário: {'; '.join(crit)}",
        f"{len(cand)} candidatas (de {resultado['brutas']} vagas encontradas; {resultado['excluidas_titulo']} cortadas "
        f"pelo título; {resultado['ja_vistas']} já vistas; {len(resultado['fora'])} fora dos critérios)",
        "",
    ]
    for i, c in enumerate(cand, 1):
        desc = c["descricao"]
        if len(desc) > trecho:
            desc = desc[:trecho].rstrip() + f"\n\n[… cortada em {trecho} caracteres; texto completo: vagas.py ver {c['id']}]"
        rep = f" · +{len(c['ids_relacionados'])} anúncio(s) igual(is)" if c["ids_relacionados"] else ""
        linhas += [
            "---",
            f"## {i}. {c['titulo']} — {c['empresa']}",
            f"id: {c['id']} · {c['plataforma']} · {c['local'] or 'local não informado'} · publicada "
            f"{c['publicada_em'] or '?'} · salário: {c['salario'] or 'não informado'} · termos: {', '.join(c['termos'])}"
            f" · busca: {', '.join(rotulo_grupo(g, f) for g in c['grupos'])}{rep}",
            "",
            desc or "(sem descrição)",
            "",
        ]
    (CACHE / "candidatas.md").write_text("\n".join(linhas), encoding="utf-8")


# ---------------------------------------------------------------- ver

def cmd_ver(args) -> int:
    dados = json.loads((CACHE / "candidatas.json").read_text(encoding="utf-8"))
    cand = {c["id"]: c for c in dados["candidatas"]}
    for jid in args.ids:
        c = cand.get(jid)
        if not c:
            print(f"## {jid}: não está na última busca\n")
            continue
        print(f"## {c['titulo']} — {c['empresa']} ({jid})")
        print(f"{c['plataforma']} · {c['local'] or 'local não informado'} · publicada {c['publicada_em'] or '?'} · "
              f"salário: {c['salario'] or 'não informado'}")
        print(f"\n{c['descricao'] or '(sem descrição)'}\n")
    return 0


# ---------------------------------------------------------------- gravar

def cmd_gravar(args) -> int:
    return gravar(sem_avaliacao=args.sem_avaliacao, arquivo=args.avaliacoes)


def gravar(sem_avaliacao: bool = False, arquivo: str | None = None) -> int:
    arq_cand = CACHE / "candidatas.json"
    if not arq_cand.exists():
        print("Nenhuma busca em .cache/candidatas.json. Rode `vagas.py buscar` antes.", file=sys.stderr)
        return 2
    dados = json.loads(arq_cand.read_text(encoding="utf-8"))
    cand = {c["id"]: c for c in dados["candidatas"]}

    if sem_avaliacao:
        avals = [{"id": jid} for jid in cand]
    else:
        arq_aval = Path(arquivo) if arquivo else CACHE / "avaliacoes.json"
        if not arq_aval.exists():
            print(f"Falta {arq_aval}. Para gravar sem nota, use --sem-avaliacao.", file=sys.stderr)
            return 2
        bruto = json.loads(arq_aval.read_text(encoding="utf-8"))
        avals = bruto.get("avaliacoes", []) if isinstance(bruto, dict) else bruto

    p = dados.get("parametros", {})
    f = p.get("filtros") or filtros.efetivos(filtros.ler_config())
    agora = datetime.now().isoformat(timespec="seconds")
    hoje = date.today().isoformat()
    busca_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    docs, problemas, notas = [], [], []
    avaliadas: set[str] = set()

    def documento(c: dict, analise: dict, motivos: list[str]) -> dict:
        d = {
            "id": c["id"], "origem": "busca", "plataforma": c["plataforma"],
            "titulo": c["titulo"], "empresa": c["empresa"], "local": c["local"], "remoto": c["remoto"],
            "publicada_em": c["publicada_em"], "url": c["url"], "url_candidatura": c.get("url_candidatura"),
            "salario": c["salario"], "tipo": c["tipo"], "descricao": c["descricao"],
            "termos": c["termos"], "grupos": c.get("grupos", []), "ids_relacionados": c["ids_relacionados"],
            "outras_plataformas": c.get("outras_plataformas", []),
            **analise,
            "triagem": "pendente", "triada_em": None,
            "etapa": None, "etapa_em": None, "resultado": None, "anotacao": "",
            "busca_id": busca_id, "encontrada_em": hoje, "criada_em": agora, "atualizada_em": agora,
        }
        if motivos:  # fura algum filtro: vai para a aba Fora dos critérios, de onde dá para seguir com ela
            d.update(triagem="fora", triada_em=hoje, motivo_fora=motivos)
        return d

    for a in avals:
        jid = str(a.get("id", "")).strip()
        if jid not in cand:
            problemas.append(f"id {jid!r} não está na última busca; ignorado")
            continue
        if jid in avaliadas:
            problemas.append(f"id {jid} avaliado duas vezes; mantida a primeira")
            continue
        if sem_avaliacao:
            analise = {"analise_status": "sem_analise"}
        else:
            try:
                analise = banco.validar_analise({**a, "analise_status": "feita"})
            except ValueError as e:
                problemas.append(f"id {jid}: {e}; ignorado")
                continue
        c = cand[jid]
        docs.append(documento(c, analise, filtros.criterios({**c, **analise}, f)))
        avaliadas.add(jid)
        notas.append((analise.get("aderencia"), c))
    for c in dados.get("fora", []):  # cortadas antes da IA (empresa excluída, senioridade do título)
        docs.append(documento(c, {"analise_status": "sem_analise"}, c["motivo_fora"]))

    novas, existentes = banco.inserir_vagas(docs)
    for vid, reg in dados.get("outros_portais", {}).items():  # vagas já no dashboard que a busca achou em outro portal
        banco.registrar_outros_portais(vid, reg["plataformas"], reg["ids"])
    fora_novas = [d for d in docs if d["triagem"] == "fora" and d["id"] in novas]
    ids_fora = {d["id"] for d in fora_novas}
    faltando = [jid for jid in cand if jid not in avaliadas]
    faixas = [n for n, c in notas if c["id"] in novas and c["id"] not in ids_fora and n is not None]
    banco.registrar_busca(busca_id, {
        "data": agora, "fontes": p.get("fontes", []), "termos": p.get("termos", []),
        "janela_horas": p.get("janela_horas"), "resumo": p.get("resumo"), "consultas": p.get("consultas"),
        "brutas": dados.get("brutas", 0), "excluidas_titulo": dados.get("excluidas_titulo", 0),
        "ja_vistas": dados.get("ja_vistas", 0) + len(existentes), "candidatas": len(cand),
        "avaliadas": len(novas) - len(fora_novas), "fora_criterios": len(fora_novas), "com_nota": not sem_avaliacao,
        "fortes": sum(n >= 80 for n in faixas), "boas": sum(65 <= n < 80 for n in faixas),
        "parciais": sum(50 <= n < 65 for n in faixas), "baixas": sum(n < 50 for n in faixas),
    })

    if problemas:
        print("Problemas nas avaliações:")
        for x in problemas:
            print(f"  - {x}")
    if faltando:
        print(f"ATENÇÃO: {len(faltando)} candidata(s) sem avaliação não foram gravadas e voltarão na próxima busca: "
              + ", ".join(faltando))
    if existentes:
        print(f"Já estavam no dashboard (não alteradas): {', '.join(existentes)}")
    print(f"Gravadas no dashboard: {len(novas) - len(fora_novas)} vaga(s) nova(s) para decidir, busca {busca_id}.")
    if fora_novas:
        print(f"Fora dos critérios: {len(fora_novas)} (aba Fora dos critérios do relatório; dá para seguir com elas de lá)")
        for d in fora_novas:
            print(f"  - {d['titulo'][:55]} | {d['empresa'][:28]}: {'; '.join(d['motivo_fora'])}")
    print(f"Dashboard: {URL_DASHBOARD}#relatorio  (se não abrir, rode: python dash/servidor.py)")

    if not sem_avaliacao and notas:
        notas.sort(key=lambda x: (-(x[0] or 0), x[1].get("publicada_em") or ""))
        print()
        print("Ranking desta busca:")
        for n, c in notas:
            marca = "  [fora dos critérios]" if c["id"] in ids_fora else ""
            print(f"  {n:3d}  {c['titulo'][:55]} | {c['empresa'][:28]} | {c['publicada_em'] or '?'} | {c['url']}{marca}")
    return 0 if novas or not docs else 1


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("buscar", help="busca vagas nos portais configurados")
    p1.add_argument("--gravar", action="store_true", help="grava tudo direto no dashboard, sem nota (uso sem IA)")
    p1.add_argument("--termos", nargs="+", help="substitui os termos do config.json")
    p1.add_argument("--fontes", nargs="+", help=f"substitui as fontes do config.json ({', '.join(FONTES)})")
    p1.add_argument("--janela-horas", type=int, help="só vagas publicadas nas últimas N horas")
    p1.add_argument("--resultados", type=int, help="máximo de vagas por termo")
    p1.add_argument("--local", help='substitui o "local" do config.json')
    p1.add_argument("--incluir-presencial", action="store_true", help="não restringe a vagas remotas")
    p1.add_argument("--trecho", type=int, default=3500, help="caracteres de descrição no .cache/candidatas.md")
    p1.add_argument("--pausa", type=float, default=2.0, help="segundos entre buscas")

    p2 = sub.add_parser("ver", help="descrição completa de uma ou mais candidatas")
    p2.add_argument("ids", nargs="+")

    p3 = sub.add_parser("gravar", help="grava as candidatas da última busca no dashboard")
    p3.add_argument("--sem-avaliacao", action="store_true", help="grava sem nota de aderência")
    p3.add_argument("--avaliacoes", help="padrão: .cache/avaliacoes.json")

    args = ap.parse_args()
    return {"buscar": cmd_buscar, "ver": cmd_ver, "gravar": cmd_gravar}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
