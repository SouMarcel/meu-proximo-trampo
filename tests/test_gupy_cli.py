"""Testes do uso por linha de comando do fontes/gupy.py (sem rede)."""
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fontes import gupy  # noqa: E402


class Argumentos(unittest.TestCase):
    def test_chave_valor(self):
        self.assertEqual(
            gupy.argumentos_da_linha(["term=analista de dados", "pwd=true", "limit=10", "workplaceTypes=hybrid,on-site",
                                      "gupyBadge=False", "filtro=a=b"]),
            {"term": "analista de dados", "pwd": True, "limit": 10, "workplaceTypes": "hybrid,on-site",
             "gupyBadge": False, "filtro": "a=b"})

    def test_json(self):
        self.assertEqual(gupy.argumentos_da_linha(['{"term": "analista", "limit": 5}']), {"term": "analista", "limit": 5})
        with self.assertRaises(ValueError):
            gupy.argumentos_da_linha(['["lista"]'])

    def test_invalido(self):
        for item in ("analista", "=valor"):
            with self.assertRaises(ValueError):
                gupy.argumentos_da_linha([item])


class Comando(unittest.TestCase):
    def rodar(self, argv):
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = gupy.main(argv)
        return codigo, saida.getvalue(), erro.getvalue()

    def test_ajuda_e_ferramenta_desconhecida(self):
        codigo, saida, _ = self.rodar(["--help"])
        self.assertEqual(codigo, 0)
        self.assertIn("search_jobs", saida)
        codigo, _, erro = self.rodar(["apagar_tudo"])
        self.assertEqual(codigo, 2)
        self.assertIn("desconhecida", erro)

    def test_argumento_invalido_nao_chama_a_rede(self):
        codigo, _, erro = self.rodar(["search_jobs", "analista"])
        self.assertEqual(codigo, 1)
        self.assertIn("chave=valor", erro)


if __name__ == "__main__":
    unittest.main()
