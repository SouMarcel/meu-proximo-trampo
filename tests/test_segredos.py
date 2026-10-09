"""Testes do segredos.py (python -m unittest discover -s tests)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import segredos  # noqa: E402


class Segredos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = Path(self.tmp.name) / ".env"
        self.patch_env = mock.patch.object(segredos, "ENV", self.env)
        self.patch_env.start()
        self.ambiente = mock.patch.dict(os.environ, {}, clear=False)
        self.ambiente.start()
        for nome in ("TESTE_CHAVE", "MCP_STARTUP_JOBS"):
            os.environ.pop(nome, None)

    def tearDown(self):
        self.ambiente.stop()
        self.patch_env.stop()
        self.tmp.cleanup()

    def test_grava_e_remove_preservando_o_resto(self):
        self.env.write_text("# minhas chaves\nMCP_STARTUP_JOBS=sj_abc123\n", encoding="utf-8")
        segredos.gravar("TESTE_CHAVE", "valor-de-teste-123456")
        self.assertEqual(segredos.ler("TESTE_CHAVE"), "valor-de-teste-123456")
        self.assertEqual(segredos.final("TESTE_CHAVE"), "3456")
        self.assertEqual(segredos.origem("TESTE_CHAVE"), "arquivo")
        segredos.gravar("TESTE_CHAVE", "outro-valor-999999")
        texto = self.env.read_text(encoding="utf-8")
        self.assertEqual(texto.count("TESTE_CHAVE="), 1)
        self.assertIn("# minhas chaves", texto)
        self.assertIn("MCP_STARTUP_JOBS=sj_abc123", texto)
        self.assertTrue(segredos.remover("TESTE_CHAVE"))
        self.assertEqual(self.env.read_text(encoding="utf-8"), "# minhas chaves\nMCP_STARTUP_JOBS=sj_abc123\n")
        self.assertFalse(segredos.remover("TESTE_CHAVE"))

    def test_ambiente_vence_o_arquivo(self):
        self.env.write_text('export TESTE_CHAVE="do-arquivo-123"\n', encoding="utf-8")
        self.assertEqual(segredos.ler("TESTE_CHAVE"), "do-arquivo-123")
        os.environ["TESTE_CHAVE"] = "do-ambiente-456"
        self.assertEqual(segredos.ler("TESTE_CHAVE"), "do-ambiente-456")
        self.assertEqual(segredos.origem("TESTE_CHAVE"), "ambiente")

    def test_valor_invalido(self):
        for valor in ("", "a\nb", "x" * 401):
            with self.assertRaises(ValueError):
                segredos.gravar("TESTE_CHAVE", valor)
        with self.assertRaises(ValueError):
            segredos.gravar("nome errado", "abc")
        self.assertFalse(self.env.exists())

    def test_sem_arquivo(self):
        self.assertEqual(segredos.ler("TESTE_CHAVE"), "")
        self.assertIsNone(segredos.origem("TESTE_CHAVE"))
        self.assertEqual(segredos.final("TESTE_CHAVE"), "")


if __name__ == "__main__":
    unittest.main()
