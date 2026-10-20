"""Front novo (spec 022): o servidor entrega os arquivos de dash/front/ em /novo/, só os da pasta e só os tipos
conhecidos, e avisa quando o front ainda não foi montado. Sem rede: uma pasta temporária faz o papel de dash/front/."""
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

    def test_entrega_index_e_arquivos(self):
        status, tipo, _, corpo = self.pedir("/novo/")
        self.assertEqual((status, tipo), (200, "text/html; charset=utf-8"))
        self.assertIn(b"root", corpo)
        status, tipo, _, corpo = self.pedir("/novo/assets/app.js")
        self.assertEqual((status, tipo, corpo), (200, "text/javascript; charset=utf-8", b"console.log(1)"))

    def test_sem_barra_redireciona(self):
        status, _, local, _ = self.pedir("/novo")
        self.assertEqual((status, local), (308, "/novo/"))

    def test_recusa_fora_da_pasta_e_tipo_desconhecido(self):
        for caminho in ("/novo/../segredo.html", "/novo/%2e%2e/segredo.html", "/novo/..%5csegredo.html",
                        "/novo/ORIGEM.json", "/novo/assets/nao-existe.js"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.pedir(caminho)[0], 404)

    def test_front_nao_montado(self):
        shutil.rmtree(self.front)
        status, tipo, _, corpo = self.pedir("/novo/")
        self.assertEqual((status, tipo), (404, "text/html; charset=utf-8"))
        self.assertIn("ainda não foi montado", corpo.decode("utf-8"))

    def test_dashboard_atual_continua_em_raiz(self):
        status, tipo, _, corpo = self.pedir("/")
        self.assertEqual((status, tipo), (200, "text/html; charset=utf-8"))
        self.assertEqual(corpo, servidor.PAGINA.read_bytes())


if __name__ == "__main__":
    unittest.main()
