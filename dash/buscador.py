"""Busca de vagas pela página, em segundo plano (uma busca por vez no computador).

O servidor chama BUSCA.plano() para a confirmação, BUSCA.iniciar() para começar, BUSCA.cancelar() para
parar entre uma consulta e outra e BUSCA.estado() para o andamento. A busca é a mesma do terminal
(vagas.executar e vagas.gravar_resultado), com as candidatas em .cache/pagina/ (as de uma busca do chat,
em .cache/, ficam intactas) e a trava de vagas.TravaBusca. Com IA e perfil, as vagas novas entram
esperando nota e a análise automática (analise.FILA) dá as notas; sem IA, ficam sem nota.

Respeito aos portais: a página só inicia uma busca 30 minutos depois da última concluída (de qualquer
origem) e pede confirmação se a última foi há menos de 6 horas.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime, timedelta

import analise
import banco

RAIZ = banco.DASH.parent
INTERVALO_MINIMO = timedelta(minutes=30)
AVISO_RECENTE = timedelta(hours=6)
SEGUNDOS_POR_CONSULTA = 8  # estimativa: consulta mais a pausa entre elas
PAUSA = 2.0  # entre consultas, a mesma do terminal
LIMITE_ERROS = 20


def _raiz():
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))


def _vagas():
    _raiz()
    import vagas
    return vagas


def _filtros():
    _raiz()
    import filtros
    return filtros


def _ia():
    _raiz()
    import ia
    return ia


def _agora() -> datetime:
    return datetime.now()


def _hora(iso) -> str:
    return str(iso or "")[11:16]


class BuscaRecusada(Exception):
    """Pedido de busca que não pode começar agora (outra busca, intervalo mínimo, busca recente sem confirmar)."""

    def __init__(self, mensagem: str, precisa_confirmar: bool = False):
        super().__init__(mensagem)
        self.precisa_confirmar = precisa_confirmar


class Busca:
    def __init__(self):
        self._trava = threading.Lock()
        self._inicio = threading.Lock()  # um pedido de início por vez
        self._cancelar = threading.Event()
        self._thread: threading.Thread | None = None
        self._e: dict = {"situacao": "ociosa"}

    # ---------- estado
    def rodando(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _set(self, **campos):
        with self._trava:
            if self._e.get("situacao") == "cancelando" and campos.get("situacao") in ("consultando", "descricoes"):
                campos.pop("situacao")  # o pedido de cancelamento não volta atrás
            self._e.update(campos)

    def resumo(self) -> dict:
        """{situacao, origem} sem consultas pesadas, para /api/versao."""
        with self._trava:
            e = {"situacao": self._e["situacao"], "origem": self._e.get("origem")}
        if not self.rodando():
            quem = _vagas().ocupada()
            if quem is not None:
                e = {"situacao": "externa", "origem": quem.get("origem") or "terminal"}
        return e

    def estado(self) -> dict:
        """O andamento (data-model.md). Sem busca da página, mostra a do terminal ou a última interrompida."""
        with self._trava:
            e = dict(self._e)
        if not self.rodando():
            v = _vagas()
            quem = v.ocupada()
            if quem is not None:
                e = {"situacao": "externa", "origem": quem.get("origem") or "terminal", "inicio": quem.get("inicio"),
                     "mensagem": v.mensagem_ocupada(quem)}
            elif e["situacao"] == "ociosa":
                ult = v.ultima()
                if ult and ult.get("situacao") == "interrompida":
                    e = {"situacao": "interrompida", "origem": ult.get("origem"), "inicio": ult.get("inicio"),
                         "mensagem": "A última busca foi interrompida (a janela foi fechada no meio); nada dela foi gravado."}
        e["analise"] = self.analise()
        return e

    @staticmethod
    def analise() -> dict:
        return {"rodando": analise.FILA.rodando, "faltam": sum(analise.precisa(v) for v in banco.listar_vagas()),
                "erro": analise.FILA.erro()}

    # ---------- plano e intervalo
    @staticmethod
    def ultima() -> dict | None:
        """A última busca {origem, situacao, fim}; sem o registro novo, a última gravada no banco."""
        ult = _vagas().ultima()
        if ult:
            return {k: ult.get(k) for k in ("origem", "situacao", "inicio", "fim")}
        b = banco.ultima_busca()
        return {"origem": b.get("origem") or "terminal", "situacao": "concluida", "inicio": None, "fim": b.get("data")} if b else None

    @staticmethod
    def intervalo(ult: dict | None, agora: datetime | None = None) -> tuple[str | None, bool]:
        """(proxima_em, recente): proxima_em quando ainda não passou o intervalo mínimo; recente abaixo do aviso."""
        if not ult or ult.get("situacao") not in ("concluida", "falha") or not ult.get("fim"):
            return None, False
        try:
            fim = datetime.fromisoformat(str(ult["fim"]))
        except ValueError:
            return None, False
        passou = (agora or _agora()) - fim
        proxima = (fim + INTERVALO_MINIMO).isoformat(timespec="minutes") if passou < INTERVALO_MINIMO else None
        return proxima, passou < AVISO_RECENTE

    def plano(self) -> dict:
        fm, v, ia = _filtros(), _vagas(), _ia()
        try:
            cfg = fm.ler_config()
        except (OSError, ValueError):
            cfg = {}
        f = fm.efetivos(cfg)
        nomes = [n for n in cfg.get("fontes", ["indeed", "gupy"]) if n in v.FONTES]
        consultas = len(fm.consultas(f)) * len(nomes) if f["termos"] else 0
        escolha = ia.escolha_efetiva(cfg)
        prov = ia.PROVEDORES[escolha["provedor"]]
        perfil = RAIZ / (cfg.get("perfil") or "perfil.md")
        ult = self.ultima()
        proxima, recente = self.intervalo(ult)
        return {
            "filtros_ok": bool(f["termos"]), "perfil_ok": perfil.exists(), "consultas": consultas,
            "portais": [v.FONTES[n].PLATAFORMA for n in nomes], "cargos": [t.strip('"') for t in f["termos"]],
            "janela_horas": f["janela_horas"], "resumo": fm.resumo(f) if f["termos"] else "",
            "estimativa_min": max(1, round(consultas * SEGUNDOS_POR_CONSULTA / 60)) if consultas else 0,
            "ia": {"ligada": ia.disponivel(cfg), "nome": prov["nome"], "modelo": ia.modelo_efetivo(escolha),
                   "cobranca": prov["cobranca"]},
            "ultima": ult, "proxima_em": proxima, "recente": recente,
        }

    # ---------- iniciar e cancelar
    def iniciar(self, sem_nota: bool = False, confirmar_recente: bool = False) -> dict:
        v = _vagas()
        with self._inicio:
            if self.rodando():
                raise BuscaRecusada("Já há uma busca rodando pela página.")
            pl = self.plano()
            if not pl["filtros_ok"]:
                raise ValueError("Escolha os cargos em Filtros da busca antes de buscar.")
            quem = v.ocupada()
            if quem is not None:
                raise BuscaRecusada(v.mensagem_ocupada(quem))
            if pl["proxima_em"]:
                raise BuscaRecusada(f"Para os portais não bloquearem a busca, espere um pouco: dá para buscar de novo "
                                    f"a partir das {_hora(pl['proxima_em'])}.")
            if pl["recente"] and not confirmar_recente:
                raise BuscaRecusada(f"A última busca terminou às {_hora(pl['ultima']['fim'])}: os portais devem ter "
                                    "pouca vaga nova. Confirme para buscar mesmo assim.", precisa_confirmar=True)
            com_nota = pl["ia"]["ligada"] and pl["perfil_ok"] and not sem_nota
            self._cancelar.clear()
            with self._trava:
                self._e = {"situacao": "consultando", "origem": "pagina", "inicio": _agora().isoformat(timespec="seconds"),
                           "com_nota": com_nota, "feitas": 0, "total": pl["consultas"], "encontradas": 0,
                           "consulta": None, "descricoes": None, "erros": [], "resumo": None, "mensagem": ""}
            self._thread = threading.Thread(target=self._rodar, args=(com_nota,), daemon=True, name="busca-pagina")
            self._thread.start()
        return self.estado()

    def cancelar(self) -> dict:
        if self.rodando():
            self._cancelar.set()
            self._set(situacao="cancelando")
        return self.estado()

    # ---------- a busca
    def _progresso(self, ev: dict):
        if ev["etapa"] == "consulta":
            self._set(situacao="consultando", consulta={"portal": ev["portal"], "cargo": ev["cargo"], "grupo": ev["grupo"]},
                      feitas=ev["feitas"], total=ev["total"], encontradas=ev["encontradas"])
        elif ev["etapa"] == "descricoes":
            self._set(situacao="descricoes", descricoes={"lidas": ev["lidas"], "total": ev["total"]})

    def _fim(self, situacao: str, **campos):
        self._set(situacao=situacao, fim=_agora().isoformat(timespec="seconds"), **campos)

    def _rodar(self, com_nota: bool):
        v, fm = _vagas(), _filtros()
        try:
            cfg = fm.ler_config()
            f = fm.efetivos(cfg)
            nomes = [n for n in cfg.get("fontes", ["indeed", "gupy"]) if n in v.FONTES]
            with v.TravaBusca("pagina") as trava:
                try:
                    resultado = v.executar(cfg, f, nomes, cfg.get("resultados_por_termo", 40), pausa=PAUSA,
                                           progresso=self._progresso, cancelado=self._cancelar.is_set)
                except ImportError:
                    trava.situacao = "erro"
                    return self._fim("falha", mensagem="Falta uma biblioteca da busca: rode python iniciar.py "
                                                       "(ele pergunta antes de instalar).")
                if v.bloqueio_provavel(resultado):
                    trava.situacao = "falha"
                elif self._cancelar.is_set():  # pedido depois da última consulta: ainda não gravou nada
                    raise v.Cancelada()
            erros = resultado["erros"][:LIMITE_ERROS]
            if v.bloqueio_provavel(resultado):
                return self._fim("falha", erros=erros, mensagem="Os portais não responderam: provável bloqueio temporário. "
                                                                "Espere antes de tentar de novo.")
            self._set(situacao="gravando", erros=erros)
            v.salvar_candidatas(resultado, v.CACHE / "pagina")
            r = v.gravar_resultado(resultado, sem_avaliacao=True, origem="pagina",
                                   status_sem_nota="pendente" if com_nota else "sem_analise")
            self._fim("concluida", erros=erros, resumo={
                "brutas": resultado["brutas"], "novas": r["para_decidir"], "fora_criterios": len(r["fora_novas"]),
                "ja_vistas": resultado["ja_vistas"] + len(r["existentes"]),
                "excluidas_titulo": resultado["excluidas_titulo"], "fora_da_janela": resultado["fora_da_janela"],
                "busca_id": r["busca_id"], "com_nota": com_nota})
            if com_nota and r["para_decidir"]:
                analise.FILA.pedir()
        except v.Cancelada:
            self._fim("cancelada", mensagem="Busca cancelada; nada dela foi gravado.")
        except v.BuscaOcupada as e:
            self._fim("falha", mensagem=str(e))
        except Exception as e:  # nunca derruba o servidor; o detalhe fica na janela dele
            print(f"[busca pela página] erro: {e!r}", file=sys.stderr)
            self._fim("falha", mensagem="A busca parou por um erro inesperado; os detalhes estão na janela do servidor.")


BUSCA = Busca()
