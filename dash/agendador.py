"""Relógio da busca agendada (spec 064): a cada 30 segundos vê se a busca do dia deve rodar.

As regras (horário, tolerância, busca manual recente) ficam em agendamento.py; aqui só o laço, a espera
quando há outra busca ou leitura em andamento e o registro do que aconteceu no estado do agendamento.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime

import banco
import buscador

RAIZ = banco.DASH.parent
INTERVALO = 30  # segundos entre uma olhada e outra


def _raiz():
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))


def _agendamento():
    _raiz()
    import agendamento
    return agendamento


def _vagas():
    _raiz()
    import vagas
    return vagas


def _filtros():
    _raiz()
    import filtros
    return filtros


class Agendador:
    def __init__(self):
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None
        self._devida: str | None = None  # data (ISO) da busca que já deve rodar e espera ficar livre

    def iniciar(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._laco, daemon=True, name="agendador")
        self._thread.start()

    def parar(self) -> None:
        self._parar.set()

    def _laco(self) -> None:
        while not self._parar.is_set():
            try:
                self.tick(datetime.now())
            except Exception as e:  # o relógio nunca cai por um erro de uma olhada
                print(f"[agendador] erro: {e!r}", file=sys.stderr)
            self._parar.wait(INTERVALO)

    @staticmethod
    def ocupado() -> bool:
        v = _vagas()
        return (buscador.BUSCA.rodando() or v.ocupada() is not None or buscador.COMPLETAR.rodando()
                or v._LEITURA.locked())

    def estado(self) -> dict:
        return {"devida": self._devida is not None}

    def tick(self, agora: datetime) -> None:
        ag = _agendamento()
        fm = _filtros()
        config = fm.efetivos(fm.ler_config())["agendamento"]
        estado = ag.ler_estado()
        hoje = agora.date().isoformat()
        if self._devida == hoje:
            return self._tentar(agora, estado, hoje)
        situacao, motivo = ag.decidir_agendada(config, agora, estado, _vagas().ler_historico())
        if situacao in ("perdida", "pulada"):
            ag.registrar_evento(estado, {"tipo": "agendada", "situacao": situacao,
                                         "em": agora.isoformat(timespec="seconds"), "motivo": motivo}, dia=hoje)
            ag.gravar_estado(estado)
        elif situacao == "rodar":
            self._devida = hoje
            self._tentar(agora, estado, hoje)

    def _tentar(self, agora: datetime, estado: dict, hoje: str) -> None:
        if self.ocupado():
            return  # tenta de novo na próxima olhada, mesmo depois da tolerância
        ag = _agendamento()
        evento = {"tipo": "agendada", "em": agora.isoformat(timespec="seconds")}
        try:
            buscador.BUSCA.iniciar(origem="agendada")
            evento["situacao"] = "rodou"
        except (buscador.BuscaRecusada, ValueError) as e:
            evento.update(situacao="falha", motivo=str(e))
        self._devida = None
        ag.registrar_evento(estado, evento, dia=hoje)
        ag.gravar_estado(estado)


AGENDADOR = Agendador()
