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


if __name__ == "__main__":
    unittest.main()
