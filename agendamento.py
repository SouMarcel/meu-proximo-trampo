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
ARQ_RETOMADAS = CACHE / "retomadas.json"
INTERVALO_RETOMADA = timedelta(hours=6)
TETO_SEM_AGENDADA = timedelta(hours=24)


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


def ler_retomadas() -> dict:
    """Lê as retomadas agendadas em arquivo. Ausente, quebrado ou não-dicionário devolve {}."""
    try:
        dados = json.loads(ARQ_RETOMADAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(dados, dict):
        return {}
    return dados


def gravar_retomadas(d: dict) -> None:
    """Grava as retomadas de forma atômica (.tmp + os.replace)."""
    ARQ_RETOMADAS.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARQ_RETOMADAS.with_name(f"{ARQ_RETOMADAS.name}.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ARQ_RETOMADAS)


def cancelar_retomada(nome: str) -> bool:
    """Lê as retomadas, apaga a chave nome e grava. Devolve False se não havia a chave."""
    retomadas = ler_retomadas()
    if nome not in retomadas:
        return False
    del retomadas[nome]
    gravar_retomadas(retomadas)
    return True


def apagar_retomadas() -> None:
    """Apaga o arquivo de retomadas se existir."""
    try:
        ARQ_RETOMADAS.unlink(missing_ok=True)
    except OSError:
        pass


def depois_da_busca(
    retomadas: dict,
    resultado: dict,
    origem: str,
    agora: datetime,
    continuar: bool,
    rotulo,
    pendentes,
) -> dict:
    """Calcula o novo dicionário de retomadas após o fim de uma busca.

    Pura: recebe e devolve o dicionário sem chamadas a datetime.now().
    """
    if not continuar:
        return {}

    if isinstance(agora, str):
        agora = datetime.fromisoformat(agora)

    if origem == "agendada":
        res = {}
    else:
        res = {k: dict(v) for k, v in retomadas.items()}

    rodaram = resultado.get("rodaram", [])
    bloqueados = resultado.get("bloqueados", [])
    faltaram_map = resultado.get("faltaram", {})

    for nome in rodaram:
        anterior = None if origem == "agendada" else retomadas.get(nome)
        if nome in bloqueados:
            tentativas_ant = anterior.get("tentativas", 0) if anterior else 0
            tentativas = tentativas_ant + (1 if origem == "retomada" else 0)
            origem_busca = (anterior.get("origem_busca") if anterior else None) or origem
            criada_em = (anterior.get("criada_em") if anterior else None) or agora.isoformat(timespec="minutes")
            proxima = (agora + INTERVALO_RETOMADA).isoformat(timespec="minutes")
            res[nome] = {
                "portal": rotulo(nome),
                "origem_busca": origem_busca,
                "criada_em": criada_em,
                "proxima": proxima,
                "faltaram": list(faltaram_map.get(nome, [])),
                "tentativas": tentativas,
            }
        else:
            if anterior:
                if pendentes(nome) > 0:
                    tentativas_ant = anterior.get("tentativas", 0)
                    tentativas = tentativas_ant + (1 if origem == "retomada" else 0)
                    origem_busca = anterior.get("origem_busca") or origem
                    criada_em = anterior.get("criada_em") or agora.isoformat(timespec="minutes")
                    proxima = (agora + INTERVALO_RETOMADA).isoformat(timespec="minutes")
                    res[nome] = {
                        "portal": rotulo(nome),
                        "origem_busca": origem_busca,
                        "criada_em": criada_em,
                        "proxima": proxima,
                        "faltaram": [],
                        "tentativas": tentativas,
                    }
                else:
                    res.pop(nome, None)
            else:
                # sem bloqueio e sem retomada anterior: nada
                pass

    return res


def registrar_retomadas(resultado: dict, origem: str, f: dict, gravado: bool = True,
                        so_consultas: dict | None = None, agora: datetime | None = None) -> dict:
    """Grava as retomadas depois de uma busca (concluída ou barrada por bloqueio provável).

    Devolve {"bloqueados": [rótulos dos portais bloqueados], "retomada_as": a menor hora da próxima retomada
    deles ou None}. Busca não gravada perdeu as vagas das consultas anteriores: o portal bloqueado refaz todas."""
    import banco
    import filtros
    import vagas

    ag = filtros.efetivos(filtros.ler_config())["agendamento"]
    agora = agora or datetime.now()
    bloqueados = [n for n in resultado.get("bloqueados", []) if n in vagas.FONTES]
    faltaram = {n: list(c) for n, c in resultado.get("faltaram", {}).items()}
    if not gravado:
        plano = filtros.consultas(f)
        for nome in bloqueados:
            faltaram[nome] = [dict(c) for c in (so_consultas[nome] if so_consultas and nome in so_consultas
                                                else vagas.consultas_da_fonte(plano, vagas.FONTES[nome]))]
    resultado = {**resultado, "faltaram": faltaram}
    retomadas = depois_da_busca(
        ler_retomadas(), resultado, origem, agora, bool(ag.get("continuar")),
        lambda n: vagas.FONTES[n].PLATAFORMA,
        lambda n: len(banco.pendentes_de_descricao(vagas.FONTES[n].PLATAFORMA)))
    gravar_retomadas(retomadas)
    horas = [retomadas[n]["proxima"] for n in bloqueados if n in retomadas]
    return {"bloqueados": [vagas.FONTES[n].PLATAFORMA for n in bloqueados], "retomada_as": min(horas) if horas else None}


def retomadas_devidas(
    retomadas: dict,
    agora: datetime,
    ag: dict,
    em_espera,
) -> tuple[list[str], dict, list[dict]]:
    """Identifica as retomadas devidas agora e atualiza o dicionário de retomadas.

    Pura: recebe e devolve (nomes devidos agora, retomadas atualizadas, eventos)
    sem chamadas a datetime.now().
    """
    if not ag or not ag.get("continuar"):
        return [], {}, []

    if isinstance(agora, str):
        agora = datetime.fromisoformat(agora)

    devidas: list[str] = []
    atualizadas: dict = {}
    eventos: list[dict] = []

    ligado = bool(ag.get("ligado"))

    for nome, ret_orig in retomadas.items():
        ret = dict(ret_orig)
        portal_nome = ret.get("portal", nome)

        try:  # retomada com data quebrada no arquivo sai, sem derrubar o relógio
            dt_criada = datetime.fromisoformat(str(ret.get("criada_em")))
            dt_proxima = datetime.fromisoformat(str(ret.get("proxima")))
        except (TypeError, ValueError):
            continue
        if dt_criada.tzinfo is not None and agora.tzinfo is None:
            dt_criada = dt_criada.replace(tzinfo=None)
        elif agora.tzinfo is not None and dt_criada.tzinfo is None:
            dt_criada = dt_criada.replace(tzinfo=agora.tzinfo)

        if dt_proxima.tzinfo is not None and agora.tzinfo is None:
            dt_proxima = dt_proxima.replace(tzinfo=None)
        elif agora.tzinfo is not None and dt_proxima.tzinfo is None:
            dt_proxima = dt_proxima.replace(tzinfo=agora.tzinfo)

        # Regra: ag["ligado"] falso e agora >= criada_em + 24 h
        if not ligado and agora >= dt_criada + TETO_SEM_AGENDADA:
            eventos.append({
                "tipo": "retomada",
                "portal": portal_nome,
                "situacao": "encerrada",
                "em": agora.isoformat(timespec="seconds"),
                "motivo": "24 horas sem busca agendada",
            })
            continue

        # Regra: agora < proxima
        if agora < dt_proxima:
            atualizadas[nome] = ret
            continue

        # Regra: agora > proxima + TOLERANCIA
        if agora > dt_proxima + TOLERANCIA:
            hora_perdida = dt_proxima.strftime("%H:%M")
            while dt_proxima + TOLERANCIA < agora:
                dt_proxima += INTERVALO_RETOMADA
            eventos.append({
                "tipo": "retomada",
                "portal": portal_nome,
                "situacao": "perdida",
                "em": agora.isoformat(timespec="seconds"),
                "motivo": f"o dashboard não estava ligado às {hora_perdida}",
            })
            if dt_proxima <= agora and em_espera(nome):  # caiu numa hora devida, mas o portal segue em espera
                dt_proxima += INTERVALO_RETOMADA
            ret["proxima"] = dt_proxima.isoformat(timespec="minutes")
            atualizadas[nome] = ret
            if dt_proxima <= agora:
                devidas.append(nome)
        elif em_espera(nome):
            dt_proxima += INTERVALO_RETOMADA
            eventos.append({
                "tipo": "retomada",
                "portal": portal_nome,
                "situacao": "pulada",
                "em": agora.isoformat(timespec="seconds"),
                "motivo": "o portal ainda está em espera",
            })
            ret["proxima"] = dt_proxima.isoformat(timespec="minutes")
            atualizadas[nome] = ret
        else:
            atualizadas[nome] = ret
            devidas.append(nome)

    return devidas, atualizadas, eventos
