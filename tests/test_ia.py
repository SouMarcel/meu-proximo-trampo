"""Testes do ia.py (python -m unittest discover -s tests). Sem rede: o ponta a ponta usa um servidor falso local."""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ia  # noqa: E402
import segredos  # noqa: E402

CHAVE = "sk-teste-1234567890abcdef"


class Falso(BaseHTTPRequestHandler):
    """Imita POST /chat/completions; o comportamento vem de Falso.modo."""
    modo = "ok"
    recebidos = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        Falso.recebidos.append({"caminho": self.path, "auth": self.headers.get("Authorization"), "corpo": corpo})
        if Falso.modo == "401":
            return self._json(401, {"error": {"message": "Incorrect API key provided"}})
        if Falso.modo == "eco":
            return self._json(400, {"error": {"message": "chave errada: " + CHAVE}})
        texto = '[{"id": "x", "aderencia": 70}]' if Falso.modo == "ok" else ""
        return self._json(200, {"choices": [{"message": {"role": "assistant", "content": texto}}]})

    def _json(self, status, obj):
        dados = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch_env = mock.patch.object(segredos, "ENV", Path(self.tmp.name) / ".env")
        self.patch_env.start()
        self.ambiente = mock.patch.dict(os.environ, {}, clear=False)
        self.ambiente.start()
        for p in ia.PROVEDORES.values():
            if p["variavel"]:
                os.environ.pop(p["variavel"], None)

    def tearDown(self):
        self.ambiente.stop()
        self.patch_env.stop()
        self.tmp.cleanup()


class Escolha(Base):
    def test_legado(self):
        with mock.patch.object(ia.shutil, "which", return_value="C:/claude.exe"):
            self.assertEqual(ia.escolha_efetiva({})["provedor"], "claude_code")
            self.assertEqual(ia.escolha_efetiva({"analise_automatica": False})["provedor"], "nenhum")
        with mock.patch.object(ia.shutil, "which", return_value=None):
            self.assertEqual(ia.escolha_efetiva({})["provedor"], "nenhum")

    def test_gravada_vence(self):
        cfg = {"analise_automatica": False, "ia": {"provedor": "gemini", "modelo": "m1"}}
        self.assertEqual(ia.escolha_efetiva(cfg), {"provedor": "gemini", "modelo": "m1", "url_base": ""})

    def test_disponivel_exige_chave(self):
        cfg = {"ia": {"provedor": "openai"}}
        self.assertFalse(ia.disponivel(cfg))
        segredos.gravar("OPENAI_API_KEY", CHAVE)
        self.assertTrue(ia.disponivel(cfg))
        self.assertFalse(ia.disponivel({"ia": {"provedor": "nenhum"}}))

    def test_validar(self):
        self.assertEqual(ia.validar_escolha({"provedor": "groq", "url_base": "https://x"})["url_base"], "")
        with self.assertRaises(ValueError):
            ia.validar_escolha({"provedor": "inexistente"})
        with self.assertRaises(ValueError):
            ia.validar_escolha({"provedor": "compativel", "url_base": "ftp://x", "modelo": "m"})
        with self.assertRaises(ValueError):
            ia.validar_escolha({"provedor": "compativel", "url_base": "https://x.dev/v1"})
        ok = ia.validar_escolha({"provedor": "compativel", "url_base": "http://127.0.0.1:9/v1/", "modelo": "m"})
        self.assertEqual(ok["url_base"], "http://127.0.0.1:9/v1")


class Pedidos(Base):
    def test_anthropic(self):
        url, cab, corpo = ia._pedido_anthropic("https://api.anthropic.com/v1", "m", CHAVE, "oi", "sis")
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(cab["x-api-key"], CHAVE)
        self.assertEqual(cab["anthropic-version"], "2023-06-01")
        self.assertEqual(corpo["system"], "sis")
        self.assertEqual(corpo["messages"], [{"role": "user", "content": "oi"}])
        self.assertEqual(ia._texto("anthropic", {"content": [{"type": "text", "text": "ok"}]}), "ok")

    def test_openai(self):
        url, cab, corpo = ia._pedido_openai("https://x/v1/", "m", CHAVE, "oi")
        self.assertEqual(url, "https://x/v1/chat/completions")
        self.assertEqual(cab["Authorization"], "Bearer " + CHAVE)
        self.assertEqual(corpo, {"model": "m", "messages": [{"role": "user", "content": "oi"}]})
        self.assertEqual(ia._texto("openai", {"choices": [{"message": {"content": " ok "}}]}), "ok")
        with self.assertRaises(ia.IAErro):
            ia._texto("openai", {"choices": []})

    def test_motivos(self):
        self.assertIn("chave recusada", ia.motivo_http(401))
        self.assertIn("sem crédito", ia.motivo_http(429, '{"error": {"code": "insufficient_quota"}}'))
        self.assertIn("limite de uso", ia.motivo_http(429, "{}"))
        self.assertIn("'m9'", ia.motivo_http(404, "", "m9"))
        self.assertIn("problema", ia.motivo_http(503))

    def test_mascarar(self):
        segredos.gravar("GEMINI_API_KEY", "AIzaSyTeste1234567890abcdefgh")
        texto = ia.mascarar("erro com AIzaSyTeste1234567890abcdefgh e sk-qualquercoisa123 e extra-9999999", "extra-9999999")
        self.assertNotIn("AIzaSy", texto)
        self.assertNotIn("sk-qualquer", texto)
        self.assertNotIn("extra-9999999", texto)


class PontaAPonta(Base):
    @classmethod
    def setUpClass(cls):
        cls.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.escolha = {"provedor": "compativel", "modelo": "modelo-falso",
                       "url_base": "http://127.0.0.1:%d/v1" % cls.servidor.server_address[1]}

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def setUp(self):
        super().setUp()
        Falso.recebidos = []

    def test_responder_e_testar(self):
        Falso.modo = "ok"
        segredos.gravar("IA_COMPATIVEL_API_KEY", CHAVE)
        self.assertIn('"aderencia": 70', ia.responder("pedido", escolha=self.escolha))
        self.assertEqual(Falso.recebidos[-1]["caminho"], "/v1/chat/completions")
        self.assertEqual(Falso.recebidos[-1]["auth"], "Bearer " + CHAVE)
        self.assertEqual(Falso.recebidos[-1]["corpo"]["model"], "modelo-falso")
        ok, msg = ia.testar(self.escolha)
        self.assertTrue(ok, msg)

    def test_chave_recusada(self):
        Falso.modo = "401"
        ok, msg = ia.testar(self.escolha, chave=CHAVE)
        self.assertFalse(ok)
        self.assertIn("chave recusada", msg)

    def test_chave_ecoada_sai_mascarada(self):
        Falso.modo = "eco"
        with self.assertRaises(ia.IAErro) as erro:
            ia.responder("pedido", escolha=self.escolha, chave=CHAVE)
        self.assertNotIn(CHAVE, str(erro.exception))

    def test_resposta_vazia(self):
        Falso.modo = "vazio"
        with self.assertRaises(ia.IAErro) as erro:
            ia.responder("pedido", escolha=self.escolha, chave=CHAVE)
        self.assertIn("vazia", str(erro.exception))

    def test_sem_ia_nao_chama_ninguem(self):
        with self.assertRaises(ia.IAErro):
            ia.responder("pedido", escolha={"provedor": "nenhum", "modelo": "", "url_base": ""})
        self.assertEqual(Falso.recebidos, [])

    def test_sem_conexao(self):
        ok, msg = ia.testar({"provedor": "compativel", "modelo": "m", "url_base": "http://127.0.0.1:9/v1"}, chave=CHAVE)
        self.assertFalse(ok)
        self.assertIn("conexão", msg)


if __name__ == "__main__":
    unittest.main()
