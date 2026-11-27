"""Busca agendada e retomada depois da espera (spec 064): configuração, regras do relógio, retomadas e integração.
Config, cache e banco numa pasta temporária; portais e relógio falsos."""
import contextlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(RAIZ / "tests")]
import filtros  # noqa: E402
import banco  # noqa: E402
import vagas  # noqa: E402
import agendamento  # noqa: E402
import agendador  # noqa: E402
import buscador  # noqa: E402
from test_busca import Base as BaseBusca  # noqa: E402


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


class TestAgendador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        (raiz / "config.json").write_text(json.dumps(
            {"termos": ["analista"], "agendamento": {"ligado": True, "horario": "08:00"}}), encoding="utf-8")
        self.iniciar = mock.Mock()
        self.patches = [
            mock.patch.object(filtros, "CONFIG", raiz / "config.json"),
            mock.patch.object(vagas, "CACHE", raiz / ".cache"),
            mock.patch.object(agendamento, "CACHE", raiz / ".cache"),
            mock.patch.object(agendamento, "ARQ_ESTADO", raiz / ".cache" / "agendamento.json"),
            mock.patch.object(agendamento, "ARQ_RETOMADAS", raiz / ".cache" / "retomadas.json"),
            mock.patch.object(buscador.BUSCA, "iniciar", self.iniciar),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)
        self.ag = agendador.Agendador()
        self.livre = mock.patch.object(agendador.Agendador, "ocupado", return_value=False)
        self.livre.start()
        self.addCleanup(self.livre.stop)

    def situacoes(self):
        return [e["situacao"] for e in agendamento.ler_estado()["historico"]]

    def test_inicia_uma_vez_com_origem_agendada(self):
        self.ag.tick(datetime(2026, 11, 28, 8, 0))
        self.iniciar.assert_called_once_with(origem="agendada")
        self.assertEqual(self.situacoes(), ["rodou"])
        self.ag.tick(datetime(2026, 11, 28, 8, 1))
        self.iniciar.assert_called_once()

    def test_ocupado_espera_e_roda_depois_da_tolerancia(self):
        with mock.patch.object(agendador.Agendador, "ocupado", return_value=True):
            self.ag.tick(datetime(2026, 11, 28, 8, 0))
            self.ag.tick(datetime(2026, 11, 28, 8, 20))
        self.iniciar.assert_not_called()
        self.assertEqual(self.situacoes(), [])
        self.ag.tick(datetime(2026, 11, 28, 8, 40))
        self.iniciar.assert_called_once_with(origem="agendada")
        self.assertEqual(self.situacoes(), ["rodou"])

    def test_janela_nao_vista_e_perdida(self):
        self.ag.tick(datetime(2026, 11, 28, 8, 20))
        self.iniciar.assert_not_called()
        self.assertEqual(self.situacoes(), ["perdida"])

    def test_manual_recente_pula(self):
        hist = [{"origem": "pagina", "situacao": "concluida", "inicio": "2026-11-28T07:30:00"}]
        with mock.patch.object(vagas, "ler_historico", return_value=hist):
            self.ag.tick(datetime(2026, 11, 28, 8, 0))
        self.iniciar.assert_not_called()
        self.assertEqual(self.situacoes(), ["pulada"])

    def test_recusa_vira_falha(self):
        self.iniciar.side_effect = buscador.BuscaRecusada("sem portais")
        self.ag.tick(datetime(2026, 11, 28, 8, 0))
        e = agendamento.ler_estado()["historico"][0]
        self.assertEqual((e["situacao"], e["motivo"]), ("falha", "sem portais"))
        self.ag.tick(datetime(2026, 11, 28, 8, 1))
        self.iniciar.assert_called_once()


class TestBuscaAgendada(BaseBusca):
    def test_ignora_intervalo_e_grava_a_origem(self):
        fim = (datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds")
        vagas._gravar_registro({"origem": "pagina", "situacao": "concluida", "fim": fim})
        with self.assertRaises(buscador.BuscaRecusada):
            buscador.Busca().iniciar()  # na página, o intervalo mínimo recusa
        b = buscador.Busca()
        b.iniciar(origem="agendada")
        b._thread.join(20)
        self.assertEqual(b.estado()["situacao"], "concluida", b.estado())
        self.assertEqual(vagas.ultima()["origem"], "agendada")
        self.assertEqual(banco.ultima_busca()["origem"], "agendada")


class TestRetomadas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / ".cache"
        self.arq_retomadas = self.cache / "retomadas.json"
        self.patches = [
            mock.patch.object(agendamento, "CACHE", self.cache),
            mock.patch.object(agendamento, "ARQ_RETOMADAS", self.arq_retomadas),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(self._limpar)

    def _limpar(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_bloqueio_cria_retomada(self):
        agora = datetime(2026, 11, 28, 8, 0)
        resultado = {
            "rodaram": ["linkedin"],
            "bloqueados": ["linkedin"],
            "faltaram": {"linkedin": [{"termo": "analista"}]},
        }
        res = agendamento.depois_da_busca(
            retomadas={},
            resultado=resultado,
            origem="pagina",
            agora=agora,
            continuar=True,
            rotulo=lambda n: "LinkedIn",
            pendentes=lambda n: 0,
        )
        self.assertIn("linkedin", res)
        self.assertEqual(res["linkedin"]["portal"], "LinkedIn")
        self.assertEqual(res["linkedin"]["origem_busca"], "pagina")
        self.assertEqual(res["linkedin"]["criada_em"], "2026-11-28T08:00")
        self.assertEqual(res["linkedin"]["proxima"], "2026-11-28T14:00")
        self.assertEqual(res["linkedin"]["faltaram"], [{"termo": "analista"}])
        self.assertEqual(res["linkedin"]["tentativas"], 0)

    def test_retomada_que_bloqueia_de_novo(self):
        agora = datetime(2026, 11, 28, 14, 0)
        anterior = {
            "linkedin": {
                "portal": "LinkedIn",
                "origem_busca": "pagina",
                "criada_em": "2026-11-28T08:00",
                "proxima": "2026-11-28T14:00",
                "faltaram": [{"termo": "analista"}],
                "tentativas": 0,
            }
        }
        resultado = {
            "rodaram": ["linkedin"],
            "bloqueados": ["linkedin"],
            "faltaram": {"linkedin": [{"termo": "analista"}]},
        }
        res = agendamento.depois_da_busca(
            retomadas=anterior,
            resultado=resultado,
            origem="retomada",
            agora=agora,
            continuar=True,
            rotulo=lambda n: "LinkedIn",
            pendentes=lambda n: 0,
        )
        self.assertEqual(res["linkedin"]["tentativas"], 1)
        self.assertEqual(res["linkedin"]["criada_em"], "2026-11-28T08:00")
        self.assertEqual(res["linkedin"]["origem_busca"], "pagina")
        self.assertEqual(res["linkedin"]["proxima"], "2026-11-28T20:00")

    def test_retomada_sem_bloqueio_e_sem_pendentes_some(self):
        agora = datetime(2026, 11, 28, 14, 0)
        anterior = {
            "linkedin": {
                "portal": "LinkedIn",
                "origem_busca": "pagina",
                "criada_em": "2026-11-28T08:00",
                "proxima": "2026-11-28T14:00",
                "faltaram": [{"termo": "analista"}],
                "tentativas": 0,
            }
        }
        resultado = {"rodaram": ["linkedin"], "bloqueados": [], "faltaram": {}}
        res = agendamento.depois_da_busca(
            retomadas=anterior,
            resultado=resultado,
            origem="retomada",
            agora=agora,
            continuar=True,
            rotulo=lambda n: "LinkedIn",
            pendentes=lambda n: 0,
        )
        self.assertEqual(res, {})

    def test_retomada_sem_bloqueio_com_pendentes_fica_com_faltaram_vazio(self):
        agora = datetime(2026, 11, 28, 14, 0)
        anterior = {
            "linkedin": {
                "portal": "LinkedIn",
                "origem_busca": "pagina",
                "criada_em": "2026-11-28T08:00",
                "proxima": "2026-11-28T14:00",
                "faltaram": [{"termo": "analista"}],
                "tentativas": 0,
            }
        }
        resultado = {"rodaram": ["linkedin"], "bloqueados": [], "faltaram": {}}
        res = agendamento.depois_da_busca(
            retomadas=anterior,
            resultado=resultado,
            origem="retomada",
            agora=agora,
            continuar=True,
            rotulo=lambda n: "LinkedIn",
            pendentes=lambda n: 5,
        )
        self.assertIn("linkedin", res)
        self.assertEqual(res["linkedin"]["faltaram"], [])
        self.assertEqual(res["linkedin"]["proxima"], "2026-11-28T20:00")
        self.assertEqual(res["linkedin"]["tentativas"], 1)
        self.assertEqual(res["linkedin"]["criada_em"], "2026-11-28T08:00")

    def test_busca_agendada_apaga_outras_e_cria_so_as_dela(self):
        agora = datetime(2026, 11, 28, 8, 0)
        anteriores = {
            "linkedin": {"portal": "LinkedIn", "criada_em": "2026-11-27T10:00", "proxima": "2026-11-27T16:00"},
            "gupy": {"portal": "Gupy", "criada_em": "2026-11-27T10:00", "proxima": "2026-11-27T16:00"},
        }
        resultado = {
            "rodaram": ["infojobs"],
            "bloqueados": ["infojobs"],
            "faltaram": {"infojobs": [{"termo": "python"}]},
        }
        res = agendamento.depois_da_busca(
            retomadas=anteriores,
            resultado=resultado,
            origem="agendada",
            agora=agora,
            continuar=True,
            rotulo=lambda n: "InfoJobs",
            pendentes=lambda n: 0,
        )
        self.assertEqual(list(res.keys()), ["infojobs"])
        self.assertEqual(res["infojobs"]["origem_busca"], "agendada")
        self.assertEqual(res["infojobs"]["tentativas"], 0)

    def test_continuar_falso_devolve_vazio(self):
        anteriores = {
            "linkedin": {"portal": "LinkedIn"},
        }
        resultado = {
            "rodaram": ["linkedin"],
            "bloqueados": ["linkedin"],
            "faltaram": {"linkedin": [{"termo": "dev"}]},
        }
        res = agendamento.depois_da_busca(
            retomadas=anteriores,
            resultado=resultado,
            origem="pagina",
            agora=datetime(2026, 11, 28, 8, 0),
            continuar=False,
            rotulo=lambda n: "LinkedIn",
            pendentes=lambda n: 0,
        )
        self.assertEqual(res, {})

    def test_portal_em_espera_fora_de_rodaram_nao_muda(self):
        anteriores = {
            "infojobs": {
                "portal": "InfoJobs",
                "origem_busca": "pagina",
                "criada_em": "2026-11-28T02:00",
                "proxima": "2026-11-28T08:00",
                "faltaram": [{"termo": "dev"}],
                "tentativas": 0,
            }
        }
        resultado = {"rodaram": ["gupy"], "bloqueados": [], "faltaram": {}}
        res = agendamento.depois_da_busca(
            retomadas=anteriores,
            resultado=resultado,
            origem="pagina",
            agora=datetime(2026, 11, 28, 8, 0),
            continuar=True,
            rotulo=lambda n: n.capitalize(),
            pendentes=lambda n: 0,
        )
        self.assertIn("infojobs", res)
        self.assertEqual(res["infojobs"], anteriores["infojobs"])

    def test_devida_na_hora(self):
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-28T08:00",
                "proxima": "2026-11-28T14:00",
            }
        }
        agora = datetime(2026, 11, 28, 14, 0)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: False
        )
        self.assertEqual(devidas, ["linkedin"])
        self.assertEqual(atualizadas, retomadas)
        self.assertEqual(eventos, [])

    def test_pulada_com_portal_em_espera(self):
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-28T08:00",
                "proxima": "2026-11-28T14:00",
            }
        }
        agora = datetime(2026, 11, 28, 14, 0)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: True
        )
        self.assertEqual(devidas, [])
        self.assertEqual(atualizadas["linkedin"]["proxima"], "2026-11-28T20:00")
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["tipo"], "retomada")
        self.assertEqual(eventos[0]["portal"], "LinkedIn")
        self.assertEqual(eventos[0]["situacao"], "pulada")
        self.assertEqual(eventos[0]["motivo"], "o portal ainda está em espera")
        self.assertEqual(eventos[0]["em"], "2026-11-28T14:00:00")

    def test_perdida_proxima_02_e_tick_as_09(self):
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-27T20:00",
                "proxima": "2026-11-28T02:00",
            }
        }
        agora = datetime(2026, 11, 28, 9, 0)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: False
        )
        self.assertEqual(devidas, [])
        self.assertEqual(atualizadas["linkedin"]["proxima"], "2026-11-28T14:00")
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["situacao"], "perdida")
        self.assertEqual(eventos[0]["motivo"], "o dashboard não estava ligado às 02:00")

    def test_perdida_tick_as_08_10_fica_devida(self):
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-27T20:00",
                "proxima": "2026-11-28T02:00",
            }
        }
        agora = datetime(2026, 11, 28, 8, 10)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: False
        )
        self.assertEqual(devidas, ["linkedin"])
        self.assertEqual(atualizadas["linkedin"]["proxima"], "2026-11-28T08:00")
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["situacao"], "perdida")
        self.assertEqual(eventos[0]["motivo"], "o dashboard não estava ligado às 02:00")

    def test_teto_24_horas_sem_agendamento_ligado(self):
        ag = {"ligado": False, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-27T08:00",
                "proxima": "2026-11-28T08:00",
            }
        }
        agora = datetime(2026, 11, 28, 8, 0)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: False
        )
        self.assertEqual(devidas, [])
        self.assertEqual(atualizadas, {})
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["tipo"], "retomada")
        self.assertEqual(eventos[0]["portal"], "LinkedIn")
        self.assertEqual(eventos[0]["situacao"], "encerrada")
        self.assertEqual(eventos[0]["motivo"], "24 horas sem busca agendada")
        self.assertEqual(eventos[0]["em"], "2026-11-28T08:00:00")

    def test_com_agendamento_ligado_nao_ha_teto(self):
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        retomadas = {
            "linkedin": {
                "portal": "LinkedIn",
                "criada_em": "2026-11-20T08:00",
                "proxima": "2026-11-28T08:00",
            }
        }
        agora = datetime(2026, 11, 28, 8, 0)
        devidas, atualizadas, eventos = agendamento.retomadas_devidas(
            retomadas, agora, ag, em_espera=lambda n: False
        )
        self.assertEqual(devidas, ["linkedin"])
        self.assertIn("linkedin", atualizadas)
        self.assertEqual(eventos, [])

    def test_cancelar_retomada_e_arquivo_quebrado(self):
        self.assertEqual(agendamento.ler_retomadas(), {})

        dados = {"linkedin": {"portal": "LinkedIn"}}
        agendamento.gravar_retomadas(dados)
        self.assertEqual(agendamento.ler_retomadas(), dados)

        self.assertTrue(agendamento.cancelar_retomada("linkedin"))
        self.assertEqual(agendamento.ler_retomadas(), {})
        self.assertFalse(agendamento.cancelar_retomada("linkedin"))

        agendamento.gravar_retomadas(dados)
        agendamento.apagar_retomadas()
        self.assertEqual(agendamento.ler_retomadas(), {})

        self.cache.mkdir(parents=True, exist_ok=True)
        self.arq_retomadas.write_text("{quebrado", encoding="utf-8")
        self.assertEqual(agendamento.ler_retomadas(), {})

        self.arq_retomadas.write_text("[1, 2, 3]", encoding="utf-8")
        self.assertEqual(agendamento.ler_retomadas(), {})

    def test_sem_datetime_now_retomadas(self):
        with mock.patch("agendamento.datetime") as m_dt:
            m_dt.fromisoformat = datetime.fromisoformat
            m_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            agora = datetime(2026, 11, 28, 8, 0)
            ag = {"ligado": True, "horario": "08:00", "continuar": True}
            retomadas = {
                "linkedin": {
                    "portal": "LinkedIn",
                    "criada_em": "2026-11-28T02:00",
                    "proxima": "2026-11-28T08:00",
                }
            }
            agendamento.depois_da_busca(
                retomadas={},
                resultado={"rodaram": ["linkedin"], "bloqueados": ["linkedin"], "faltaram": {}},
                origem="pagina",
                agora=agora,
                continuar=True,
                rotulo=lambda n: "LinkedIn",
                pendentes=lambda n: 0,
            )
            agendamento.retomadas_devidas(retomadas, agora, ag, em_espera=lambda n: False)
            m_dt.now.assert_not_called()



class TestRetomadasRobustas(unittest.TestCase):
    def test_perdida_que_cai_na_hora_com_portal_em_espera_vai_para_depois(self):
        from datetime import datetime
        import agendamento
        r = {"falsa": {"portal": "Falsa", "criada_em": "2026-11-27T02:00", "proxima": "2026-11-27T02:00",
                       "faltaram": [], "tentativas": 0}}
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        devidas, novas, _ = agendamento.retomadas_devidas(r, datetime(2026, 11, 27, 8, 10), ag, lambda n: True)
        self.assertEqual(devidas, [])
        self.assertEqual(novas["falsa"]["proxima"], "2026-11-27T14:00")

    def test_data_quebrada_sai_sem_erro(self):
        from datetime import datetime
        import agendamento
        r = {"falsa": {"portal": "Falsa", "criada_em": None, "proxima": "x"}}
        ag = {"ligado": True, "horario": "08:00", "continuar": True}
        self.assertEqual(agendamento.retomadas_devidas(r, datetime(2026, 11, 27, 8, 0), ag, lambda n: False)[:2],
                         ([], {}))


class PortalComVaga(PortalFalso):
    """Devolve uma vaga por consulta, até bloquear: a busca que bloqueia no meio ainda vale (não é bloqueio provável)."""

    def buscar(self, consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
        vagas_, erros = super().buscar(consulta, horas, por_termo)
        if erros:
            return vagas_, erros
        termo = consulta["termo"]
        return [{"id": f"falsa-{termo}", "titulo": f"Analista {termo}", "empresa": f"Empresa {termo}", "local": "Remoto",
                 "remoto": True, "publicada_em": datetime.now().date().isoformat(), "url": f"https://exemplo.invalid/{termo}",
                 "url_candidatura": None, "salario": None, "tipo": None, "descricao": f"Descrição {termo}.",
                 "plataforma": "Falsa"}], []


class TestRetomadaPontaAPonta(BaseBusca):
    CONFIG = {"fontes": ["falsa"], "termos": ["c1", "c2", "c3", "c4", "c5"],
              "modelos": {"remoto": True, "hibrido": False, "presencial": False}, "empresas_excluir": [],
              "janela_horas": 168, "ia": {"provedor": "nenhum"}, "agendamento": {"continuar": True}}

    def setUp(self):
        super().setUp()
        (self.tmp / "config.json").write_text(json.dumps(self.CONFIG), encoding="utf-8")
        cache = self.tmp / ".cache"
        self.busca = buscador.Busca()
        for p in (mock.patch.object(agendamento, "CACHE", cache),
                  mock.patch.object(agendamento, "ARQ_ESTADO", cache / "agendamento.json"),
                  mock.patch.object(agendamento, "ARQ_RETOMADAS", cache / "retomadas.json"),
                  mock.patch.object(buscador, "BUSCA", self.busca),
                  mock.patch.object(agendador.Agendador, "ocupado", lambda self_: self.busca.rodando())):
            p.start()
            self.addCleanup(p.stop)
        self.ag = agendador.Agendador()

    def portal(self, classe=PortalComVaga, **kw):
        portal = classe(**kw)
        p = mock.patch.dict(vagas.FONTES, {"falsa": portal})
        p.start()
        self.addCleanup(p.stop)
        return portal

    def tick_seis_horas_depois(self):
        self.ag.tick(datetime.now() + timedelta(hours=6, minutes=1))
        if self.busca._thread is not None:
            self.busca._thread.join(20)

    def busca_bloqueada(self, portal):
        self.busca.iniciar()
        self.busca._thread.join(20)
        self.busca._thread = None
        return self.busca.estado()

    def test_bloqueio_grava_as_consultas_que_faltam_e_o_tick_retoma(self):
        portal = self.portal(bloqueia_em=3)
        estado = self.busca_bloqueada(portal)
        self.assertEqual(estado["situacao"], "concluida", estado)
        self.assertEqual(estado["resumo"]["bloqueados"], ["Falsa"])
        self.assertTrue(estado["resumo"]["retomada_as"])
        ret = agendamento.ler_retomadas()["falsa"]
        self.assertEqual([c["termo"] for c in ret["faltaram"]], ["c3", "c4", "c5"])

        portal.chamadas.clear()
        portal._bloqueado, portal.bloqueia_em = False, None
        self.tick_seis_horas_depois()
        self.assertEqual([c["termo"] for c in portal.chamadas], ["c3", "c4", "c5"])
        self.assertEqual(self.busca.estado()["retomada"], {"nome": "falsa", "portal": "Falsa"})
        self.assertEqual(agendamento.ler_retomadas(), {})
        self.assertEqual(agendamento.ler_estado()["historico"][0]["situacao"], "rodou")

    def test_retomada_que_bloqueia_de_novo_continua(self):
        portal = self.portal(bloqueia_em=3)
        self.busca_bloqueada(portal)
        portal.chamadas.clear()
        portal._bloqueado, portal.bloqueia_em = False, 2
        self.tick_seis_horas_depois()
        self.assertEqual([c["termo"] for c in portal.chamadas], ["c3", "c4"])
        ret = agendamento.ler_retomadas()["falsa"]
        self.assertEqual([c["termo"] for c in ret["faltaram"]], ["c4", "c5"])
        self.assertEqual(ret["tentativas"], 1)

    def test_portal_em_espera_pula_a_retomada(self):
        portal = self.portal(bloqueia_em=3)
        self.busca_bloqueada(portal)
        antes = agendamento.ler_retomadas()["falsa"]["proxima"]
        portal.chamadas.clear()
        portal._espera = {"ate": "2099-01-01T00:00", "motivo": "teste"}
        self.tick_seis_horas_depois()
        self.assertEqual(portal.chamadas, [])
        depois = agendamento.ler_retomadas()["falsa"]
        self.assertEqual(datetime.fromisoformat(depois["proxima"]) - datetime.fromisoformat(antes), timedelta(hours=6))
        self.assertEqual(len(depois["faltaram"]), 3)
        self.assertEqual(agendamento.ler_estado()["historico"][0]["situacao"], "pulada")

    def test_ocupado_deixa_a_retomada_para_o_proximo_tick(self):
        portal = self.portal(bloqueia_em=3)
        self.busca_bloqueada(portal)
        portal.chamadas.clear()
        portal._bloqueado = False
        with mock.patch.object(agendador.Agendador, "ocupado", return_value=True):
            self.tick_seis_horas_depois()
        self.assertEqual(portal.chamadas, [])
        self.assertIn("falsa", agendamento.ler_retomadas())

    def test_busca_nao_gravada_refaz_todas_as_consultas(self):
        portal = self.portal(PortalFalso, bloqueia_em=3)  # nenhuma vaga e só erros: bloqueio provável, nada gravado
        estado = self.busca_bloqueada(portal)
        self.assertEqual(estado["situacao"], "falha", estado)
        self.assertEqual(estado["resumo"]["bloqueados"], ["Falsa"])
        ret = agendamento.ler_retomadas()["falsa"]
        self.assertEqual([c["termo"] for c in ret["faltaram"]], ["c1", "c2", "c3", "c4", "c5"])

    def test_retomada_sem_registro_e_recusada(self):
        self.portal()
        with self.assertRaises(buscador.BuscaRecusada):
            self.busca.iniciar(origem="retomada", retomada="falsa")


class TestRotasEComando(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.config_arq = self.raiz / "config.json"
        self.config_arq.write_text(json.dumps({
            "termos": ["analista"],
            "fontes": ["falsa"],
            "agendamento": {"ligado": True, "horario": "08:00", "continuar": True}
        }), encoding="utf-8")
        self.cache = self.raiz / ".cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.arq_estado = self.cache / "agendamento.json"
        self.arq_retomadas = self.cache / "retomadas.json"

        import servidor
        self.patches = [
            mock.patch.object(filtros, "CONFIG", self.config_arq),
            mock.patch.object(agendamento, "CACHE", self.cache),
            mock.patch.object(agendamento, "ARQ_ESTADO", self.arq_estado),
            mock.patch.object(agendamento, "ARQ_RETOMADAS", self.arq_retomadas),
            mock.patch.object(banco, "ARQUIVO", self.raiz / "banco.db"),
            mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(self._limpar)

        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        self.thread_srv = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread_srv.start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def _limpar(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        headers = {"Content-Type": "application/json"}
        con.request(metodo, caminho, dados, headers)
        r = con.getresponse()
        return r.status, json.loads(r.read().decode("utf-8"))

    def test_get_devolve_formato_do_contrato(self):
        st, r = self.pedir("GET", "/api/agendamento")
        self.assertEqual(st, 200)
        chaves_esperadas = {"agendamento", "proxima", "hoje", "retomadas", "historico", "aviso_login", "pode_alterar"}
        self.assertTrue(chaves_esperadas.issubset(r.keys()))
        self.assertEqual(r["agendamento"], {"ligado": True, "horario": "08:00", "continuar": True})
        self.assertTrue(r["pode_alterar"])
        self.assertIsInstance(r["retomadas"], list)
        self.assertIsInstance(r["historico"], list)

    def test_put_com_horario_invalido_400(self):
        st, r = self.pedir("PUT", "/api/agendamento", {"horario": "25:00"})
        self.assertEqual(st, 400)
        self.assertIn("erro", r)
        self.assertIn("horário inválido", r["erro"])

    def test_put_continuar_falso_apaga_as_retomadas(self):
        agendamento.gravar_retomadas({
            "falsa": {
                "portal": "Falsa",
                "proxima": "2026-11-27T14:00",
                "faltaram": [],
                "tentativas": 0,
                "criada_em": "2026-11-27T08:00",
                "origem_busca": "agendada"
            }
        })
        self.assertIn("falsa", agendamento.ler_retomadas())

        st, r = self.pedir("PUT", "/api/agendamento", {"continuar": False})
        self.assertEqual(st, 200)
        self.assertFalse(r["agendamento"]["continuar"])
        self.assertEqual(agendamento.ler_retomadas(), {})
        self.assertEqual(r["retomadas"], [])

    def test_delete_retomada_existente_200_e_some(self):
        agendamento.gravar_retomadas({
            "falsa": {
                "portal": "Falsa",
                "proxima": "2026-11-27T14:00",
                "faltaram": [],
                "tentativas": 0,
                "criada_em": "2026-11-27T08:00",
                "origem_busca": "agendada"
            }
        })
        self.assertIn("falsa", agendamento.ler_retomadas())

        st, r = self.pedir("DELETE", "/api/agendamento/retomadas/falsa")
        self.assertEqual(st, 200)
        self.assertNotIn("falsa", agendamento.ler_retomadas())
        self.assertEqual(r["retomadas"], [])

    def test_delete_retomada_inexistente_404(self):
        st, r = self.pedir("DELETE", "/api/agendamento/retomadas/inexistente")
        self.assertEqual(st, 404)
        self.assertEqual(r, {"erro": "não há retomada para este portal"})

    def test_vagas_agendamento_horario_invalido_codigo_2(self):
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["vagas.py", "agendamento", "--ligar", "25:00"]), \
             contextlib.redirect_stderr(err):
            codigo = vagas.main()
        self.assertEqual(codigo, 2)
        self.assertIn("horário inválido", err.getvalue())

    def test_vagas_agendamento_ligar_0730_grava_no_config(self):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["vagas.py", "agendamento", "--ligar", "07:30"]), \
             contextlib.redirect_stdout(out):
            codigo = vagas.main()
        self.assertEqual(codigo, 0)
        cfg = json.loads(self.config_arq.read_text(encoding="utf-8"))
        self.assertEqual(cfg["agendamento"]["horario"], "07:30")
        self.assertTrue(cfg["agendamento"]["ligado"])
        self.assertIn("Busca agendada: ligada às 07:30", out.getvalue())

    def test_vagas_agendamento_sem_opcao_mostra_estado(self):
        agendamento.gravar_retomadas({
            "falsa": {
                "portal": "LinkedIn",
                "proxima": "2026-11-27T14:00",
                "faltaram": [{"termo": "a"}, {"termo": "b"}],
                "tentativas": 0,
                "criada_em": "2026-11-27T08:00",
                "origem_busca": "agendada"
            }
        })
        estado = agendamento.ler_estado()
        agendamento.registrar_evento(estado, {
            "tipo": "agendada", "situacao": "rodou", "em": "2026-11-27T08:00:12", "motivo": None
        })
        agendamento.gravar_estado(estado)

        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["vagas.py", "agendamento"]), \
             contextlib.redirect_stdout(out):
            codigo = vagas.main()
        self.assertEqual(codigo, 0)
        texto = out.getvalue()
        self.assertIn("Busca agendada: ligada às 08:00", texto)
        self.assertIn("Continuar de onde parou: sim", texto)
        self.assertIn("Próxima busca:", texto)
        self.assertIn("LinkedIn: retoma às 14:00, faltam 2 consultas e 0 descrições", texto)
        self.assertIn("Último evento: agendada rodou em 2026-11-27T08:00:12", texto)

    def test_vagas_agendamento_cancelar_retomada(self):
        agendamento.gravar_retomadas({"falsa": {"portal": "Falsa", "proxima": "2026-11-27T14:00"}})
        self.assertIn("falsa", agendamento.ler_retomadas())
        with mock.patch.object(sys, "argv", ["vagas.py", "agendamento", "--cancelar-retomada", "falsa"]), \
             contextlib.redirect_stdout(io.StringIO()):
            codigo = vagas.main()
        self.assertEqual(codigo, 0)
        self.assertNotIn("falsa", agendamento.ler_retomadas())



if __name__ == "__main__":
    unittest.main()
