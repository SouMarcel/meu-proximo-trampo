"""Ocultar vagas de empresas excluídas (spec 055): a regra única (filtros.empresa_excluida), o motivo de Fora dos
critérios igual ao de antes, a marca empresa_excluida em com_kit e em GET /api/vagas. Empresas fictícias."""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402

CFG = {"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
       "empresas_excluir": ["Empresa Beta", "Ômega"]}


def vaga(vid, empresa):
    return {"id": vid, "origem": "busca", "plataforma": "Gupy", "titulo": f"Analista {vid}", "empresa": empresa,
            "url": f"https://exemplo.invalid/{vid}", "triagem": "pendente", "encontrada_em": "2026-11-01"}


class TestRegra(unittest.TestCase):
    def test_empresa_excluida(self):
        lista = ["Empresa Beta", "Ômega", " "]
        self.assertEqual(filtros.empresa_excluida("EMPRESA BETA Ltda.", lista), "Empresa Beta")
        self.assertEqual(filtros.empresa_excluida("Grupo Omega S.A.", lista), "Ômega")
        self.assertIsNone(filtros.empresa_excluida("Empresa Alfa", lista))
        self.assertIsNone(filtros.empresa_excluida(None, lista))
        self.assertIsNone(filtros.empresa_excluida("Empresa Beta", []))

    def test_criterios_mantem_o_motivo(self):
        f = filtros.efetivos(CFG)
        motivos = filtros.criterios({"empresa": "Empresa Beta Ltda.", "titulo": "Analista"}, f)
        self.assertIn("Empresa na sua lista de exclusão (Empresa Beta)", motivos)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)


class TestMarca(Base):
    def test_com_kit(self):
        self.assertTrue(banco.com_kit(vaga("a", "Empresa Beta"), {})["empresa_excluida"])
        self.assertFalse(banco.com_kit(vaga("b", "Empresa Alfa"), {})["empresa_excluida"])
        self.assertFalse(banco.com_kit(vaga("a", "Empresa Beta"), {}, [])["empresa_excluida"])  # lista passada vazia
        self.assertTrue(banco.com_kit(vaga("b", "Empresa Alfa"), {}, ["alfa"])["empresa_excluida"])

    def test_config_ausente(self):
        (self.tmp / "config.json").unlink()
        self.assertFalse(banco.com_kit(vaga("a", "Empresa Beta"), {})["empresa_excluida"])

    def test_marca_nao_e_gravada(self):
        with banco.escrita() as con:
            banco._gravar(con, "a", vaga("a", "Empresa Beta"))
        banco.com_kit(banco.obter("a"), {})
        self.assertNotIn("empresa_excluida", banco.obter("a"))


class TestRota(Base):
    def test_api_vagas(self):
        import servidor
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        with banco.escrita() as con:
            banco._gravar(con, "a", vaga("a", "Empresa Beta"))
            banco._gravar(con, "b", vaga("b", "Empresa Alfa"))
        con = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        con.request("GET", "/api/vagas")
        vagas = {v["id"]: v for v in json.loads(con.getresponse().read())["vagas"]}
        self.assertEqual((vagas["a"]["empresa_excluida"], vagas["b"]["empresa_excluida"]), (True, False))


if __name__ == "__main__":
    unittest.main()
