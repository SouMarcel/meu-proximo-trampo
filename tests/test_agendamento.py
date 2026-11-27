"""Busca agendada e retomada depois da espera (spec 064): configuração, regras do relógio, retomadas e integração.
Config, cache e banco numa pasta temporária; portais e relógio falsos."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402
import banco  # noqa: E402
import vagas  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
