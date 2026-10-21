"""A página (specs 022 e 025): o servidor entrega os arquivos de dash/front/ em /, só os da pasta e só os tipos
conhecidos, leva o endereço antigo /novo/ para a raiz e avisa quando a página ainda não foi montada. Sem rede: uma
pasta temporária faz o papel de dash/front/."""
import http.client
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import servidor  # noqa: E402


class TestFrontEstatico(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.front = self.tmp / "front"
        (self.front / "assets").mkdir(parents=True)
        (self.front / "index.html").write_text("<!doctype html><div id='root'></div>", encoding="utf-8")
        (self.front / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
        (self.front / "favicon.svg").write_text("<svg/>", encoding="utf-8")
        (self.front / "ORIGEM.json").write_text("{}", encoding="utf-8")
        (self.tmp / "segredo.html").write_text("fora da pasta", encoding="utf-8")
        for p in (mock.patch.object(servidor, "FRONT", self.front),
                  mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, caminho):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        con.request("GET", caminho)
        r = con.getresponse()
        return r.status, r.getheader("Content-Type"), r.getheader("Location"), r.read()

    def test_entrega_index_e_arquivos_na_raiz(self):
        for caminho in ("/", "/index.html"):
            with self.subTest(caminho=caminho):
                status, tipo, _, corpo = self.pedir(caminho)
                self.assertEqual((status, tipo), (200, "text/html; charset=utf-8"))
                self.assertIn(b"root", corpo)
        status, tipo, _, corpo = self.pedir("/assets/app.js")
        self.assertEqual((status, tipo, corpo), (200, "text/javascript; charset=utf-8", b"console.log(1)"))
        self.assertEqual(self.pedir("/favicon.svg")[:2], (200, "image/svg+xml"))

    def test_endereco_antigo_leva_para_a_raiz(self):
        for caminho, destino in (("/novo", "/"), ("/novo/", "/"), ("/novo/assets/app.js", "/assets/app.js")):
            with self.subTest(caminho=caminho):
                status, _, local, _ = self.pedir(caminho)
                self.assertEqual((status, local), (308, destino))

    def test_recusa_fora_da_pasta_e_tipo_desconhecido(self):
        for caminho in ("/../segredo.html", "/%2e%2e/segredo.html", "/..%5csegredo.html",
                        "/ORIGEM.json", "/assets/nao-existe.js", "/dashboard.html"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.pedir(caminho)[0], 404)

    def test_api_desconhecida_continua_json(self):
        status, tipo, _, _ = self.pedir("/api/nao-existe")
        self.assertEqual((status, tipo), (404, "application/json; charset=utf-8"))

    def test_front_nao_montado(self):
        shutil.rmtree(self.front)
        status, tipo, _, corpo = self.pedir("/")
        self.assertEqual((status, tipo), (404, "text/html; charset=utf-8"))
        self.assertIn("ainda não foi montada", corpo.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
