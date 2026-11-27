"""Regras da busca agendada e histórico de execuções do agendamento (spec 064).
Biblioteca padrão, sem chamadas a datetime.now() dentro das regras."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

TOLERANCIA = timedelta(minutes=15)
JANELA_MANUAL = timedelta(hours=4)
ORIGENS_MANUAIS = ("pagina", "terminal", "chat")
MAX_EVENTOS = 30
CACHE = Path(__file__).resolve().parent / ".cache"
ARQ_ESTADO = CACHE / "agendamento.json"


def horario_de_hoje(ag: dict, agora: datetime) -> datetime:
    """Retorna datetime com o ano/mês/dia de agora e o horário HH:MM de ag."""
    horario = ag.get("horario", "08:00") if isinstance(ag, dict) else "08:00"
    try:
        h_str, m_str = str(horario).split(":")
        hora, minuto = int(h_str), int(m_str)
    except (ValueError, TypeError, AttributeError):
        hora, minuto = 8, 0
    return agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)


def manual_recente(historico: list[dict], h: datetime) -> dict | None:
    """A busca de origem manual cujo inicio está entre h - JANELA_MANUAL e h (inclusive) e cuja situação é concluida ou rodando; a mais nova delas."""
    if not isinstance(historico, list):
        return None
    limite_inferior = h - JANELA_MANUAL
    candidatos = []
    for item in historico:
        if not isinstance(item, dict):
            continue
        if item.get("origem") not in ORIGENS_MANUAIS:
            continue
        if item.get("situacao") not in ("concluida", "rodando"):
            continue
        inicio_raw = item.get("inicio")
        if not inicio_raw:
            continue
        try:
            if isinstance(inicio_raw, datetime):
                dt = inicio_raw
            else:
                dt = datetime.fromisoformat(str(inicio_raw))
        except (ValueError, TypeError):
            continue
        if dt.tzinfo is not None and h.tzinfo is None:
            dt = dt.replace(tzinfo=None)
        elif h.tzinfo is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=h.tzinfo)
        if limite_inferior <= dt <= h:
            candidatos.append((dt, item))
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c[0])[1]


def decidir_agendada(ag: dict, agora: datetime, estado: dict, historico: list[dict]) -> tuple[str | None, str | None]:
    """Decide se a busca agendada deve rodar, foi pulada ou perdida.

    Retorna:
    - (None, None) se ag["ligado"] é falso, se o dia já foi registrado em estado["dia"] ou se agora < h;
    - ("perdida", "o dashboard não estava ligado às HH:MM") se agora > h + TOLERANCIA;
    - ("pulada", "busca manual às HH:MM") se houve busca manual recente;
    - ("rodar", None) caso contrário.
    """
    if not ag or not ag.get("ligado"):
        return None, None
    dia_hoje = agora.date().isoformat()
    if estado and estado.get("dia") == dia_hoje:
        return None, None
    h = horario_de_hoje(ag, agora)
    if agora < h:
        return None, None
    if agora > h + TOLERANCIA:
        return "perdida", f"o dashboard não estava ligado às {h.strftime('%H:%M')}"
    manual = manual_recente(historico, h)
    if manual:
        inicio_raw = manual.get("inicio", "")
        try:
            dt = datetime.fromisoformat(str(inicio_raw))
            hh_mm = dt.strftime("%H:%M")
        except (ValueError, TypeError):
            hh_mm = str(inicio_raw)[11:16] if len(str(inicio_raw)) >= 16 else str(inicio_raw)
        return "pulada", f"busca manual às {hh_mm}"
    return "rodar", None


def proxima_agendada(ag: dict, agora: datetime, estado: dict) -> str | None:
    """ISO YYYY-MM-DDTHH:MM da próxima busca: hoje no horário se ainda não passou de h + TOLERANCIA e o dia não consta em estado["dia"]; senão amanhã; None se desligado."""
    if not ag or not ag.get("ligado"):
        return None
    h = horario_de_hoje(ag, agora)
    dia_hoje = agora.date().isoformat()
    dia_registrado = estado.get("dia") if isinstance(estado, dict) else None
    if agora <= h + TOLERANCIA and dia_registrado != dia_hoje:
        return h.strftime("%Y-%m-%dT%H:%M")
    amanha = h + timedelta(days=1)
    return amanha.strftime("%Y-%m-%dT%H:%M")


def ler_estado() -> dict:
    """Lê o estado do agendamento em arquivo. Se ausente ou quebrado, devolve o padrão."""
    padrao = {"dia": None, "historico": []}
    try:
        dados = json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao.copy()
    if not isinstance(dados, dict):
        return padrao.copy()
    res = dict(dados)
    if "dia" not in res or not (res["dia"] is None or isinstance(res["dia"], str)):
        res["dia"] = None
    if "historico" not in res or not isinstance(res["historico"], list):
        res["historico"] = []
    else:
        res["historico"] = [e for e in res["historico"] if isinstance(e, dict)]
    return res


def gravar_estado(estado: dict) -> None:
    """Grava o estado de forma atômica (.tmp + os.replace)."""
    ARQ_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARQ_ESTADO.with_name(f"{ARQ_ESTADO.name}.tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ARQ_ESTADO)


def registrar_evento(estado: dict, evento: dict, dia: str | None = None) -> dict:
    """Põe o evento no começo de estado["historico"] (até MAX_EVENTOS), e se dia vier grava estado["dia"] = dia. Devolve o estado."""
    if "historico" not in estado or not isinstance(estado["historico"], list):
        estado["historico"] = []
    novo_hist = [evento] + [e for e in estado["historico"] if isinstance(e, dict)]
    estado["historico"] = novo_hist[:MAX_EVENTOS]
    if dia is not None:
        estado["dia"] = dia
    return estado
