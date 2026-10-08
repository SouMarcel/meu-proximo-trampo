"""Testes das funções puras do iniciar.py (python -m unittest discover -s tests)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import iniciar  # noqa: E402


def escrever(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")
    return caminho


class Requisitos(unittest.TestCase):
    def test_formatos(self):
        with tempfile.TemporaryDirectory() as d:
            arq = escrever(Path(d) / "requirements.txt",
                           "# comentário\npython-jobspy>=1.2.0\n\npython-docx >= 1.1  # docx\nrequests\npandas==2.0\n")
            self.assertEqual(iniciar.ler_requisitos(arq), [
                ("python-jobspy", "1.2.0", "python-jobspy>=1.2.0"),
                ("python-docx", "1.1", "python-docx >= 1.1"),
                ("requests", None, "requests"),
                ("pandas", "?", "pandas==2.0"),
            ])

    def test_hash_ignora_comentario_e_fim_de_linha(self):
        with tempfile.TemporaryDirectory() as d:
            a = escrever(Path(d) / "a.txt", "x>=1\ny\n")
            b = Path(d) / "b.txt"
            b.write_bytes(b"# nota\r\nx>=1\r\n\r\ny\r\n")
            self.assertEqual(iniciar.hash_requisitos(a), iniciar.hash_requisitos(b))
            c = escrever(Path(d) / "c.txt", "x>=2\ny\n")
            self.assertNotEqual(iniciar.hash_requisitos(a), iniciar.hash_requisitos(c))


class Versoes(unittest.TestCase):
    def test_comparacao(self):
        self.assertTrue(iniciar.versao_ok("1.2.0", "1.2"))
        self.assertTrue(iniciar.versao_ok("1.10", "1.9"))
        self.assertFalse(iniciar.versao_ok("1.1.9", "1.2"))
        self.assertTrue(iniciar.versao_ok("2.0rc1", "1.9"))

    def test_sem_minimo_e_desconhecido(self):
        self.assertTrue(iniciar.versao_ok("0.1", None))
        self.assertTrue(iniciar.versao_ok("0.1", "?"))
        self.assertFalse(iniciar.versao_ok(None, None))
        self.assertFalse(iniciar.versao_ok(None, "?"))


class Ambiente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.req = escrever(self.raiz / "requirements.txt", "x>=1\n")
        self.venv = self.raiz / ".venv"

    def tearDown(self):
        self.tmp.cleanup()

    def preparar(self, home=None, executavel=True):
        escrever(self.venv / "pyvenv.cfg", "home = %s\nversion = 3.12.0\n" % (home or self.raiz))
        if executavel:
            escrever(iniciar.python_do_venv(self.venv), "")

    def estado(self):
        return iniciar.estado_ambiente(self.venv, self.req)

    def test_ausente(self):
        self.assertEqual(self.estado(), "ausente")

    def test_sem_executavel(self):
        self.preparar(executavel=False)
        self.assertEqual(self.estado(), "invalido")

    def test_home_de_outra_maquina(self):
        self.preparar(home=str(self.raiz / "nao-existe"))
        self.assertEqual(self.estado(), "invalido")

    def test_sem_carimbo(self):
        self.preparar()
        self.assertEqual(self.estado(), "sem_carimbo")

    def test_carimbo_velho_e_certo(self):
        self.preparar()
        iniciar.gravar_carimbo(self.venv, "hash-antigo", "3.12.0")
        self.assertEqual(self.estado(), "desatualizado")
        iniciar.gravar_carimbo(self.venv, iniciar.hash_requisitos(self.req), "3.12.0")
        self.assertEqual(self.estado(), "pronto")
        self.assertEqual(iniciar.ler_carimbo(self.venv)["python"], "3.12.0")


class Opcoes(unittest.TestCase):
    def test_padrao(self):
        op, repassar = iniciar.ler_opcoes([])
        self.assertFalse(op.sim)
        self.assertEqual(op.porta, iniciar.PORTA_PADRAO)
        self.assertEqual(repassar, [])

    def test_repassa_ao_servidor(self):
        op, repassar = iniciar.ler_opcoes(["--sim", "--sem-navegador", "--rede", "--porta", "8799"])
        self.assertTrue(op.sim)
        self.assertEqual(repassar, ["--sem-navegador", "--rede", "--porta", "8799"])

    def test_perguntar_com_sim(self):
        self.assertTrue(iniciar.perguntar("Instalar?", sim=True))


if __name__ == "__main__":
    unittest.main()
