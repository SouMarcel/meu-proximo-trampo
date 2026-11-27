"""Busca agendada e retomada depois da espera (spec 064): configuração, regras do relógio, retomadas e integração.
Config, cache e banco numa pasta temporária; portais e relógio falsos."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402
import banco  # noqa: E402
import vagas  # noqa: E402
import agendamento  # noqa: E402


class TestConfigAgendamento(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name) / "config.json"
        self.config.write_text(json.dumps({"termos": ["analista"], "limpeza": {"fora": {"ligado": False}}}),
                               encoding="utf-8")
        p = mock.patch.object(filtros, "CONFIG", self.config)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_padrao_sem_chave(self):
        self.assertEqual(filtros.efetivos({})["agendamento"],
                         {"ligado": False, "horario": "08:00", "continuar": False})

    def test_config_fora_do_formato_fica_no_padrao(self):
        a = filtros.efetivos({"agendamento": {"ligado": "sim", "horario": "25:00", "continuar": True}})["agendamento"]
        self.assertEqual(a, {"ligado": False, "horario": "08:00", "continuar": True})

    def test_validar_horario(self):
        self.assertEqual(filtros.validar_agendamento({"horario": "7:05"})["horario"], "07:05")
        self.assertEqual(filtros.validar_agendamento({"horario": "23:59"})["horario"], "23:59")
        for ruim in ("24:00", "08:60", "8h", "", None, "08:00:00"):
            with self.assertRaisesRegex(ValueError, "horário inválido"):
                filtros.validar_agendamento({"horario": ruim})

    def test_salvar_grava_so_a_chave_e_mantem_o_resto(self):
        filtros.salvar_agendamento({"ligado": True, "horario": "09:30"})
        filtros.salvar_agendamento({"continuar": True})  # campo ausente fica como está
        cfg = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(cfg["agendamento"], {"ligado": True, "horario": "09:30", "continuar": True})
        self.assertEqual(cfg["termos"], ["analista"])
        self.assertEqual(cfg["limpeza"], {"fora": {"ligado": False}})

    def test_salvar_filtros_nao_desfaz_o_agendamento(self):
        filtros.salvar_agendamento({"ligado": True})
        self.assertNotIn("agendamento", filtros.validar({**filtros.efetivos(filtros.ler_config()),
                                                          "termos": ["analista"]}))


class PortalFalso:
    NOME = "falsa"
    PLATAFORMA = "Falsa"

    def __init__(self, bloqueia_em: int | None = None):
        self.bloqueia_em = bloqueia_em
        self.chamadas: list[dict] = []
        self._bloqueado = False
        self._espera: dict | None = None

    def parada(self) -> bool:
        return self._bloqueado or self._espera is not None

    def espera(self) -> dict | None:
        return self._espera

    def buscar(self, consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
        self.chamadas.append(dict(consulta))
        if self.bloqueia_em is not None and len(self.chamadas) >= self.bloqueia_em:
            self._bloqueado = True
            return [], ["bloqueio provável"]
        return [], []


class TestFaltaram(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.cfg = {
            "fontes": ["falsa"],
            "termos": ["c1", "c2", "c3", "c4", "c5"],
            "modelos": {"remoto": True, "hibrido": False, "presencial": False},
            "empresas_excluir": [],
            "janela_horas": 168,
            "ia": {"provedor": "nenhum"},
        }
        self.config_arq = self.raiz / "config.json"
        self.config_arq.write_text(json.dumps(self.cfg), encoding="utf-8")
        self.patches = [
            mock.patch.object(filtros, "CONFIG", self.config_arq),
            mock.patch.object(vagas, "CACHE", self.raiz / ".cache"),
            mock.patch.object(banco, "ARQUIVO", self.raiz / "banco.db"),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(self._limpar)

    def _limpar(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_bloqueio_na_terceira_consulta(self):
        portal = PortalFalso(bloqueia_em=3)
        with mock.patch.dict(vagas.FONTES, {"falsa": portal}):
            f = filtros.efetivos(self.cfg)
            res = vagas.executar(self.cfg, f, ["falsa"], 40, pausa=0)
            self.assertEqual(len(portal.chamadas), 3)
            self.assertEqual(res["bloqueados"], ["falsa"])
            self.assertIn("falsa", res["faltaram"])
            faltaram = res["faltaram"]["falsa"]
            self.assertEqual(len(faltaram), 3)
            self.assertEqual([c["termo"] for c in faltaram], ["c3", "c4", "c5"])

    def test_sem_bloqueio(self):
        portal = PortalFalso(bloqueia_em=None)
        with mock.patch.dict(vagas.FONTES, {"falsa": portal}):
            f = filtros.efetivos(self.cfg)
            res = vagas.executar(self.cfg, f, ["falsa"], 40, pausa=0)
            self.assertEqual(len(portal.chamadas), 5)
            self.assertNotIn("falsa", res["faltaram"])
            self.assertEqual(res["bloqueados"], [])

    def test_portal_em_espera_no_comeco(self):
        portal = PortalFalso()
        portal._espera = {"ate": "2026-11-27T12:00:00", "motivo": "excesso"}
        with mock.patch.dict(vagas.FONTES, {"falsa": portal}):
            f = filtros.efetivos(self.cfg)
            res = vagas.executar(self.cfg, f, ["falsa"], 40, pausa=0)
            self.assertNotIn("falsa", res["rodaram"])

    def test_so_consultas_especificas(self):
        portal = PortalFalso()
        with mock.patch.dict(vagas.FONTES, {"falsa": portal}):
            f = filtros.efetivos(self.cfg)
            plano = filtros.consultas(f)
            c4, c5 = plano[3], plano[4]
            vagas.executar(self.cfg, f, ["falsa"], 40, pausa=0, so_consultas={"falsa": [c4, c5]})
            self.assertEqual(len(portal.chamadas), 2)
            self.assertEqual(portal.chamadas, [c4, c5])

    def test_so_consultas_vazia(self):
        portal = PortalFalso()
        with mock.patch.dict(vagas.FONTES, {"falsa": portal}):
            f = filtros.efetivos(self.cfg)
            vagas.executar(self.cfg, f, ["falsa"], 40, pausa=0, so_consultas={"falsa": []})
            self.assertEqual(len(portal.chamadas), 0)


class TestHistoricoBuscas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / ".cache"
        p = mock.patch.object(vagas, "CACHE", self.cache)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_duas_buscas_seguidas_mais_nova_primeiro(self):
        with vagas.TravaBusca("pagina") as t:
            t.situacao = "concluida"
        with vagas.TravaBusca("terminal") as t:
            t.situacao = "falha"
        hist = vagas.ler_historico()
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]["origem"], "terminal")
        self.assertEqual(hist[0]["situacao"], "falha")
        self.assertEqual(hist[1]["origem"], "pagina")
        self.assertEqual(hist[1]["situacao"], "concluida")
        for item in hist:
            self.assertEqual(set(item.keys()), {"origem", "inicio", "fim", "situacao"})

    def test_limite_de_vinte_buscas(self):
        for i in range(25):
            with vagas.TravaBusca(f"origem-{i}"):
                pass
        hist = vagas.ler_historico()
        self.assertEqual(len(hist), 20)
        self.assertEqual(hist[0]["origem"], "origem-24")
        self.assertEqual(hist[-1]["origem"], "origem-5")

    def test_arquivo_ausente_ou_quebrado(self):
        self.assertEqual(vagas.ler_historico(), [])
        self.cache.mkdir(parents=True, exist_ok=True)
        (self.cache / "buscas-historico.json").write_text("{quebrado", encoding="utf-8")
        self.assertEqual(vagas.ler_historico(), [])
        (self.cache / "buscas-historico.json").write_text('{"nao": "lista"}', encoding="utf-8")
        self.assertEqual(vagas.ler_historico(), [])


class TestDecidirAgendada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / ".cache"
        self.arq_estado = self.cache / "agendamento.json"
        self.patches = [
            mock.patch.object(agendamento, "CACHE", self.cache),
            mock.patch.object(agendamento, "ARQ_ESTADO", self.arq_estado),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(self._limpar)

    def _limpar(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_horario_e_tolerancia(self):
        ag = {"ligado": True, "horario": "08:00"}
        estado = {}
        hist = []
        agora_800 = datetime(2026, 11, 28, 8, 0)
        agora_815 = datetime(2026, 11, 28, 8, 15)
        agora_816 = datetime(2026, 11, 28, 8, 16)
        agora_759 = datetime(2026, 11, 28, 7, 59)
        self.assertEqual(agendamento.decidir_agendada(ag, agora_800, estado, hist), ("rodar", None))
        self.assertEqual(agendamento.decidir_agendada(ag, agora_815, estado, hist), ("rodar", None))
        self.assertEqual(
            agendamento.decidir_agendada(ag, agora_816, estado, hist),
            ("perdida", "o dashboard não estava ligado às 08:00"),
        )
        self.assertEqual(agendamento.decidir_agendada(ag, agora_759, estado, hist), (None, None))

    def test_desligado(self):
        ag = {"ligado": False, "horario": "08:00"}
        agora = datetime(2026, 11, 28, 8, 0)
        self.assertEqual(agendamento.decidir_agendada(ag, agora, {}, []), (None, None))

    def test_dia_ja_registrado(self):
        estado = {"dia": "2026-11-28", "historico": []}
        ag = {"ligado": True, "horario": "08:00"}
        agora = datetime(2026, 11, 28, 8, 0)
        self.assertEqual(agendamento.decidir_agendada(ag, agora, estado, []), (None, None))
        # Mesmo depois de mudar o horário para mais tarde no mesmo dia
        ag_tarde = {"ligado": True, "horario": "10:00"}
        agora_tarde = datetime(2026, 11, 28, 10, 0)
        self.assertEqual(agendamento.decidir_agendada(ag_tarde, agora_tarde, estado, []), (None, None))

    def test_manual_recente(self):
        ag = {"ligado": True, "horario": "08:00"}
        agora = datetime(2026, 11, 28, 8, 0)

        # manual concluída às 07:30 -> "pulada" com "07:30"
        hist_concluida = [{"origem": "pagina", "inicio": "2026-11-28T07:30:00", "situacao": "concluida"}]
        decisao, motivo = agendamento.decidir_agendada(ag, agora, {}, hist_concluida)
        self.assertEqual(decisao, "pulada")
        self.assertIn("07:30", motivo)
        self.assertEqual(motivo, "busca manual às 07:30")

        # manual às 03:00 -> "rodar" (mais de 4h antes)
        hist_3h = [{"origem": "pagina", "inicio": "2026-11-28T03:00:00", "situacao": "concluida"}]
        self.assertEqual(agendamento.decidir_agendada(ag, agora, {}, hist_3h), ("rodar", None))

        # manual cancelada às 07:30 -> "rodar"
        hist_cancelada = [{"origem": "pagina", "inicio": "2026-11-28T07:30:00", "situacao": "cancelada"}]
        self.assertEqual(agendamento.decidir_agendada(ag, agora, {}, hist_cancelada), ("rodar", None))

        # manual rodando desde 07:55 -> "pulada"
        hist_rodando = [{"origem": "terminal", "inicio": "2026-11-28T07:55:00", "situacao": "rodando"}]
        decisao, motivo = agendamento.decidir_agendada(ag, agora, {}, hist_rodando)
        self.assertEqual(decisao, "pulada")
        self.assertIn("07:55", motivo)

        # busca de origem "retomada" às 07:30 -> "rodar" (não é origem manual)
        hist_retomada = [{"origem": "retomada", "inicio": "2026-11-28T07:30:00", "situacao": "concluida"}]
        self.assertEqual(agendamento.decidir_agendada(ag, agora, {}, hist_retomada), ("rodar", None))

    def test_proxima_agendada(self):
        ag = {"ligado": True, "horario": "08:00"}
        # às 07:00 -> hoje 08:00
        agora_7 = datetime(2026, 11, 28, 7, 0)
        self.assertEqual(agendamento.proxima_agendada(ag, agora_7, {}), "2026-11-28T08:00")

        # às 09:00 -> amanhã 08:00
        agora_9 = datetime(2026, 11, 28, 9, 0)
        self.assertEqual(agendamento.proxima_agendada(ag, agora_9, {}), "2026-11-29T08:00")

        # com o dia registrado às 08:05 -> amanhã
        agora_805 = datetime(2026, 11, 28, 8, 5)
        estado_registrado = {"dia": "2026-11-28"}
        self.assertEqual(agendamento.proxima_agendada(ag, agora_805, estado_registrado), "2026-11-29T08:00")

        # desligado -> None
        self.assertIsNone(agendamento.proxima_agendada({"ligado": False, "horario": "08:00"}, agora_7, {}))

    def test_registrar_evento_limite_trinta(self):
        estado = {"dia": None, "historico": []}
        for i in range(35):
            estado = agendamento.registrar_evento(estado, {"idx": i})
        self.assertEqual(len(estado["historico"]), 30)
        self.assertEqual(estado["historico"][0]["idx"], 34)
        self.assertEqual(estado["historico"][-1]["idx"], 5)

        estado = agendamento.registrar_evento(estado, {"novo": True}, dia="2026-11-28")
        self.assertEqual(estado["dia"], "2026-11-28")
        self.assertEqual(estado["historico"][0]["novo"], True)

    def test_estado_em_disco(self):
        # Ausente -> padrão
        self.assertEqual(agendamento.ler_estado(), {"dia": None, "historico": []})

        # Quebrado -> padrão
        self.cache.mkdir(parents=True, exist_ok=True)
        self.arq_estado.write_text("{quebrado", encoding="utf-8")
        self.assertEqual(agendamento.ler_estado(), {"dia": None, "historico": []})

        # Gravar e ler atômico
        estado = {"dia": "2026-11-28", "historico": [{"tipo": "agendada", "situacao": "rodou"}]}
        agendamento.gravar_estado(estado)
        self.assertEqual(agendamento.ler_estado(), estado)

    def test_sem_datetime_now(self):
        with mock.patch("agendamento.datetime") as m_dt:
            m_dt.fromisoformat = datetime.fromisoformat
            m_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            ag = {"ligado": True, "horario": "08:00"}
            agora = datetime(2026, 11, 28, 8, 0)
            agendamento.decidir_agendada(ag, agora, {}, [])
            agendamento.manual_recente([], agora)
            agendamento.proxima_agendada(ag, agora, {})
            m_dt.now.assert_not_called()


if __name__ == "__main__":
    unittest.main()
