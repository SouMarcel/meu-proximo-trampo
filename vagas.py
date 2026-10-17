#!/usr/bin/env python3
"""meu-proximo-trampo: busca vagas e manda para o dashboard local.

  python vagas.py buscar --gravar   busca e grava tudo no dashboard, sem nota (uso sem IA)
  python vagas.py buscar            busca e deixa as candidatas em .cache/ para avaliação
  python vagas.py ver ID [ID…]      descrição completa de candidatas
  python vagas.py gravar            grava as candidatas avaliadas (.cache/avaliacoes.json)
  python vagas.py gravar --sem-avaliacao   grava as candidatas da última busca sem nota

Configuração em config.json (copie de config.exemplo.json). Dashboard: python dash/servidor.py
Uma busca por vez no computador: com uma busca rodando pela página do dashboard, buscar sai com código 4.
Portal em espera depois de um bloqueio (ex.: LinkedIn, 6 horas): buscar pergunta antes de seguir sem ele; sem
terminal interativo, sai com código 5 até receber --confirmar-espera.
"""
from __future__ import annotations

import argparse
import json
import math
import os
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
from fontes import FONTES, _comum  # noqa: E402


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


# ---------------------------------------------------------------- uma busca por vez

class Cancelada(Exception):
    """A pessoa cancelou a busca (pela página); nada dela é gravado."""


class BuscaOcupada(RuntimeError):
    """Outro processo (a página ou outro terminal) está consultando os portais."""

    def __init__(self, quem: dict | None):
        self.quem = quem or {}
        super().__init__(mensagem_ocupada(self.quem))


def mensagem_ocupada(quem: dict) -> str:
    desde = str(quem.get("inicio") or "")[11:16]
    if quem.get("origem") == "pagina":
        return ("Há uma busca rodando pela página do dashboard" + (f" (desde {desde})" if desde else "")
                + ". Espere ela terminar ou cancele por lá.")
    return "Há outra busca rodando no terminal ou no chat" + (f" desde {desde}" if desde else "") + ". Espere ela terminar."


def _arq_trava() -> Path:
    return CACHE / "busca.trava"


def _arq_registro() -> Path:
    return CACHE / "busca.json"


def _travar(arq) -> bool:
    """Trava do sistema operacional: o sistema solta sozinho se o processo morrer."""
    try:
        if os.name == "nt":
            import msvcrt
            arq.seek(0)
            msvcrt.locking(arq.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(arq.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _destravar(arq) -> None:
    try:
        if os.name == "nt":
            import msvcrt
            arq.seek(0)
            msvcrt.locking(arq.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(arq.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def _ler_registro() -> dict | None:
    try:
        dados = json.loads(_arq_registro().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def _gravar_registro(dados: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = _arq_registro().with_name("busca.json.tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, _arq_registro())


def ocupada() -> dict | None:
    """Quem está consultando os portais agora (o registro da busca), ou None."""
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(_arq_trava(), "a+b") as arq:
        if _travar(arq):
            _destravar(arq)
            return None
    return _ler_registro() or {}


def ultima() -> dict | None:
    """A última busca {origem, inicio, situacao, fim}; "rodando" com a trava livre vira "interrompida"."""
    reg = _ler_registro()
    if reg and reg.get("situacao") == "rodando" and ocupada() is None:
        reg = {**reg, "situacao": "interrompida"}
    return reg


class TravaBusca:
    """Uma busca por vez no computador (página, terminal ou chat), com o registro em .cache/busca.json.
    Ao sair, situacao: a que quem buscou definiu ("concluida" ou "falha"), "cancelada" ou "erro"."""

    def __init__(self, origem: str):
        self.origem, self.situacao, self.arq, self.inicio = origem, "concluida", None, None

    def __enter__(self):
        CACHE.mkdir(parents=True, exist_ok=True)
        self.arq = open(_arq_trava(), "a+b")
        if not _travar(self.arq):
            self.arq.close()
            raise BuscaOcupada(_ler_registro())
        self.inicio = datetime.now().isoformat(timespec="seconds")
        _gravar_registro({"origem": self.origem, "inicio": self.inicio, "situacao": "rodando", "pid": os.getpid()})
        return self

    def __exit__(self, tipo, erro, rastro):
        situacao = self.situacao
        if tipo is not None:
            situacao = "cancelada" if issubclass(tipo, (Cancelada, KeyboardInterrupt)) else "erro"
        try:
            _gravar_registro({"origem": self.origem, "inicio": self.inicio, "situacao": situacao,
                              "fim": datetime.now().isoformat(timespec="seconds"), "pid": os.getpid()})
        finally:
            _destravar(self.arq)
            self.arq.close()
        return False


# ---------------------------------------------------------------- buscar

def rotulo_grupo(grupo: str, f: dict) -> str:
    if grupo == filtros.GLOBAL:
        return "exterior"
    if grupo.startswith("internacional:"):
        return grupo.split(":", 1)[1]
    if grupo.startswith("mudanca:"):
        return grupo.split(":", 1)[1] + " (presencial/híbrido)"
    return {"remoto": "remoto", "pais": "país todo", "local": filtros.cidade_rotulo(f)}.get(grupo, grupo)


def fontes_da_busca(cfg: dict, f: dict) -> list[str]:
    """As fontes do config.json e, com a busca internacional ligada, as do exterior escolhidas no painel e a das
    empresas acompanhadas."""
    nomes = list(cfg.get("fontes", ["indeed", "gupy"]))
    inter = f["internacional"]
    if inter["ativo"]:
        nomes += [n for n in inter.get("fontes") or [] if n not in nomes]
        if inter.get("empresas") and "ats" not in nomes:
            nomes.append("ats")
    return nomes


def atende(fonte, c: dict) -> bool:
    """Cada portal só na sua área; as fontes sem filtro de país (POR_PAIS = False) só nas consultas globais, e as
    com GLOBAL = True nas duas."""
    if c.get("area", "nacional") not in getattr(fonte, "AREAS", ("nacional", "internacional")):
        return False
    por_pais = getattr(fonte, "POR_PAIS", True)
    return (not por_pais or getattr(fonte, "GLOBAL", False)) if c.get("global") else por_pais


def fontes_em_espera(nomes_fontes: list[str]) -> list[dict]:
    """As fontes em espera depois de um bloqueio (as que têm espera()): [{nome, portal, ate, motivo}]."""
    lista = []
    for n in nomes_fontes:
        fonte = FONTES.get(n)
        esp = getattr(fonte, "espera", None)
        e = esp() if esp else None
        if e:
            lista.append({"nome": n, "portal": fonte.PLATAFORMA, "ate": e["ate"], "motivo": e["motivo"]})
    return lista


def aviso_espera(esperas: list[dict]) -> str:
    return "; ".join(f"{e['portal']} em espera até {str(e['ate'])[11:16]} ({e['motivo']})" for e in esperas)


def consultas_da_fonte(plano: list[dict], fonte) -> list[dict]:
    """As consultas do plano que o portal atende; com AGRUPAR, uma por grupo (os cargos ligados por OR, dividida
    se a expressão passar do tamanho máximo)."""
    lista = [c for c in plano if atende(fonte, c)]
    if not getattr(fonte, "AGRUPAR", False):
        return lista
    grupos: dict[str, list[dict]] = {}
    for c in lista:
        grupos.setdefault(c["grupo"], []).append(c)
    saida = []
    for cs in grupos.values():
        if len(cs) == 1:
            saida.append(cs[0])
            continue
        for termos, expressao in filtros.expressao_or([c["termo"] for c in cs]):
            saida.append({**cs[0], "termo": expressao, "termos": termos, "agrupada": len(termos) > 1})
    return saida


def contar_consultas(plano: list[dict], nomes_fontes: list[str]) -> int:
    return sum(len(consultas_da_fonte(plano, FONTES[n])) for n in nomes_fontes if n in FONTES)


def aviso_pausa(f: dict, nomes_fontes: list[str]) -> str | None:
    """A pausa do LinkedIn quando LINKEDIN_PAUSA está definida (spec 017): no começo da busca, na página e no terminal.
    Sem o LinkedIn na busca, ou em espera depois de um bloqueio, não há pedidos e não há aviso."""
    if "linkedin" not in nomes_fontes or "linkedin" not in FONTES or not f.get("termos"):
        return None
    fonte = FONTES["linkedin"]
    if getattr(fonte, "espera", None) and fonte.espera():
        return None
    return fonte.aviso_pausa(len(consultas_da_fonte(filtros.consultas(f), fonte)))


def executar(cfg: dict, f: dict, nomes_fontes: list[str], por_termo: int, pausa: float = 2.0,
             incluir_presencial: bool = False, progresso=None, cancelado=None) -> dict:
    """A busca, sem imprimir: consulta os portais, corta, agrupa repetidas e lê as descrições que faltam.

    progresso(evento) recebe {"etapa": "consulta", portal, cargo, grupo, feitas, total, encontradas} antes e
    depois de cada consulta e {"etapa": "descricoes", lidas, total} a cada descrição; cancelado() é olhado
    antes de cada consulta e de cada descrição (verdadeiro: levanta Cancelada). ImportError sobe."""
    avisar = progresso or (lambda evento: None)

    def conferir():
        if cancelado and cancelado():
            raise Cancelada()

    termos = f["termos"]
    horas = f["janela_horas"]
    plano = filtros.consultas(f, incluir_presencial=incluir_presencial)
    total = contar_consultas(plano, nomes_fontes)
    esperas = fontes_em_espera(nomes_fontes)
    _comum.esquecer()  # as listas das fontes do exterior são baixadas de novo a cada busca
    brutas: dict[str, dict] = {}
    por_busca: dict[str, int] = {}
    erros: list[str] = []
    feitas = 0
    for nome in nomes_fontes:
        fonte = FONTES[nome]
        for c in consultas_da_fonte(plano, fonte):
            conferir()
            if feitas:
                time.sleep(pausa)
                conferir()
            cargo = f"{len(c['termos'])} cargos" if c.get("agrupada") else c["termo"].strip('"')
            evento = {"etapa": "consulta", "portal": fonte.PLATAFORMA, "cargo": cargo,
                      "grupo": rotulo_grupo(c["grupo"], f), "total": total}
            avisar({**evento, "feitas": feitas, "encontradas": len(brutas)})
            vagas, errs = fonte.buscar(c, horas, por_termo)
            rotulo = (f"{nome}: {cargo if c.get('agrupada') else c['termo']}"
                      + ("" if c["grupo"] == "remoto" else f" [{rotulo_grupo(c['grupo'], f)}]"))
            erros += [f"{rotulo}: {m}" for m in errs]
            por_busca[rotulo] = len(vagas)
            for v in vagas:
                atual = brutas.setdefault(v["id"], {**v, "termos": [], "grupos": []})
                # consulta combinada: os cargos que aparecem no título (ou a expressão, se nenhum aparecer)
                termos_v = [c["termo"]]
                if c.get("agrupada"):
                    termos_v = filtros.termos_no_titulo(v["titulo"], c["termos"]) or termos_v
                for t in termos_v:
                    if t not in atual["termos"]:
                        atual["termos"].append(t)
                if c["grupo"] not in atual["grupos"]:
                    atual["grupos"].append(c["grupo"])
            feitas += 1
            avisar({**evento, "feitas": feitas, "encontradas": len(brutas)})

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
    descricoes_completadas = ler_descricoes(candidatas, fora, nomes_fontes, erros, avisar, conferir)
    candidatas.sort(key=lambda r: r.get("publicada_em") or "", reverse=True)

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "parametros": {"fontes": nomes_fontes, "termos": termos, "janela_horas": horas, "consultas": len(plano),
                       "resumo": filtros.resumo(f), "filtros": f, "resultados_por_termo": por_termo},
        "por_busca": por_busca,
        "brutas": len(brutas),
        "fora_da_janela": antigas,
        "excluidas_titulo": len(excluidas),
        "excluidas": excluidas,
        "ja_vistas": ja_vistas,
        "outros_portais": outros_portais,
        "erros": erros,
        "espera": esperas,
        "aviso_cargos": filtros.aviso_cargos(f, nomes_fontes),
        "descricoes_completadas": descricoes_completadas,
        "candidatas": candidatas,
        "fora": fora,
    }


def ler_descricoes(candidatas: list[dict], fora: list[dict], nomes_fontes: list[str], erros: list[str], avisar,
                   conferir) -> list[dict]:
    """Descrições dos portais cuja busca não traz o texto, só das vagas que vão para o relatório.

    Portal com MAX_DESCRICOES (ex.: LinkedIn): no máximo N pedidos por busca, contando os que falham, nesta ordem:
    as vagas do dashboard com descrição pendente, as candidatas novas e as fora dos critérios, das mais recentes
    para as mais antigas. Candidata que fica sem texto (limite, bloqueio ou espera) sai com descricao_pendente;
    as pendentes do dashboard tratadas agora voltam na lista devolvida, para gravar_resultado completar."""
    por_plataforma = {x.PLATAFORMA: x for x in FONTES.values()}
    recentes = lambda lista: sorted(lista, key=lambda v: v.get("publicada_em") or "", reverse=True)
    ids_busca = {v["id"] for v in candidatas + fora}
    ids_cand = {v["id"] for v in candidatas}
    fila = []
    for nome in nomes_fontes:
        fonte = FONTES.get(nome)
        if getattr(fonte, "MAX_DESCRICOES", None) and hasattr(fonte, "descrever"):
            fila += [(v, fonte, True) for v in banco.pendentes_de_descricao(fonte.PLATAFORMA)
                     if v["id"] not in ids_busca]
    fila += [(v, por_plataforma.get(v["plataforma"]), False) for v in recentes(candidatas) + recentes(fora)]
    fila = [(v, fonte, do_banco) for v, fonte, do_banco in fila if hasattr(fonte, "descrever")]
    usadas: dict[str, int] = {}
    completadas = []
    for i, (v, fonte, do_banco) in enumerate(fila, 1):
        conferir()
        limite = getattr(fonte, "MAX_DESCRICOES", None)
        parada = getattr(fonte, "parada", lambda: False)
        pulada = limite is not None and (usadas.get(fonte.NOME, 0) >= limite or parada())  # sem pedido
        if not pulada:
            usadas[fonte.NOME] = usadas.get(fonte.NOME, 0) + 1
            try:
                v["descricao"] = fonte.descrever(v)
            except Exception as e:  # cada portal tem o seu tipo de erro; a vaga segue com o que já tinha
                erros.append(f"{fonte.NOME}: descrição de {v['id']}: {e}")
        avisar({"etapa": "descricoes", "lidas": i, "total": len(fila)})
        if limite is None:
            continue
        pendente = not v.get("descricao") and (pulada or parada())  # erro só da vaga (ex.: removida): não fica
        if do_banco and not pendente:
            completadas.append({"id": v["id"], "descricao": v.get("descricao") or "",
                                "tipo_emprego": v.get("tipo_emprego") or []})
        elif not do_banco and pendente and v["id"] in ids_cand:
            v["descricao_pendente"] = True
    return completadas


def salvar_candidatas(resultado: dict, pasta: Path | None = None, trecho: int = 3500) -> None:
    pasta = pasta or CACHE
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "candidatas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_digest(resultado, trecho, pasta)


def bloqueio_provavel(resultado: dict) -> bool:
    """Nenhuma vaga e todos os portais consultados deram erro. Um portal que respondeu sem vagas não é bloqueio: a
    busca vale, com zero vagas e o aviso do portal que falhou."""
    if resultado["brutas"] or not resultado["erros"]:
        return False
    consultados = {rotulo.split(":", 1)[0] for rotulo in resultado.get("por_busca", {})}
    com_erro = {erro.split(":", 1)[0] for erro in resultado["erros"]}
    return not (consultados - com_erro)


def confirmar_espera(nomes_fontes: list[str], confirmado: bool) -> bool:
    """Com portal em espera, só segue com a confirmação da pessoa (pergunta no terminal ou --confirmar-espera)."""
    esperas = fontes_em_espera(nomes_fontes)
    if not esperas:
        return True
    aviso = aviso_espera(esperas)
    if len(esperas) == len(nomes_fontes):
        print(f"{aviso}. Nenhum outro portal está ligado: não há o que buscar agora.", file=sys.stderr)
        return False
    if confirmado:
        return True
    portais = " e o ".join(e["portal"] for e in esperas)
    if sys.stdin.isatty():
        try:
            resp = input(f"{aviso}: fica de fora desta busca. Seguir sem o {portais}? [s/N] ")
        except EOFError:  # sem ninguém digitando (no Windows, NUL também conta como terminal)
            print()
        else:
            if resp.strip().lower() in ("s", "sim"):
                return True
            print("Busca não iniciada.")
            return False
    print(f"{aviso}: fica de fora desta busca. Para seguir só com os outros portais, rode de novo com "
          "--confirmar-espera.", file=sys.stderr)
    return False


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
    por_termo = args.resultados or cfg.get("resultados_por_termo", 40)
    nomes_fontes = args.fontes or fontes_da_busca(cfg, f)
    if args.fontes:
        f["fontes"] = list(args.fontes)  # o plano de consultas segue as fontes pedidas (ex.: o LinkedIn no "mundo todo")
    desconhecidas = [n for n in nomes_fontes if n not in FONTES]
    if desconhecidas:
        print(f"Fonte(s) desconhecida(s): {', '.join(desconhecidas)}. Disponíveis: {', '.join(FONTES)}", file=sys.stderr)
        return 2
    if not confirmar_espera(nomes_fontes, args.confirmar_espera):
        return 5
    for aviso in (filtros.aviso_cargos(f, nomes_fontes), aviso_pausa(f, nomes_fontes)):
        if aviso:
            print(f"Aviso: {aviso}")

    try:
        with TravaBusca("terminal") as trava:
            try:
                resultado = executar(cfg, f, nomes_fontes, por_termo, pausa=args.pausa,
                                     incluir_presencial=args.incluir_presencial)
            except ImportError as e:
                print(f"ERRO: dependência ausente ({e}). Rode: pip install -r requirements.txt", file=sys.stderr)
                trava.situacao = "erro"
                return 2
            if bloqueio_provavel(resultado):
                trava.situacao = "falha"
    except BuscaOcupada as e:
        print(str(e), file=sys.stderr)
        return 4
    salvar_candidatas(resultado, CACHE, args.trecho)

    candidatas, fora, erros, excluidas = (resultado["candidatas"], resultado["fora"], resultado["erros"],
                                          resultado["excluidas"])
    print(f"Consultas: {resultado['parametros']['consultas']} ({filtros.resumo(f)})")
    print(f"Vagas encontradas: {resultado['brutas']}  "
          f"({', '.join(f'{k}: {n}' for k, n in resultado['por_busca'].items())})")
    print(f"Publicadas antes da janela (descartadas): {resultado['fora_da_janela']}")
    print(f"Cortadas pelo título: {len(excluidas)}")
    print(f"Já vistas (já estão no dashboard): {resultado['ja_vistas']}")
    print(f"Fora dos critérios (vão para a aba Fora dos critérios, sem avaliação): {len(fora)}")
    for v in fora:
        print(f"  - {v['titulo'][:55]} | {v['empresa'][:28]}: {'; '.join(v['motivo_fora'])}")
    print(f"CANDIDATAS: {len(candidatas)}")
    sem_texto = sum(1 for c in candidatas if c.get("descricao_pendente"))
    if sem_texto:
        print(f"  {sem_texto} com descrição pendente (o portal limitou os pedidos): entram sem nota e o texto "
              "é lido na próxima busca; não avalie essas.")
    if resultado.get("descricoes_completadas"):
        print(f"Descrições pendentes de buscas anteriores lidas agora: {len(resultado['descricoes_completadas'])}")
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

    if bloqueio_provavel(resultado):
        print("\nO portal não devolveu nada e houve erros: provável bloqueio temporário. Espere antes de tentar de novo.")
        return 3
    if args.gravar:
        print()
        return gravar(sem_avaliacao=True)
    print(f"\nPróximo passo: avaliar as candidatas ({(CACHE / 'candidatas.md').as_posix()}) e rodar `vagas.py gravar`,")
    print("ou gravar sem nota com `vagas.py gravar --sem-avaliacao`.")
    return 0


def escrever_digest(resultado: dict, trecho: int, pasta: Path | None = None) -> None:
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
            desc or ("(descrição pendente: o portal limitou os pedidos. NÃO avalie esta vaga; ela entra sem nota "
                     "e o texto é lido na próxima busca)" if c.get("descricao_pendente") else "(sem descrição)"),
            "",
        ]
    ((pasta or CACHE) / "candidatas.md").write_text("\n".join(linhas), encoding="utf-8")


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


def gravar_resultado(dados: dict, avals: list[dict] | None = None, sem_avaliacao: bool = False,
                     status_sem_nota: str = "sem_analise", origem: str = "terminal") -> dict:
    """Grava no dashboard o resultado de uma busca (o conteúdo de candidatas.json), sem imprimir.

    sem_avaliacao: as candidatas entram com analise_status=status_sem_nota ("sem_analise" fica sem nota;
    "pendente" deixa para a análise automática); senão, com as avaliações de avals. Devolve o que a linha
    de comando e a página mostram."""
    cand = {c["id"]: c for c in dados["candidatas"]}
    if sem_avaliacao:
        avals = [{"id": jid} for jid in cand]
    p = dados.get("parametros", {})
    f = p.get("filtros") or filtros.efetivos(filtros.ler_config())
    agora = datetime.now().isoformat(timespec="seconds")
    hoje = date.today().isoformat()
    busca_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    docs, problemas, notas = [], [], []
    avaliadas: set[str] = set()

    def documento(c: dict, analise: dict, motivos: list[str]) -> dict:
        area, pais_vaga = filtros.area_da_vaga(c, f)
        d = {
            "id": c["id"], "origem": "busca", "plataforma": c["plataforma"],
            "titulo": c["titulo"], "empresa": c["empresa"], "local": c["local"], "remoto": c["remoto"],
            "publicada_em": c["publicada_em"], "url": c["url"], "url_candidatura": c.get("url_candidatura"),
            "salario": c["salario"], "tipo": c["tipo"], "descricao": c["descricao"],
            "termos": c["termos"], "grupos": c.get("grupos", []), "ids_relacionados": c["ids_relacionados"],
            "outras_plataformas": c.get("outras_plataformas", []),
            "area": area, "pais_vaga": pais_vaga, "idioma": filtros.idioma_da_vaga(c),
            **{k: c[k] for k in ("restricao_local", "ats", "moeda", "modelo_trabalho", "tipo_emprego",
                                 "descricao_pendente") if c.get(k)},  # o que a fonte informa
            **({"sinais": s} if (s := filtros.sinais(c, f)) else {}),  # patrocínio de visto, relocation…
            **analise,
            "triagem": "pendente", "triada_em": None,
            "etapa": None, "etapa_em": None, "resultado": None, "anotacao": "",
            "busca_id": busca_id, "encontrada_em": hoje, "criada_em": agora, "atualizada_em": agora,
        }
        if motivos:  # fura algum filtro: vai para a aba Fora dos critérios, de onde dá para seguir com ela
            d.update(triagem="fora", triada_em=hoje, motivo_fora=motivos)
        return d

    for a in avals or []:
        jid = str(a.get("id", "")).strip()
        if jid not in cand:
            problemas.append(f"id {jid!r} não está na última busca; ignorado")
            continue
        if jid in avaliadas:
            problemas.append(f"id {jid} avaliado duas vezes; mantida a primeira")
            continue
        if sem_avaliacao:
            analise = {"analise_status": status_sem_nota}
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
    for jid, c in cand.items():  # sem texto (limite de pedidos do portal): entra sem nota, à espera da descrição
        if jid not in avaliadas and c.get("descricao_pendente"):
            docs.append(documento(c, {"analise_status": "sem_analise"}, filtros.criterios(c, f)))
            avaliadas.add(jid)
    for c in dados.get("fora", []):  # cortadas antes da IA (empresa excluída, senioridade do título)
        docs.append(documento(c, {"analise_status": "sem_analise"}, c["motivo_fora"]))

    novas, existentes = banco.inserir_vagas(docs)
    for vid, reg in dados.get("outros_portais", {}).items():  # vagas já no dashboard que a busca achou em outro portal
        banco.registrar_outros_portais(vid, reg["plataformas"], reg["ids"])
    fora_novas = [d for d in docs if d["triagem"] == "fora" and d["id"] in novas]
    ids_fora = {d["id"] for d in fora_novas}
    faltando = [jid for jid in cand if jid not in avaliadas]
    faixas = [n for n, c in notas if c["id"] in novas and c["id"] not in ids_fora and n is not None]
    completadas = sum(1 for c in dados.get("descricoes_completadas") or []
                      if banco.completar_descricao(c["id"], c.get("descricao") or "", c.get("tipo_emprego")))
    pendentes = sum(1 for d in docs if d.get("descricao_pendente") and d["id"] in novas and d["triagem"] != "fora")
    banco.registrar_busca(busca_id, {
        "data": agora, "fontes": p.get("fontes", []), "termos": p.get("termos", []),
        "janela_horas": p.get("janela_horas"), "resumo": p.get("resumo"), "consultas": p.get("consultas"),
        "brutas": dados.get("brutas", 0), "excluidas_titulo": dados.get("excluidas_titulo", 0),
        "ja_vistas": dados.get("ja_vistas", 0) + len(existentes), "candidatas": len(cand),
        "avaliadas": len(novas) - len(fora_novas), "fora_criterios": len(fora_novas),
        "com_nota": not sem_avaliacao or status_sem_nota == "pendente",
        "fortes": sum(n >= 80 for n in faixas), "boas": sum(65 <= n < 80 for n in faixas),
        "parciais": sum(50 <= n < 65 for n in faixas), "baixas": sum(n < 50 for n in faixas),
        "origem": origem, "situacao": "concluida",
    })
    return {"busca_id": busca_id, "novas": novas, "existentes": existentes, "fora_novas": fora_novas,
            "ids_fora": ids_fora, "faltando": faltando, "problemas": problemas, "notas": notas, "docs": len(docs),
            "para_decidir": len(novas) - len(fora_novas), "completadas": completadas, "pendentes": pendentes}


def gravar(sem_avaliacao: bool = False, arquivo: str | None = None, pasta: Path | None = None) -> int:
    pasta = pasta or CACHE
    arq_cand = pasta / "candidatas.json"
    if not arq_cand.exists():
        print("Nenhuma busca em .cache/candidatas.json. Rode `vagas.py buscar` antes.", file=sys.stderr)
        return 2
    dados = json.loads(arq_cand.read_text(encoding="utf-8"))
    avals = None
    if not sem_avaliacao:
        arq_aval = Path(arquivo) if arquivo else pasta / "avaliacoes.json"
        if not arq_aval.exists():
            print(f"Falta {arq_aval}. Para gravar sem nota, use --sem-avaliacao.", file=sys.stderr)
            return 2
        bruto = json.loads(arq_aval.read_text(encoding="utf-8"))
        avals = bruto.get("avaliacoes", []) if isinstance(bruto, dict) else bruto

    r = gravar_resultado(dados, avals, sem_avaliacao=sem_avaliacao)
    if r["problemas"]:
        print("Problemas nas avaliações:")
        for x in r["problemas"]:
            print(f"  - {x}")
    if r["faltando"]:
        print(f"ATENÇÃO: {len(r['faltando'])} candidata(s) sem avaliação não foram gravadas e voltarão na próxima busca: "
              + ", ".join(r["faltando"]))
    if r["existentes"]:
        print(f"Já estavam no dashboard (não alteradas): {', '.join(r['existentes'])}")
    print(f"Gravadas no dashboard: {r['para_decidir']} vaga(s) nova(s) para decidir, busca {r['busca_id']}.")
    if r["fora_novas"]:
        print(f"Fora dos critérios: {len(r['fora_novas'])} (aba Fora dos critérios do relatório; dá para seguir com elas de lá)")
        for d in r["fora_novas"]:
            print(f"  - {d['titulo'][:55]} | {d['empresa'][:28]}: {'; '.join(d['motivo_fora'])}")
    print(f"Dashboard: {URL_DASHBOARD}#relatorio  (se não abrir, rode: python dash/servidor.py)")

    notas = r["notas"]
    if not sem_avaliacao and notas:
        notas.sort(key=lambda x: (-(x[0] or 0), x[1].get("publicada_em") or ""))
        print()
        print("Ranking desta busca:")
        for n, c in notas:
            marca = "  [fora dos critérios]" if c["id"] in r["ids_fora"] else ""
            print(f"  {n:3d}  {c['titulo'][:55]} | {c['empresa'][:28]} | {c['publicada_em'] or '?'} | {c['url']}{marca}")
    return 0 if r["novas"] or not r["docs"] else 1


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
    p1.add_argument("--confirmar-espera", action="store_true",
                    help="segue sem os portais em espera depois de um bloqueio (ex.: LinkedIn), sem perguntar")

    p2 = sub.add_parser("ver", help="descrição completa de uma ou mais candidatas")
    p2.add_argument("ids", nargs="+")

    p3 = sub.add_parser("gravar", help="grava as candidatas da última busca no dashboard")
    p3.add_argument("--sem-avaliacao", action="store_true", help="grava sem nota de aderência")
    p3.add_argument("--avaliacoes", help="padrão: .cache/avaliacoes.json")

    args = ap.parse_args()
    return {"buscar": cmd_buscar, "ver": cmd_ver, "gravar": cmd_gravar}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
