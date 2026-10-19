"""Navegador da ferramenta (navegador.py, spec 018): quadros do WebSocket e a procura do Edge/Chrome, sem abrir
navegador nenhum."""
import io
import struct
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import navegador  # noqa: E402


class TestQuadros(unittest.TestCase):
    def ida_e_volta(self, texto):
        buf = io.BytesIO(navegador.quadro(texto))
        opcode, final, dados = navegador.ler_quadro(buf.read)
        self.assertEqual((opcode, final), (1, True))
        return dados.decode("utf-8")

    def test_tamanhos(self):  # comprimento em 7 bits, 16 bits (126) e 64 bits (127)
        for n in (0, 5, 125, 126, 200, 65535, 70000):
            self.assertEqual(self.ida_e_volta("x" * n), "x" * n)

    def test_acentos_e_mascara(self):
        texto = '{"método": "Runtime.evaluate", "ç": "ã"}'
        q = navegador.quadro(texto, b"\x01\x02\x03\x04")
        self.assertEqual(q[1] & 0x80, 0x80)  # cliente sempre manda com máscara
        self.assertNotIn(texto.encode("utf-8"), q)
        self.assertEqual(self.ida_e_volta(texto), texto)

    def test_quadro_do_servidor_sem_mascara(self):
        dados = b'{"id":1,"result":{}}'
        buf = io.BytesIO(struct.pack("!BB", 0x81, len(dados)) + dados)
        self.assertEqual(navegador.ler_quadro(buf.read), (1, True, dados))

    def test_quadro_grande_demais(self):
        buf = io.BytesIO(struct.pack("!BBQ", 0x81, 127, navegador.LIMITE_QUADRO + 1))
        with self.assertRaises(navegador.NavegadorErro):
            navegador.ler_quadro(buf.read)


class TestAchar(unittest.TestCase):
    def test_primeiro_que_existe(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "msedge.exe"
            exe.write_text("")
            self.assertEqual(navegador.achar((str(Path(d) / "nao.exe"), str(exe))), str(exe))
            self.assertIsNone(navegador.achar((str(Path(d) / "nao.exe"),)))

    def test_endereco_de_depuracao_so_local(self):
        with self.assertRaisesRegex(navegador.NavegadorErro, "inesperado"):
            navegador._WS("ws://exemplo.com:9222/devtools/page/1")


if __name__ == "__main__":
    unittest.main()
